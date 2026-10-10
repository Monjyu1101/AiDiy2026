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
import { warpMotion } from '../web/layout.js';

test('入る時は拡大、戻る時は縮小し、次の表示はぼけた状態から現れる', () => {
  const scale = frame => Number(frame.transform.match(/scale\((.*?)\)/)[1]);
  for (const direction of ['in', 'out']) {
    const { exit, entry } = warpMotion(direction);
    assert.equal(exit.frames[0].opacity, 1);
    assert.equal(exit.frames.at(-1).opacity, 0);
    assert(direction === 'in' ? scale(exit.frames.at(-1)) > 1 : scale(exit.frames.at(-1)) < 1);
    assert.equal(entry.frames[0].opacity, 0);
    assert.equal(entry.frames[0].filter, 'blur(18px)');
    assert.equal(entry.frames.at(-1).opacity, 1);
    assert.equal(entry.frames.at(-1).filter, 'blur(0px)');
    assert.equal(scale(entry.frames.at(-1)), 1);

  }
});

const source = await readFile(new URL('../web/app.js', import.meta.url), 'utf8');
function harness() {
  const animations = [], swaps = [], attributes = {};
  const context = createContext({
    warpMotion, selectionOrigin: null, diving: false, tracking: null, dragging: false, touch: new Map(),
    CX: 400, W: 800, H: 600, cam: { dist: 1000 }, goal: {}, trail: [],
    nodeAt: path => !path.includes('missing'), setAutoSpin() {}, project: () => false,
    remember() {},
    document: { body: { classList: { toggle() {} } } },
    $: () => ({ hidden: false }),
    canvas: {
      style: { removeProperty() {} }, classList: { remove() {} }, setAttribute(name, value) { attributes[name] = value; },
      animate(frames, options) {
        let resolve, reject;
        const finished = new Promise((yes, no) => { resolve = yes; reject = no; });
        const animation = { frames, options, finished, finish: resolve, cancel: () => reject(new Error('cancelled')) };
        animations.push(animation); return animation;
      },
    },
    enterWorld: options => swaps.push({ path: [...context.trail], options }),
  });
  runInContext(source.slice(source.indexOf('let warpSequence ='), source.indexOf('// URL の #/')), context);
  return { context, animations, swaps, attributes };
}
const tick = () => new Promise(resolve => setImmediate(resolve));

test('消え終わるまで階層を変えず、次の表示終了後に操作を戻す', async () => {
  const h = harness();
  const pending = h.context.travelTo(['folder']);
  assert.equal(h.context.diving, true); assert.equal(h.attributes['aria-busy'], 'true');
  assert.equal(h.swaps.length, 0);
  h.animations[0].finish(); await tick();
  assert.deepEqual(h.swaps.map(s => s.path), [['folder']]);
  assert.equal(h.swaps[0].options.immediate, true);
  assert.equal(h.context.diving, true);
  h.animations[1].finish(); await pending;
  assert.equal(h.context.diving, false); assert.equal(h.attributes['aria-busy'], 'false');
});

test('途中で別の移動を選んだ時は最後の移動だけを採用する', async () => {
  for (const phase of ['exit', 'entry']) {
    const h = harness();
    let selected = 0;
    const old = h.context.travelTo(['old']);
    if (phase === 'entry') { h.animations[0].finish(); await tick(); }
    const latest = h.context.travelTo(['latest'], { history: false, after: () => selected++ });
    await old;
    assert.equal(h.context.diving, true);
    h.animations.at(-1).finish(); await tick();
    assert.equal(h.swaps.at(-1).path[0], 'latest');
    assert.equal(h.swaps.at(-1).options.history, false);
    h.animations.at(-1).finish(); await latest;
    assert.equal(selected, 1); assert.equal(h.context.diving, false);
    assert.equal(h.context.trail[0], 'latest');
  }
});

test('中央のフォルダ・ワームホールはダブルクリックだけで移動する', () => {
  const calls = [];
  const folder = { path: 'folder' };
  const context = createContext({
    diving: false, hoveredGate: false, hovered: null, hoveredGalaxy: folder,
    selected: null, focus: null, tracking: null, trail: ['folder'],
    updateHover() {}, updateSide() {}, selectBody() {},
    dive: g => calls.push(['in', g.path]), ascend: n => calls.push(['out', n]),
    approach() {}, flyHome: () => calls.push(['home']),
  });
  runInContext(source.slice(source.indexOf('function handleClick('), source.indexOf('function flyTo(')), context);
  context.handleClick(100, 100); context.handleClick(100, 100);
  assert.equal(calls.length, 0);
  context.handleDoubleClick(100, 100);
  assert.deepEqual(calls, [['in', 'folder']]);
  context.hoveredGate = true; context.hoveredGalaxy = null;
  context.handleClick(100, 100); context.handleClick(100, 100);
  assert.equal(calls.length, 1);
  context.handleDoubleClick(100, 100);
  assert.deepEqual(calls.at(-1), ['out', 0]);
  context.diving = true; context.handleDoubleClick(100, 100);
  assert.equal(calls.length, 2);
});

test('フォルダ一覧は名前選択で直接ワープし、開閉矢印では移動しない', () => {
  const calls = [], listeners = {};
  const context = createContext({
    diving: false, trail: [], world: { galaxies: [], byPath: new Map() },
    nodeAt: () => true, basePath: () => context.trail.join('/'),
    revealCurrent() {}, remember() {}, approach() {}, explorerCursor: null,
    travelTo: (next, options) => calls.push({ path: [...next], direction: options.direction }),
    $: () => ({ addEventListener: (name, fn) => { listeners[name] = fn; } }),
    toggleDir: () => calls.push('toggle'),
    openExplorerRow: row => context.goTo(row),
  });
  runInContext(source.slice(source.indexOf('function goTo('), source.indexOf('// ---------------------------------------------------------------- 航路')), context);
  runInContext(source.slice(source.indexOf("const explorerTree = $('explorer-tree');"), source.indexOf("explorerTree.addEventListener('keydown'")), context);
  const event = (chevron, detail = 1) => ({ detail, target: { closest: selector => selector === 'li'
    ? { dataset: { type: 'dir', path: 'folder' } } : chevron ? {} : null } });
  listeners.click(event(true)); assert.deepEqual(calls, ['toggle']); calls.length = 0;
  listeners.click(event(false));
  assert.deepEqual(calls, [{ path: ['folder'], direction: 'in' }]);
  listeners.click(event(false, 2)); assert.equal(calls.length, 1);
  context.trail = ['folder', 'child']; listeners.click(event(false));
  assert.deepEqual(calls.at(-1), { path: ['folder'], direction: 'out' });
  context.trail = ['folder']; listeners.click(event(false)); assert.equal(calls.length, 2);
});
