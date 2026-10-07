'use strict';
const api = window.discordPanel;
const el = id => document.getElementById(id);
const provider = el('provider'), model = el('model'), voice = el('voice'), toggle = el('toggle');
const codeProvider = el('code-provider'), codeModel = el('code-model');
const keys = { freeai_live: ['LIVE_FREEAI_MODEL', 'LIVE_FREEAI_VOICE'], gemini_live: ['LIVE_GEMINI_MODEL', 'LIVE_GEMINI_VOICE'], openai_live: ['LIVE_OPENAI_MODEL', 'LIVE_OPENAI_VOICE'] };
const labels = { freeai_live: 'FreeAI Live', gemini_live: 'Gemini Live', openai_live: 'OpenAI Live' };
let settings = {}, models = {}, voices = {}, state = { phase: 'idle' }, loaded = false, saving = false, fatal = false;
let saveQueue = Promise.resolve();
let catalogGeneration = 0;
function note(text, error = false) { el('note').textContent = text; el('note').classList.toggle('error', error); }
function controls() {
  document.body.classList.toggle('connected', state.phase === 'connected');
  document.body.classList.toggle('live-view', ['connected', 'reconnecting'].includes(state.phase));
  const editable = loaded && !fatal && ['idle', 'error'].includes(state.phase);
  for (const input of [provider, model, voice, codeProvider, codeModel]) input.disabled = !editable || saving;
  toggle.disabled = !loaded || fatal || saving || state.phase === 'stopping' || editable && (!model.value || !voice.value);
  toggle.textContent = state.phase === 'connecting' ? '接続中…' : ['connected', 'reconnecting'].includes(state.phase) ? '切断' : state.phase === 'stopping' ? '切断中…' : '接続';
  toggle.classList.toggle('awaiting', editable);
}
const phaseLabels = { idle: '未接続', connecting: '接続中', connected: '接続済み', reconnecting: '再接続中', stopping: '切断中', error: 'エラー' };
let stateNote = false;
function showState(value) {
  state = value; fatal ||= !!value.fatal;
  // 左上はaidiy_liveと同じく短い状態名だけ。エラーの内容は下の案内欄に出す。
  el('dot').dataset.phase = value.phase; el('status-text').textContent = phaseLabels[value.phase] || value.phase;
  if (value.phase === 'error' && value.message) { note(value.message, true); stateNote = true; }
  else if (stateNote) { note(''); stateNote = false; }
  if (!['connected', 'reconnecting'].includes(value.phase)) { stageClear(); meterReset(); monitorStop(); }
  el('error-detail').value = value.details || ''; el('error-detail').hidden = !value.details;
  if (value.details) el('error-detail').scrollIntoView({ block: 'nearest' });
  controls();
}
function options(select, values, selected) {
  select.replaceChildren();
  if (selected && !(selected in values)) values = { [selected]: selected, ...values };
  for (const [value, label] of Object.entries(values)) select.add(new Option(label, value));
  if (selected) select.value = selected;
}
function showModels() {
  const [modelKey, voiceKey] = keys[provider.value];
  liveOptions(voice, voices[provider.value] || {}, settings[voiceKey]);
  liveOptions(model, models[provider.value] || {}, settings[modelKey]);
  controls();
}
function liveOptions(select, values, selected) {
  select.replaceChildren();
  const missing = !!selected && !Object.hasOwn(values, selected);
  if (missing || !Object.keys(values).length) {
    const placeholder = new Option('候補から選択してください', '');
    placeholder.disabled = true; select.add(placeholder);
  }
  for (const [value, label] of Object.entries(values)) select.add(new Option(label, value));
  if (selected) select.value = missing ? '' : selected;
}
function selection() {
  const [modelKey, voiceKey] = keys[provider.value];
  return { LIVE_AI_NAME: provider.value, [modelKey]: model.value.trim(), ...(voice.value ? { [voiceKey]: voice.value } : {}) };
}
function save() {
  const value = selection();
  if (!model.value || !voice.value) { note('モデルと音声を候補から選択してください。', true); controls(); return Promise.resolve(false); }
  saving = true; controls();
  saveQueue = saveQueue.then(async () => {
    try {
      Object.assign(settings, await api.select(value));
      await api.selectCode({ provider: codeProvider.value, model: codeModel.value.trim() });
      note('選択を保存しました。次回もこのモデル・音声を使用します。'); return true;
    }
    catch (error) { note(error.message || '選択を保存できませんでした。保存先を確認して再試行してください。', true); return false; }
    finally { saving = false; controls(); }
  });
  return saveQueue;
}
provider.onchange = () => { settings.LIVE_AI_NAME = provider.value; showModels(); void save(); };
model.oninput = controls;
model.onchange = voice.onchange = () => { void save(); };
async function codeModels() {
  const run = ++catalogGeneration, name = codeProvider.value;
  el('code-models').replaceChildren();
  if (!name) return;
  try {
    const result = await api.catalogCode(name);
    if (run !== catalogGeneration || name !== codeProvider.value) return;
    el('code-models').replaceChildren(...(result.models || []).map(item => new Option(item.label, item.id)));
  } catch { if (run === catalogGeneration) note('コードモデルの候補を取得できません。モデル名を直接入力できます。'); }
}
codeProvider.onchange = () => { codeModel.value = ''; void save(); void codeModels(); };
codeModel.onchange = () => { void save(); };
toggle.onclick = async () => {
  try {
    if (['connecting', 'connected', 'reconnecting'].includes(state.phase)) await api.stop();
    else if (await save()) await api.start();
  } catch { note('操作できませんでした。設定を確認して再試行してください。', true); }
};
el('minimize').onclick = () => api.window('minimize');
el('close').onclick = async () => { await saveQueue; await api.window('close'); };
// 接続中の背景に、aidiy_live と同じ円型インジケーターで通過する入力（赤）・再生音（水色）を描く。
// 小型パネルでは aidiy_live の半径だと小さいため、少し大きく、やや下寄りに描く。
const cloud = new AudioCloud(el('audio-cloud'), (width, height) => ({ x: width / 2, y: height * .58, radius: Math.min(width * .3, height * .3, 150) }));
function meterReset() { for (const kind of ['input', 'output']) { cloud.level(kind, 0); cloud.spectrum(kind, new Uint8Array(0)); } }
api.onMeter(value => {
  if (!['input', 'output'].includes(value?.kind) || !document.body.classList.contains('live-view')) return;
  cloud.level(value.kind, Math.max(0, Math.min(1, Number(value.level) || 0)));
  cloud.spectrum(value.kind, Uint8Array.from(Array.isArray(value.bins) ? value.bins : []));
});
// モニター: ON の間だけ worker から届く通過音声（入力・AI の声、PCM16 mono）をこの PC で再生する。
// 接続ごとに OFF から始める。スピーカーの音を Discord のマイクが拾うとエコーになるため既定では鳴らさない。
let monitorContext, monitorNext = { input: 0, output: 0 };
function monitorShow(on) { el('monitor').setAttribute('aria-checked', String(on)); el('monitor-state').textContent = on ? 'ON' : 'OFF'; }
function monitorStop() {
  if (monitorContext) void monitorContext.close().catch(() => {});
  monitorContext = undefined; monitorNext = { input: 0, output: 0 }; monitorShow(false);
}
el('monitor').onclick = async () => {
  const on = !monitorContext;
  try {
    if (on) { monitorContext = new AudioContext(); monitorShow(true); }
    else monitorStop();
    await api.monitor(on);
  } catch { monitorStop(); note('モニターを切り替えられませんでした。', true); }
};
api.onAudio(value => {
  const context = monitorContext;
  if (!context || !['input', 'output'].includes(value?.kind) || ![16000, 24000].includes(value.rate) || typeof value.data !== 'string') return;
  const bytes = Uint8Array.from(atob(value.data), char => char.charCodeAt(0));
  const samples = new Int16Array(bytes.buffer, 0, bytes.length >> 1);
  if (!samples.length) return;
  const buffer = context.createBuffer(1, samples.length, value.rate), channel = buffer.getChannelData(0);
  for (let i = 0; i < samples.length; i++) channel[i] = samples[i] / 32768;
  const now = context.currentTime;
  // 届いた順に隙間なく並べる。遅れが1秒を超えたら追いつくため捨てる。
  const start = Math.max(monitorNext[value.kind], now + .08);
  if (start - now > 1) return;
  const source = context.createBufferSource();
  source.buffer = buffer; source.connect(context.destination); source.start(start);
  monitorNext[value.kind] = start + buffer.duration;
});
// 接続中は最後のやり取りだけを aidiy_live の回答と同じターミナル演出で1回表示し、約1分で消す。
let typingTimer, clearTimer;
function stageClear() {
  clearTimeout(typingTimer); clearTimeout(clearTimer);
  el('stage-message').hidden = true; el('stage-message').classList.remove('fading'); el('stage-idle').hidden = false;
}
api.onActivity(value => {
  clearTimeout(typingTimer); clearTimeout(clearTimer);
  const message = el('stage-message'), output = el('stage-text');
  el('stage-idle').hidden = true; message.hidden = false; message.classList.remove('fading');
  message.dataset.role = value.role === 'user' ? 'user' : 'ai';
  el('stage-who').textContent = value.who;
  const text = String(value.text || '');
  clearTimer = setTimeout(() => { message.classList.add('fading'); clearTimer = setTimeout(stageClear, 600); }, 60_000);
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) { output.textContent = text; return; }
  const typed = document.createElement('span'), cursor = document.createElement('span');
  cursor.className = 'terminal-cursor'; output.replaceChildren(typed, cursor);
  // Code / Live の回答表示と同じく、500ms 待ってから10msごとに文字を追加する（約0.5秒で全文）。
  const batch = Math.max(1, Math.floor(text.length / 50) + 1);
  let index = 0;
  const tick = () => {
    index = Math.min(index + batch, text.length); typed.textContent = text.slice(0, index);
    output.scrollTop = output.scrollHeight;
    if (index < text.length) typingTimer = setTimeout(tick, 10);
    else output.textContent = text;
  };
  typingTimer = setTimeout(tick, 500);
});
api.onState(showState);
api.initial().then(data => {
  settings = data.settings; models = data.models; voices = data.voices;
  options(provider, labels, settings.LIVE_AI_NAME || 'freeai_live');
  options(codeProvider, { '': '自動選択', [data.code.provider]: data.code.provider || '自動選択' }, data.code.provider);
  codeModel.value = data.code.model;
  el('project-folder').textContent = data.folder?.name || ''; el('project-folder').title = data.folder?.path || '';
  codeModel.placeholder = '未指定時はコード AI の既定モデル';
  loaded = true; showModels(); showState(data.state);
  if (data.notice) note(data.notice);
  void api.catalogCode('').then(catalog => {
    const selected = codeProvider.value;
    options(codeProvider, { '': '自動選択', ...Object.fromEntries((catalog.providers || []).map(item => [item.id, item.label])) }, selected);
  }).catch(() => {});
  void codeModels();
}).catch(error => { showState({ phase: 'error', message: `${error.message || ''} 共通設定を確認し、パネルを開き直してください。`.trim() }); });
