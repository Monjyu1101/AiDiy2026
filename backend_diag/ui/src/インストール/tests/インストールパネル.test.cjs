const test = require('node:test');
const assert = require('node:assert/strict');
const { render, source } = require('../../../../tests/ui-components.cjs');

test('install list keeps categories and badges without search, legend or state filter', async () => {
  const html = await render('インストール/インストールパネル.vue', {
    項目: [{ id: 'node', name: 'Node.js', description: 'runtime', commands: ['node'], category: 'base', menuGroup: 'ベース' }],
    結果: [{ id: 'node', 状態: 'OK' }], 確認中: false, 接続済み: true,
  });
  assert.match(html, /id="install-run"/);
  assert.match(html, /ベース/);
  assert.doesNotMatch(html, /class="legend"|<select|状態で絞り込む|<input|プログラムを検索/);
  assert.equal((html.match(/data-state="OK"/g) || []).length, 1);
});

test('成功時は通知を消し、エラーは共通通知欄へ表示する', () => {
  const controller = source('インストール/インストール状態.mjs');
  assert.match(controller, /結果;通知.value='';\}catch\(error\)\{通知.value=error.message/);
  assert.match(source('App.vue'), /<p v-if="message" id="message" role="status"/);
});
