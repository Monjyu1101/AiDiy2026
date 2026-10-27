// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1". See LICENSE.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const root = new URL('../', import.meta.url);
test('Term title keeps its geometry with a light-gray band and bright-green original glyphs', async () => {
  const svg = await readFile(new URL('public/AiDiy_term.svg', root), 'utf8');
  assert.match(svg, /width="512" height="512" viewBox="0 0 512 512"/);
  assert.match(svg, /<rect x="0" y="384" width="512" height="128" fill="#D3D3D3"\/>/);
  assert.match(svg, /<use xlink:href="#original" clip-path="url\(#art\)"\/>/);
  assert.match(svg, /color-interpolation-filters="sRGB"/);
  assert.doesNotMatch(svg, /transform=|<text\b/);
  const matrix = svg.match(/<feColorMatrix type="matrix" values="([^"]+)"/)[1].trim().split(/\s+/).map(Number);
  function mapped(g) { return [0,1,2].map(row => Math.round(255*(matrix[row*5+1]*g+matrix[row*5+4]))); }
  assert.deepEqual(mapped(0), [0,208,64]);
  assert.deepEqual(mapped(197/255), [211,211,211]);
});
test('Term title PNG is identical in IDE and both Diag distributions', async () => {
  const png = await readFile(new URL('public/AiDiy_term.png', root));
  assert.equal(png.readUInt32BE(16), 512); assert.equal(png.readUInt32BE(20), 512);
  for (const relative of ['../backend_diag/ui/src/アプリ起動/アイコン/AiDiy_term.png', '../backend_diag/static/AiDiy_term.png']) {
    assert.deepEqual(await readFile(new URL(relative, root)), png);
  }
});
