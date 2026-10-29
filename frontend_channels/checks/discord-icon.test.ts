// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

const root = new URL('../', import.meta.url);
test('Discord アイコンは512px・下128pxの黒帯で、元の字形を白く縦110px相当に表示する', async () => {
  const svg = await readFile(new URL('panel/AiDiy_discord.svg', root), 'utf8');
  assert.match(svg, /width="512" height="512" viewBox="0 0 512 512"/);
  assert.match(svg, /<rect x="0" y="384" width="512" height="128" fill="#000000"\/>/);
  assert.match(svg, /<use xlink:href="#original" clip-path="url\(#art\)"\/>/);
  assert.match(svg, /scale\(1 1\.222222222\)/);
  assert.match(svg, /color-interpolation-filters="sRGB"/);
  assert.match(svg, /1\.526946108 0 0 0 -0\.526946108/);
  const png = await readFile(new URL('panel/AiDiy_discord.png', root));
  assert.equal(png.readUInt32BE(16), 512); assert.equal(png.readUInt32BE(20), 512);
  for (const path of ['../backend_diag/ui/src/アプリ起動/アイコン/AiDiy_discord.png', '../backend_diag/static/AiDiy_discord.png']) {
    assert.deepEqual(await readFile(new URL(path, root)), png, `${path} が同じアイコンを使用する`);
  }
});
