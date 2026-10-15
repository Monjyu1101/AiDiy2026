const test = require('node:test');
const assert = require('node:assert/strict');
const { createRequire } = require('node:module');
const path = require('node:path');
const uiRequire = createRequire(path.join(__dirname, '../../..', 'package.json'));
const { ref, reactive } = uiRequire('vue');
const 状態を作成 = async (api, connected = true) => {
  const { インストール状態を作成 } = await import('../インストール状態.mjs');
  const 接続済み = ref(connected), 通知 = ref('');
  return { ...インストール状態を作成({ api, 接続済み, 通知 }), 接続済み, 通知 };
};
test('未接続・重複クリックを抑止し、診断結果と通知を更新する', async () => {
  let calls = 0, finish;
  const state = await 状態を作成((url, method) => {
    calls++; assert.equal(url, 'api/診断'); assert.equal(method, 'POST');
    return new Promise(resolve => { finish = resolve; });
  }, false);
  await state.インストール確認(); assert.equal(calls, 0);
  state.接続済み.value = true;
  const pending = state.インストール確認(); await state.インストール確認();
  assert.equal(calls, 1); assert.equal(state.確認中.value, true); assert.match(state.通知.value, /確認中/);
  finish({ 結果: [{ id: 'node', 状態: 'OK' }] }); await pending;
  assert.equal(state.確認中.value, false); assert.equal(state.通知.value, '');
  assert.equal(state.結果.value[0].状態, 'OK');
});
test('失敗後も再実行でき、一覧を再接続の応答で置き換える', async () => {
  const state = await 状態を作成(async () => { throw new Error('通信失敗'); });
  state.一覧を反映({ 項目: [{ id: 'node' }], 結果: [], 調査: { complete: true } });
  await state.インストール確認(); assert.equal(state.通知.value, '通信失敗'); assert.equal(state.確認中.value, false);
  state.一覧を反映({ 項目: [], 結果: [] });
  assert.deepEqual(state.項目.value, []); assert.deepEqual(state.調査.value, {});
});
test('選択・詳細・参照重複除外・分類開閉は結果更新後も保持する', async () => {
  const { インストール表示を作成 } = await import('../インストール表示.mjs');
  const props = reactive({ 項目: [{ id: 'node', name: 'Node.js', commands: ['node'], usageTier: 'base', minimumVersion: '18', evidence: [{ path: 'a', line: 1 }, { path: 'a', line: 1 }] }], 結果: [] });
  const view = インストール表示を作成(props);
  assert.deepEqual(view.分類, ['ベース', 'CLI群', 'その他拡張']);
  assert.equal(view.選択項目.value, undefined); assert.equal(view.状態('node'), '未確認');
  view.選択ID.value = 'node'; assert.deepEqual(view.参照箇所.value, ['a:1']);
  assert.ok(view.詳細項目.value.some(([label, value]) => label === '必要バージョン' && value.includes('18')));
  props.結果 = [{ id: 'node', 状態: 'OK', バージョン: 'v22' }];
  assert.equal(view.状態('node'), 'OK'); assert.equal(view.選択ID.value, 'node');
  view.開閉('その他拡張', { target: { open: true } }); assert.equal(view.折り畳み.value.has('その他拡張'), false);
  view.開閉('その他拡張', { target: { open: false } }); assert.equal(view.折り畳み.value.has('その他拡張'), true);
});
