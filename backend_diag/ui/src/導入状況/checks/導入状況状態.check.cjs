const test = require('node:test');
const assert = require('node:assert/strict');
const { createRequire } = require('node:module');
const path = require('node:path');
const uiRequire = createRequire(path.join(__dirname, '../../..', 'package.json'));
const { ref, reactive, watch } = uiRequire('vue');
const 状態を作成 = async (api, connected = true) => {
  const { 導入状況状態を作成 } = await import('../導入状況状態.mjs');
  const 接続済み = ref(connected), 通知 = ref('');
  return { ...導入状況状態を作成({ api, 接続済み, 通知, 間隔: 0 }), 接続済み, 通知 };
};
const 一覧 = { 項目: [{ id: 'ffmpeg' }, { id: 'claude', menuGroup: 'CLI群' }, { id: 'node', menuGroup: 'ベース' }], 結果: [] };
test('未接続・重複クリックを抑止し、全項目を確認中にしてから結果へ切り替える', async () => {
  let calls = 0, finish;
  const state = await 状態を作成((url, method) => {
    calls++; assert.equal(url, 'api/診断'); assert.equal(method, 'POST');
    return new Promise(resolve => { finish = resolve; });
  }, false);
  state.一覧を反映(一覧);
  assert.equal(await state.状況確認(), false); assert.equal(calls, 0);
  state.接続済み.value = true;
  const pending = state.状況確認(); await state.状況確認();
  assert.equal(calls, 1); assert.equal(state.確認中.value, true); assert.equal(state.通知.value, '');
  assert.deepEqual(state.結果.value.map(r => r.状態), ['確認中', '確認中', '確認中']);
  finish({ 結果: 一覧.項目.map(e => ({ id: e.id, 状態: 'OK' })) });
  assert.equal(await pending, true);
  assert.equal(state.確認中.value, false); assert.equal(state.確認済み.value, true);
  assert.deepEqual(state.結果.value.map(r => r.状態), ['OK', 'OK', 'OK']);
});
test('結果は画面の上から順（ベース→CLI群→その他拡張）に反映する', async () => {
  const seen = [];
  const state = await 状態を作成(async () => ({ 結果: 一覧.項目.map(e => ({ id: e.id, 状態: 'OK' })) }));
  state.一覧を反映(一覧);
  const stop = watch(state.結果, value => seen.push(value.filter(r => r.状態 === 'OK').map(r => r.id).join(',')), { flush: 'sync' });
  await state.状況確認(); stop();
  assert.deepEqual(seen.slice(1, 4), ['node', 'claude,node', 'ffmpeg,claude,node']);
});
test('書込は確認後だけ実行し、全テストは確認してから書き込む', async () => {
  const calls = [];
  const state = await 状態を作成(async url => { calls.push(url); return url === 'api/診断' ? { 結果: 一覧.項目.map(e => ({ id: e.id, 状態: 'OK' })) } : { 件数: 3 }; });
  state.一覧を反映(一覧);
  assert.equal(await state.書込(), false); assert.deepEqual(calls, []);
  assert.equal(await state.全テスト(), true);
  assert.deepEqual(calls, ['api/診断', 'api/書込']); assert.equal(state.書込済み.value, true);
  state.一覧を反映(一覧); assert.equal(state.確認済み.value, false); assert.equal(state.書込済み.value, false);
});
test('確認失敗では前回の結果へ戻し、書込はできない。書込失敗は通知する', async () => {
  const state = await 状態を作成(async () => { throw new Error('通信失敗'); });
  state.一覧を反映({ 項目: [{ id: 'node' }], 結果: [{ id: 'node', 状態: '未検出' }], 調査: { complete: true } });
  assert.equal(await state.全テスト(), false); assert.equal(state.通知.value, '通信失敗'); assert.equal(state.確認中.value, false);
  assert.deepEqual(state.結果.value, [{ id: 'node', 状態: '未検出' }]); assert.equal(state.確認済み.value, false);
  const writer = await 状態を作成(async url => { if (url === 'api/書込') throw new Error('書き込みに失敗しました。'); return { 結果: [{ id: 'node', 状態: 'OK' }] }; });
  writer.一覧を反映({ 項目: [{ id: 'node' }], 結果: [] });
  assert.equal(await writer.全テスト(), false); assert.equal(writer.通知.value, '書き込みに失敗しました。'); assert.equal(writer.書込済み.value, false);
  state.一覧を反映({ 項目: [], 結果: [] });
  assert.deepEqual(state.項目.value, []); assert.deepEqual(state.調査.value, {});
});
test('選択・詳細・参照重複除外・分類開閉は結果更新後も保持する', async () => {
  const { 導入状況表示を作成 } = await import('../導入状況表示.mjs');
  const props = reactive({ 項目: [{ id: 'node', name: 'Node.js', commands: ['node'], usageTier: 'base', minimumVersion: '18', evidence: [{ path: 'a', line: 1 }, { path: 'a', line: 1 }] }], 結果: [] });
  const view = 導入状況表示を作成(props);
  assert.deepEqual(view.分類, ['ベース', 'CLI群', 'その他拡張']);
  assert.equal(view.選択項目.value, undefined); assert.equal(view.状態('node'), '未確認');
  view.選択ID.value = 'node'; assert.deepEqual(view.参照箇所.value, ['a:1']);
  assert.ok(view.詳細項目.value.some(([label, value]) => label === '必要バージョン' && value.includes('18')));
  props.結果 = [{ id: 'node', 状態: 'OK', バージョン: 'v22' }];
  assert.equal(view.状態('node'), 'OK'); assert.equal(view.選択ID.value, 'node');
  view.開閉('その他拡張', { target: { open: true } }); assert.equal(view.折り畳み.value.has('その他拡張'), false);
  view.開閉('その他拡張', { target: { open: false } }); assert.equal(view.折り畳み.value.has('その他拡張'), true);
});
test('演出中は表示中の項目へ選択（右側の詳細）を順に切り替え、閉じた分類を開く', async () => {
  const order = [];
  const state = await 状態を作成(async () => ({ 結果: 一覧.項目.map(e => ({ id: e.id, 状態: 'OK' })) }));
  state.一覧を反映(一覧);
  const stop = watch(state.表示中, id => order.push(id), { flush: 'sync' });
  await state.状況確認(); stop();
  assert.deepEqual(order, ['node', 'claude', 'ffmpeg']);
  const { 導入状況表示を作成 } = await import('../導入状況表示.mjs');
  const props = reactive({ 項目: 一覧.項目, 結果: [], 表示中: null });
  const view = 導入状況表示を作成(props);
  assert.equal(view.折り畳み.value.has('その他拡張'), true);
  props.表示中 = 'claude'; await Promise.resolve(); assert.equal(view.選択ID.value, 'claude');
  props.表示中 = 'ffmpeg'; await Promise.resolve(); assert.equal(view.選択ID.value, 'ffmpeg'); assert.equal(view.折り畳み.value.has('その他拡張'), false);
});
