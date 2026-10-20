/*!
 * -*- coding: utf-8 -*-
 *
 * -------------------------------------------------------------------------
 * COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
 * Licensed under "AiDiy 公開利用ライセンス v1.1".
 * Commercial use requires prior written consent from all copyright holders.
 * See LICENSE for full terms. Thank you for keeping the rules.
 * https://github.com/monjyu1101/AiDiy2026
 * -------------------------------------------------------------------------
 */

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { Window } from 'happy-dom';

const bundle = readFileSync(new URL('../panel/view.js', import.meta.url), 'utf8');
const initial = () => ({
  features: { live: true, code: true },
  settings: { LIVE_AI_NAME: 'freeai_live', LIVE_FREEAI_MODEL: 'live-a', LIVE_FREEAI_VOICE: 'voice-a', LIVE_OPENAI_MODEL: 'gone', LIVE_OPENAI_VOICE: 'voice-b' },
  models: { freeai_live: { 'live-a': 'モデル A', 'live-b': 'モデル B' }, openai_live: { 'open-a': 'Open A' } },
  voices: { freeai_live: { 'voice-a': '音声 A' }, openai_live: { 'voice-b': '音声 B' } },
  code: { provider: 'aidiy_hermes', model: 'code-a' }, folder: { name: 'sample', path: '/sample' }, state: { phase: 'idle' },
});
const flush = async () => { for (let i = 0; i < 20; i++) await Promise.resolve(); };
function deferred() { let resolve!: (value?: any) => void, reject!: (error: Error) => void; const promise = new Promise<any>((a, b) => { resolve = a; reject = b; }); return { promise, resolve, reject }; }
function fixture(overrides: Record<string, any> = {}) {
  const window: any = new Window({ url: 'http://localhost/token/', settings: { enableJavaScriptEvaluation: true, disableJavaScriptFileLoading: true, disableCSSFileLoading: true } });
  const calls: any[][] = [], listeners = new Map<string, Set<Function>>(), contexts: any[] = [];
  let disconnected = 0, cancelled = 0, timerId = 0, now = 0;
  const timers = new Map<number, { at: number; callback: Function }>();
  window.setTimeout = (callback: Function, ms: number) => { const id = ++timerId; timers.set(id, { at: now + ms, callback }); return id; };
  window.clearTimeout = (id: number) => timers.delete(id);
  window.requestAnimationFrame = () => 1; window.cancelAnimationFrame = () => { cancelled++; };
  window.ResizeObserver = class { observe() {} disconnect() { disconnected++; } };
  window.HTMLCanvasElement.prototype.getContext = () => null;
  window.AudioContext = class {
    currentTime = 0; destination = {}; closed = 0; starts: number[] = []; samples: any[] = [];
    constructor() { contexts.push(this); }
    close() { this.closed++; return Promise.resolve(); }
    createBuffer(_channels: number, count: number, rate: number) { const samples = new Float32Array(count); this.samples.push(samples); return { duration: count / rate, getChannelData: () => samples }; }
    createBufferSource() { return { connect() {}, start: (at: number) => this.starts.push(at) }; }
  };
  const api: any = {};
  for (const action of ['select', 'selectFeatures', 'selectCode', 'start', 'stop', 'monitor', 'window']) api[action] = async (value: any) => { calls.push([action, value]); return value; };
  api.initial = async () => initial();
  let pinned = false, maximized = false;
  api.getPinState = async () => ({ pinned, locked: false });
  api.togglePin = async () => { calls.push(['togglePin']); pinned = !pinned; return { pinned, locked: false }; };
  api.isMaximized = async () => maximized;
  api.window = async (value: string) => { calls.push(['window', value]); if (value === 'maximize') maximized = !maximized; };
  api.catalogCode = async (provider: string) => provider ? { models: [{ id: 'code-a', label: 'Code A' }] } : { providers: [{ id: 'aidiy_hermes', label: 'Hermes' }, { id: 'codex_cli', label: 'Codex' }] };
  for (const type of ['State', 'Activity', 'Meter', 'Audio', 'PinState']) api[`on${type}`] = (callback: Function) => { const set = listeners.get(type) || new Set(); set.add(callback); listeners.set(type, set); return () => set.delete(callback); };
  Object.assign(api, overrides); window.discordPanel = api;
  window.document.body.innerHTML = '<div id="app"></div>';
  window.eval(bundle);
  const get = (id: string) => window.document.getElementById(id);
  const emit = async (type: string, value: any) => { for (const fn of listeners.get(type) || []) fn(value); await flush(); };
  const change = async (id: string, value: string) => { get(id).value = value; get(id).dispatchEvent(new window.Event('change', { bubbles: true })); await flush(); };
  const click = async (id: string) => { get(id).click(); await flush(); };
  const tick = async (ms: number) => {
    const end = now + ms;
    for (;;) {
      const next = [...timers].filter(([, timer]) => timer.at <= end).sort((a, b) => a[1].at - b[1].at)[0];
      if (!next) break; now = next[1].at; timers.delete(next[0]); next[1].callback(); await flush();
    }
    now = end;
  };
  const dispose = async () => { window.dispatchEvent(new window.Event('pagehide')); await flush(); await window.happyDOM.close(); };
  return { window, calls, listeners, contexts, get, emit, change, click, tick, dispose, timers, resources: () => ({ disconnected, cancelled }) };
}

test('Vue 配布画面は既存の項目・選択・機能切替と外部設定キーを保つ', async () => {
  const f = fixture();
  try {
    await flush();
    for (const id of ['audio-cloud', 'status', 'dot', 'status-text', 'minimize', 'close', 'activity-bar', 'project-folder', 'toggle', 'features', 'feature-live', 'feature-code', 'settings', 'live-toggle', 'provider', 'voice', 'model', 'code-toggle', 'code-provider', 'code-model', 'code-models', 'error-detail', 'note', 'stage', 'stage-log', 'stage-idle', 'stage-message', 'stage-who', 'stage-text', 'monitor', 'monitor-state']) assert.ok(f.get(id), id);
    assert.equal(f.get('status-text').textContent, '未接続');
    assert.equal(f.get('model').value, 'live-a'); assert.equal(f.get('model').options.length, 2);
    assert.equal(f.get('voice').value, 'voice-a'); assert.equal(f.get('project-folder').title, '/sample');
    assert.equal(f.get('code-toggle').disabled, true); assert.equal(f.get('code-toggle').getAttribute('aria-checked'), 'true');
    assert.equal(f.get('monitor').getAttribute('aria-checked'), 'false');
    await f.change('model', 'live-b');
    assert.deepEqual(JSON.parse(JSON.stringify(f.calls.slice(0, 3))), [['selectFeatures', { live: true, code: true }], ['select', { LIVE_AI_NAME: 'freeai_live', LIVE_FREEAI_MODEL: 'live-b', LIVE_FREEAI_VOICE: 'voice-a' }], ['selectCode', { provider: 'aidiy_hermes', model: 'code-a' }]]);
    await f.change('provider', 'openai_live');
    assert.equal(f.get('model').value, ''); assert.equal(f.get('toggle').disabled, true);
    await f.change('model', 'open-a'); assert.equal(f.get('toggle').disabled, false);
    await f.click('live-toggle');
    assert.equal(f.get('provider').disabled, true); assert.equal(f.get('live-toggle').getAttribute('aria-checked'), 'false');
    assert.equal(f.get('feature-live').querySelector('b').textContent, 'OFF');
    assert.equal(f.get('code-model').disabled, false); assert.equal(f.get('toggle').disabled, false);
    await f.change('code-provider', 'codex_cli');
    assert.equal(f.get('code-model').value, ''); assert.ok(f.calls.some(([name, value]) => name === 'selectCode' && value.provider === 'codex_cli'));
    await f.click('minimize'); await f.click('close');
    assert.deepEqual(f.calls.filter(([name]) => name === 'window'), [['window', 'minimize'], ['window', 'close']]);
  } finally { await f.dispose(); }
});

test('接続・再接続・切断・エラー復旧と連打の保存/起動重複を防ぐ', async () => {
  const gate = deferred(); let starts = 0;
  const f = fixture({ start: async () => { starts++; await gate.promise; } });
  try {
    await flush(); await f.click('toggle'); await f.click('toggle');
    assert.equal(starts, 1);
    await f.emit('State', { phase: 'connecting' }); assert.equal(f.get('toggle').textContent, '接続中…');
    assert.equal(f.get('toggle').disabled, false, 'start 応答待ちでも connecting は停止できる');
    await f.click('toggle'); assert.ok(f.calls.some(([name]) => name === 'stop'));
    gate.resolve(); await flush();
    await f.emit('State', { phase: 'connected' });
    assert.equal(f.get('toggle').textContent, '切断'); assert.equal(f.get('provider').disabled, true);
    assert.ok(f.window.document.body.classList.contains('connected'));
    await f.emit('State', { phase: 'reconnecting' });
    assert.ok(f.window.document.body.classList.contains('live-view')); assert.equal(f.get('status-text').textContent, '再接続中');
    await f.emit('State', { phase: 'stopping' }); assert.equal(f.get('toggle').disabled, true);
    await f.emit('State', { phase: 'error', message: '接続失敗', details: 'コピー可能な詳細' });
    assert.equal(f.get('error-detail').value, 'コピー可能な詳細'); assert.equal(f.get('error-detail').hidden, false);
    assert.equal(f.get('note').textContent, '接続失敗');
    await f.emit('State', { phase: 'idle' });
    assert.equal(f.get('error-detail').hidden, true); assert.equal(f.get('note').textContent, '');
    await f.emit('State', { phase: 'error', fatal: true, message: 'サーバー終了' });
    await f.emit('State', { phase: 'idle' }); assert.equal(f.get('toggle').disabled, true);
  } finally { gate.resolve(); await f.dispose(); }
});

test('音声はモニター ON の間だけ再生し、切断/終了で音声・購読・タイマーを回収する', async () => {
  const f = fixture();
  try {
    await flush(); await f.emit('State', { phase: 'connected' });
    const audio = { kind: 'input', rate: 16000, data: Buffer.from([0, 64, 0, 192]).toString('base64') };
    await f.emit('Audio', audio); assert.equal(f.contexts.length, 0);
    await f.click('monitor'); assert.equal(f.get('monitor-state').textContent, 'ON');
    await f.emit('Audio', audio); assert.equal(f.contexts[0].starts.length, 1);
    assert.deepEqual([...f.contexts[0].samples[0]], [.5, -.5]);
    await f.emit('Audio', { ...audio, data: '%%%%' }); await f.emit('Audio', { ...audio, rate: 48000 });
    assert.equal(f.contexts[0].starts.length, 1);
    await f.emit('Activity', { role: 'user', who: '利用者', text: '<script>hello</script>' });
    assert.equal(f.get('stage-message').hidden, false); await f.tick(1100);
    assert.equal(f.get('stage-text').textContent, '<script>hello</script>'); assert.equal(f.get('stage-text').querySelector('script'), null);
    await f.tick(60_000); assert.equal(f.get('stage-message').hidden, true);
    await f.emit('State', { phase: 'idle' });
    assert.equal(f.contexts[0].closed, 1); assert.equal(f.get('monitor-state').textContent, 'OFF');
    await f.emit('State', { phase: 'connected' }); assert.equal(f.get('monitor-state').textContent, 'OFF');
    await f.click('monitor'); await f.emit('Activity', { who: 'AI', text: 'typing' });
    await f.dispose();
    assert.equal(f.contexts[1].closed, 1); assert.equal(f.timers.size, 0);
    assert.ok([...f.listeners.values()].every(set => set.size === 0)); assert.equal(f.resources().disconnected, 1);
  } finally { await f.dispose(); }
});

test('遅い初期読込は新しい状態通知を上書きせず、終了後の候補応答も無視する', async () => {
  const load = deferred(), catalog = deferred();
  const f = fixture({ initial: () => load.promise, catalogCode: () => catalog.promise });
  try {
    await f.emit('State', { phase: 'error', fatal: true, message: '切断しました' });
    load.resolve(initial()); await flush();
    assert.equal(f.get('status-text').textContent, 'エラー'); assert.equal(f.get('toggle').disabled, true);
    await f.dispose(); catalog.resolve({ models: [], providers: [] }); await flush();
    assert.equal(f.window.document.getElementById('toggle'), null);
  } finally { load.resolve(initial()); catalog.resolve({}); await f.dispose(); }
});

test('選択保存の拒否では起動せず、再試行できる', async () => {
  let reject = true, starts = 0;
  const f = fixture({ selectCode: async () => { if (reject) throw new Error('保存先がありません'); }, start: async () => { starts++; } });
  try {
    await flush(); await f.click('toggle'); assert.equal(starts, 0);
    assert.equal(f.get('note').textContent, '保存先がありません'); assert.equal(f.get('toggle').disabled, false);
    reject = false; await f.click('toggle'); assert.equal(starts, 1);
  } finally { await f.dispose(); }
});

test('ブラウザの戻る/進む復元では再マウントし、購読を重複させずモニターは OFF に戻る', async () => {
  const f = fixture();
  try {
    await flush(); await f.emit('State', { phase: 'connected' }); await f.click('monitor');
    f.window.dispatchEvent(new f.window.Event('pagehide')); await flush();
    assert.ok(f.calls.some(([name, value]) => name === 'monitor' && value === false));
    const restore = new f.window.Event('pageshow'); Object.defineProperty(restore, 'persisted', { value: true });
    f.window.dispatchEvent(restore); await flush();
    assert.equal(f.get('status-text').textContent, '未接続');
    assert.equal(f.get('monitor-state').textContent, 'OFF');
    assert.ok([...f.listeners.values()].every(set => set.size === 1));
    f.window.dispatchEvent(restore); await flush();
    assert.ok([...f.listeners.values()].every(set => set.size === 1));
  } finally { await f.dispose(); }
});


test('Live の候補が欠落していても Code の AI・モデルを保存でき、接続時は Live を検証する', async () => {
  let saved = { provider: 'openai_oauth', model: 'code-a' }, starts = 0;
  const f = fixture({
    initial: async () => ({ ...initial(), settings: { ...initial().settings, LIVE_FREEAI_MODEL: 'removed-live' }, code: saved }),
    catalogCode: async (provider: string) => provider ? { models: [{ id: 'code-b', label: 'Code B' }] }
      : { providers: [{ id: 'openai_oauth', label: 'OpenAI OAuth' }, { id: 'freeai', label: 'FreeAI' }] },
    selectCode: async (value: typeof saved) => { saved = { ...value }; return saved; },
    start: async () => { starts++; },
  });
  try {
    await flush();
    assert.equal(f.get('model').value, '');
    assert.equal(f.get('code-provider').disabled, false);
    await f.change('code-provider', 'freeai');
    assert.deepEqual(JSON.parse(JSON.stringify(saved)), { provider: 'freeai', model: '' });
    f.get('code-model').value = 'code-b';
    f.get('code-model').dispatchEvent(new f.window.Event('input', { bubbles: true }));
    await f.change('code-model', 'code-b');
    assert.deepEqual(JSON.parse(JSON.stringify(saved)), { provider: 'freeai', model: 'code-b' });
    assert.ok(!f.calls.some(([action]) => ['select', 'selectFeatures'].includes(action)), 'Code の変更で Live 設定を保存しない');
    assert.equal(f.get('toggle').disabled, true);
    await f.click('toggle'); assert.equal(starts, 0, 'Live 未選択のまま接続しない');
    await f.change('model', 'live-a');
    await f.click('toggle'); assert.equal(starts, 1);
    assert.deepEqual(JSON.parse(JSON.stringify(saved)), { provider: 'freeai', model: 'code-b' });
  } finally { await f.dispose(); }
});


test('自動選択では無視される Code モデルを編集させず、AI を指定すれば再び入力できる', async () => {
  const f = fixture();
  try {
    await flush();
    await f.change('code-provider', '');
    assert.equal(f.get('code-model').value, '');
    assert.equal(f.get('code-model').disabled, true);
    assert.match(f.get('code-model').placeholder, /コード AI を選択/);
    const saved = f.calls.filter(([action]) => action === 'selectCode').at(-1)?.[1];
    assert.deepEqual(JSON.parse(JSON.stringify(saved)), { provider: '', model: '' });
    await f.change('code-provider', 'codex_cli');
    assert.equal(f.get('code-model').disabled, false);
  } finally { await f.dispose(); }
});

test('モデルまたは音声候補のない Live AI は候補なしと表示して選択を無効にする', async () => {
  const f = fixture({ initial: async () => ({ ...initial(),
    models: { ...initial().models, gemini_live: { 'gemini-a': 'Gemini A' } },
    voices: { ...initial().voices, openai_live: {} },
  }) });
  try {
    await flush();
    const options = Object.fromEntries([...f.get('provider').options].map((item: any) => [item.value, item]));
    assert.equal(options.freeai_live.disabled, false);
    for (const id of ['gemini_live', 'openai_live']) {
      assert.equal(options[id].disabled, true);
      assert.match(options[id].textContent, /候補なし/);
    }
    assert.equal(f.get('model').disabled, false);
    assert.equal(f.get('toggle').disabled, false);
  } finally { await f.dispose(); }
});


test('Code AI を変更した後に古い候補が届いても新しい AI・モデルを上書きしない', async () => {
  const previous = deferred();
  const f = fixture({ catalogCode: async (provider: string) => provider === 'aidiy_hermes' ? previous.promise
    : provider ? { models: [{ id: 'new-code', label: 'New Code' }] }
      : { providers: [{ id: 'aidiy_hermes', label: 'Hermes' }, { id: 'codex_cli', label: 'Codex' }] },
  });
  try {
    await flush();
    await f.change('code-provider', 'codex_cli');
    assert.equal(f.get('code-models').options[0].value, 'new-code');
    previous.resolve({ models: [{ id: 'old-code', label: 'Old Code' }] }); await flush();
    assert.equal(f.get('code-provider').value, 'codex_cli');
    assert.equal(f.get('code-models').options[0].value, 'new-code');
    assert.equal(f.get('code-model').value, '');
  } finally { previous.resolve({ models: [] }); await f.dispose(); }
});

test('保存済み Live AI の候補が消えても無断で切り替えず、候補のある AI へ変更できる', async () => {
  const f = fixture({ initial: async () => ({ ...initial(),
    settings: { ...initial().settings, LIVE_AI_NAME: 'openai_live' },
    models: { freeai_live: initial().models.freeai_live },
  }) });
  try {
    await flush();
    assert.equal(f.get('provider').value, 'openai_live');
    assert.equal(f.get('provider').selectedOptions[0].disabled, true);
    assert.equal(f.get('model').value, ''); assert.equal(f.get('toggle').disabled, true);
    assert.equal(f.calls.length, 0, '初期表示だけで保存済み設定を変更しない');
    await f.change('provider', 'freeai_live');
    assert.equal(f.get('model').value, 'live-a'); assert.equal(f.get('toggle').disabled, false);
    assert.ok(f.calls.some(([name, value]) => name === 'select' && value.LIVE_AI_NAME === 'freeai_live'));
  } finally { await f.dispose(); }
});

test('Discord のタイトル操作は最小化・最大化・ピン・閉じる順で、OFF/ON/ロックを同期する', async () => {
  const f = fixture();
  try {
    await flush();
    assert.deepEqual([...f.window.document.querySelectorAll('.window-actions button')].map((button: any) => button.id), ['minimize', 'maximize', 'pin', 'close']);
    assert.equal(f.get('pin').getAttribute('aria-pressed'), 'false'); assert.equal(f.get('pin').classList.contains('pinned'), false);
    await f.click('pin'); assert.equal(f.get('pin').getAttribute('aria-pressed'), 'true'); assert.equal(f.get('pin').classList.contains('pinned'), true);
    await f.click('pin'); assert.equal(f.get('pin').getAttribute('aria-pressed'), 'false');
    await f.emit('PinState', { pinned: true, locked: true }); assert.equal(f.get('pin').disabled, true); assert.match(f.get('pin').title, /VR/);
    const count = f.calls.filter(([action]) => action === 'togglePin').length;
    await f.click('pin'); assert.equal(f.calls.filter(([action]) => action === 'togglePin').length, count);
    await f.emit('PinState', { pinned: false, locked: false }); assert.equal(f.get('pin').disabled, false); assert.equal(f.get('pin').getAttribute('aria-pressed'), 'false');
    await f.click('maximize'); assert.equal(f.get('maximize').title, '元のサイズに戻す');
    await f.click('maximize'); assert.equal(f.get('maximize').title, '最大化');
    await f.dispose(); assert.equal(f.listeners.get('PinState')?.size, 0);
  } finally { await f.dispose(); }
});

test('Discord の遅いピン初期読込は新しい通知を上書きしない', async () => {
  const gate = deferred(), f = fixture({ getPinState: () => gate.promise });
  try {
    await f.emit('PinState', { pinned: true, locked: true });
    gate.resolve({ pinned: false, locked: false }); await flush();
    assert.equal(f.get('pin').getAttribute('aria-pressed'), 'true'); assert.equal(f.get('pin').disabled, true);
  } finally { gate.resolve({ pinned: false, locked: false }); await f.dispose(); }
});
