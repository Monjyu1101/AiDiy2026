const test = require('node:test');
const assert = require('node:assert/strict');
const { render, source } = require('./ui-components.cjs');
test('compiled badges distinguish every state with visible text and decorative semantic icons', async () => {
  for (const [state, tone] of Object.entries({ 未確認: 'neutral', 未実施: 'neutral', 未取得: 'neutral', 未検出: 'warning', 注意: 'warning', OK: 'success', NG: 'danger', ERR: 'danger', 取得済: 'success', 取得中: 'pending', 失敗: 'danger' })) {
    const html = await render('StatusBadge.vue', { state });
    assert.ok(html.includes(`data-state="${state}"`));
    assert.ok(html.includes(`data-tone="${tone}"`));
    assert.ok(html.includes(`aria-label="${state}"`));
    assert.ok(html.includes(`class="badge-label">${state}</span>`));
    assert.match(html, /<svg[^>]*aria-hidden="true"[^>]*focusable="false"/);
    if (tone === 'neutral') assert.match(html, /badge-neutral-dot/);
    else assert.match(html, /<path/);
  }
});

test('untrusted labels are escaped', async () => {
  const escaped = await render('StatusBadge.vue', { label: '<script>alert(1)</script>' });
  assert.doesNotMatch(escaped, /<script>/);
  assert.match(escaped, /&lt;script&gt;/);
});

test('key list keeps public acquisition and individual test outcomes separate', async () => {
  const html = await render('モデルキー設定/モデルキー設定パネル.vue', {
    data: { 設定状態: '読込済み', 項目: [{ id: 'openai', 名前: 'OpenAI', キー名: 'OPENAI_API_KEY', 設定済み: true, テスト可能: true }] },
    results: { openai: { 状態: 'NG' } }, loading: false, testing: '', connected: true,
    publicModels: { 状態: '取得済', 件数: 12 }, publicBusy: false,
  });
  assert.match(html, /class="badge public-indicator" data-state="取得済" data-tone="success"/);
  assert.match(html, /公開モデル取得済/);
  assert.match(html, /data-state="NG" data-tone="danger"/);
  assert.match(html, />テスト<\/button>/);
  assert.match(html, /設定状況を更新/);
  assert.match(html, /公開モデルを再取得/);
  assert.match(html, /class="config-state">設定済/);
  assert.match(html, /<details class="test-notes"><summary>テストについて/);
  assert.match(html, /各サービスへモデル一覧を問い合わせます/);
  assert.doesNotMatch(html, /<input|<select|設定ファイル:|12 件/);
});

test('badge palette has accessible text contrast and preserves black unchecked markers', () => {
  const css = source('style.css');
  const luminance = hex => hex.match(/\w\w/g).map(v => parseInt(v, 16) / 255).map(v => v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4).reduce((s, v, i) => s + v * [.2126, .7152, .0722][i], 0);
  const palettes = [...css.matchAll(/--badge-fg:#([0-9a-f]{6});--badge-bg:#([0-9a-f]{6})/g)];
  assert.equal(palettes.length, 5);
  for (const [, fg, bg] of palettes) assert.ok((luminance(fg) + .05) / (luminance(bg) + .05) >= 4.5, `${fg} on ${bg}`);
  assert.match(css, /badge-neutral-dot\{fill:#090909/);
  assert.doesNotMatch(css, /\.badge::before|\.status::before/);
  assert.doesNotMatch(source('StatusBadge.vue'), /v-html|innerHTML|https?:/);
});


test('simplified key settings still display public and configuration failures', async () => {
  const html = await render('モデルキー設定/モデルキー設定パネル.vue', {
    data: { 設定状態: '読込不可', 説明: '設定の読込に失敗', 項目: [] }, results: {},
    publicModels: { 状態: '失敗', 説明: '公開一覧への接続に失敗' }, connected: true,
  });
  assert.match(html, /設定ファイル: 読込不可/);
  assert.match(html, /設定の読込に失敗/);
  assert.match(html, /公開一覧への接続に失敗/);
  assert.match(html, /公開モデルを再取得/);
});
