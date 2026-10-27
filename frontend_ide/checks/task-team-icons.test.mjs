// COPYRIGHT (C) 2026 Mitsuo KONDOU and contributors.
// Licensed under AiDiy 公開利用ライセンス v1.1. See LICENSE.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const root=new URL('../',import.meta.url);
test('Task and Team use the common AiDiy artwork and fixed colored title bands',async()=>{
 const code=await readFile(new URL('public/AiDiy_code.svg',root),'utf8');
 const image=code.match(/<image\b[^>]+\/>/)[0];
 for(const [id,color] of [['task','#F6C76B'],['team','#7DD3FC']]){
  const svg=await readFile(new URL(`public/AiDiy_${id}.svg`,root),'utf8');
  assert.equal(svg.match(/<image\b[^>]+\/>/)[0],image);
  assert.match(svg,/width="512" height="512" viewBox="0 0 512 512"/);
  assert.ok(svg.includes(`<rect x="0" y="384" width="512" height="128" fill="${color}"/>`));
  assert.ok(svg.includes(`aria-label="${id.toUpperCase()}"`));
  assert.match(svg,/stroke:#000000/);assert.doesNotMatch(svg,/<text\b/);
  assert.equal(await readFile(new URL(`../backend_diag/ui/src/アプリ起動/アプリアイコン/${id}.svg`,root),'utf8'),svg);
  assert.equal(await readFile(new URL(`../backend_diag/static/AiDiy_${id}.svg`,root),'utf8'),svg);
  const png=await readFile(new URL(`public/AiDiy_${id}.png`,root));assert.equal(png.readUInt32BE(16),512);assert.equal(png.readUInt32BE(20),512);
 }
});
test('standalone Task and Team select their own public icon',async()=>{
 const desktop=await readFile(new URL('desktop.cjs',root),'utf8');
 assert.match(desktop,/\['code','live','console','task','team'\]\.includes\(kind\)/);
});
