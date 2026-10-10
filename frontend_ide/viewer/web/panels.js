// -*- coding: utf-8 -*-
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026

const $ = id => document.getElementById(id);
let session = '', mode = '', opened = false, selected = 'code', revision = 0;
const frames = new Map();
function remove(kind) {
  frames.get(kind)?.remove(); frames.delete(kind);
}
function display() {
  $('ai-panel').hidden = !opened;
  $('ai-toggle').setAttribute('aria-expanded', String(opened));
  for (const kind of ['code', 'live']) {
    $(`ai-${kind}`).hidden = selected !== kind;
    $(`ai-${kind}-tab`).setAttribute('aria-selected', String(selected === kind));
    $(`ai-${kind}-tab`).tabIndex = selected === kind ? 0 : -1;
  }
}
export function updatePanels(state) {
  const next = state.active ? `${state.mode}:${state.startedAt}` : '';
  if (session !== next) {
    revision++; session = next; opened = false; selected = 'code';
    remove('code'); remove('live'); $('ai-error').hidden = true;
  }
  mode = state.mode;
  $('ai-toggle').textContent = mode === 'offline' ? '☰ Code' : '☰ Code / Live';
  $('ai-live-tab').hidden = mode !== 'online';
  display();
}
async function show(kind) {
  if (!session || (kind === 'live' && mode !== 'online')) return;
  const run = ++revision;
  selected = kind; opened = true;
  if (kind !== 'live') remove('live'); // 音声入力を非表示のまま残さない。
  display(); $('ai-error').hidden = true;
  if (frames.has(kind)) return;
  try {
    const response = await fetch(`/api/panels/${kind}`, { method: 'POST' });
    if (!response.ok) throw new Error(await response.text());
    const { url } = await response.json();
    if (run !== revision || !opened) return;
    const frame = document.createElement('iframe');
    frame.title = kind === 'code' ? 'AiDiy Code' : 'AiDiy Live 音声会話';
    frame.allow = kind === 'live' ? "microphone 'self'; autoplay 'self'" : "clipboard-write 'self'";
    frame.src = url;
    frame.addEventListener('load', () => {
      // 単独版の接続モード操作は親画面に集約する。
      const auto = frame.contentDocument?.getElementById('auto-connect');
      if (auto) auto.style.display = 'none';
    });
    frames.set(kind, frame); $(`ai-${kind}`).append(frame);
  } catch (error) {
    if (run !== revision) return;
    $('ai-error').textContent = error.message; $('ai-error').hidden = false;
  }
}
function close() {
  revision++; opened = false; remove('live'); display(); $('ai-toggle').focus();
}
$('ai-toggle').onclick = () => opened ? close() : show(selected);
$('ai-close').onclick = close;
for (const kind of ['code', 'live']) {
  $(`ai-${kind}-tab`).onclick = () => show(kind);
  $(`ai-${kind}-tab`).onkeydown = event => {
    if (mode === 'online' && ['ArrowLeft', 'ArrowRight'].includes(event.key)) {
      event.preventDefault(); const next = kind === 'code' ? 'live' : 'code';
      void show(next); $(`ai-${next}-tab`).focus();
    }
  };
}
