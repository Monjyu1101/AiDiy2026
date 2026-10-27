// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1". See LICENSE for full terms.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { parse, compileScript } from '@vue/compiler-sfc';
import { transform } from 'esbuild';
import * as Vue from 'vue';
import * as sessionTools from '../src/タスクチーム/task-session.js';
const source = await readFile(new URL('../src/タスクチーム/タスクチームパネル.vue', import.meta.url), 'utf8');
let script = compileScript(parse(source).descriptor, { id: 'taskteam-test' }).content;
script = script.replace(/import\s+(?:\{[^}]*\}|[\w,\s]+)\s+from\s+['"]vue['"];?/g, match => {
  const binding = match.match(/import\s+(.*?)\s+from/s)[1].replace(/\s+as\s+/g, ': ');
  return `const ${binding} = Vue;`;
});
script = script.replace(/import StatusBar[^;]+;/, 'const StatusBar = {};').replace(/import TaskPanel[^;]+;/, 'const TaskPanel = {};').replace(/import TeamPanel[^;]+;/, 'const TeamPanel = {};');
script = script.replace(/import Task(?:Request|Flow|Detail|Editor)[^;]+;/g, match => 'const ' + match.match(/import (\w+)/)[1] + ' = {};');
script = script.replace(/import \{ resolveTaskView, createTaskSession, createTaskSelectionCache \}[^;]+;/, 'const { resolveTaskView, createTaskSession, createTaskSelectionCache } = sessionTools;');
script = script.replace(/import apiClient[^;]+;/, 'const { apiClient, token } = bridge;').replace('export default', 'return');
const compiled = await transform(script, { loader: 'ts', target: 'esnext' });
const componentFactory = new Function('Vue', 'bridge', 'sessionTools', compiled.code);
const renderer = Vue.createRenderer({
  createElement: () => ({}), createText: () => ({}), createComment: () => ({}),
  setText() {}, setElementText() {}, parentNode: () => null, nextSibling: () => null,
  insert() {}, remove() {}, patchProp() {},
});
const flush = async () => { await Promise.resolve(); await Vue.nextTick(); await Promise.resolve(); await Vue.nextTick(); };
function mount({ stored = '', health = true, desktopApi = null, view = '' } = {}) {
  let value = stored, healthSignal;
  const calls = [];
  const bridge = { token: input => { if (input !== undefined) value = input; return value; }, apiClient: { post: async (path, body) => {
    calls.push({ path, body });
    if (path.endsWith('/ログイン')) return { data: { status: 'OK', data: { access_token: 'test-token' } } };
    return { data: { status: 'OK', data: { 利用者ID: 'test', 利用者名: 'Test', 権限ID: 'admin' } } };
  } } };
  globalThis.window = new EventTarget(); window.location = { hash: view ? '#task-view=' + view : '' }; if (desktopApi) window.aidiyWindow = desktopApi;
  globalThis.fetch = async (url, options) => { healthSignal = options.signal; assert.equal(url, '/taskteam-api/status'); return { ok: true, json: async () => ({ connected: health, port: 9003 }) }; };
  const component = componentFactory(Vue, bridge, sessionTools); component.render = () => null;
  const app = renderer.createApp(component, { config: { kind: 'task', taskTeamBase: '/taskteam-api' } });
  const instance = app.mount({});
  return { app, state: instance.$.setupState, calls, bridge, signal: () => healthSignal };
}
test('actual Vue setup logs in, loads user and clears password; logout tears down authenticated state', async () => {
  const run = mount(); await flush();
  assert.equal(run.state.connected, true); assert.equal(run.state.port, 9003);
  run.state.userId = 'test'; run.state.password = 'password'; await run.state.login();
  assert.equal(run.state.user.利用者ID, 'test'); assert.equal(run.state.password, ''); assert.equal(run.bridge.token(), 'test-token');
  assert.equal(run.calls[0].path, '/core/auth/ログイン'); assert.equal(run.calls[1].path, '/core/auth/現在利用者');
  run.state.logout(); assert.equal(run.state.user, null); assert.equal(run.bridge.token(), '');
  run.app.unmount(); assert.equal(run.signal().aborted, true);
});
test('actual Vue setup restores a session and handles expiry independently of backend health', async () => {
  const run = mount({ stored: 'saved', health: false }); await flush();
  assert.equal(run.state.user.利用者ID, 'test'); assert.equal(run.state.connected, false); assert.equal(run.state.restoring, false);
  window.dispatchEvent(new Event('taskteam-auth-expired')); assert.equal(run.state.user, null); assert.equal(run.bridge.token(), '');
  assert.match(run.state.error, /有効期限/); run.app.unmount();
});
test('disposal prevents a late login response from restoring session state', async () => {
  const run = mount(); await flush(); let respond;
  run.bridge.apiClient.post = () => new Promise(resolve => { respond = resolve; });
  const login = run.state.login(); run.app.unmount();
  respond({ data: { status: 'OK', data: { access_token: 'late' } } }); await login;
  assert.equal(run.bridge.token(), ''); assert.equal(run.state.user, null);
});

test('each desktop peer restores host authentication, exposes closed views and never automatically reopens all', async () => {
  const actions = []; let sessionCallback;
  const api = {
    onTaskSession(callback) { sessionCallback = callback; return () => {}; },
    taskSession: async action => ({ ok: true, revision: 1, token: 'shared' }),
    taskWindows: async (action, payload) => { actions.push({ action, payload }); return { ok: true, views: ['flow', 'detail'] }; },
  };
  const run = mount({ desktopApi: api, view: 'flow' }); await flush(); await flush();
  assert.equal(run.state.taskView, 'flow'); assert.equal(run.state.user.利用者ID, 'test');
  assert.deepEqual(run.state.openViews, ['flow', 'detail']); assert.equal(actions.some(item => item.action === 'open-all'), false);
  await run.state.openTaskWindows('request'); assert.deepEqual(actions.find(item => item.action === 'open'), { action: 'open', payload: { view: 'request' } });
  sessionCallback({ revision: 2, token: '' }); await flush(); assert.equal(run.state.user, null); assert.equal(run.bridge.token(), '');
  run.app.unmount();
});
