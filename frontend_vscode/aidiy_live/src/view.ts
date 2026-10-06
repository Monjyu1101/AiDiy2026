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
const errorBox = element('error'), modelError = element('model-error'), status = element('status'), transcript = element('transcript');
const initialWelcome = element('empty').cloneNode(true);
let 回答演出停止: (() => void) | undefined;
const environment = new LiveEnvironment();
let connected = false, busy = false, mic = false, micBusy = false, changing = false, generation = 0;
let micGeneration = 0;
let modelLoading = false;
let preferredSettings: Record<string, string> = {};
let sessionProject: string | undefined;
let settings: Record<string, string> = {}, models: Catalog = {}, voices: Catalog = {};
let heartbeat: ReturnType<typeof setInterval> | undefined;
const cloud = new AudioCloud(element<HTMLCanvasElement>('audio-cloud'));
const audio = new LiveAudio(base64 => connection.send('audio', 音声入力(base64)), (kind, value) => {
  cloud.level(kind, value);
}, (kind, values) => cloud.spectrum(kind, values), environment.captureUrl, environment.host ? environment.acquireMicrophone : undefined);
const connection = new LiveConnection(environment.socketUrl, receive, () => {
  void disconnect(); showError('接続が切れました。「接続」で新しい会話を開始できます。');
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
function showError(message = '') {
  for (const box of [errorBox, modelError]) { box.textContent = message; box.hidden = !message; }
}
function showFolder(folder?: Folder | null) {
  const label = element('project-folder');
  label.textContent = folder?.名前 || '';
  label.title = folder?.パス || '';
  if (sessionProject !== undefined && sessionProject !== (folder?.パス || '') && (connected || busy)) {
    void disconnect();
    showError('プロジェクトフォルダが変わりました。「接続」で新しいプロジェクトの会話を開始してください。');
  }
}
environment.onFolder(showFolder);
function controls() {
  document.body.classList.toggle('connected', connected);
  button('connect').classList.toggle('awaiting', !connected && !busy);
  element('activity').classList.toggle('connected', connected);
  element('activity').classList.toggle('running', busy || mic);
  button('connect').textContent = busy ? '接続中…' : connected ? '切断' : '接続';
  button('connect').disabled = busy || changing;
  button('new').disabled = busy || changing;
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
  button('send').classList.toggle('ws-disabled', !connected);
  const key = keys();
  const selectionChanged = provider.value !== settings.LIVE_AI_NAME || model.value !== settings[key.model]
    || voice.value !== (settings[key.voice] || '');
  button('apply').disabled = busy || changing || modelLoading || !provider.value || !model.value || !selectionChanged;
  button('apply').textContent = changing ? '再接続中…' : connected ? '変更して再接続' : '選択する';
  element('model-behavior').textContent = connected || changing
    ? 'モデルや音声を変更すると、音声AIへ自動で再接続します。マイクは OFF に戻ります。'
    : '選択したモデルと音声で、次の接続を開始します。';
  element('model-conversation').hidden = !connected && !changing;
  button('choose-model').disabled = busy || changing || modelLoading;
  button('cancel-model').disabled = changing;
  button('close-model').disabled = changing;
  for (const select of [provider, model, voice]) select.disabled = busy || changing || modelLoading || !Object.keys(models).length;
  status.textContent = changing ? '再接続中' : busy ? '接続中' : connected ? mic ? '会話中' : '接続済み' : '未接続';
}
function コンソール演出(row: HTMLDivElement, text: string) {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    row.textContent = text; return;
  }
  row.classList.add('console-effect');
  const terminalText = document.createElement('span');
  const cursor = document.createElement('span'); cursor.className = 'terminal-cursor';
  row.replaceChildren(terminalText, cursor);
  const batch = Math.max(1, Math.floor(text.length / 50) + 1);
  let index = 0, timer: number;
  const finish = () => {
    clearTimeout(timer);
    row.classList.remove('console-effect'); row.textContent = text;
    回答演出停止 = undefined;
  };
  const tick = () => {
    const end = Math.min(index + batch, text.length);
    terminalText.textContent += text.slice(index, end); index = end;
    transcript.scrollTop = transcript.scrollHeight;
    if (index < text.length) { timer = window.setTimeout(tick, 10); return; }
    finish();
    transcript.scrollTop = transcript.scrollHeight;
  };
  回答演出停止 = finish;
  // Code の回答表示と同じく、500ms 待ってから10msごとに文字を追加する。
  timer = window.setTimeout(tick, 500);
}
function message(role: 'user' | 'ai' | 'system', text: string, 音声認識 = false) {
  if (!text.trim() || ['!', '\x02', '\x03', '\x18'].includes(text.trim())) return;
  element('empty')?.remove();
  const row = document.createElement('div'); row.className = `message ${role}`;
  if (音声認識) row.classList.add('recognition');
  if (role === 'user' || 音声認識) {
    row.title = 'クリックして入力欄へ戻す';
    row.addEventListener('click', () => {
      const input = element<HTMLTextAreaElement>('text');
      input.value = text;
      input.focus(); input.setSelectionRange(input.value.length, input.value.length);
      controls();
    });
  }
  回答演出停止?.();
  transcript.append(row);
  if (role === 'ai') コンソール演出(row, text.slice(0, 20000));
  else row.textContent = text.slice(0, 20000);
  while (transcript.children.length > 100) transcript.firstElementChild?.remove();
  transcript.scrollTop = transcript.scrollHeight;
}
function receive(packet: Packet) {
  const type = packet.メッセージ識別;
  if (type === 'output_audio') audio.play(packet);
  else if (type === 'cancel_audio') audio.cancel();
  else if (['input_text', 'output_text', 'output_request', 'output', 'recognition_input', 'recognition_output'].includes(type || '') && packet.チャンネル === '0') {
    // 旧バックエンドの送信失敗通知も、無反応に見せず案内する。
    if (type === 'output_text' && String(packet.メッセージ内容 || '').trim() === '!') {
      showError('LiveAI に送信できませんでした。音声AIへの接続状態を確認し、接続し直して再送してください。'); return;
    }
    message(type === 'input_text' || type === 'recognition_input' ? 'user' : 'ai', String(packet.メッセージ内容 || ''),
      type === 'recognition_input' || type === 'recognition_output');
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
  await initialContext;
  if (run !== generation) return;
  const data = await api('core/AIコア/モデル情報/取得', { セッションID: connection.session });
  if (run !== generation) return;
  settings = connection.session ? data.モデル設定 || {} : { ...data.モデル設定, ...preferredSettings }; models = data.available_models?.live_models || {}; voices = data.available_models?.live_voices || {};
  options(provider, Object.fromEntries(Object.keys(models).map(name => [name, name])), settings.LIVE_AI_NAME);
  modelOptions();
  element('model-label').textContent = [settings.LIVE_AI_NAME, settings[keys(settings.LIVE_AI_NAME).model], settings[keys(settings.LIVE_AI_NAME).voice]].filter(Boolean).join(' · ');
}
async function disconnect() {
  回答演出停止?.();
  ++generation; connected = false; busy = false; mic = false; micBusy = false; changing = false;
  ++micGeneration;
  sessionProject = undefined;
  if (heartbeat) clearInterval(heartbeat); heartbeat = undefined;
  connection.send('input', 音声操作(false, false)); audio.close(); audio.mute(true); connection.disconnect();
  transcript.replaceChildren(initialWelcome.cloneNode(true)); transcript.scrollTop = 0;
  element<HTMLTextAreaElement>('text').value = '';
  settings = {}; models = {}; voices = {};
  for (const select of [provider, model, voice]) { select.replaceChildren(); select.value = ''; }
  element('model-label').textContent = 'AiDiy のライブ会話';
  modelPicker.close(); showError(); controls();
  element('session-label').textContent = '音声はマイク ON の間だけ送信します。';
}
async function connectSession(preserveConversation = false, automatic = false) {
  const run = ++generation; busy = true; showError(); controls();
  if (heartbeat) clearInterval(heartbeat); heartbeat = undefined;
  try {
    // 起動時の接続を、ブラウザの音声再生許可待ちで止めない。
    if (!automatic) await audio.unlock();
    if (run !== generation) return;
    await initialContext;
    if (run !== generation) return;
    const config = await environment.context();
    if (run !== generation) return;
    showFolder(config.作業フォルダ);
    sessionProject = config.作業フォルダ?.パス || '';
    if (run !== generation) return;
    if (!preserveConversation) { 回答演出停止?.(); transcript.replaceChildren(); }
    await connection.connect({ codeBasePath: sessionProject, modelSettings: preferredSettings });
    if (run !== generation) return;
    await loadModels();
    if (run !== generation) return;
    connected = true; connection.send('input', 音声操作(false, audio.speaker));
    if (!environment.host) heartbeat = setInterval(() => connection.send('input', { type: 'ping' }), 20000);
    element('session-label').textContent = `会話 ${connection.session.slice(0, 12)}`;
  } catch (error) { if (run === generation) { await disconnect(); showError(error instanceof Error ? error.message : String(error)); } }
  finally { if (run === generation) { busy = false; changing = false; controls(); } }
}
button('connect').onclick = async () => {
  if (connected) await disconnect();
  else await connectSession();
};
async function startMicrophone() {
  if (!connected || mic || micBusy || changing) return;
  showError();
  const run = generation, micRun = ++micGeneration; micBusy = true; controls();
  try {
    await audio.unlock();
    if (run !== generation || micRun !== micGeneration) return;
    mic = await audio.start(入力レート(settings.LIVE_AI_NAME || ''));
    if (run !== generation || micRun !== micGeneration) { audio.stop(); mic = false; return; }
    connection.send('input', 音声操作(mic, audio.speaker));
  } catch (error) { if (run === generation && micRun === micGeneration) { mic = false; showError(`マイクを開始できません: ${microphoneError(error)}`); } }
  finally { if (micRun === micGeneration) { micBusy = false; controls(); } }
}
button('mic').onclick = async () => {
  if (!connected || micBusy || changing) return;
  if (mic) { showError(); mic = false; audio.stop(); connection.send('input', 音声操作(false, audio.speaker)); controls(); return; }
  await startMicrophone();
};
button('speaker').onclick = async () => {
  if (!connected || changing) return;
  const enabled = !audio.speaker;
  try { if (enabled) await audio.unlock(); audio.mute(enabled); connection.send('input', 音声操作(mic, enabled)); controls(); }
  catch (error) { showError(String(error)); }
};
button('new').onclick = async () => {
  if (busy || changing) return;
  const reconnect = connected, speaker = audio.speaker, microphone = mic;
  const selectedSettings = { ...preferredSettings };
  for (const key of ['LIVE_AI_NAME', ...Object.values(keys(settings.LIVE_AI_NAME))]) {
    if (settings[key]) selectedSettings[key] = settings[key];
  }
  const reset = disconnect(), run = generation;
  await reset;
  if (!reconnect || run !== generation) return;
  preferredSettings = selectedSettings;
  audio.mute(speaker);
  // 表示を初期化したうえで、同じモデル・音声の新しいセッションを作る。
  const connecting = connectSession(true), reconnectRun = generation;
  await connecting;
  if (microphone && reconnectRun === generation && connected) await startMicrophone();
};
const modelPicker = element<HTMLDialogElement>('model-picker');
button('choose-model').onclick = async () => {
  modelPicker.showModal(); modelLoading = true; showError(); controls();
  try { await loadModels(); }
  catch (error) { showError(error instanceof Error ? error.message : String(error)); }
  finally { modelLoading = false; controls(); }
};
button('close-model').onclick = () => modelPicker.close();
button('cancel-model').onclick = () => modelPicker.close();
modelPicker.addEventListener('cancel', event => { if (changing) event.preventDefault(); });
element<HTMLFormElement>('text-form').onsubmit = event => {
  event.preventDefault(); const input = element<HTMLTextAreaElement>('text'), text = input.value.trim();
  if (!connected || changing || !text) return;
  showError();
  void audio.unlock().catch(error => showError(String(error)));
  if (connection.send('input', { チャンネル: '0', メッセージ識別: 'input_text', メッセージ内容: text, 送信モード: 'Live', 出力先チャンネル: '0' })) input.value = '';
  else showError('送信できませんでした。接続を確認し、もう一度送信してください。');
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
model.onchange = controls;
voice.onchange = controls;
button('apply').onclick = async () => {
  if (button('apply').disabled) return;
  const key = keys();
  preferredSettings = { LIVE_AI_NAME: provider.value, [key.model]: model.value,
    ...(voice.value ? { [key.voice]: voice.value } : {}) };
  if (!connected) {
    settings = { ...settings, ...preferredSettings };
    element('model-label').textContent = [provider.value, model.value, voice.value].filter(Boolean).join(' · ');
    modelPicker.close(); showError(); controls(); return;
  }
  changing = true; ++micGeneration; mic = false; micBusy = false;
  connection.send('input', 音声操作(false, audio.speaker)); audio.close(); connected = false; controls();
  await connectSession(true);
  if (connected) {
    modelPicker.close();
    message('system', '選択したモデルで接続しました。マイクを ON にして新しい会話を開始できます。');
  }
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
const initialContext = environment.context().then(config => {
  element<HTMLInputElement>('backend').value = config.backend || '';
  showFolder(config.作業フォルダ);
  preferredSettings = { ...config.モデル設定, ...preferredSettings };
  if (Object.keys(preferredSettings).length) {
    settings = { ...settings, ...preferredSettings };
    element('model-label').textContent = [settings.LIVE_AI_NAME, settings[keys(settings.LIVE_AI_NAME).model]].filter(Boolean).join(' · ');
  }
  // 起動引数でモデルを指定した単独画面だけ、初回に自動接続する。
  return !environment.host && !!config.モデル設定?.[keys(config.モデル設定.LIVE_AI_NAME).model];
}).catch(() => { showError('接続先情報を取得できません。'); return false; }).finally(reveal);
controls();
environment.ready();
void initialContext.then(automatic => {
  if (automatic && generation === 0 && !connected && !busy) void connectSession(false, true);
});
