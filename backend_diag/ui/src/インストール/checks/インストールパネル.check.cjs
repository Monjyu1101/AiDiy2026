const test = require('node:test');
const assert = require('node:assert/strict');
const { render, source } = require('../../../../checks/ui-components.cjs');

test('install list keeps categories and badges without search, legend or state filter', async () => {
  const html = await render('インストール/インストールパネル.vue', {
    項目: [{ id: 'node', name: 'Node.js', description: 'runtime', commands: ['node'], category: 'base', menuGroup: 'ベース' }],
    結果: [{ id: 'node', 状態: 'OK' }], 確認中: false, 接続済み: true,
  });
  assert.match(html, /id="install-run"/);
  assert.match(html, /<button id="install-write" disabled[^>]*>書込<\/button>/);
  assert.match(html, /ベース/);
  assert.doesNotMatch(html, /class="legend"|<select|状態で絞り込む|<input|プログラムを検索/);
  assert.equal((html.match(/data-state="OK"/g) || []).length, 1);
});

test('write button is enabled only after a completed check', async () => {
  const props = { 項目: [{ id: 'node', name: 'Node.js', commands: ['node'], menuGroup: 'ベース' }], 結果: [{ id: 'node', 状態: 'OK' }], 確認中: false, 接続済み: true, 確認済み: true, 書込中: false, 書込済み: false };
  assert.match(await render('インストール/インストールパネル.vue', props), /<button id="install-write"[^>]*>書込<\/button>/);
  assert.doesNotMatch(await render('インストール/インストールパネル.vue', props), /id="install-write" disabled/);
  assert.match(await render('インストール/インストールパネル.vue', { ...props, 書込済み: true }), />書込済<\/button>/);
  assert.match(await render('インストール/インストールパネル.vue', { ...props, 確認中: true }), /id="install-write" disabled/);
});

test('エラーは共通通知欄へ表示する', () => {
  const controller = source('インストール/インストール状態.mjs');
  assert.match(controller, /catch \(error\) \{ 結果.value = 前回; 通知.value = error.message;/);
  assert.match(source('App.vue'), /<p v-if="message" id="message" role="status"/);
});
