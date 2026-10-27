import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';

// 実コンポーネントのscriptを実行し、Electronから空セッションが返る経路を再現する。
// Vueの描画・通信・ホストだけを置き換え、認証関数自体はコピーしない。
function panel() {
  const source = fs.readFileSync(new URL('../src/タスクチーム/タスクチームパネル.vue', import.meta.url), 'utf8');
  const script = source.match(/<script setup lang="ts">([\s\S]*?)<\/script>/)[1].replace(/^import .*;\r?\n/gm, '');
  let savedToken = '';
  const context = vm.createContext({
    ref: value => ({ value }), onMounted() {}, onBeforeUnmount() {},
    defineProps: () => ({ config: { kind: 'task', taskTeamBase: '/taskteam' } }),
    window: { aidiyWindow: {}, location: { hash: '#task-view=request' } },
    localStorage: { getItem() {}, setItem() {} },
    resolveTaskView: () => 'request', AbortController, setTimeout, clearTimeout,
    token: value => value === undefined ? savedToken : (savedToken = value),
    createTaskSelectionCache: () => ({ dispose() {} }),
    apiClient: { post: async () => ({ data: { status: 'NG', message: '利用者IDまたはパスワードが間違っています' } }) },
  });
  vm.runInContext(ts.transpileModule(script, { compilerOptions: { target: ts.ScriptTarget.ES2022 } }).outputText, context);
  vm.runInContext("sessionSync = { set: async value => receiveSession(value) };", context);
  return { run: text => vm.runInContext(text, context), context };
}

test('Task login rejection remains visible after its empty-session echo', async () => {
  const p = panel();
  await p.run('login()');
  assert.equal(p.run('error.value'), '利用者IDまたはパスワードが間違っています');
  assert.equal(p.run('user.value'), null);
  assert.equal(p.run('busy.value'), false);
  assert.equal(p.run('token()'), '');
  await p.run("receiveSession('')");
  assert.equal(p.run('error.value'), '利用者IDまたはパスワードが間違っています');
});

test('successful login clears rejection; a peer logout clears authenticated state', async () => {
  const p = panel();
  await p.run('login()');
  p.context.apiClient.post = async path => ({ data: { status: 'OK', data: path.endsWith('ログイン') ? { access_token: 'test-only' } : { 利用者ID: 'test-user' } } });
  await p.run('login()');
  assert.equal(p.run('error.value'), '');
  assert.equal(p.run('user.value.利用者ID'), 'test-user');
  await p.run("receiveSession('')");
  assert.equal(p.run('user.value'), null);
  assert.equal(p.run('error.value'), '');
});
