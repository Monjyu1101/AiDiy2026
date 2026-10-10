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

const source = await readFile(new URL('../web/app.js', import.meta.url), 'utf8');
const initialView = { tx: 12, ty: 34, tz: -56, yaw: 1.2, pitch: -0.3, dist: 4500 };
function harness() {
  const warps = [], previews = [], galaxy = { path: 'folder' };
  const files = new Map([
    ['a.js', { path: 'a.js', x: 100, y: 200, z: 300, R: 20, isPlanet: true }],
    ['b.js', { path: 'b.js', x: -100, y: -200, z: -300, R: 25, isPlanet: true }],
    ['folder/c.js', { path: 'folder/c.js', x: 10, y: 20, z: 30, R: 18, isPlanet: true }],
  ]);
  const context = createContext({
    trail: [], goal: { ...initialView }, selected: null, selectionOrigin: null,
    focus: galaxy, tracking: null, autoSpin: true, diving: false, F: 720, W: 1280, H: 720,
    world: { galaxies: [galaxy], byPath: files },
    basePath: () => context.trail.join('/'),
    nodeAt: trail => ({ f: trail.length ? [['c.js']] : [['a.js'], ['b.js']] }),
    updateSide: () => previews.push(context.selected?.path ?? null),
    setAutoSpin: value => { context.autoSpin = value; }, touchIdle() {}, remember() {},
    revealCurrent() {}, flyHome() { throw new Error('unexpected fallback'); },
    travelTo(next, options) {
      warps.push({ path: [...next], ...options });
      if (!options.preserveSelection) context.selectionOrigin = null;
      context.trail = [...next]; context.selected = null; context.focus = null; context.tracking = null;
      Object.assign(context.goal, { tx: 0, ty: 0, tz: 0, yaw: 0.6, pitch: 0.35, dist: 4700 });
      options.after?.();
    },
  });
  runInContext(source.slice(source.indexOf('function rememberSelectionView('), source.indexOf('// ---------------------------------------------------------------- 右側:')), context);
  runInContext(source.slice(source.indexOf('function goTo('), source.indexOf('// ---------------------------------------------------------------- 航路')), context);
  return { context, warps, previews, files, galaxy };
}

test('星を選ぶとズームとプレビュー、解除すると直前の視点へ戻る', () => {
  const h = harness(), c = h.context;
  c.selectBody(h.files.get('a.js'));
  assert.deepEqual([c.goal.tx, c.goal.ty, c.goal.tz], [100, 200, 300]);
  assert(c.goal.dist < initialView.dist); assert.equal(c.autoSpin, false);
  assert.equal(h.previews.at(-1), 'a.js');
  c.selectBody(null);
  assert.deepEqual(c.goal, initialView);
  assert.equal(c.focus, h.galaxy); assert.equal(c.autoSpin, true);
  assert.equal(c.tracking, null); assert.equal(h.previews.at(-1), null);
});

test('一覧から選び替えても最初の視点を保持し、再読み込みは再ズームしない', () => {
  const h = harness(), c = h.context;
  c.goTo({ type: 'file', path: 'a.js' });
  c.goTo({ type: 'file', path: 'b.js' });
  assert.equal(h.warps.length, 0); assert.equal(c.selected.path, 'b.js');
  c.goal.dist = 777;
  const updated = { ...h.files.get('b.js'), mtime: 123 };
  c.selectBody(updated, { record: false, zoom: false });
  assert.equal(c.goal.dist, 777); assert.equal(c.tracking, updated);
  c.selectBody(null); assert.deepEqual(c.goal, initialView);
});

test('別階層のファイルはワープして選び、解除時は元の階層・視点へワープして戻る', () => {
  const h = harness(), c = h.context;
  c.goTo({ type: 'file', path: 'folder/c.js' });
  assert.deepEqual(c.trail, ['folder']); assert.equal(c.selected.path, 'folder/c.js');
  assert.equal(h.warps[0].preserveSelection, true);
  assert.equal(h.previews.at(-1), 'folder/c.js');
  c.selectBody(null);
  assert.equal(h.warps.length, 2); assert.deepEqual(c.trail, []);
  assert.equal(h.warps[1].direction, 'out');
  assert.deepEqual(c.goal, initialView); assert.equal(c.selectionOrigin, null);
  assert.equal(h.previews.at(-1), null);
});
