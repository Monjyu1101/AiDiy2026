// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import vm from 'node:vm';
import { createSpace } from '../src/engines/space.js';
import * as latest from '../src/latest-file.js';
import * as pages from '../src/folder-pages.js';
import * as references from '../src/file-reference.js';
import { scanWarning } from '../src/scan-warning.js';

const require = createRequire(import.meta.url), vue = require('vue');
const { parse, compileScript, compileTemplate } = require('@vue/compiler-sfc');
const { transformSync } = require('esbuild');
const flush = async () => { for (let n = 0; n < 30; n++) await Promise.resolve(); };
const deferred = () => { let resolve; const promise = new Promise(done => resolve = done); return { promise, resolve }; };
const reply = data => ({ ok: true, json: async () => structuredClone(data) });
const directory = (n, names = [], d = []) => ({ n, f: names.map(name => [name, 40, 1000]), d });
const snapshot = () => ({ root: '/project', truncated: false, tree: directory('project', ['root.js'], [
  directory('src', ['main.js'], [directory('nested', ['deep.js'])]),
  directory('other', ['second.js']), directory('empty'),
]) });
const walk = (node, predicate) => predicate(node) ? node : node.children?.map(child => walk(child, predicate)).find(Boolean);
const hasClass = (node, value) => String(node.props?.class || '').split(/\s+/).includes(value);
const textOf = node => [node.text || '', ...(node.children || []).map(textOf)].join('');

// 実際のSFCテンプレートのイベント/propsで全体を接続する。エンジンや選択処理は置き換えない。
// 描画先だけをメモリ内にし、AI結果は確定済みの通知、Monacoは簡易表示へ置き換える。
async function workspace(t, { auto = false, fetcher, hash = '' } = {}) {
  const old = new Map(), frames = new Map(), timers = new Map(), intervals = new Map(), storage = new Map();
  const requests = [], warnings = [], states = new Map(), props = new Map(), components = new Map();
  const window = new EventTarget(), document = new EventTarget(), location = { hash, origin: 'http://localhost' };
  let clock = 0, id = 0, engine, navigation, emitAI;
  document.hidden = false;
  const context = new Proxy({ font: '', createRadialGradient: () => ({ addColorStop() {} }), measureText: text => ({ width: text.length * 6 }) }, { get: (object, key) => key in object ? object[key] : () => {} });
  function node(type, text = '') {
    const element = new EventTarget();
    Object.assign(element, { type, tagName: type.toUpperCase(), text, children: [], props: {}, scrollTop: 0, value: '',
      style: { setProperty(key, value) { this[key] = value; }, removeProperty(key) { delete this[key]; } },
      classList: { add() {}, remove() {}, toggle() {} },
      setAttribute(key, value) { this.props[key] = value; }, removeAttribute(key) { delete this.props[key]; },
      getContext: () => context, getBoundingClientRect: () => ({ left: 16, right: 280, top: 78, bottom: 126, width: 264, height: 48 }),
      getRootNode: () => document,
      focus() { document.activeElement = this; }, contains(target) { return !!walk(this, value => value === target); },
      closest() { return null; }, scrollIntoView() {},
      querySelector(selector) {
        return walk(this, value => selector.startsWith('.') ? hasClass(value, selector.slice(1))
          : selector === '[data-cursor="true"]' ? value.props?.['data-cursor'] === true
            : selector.startsWith('[data-path=') ? value.props?.['data-path'] === selector.slice(12, -2)
              : value.type === selector);
      },
      animate: () => ({ finished: Promise.resolve(), cancel() {} }),
    });
    return element;
  }
  document.createElement = node;
  Object.assign(window, { devicePixelRatio: 1, history: { pushState(_state, _title, next) { location.hash = next; } },
    requestAnimationFrame: callback => { frames.set(++id, callback); return id; }, cancelAnimationFrame: key => frames.delete(key) });
  const globals = { window, document, location, innerWidth: 1280, innerHeight: 800,
    Element: class Element {}, Document: EventTarget, ShadowRoot: class ShadowRoot {},
    localStorage: { getItem: key => storage.get(key) || null, setItem: (key, value) => storage.set(key, value) },
    getComputedStyle: () => ({ getPropertyValue: () => '78px' }), matchMedia: () => ({ matches: true }), CSS: { escape: value => value },
    fetch: async (url, options) => {
      requests.push({ url, ...options });
      if (fetcher) { const result = await fetcher(url, options); if (result !== undefined) return result; }
      if (url.startsWith('/api/galaxy')) return reply(snapshot());
      if (url.startsWith('/api/latest')) return reply({ files: [] });
      if (url.startsWith('/api/file?')) return reply({ kind: 'text', text: 'first line\n  日本語 result\nlast line' });
      throw Error(`Unexpected API request: ${url}`);
    },
    setTimeout: (callback, delay = 0) => { timers.set(++id, { callback, at: clock + delay }); return id; }, clearTimeout: key => timers.delete(key),
    setInterval: (callback, delay) => { intervals.set(++id, { callback, delay }); return id; }, clearInterval: key => intervals.delete(key),
  };
  for (const [key, value] of Object.entries(globals)) {
    old.set(key, Object.getOwnPropertyDescriptor(globalThis, key));
    Object.defineProperty(globalThis, key, { configurable: true, writable: true, value });
  }
  t.mock.method(performance, 'now', () => clock);
  const moduleMap = {
    '../engines/space.js': { createSpace(...args) { engine = createSpace(...args); navigation = t.mock.method(engine, 'goTo'); engine.setAutoSpin(auto); return engine; } },
    '../latest-file.js': latest, '../folder-pages.js': pages, '../file-reference.js': references,
    '../scan-warning.js': { scanWarning }, '../engines/monaco.js': { loadMonaco: async () => null, monacoLanguage: () => 'javascript' },
  };
  const aiPanel = { props: ['root'], emits: ['result'], setup(_props, { emit }) { emitAI = result => emit('result', result); return () => null; } };
  const runtime = { ...vue, TransitionGroup: { inheritAttrs: false, setup(_props, { slots }) { return () => slots.default?.(); } } };
  function component(name) {
    if (components.has(name)) return components.get(name);
    const filename = new URL(`../src/components/${name}.vue`, import.meta.url).pathname;
    const { descriptor } = parse(readFileSync(filename, 'utf8'));
    const script = compileScript(descriptor, { id: name, genDefaultAs: 'component' });
    const template = compileTemplate({ source: descriptor.template.content, id: name, filename, compilerOptions: { bindingMetadata: script.bindings } });
    assert.deepEqual(template.errors, []);
    const module = { exports: {} };
    vm.runInNewContext(transformSync(`${script.content}\n${template.code}\ncomponent.render=render;module.exports=component;`, { format: 'cjs' }).code, {
      ...globals, module, Date, console, AbortController, AbortSignal, URLSearchParams,
      require: id => id === 'vue' ? runtime : id === './AISearchPanel.vue' ? aiPanel
        : id.endsWith('.vue') ? component(id.slice(2, -4)) : moduleMap[id] || assert.fail(`Unexpected import: ${id}`),
    });
    const result = module.exports, setup = result.setup;
    result.setup = (input, context) => { props.set(name, input); const state = setup(input, context); states.set(name, state); return state; };
    components.set(name, result);
    return result;
  }
  const renderer = vue.createRenderer({
    createElement: node, createText: text => node('text', text), createComment: text => node('comment', text),
    insert(element, parent, anchor) {
      if (element.parent) element.parent.children.splice(element.parent.children.indexOf(element), 1);
      element.parent = parent; const index = anchor ? parent.children.indexOf(anchor) : -1;
      if (index < 0) parent.children.push(element); else parent.children.splice(index, 0, element);
    },
    remove(element) { if (element.parent) element.parent.children.splice(element.parent.children.indexOf(element), 1); element.parent = null; },
    parentNode: element => element.parent, nextSibling: element => element.parent?.children[element.parent.children.indexOf(element) + 1],
    patchProp: (element, key, _previous, value) => { element.props[key] = value; },
    setText: (element, text) => { element.text = text; }, setElementText: (element, text) => { element.text = text; element.children = []; },
  });
  const root = node('root'), viewProps = vue.reactive({ startedAt: 1, viewMode: '2d' });
  const app = renderer.createApp({ render: () => vue.h(component('SpaceView'), viewProps) });
  app.config.warnHandler = message => warnings.push(message);
  function dispose() {
    try { app.unmount(); }
    finally { for (const [key, descriptor] of old) if (descriptor) Object.defineProperty(globalThis, key, descriptor); else delete globalThis[key]; }
  }
  try { app.mount(root); await flush(); } catch (error) { dispose(); throw error; }
  t.after(() => assert.deepEqual(warnings, [], 'Vue mount/update/unmount completes without warnings'));
  const find = predicate => walk(root, predicate);
  return { engine, navigation, root, states, props, viewProps, requests, frames, timers, intervals, warnings, window, document, location, dispose,
    emitAI: value => emitAI(value), find,
    async click(predicate) { const element = find(predicate); assert.ok(element, 'rendered control exists'); assert.equal(typeof element.props.onClick, 'function'); element.props.onClick({ target: element, currentTarget: element, stopPropagation() {}, preventDefault() {} }); await flush(); return element; },
    async advance(ms) {
      clock += ms;
      for (let n = 0; n < 20; n++) {
        const due = [...timers].filter(([, timer]) => timer.at <= clock);
        if (!due.length) break;
        for (const [key, timer] of due) if (timers.delete(key)) timer.callback();
        await flush();
      }
      await flush();
    },
  };
}

function selected(h, path) {
  const parent = path.split('/').slice(0, -1).join('/');
  assert.equal(h.engine.trail.join('/'), parent);
  assert.equal(h.states.get('SpaceView').trail.value.join('/'), parent);
  assert.equal(h.props.get('FolderPages').current, parent);
  assert.equal(h.props.get('FolderPages').selected, path);
  assert.equal(h.props.get('FileExplorer').selected, path);
  assert.equal(h.props.get('FileExplorer').current, parent);
  assert.equal(h.props.get('FileViewer').file.path, path);
  assert.equal(h.engine.selected.path, path);
  assert.ok(h.states.get('FolderPages').entries.value.some(entry => entry.path === path));
  assert.equal(h.states.get('SpaceView').explorerNavigation.value, null);
  assert.equal(h.frames.size, 0, '2D navigation never needs a drawing frame');
}

test('2D統合: エクスプローラーのフォルダ/ファイル・ページ・直接要求・ブラウザ履歴が共通選択へ届く', async t => {
  const h = await workspace(t);
  try {
    await h.click(node => node.props?.['data-path'] === 'src');
    assert.equal(h.props.get('FolderPages').current, 'src'); assert.equal(h.engine.selected, null);
    await h.click(node => node.props?.['data-path'] === 'src/nested');
    await h.click(node => node.props?.['data-path'] === 'src/nested/deep.js'); selected(h, 'src/nested/deep.js');
    assert.equal(h.states.get('SpaceView').autoSpin.value, false);
    await h.click(node => node.props?.title === 'プロジェクトルートへ');
    assert.equal(h.props.get('FolderPages').current, ''); assert.equal(h.engine.selected, null);
    await h.click(node => hasClass(node, 'folder-page-entry') && node.props.title === 'root.js'); selected(h, 'root.js');
    assert.equal(await h.engine.goTo({ type: 'file', path: 'other/second.js' }), true); await flush(); selected(h, 'other/second.js');
    h.location.hash = '#/src/nested'; h.window.dispatchEvent(new Event('popstate')); await flush();
    assert.equal(h.props.get('FolderPages').current, 'src/nested'); assert.equal(h.engine.selected, null);
    h.location.hash = '#/'; h.window.dispatchEvent(new Event('popstate')); await flush();
    assert.equal(h.props.get('FolderPages').current, ''); assert.equal(h.props.get('FileExplorer').current, '');
    assert.deepEqual(h.warnings, []);
  } finally { h.dispose(); }
});

test('2D統合: AI結果の通知は移動せず、結果クリック・前後のAI軌跡・閲覧軌跡が親ページへ移動する', async t => {
  const h = await workspace(t);
  try {
    const route = ['src/nested/deep.js', 'other/second.js', 'root.js'];
    h.emitAI({ title: '関連ファイル', query: '構成を探す', route, files: route.map(path => ({ path, reason: 'テスト結果' })) }); await flush();
    assert.equal(h.engine.selected, null); assert.equal(h.props.get('FolderPages').current, '');
    assert.deepEqual(h.engine.routeState, { mode: 'ai', paths: route });
    assert.equal(h.states.get('FolderPages').entries.value.find(entry => entry.path === 'src').marked, 1);
    const results = h.find(node => hasClass(node, 'ai-route-results'));
    await h.click(node => node.type === 'button' && textOf(node) === route[0] && results.contains(node)); selected(h, route[0]);
    await h.click(node => node.props?.['aria-label'] === '次の関連ファイル'); selected(h, route[1]);
    await h.click(node => node.props?.['aria-label'] === '次の関連ファイル'); selected(h, route[2]);
    await h.click(node => node.props?.['aria-label'] === '前の関連ファイル'); selected(h, route[1]);
    await h.click(node => hasClass(node, 'route-choice') && textOf(node) === '閲覧軌跡');
    const viewRoute = [...h.states.get('FileExplorer').routePaths.value];
    assert.equal(new Set(viewRoute).size, 3);
    await h.click(node => node.props?.['data-route-path'] === viewRoute[0]); selected(h, viewRoute[0]);
    await h.click(node => node.props?.['aria-label'] === '次の閲覧ファイル'); selected(h, viewRoute[1]);
    await h.click(node => node.props?.['aria-label'] === '次の閲覧ファイル'); selected(h, viewRoute[2]);
    assert.deepEqual([...h.states.get('FileExplorer').routePaths.value], viewRoute, '閲覧順を途中で入れ替えず全件を辿る');
    assert.equal(h.requests.some(request => request.url.includes('ai-search')), false);
  } finally { h.dispose(); }
});

test('2D統合: grep行の検索時メタデータを共有ビューアまで渡し、再クリックと再走査でも位置を保持する', async t => {
  const match = { path: 'src/nested/deep.js', line: 2, column: 3, length: 3, mtime: 1000, size: 40, snippet: '  日本語 result' };
  const h = await workspace(t, { fetcher: url => url.startsWith('/api/grep?') ? reply({ paths: [match.path], matches: [match], checked: 1, skipped: 0, truncated: false }) : undefined });
  try {
    const explorer = h.states.get('FileExplorer'); explorer.mode.value = 'grep'; await flush();
    explorer.query.value = '日本語'; explorer.caseSensitive.value = true; await explorer.grep(); await flush();
    explorer.query.value = 'changed'; explorer.caseSensitive.value = false;
    const row = node => node.type === 'button' && node.props?.title === `${match.path}:2:3`;
    await h.click(row); selected(h, match.path);
    assert.equal(h.navigation.mock.calls.at(-1).arguments[0].source, 'grep');
    const file = h.props.get('FileViewer').file;
    for (const [key, value] of Object.entries({ line: 2, column: 3, query: '日本語', caseSensitive: true, matchMtime: 1000, matchLength: 3 })) assert.equal(file[key], value, key);
    assert.equal(h.states.get('FileViewer').fallback.value, true);
    assert.equal(h.states.get('FileViewer').fallbackParts.value.match, '日本語');
    assert.equal(h.states.get('FileViewer').jump.value.stale, false);
    assert.equal(h.states.get('FolderPages').entries.value.find(entry => entry.path === match.path).marked, true);
    const first = file.navigationId;
    await h.click(row); assert.notEqual(h.props.get('FileViewer').file.navigationId, first);
    await h.engine.refresh(); await flush(); selected(h, match.path);
    assert.equal(h.props.get('FileViewer').file.line, 2); assert.equal(h.states.get('FileViewer').fallbackParts.value.match, '日本語');
  } finally { h.dispose(); }
});

test('2D統合: 自動OFFの最終更新クリックは未知の深い親ページを再走査し、フィルターOFFでも手動操作できる', async t => {
  let data = snapshot(), updates = [];
  const h = await workspace(t, { fetcher: url => url.startsWith('/api/galaxy') ? reply(data)
    : url.startsWith('/api/latest') ? reply({ files: updates }) : undefined });
  try {
    updates = [{ path: 'generated/deep/new.js', name: 'new.js', mtime: 3000 }];
    await h.states.get('FileExplorer').pollLatest(); await flush();
    assert.equal(h.engine.selected, null, '更新一覧が届いても自動OFFなら移動しない');
    assert.equal(h.props.get('FolderPages').current, '');
    data.tree.d.push(directory('generated', [], [directory('deep', ['new.js'])]));
    data.tree.d.at(-1).d[0].f[0][2] = 3000;
    await h.click(node => node.props?.['data-latest-path'] === updates[0].path);
    selected(h, updates[0].path);
    assert.equal(h.navigation.mock.calls.at(-1).arguments[0].source, 'latest');
    assert.equal(h.props.get('FileViewer').file.mtime, 3000);
    assert.match(h.requests.filter(request => request.url.startsWith('/api/galaxy')).at(-1).url, /fresh=1/);
    await h.click(node => node.props?.['aria-label'] === 'フィルター');
    assert.equal(h.states.get('SpaceView').filter.value, false);
    assert.equal(h.props.get('FileExplorer').filter, false);
    updates = [{ path: 'other/unfiltered.js', name: 'unfiltered.js', mtime: 4000 }];
    await h.states.get('FileExplorer').pollLatest(); await flush();
    assert.equal(h.engine.selected.path, 'generated/deep/new.js');
    data.tree.d.find(dir => dir.n === 'other').f.push(['unfiltered.js', 50, 4000]);
    await h.click(node => node.props?.['data-latest-path'] === updates[0].path);
    selected(h, updates[0].path);
    assert.doesNotMatch(h.requests.filter(request => request.url.startsWith('/api/galaxy')).at(-1).url, /filter=/);
    data.tree.d = data.tree.d.filter(dir => dir.n !== 'other');
    await h.engine.refresh(); await flush();
    assert.equal(h.props.get('FolderPages').current, ''); assert.equal(h.engine.selected, null);
    assert.equal(h.find(node => node.props?.['data-component'] === 'FileViewer'), undefined);
    assert.equal(h.states.get('FolderPages').entries.value.some(entry => entry.path === 'other'), false);
  } finally { h.dispose(); }
});

test('2D統合: latestの遅い再走査より後の行クリック・閉じる・フィルター・セッションを優先する', async t => {
  for (const action of ['select', 'clear', 'filter', 'session']) {
    let pending = null;
    const h = await workspace(t, { fetcher: url => url.startsWith('/api/galaxy') && pending ? pending.promise : undefined });
    try {
      h.states.get('FileExplorer').acceptUpdates([{ path: 'new/late.js', name: 'late.js', mtime: 5000 }]); await flush();
      pending = deferred();
      await h.click(node => node.props?.['data-latest-path'] === 'new/late.js');
      assert.equal(h.states.get('SpaceView').explorerNavigation.value.path, 'new/late.js');
      if (action === 'select') await h.click(node => node.props?.['data-path'] === 'root.js');
      if (action === 'clear') h.engine.clear();
      if (action === 'filter') await h.click(node => node.props?.['aria-label'] === 'フィルター');
      if (action === 'session') { h.viewProps.startedAt = 2; await flush(); }
      const data = snapshot(); data.tree.d.push(directory('new', ['late.js']));
      const response = pending; pending = null; response.resolve(reply(data)); await flush();
      assert.notEqual(h.engine.selected?.path, 'new/late.js', action);
      assert.notEqual(h.props.get('FolderPages').current, 'new', action);
      assert.equal(h.states.get('SpaceView').explorerNavigation.value, null, action);
      if (action === 'select') selected(h, 'root.js');
      assert.equal(h.frames.size, 0);
    } finally { pending?.resolve(reply(snapshot())); await flush(); h.dispose(); }
  }
});

test('2D統合: 最新通知から自動ONで親ページとビューアへ追従し、手動選択を奪わずOFF中の更新は保留する', async t => {
  let data = snapshot(), updates = [];
  const h = await workspace(t, { auto: true, fetcher: url => url.startsWith('/api/galaxy') ? reply(data)
    : url.startsWith('/api/latest') ? reply({ files: updates }) : undefined });
  try {
    await flush();
    assert.ok(h.engine.selected, '初回最新ファイルもRAFなしで自動表示する');
    data.tree.d.push(directory('created', ['latest.js']));
    data.tree.d.at(-1).f[0][2] = 3000;
    updates = [{ path: 'created/latest.js', name: 'latest.js', mtime: 3000 }];
    await h.states.get('FileExplorer').pollLatest(); await flush(); selected(h, updates[0].path);
    await h.click(node => node.props?.['data-path'] === 'root.js'); selected(h, 'root.js');
    data.tree.d.find(dir => dir.n === 'other').f.push(['newest.js', 50, 4000]);
    updates = [{ path: 'other/newest.js', name: 'newest.js', mtime: 4000 }];
    await h.states.get('FileExplorer').pollLatest(); await h.advance(61_000); selected(h, 'root.js');
    const toggle = await h.click(node => node.props?.['aria-label'] === '自動探索');
    assert.equal(toggle.props['aria-checked'], false);
    assert.notEqual(h.find(node => hasClass(node, 'space-flight-controls')).style.display, 'none');
    await h.click(node => node.props?.['aria-label'] === 'プレビューを閉じる');
    assert.equal(h.engine.selected, null); assert.equal(h.frames.size, 0);
    await h.click(node => node.props?.['aria-label'] === '自動探索'); selected(h, updates[0].path);
    assert.equal(h.intervals.size, 1, 'latestの既存ポーリング以外にループを増やさない');
  } finally { h.dispose(); }
});

test('2D統合: フィルター外grepは既知の親へ移動し、親も一覧外なら現在ページとプレビューを保ち案内する', async t => {
  const paths = ['src/hidden.txt', 'excluded/deep/hidden.txt'];
  const matches = paths.map(path => ({ path, line: 2, column: 3, length: 3, mtime: 1000, size: 40, snippet: '  日本語 result' }));
  const h = await workspace(t, { fetcher: url => url.startsWith('/api/grep?') ? reply({ paths, matches, checked: 2, skipped: 0, truncated: false }) : undefined });
  try {
    const explorer = h.states.get('FileExplorer'); explorer.mode.value = 'grep'; await flush();
    explorer.query.value = '日本語'; await explorer.grep(); await flush();
    await h.click(node => node.type === 'button' && node.props?.title === `${paths[0]}:2:3`);
    assert.equal(h.props.get('FolderPages').current, 'src'); assert.equal(h.engine.trail.join('/'), 'src');
    assert.equal(h.props.get('FileViewer').file.path, paths[0]); assert.equal(h.props.get('FileViewer').file.unlisted, true);
    assert.equal(h.states.get('FileViewer').fallbackParts.value.match, '日本語');
    assert.equal(h.props.get('FolderPages').unlistedParent, undefined);
    assert.equal(h.find(node => hasClass(node, 'folder-page-reference-note')), undefined);
    await h.click(node => node.type === 'button' && node.props?.title === `${paths[1]}:2:3`);
    assert.equal(h.props.get('FolderPages').current, 'src', '存在しない親ページは捏造しない');
    assert.equal(h.props.get('FileViewer').file.path, paths[1]); assert.equal(h.props.get('FileViewer').file.unlisted, true);
    assert.equal(h.states.get('FileViewer').fallbackParts.value.match, '日本語');
    assert.equal(h.props.get('FileExplorer').selected, paths[1]); assert.equal(h.props.get('FileExplorer').current, 'src');
    assert.equal(h.props.get('FolderPages').unlistedParent, 'excluded/deep');
    const note = h.find(node => hasClass(node, 'folder-page-reference-note'));
    assert.ok(note); assert.equal(note.props.role, 'status');
    for (const message of [/excluded\/deep/, /フィルターをOFF/, /一覧を更新/, /選び直/]) assert.match(textOf(note), message);
    assert.equal(h.states.get('SpaceView').error.value, '', '案内は操作を塞ぐエラーにしない');
    await h.engine.refresh(); await flush();
    assert.equal(h.props.get('FileViewer').file.path, paths[1]); assert.equal(h.props.get('FolderPages').current, 'src');
    assert.ok(h.find(node => hasClass(node, 'folder-page-reference-note')));
    assert.equal(h.props.get('FileExplorer').filter, true);
    assert.ok(h.requests.filter(request => request.url.startsWith('/api/galaxy')).every(request => /filter=backup/.test(request.url)));
  } finally { h.dispose(); }
});

test('2D統合: 一覧外AI結果と削除済み閲覧履歴は既存ページを保ち、フィルターを変えず再取得を案内する', async t => {
  const data = snapshot();
  const h = await workspace(t, { fetcher: url => url.startsWith('/api/galaxy') ? reply(data) : undefined });
  try {
    await h.click(node => node.props?.['data-path'] === 'root.js'); selected(h, 'root.js');
    await h.engine.goTo({ type: 'file', path: 'src/main.js' }); await flush(); selected(h, 'src/main.js');
    data.tree.f = [];
    h.emitAI({ title: '一覧外の関連ファイル', query: '不明な参照', route: ['missing/ai.js'], files: [{ path: 'missing/ai.js', reason: '保存済み検索' }] }); await flush();
    const results = h.find(node => hasClass(node, 'ai-route-results'));
    await h.click(node => node.type === 'button' && textOf(node) === 'missing/ai.js' && results.contains(node));
    selected(h, 'src/main.js');
    assert.match(h.states.get('SpaceView').error.value, /フィルターをOFF/);
    assert.match(h.states.get('SpaceView').error.value, /一覧を更新/);
    await h.click(node => hasClass(node, 'route-choice') && textOf(node) === '閲覧軌跡');
    await h.click(node => node.props?.['data-route-path'] === 'root.js');
    selected(h, 'src/main.js');
    assert.match(h.states.get('SpaceView').error.value, /移動・削除/);
    assert.equal(h.props.get('FileExplorer').filter, true);
    assert.ok(h.requests.filter(request => request.url.startsWith('/api/galaxy')).every(request => /filter=backup/.test(request.url)));
    assert.equal(h.requests.some(request => request.url.includes('ai-search')), false);
  } finally { h.dispose(); }
});
