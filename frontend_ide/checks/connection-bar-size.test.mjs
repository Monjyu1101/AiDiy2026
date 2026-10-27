// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
const read = path => readFileSync(new URL(path, import.meta.url), 'utf8');
const rules = css => [...css.matchAll(/([^{}]+)\{([^{}]*)\}/g)];
const declaration = (body, property) => body.match(new RegExp(`(?:^|;)\\s*${property}\\s*:\\s*([^;]+)`))?.[1].trim();
test('Console / Code / Live / IDE の接続バーは境界線込み3pxを共有する', () => {
  const css = read('../src/style.css') + '\n' + read('../src/共通表示/会話表示.css');
  assert.match(css, /\*\s*\{\s*box-sizing\s*:\s*border-box/);
  const sizes = rules(css).filter(([_, selector, body]) => selector.includes('.connection-bar') && declaration(body, 'height'));
  assert.equal(sizes.length, 1, 'アプリ別の高さ上書きを追加しない');
  assert.equal(sizes[0][1].trim(), '.connection-bar');
  assert.equal(declaration(sizes[0][2], 'height'), '3px');
  assert.equal(declaration(sizes[0][2], 'border-top'), '1px solid #242424');
  assert.equal(declaration(sizes[0][2], 'flex'), 'none');
});
test('Diag / Discord も境界線込み3pxに揃う', () => {
  const diag = read('../../backend_diag/ui/src/style.css');
  assert.match(diag, /\*\s*\{\s*box-sizing\s*:\s*border-box/);
  const diagBar = rules(diag).find(([_, selector]) => selector.trim() === '.connection-bar')[2];
  assert.equal(declaration(diagBar, 'height'), '3px');
  assert.equal(declaration(diagBar, 'border-top'), '1px solid #242424');
  const discordBar = rules(read('../../frontend_channels/panel/style.css')).find(([_, selector]) => selector.trim() === '#activity-bar')[2];
  assert.equal(declaration(discordBar, 'box-sizing'), 'content-box');
  assert.equal(declaration(discordBar, 'height'), '2px');
  assert.equal(declaration(discordBar, 'border-top'), '1px solid #242424');
});
test('VS Code版は単独版と同じ共通CSSを配布・参照する', () => {
  assert.match(read('../host/src/vscode-html.ts'), /dist\/development\/app\.css/);
  const build = read('../scripts/build.mjs');
  assert.match(build, /host\/dist\/development/);
  assert.match(build, /host\/aidiy_live\/dist\/development/);
  assert.match(build, /'app\.css'/);
});
