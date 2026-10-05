import { LiveConnection, 入力レート, 音声入力, 音声操作, type Packet } from './protocol';
import { LiveAudio } from './audio';
import { AudioCloud } from './visualizer';
import { LiveEnvironment, type Folder } from './bridge';
import { microphoneError } from './microphone-error';

type Catalog = Record<string, Record<string, string>>;
type DesktopApi = { windowAction: (action: string) => void; onState: (callback: (state: { opening: boolean }) => void) => () => void };
const element = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const button = (id: string) => element<HTMLButtonElement>(id);
const provider = element<HTMLSelectElement>('provider'), model = element<HTMLSelectElement>('model'), voice = element<HTMLSelectElement>('voice');
const errorBox = element('error'), status = element('status'), transcript = element('transcript');
const environment = new LiveEnvironment();
let connected = false, busy = false, mic = false, micBusy = false, changing = false, generation = 0;
let micGeneration = 0;
let settings: Record<string, string> = {}, models: Catalog = {}, voices: Catalog = {};
let heartbeat: ReturnType<typeof setInterval> | undefined;
const cloud = new AudioCloud(element<HTMLCanvasElement>('audio-cloud'));
const audio = new LiveAudio(base64 => connection.send('audio', 音声入力(base64)), (kind, value) => {
  cloud.level(kind, value);
}, (kind, values) => cloud.spectrum(kind, values), environment.captureUrl, environment.host ? environment.acquireMicrophone : undefined);
const connection = new LiveConnection(environment.socketUrl, receive, () => {
  void disconnect(); showError('接続が切れました。「接続する」で新しい会話を開始できます。');
}, environment.socket);
environment.onStop(error => {
  void disconnect(); if (error) showError(error);
  void environment.backend().then(backend => { element<HTMLInputElement>('backend').value = backend; });
});
environment.onMicrophoneStop(() => {
  ++micGeneration; mic = false; micBusy = false; audio.stop(); controls();
});
if (environment.host) {
  document.body.classList.add('vscode-host');
  button('standalone').hidden = false;
  button('standalone').onclick = () => environment.standalone();
}
const desktop = (window as Window & { aidiyLiveDesktop?: DesktopApi }).aidiyLiveDesktop;
let stopDesktopState: (() => void) | undefined;
if (desktop) {
  document.documentElement.classList.add('desktop-window', 'desktop-opening');
  stopDesktopState = desktop.onState(({ opening }) => document.documentElement.classList.toggle('desktop-opening', opening));
  element('window-controls').hidden = false;
  document.querySelectorAll<HTMLButtonElement>('[data-window]').forEach(control => {
    control.addEventListener('click', () => desktop.windowAction(control.dataset.window!));
  });
}
function showError(message = '') { errorBox.textContent = message; errorBox.hidden = !message; }
function showFolder(folder?: Folder | null) {
  const label = element('project-folder');
  label.textContent = folder?.名前 || '';
  label.title = folder?.パス || '';
}
environment.onFolder(showFolder);
function controls() {
  document.body.classList.toggle('connected', connected);
  button('connect').classList.toggle('awaiting', !connected && !busy);
  element('activity').classList.toggle('connected', connected);
  element('activity').classList.toggle('running', busy || mic);
  button('connect').textContent = busy ? '接続中…' : connected ? '切断' : '接続';
  button('connect').disabled = busy || changing;
  button('mic').disabled = !connected || micBusy || changing;
  button('mic').setAttribute('aria-pressed', String(mic));
  button('mic').querySelector('strong')!.textContent = mic ? 'ON' : 'OFF';
  button('mic').setAttribute('aria-label', micBusy ? 'マイク準備中' : `マイク ${mic ? 'ON' : 'OFF'}`);
  button('mic').setAttribute('aria-busy', String(micBusy));
  const speakerOn = connected && audio.speaker;
  button('speaker').disabled = !connected || changing;
  button('speaker').setAttribute('aria-pressed', String(speakerOn));
  button('speaker').querySelector('strong')!.textContent = speakerOn ? 'ON' : 'OFF';
  button('speaker').setAttribute('aria-label', `スピーカー ${speakerOn ? 'ON' : 'OFF'}`);
  button('send').disabled = !connected || changing || !element<HTMLTextAreaElement>('text').value.trim();
  button('apply').disabled = !connected || changing || !provider.value || !model.value;
  for (const select of [provider, model, voice]) select.disabled = !connected || changing;
  status.textContent = busy ? '接続中' : connected ? mic ? '会話中' : '接続済み' : '未接続';
}
function message(role: 'user' | 'ai' | 'system', text: string) {
  if (!text.trim() || ['!', '\x02', '\x03', '\x18'].includes(text.trim())) return;
  element('empty')?.remove();
  const row = document.createElement('div'); row.className = `message ${role}`;
  row.textContent = text.slice(0, 20000); transcript.append(row);
  while (transcript.children.length > 100) transcript.firstElementChild?.remove();
  transcript.scrollTop = transcript.scrollHeight;
}
function receive(packet: Packet) {
  const type = packet.メッセージ識別;
  if (type === 'output_audio') audio.play(packet);
  else if (type === 'cancel_audio') audio.cancel();
  else if (['input_text', 'output_text', 'output', 'recognition_input', 'recognition_output'].includes(type || '') && packet.チャンネル === '0') {
    message(type === 'input_text' || type === 'recognition_input' ? 'user' : 'ai', String(packet.メッセージ内容 || ''));
  } else if (type === 'welcome_text') message('system', String(packet.メッセージ内容 || ''));
  else if (type === 'error') showError(String(packet.メッセージ内容 || packet.error || '会話エラーが発生しました。'));
}
async function api(path: string, body: object) {
  const result = await environment.api(path, body);
  if (result.status !== 'OK') throw new Error(result.message || '接続エラーが発生しました。');
  return result.data;
}
function options(select: HTMLSelectElement, values: Record<string, string>, selected = '') {
  select.replaceChildren();
  // 設定済みの値がカタログにない場合も表示・維持する。
  if (selected && !(selected in values)) values = { [selected]: selected, ...values };
  for (const [value, label] of Object.entries(values)) select.add(new Option(String(label), value));
  if (selected) select.value = selected;
}
function keys(name = provider.value) {
  const vendor = name === 'openai_live' ? 'OPENAI' : name === 'freeai_live' ? 'FREEAI' : 'GEMINI';
  return { model: `LIVE_${vendor}_MODEL`, voice: `LIVE_${vendor}_VOICE` };
}
function modelOptions() {
  const key = keys();
  options(model, models[provider.value] || {}, settings[key.model]);
  options(voice, voices[provider.value] || {}, settings[key.voice]);
  controls();
}
async function loadModels() {
  const run = generation;
  const data = await api('core/AIコア/モデル情報/取得', { セッションID: connection.session });
  if (run !== generation) return;
  settings = data.モデル設定 || {}; models = data.available_models?.live_models || {}; voices = data.available_models?.live_voices || {};
  options(provider, Object.fromEntries(Object.keys(models).map(name => [name, name])), settings.LIVE_AI_NAME);
  modelOptions();
  element('model-label').textContent = [settings.LIVE_AI_NAME, settings[keys(settings.LIVE_AI_NAME).model], settings[keys(settings.LIVE_AI_NAME).voice]].filter(Boolean).join(' · ');
}
async function disconnect() {
  ++generation; connected = false; busy = false; mic = false; micBusy = false; changing = false;
  if (heartbeat) clearInterval(heartbeat); heartbeat = undefined;
  connection.send('input', 音声操作(false, false)); audio.close(); connection.disconnect(); controls();
  element('session-label').textContent = '音声はマイク ON の間だけ送信します。';
}
button('connect').onclick = async () => {
  if (connected) { await disconnect(); return; }
  const run = ++generation; busy = true; showError(); controls();
  try {
    await audio.unlock();
    if (run !== generation) return;
    transcript.replaceChildren();
    await connection.connect();
    if (run !== generation) return;
    await loadModels();
    if (run !== generation) return;
    connected = true; connection.send('input', 音声操作(false, audio.speaker));
    if (!environment.host) heartbeat = setInterval(() => connection.send('input', { type: 'ping' }), 20000);
    element('session-label').textContent = `会話 ${connection.session.slice(0, 12)}`;
  } catch (error) { if (run === generation) { await disconnect(); showError(error instanceof Error ? error.message : String(error)); } }
  finally { if (run === generation) { busy = false; controls(); } }
};
button('mic').onclick = async () => {
  if (!connected || micBusy) return;
  showError();
  if (mic) { mic = false; audio.stop(); connection.send('input', 音声操作(false, audio.speaker)); controls(); return; }
  const run = generation, micRun = ++micGeneration; micBusy = true; controls();
  try {
    mic = await audio.start(入力レート(settings.LIVE_AI_NAME || ''));
    if (run !== generation || micRun !== micGeneration) { audio.stop(); mic = false; return; }
    connection.send('input', 音声操作(mic, audio.speaker));
  } catch (error) { if (run === generation && micRun === micGeneration) { mic = false; showError(`マイクを開始できません: ${microphoneError(error)}`); } }
  finally { if (micRun === micGeneration) { micBusy = false; controls(); } }
};
button('speaker').onclick = async () => {
  if (!connected || changing) return;
  const enabled = !audio.speaker;
  try { if (enabled) await audio.unlock(); audio.mute(enabled); connection.send('input', 音声操作(mic, enabled)); controls(); }
  catch (error) { showError(String(error)); }
};
button('new').onclick = async () => { await disconnect(); transcript.replaceChildren(); element('model-label').textContent = 'AiDiy のライブ会話'; message('system', '次の接続で新しい会話を開始します。'); };
const modelPicker = element<HTMLDialogElement>('model-picker');
button('choose-model').onclick = () => modelPicker.showModal();
button('close-model').onclick = () => modelPicker.close();
element<HTMLFormElement>('text-form').onsubmit = event => {
  event.preventDefault(); const input = element<HTMLTextAreaElement>('text'), text = input.value.trim();
  if (!connected || changing || !text) return;
  if (connection.send('input', { チャンネル: '0', メッセージ識別: 'input_text', メッセージ内容: text, 送信モード: 'Live', 出力先チャンネル: '0' })) input.value = '';
  controls();
};
element<HTMLTextAreaElement>('text').addEventListener('input', () => {
  element('empty')?.classList.add('input-started');
  controls();
});
element<HTMLTextAreaElement>('text').addEventListener('keydown', event => {
  if (event.key !== 'Tab' || event.shiftKey || event.altKey || event.ctrlKey || event.metaKey
      || event.isComposing || event.keyCode === 229 || button('send').disabled) return;
  event.preventDefault(); button('send').focus();
});
provider.onchange = modelOptions;
button('apply').onclick = async () => {
  const run = generation; changing = true; showError(); mic = false; audio.stop(); audio.cancel(); connection.send('input', 音声操作(false, audio.speaker)); controls();
  try {
    const key = keys();
    await api('core/AIコア/モデル設定', { セッションID: connection.session, モデル設定: { LIVE_AI_NAME: provider.value, [key.model]: model.value, [key.voice]: voice.value }, save: false });
    if (run !== generation) return;
    await loadModels();
    if (run === generation) { modelPicker.close(); message('system', 'モデルを切り替えました。マイクを ON にして会話を再開できます。'); }
  } catch (error) { if (run === generation) showError(String(error)); }
  finally { if (run === generation) { changing = false; controls(); } }
};
window.addEventListener('pagehide', () => { stopDesktopState?.(); void disconnect(); cloud.dispose(); environment.dispose(); });
let revealed = false;
function reveal() {
  if (revealed) return;
  revealed = true; clearTimeout(revealTimeout);
  requestAnimationFrame(() => requestAnimationFrame(() => document.body.classList.add('ui-ready')));
}
// 接続先情報が遅れても操作できる画面を表示する。
const revealTimeout = window.setTimeout(reveal, 2500);
environment.context().then(config => {
  element<HTMLInputElement>('backend').value = config.backend || '';
  showFolder(config.作業フォルダ);
}).catch(() => showError('接続先情報を取得できません。')).finally(reveal);
controls();
environment.ready();
