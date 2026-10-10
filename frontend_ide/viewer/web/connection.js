// -*- coding: utf-8 -*-
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026

const $ = id => document.getElementById(id);
import { updatePanels } from './panels.js';
let active = false, actionPending = false, polling = false, app, revision = 0;
async function render(state) {
  const nextActive = !!state.active;
  updatePanels(state);
  const changed = active !== nextActive;
  active = nextActive;
  const offline = active && state.mode === 'offline';
  document.body.classList.toggle('connected', !!state.connected);
  document.body.classList.toggle('offline', offline);
  document.body.classList.toggle('workspace-active', active);
  $('workspace').hidden = !active;
  $('workspace').inert = !active;
  $('connection-welcome').hidden = active;
  $('connection-status').textContent = offline ? 'オフライン利用中' : state.connected ? 'AiDiy接続利用中' : state.connecting || actionPending === 'connect' ? '接続中…' : '未接続';
  for (const id of ['core-connect', 'offline-start']) {
    $(id).hidden = active;
    $(id).disabled = !!actionPending || !!state.connecting;
  }
  $('usage-stop').hidden = !active && !state.connecting;
  $('usage-stop').disabled = !!actionPending;
  $('core-connect').textContent = state.connecting || actionPending === 'connect' ? '接続中…' : 'AiDiy接続利用';
  $('connection-error').textContent = state.message || '';
  $('connection-error').hidden = !state.message;
  if (state.project) {
    $('connection-project').textContent = state.project.name;
    $('connection-project').title = state.project.path;
  }
  if (state.backend) $('connection-target').textContent = state.backend;
  if (changed && active) {
    try {
      app ||= await import('./app.js');
      if (active) await app.refreshWorkspace(state.startedAt);
    } catch { $('connection-error').textContent = '画面を読み込めません。再読み込みしてください。'; $('connection-error').hidden = false; }
  }
}
async function status() {
  if (polling || actionPending) return;
  polling = true;
  const run = revision;
  try {
    const response = await fetch('/api/connection', { cache: 'no-store', signal: AbortSignal.timeout(5000) });
    if (!response.ok) throw new Error();
    const state = await response.json();
    if (run === revision) await render(state);
  } catch {
    if (run === revision) await render({ active: false, message: 'AiDiy IDE サーバーに接続できません。起動状態を確認してください。' });
  } finally { polling = false; }
}
async function start(action) {
  if (actionPending) return;
  ++revision;
  actionPending = action;
  for (const id of ['core-connect', 'offline-start', 'usage-stop']) $(id).disabled = true;
  if (action === 'connect') {
    $('core-connect').textContent = '接続中…';
    $('connection-status').textContent = '接続中…';
  }
  if (action === 'disconnect') await render({ active: false });
  let state;
  try {
    const response = await fetch('/api/connection/' + action, { method: 'POST', signal: AbortSignal.timeout(6000) });
    if (!response.ok) throw new Error();
    state = await response.json();
  } catch { state = { active: false, message: 'AiDiy IDE サーバーに接続できません。起動状態を確認してください。' }; }
  finally { actionPending = false; }
  await render(state);
}
$('core-connect').onclick = () => start('connect');
$('offline-start').onclick = () => start('offline');
$('usage-stop').onclick = () => start('disconnect');
setInterval(status, 1000);
await status();
