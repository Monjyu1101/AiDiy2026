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
  const editable = loaded && !fatal && ['idle', 'error'].includes(state.phase);
  for (const input of [provider, model, voice, codeProvider, codeModel]) input.disabled = !editable || saving;
  toggle.disabled = !loaded || fatal || saving || state.phase === 'stopping' || editable && !model.value.trim();
  toggle.textContent = ['connecting', 'connected', 'reconnecting'].includes(state.phase) ? '停止' : state.phase === 'stopping' ? '停止中' : '開始';
  toggle.dataset.stop = String(!editable);
}
function showState(value) { state = value; fatal ||= !!value.fatal; el('dot').dataset.phase = value.phase; el('status-text').textContent = value.message; controls(); }
function options(select, values, selected) {
  select.replaceChildren();
  if (selected && !(selected in values)) values = { [selected]: selected, ...values };
  for (const [value, label] of Object.entries(values)) select.add(new Option(label, value));
  if (selected) select.value = selected;
}
function showModels() {
  const [modelKey, voiceKey] = keys[provider.value];
  options(voice, voices[provider.value] || {}, settings[voiceKey]);
  model.value = settings[modelKey] || Object.keys(models[provider.value] || {})[0] || '';
  el('models').replaceChildren(...Object.entries(models[provider.value] || {}).map(([value, label]) => new Option(label, value)));
  controls();
}
function selection() {
  const [modelKey, voiceKey] = keys[provider.value];
  return { LIVE_AI_NAME: provider.value, [modelKey]: model.value.trim(), ...(voice.value ? { [voiceKey]: voice.value } : {}) };
}
function save() {
  const value = selection();
  if (!model.value.trim()) { note('モデル名を指定してください。', true); controls(); return Promise.resolve(false); }
  saving = true; controls();
  saveQueue = saveQueue.then(async () => {
    try {
      Object.assign(settings, await api.select(value));
      await api.selectCode({ provider: codeProvider.value, model: codeModel.value.trim() });
      note('選択を保存しました。次回もこのモデル・音声を使用します。'); return true;
    }
    catch { note('選択を保存できませんでした。保存先を確認して再試行してください。', true); return false; }
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
api.onState(showState);
api.initial().then(data => {
  settings = data.settings; models = data.models; voices = data.voices;
  options(provider, labels, settings.LIVE_AI_NAME || 'freeai_live');
  options(codeProvider, { '': '自動選択', [data.code.provider]: data.code.provider || '自動選択' }, data.code.provider);
  codeModel.value = data.code.model;
  codeModel.placeholder = '未指定時はコード AI の既定モデル';
  loaded = true; showModels(); showState(data.state);
  if (data.notice) note(data.notice);
  void api.catalogCode('').then(catalog => {
    const selected = codeProvider.value;
    options(codeProvider, { '': '自動選択', ...Object.fromEntries((catalog.providers || []).map(item => [item.id, item.label])) }, selected);
  }).catch(() => {});
  void codeModels();
}).catch(error => { note('共通設定を確認し、パネルを開き直してください。', true); showState({ phase: 'error', message: error.message }); });
