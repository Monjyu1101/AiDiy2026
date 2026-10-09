import { 最下部追従 } from '../../src/scroll-follow';
import { 演出初期化, 到着表示, 即時表示, 枠飛行, 入力枠作成, 受信通知作成 } from '../../src/arrival-effect';
import { LiveConnection, 入力レート, 音声入力, 音声操作, type Packet } from './protocol';
import { LiveAudio } from './audio';
import { AudioCloud } from './visualizer';
import { LiveEnvironment, type Folder } from './bridge';
import { microphoneError } from './microphone-error';
import { ライブ選択エラー } from './model-catalog';

type Catalog = Record<string, Record<string, string>>;
type DesktopApi = { windowAction: (action: string) => void; onState: (callback: (state: { opening: boolean }) => void) => () => void };
const element = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const button = (id: string) => element<HTMLButtonElement>(id);
const provider = element<HTMLSelectElement>('provider'), model = element<HTMLSelectElement>('model'), voice = element<HTMLSelectElement>('voice');
const errorBox = element('error'), modelError = element('model-error'), status = element('status'), transcript = element('transcript');
const 最下部表示 = 最下部追従([transcript]);
const initialWelcome = element('empty').cloneNode(true);
let 回答演出停止: (() => void) | undefined;
const environment = new LiveEnvironment();
let connected = false, busy = false, mic = false, micBusy = false, changing = false, generation = 0;
let micGeneration = 0;
let modelLoading = false;
let modelSaving = false;
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
  button('connect').disabled = busy || changing || modelSaving;
  button('new').disabled = busy || changing || modelSaving;
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
  const selectionError = ライブ選択エラー({ LIVE_AI_NAME: provider.value, [key.model]: model.value, [key.voice]: voice.value }, { models, voices });
  button('apply').disabled = busy || changing || modelLoading || modelSaving || !!selectionError || !selectionChanged;
  button('apply').textContent = modelSaving ? '保存中…' : changing ? '再接続中…' : connected ? '変更して再接続' : '選択する';
  element('model-behavior').textContent = connected || changing
    ? 'モデルや音声を変更すると、音声AIへ自動で再接続します。マイクは OFF に戻ります。'
    : '選択したモデルと音声で、次の接続を開始します。';
  element('model-conversation').hidden = !connected && !changing;
  button('choose-model').disabled = busy || changing || modelLoading || modelSaving;
  button('cancel-model').disabled = changing || modelSaving;
  button('close-model').disabled = changing || modelSaving;
  for (const select of [provider, model, voice]) select.disabled = busy || changing || modelLoading || modelSaving || !Object.keys(models).length;
  status.textContent = changing ? '再接続中' : busy ? '接続中' : connected ? mic ? '会話中' : '接続済み' : '未接続';
}
// 発言の登場演出は AiDiy Code と共通（src/arrival-effect.ts）。発言は透明のまま会話欄に置いて場所を確保し、
// そこへ枠を飛ばしてから浮かび上がらせる。OS の「動きを減らす」設定には従わない。
// 送信した文字入力は、バックエンドから戻った同じ input_text の行へ入力枠を飛ばす。
let 送信予約: { 起点: DOMRect; 本文: string; 期限: number } | undefined;
let 入力枠: HTMLElement | undefined;
function 入力飛行(row: HTMLDivElement, 起点: DOMRect, 本文: string) {
  入力枠?.remove();
  row.classList.add('arrival-pending');
  const frame = 入力枠 = 入力枠作成(本文);
  枠飛行(frame, 起点, () => row, () => {
    if (入力枠 === frame) 入力枠 = undefined;
    if (row.isConnected !== false) 到着表示(row);
  });
}
// AI の回答は画面中央の受信通知にターミナル演出（AIコード.vue と同じ文字送り）で出し、全文を表示し終えてから3秒止めて会話欄の行へ飛ばす。
// 次の発言が届いたとき・切断・新しい会話では演出を止め、回答の行をすぐに表示する。
function 受信通知(row: HTMLDivElement, text: string, type: string) {
  row.classList.add('arrival-waiting');
  const { popup, body } = 受信通知作成(type);
  let holdTimer: number | undefined, 終了 = false;
  const カーソル色 = type === 'output_request' ? '#00ffff' : type === 'recognition_output' ? '#9ae6b4' : '#00ff00';
  const 片付け = (show: () => void) => {
    if (終了) return;
    終了 = true; clearTimeout(holdTimer); effect.停止(); popup.remove();
    if (回答演出停止 === stop) 回答演出停止 = undefined;
    show(); 最下部表示();
  };
  const stop = () => 片付け(() => 即時表示(row));
  const 着地 = () => {
    if (終了) return;
    row.classList.remove('arrival-waiting'); row.classList.add('arrival-pending');
    最下部表示();
    枠飛行(popup, popup.getBoundingClientRect(), () => row, () => 片付け(() => 到着表示(row)));
  };
  const effect = 演出初期化(body, {
    カーソル色, isStream: false,
    表示更新: () => { body.scrollTop = body.scrollHeight; },
    完了: () => { if (!終了) holdTimer = window.setTimeout(着地, 3000); },
  });
  回答演出停止 = stop;
  effect.追加(text, true);
}
function message(role: 'user' | 'ai' | 'system', text: string, type = '') {
  if (!text.trim() || ['!', '\x02', '\x03', '\x18'].includes(text.trim())) return;
  element('empty')?.remove();
  const row = document.createElement('div'); row.className = `message ${role}`;
  if (type) row.classList.add(type);
  const 音声認識 = type === 'recognition_input' || type === 'recognition_output';
  if (音声認識) row.classList.add('recognition');
  if (role === 'user' || 音声認識) {
    row.title = 'クリックして入力欄へ戻す';
    row.addEventListener('click', () => {
      const input = element<HTMLTextAreaElement>('text');
      input.value = text;
      input.focus(); input.setSelectionRange(input.value.length, input.value.length);
      controls(); 最下部表示();
    });
  }
  回答演出停止?.();
  row.textContent = text.slice(0, 20000);
  transcript.append(row);
  const 予約 = 送信予約;
  if (role === 'user' && type === 'input_text' && 予約 && Date.now() <= 予約.期限 && 予約.本文 === text.trim()) {
    送信予約 = undefined;
    入力飛行(row, 予約.起点, 予約.本文);
  } else if (role === 'ai' && !document.hidden) 受信通知(row, text.slice(0, 20000), type);
  while (transcript.children.length > 100) transcript.firstElementChild?.remove();
  最下部表示();
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
    message(type === 'input_text' || type === 'recognition_input' ? 'user' : 'ai', String(packet.メッセージ内容 || ''), type);
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
  const missing = !!selected && !Object.hasOwn(values, selected);
  if (missing || !Object.keys(values).length) {
    const placeholder = new Option('候補から選択してください', '');
    placeholder.disabled = true; select.add(placeholder);
  }
  for (const [value, label] of Object.entries(values)) select.add(new Option(String(label), value));
  if (selected) select.value = missing ? '' : selected;
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
function showModels() {
  options(provider, Object.fromEntries(Object.keys(models).map(name => [name, name])), settings.LIVE_AI_NAME);
  modelOptions();
  element('model-label').textContent = [settings.LIVE_AI_NAME, settings[keys(settings.LIVE_AI_NAME).model]].filter(Boolean).join(' - ') || 'AiDiy のライブ会話';
}
async function loadModels(session = connection.session) {
  const run = generation;
  await initialContext;
  if (run !== generation) return;
  const data = await api('core/AIコア/モデル情報/取得', { セッションID: session });
  if (run !== generation) return;
  settings = session ? data.モデル設定 || {} : { ...data.モデル設定, ...preferredSettings }; models = data.available_models?.live_models || {}; voices = data.available_models?.live_voices || {};
  showModels();
  if (!session) showError(ライブ選択エラー(settings, { models, voices }));
}
async function disconnect() {
  回答演出停止?.();
  送信予約 = undefined; 入力枠?.remove(); 入力枠 = undefined;
  ++generation; connected = false; busy = false; mic = false; micBusy = false; changing = false; modelSaving = false;
  ++micGeneration;
  sessionProject = undefined;
  if (heartbeat) clearInterval(heartbeat); heartbeat = undefined;
  connection.send('input', 音声操作(false, false)); audio.close(); audio.mute(true); connection.disconnect();
  transcript.replaceChildren(initialWelcome.cloneNode(true)); transcript.scrollTop = 0;
  element<HTMLTextAreaElement>('text').value = '';
  // 未接続でも次回のモデル・音声を確認できるよう、確定した設定を表示する。
  settings = { ...settings, ...preferredSettings };
  showModels();
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
    // 保存済み・起動引数の指定も、接続を作る前に最新の候補と照合する。
    await loadModels('');
    if (run !== generation) return;
    const selectionError = ライブ選択エラー(settings, { models, voices });
    if (selectionError) throw new Error(selectionError);
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
modelPicker.addEventListener('cancel', event => { if (changing || modelSaving) event.preventDefault(); });
element<HTMLFormElement>('text-form').onsubmit = event => {
  event.preventDefault(); const input = element<HTMLTextAreaElement>('text'), text = input.value.trim();
  if (!connected || changing || !text) return;
  showError();
  void audio.unlock().catch(error => showError(String(error)));
  // 送信した位置を覚えておき、戻ってきた同じ文字入力の行へ入力枠を飛ばす。
  const 起点 = input.getBoundingClientRect();
  if (connection.send('input', { チャンネル: '0', メッセージ識別: 'input_text', メッセージ内容: text, 送信モード: 'Live', 出力先チャンネル: '0' })) {
    input.value = ''; 送信予約 = { 起点, 本文: text, 期限: Date.now() + 15_000 };
  } else showError('送信できませんでした。接続を確認し、もう一度送信してください。');
  controls(); 最下部表示();
};
element<HTMLTextAreaElement>('text').addEventListener('input', () => {
  element('empty')?.classList.add('input-started');
  controls(); 最下部表示();
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
  const selected = { LIVE_AI_NAME: provider.value, [key.model]: model.value,
    ...(voice.value ? { [key.voice]: voice.value } : {}) };
  const run = generation;
  modelSaving = true; showError(); controls();
  try { await environment.saveModel(selected); }
  catch (error) { if (run === generation) showError(`モデルを保存できません: ${error instanceof Error ? error.message : String(error)}`); return; }
  finally { modelSaving = false; controls(); }
  if (run !== generation) return;
  preferredSettings = selected;
  if (!connected) {
    settings = { ...settings, ...preferredSettings };
    element('model-label').textContent = [provider.value, model.value].filter(Boolean).join(' - ');
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
  showFolder(config.作業フォルダ);
  const saved = config.保存モデル設定;
  // 明示した起動設定を優先し、未指定なら最後に手動で選択したモデル・音声を復元する。
  const remember = !config.モデル設定?.[keys(config.モデル設定?.LIVE_AI_NAME).model]
    && (!config.モデル設定?.LIVE_AI_NAME || config.モデル設定.LIVE_AI_NAME === saved?.LIVE_AI_NAME);
  preferredSettings = { ...(remember ? saved : {}), ...config.モデル設定, ...preferredSettings };
  if (Object.keys(preferredSettings).length) {
    settings = { ...settings, ...preferredSettings };
    showModels();
  }
  // 全体起動の接続指定、またはモデル指定がある単独画面は初回に自動接続する。
  return !environment.host && (config.自動接続 === true || !!config.モデル設定?.[keys(config.モデル設定.LIVE_AI_NAME).model]);
}).catch(() => { showError('接続先情報を取得できません。'); return false; }).finally(reveal);
controls();
environment.ready();
void initialContext.then(async automatic => {
  if (generation !== 0) return;
  // セッションを作らず、AiDiy_key.json の既定設定とモデル・音声候補を取得する。
  modelLoading = true; controls();
  try { await loadModels(); }
  catch (error) { if (generation === 0) showError(error instanceof Error ? error.message : String(error)); }
  finally { modelLoading = false; controls(); }
  if (automatic && generation === 0 && !connected && !busy) void connectSession(false, true);
});
