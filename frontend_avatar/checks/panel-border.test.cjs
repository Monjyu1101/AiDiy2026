const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const source = name => readFileSync(join(__dirname, '../src', name), 'utf8');
test('既存shell枠の太さ・外寸・透明表示を維持', () => {
  const s = source('components/_WindowShell.vue');
  assert.match(s, /width: 100vw;\s+height: 100vh;/);
  assert.match(s, /border: 1px solid #383838;/);
  assert.match(s, /\.window-shell.chrome-hidden\s*\{\s*border-color: transparent;/);
});
test('Web枠は内容領域を確保し、内側shellの二重枠を抑止', () => {
  const s = source('AiDiy.vue');
  assert.match(s, /\.web-left-pane,\s*\.web-right-pane\s*\{\s*box-sizing: border-box;\s*border: 1px solid #383838;/);
  assert.match(s, /\.web-right-content :deep\(\.window-shell\)\s*\{\s*border-color: transparent;/);
});
test('loginは既存枠を着色し追加の外周リングを除去', () => {
  const s = source('components/ログイン.vue');
  assert.match(s, /border: 1px solid #383838;/);
  assert.doesNotMatch(s, /0 0 0 1px rgba\(130, 105, 220/);
});
