// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import { fileURLToPath } from 'node:url';
import { componentPaths, componentName } from './component-paths.mjs';
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import vm from 'node:vm';
import { createSpace } from '../src/開発スペース/宇宙描画.js';
import { createFolderMonitor } from '../src/ファイル閲覧/フォルダ監視.js';
import * as viewerIdle from '../src/ファイル閲覧/閲覧待機.js';
import * as routeTree from '../src/開発スペース/軌跡ツリー.js';
import * as routeRecords from '../src/開発スペース/経路記録.js';
import * as fileDates from '../src/ファイル閲覧/ファイル日時.js';
import * as latest from '../src/ファイル閲覧/最新ファイル.js';
import * as pages from '../src/ファイル閲覧/フォルダページ構成.js';
import * as references from '../src/ファイル閲覧/ファイル参照.js';
import * as fileActions from '../src/ファイル閲覧/ファイル操作.js';
import * as browserLaunch from '../src/ブラウザ/起動.js';
import * as mediaTypes from '../viewer/media-types.mjs';
import * as routeExpansion from '../src/ファイル閲覧/軌跡パネル展開.js';
import * as panelWindows from '../src/ファイル閲覧/パネル別窓.js';
import { scanWarning } from '../src/ファイル閲覧/走査警告.js';
import { fileIcon } from '../src/ファイル閲覧/ファイルアイコン.js';

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
async function workspace(t, { auto = false, fetcher, hash = '', mode = '2d', actualAI = false } = {}) {
  const old = new Map(), frames = new Map(), timers = new Map(), intervals = new Map(), storage = new Map();
  const requests = [], warnings = [], states = new Map(), props = new Map(), components = new Map();
  const window = new EventTarget(), document = new EventTarget(), location = { hash, origin: 'http://localhost' };
  let clock = 0, id = 0, engine, navigation, emitAI, beginAI;
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
      // 既存の移動/追跡リクエスト件数とは別の監視。監視自体は専用テストで検証する。
      if (url.startsWith('/api/folder-state')) return reply({ revision: 'unchanged', files: 0 });
      requests.push({ url, at: clock, ...options });
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
    '../ブラウザ/起動.js': browserLaunch,
    '../../viewer/media-types.mjs': mediaTypes,
    '../ファイル閲覧/閲覧待機.js':viewerIdle,
    '../ファイル閲覧/軌跡パネル展開.js':routeExpansion,'../ファイル閲覧/パネル別窓.js':panelWindows,
    './ファイル日時.js': fileDates,
    '../開発スペース/軌跡ツリー.js':routeTree,'../開発スペース/経路記録.js':routeRecords,
    '../ファイル閲覧/フォルダ監視.js': { createFolderMonitor },
    '../開発スペース/宇宙描画.js': { createSpace(...args) { engine = createSpace(...args); navigation = t.mock.method(engine, 'goTo'); engine.setAutoSpin(auto); return engine; } },
    '../ファイル閲覧/最新ファイル.js': latest, '../ファイル閲覧/フォルダページ構成.js': pages, '../ファイル閲覧/ファイル参照.js': references, '../ファイル閲覧/ファイル操作.js': fileActions,
    '../ファイル閲覧/ファイルアイコン.js': { fileIcon }, '../ファイル閲覧/走査警告.js': { scanWarning }, '../ファイル閲覧/コード表示.js': { loadMonaco: async () => null, monacoLanguage: () => 'javascript' },
  };
  const aiPanel = { props: ['root'], emits: ['result','search'], setup(_props, { emit }) { emitAI = result => emit('result', result);beginAI=()=>emit('search'); return () => null; } };
  const runtime = { ...vue, TransitionGroup: { inheritAttrs: false, setup(_props, { slots }) { return () => slots.default?.(); } } };
  function component(name) {
    if (components.has(name)) return components.get(name);
    const filename = fileURLToPath(new URL(`../src/${componentPaths[name]}`, import.meta.url));
    const { descriptor } = parse(readFileSync(filename, 'utf8'));
    const script = compileScript(descriptor, { id: name, genDefaultAs: 'component' });
    const template = compileTemplate({ source: descriptor.template.content, id: name, filename, compilerOptions: { bindingMetadata: script.bindings } });
    assert.deepEqual(template.errors, []);
    const module = { exports: {} };
    vm.runInNewContext(transformSync(`${script.content}\n${template.code}\ncomponent.render=render;module.exports=component;`, { format: 'cjs' }).code, {
      ...globals, module, Date, console, AbortController, AbortSignal, URLSearchParams,
      require: id => id === 'vue' ? runtime : id === '../ファイル検索/AI検索パネル.vue' ? (actualAI?component('AISearchPanel'):aiPanel)
        : id.endsWith('.vue') ? component(componentName(id)) : moduleMap[id] || assert.fail(`Unexpected import: ${id}`),
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
  const root = node('root'), viewProps = vue.reactive({ startedAt: 1, viewMode: mode });
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
    emitAI: value => emitAI(value), beginAI:()=>beginAI(),find,
    async frame(ms = 100) { const callbacks = [...frames.values()]; frames.clear(); await this.advance(ms); for (const callback of callbacks) callback(clock); await flush(); },
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
    const explorer=h.states.get('FileExplorer'),steps=[...explorer.routeSteps.value];
    assert.equal(new Set(explorer.routePaths.value).size,3);
    await h.click(node=>node.props?.['data-route-path']===steps[0].path);
    for(const row of steps.slice(1)){
      await h.click(node=>node.props?.['aria-label']==='次の閲覧ファイル');
      if(row.type==='file')selected(h,row.path);else {assert.equal(h.engine.trail.join('/'),row.path);assert.equal(h.engine.selected,null);}
    }
    assert.equal(explorer.routeIndex.value,explorer.routeSteps.value.length-1,'リスト順に終端まで辿る');
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
    assert.equal(!!h.find(node => hasClass(node, 'space-loading')), false, '移動失敗で表示済みページを遮らない');
    assert.match(textOf(h.find(node => hasClass(node, 'space-notice'))), /フィルターをOFF/);
    await h.click(node => hasClass(node, 'route-choice') && textOf(node) === '閲覧軌跡');
    await h.click(node => node.props?.['data-route-path'] === 'root.js');
    selected(h, 'src/main.js');
    assert.match(h.states.get('SpaceView').error.value, /移動・削除/);
    assert.equal(h.props.get('FileExplorer').filter, true);
    assert.ok(h.requests.filter(request => request.url.startsWith('/api/galaxy')).every(request => /filter=backup/.test(request.url)));
    assert.equal(h.requests.some(request => request.url.includes('ai-search')), false);
    await h.click(node => node.props?.['aria-label'] === '案内を閉じる');
    assert.equal(h.find(node => hasClass(node, 'space-notice')), undefined); selected(h, 'src/main.js');
    await h.engine.goTo({type:'file',path:'missing/again.js'}); await flush();
    await h.click(node => node.props?.['aria-label'] === '一覧を更新');
    assert.equal(h.states.get('SpaceView').error.value, ''); selected(h, 'src/main.js');
  } finally { h.dispose(); }
});


for (const input of ['ArrowDown', 'PageDown', 'wheel', 'touchmove', 'pointerdown']) test(`2D統合: ${input}は手動待機を更新し、直前の期限でページを奪わない`, async t => {
  const h = await workspace(t, {auto:true});
  try {
    await h.engine.goTo({type:'dir',path:'src'}); await flush();
    h.engine.requestFollow('other/second.js'); await h.advance(59_999);
    const section=h.find(node=>hasClass(node,'folder-pages')),body=h.find(node=>hasClass(node,'folder-page-body'));
    const event={key:input,target:body,currentTarget:section,buttons:1,preventDefault(){},stopPropagation(){}};
    const handler=input==='ArrowDown'||input==='PageDown' ? section.props.onKeydown : section.props['on'+input[0].toUpperCase()+input.slice(1)+(input==='wheel'||input==='touchmove'?'Passive':'')];
    assert.equal(typeof handler,'function',`${input}を実際のテンプレートが購読する`);handler(event);await flush();
    await h.advance(1);assert.equal(h.engine.trail.join('/'),'src');assert.equal(h.engine.selected,null);
    await h.advance(59_998);assert.equal(h.engine.trail.join('/'),'src');
    await h.advance(1);selected(h,'other/second.js');assert.equal(h.frames.size,0);
  } finally {h.dispose();}
});

test('2D統合: 復元・検索更新・プログラムによるscrollは手動待機を延長しない', async t => {
  const h=await workspace(t,{auto:true});
  try {
    await h.engine.goTo({type:'dir',path:'src'});await flush();h.engine.requestFollow('other/second.js');
    await h.advance(59_999);
    const body=h.find(node=>hasClass(node,'folder-page-body'));body.scrollTop=70;body.props.onScroll({target:body,currentTarget:body});
    h.states.get('SpaceView').marks.value={mode:'grep',paths:['src/main.js']};await flush();
    await h.advance(1);selected(h,'other/second.js');assert.equal(h.frames.size,0);
  } finally {h.dispose();}
});

for(const mode of ['2d','3d']) test(`${mode}実部品の更新時系列: 通知到着後は追加の1分を待たず、同じファイル監視と手動保護を使う`,async t=>{
  const data=snapshot();let updates=[];
  const h=await workspace(t,{mode,auto:true,fetcher:url=>url.startsWith('/api/galaxy')?reply(data):url.startsWith('/api/latest')?reply({files:updates}):undefined});
  const finish=async predicate=>{for(let n=0;n<200&&!predicate();n++)await h.frame();assert.equal(predicate(),true,'3D演出を含む処理が終わる');};
  try {
    await finish(()=>!!h.engine.selected);await finish(()=>h.engine.canFollow());
    const polling=[...h.intervals.values()];assert.equal(polling.length,1);assert.equal(polling[0].delay,60000,'ファイル監視は共通の60秒。接続監視とは別');
    data.tree.d.find(dir=>dir.n==='other').f.push(['new.js',30,3000]);updates=[{path:'other/new.js',name:'new.js',mtime:3000}];
    const before=h.requests.length;await h.advance(59000);assert.notEqual(h.engine.selected?.path,'other/new.js');assert.equal(h.requests.length,before);
    await h.advance(1000);polling[0].callback();await flush();
    const arrival=h.requests.find((request,index)=>index>=before&&request.url.startsWith('/api/latest')).at;
    await finish(()=>h.engine.selected?.path==='other/new.js');await finish(()=>h.engine.canFollow());
    const started=h.requests.find((request,index)=>index>=before&&request.url.startsWith('/api/galaxy'));
    assert.ok(started.at-arrival<=100,'通知後2Dは同tick、3Dは次のframeで再走査を始める');
    assert.equal(h.engine.trail.join('/'),'other');assert.equal(h.frames.size,mode==='2d'?0:1);
    // 自動で開いたプレビューの次の更新も、別の手動待機へ誤変換しない。
    updates=[{path:'root.js',name:'root.js',mtime:4000}];data.tree.f[0][2]=4000;
    await h.states.get('FileExplorer').pollLatest();await finish(()=>h.engine.selected?.path==='root.js');await finish(()=>h.engine.canFollow());
    // 表示モードの切替だけでは手動待機を作らない。
    h.viewProps.viewMode=mode==='2d'?'3d':'2d';await flush();assert.equal(h.engine.canFollow(),true);
    updates=[{path:'other/new.js',name:'new.js',mtime:5000}];data.tree.d.find(dir=>dir.n==='other').f.at(-1)[2]=5000;
    await h.states.get('FileExplorer').pollLatest();await finish(()=>h.engine.selected?.path==='other/new.js');
  } finally {h.dispose();}
});

for(const mode of ['2d','3d'])test(`${mode}実部品の探索枠: 更新候補がなくても開始し、手動待機・非表示・OFFだけで止める`,async t=>{
  const h=await workspace(t,{auto:true,mode,fetcher:url=>url.startsWith('/api/galaxy')?reply({root:'/project',tree:directory('project'),truncated:false}):undefined});
  const spinning=()=>hasClass(h.find(node=>node.props?.['aria-label']==='自動探索'),'driving');
  try {
    await h.frame();assert.equal(spinning(),true);
    h.engine.interact();await h.frame();assert.equal(spinning(),false);
    const calls=h.requests.length;await h.advance(60000);await h.frame();assert.equal(spinning(),true);assert.equal(h.requests.length,calls);
    h.document.hidden=true;h.document.dispatchEvent(new Event('visibilitychange'));await flush();assert.equal(spinning(),false);assert.equal(h.frames.size,0);
    h.document.hidden=false;h.document.dispatchEvent(new Event('visibilitychange'));await h.frame();assert.equal(spinning(),true);
    await h.click(node=>node.props?.['aria-label']==='自動探索');await h.frame();assert.equal(spinning(),false);
    await h.click(node=>node.props?.['aria-label']==='自動探索');await h.frame();assert.equal(spinning(),true);
    assert.equal(h.frames.size,mode==='2d'?0:1);assert.equal(h.timers.size,mode==='2d'?3:1,'共通の更新目印の深夜予約に加え、2Dだけ監視と日時更新を予約');assert.equal(h.intervals.size,1);
  } finally {h.dispose();}
});

const finishFollow=async(h,predicate)=>{for(let n=0;n<220&&!predicate();n++)await h.frame();assert.equal(predicate(),true,'有限のフレームで移動を完了する');};
function addUpdatedFile(data,path,mtime){const parts=path.split('/');let dir=data.tree;for(const name of parts.slice(0,-1)){let child=dir.d.find(value=>value.n===name);if(!child){child=directory(name);dir.d.push(child);}dir=child;}const file=dir.f.find(value=>value[0]===parts.at(-1));if(file)file[2]=mtime;else dir.f.push([parts.at(-1),40,mtime]);}
for(const mode of ['2d','3d'])for(const target of ['new','same','deleted'])test(`${mode}更新追跡: 通知より前の走査へ合流した${target}を1回だけ再検証する`,async t=>{
  let data=snapshot(),updates=[],pending;
  const h=await workspace(t,{auto:true,mode,fetcher:url=>url.startsWith('/api/galaxy')?(pending?pending.promise:reply(data)):url.startsWith('/api/latest')?reply({files:updates}):undefined});
  try {
    await finishFollow(h,()=>!!h.engine.selected&&h.engine.canFollow());
    const path=target==='same'?h.engine.selected.path:'new/deep/file.js';
    if(target==='deleted')addUpdatedFile(data,path,2000);
    const old=structuredClone(data),before=h.requests.filter(request=>request.url.startsWith('/api/galaxy')).length;
    pending=deferred();const background=h.engine.refresh();await flush();
    if(target==='deleted')data.tree.d=data.tree.d.filter(dir=>dir.n!=='new');else addUpdatedFile(data,path,5000);
    updates=[{path,name:path.split('/').at(-1),mtime:5000}];await h.states.get('FileExplorer').pollLatest();await h.frame();
    const waiting=pending;pending=null;waiting.resolve(reply(old));await background;await flush();
    if(target==='deleted'){for(let n=0;n<100;n++)await h.frame();assert.notEqual(h.engine.selected?.path,path);}
    else await finishFollow(h,()=>h.engine.selected?.path===path&&h.engine.selected.mtime===5000&&h.engine.canFollow());
    const scans=h.requests.filter(request=>request.url.startsWith('/api/galaxy')).slice(before);assert.equal(scans.length,2,'旧走査と追加1回だけ');assert.match(scans.at(-1).url,/fresh=1/);
    const calls=h.requests.length;await h.advance(120000);await h.frame();assert.equal(h.requests.length,calls,'欠落や同じ更新を際限なく再試行しない');
  } finally {pending?.resolve(reply(data));await flush();h.dispose();}
});
for(const mode of ['2d','3d'])for(const action of ['switch','rapid','deleted','dispose'])test(`${mode}更新追跡中の${action}: 古い航行を中止し、最後のモードで更新先を再検証する`,async t=>{
  let data=snapshot(),updates=[],pending;
  const h=await workspace(t,{auto:true,mode,fetcher:url=>url.startsWith('/api/galaxy')?(pending?pending.promise:reply(data)):url.startsWith('/api/latest')?reply({files:updates}):undefined});
  try {
    await finishFollow(h,()=>!!h.engine.selected&&h.engine.canFollow());
    const path='new/deep/file.js';addUpdatedFile(data,path,5000);const old=structuredClone(data);
    pending=deferred();updates=[{path,name:'file.js',mtime:5000}];await h.states.get('FileExplorer').pollLatest();await h.frame();
    h.viewProps.viewMode=mode==='2d'?'3d':'2d';await flush();
    if(action==='rapid'){for(let n=0;n<5;n++){h.viewProps.viewMode=h.viewProps.viewMode==='2d'?'3d':'2d';await flush();await h.frame();}}
    if(action==='deleted')data.tree.d=data.tree.d.filter(dir=>dir.n!=='new');
    if(action==='dispose')h.engine.dispose();
    const waiting=pending;pending=null;waiting.resolve(reply(old));await flush();
    if(action==='deleted'||action==='dispose'){for(let n=0;n<100;n++)await h.frame();assert.notEqual(h.engine.selected?.path,path);}
    else {await finishFollow(h,()=>h.engine.selected?.path===path&&h.engine.canFollow());assert.equal(h.engine.trail.join('/'),'new/deep');}
    const calls=h.requests.length;await h.advance(120000);await h.frame();assert.equal(h.requests.length,calls);
    assert.equal(h.frames.size,action==='dispose'||h.viewProps.viewMode==='2d'?0:1);
  } finally {pending?.resolve(reply(data));await flush();h.dispose();}
});


test('閲覧軌跡クリア: 開いた見出しだけに表示し、現在位置・経路・検索軌跡を保持する',async t=>{
 const h=await workspace(t,{auto:false,mode:'2d'});
 try{
  assert.equal(h.find(n=>n.props?.['aria-label']==='閲覧軌跡をクリア'),undefined);
  await h.engine.goTo({type:'file',path:'src/main.js'});await flush();
  h.emitAI({route:['root.js','src/main.js'],files:[]});await flush();
  await h.click(n=>n.text==='閲覧軌跡');
  const before=JSON.parse(localStorage.getItem('aidiy_ide:/project'));
  const selected=h.engine.selected,trail=[...h.engine.trail];
  await h.click(n=>n.props?.['aria-label']==='閲覧軌跡をクリア');
  assert.equal(h.engine.selected,selected);assert.deepEqual(h.engine.trail,trail);
  assert.equal(h.props.get('FileExplorer').viewHistory.filter(e=>e.type==='file').length,0);
  const saved=JSON.parse(localStorage.getItem('aidiy_ide:/project'));
  assert.deepEqual(saved.voyages,before.voyages);assert.deepEqual(saved.voyageCurrent,before.voyageCurrent);
  assert.equal(h.find(n=>n.props?.['aria-label']==='閲覧軌跡をクリア').props.disabled,true);
  await h.click(n=>n.text==='AiDiy検索軌跡');assert.equal(h.find(n=>n.props?.['aria-label']==='閲覧軌跡をクリア'),undefined);
  assert.deepEqual([...h.states.get('FileExplorer').aiRoute.value],['root.js','src/main.js']);
  await h.click(n=>n.text==='閲覧軌跡');await h.click(n=>n.text==='閲覧軌跡');assert.equal(h.find(n=>n.props?.['aria-label']==='閲覧軌跡をクリア'),undefined);
 }finally{h.dispose();}
});


test('エクスプローラー: 起点/grepのフォルダは通常色対象、右側の対象件数とファイル着色を保持する',async t=>{
 const h=await workspace(t,{auto:false,mode:'2d'});
 try{
  const explorer=h.states.get('FileExplorer');explorer.mode.value='since';explorer.since.value=1;await flush();
  let row=h.find(n=>n.props?.['data-path']==='src');assert.ok(hasClass(row,'plain-folder'));assert.ok(hasClass(row,'fresh'));assert.equal(row.props['data-entry-type'],'dir');
  explorer.mode.value='grep';await flush();explorer.matches.value=new Set(['src/main.js']);await flush();
  row=h.find(n=>n.props?.['data-path']==='src');assert.ok(hasClass(row,'plain-folder'));assert.ok(hasClass(row,'fresh'));assert.ok(explorer.counts.value.get('src')>0);
  const file=h.find(n=>n.props?.['data-path']==='src/main.js');if(file)assert.equal(hasClass(file,'plain-folder'),false);
  explorer.mode.value='ai';await flush();row=h.find(n=>n.props?.['data-path']==='src');assert.equal(hasClass(row,'plain-folder'),false,'既存のAI検索用表示は変更しない');
 }finally{h.dispose();}
});


test('軌跡3分類: 起点/grep開始・結果・失敗・再検索・空結果を独立表示し、経路を変更しない',async t=>{
 let next=reply({paths:['src/main.js','other/second.js'],matches:[],checked:4,skipped:0});
 const h=await workspace(t,{fetcher:url=>url.startsWith('/api/grep')?next:undefined});
 try{
  const ex=h.states.get('FileExplorer');
  await h.engine.goTo({type:'file',path:'root.js'});await flush();
  const saved=JSON.parse(localStorage.getItem('aidiy_ide:/project'));
  await h.click(n=>n.text==='検索軌跡');assert.equal(ex.routeRows.value.length,0);assert.equal(h.engine.routeState.mode,'search');
  await h.click(n=>n.text==='閲覧軌跡');
  ex.choose('start');await flush();assert.equal(ex.routeMode.value,'search');assert.ok(ex.routePaths.value.includes('root.js'));
  assert.ok(ex.routeRows.value.every(row=>row.parent===null));
  ex.mode.value='grep';await flush();ex.query.value='needle';
  let pending=deferred();next=pending.promise;const running=ex.grep();await flush();assert.equal(h.engine.routeState.mode,'search');
  pending.resolve(reply({paths:['src/main.js','other/second.js'],matches:[],checked:4,skipped:0}));await running;await flush();
  assert.deepEqual([...ex.routePaths.value],['src/main.js','other/second.js']);
  await h.click(n=>n.text==='AiDiy検索軌跡');assert.equal(ex.routeRows.value.length,0);assert.equal(h.engine.routeState.mode,'ai');
  h.beginAI();await flush();assert.equal(ex.routeMode.value,'ai');
  h.emitAI({query:'AI',route:['root.js','src/nested/deep.js'],files:[],routeRecords:[{from:null,to:'f:root.js'},{from:'f:root.js',to:'f:src/nested/deep.js'}]});await flush();
  assert.deepEqual(ex.routeRows.value.map(row=>[row.path,row.parent]),[['root.js',null],['src/nested/deep.js','f:root.js']]);
  await h.click(n=>n.text==='検索軌跡');assert.deepEqual([...ex.routePaths.value],['src/main.js','other/second.js']);
  assert.equal(h.find(n=>n.props?.['aria-label']==='閲覧軌跡をクリア'),undefined);
  ex.mode.value='grep';await flush();next={ok:false,text:async()=> 'fixture failure'};await ex.grep();await flush();
  assert.match(ex.status.value,/fixture failure/);assert.equal(h.engine.routeState.mode,'search');assert.deepEqual([...ex.routePaths.value],['src/main.js','other/second.js']);
  next=reply({paths:[],matches:[],checked:4,skipped:0});await ex.grep();await flush();assert.equal(ex.routeRows.value.length,0);
  await h.click(n=>n.text==='閲覧軌跡');assert.deepEqual([...ex.routePaths.value],['root.js']);
  assert.deepEqual(JSON.parse(localStorage.getItem('aidiy_ide:/project')),saved,'分類切替と検索だけでは閲覧記録や経路を追加しない');
  await h.click(n=>n.text==='AiDiy検索軌跡');assert.deepEqual([...ex.aiRoute.value],['root.js','src/nested/deep.js']);
 }finally{h.dispose();}
});

test('閲覧ツリーの実部品: 再訪・分岐・ポイント移動・クリアの分類分離',async t=>{
 const h=await workspace(t);
 try{
  const ex=h.states.get('FileExplorer');
  for(const path of ['src/main.js','src/nested/deep.js','src/main.js','root.js']){await h.engine.goTo({type:'file',path});await flush();}
  await h.click(n=>n.text==='閲覧軌跡');
  const records=JSON.parse(localStorage.getItem('aidiy_ide:/project')).voyages;
  const row=ex.routeRows.value.find(r=>r.path==='src/main.js');assert.ok(row);
  await h.click(n=>n.props?.['data-route-path']==='src/main.js');selected(h,'src/main.js');
  assert.deepEqual(JSON.parse(localStorage.getItem('aidiy_ide:/project')).voyages,records,'再訪で重複枝を増やさない');
  ex.acceptSearch(['root.js','other/second.js'],'grep','query');h.emitAI({route:['src/nested/deep.js'],files:[]});await flush();
  await h.click(n=>n.text==='検索軌跡');await h.click(n=>n.props?.['data-route-path']==='other/second.js');selected(h,'other/second.js');
  await h.click(n=>n.text==='閲覧軌跡');await h.click(n=>n.props?.['aria-label']==='閲覧軌跡をクリア');assert.equal(ex.routeRows.value.length,0);
  await h.click(n=>n.text==='検索軌跡');assert.deepEqual([...ex.routePaths.value],['root.js','other/second.js']);
  await h.click(n=>n.text==='AiDiy検索軌跡');assert.deepEqual([...ex.routePaths.value],['src/nested/deep.js']);
 }finally{h.dispose();}
});


test('実AI検索部品: 開始・失敗・再検索・再確認でAiDiy分類へ切替、前回確定結果を保持',async t=>{
 let response=reply({status:'failed',message:'fixture offline',id:'test'});
 const h=await workspace(t,{actualAI:true,fetcher:url=>url.includes('/api/ai-search/history')?reply({entries:[]}):url.startsWith('/api/ai-search')?response:undefined});
 try{
  const ai=h.states.get('AISearchPanel'),ex=h.states.get('FileExplorer');ai.query.value='query';
  await ai.search();await flush();assert.equal(ex.routeMode.value,'ai');assert.equal(ex.aiRoute.value.length,0);assert.match(ai.message.value,/fixture offline/);
  response=reply({status:'complete',result:{id:'fixture',query:'query',files:[],route:['src/main.js']}});
  await h.click(n=>n.text==='閲覧軌跡');await ai.search();await flush();assert.equal(ex.routeMode.value,'ai');assert.deepEqual([...ex.aiRoute.value],['src/main.js']);
  await h.click(n=>n.text==='閲覧軌跡');response=reply({status:'failed',message:'fixture fail',id:'test'});await ai.search();await flush();assert.equal(ex.routeMode.value,'ai');assert.deepEqual([...ex.aiRoute.value],['src/main.js']);
  await h.click(n=>n.text==='検索軌跡');ai.recheck();await flush();assert.equal(ex.routeMode.value,'ai');assert.deepEqual([...ex.aiRoute.value],['src/main.js']);
 }finally{h.dispose();}
});

test('フォルダA/Bの対とリスト連続移動: 2つの関係は1操作、ファイルは飛ばさず再訪で枝を増やさない',async t=>{
 const data={root:'/project',tree:directory('project',[],[directory('A',[],[directory('B',['one.txt','two.txt'])])])};
 const h=await workspace(t,{fetcher:url=>url.startsWith('/api/galaxy')?reply(data):undefined});
 try{
  for(const entry of [{type:'dir',path:'A'},{type:'dir',path:'A/B'},{type:'file',path:'A/B/one.txt'},{type:'file',path:'A/B/two.txt'}]){await h.engine.goTo(entry);await flush();}
  await h.click(n=>n.text==='閲覧軌跡');const ex=h.states.get('FileExplorer');
  assert.deepEqual(ex.routeSteps.value.map(r=>r.path),['','A','A/B','A/B/one.txt','A/B/two.txt']);
  const stored=JSON.parse(localStorage.getItem('aidiy_ide:/project')).voyages;
  await h.click(n=>n.props?.['data-route-path']==='A/B');assert.equal(h.engine.trail.join('/'),'A/B');assert.equal(h.engine.selected,null);
  await h.click(n=>n.props?.['aria-label']==='次の閲覧ファイル');selected(h,'A/B/one.txt');
  await h.click(n=>n.props?.['aria-label']==='次の閲覧ファイル');selected(h,'A/B/two.txt');
  assert.equal(h.find(n=>n.props?.['aria-label']==='次の閲覧ファイル').props.disabled,true);
  await h.click(n=>n.props?.['aria-label']==='前の閲覧ファイル');selected(h,'A/B/one.txt');
  await h.click(n=>n.props?.['aria-label']==='前の閲覧ファイル');assert.equal(h.engine.trail.join('/'),'A/B');assert.equal(h.engine.selected,null);
  await h.click(n=>n.props?.['aria-label']==='前の閲覧ファイル');assert.equal(h.engine.trail.join('/'),'A');
  assert.deepEqual(JSON.parse(localStorage.getItem('aidiy_ide:/project')).voyages,stored);
 }finally{h.dispose();}
});
