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
import * as folderPages from '../src/folder-pages.js';
import { validConnectionState } from '../src/connection-state.js';
import { createDraftTargetRegistry } from '../src/draft-target-registry.js';
const require = createRequire(import.meta.url), vue = require('vue');
const { parse, compileScript, compileTemplate } = require('@vue/compiler-sfc'), { transformSync } = require('esbuild');
const flush = async () => { for (let i = 0; i < 15; i++) await Promise.resolve(); };
const tree = () => ({ n: 'project', f: [['root10.md', 10, 1000], ['root2.js', 20, 2000]], d: [
  { n: 'src', f: [['main.js', 30, 3000]], d: [{ n: 'nested', f: [['deep.js', 40, 4000]], d: [] }] },
  { n: 'empty', f: [], d: [] },
] });

function setup(path, { props = {}, modules = {}, globals = {} } = {}) {
  const source = readFileSync(new URL(`../src/${path}.vue`, import.meta.url), 'utf8');
  const { descriptor } = parse(source);
  assert.deepEqual(compileTemplate({ source: descriptor.template.content, id: path, filename: path }).errors, []);
  const script = compileScript(descriptor, { id: path, genDefaultAs: 'component' });
  const mounted = [], unmounted = [], emitted = [], module = { exports: {} };
  const window = new EventTarget();
  vm.runInNewContext(transformSync(script.content + '\nmodule.exports=component;', { format: 'cjs' }).code, {
    module, window, location: { hash: '' }, AbortController, AbortSignal, URLSearchParams, Date,
    setInterval: () => 1, clearInterval() {}, setTimeout: () => 1, clearTimeout() {},
    require: id => id === 'vue' ? { ...vue, provide() {}, inject: (_key, fallback) => fallback, onMounted: callback => mounted.push(callback), onBeforeUnmount: callback => unmounted.push(callback) }
      : id.endsWith('/folder-pages.js') ? folderPages
      : id.endsWith('/connection-state.js') ? { validConnectionState }
      : id.endsWith('/draft-target-registry.js') ? { createDraftTargetRegistry } : modules[id] || {},
    ...globals,
  });
  const scope = vue.effectScope(), reactive = vue.reactive(props);
  const state = scope.run(() => module.exports.setup(reactive, { expose() {}, emit: (...args) => emitted.push(args) }));
  return { source, state, props: reactive, emitted, async mount() { for (const callback of mounted) await callback(); await flush(); }, dispose() { for (const callback of unmounted) callback(); scope.stop(); } };
}

test('2Dページ: 直下だけをフォルダ先・自然順で表示し、深いファイルは集計に留める', () => {
  const pages = folderPages.indexFolderPages(tree(), { mode: 'since', since: 3000 });
  assert.deepEqual(pages.get('').entries.map(entry => entry.path), ['empty', 'src', 'root2.js', 'root10.md']);
  assert.deepEqual(pages.get('src').entries.map(entry => entry.path), ['src/nested', 'src/main.js']);
  assert.equal(pages.get('').folders.find(entry => entry.name === 'src').count, 2);
  assert.equal(pages.get('').folders.find(entry => entry.name === 'src').marked, 2);
  assert.equal(pages.get('empty').entries.length, 0);
  for (const mode of ['grep', 'ai']) {
    const marked = folderPages.indexFolderPages(tree(), { mode, since: 0, paths: ['src/nested/deep.js'] });
    assert.equal(marked.get('').marked, 1); assert.equal(marked.get('src/nested').files[0].marked, true);
  }
  assert.equal(folderPages.indexFolderPages(tree(), { mode: 'since', since: null }).get('').marked, 0);
});

test('2Dページ記憶: 親へ戻ると位置と選択行を復元し、削除・フィルター外は残さない', () => {
  const memory = folderPages.createFolderPageMemory(), entries = folderPages.indexFolderPages(tree()).get('').entries;
  memory.save('', { scrollTop: 360, cursor: 'src' }); memory.save('src', { scrollTop: 50, cursor: 'src/main.js' });
  assert.deepEqual(memory.restore('', entries), { scrollTop: 360, cursor: 'src' });
  assert.deepEqual(memory.restore('', entries, 'root2.js'), { scrollTop: 360, cursor: 'root2.js' });
  assert.equal(memory.restore('', entries.filter(entry => entry.path !== 'src')).cursor, 'empty');
  assert.equal(memory.restore('', []).cursor, '');
  memory.clear(); assert.deepEqual(memory.restore('', entries), { scrollTop: 0, cursor: 'empty' });
});

test('ページをめくる方向: 子・別の枝は前、親・パンくずの祖先・ルートは逆、同階層は静止', () => {
  for (const [previous, next, direction] of [
    ['', 'src', 'forward'], ['src', 'src/nested', 'forward'], ['src/nested', 'src', 'back'],
    ['src/nested/deep', 'src', 'back'], ['src/nested', '', 'back'], ['', '', ''],
    ['src', 'src', ''], ['src-old', 'src', 'forward'], ['src/nested', 'other', 'forward'],
  ]) assert.equal(folderPages.folderPageDirection(previous, next), direction, `${previous} → ${next}`);
});

test('複数ページ: 共通の親経由で戻して進み、深い移動も5枚に収め最後の目的地を落とさない', () => {
  assert.deepEqual(folderPages.folderPageTurnPlan('src/nested', 'other/deep').map(({ path, direction }) => [path, direction]), [
    ['src', 'back'], ['', 'back'], ['other', 'forward'], ['other/deep', 'forward'],
  ]);
  assert.deepEqual(folderPages.folderPageTurnPlan('src', 'src'), []);
  assert.equal(folderPages.folderPageTurnPlan('', 'src/nested').length, 2);
  const destination = Array.from({ length: 128 }, (_value, i) => 'part' + i).join('/');
  const long = folderPages.folderPageTurnPlan('a/b/c/d/e/f', destination);
  assert.equal(long.length, 5); assert.equal(long.at(-1).path, destination);
  assert.ok(long.some(step => step.path === '' && step.direction === 'back'));
  assert.ok(long.some(step => step.skipped > 0));
  assert.equal(long.reduce((total, step) => total + step.skipped + 1, 0), 134);
});

function pageFixture(globals = {}) {
  const h = setup('components/FolderPages', { props: { tree: tree(), current: '', selected: '', marks: { mode: 'since', since: 1 }, active: true, color: () => '#fff' }, globals });
  const actions = [], body = { scrollTop: 0, focus: options => actions.push(['focus', options]), contains: target => target === body, querySelector: () => ({ scrollIntoView: options => actions.push(['scroll', options]) }) };
  h.state.body.value = body;
  const key = (key, extra = {}) => { const event = { key, target: body, preventDefault() { this.prevented = true; }, stopPropagation() { this.stopped = true; }, ...extra }; h.state.keydown(event); return event; };
  return { ...h, body, actions, key };
}

test('2D部品: フォルダを開く・親へ戻る・ルート・空フォルダとスクロール/カーソル復元', async () => {
  const h = pageFixture();
  try {
    await h.mount(); h.body.scrollTop = 275;
    h.state.select(h.state.entries.value.find(entry => entry.path === 'src'));
    assert.equal(h.emitted.at(-1)[1].path, 'src'); assert.equal(h.emitted.at(-1)[1].type, 'dir');
    const focusBefore = h.actions.filter(([type]) => type === 'focus').length;
    h.props.current = 'src'; await flush(); assert.equal(h.body.scrollTop, 0);
    assert.equal(h.actions.filter(([type]) => type === 'focus').length, focusBefore + 1);
    h.body.scrollTop = 62; h.state.select(h.state.entries.value.find(entry => entry.type === 'file'));
    assert.equal(h.emitted.at(-1)[1].path, 'src/main.js');
    h.state.back(); assert.equal(h.emitted.at(-1)[1].path, '');
    h.props.selected = ''; h.props.current = ''; await flush();
    assert.equal(h.body.scrollTop, 275); assert.equal(h.state.cursor.value, 'src');
    h.state.navigate('src'); h.props.current = 'src'; await flush();
    assert.equal(h.body.scrollTop, 62); assert.equal(h.state.cursor.value, 'src/main.js');
    h.props.current = 'empty'; await flush(); assert.equal(h.state.entries.value.length, 0); assert.equal(h.state.cursor.value, '');
    h.key('Enter'); assert.equal(h.emitted.at(-1)[1].path, 'src');
  } finally { h.dispose(); }
});

test('ページをめくる演出: 初回/更新/モード復帰は静止、親は逆、連打の旧イベントは無視', async () => {
  const h = pageFixture();
  try {
    await h.mount(); assert.equal(h.state.pageTurn.value, '');
    h.props.current = 'src'; await flush(); assert.equal(h.state.pageTurn.value, 'forward');
    h.state.finishTurn({ target: {}, currentTarget: {}, animationName: 'folder-page-forward' });
    assert.equal(h.state.pageTurn.value, 'forward');
    h.state.finishTurn({ target: h.state.body.value, currentTarget: h.state.body.value, animationName: 'folder-page-forward' });
    assert.equal(h.state.pageTurn.value, '');
    h.props.tree = tree(); await flush(); assert.equal(h.state.pageTurn.value, '');
    h.props.current = 'src/nested'; await flush(); assert.equal(h.state.pageTurn.value, 'forward');
    h.props.current = 'src'; await flush(); assert.equal(h.state.pageTurn.value, 'back');
    h.state.finishTurn({ target: h.state.body.value, currentTarget: h.state.body.value, animationName: 'folder-page-forward' });
    assert.equal(h.state.pageTurn.value, 'back');
    h.props.active = false; await flush(); assert.equal(h.state.pageTurn.value, '');
    h.props.active = true; await flush(); assert.equal(h.state.pageTurn.value, '');
    h.props.current = ''; await flush(); assert.equal(h.state.pageTurn.value, 'back');
    h.props.current = 'src'; h.props.current = 'src/nested'; h.props.current = ''; await flush();
    assert.equal(h.state.pageTurn.value, 'back', '同じ最終パスへ戻る連打で新しい演出を追加しない');
  } finally { h.dispose(); }
});

test('ページ演出: reduce-motionではアニメーション状態を残さず、同時モード/パス切替も旧ページに保存する', async () => {
  const h = pageFixture({ matchMedia: () => ({ matches: true }) });
  try {
    await h.mount(); h.body.scrollTop = 180; h.state.save();
    h.props.current = 'src'; h.props.active = false; await flush(); assert.equal(h.state.pageTurn.value, '');
    h.props.active = true; await flush(); assert.equal(h.body.scrollTop, 0);
    h.props.current = ''; await flush(); assert.equal(h.body.scrollTop, 180); assert.equal(h.state.pageTurn.value, '');
    h.props.current = 'src/nested'; await flush(); assert.equal(h.state.pageTurn.value, '');
  } finally { h.dispose(); }
});

test('複数ページ演出: 戻る→進むの各枚数と経由表示、連打・キャンセル・モード切替は最後を優先する', async () => {
  const h = pageFixture();
  const event = (name, type = 'animationend', target = h.state.body.value) => ({ type, target, currentTarget: target, animationName: 'folder-page-' + name });
  try {
    await h.mount(); h.props.current = 'src/nested'; await flush();
    assert.equal(h.state.pageTurn.value, 'forward'); assert.equal(h.state.turnCount.value, 2); assert.equal(h.state.turnDuration.value, 180);
    assert.equal(h.state.turnPath.value, 'src'); h.state.nextTurn(event('forward', 'animationiteration')); assert.equal(h.state.turnPath.value, 'src/nested');
    h.state.finishTurn(event('forward')); assert.equal(h.state.pageTurn.value, '');
    h.props.current = 'empty'; await flush();
    assert.equal(h.state.pageTurn.value, 'back'); assert.equal(h.state.turnCount.value, 2);
    h.state.nextTurn(event('back', 'animationiteration')); assert.equal(h.state.turnPath.value, '');
    h.state.finishTurn(event('back')); assert.equal(h.state.pageTurn.value, 'forward'); assert.equal(h.state.turnCount.value, 1); assert.equal(h.state.turnPath.value, 'empty');
    h.state.finishTurn(event('back')); assert.equal(h.state.pageTurn.value, 'forward', '古い戻り演出の終了を再適用しない');
    h.props.current = 'src/main'; h.props.current = 'src/nested'; await flush();
    assert.equal(h.state.pageTurn.value, 'back'); assert.equal(h.state.turnPath.value, '');
    h.state.finishTurn(event('back', 'animationcancel')); assert.equal(h.state.pageTurn.value, '');
    h.props.current = ''; await flush(); assert.equal(h.state.turnCount.value, 2);
    h.props.active = false; await flush(); h.state.finishTurn(event('back')); assert.equal(h.state.pageTurn.value, '');
    h.props.active = true; await flush(); assert.equal(h.state.pageTurn.value, '');
  } finally { h.dispose(); }
});

test('2D部品: 新規・削除・検索マーク・外部選択・フィルター変更をイベントだけで反映する', async () => {
  const h = pageFixture();
  try {
    await h.mount(); h.props.current = 'src'; h.props.selected = 'src/main.js'; await flush();
    assert.equal(h.state.cursor.value, 'src/main.js');
    const updated = tree(); updated.d[0].f.push(['new.ts', 60, 5000]); h.props.tree = updated; await flush();
    assert.equal(h.state.entries.value.at(-1).path, 'src/new.ts');
    h.props.marks = { mode: 'grep', paths: ['src/new.ts'] }; await flush();
    assert.equal(h.state.entries.value.find(entry => entry.path === 'src/new.ts').marked, true);
    await h.state.move(h.state.entries.value.findIndex(entry => entry.path === 'src/new.ts'));
    assert.equal(h.state.cursor.value, 'src/new.ts');
    h.props.tree = JSON.parse(JSON.stringify(updated)); await flush();
    assert.equal(h.state.cursor.value, 'src/new.ts', '更新通知で開いているファイルへカーソルを巻き戻さない');
    const filtered = tree(); filtered.d[0].f = []; h.props.tree = filtered; h.props.selected = ''; await flush();
    assert.equal(h.state.cursor.value, 'src/nested'); assert.equal(h.state.entries.value.some(entry => entry.path === 'src/main.js'), false);
  } finally { h.dispose(); }
});

test('2D部品: キーボードと戻る、入力中/非表示の無効化、連続ページ切替、破棄', async () => {
  const h = pageFixture();
  try {
    await h.mount(); assert.equal(h.key('End').prevented, true); await flush(); assert.equal(h.state.cursor.value, 'root10.md');
    h.key('ArrowUp'); await flush(); h.key('Enter'); assert.equal(h.emitted.at(-1)[1].path, 'root2.js');
    h.props.selected = 'root2.js'; await flush(); h.key('Escape'); assert.equal(h.emitted.at(-1)[0], 'clear');
    h.key('b', { ctrlKey: true }); assert.equal(h.emitted.at(-1)[0], 'toggle-explorer');
    h.key('r'); assert.equal(h.emitted.at(-1)[0], 'refresh');
    h.props.current = 'src/nested'; await flush(); h.key('Backspace'); assert.equal(h.emitted.at(-1)[1].path, 'src');
    h.key('ArrowLeft', { altKey: true }); assert.equal(h.emitted.at(-1)[1].path, 'src');
    const count = h.emitted.length; h.key('Backspace', { target: { closest: () => ({}) } }); assert.equal(h.emitted.length, count);
    h.props.active = false; await flush(); h.key('Enter'); assert.equal(h.emitted.length, count);
    h.props.current = ''; h.props.active = true; h.props.current = 'src'; h.props.current = 'empty'; await flush();
    assert.equal(h.state.cursor.value, ''); assert.equal(h.body.scrollTop, 0);
    const actions = h.actions.length; h.state.restore(true); h.dispose(); await flush(); assert.equal(h.actions.length, actions);
  } finally { h.dispose(); }
});

test('3Dラッパー: モード切替は同じengineへ停止/再開を伝え、再生成せず破棄を1回行う', async () => {
  const modes = [], engines = [], disposed = [];
  const h = setup('components/SpaceCanvas', { props: { mode: '3d', layout: () => ({}) }, modules: { '../engines/space.js': { createSpace(_canvas, _elements, callbacks) { const engine = { setViewMode: mode => modes.push(mode), dispose: () => disposed.push(engine), callbacks }; engines.push(engine); return engine; } } } });
  await h.mount(); assert.equal(engines.length, 1); assert.equal(h.emitted[0][0], 'ready');
  for (const mode of ['2d', '3d', '2d', '3d']) h.props.mode = mode;
  assert.deepEqual(modes, ['3d', '2d', '3d', '2d', '3d']); assert.equal(engines.length, 1);
  h.dispose(); assert.equal(disposed.length, 1);
});

test('IDE: 3Dが既定。2D切替で利用状態・Term/Code/Live・下書き対象を作り直さない', async () => {
  const h = setup('App', { props: { config: { kind: 'ide' } } });
  try {
    const state = { active: true, mode: 'online', startedAt: 10, project: { path: '/same', name: 'same' } };
    h.state.update(state); assert.equal(h.state.viewMode.value, '3d');
    h.state.base.term = '/term'; h.state.base.code = '/code'; h.state.base.live = '/live';
    h.state.tab.value = 'live'; h.state.panelOpen.value = true; h.state.liveOpen.value = true;
    const request = { text: '下書き' }; h.state.draftRequest.value = request;
    const identity = h.state.state.value;
    h.state.viewMode.value = '2d'; await flush(); h.state.update({ ...state, connected: false });
    assert.equal(h.state.viewMode.value, '2d'); assert.equal(h.state.base.code, '/code'); assert.equal(h.state.base.term, '/term'); assert.equal(h.state.base.live, '/live');
    assert.equal(h.state.draftRequest.value.text, request.text); assert.equal(h.state.panelOpen.value, true); assert.equal(h.state.tab.value, 'live'); assert.equal(h.state.liveOpen.value, true);
    h.state.viewMode.value = '3d'; await flush(); assert.equal(identity.project.path, h.state.state.value.project.path);
    h.state.update({ ...state, startedAt: 11 }); assert.equal(h.state.viewMode.value, '3d'); assert.equal(h.state.base.code, '');
  } finally { h.dispose(); }
});

test('部品境界/配置: プロジェクト右に3D/2D、右端にTerm/Code/Live、共通機能はモード外', () => {
  const app = readFileSync(new URL('../src/App.vue', import.meta.url), 'utf8');
  const view = readFileSync(new URL('../src/components/SpaceView.vue', import.meta.url), 'utf8');
  const css = readFileSync(new URL('../src/style.css', import.meta.url), 'utf8');
  assert.ok(app.indexOf('class="ide-project-name"') < app.indexOf('class="ide-view-modes"'));
  assert.ok(app.indexOf('class="ide-view-modes"') < app.indexOf('class="ide-toolbar-right"'));
  assert.match(app, /class="ide-toolbar-right">\s*<nav[^>]+class="ai-launchers"/);
  assert.match(app, /<SpaceView :key="[^"\n]+" :started-at="state.startedAt" :view-mode="viewMode"/);
  assert.doesNotMatch(app, /<SpaceView[^>]*:key="[^"\n]*viewMode/);
  assert.equal((view.match(/<FileViewer /g) || []).length, 1); assert.equal((view.match(/<FileExplorer /g) || []).length, 1);
  assert.match(view, /<SpaceCanvas :mode="viewMode"/); assert.match(view, /<FolderPages v-if="scan&&pagesReady" :active="viewMode==='2d'"/);
  assert.match(view, /<FileViewer v-if="selected"/); assert.match(css, /prefers-reduced-motion:reduce\)\{\.folder-page-body:is\(\.page-turn-forward,\.page-turn-back\)\{animation:none/);
  assert.match(css, /animation:folder-page-forward var\(--page-turn-duration,300ms\)/); assert.match(css, /animation:folder-page-back var\(--page-turn-duration,300ms\)/);
  assert.match(css, /var\(--page-turn-count,1\)/);
  assert.match(css, /@keyframes folder-page-forward\{from\{[^}]+rotateY\(65deg\)/);
  assert.match(css, /@keyframes folder-page-back\{from\{[^}]+rotateY\(-65deg\)/);
  assert.doesNotMatch(readFileSync(new URL('../src/components/FolderPages.vue', import.meta.url), 'utf8'), /requestAnimationFrame|setInterval|setTimeout/);
});

test('2D配色: 既存AiDiyメニューのクリーム色を専用変数で使い、3Dの黒を維持する', () => {
  const css = readFileSync(new URL('../src/style.css', import.meta.url), 'utf8');
  const menu = readFileSync(new URL('../../frontend_web/src/assets/menu-common.css', import.meta.url), 'utf8');
  for (const color of ['#faf7f2', '#f5f1e8', '#f0ebe0', '#5a4a3a']) { assert.ok(menu.includes(color)); assert.ok(css.includes(color)); }
  assert.match(css, /\.space-view\.mode-2d\{--aidiy-cream-light:/);
  assert.match(css, /\.space-view\{height:100%;background:#000\}/);
  assert.match(css, /\.mode-2d \.folder-pages,\.mode-2d \.folder-page-body,\.mode-2d \.space-loading\{background:var\(--aidiy-cream-light\)/);
});

test('共通画面: 2Dの遅延初期化・共通ビューアEsc・入力中の戻る抑止・軌跡バー高さ追従', async () => {
  const calls = [], styles = [], observers = []; let bottom = 208;
  const h = setup('components/SpaceView', { props: { viewMode: '3d', startedAt: 1 }, globals: {
    getComputedStyle: () => ({ getPropertyValue: () => '78px' }),
    ResizeObserver: class { constructor(callback) { this.callback = callback; observers.push(this); } observe() {} disconnect() { calls.push('disconnect'); } },
  } });
  h.state.root.value = { querySelector: () => ({ getBoundingClientRect: () => ({ bottom }) }), style: { setProperty: (...args) => styles.push(args) } };
  const engine = { marks() {}, route() {}, refresh() {}, clear: () => calls.push('clear'), ascend: level => calls.push(['ascend', level]) };
  h.state.ready(engine);
  try {
    await h.mount(); assert.equal(h.state.pagesReady.value, false);
    assert.deepEqual(styles.at(-1), ['--folder-page-top', '216px']);
    bottom = 126; observers[0].callback(); assert.deepEqual(styles.at(-1), ['--folder-page-top', '134px']);
    h.props.viewMode = '2d'; await flush(); assert.equal(h.state.pagesReady.value, true);
    h.state.selected.value = { path: 'src/main.js' }; h.state.trail.value = ['src'];
    const key = (key, extra = {}) => { const event = { key, preventDefault() { this.prevented = true; }, target: { closest: () => null }, ...extra }; h.state.pageKey(event); return event; };
    assert.equal(key('Escape').prevented, true); assert.equal(calls.at(-1), 'clear');
    h.state.selected.value = null; key('Backspace'); assert.deepEqual(calls.at(-1), ['ascend', 0]);
    const count = calls.length; key('Backspace', { target: { closest: () => ({}) } }); key('Escape', { defaultPrevented: true }); assert.equal(calls.length, count);
    h.props.viewMode = '3d'; await flush(); key('Escape'); assert.equal(calls.length, count); assert.equal(h.state.pagesReady.value, true);
  } finally { h.dispose(); }
  assert.equal(calls.at(-1), 'disconnect');
});

test('実マウント: 2DのDOMを外してもページ位置・選択行を保持し、同じ部品で復帰する', async () => {
  const { descriptor } = parse(readFileSync(new URL('../src/components/FolderPages.vue', import.meta.url), 'utf8'));
  const script = compileScript(descriptor, { id: 'mounted-pages', genDefaultAs: 'component', inlineTemplate: true });
  const module = { exports: {} };
  vm.runInNewContext(transformSync(script.content + '\nmodule.exports=component;', { format: 'cjs' }).code, {
    module, Date, require: id => id === 'vue' ? vue : folderPages,
  });
  const walk = (element, predicate) => predicate(element) ? element : (element.children || []).map(child => walk(child, predicate)).find(Boolean);
  const node = type => ({ type, children: [], props: {}, scrollTop: 0,
    focus() { this.focused = true; }, contains(target) { return !!walk(this, element => element === target); },
    querySelector() { return walk(this, element => element.props['data-cursor'] === true); }, scrollIntoView() {},
  });
  const renderer = vue.createRenderer({
    createElement: node, createText: text => ({ ...node('text'), text }), createComment: text => ({ ...node('comment'), text }),
    insert(element, parent, anchor) {
      if (element.parent) element.parent.children.splice(element.parent.children.indexOf(element), 1);
      element.parent = parent; const index = anchor ? parent.children.indexOf(anchor) : -1;
      if (index < 0) parent.children.push(element); else parent.children.splice(index, 0, element);
    },
    remove(element) { if (element.parent) element.parent.children.splice(element.parent.children.indexOf(element), 1); element.parent = null; },
    parentNode: element => element.parent, nextSibling: element => element.parent?.children[element.parent.children.indexOf(element) + 1],
    patchProp: (element, key, _previous, next) => element.props[key] = next,
    setText: (element, text) => element.text = text, setElementText: (element, text) => { element.text = text; element.children = []; },
  });
  const props = vue.reactive({ active: true, tree: tree(), current: '', selected: '', marks: { mode: 'since', since: 1 } });
  const emitted = [], root = node('root');
  const app = renderer.createApp({ render: () => vue.h(module.exports, { ...props, onSelect: entry => { emitted.push(entry); if (entry.type === 'dir') { props.current = entry.path; props.selected = ''; } else props.selected = entry.path; } }) });
  const warnings = []; app.config.warnHandler = message => warnings.push(message);
  app.mount(root); await flush();
  const find = className => walk(root, element => element.props.class?.split(' ').includes(className));
  try {
    const body = find('folder-page-body'); body.scrollTop = 180; body.props.onScroll();
    assert.doesNotMatch(body.props.class, /page-turn-/);
    const file = walk(root, element => element.props.title === 'root2.js'); file.props.onClick(); await flush();
    assert.equal(props.selected, 'root2.js');
    props.active = false; await flush(); assert.equal(find('folder-page-body'), undefined);
    props.active = true; await flush();
    assert.equal(find('folder-page-body').scrollTop, 180);
    assert.doesNotMatch(find('folder-page-body').props.class, /page-turn-/);
    assert.equal(walk(root, element => element.props.title === 'root2.js').props['aria-selected'], true);
    walk(root, element => element.props.title === 'src').props.onClick(); await flush();
    assert.equal(props.current, 'src'); assert.equal(find('folder-page-body').scrollTop, 0);
    const childBody = find('folder-page-body'); assert.notEqual(childBody, body); assert.match(childBody.props.class, /page-turn-forward/);
    walk(root, element => element.props.title === 'src/nested').props.onClick(); await flush();
    const nestedBody = find('folder-page-body'); assert.notEqual(nestedBody, childBody); assert.match(nestedBody.props.class, /page-turn-forward/);
    childBody.props.onAnimationend({ target: childBody, currentTarget: childBody, animationName: 'folder-page-forward' }); await flush();
    assert.match(find('folder-page-body').props.class, /page-turn-forward/);
    walk(root, element => element.props.title?.startsWith('親フォルダ')).props.onClick(); await flush();
    assert.equal(props.current, 'src'); assert.match(find('folder-page-body').props.class, /page-turn-back/);
    walk(root, element => element.props.title?.startsWith('親フォルダ')).props.onClick(); await flush();
    assert.equal(props.current, ''); assert.equal(find('folder-page-body').scrollTop, 180);
    assert.equal(walk(root, element => element.props.title === 'src').props['aria-selected'], true);
    assert.equal(find('folder-page-body').focused, true); assert.match(find('folder-page-body').props.class, /page-turn-back/);
    assert.deepEqual(warnings, []);
  } finally { app.unmount(); }
});


test('3Dパネル境界: エクスプローラー・ビューア・閲覧/検索軌跡へ静かな白い影を限定する',()=>{
  const css=readFileSync(new URL('../src/style.css',import.meta.url),'utf8');
  const rule=css.match(/\.space-view:not\(\.mode-2d\) :is\(\.explorer-panel,\.viewer-popup,\.explorer-routes,\.route-file-list\)\{([^}]+)\}/);
  assert.ok(rule,'2D以外の4パネルだけを対象にする');
  assert.match(rule[1],/box-shadow:[^;]+rgba\(255,255,255,/);assert.doesNotMatch(rule[1],/animation|transition/);
});
