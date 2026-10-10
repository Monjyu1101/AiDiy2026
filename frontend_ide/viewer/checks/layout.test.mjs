// -*- coding: utf-8 -*-

// -------------------------------------------------------------------------
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
// -------------------------------------------------------------------------

import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createContext, runInContext } from 'node:vm';
import { spacePosition, WORLD_RADIUS, HOME_VIEW, orbitView, panOffset } from '../web/layout.js';

test('名前のハッシュを毎回同じ3D座標へ変換し、全方向へ分散する', () => {
  assert.deepEqual(spacePosition('か\u3099.md'), spacePosition('が.md'));
  assert.deepEqual(spacePosition('日本語😀.md'), spacePosition('日本語😀.md'));
  // 旧方式で同じ合計になる名前・文字の順序違いも区別する。
  assert.notDeepEqual(spacePosition('README.md'), spacePosition('CLAUDE.md'));
  assert.notDeepEqual(spacePosition('ab.js'), spacePosition('ba.js'));
  assert.notDeepEqual(spacePosition('a.js', { identity: 'one/a.js' }), spacePosition('a.js', { identity: 'two/a.js' }));
  const octants = new Array(8).fill(0), mean = [0, 0, 0], unique = new Set();
  for (let i = 0; i < 1024; i++) {
    const p = spacePosition(`file-${i}.js`);
    const radius = Math.hypot(p.x, p.y, p.z);
    assert(Number.isFinite(radius));
    assert(radius >= 300 && radius <= 1500);
    assert(radius + 160 < WORLD_RADIUS);
    octants[(p.x > 0 ? 1 : 0) + (p.y > 0 ? 2 : 0) + (p.z > 0 ? 4 : 0)]++;
    [p.x, p.y, p.z].forEach((v, axis) => { mean[axis] += v / 1024; });
    unique.add(JSON.stringify(p));
    const small = spacePosition(`file-${i}.js`, { scale: 150 });
    for (const axis of ['x', 'y', 'z']) assert(Math.abs(small[axis] * 10 - p[axis]) < 1e-9);
  }
  assert.equal(unique.size, 1024);
  assert(octants.every(n => n > 70 && n < 190), String(octants));
  assert(mean.every(n => Math.abs(n) < 100), String(mean));
});

test('上下左右の回転は極で止まらず、一周で同じ向きへ戻る', () => {
  const view = { ...HOME_VIEW };
  orbitView(view, 0, 400); assert(view.pitch > Math.PI / 2);
  orbitView(view, 0, -400);
  orbitView(view, Math.PI * 2 / 0.005, Math.PI * 2 / 0.005);
  for (const key of ['yaw', 'pitch']) {
    assert(Math.abs(Math.sin(view[key]) - Math.sin(HOME_VIEW[key])) < 1e-12);
    assert(Math.abs(Math.cos(view[key]) - Math.cos(HOME_VIEW[key])) < 1e-12);
  }
});

test('平行移動はどの視点でも画面に沿い、奥行きを変えない', () => {
  for (const yaw of [0, 0.6, Math.PI, 5]) for (const pitch of [0, 0.35, Math.PI / 2, Math.PI, 5]) {
    const delta = panOffset(yaw, pitch, 12, -8, 3);
    const x = delta.x * Math.cos(yaw) - delta.z * Math.sin(yaw);
    const z = delta.x * Math.sin(yaw) + delta.z * Math.cos(yaw);
    const y = delta.y * Math.cos(pitch) - z * Math.sin(pitch);
    const depth = delta.y * Math.sin(pitch) + z * Math.cos(pitch);
    assert(Math.abs(x + 36) < 1e-10);
    assert(Math.abs(y + 24) < 1e-10);
    assert(Math.abs(depth) < 1e-10);
  }
});

// DOMに依存しない実際の宇宙組み立て部分を読み、変更前後の全座標を比較する。
const source = await readFile(new URL('../web/app.js', import.meta.url), 'utf8');
const context = createContext({ spacePosition, WORLD_RADIUS, since: null, KINDS: new Array(10), kindOf: () => 0 });
runInContext(source.slice(source.indexOf('function hash('), source.indexOf('// ---------------------------------------------------------------- 遠景の星')) + `
  globalThis.make = (tree, folder = []) => { scan = {tree}; trail = folder; return buildWorld(); };
`, context);
const file = (name, size = 1, time = 1) => [name, size, time];
const dir = (n, f = [], d = []) => ({ n, f, d });
function snapshot(world) {
  return Object.fromEntries([...world.galaxies, ...world.stars, ...world.planets].map(p => [p.path, [p.x, p.y, p.z]]));
}
function unchanged(before, after) {
  for (const [path, position] of Object.entries(before)) assert.deepEqual(after[path], position, path);
}

test('件数・列挙順・サイズ・更新日時が変わっても既存の全座標と全景倍率は変わらない', () => {
  const tree = dir('root', [file('README.md'), file('CLAUDE.md')], [
    dir('frontend_ide/viewer', Array.from({ length: 23 }, (_, i) => file(`${i}.js`))),
    dir('日本語', [file('文書.md')], [dir('child', [file('文書.md')])]), dir('empty'),
  ]);
  const initial = context.make(tree);
  const positions = snapshot(initial);
  tree.f.reverse(); tree.d.reverse();
  tree.d.find(d => d.n === 'frontend_ide/viewer').f.reverse();
  unchanged(positions, snapshot(context.make(tree)));
  tree.f.push(file('追加.txt'));
  tree.d.push(dir('new-folder', [file('a.js')]));
  tree.d.find(d => d.n === 'frontend_ide/viewer').f.push(file('24個目.js'));
  tree.d.find(d => d.n === 'empty').f.push(file('最初.md'));
  tree.f[0][1] = 100000000; tree.f[0][2] = Date.now();
  const changed = context.make(tree);
  unchanged(positions, snapshot(changed));
  assert.equal(changed.radius, initial.radius);
  assert.equal(changed.galaxies.find(g => g.name === 'frontend_ide/viewer').R, initial.galaxies.find(g => g.name === 'frontend_ide/viewer').R);
  tree.f.pop(); tree.d.pop();
  unchanged(positions, snapshot(context.make(tree)));
  const entered = context.make(tree, ['日本語']);
  context.make(tree, ['frontend_ide/viewer']);
  unchanged(snapshot(entered), snapshot(context.make(tree, ['日本語'])));
  assert.deepEqual(JSON.parse(JSON.stringify(entered.gate)), { x: 0, y: 0, z: 0, R: 60, name: 'root' });
});

test('描画時刻が進んでも惑星・帰還ゲートの座標を動かさない', () => {
  // 投影以降のCanvas描画を省略して、公転・上下動が再導入されていないか確認する。
  Object.assign(context, { introAt: 0, matches: null, bodies: [], ctx: {}, project: () => false });
  runInContext(source.slice(source.indexOf('function drawPlanets('), source.indexOf('function voyageTargets(')) + `
    globalThis.renderAt = (value, seconds) => { world = value; drawPlanets(seconds, seconds * 1000); drawGate(seconds); };
  `, context);
  const value = context.make(dir('root', [], [dir('child', [file('日本語.md'), file('README.md')])]), ['child']);
  const positions = snapshot(value);
  const gate = JSON.stringify(value.gate);
  for (const seconds of [0, 10, 3600, 86400]) {
    context.renderAt(value, seconds);
    unchanged(positions, snapshot(value));
    assert.equal(JSON.stringify(value.gate), gate);
  }
});
