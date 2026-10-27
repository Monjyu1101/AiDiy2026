// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1". See LICENSE.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const root = new URL('../', import.meta.url);
test('Console title keeps the standard band and bright green path glyphs', async () => {
  const svg = await readFile(new URL('public/AiDiy_console.svg', root), 'utf8');
  assert.match(svg, /width="512"/); assert.match(svg, /height="512"/);
  assert.match(svg, /viewBox="0 0 512 512"/);
  assert.match(svg, /<title[^>]*>AiDiy CONSOLE<\/title>/);
  assert.match(svg, /fill="#D3D3D3"/i);
  assert.match(svg, /aria-label="CONSOLE"/);
  assert.match(svg, /fill:#00d040/i);
  assert.doesNotMatch(svg, /<text\b/);
});
test('Console title PNG is identical in IDE and both Diag distributions', async () => {
  const png = await readFile(new URL('public/AiDiy_console.png', root));
  assert.equal(png.readUInt32BE(16), 512); assert.equal(png.readUInt32BE(20), 512);
  for (const relative of ['../backend_diag/ui/src/アプリ起動/アイコン/AiDiy_console.png', '../backend_diag/static/AiDiy_console.png']) {
    assert.deepEqual(await readFile(new URL(relative, root)), png);
  }
});
