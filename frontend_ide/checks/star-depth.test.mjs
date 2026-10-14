// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import test from 'node:test';
import assert from 'node:assert/strict';
import { BASE_STAR_MAG, createSpace, representativeStarScale } from '../src/engines/space.js';

const flush = async () => { for (let n = 0; n < 20; n++) await Promise.resolve(); };
const dir = (n, f = [], d = []) => ({ n, f: f.map(file => Array.isArray(file) ? file : [file, 40, 100]), d });
const snapshot = tree => ({ root: '/project', tree, truncated: false });
const fixture = () => snapshot(dir('project', ['root.js'], [
  dir('src', ['main.js'], [dir('nested', [['note.txt', 50, 200]], [dir('deeper', [['deep.py', 60, 300]])]), dir('empty')]),
  dir('vacant'),
]));
const event = (type, values = {}) => Object.assign(new Event(type, { cancelable: true }), values);

// 実エンジンを使い、Canvas/API/時計だけをメモリ内へ置き換える。ブラウザ・AI・ソケットは使わない。
function space(t, initial = fixture()) {
  const old = new Map(), frames = new Map(), timers = new Map(), changes = [], requests = [], draws = [], arcs = [], texts = [], routeLines = [], storage = new Map();
  const window = new EventTarget(), document = new EventTarget(), canvas = new EventTarget(), location = { hash: '' };
  let data = initial, clock = 0, id = 0, busy = false, dash = [];
  document.hidden = false;
  const context = new Proxy({ font: '', createRadialGradient: () => ({ addColorStop() {} }),
    measureText: text => ({ width: text.length * 6 }), drawImage: (...args) => draws.push(args), fillText: (...args) => texts.push(args),
    arc: (...args) => arcs.push({ args, fill: context.fillStyle, alpha: context.globalAlpha, composite: context.globalCompositeOperation }),
    setLineDash: value => { dash = value; }, lineTo: (...args) => { if (dash.join(',') === '5,7') routeLines.push(args); },
  }, { get: (object, key) => key in object ? object[key] : () => {} });
  const tipNodes = { '.t-name': {}, '.t-sub': {} };
  const tooltip = { style: {}, querySelector: name => tipNodes[name] };
  Object.assign(canvas, { getContext: () => context, classList: { add() {}, remove() {}, toggle() {} },
    style: { removeProperty(key) { delete this[key]; } }, setAttribute(name, value) { if (name === 'aria-busy') busy = value === 'true'; },
    setPointerCapture() {}, animate: () => ({ finished: Promise.resolve(), cancel() {} }),
  });
  document.createElement = () => ({ getContext: () => context });
  Object.assign(window, { devicePixelRatio: 1, history: { pushState(_a, _b, hash) { location.hash = hash; } },
    requestAnimationFrame: callback => { frames.set(++id, callback); return id; }, cancelAnimationFrame: key => frames.delete(key),
  });
  for (const [key, value] of Object.entries({ window, document, location, innerWidth: 1280, innerHeight: 800, Element: class Element {},
    localStorage: { getItem: key => storage.get(key) || null, setItem: (key, value) => storage.set(key, value) },
    fetch: async (url, options) => { requests.push({ url, ...options }); return { ok: true, json: async () => structuredClone(data) }; },
    setTimeout: (callback, delay = 0) => { timers.set(++id, { callback, at: clock + delay }); return id; }, clearTimeout: key => timers.delete(key),
  })) {
    old.set(key, Object.getOwnPropertyDescriptor(globalThis, key)); Object.defineProperty(globalThis, key, { configurable: true, writable: true, value });
  }
  t.mock.method(performance, 'now', () => clock);
  t.mock.method(Date, 'now', () => 1000000 + clock);
  const engine = createSpace(canvas, { tooltip }, { change: value => changes.push(value) });
  engine.setAutoSpin(false);
  const pump = async (ms = 100) => {
    clock += ms;
    const callbacks = [...frames.values()]; frames.clear(); for (const callback of callbacks) callback(clock);
    for (const [key, timer] of [...timers]) if (timer.at <= clock && timers.delete(key)) timer.callback();
    await flush();
  };
  const until = async predicate => {
    for (let n = 0; n < 500 && !predicate(); n++) await pump();
    assert.ok(predicate(), 'navigation completes');
  };
  const finish = async promise => {
    let done = false, result, error;
    Promise.resolve(promise).then(value => { result = value; done = true; }, value => { error = value; done = true; });
    await until(() => done); if (error) throw error; return result;
  };
  return { engine, canvas, window, location, draws, arcs, texts, routeLines, requests, tooltip, tipNodes, storage, frames, pump, until, finish,
    data: value => { data = value; }, state: () => changes.filter(value => 'scan' in value).at(-1),
    errors: () => changes.filter(value => value.error).map(value => value.error), idle: () => !busy,
    async ready() { await engine.refresh(150); for (let n = 0; n < 30; n++) await pump(); },
    camera() { Object.assign(engine.cam, { tx: 0, ty: 0, tz: 0, dist: 600, yaw: 0, pitch: 0, roll: 0 }); Object.assign(engine.goal, engine.cam); },
    dispose() { engine.dispose(); for (const [key, descriptor] of old) if (descriptor) Object.defineProperty(globalThis, key, descriptor); else delete globalThis[key]; },
  };
}

const coordinates = body => [body.x, body.y, body.z];

// 配下の空フォルダは数えず、直下とさらに深いファイルを混在させる。
const countedFolder = (name, count) => {
  const files = Array.from({ length: count }, (_, i) => [`file-${i}.png`, 0, 100]);
  const split = Math.floor(count / 3);
  return dir(name, files.slice(0, split), [dir('empty'), dir('nested', [], [dir('deep', files.slice(split))])]);
};
const countFixture = counts => snapshot(dir('project', [], [dir('src', [['reference.png', 0, 100]], counts.map(count => countedFolder(`count-${count}`, count)))]));
const close = (actual, expected, message) => assert.ok(Math.abs(actual - expected) < 1e-9, `${message}: ${actual} != ${expected}`);

function positionSizeSamples(h) {
  const g = h.engine.world.galaxies[0];
  Object.assign(g, { x: 200, y: 170, z: 0 });
  g.stars.forEach((body, i) => Object.assign(body, { x: -250 + i * 65, y: -100, z: 0, lr: 0 }));
  h.camera();
}

// サイズの計算値だけでなく、実エンジンがCanvasへ渡す画像寸法と不透明な円の直径を調べる。
function renderedStar(h, body) {
  const k = 840 / h.engine.cam.dist, x = 640 + body.x * k, y = 400 - body.y * k;
  const images = h.draws.filter(([, left, top, width, height]) => Math.abs(left + width / 2 - x) < 1e-8 && Math.abs(top + height / 2 - y) < 1e-8);
  const cores = h.arcs.filter(({ args, fill, alpha, composite }) => fill === '#000' && alpha === 1 && composite === 'source-over' && Math.abs(args[0] - x) < 1e-8 && Math.abs(args[1] - y) < 1e-8);
  assert.ok(images.length > 0, `${body.path} の星画像を描画する`);
  assert.equal(cores.length, 1, `${body.path} の不透明な本体は1つ`);
  close(images[0][3], images[0][4], '星画像は正方形');
  return { diameter: images[0][3], coreDiameter: cores[0].args[2] * 2, images };
}

const drawFrame = async (h, ms = 0) => { h.draws.length = 0; h.arcs.length = 0; await h.pump(ms); };

test('代表星の直径倍率: 通常基準星の1倍から対数的に増え、100ファイル以上は3倍に制限する', () => {
  assert.equal(BASE_STAR_MAG, 1, '容量・種類の補正前の通常星を基準にする');
  for (const [count, expected] of [[0, 1], [1, 1], [2, 1 + Math.log10(2)], [5, 1 + Math.log10(5)], [10, 2], [100, 3], [12000, 3], [Number.MAX_SAFE_INTEGER, 3]]) {
    assert.equal(representativeStarScale(count), expected, `${count} files`);
  }
  let previous = 1;
  for (let count = 0; count <= 1000; count++) {
    const scale = representativeStarScale(count);
    assert.ok(Number.isFinite(scale) && scale >= 1 && scale <= 3 && scale >= previous, `count=${count}`);
    if (count > 1 && count <= 100) assert.ok(scale > previous, '上限までは厳密に増える');
    previous = scale;
  }
});

test('代表星の件数と大きさ: 再帰ファイルだけを数え、追加・削除・更新後に再計算し配置を変えない', async t => {
  const counts = [0, 1, 2, 10, 99, 100, 101, 12000], data = countFixture(counts), h = space(t, data);
  try {
    await h.ready();
    const original = new Map(h.engine.world.stars.map(body => [body.path, coordinates(body)]));
    assert.equal(h.engine.world.stars.length, counts.length + 1);
    assert.equal(h.engine.world.galaxies[0].files.length, 1 + counts.reduce((sum, count) => sum + count, 0));
    for (const count of counts) {
      const body = h.engine.world.byPath.get(`src/count-${count}`);
      assert.equal(body.fileCount, count);
      close(body.mag, BASE_STAR_MAG * representativeStarScale(count), `${count}ファイルの大きさ`);
      assert.equal(body.size, 0, 'ファイル容量とは独立に件数だけで大きくする');
    }
    const path = 'src/count-2';
    for (const count of [10, 100, 1000, 1, 0]) {
      data.tree.d[0].d[2] = countedFolder('count-2', count);
      h.data(data); await h.engine.refresh();
      const body = h.engine.world.byPath.get(path);
      assert.equal(body.fileCount, count); assert.equal(body.mag, BASE_STAR_MAG * representativeStarScale(count));
      assert.deepEqual(coordinates(body), original.get(path), '件数によって代表星の座標は変えない');
      assert.equal(h.engine.world.stars.length, counts.length + 1, '深い件数で表示天体数は増やさない');
    }
    data.tree.d[0].d[2] = countedFolder('count-2', 10); h.data(data); await h.engine.refresh();
    const before = h.engine.world.byPath.get(path).mag;
    data.tree.d[0].d[2].d[1].d[0].f[0][1] = 1e12;
    data.tree.d[0].d[2].d[1].d[0].f[0][2] = 999999;
    h.data(data); await h.engine.refresh();
    assert.equal(h.engine.world.byPath.get(path).mag, before, '同数の内容・容量・時刻の更新では大きさは変わらない');
  } finally { h.dispose(); }
});

test('代表星のCanvas実寸: 同じズームで通常基準星の最大3倍、空フォルダも表示し遠近倍率を保つ', async t => {
  const counts = [0, 1, 2, 10, 100, 12000], h = space(t, countFixture(counts));
  try {
    await h.ready(); h.engine.marks({ mode: 'since', since: null }); positionSizeSamples(h);
    const reference = h.engine.world.byPath.get('src/reference.png');
    assert.equal(reference.mag, BASE_STAR_MAG); assert.equal(reference.isDirectory, undefined);
    let previous;
    for (const distance of [600, 1200]) {
      h.engine.cam.dist = h.engine.goal.dist = distance;
      await drawFrame(h);
      const baseline = renderedStar(h, reference), current = [];
      close(baseline.diameter, BASE_STAR_MAG * (840 / distance) * 4, '通常星の描画寸法');
      for (const count of counts) {
        const sample = renderedStar(h, h.engine.world.byPath.get(`src/count-${count}`)), scale = representativeStarScale(count);
        close(sample.diameter / baseline.diameter, scale, `${count}件の画像直径比`);
        close(sample.coreDiameter / baseline.coreDiameter, scale, `${count}件の不透明本体直径比`);
        assert.ok(sample.diameter <= baseline.diameter * 3 && sample.coreDiameter <= baseline.coreDiameter * 3 + 1e-9);
        assert.ok(sample.coreDiameter > 0, '空フォルダを含め本体を描く');
        current.push(sample.diameter);
      }
      if (previous) current.forEach((size, index) => close(previous[index] / size, 2, '距離2倍で直径は半分'));
      previous = current;
    }
  } finally { h.dispose(); }
});

test('代表星の新規・更新強調: Canvas画像と不透明本体は常に最大3倍、光輪は6秒で終了する', async t => {
  const counts = [1, 10, 100], data = countFixture(counts), h = space(t, data);
  try {
    await h.ready(); h.engine.marks({ mode: 'since', since: null }); positionSizeSamples(h); await drawFrame(h);
    const baseline = renderedStar(h, h.engine.world.byPath.get('src/reference.png'));
    const verify = () => {
      for (const count of counts) {
        const body = h.engine.world.byPath.get(`src/count-${count}`), drawn = renderedStar(h, body);
        close(drawn.diameter / baseline.diameter, representativeStarScale(body.fileCount), '強調中も画像は件数どおり');
        close(drawn.coreDiameter / baseline.coreDiameter, representativeStarScale(body.fileCount), '強調中も本体は件数どおり');
        assert.ok(drawn.diameter <= baseline.diameter * 3 && drawn.coreDiameter <= baseline.coreDiameter * 3 + 1e-9);
      }
    };
    // 同数のパス置換で新規ファイルを発生させ、件数による直径は変えずに6秒の演出を検証する。
    for (const folder of data.tree.d[0].d) folder.d[1].d[0].f[0][0] = 'newborn.png';
    h.data(data); await h.engine.refresh(); positionSizeSamples(h);
    assert.ok(counts.every(count => h.engine.world.byPath.get(`src/count-${count}`).born > 0));
    for (const ms of [0, 100, 2800, 3000]) {
      await drawFrame(h, ms); verify();
      for (const count of counts) assert.equal(renderedStar(h, h.engine.world.byPath.get(`src/count-${count}`)).images.length, 2, '生後6秒未満は星画像に光輪を重ねる');
    }
    await drawFrame(h, 100); verify();
    for (const count of counts) assert.equal(renderedStar(h, h.engine.world.byPath.get(`src/count-${count}`)).images.length, 1, '生後6秒で新規光輪を終える');
    for (const mode of ['since', 'grep', 'ai']) {
      h.engine.marks(mode === 'since' ? { mode, since: 0 } : { mode, paths: counts.map(count => `src/count-${count}/nested/deep/newborn.png`) });
      for (const ms of [0, 400, 500, 600, 700, 800]) { await drawFrame(h, ms); verify(); }
    }
    // 新規と更新が同時でも上限を保つ。
    data.tree.d[0].d[2].d[1].d[0].f.push(['another.png', 0, 100]);
    h.data(data); await h.engine.refresh(); positionSizeSamples(h); h.engine.marks({ mode: 'since', since: 0 });
    await drawFrame(h); verify();
    assert.equal(h.engine.world.byPath.get('src/count-100').fileCount, 101);
  } finally { h.dispose(); }
});

test('通常ファイル星の大きさと新規・更新パルスは従来どおり', async t => {
  const h = space(t, countFixture([1]));
  try {
    await h.ready(); h.engine.marks({ mode: 'since', since: null }); positionSizeSamples(h);
    const reference = h.engine.world.byPath.get('src/reference.png');
    await drawFrame(h); const baseline = renderedStar(h, reference);
    h.engine.marks({ mode: 'grep', paths: ['src/reference.png'] });
    await drawFrame(h);
    const blink = 0.5 + 0.5 * Math.sin(performance.now() / 1000 * 1.8), fresh = renderedStar(h, reference);
    close(fresh.diameter / baseline.diameter, 1 + 0.08 * blink, '通常ファイルの更新サイズパルスは維持');
    close(fresh.coreDiameter / baseline.coreDiameter, 1 + 0.08 * blink, '通常ファイルの本体パルスは維持');
    h.engine.marks({ mode: 'since', since: null }); reference.born = performance.now();
    await drawFrame(h);
    close(renderedStar(h, reference).diameter / baseline.diameter, 4, '通常ファイルの既存新規サイズ計算は維持');
  } finally { h.dispose(); }
});

test('3D表示深度: 直下は惑星、子の直下ファイルは星、孫の各部分木と空フォルダは代表星1つ', async t => {
  const h = space(t);
  try {
    await h.ready();
    const { world } = h.engine, src = world.galaxies.find(g => g.path === 'src');
    assert.deepEqual(world.planets.map(p => p.path), ['root.js']);
    assert.deepEqual(src.stars.map(s => s.path), ['src/main.js', 'src/nested', 'src/empty']);
    assert.equal(world.stars.length, 3); assert.equal(world.byPath.size, 4);
    assert.equal(src.files.length, 3); assert.equal(src.sub, 2); assert.equal(src.fresh, 2);
    const nested = world.byPath.get('src/nested'), empty = world.byPath.get('src/empty');
    assert.equal(nested.isDirectory, true); assert.equal(nested.fileCount, 2); assert.equal(nested.mtime, 300); assert.equal(nested.size, 110);
    assert.equal(nested.fresh, 2); assert.equal(empty.fileCount, 0); assert.equal(empty.fresh, 0);
    for (const body of world.stars) for (const value of ['x', 'y', 'z', 'mag', 'glow', 'mtime']) assert.ok(Number.isFinite(body[value]), `${body.path}.${value}`);
    assert.equal(world.byPath.has('src/nested/deeper/deep.py'), false, '深いファイルの3D天体は作らない');
    assert.equal(h.state().scan.tree.d[0].d[0].d[0].f[0][0], 'deep.py', '全走査結果は保持する');
    assert.ok(h.texts.some(([name]) => name === 'src (3)'), '銀河ラベルは代表星数ではなく全ファイル数');
    const before = new Map([...world.planets, ...world.stars].map(body => [body.path, coordinates(body)]));
    const data = fixture(); data.tree.d[0].d[0].d[0].f.push(['another.py', 90, 400]);
    h.data(data); await h.engine.refresh();
    assert.equal(h.engine.world.stars.length, 3); assert.equal(h.engine.world.galaxies[0].files.length, 4);
    for (const body of [...h.engine.world.planets, ...h.engine.world.stars]) assert.deepEqual(coordinates(body), before.get(body.path), '件数増加で既存配置を動かさない');
    assert.ok(h.engine.world.byPath.get('src/nested').born > 0, '新規の深いファイルは代表星で通知');
    await h.engine.refresh(); assert.equal(h.engine.world.byPath.get('src/nested').born, 0, '代表フォルダを毎回新規扱いしない');
    data.tree.d[0].d = [dir('new-empty')]; h.data(data); await h.engine.refresh();
    assert.deepEqual(h.engine.world.stars.map(body => body.path), ['src/main.js', 'src/new-empty']);
    assert.equal(h.engine.world.galaxies[0].files.length, 1); assert.equal(h.engine.world.byPath.has('src/nested'), false);
  } finally { h.dispose(); }
});

test('深い更新/grep/AI: 代表星と銀河は全ファイルから正確に再集計し、描画時には配下を読まない', async t => {
  const h = space(t);
  try {
    await h.ready();
    const g = h.engine.world.galaxies[0], representative = h.engine.world.byPath.get('src/nested');
    for (const [marks, count] of [
      [{ mode: 'since', since: 250 }, 1],
      [{ mode: 'grep', paths: ['src/nested/deeper/deep.py', 'src/nested/note.txt', 'src/nested-extra/no.py'] }, 2],
      [{ mode: 'ai', paths: ['src/nested/deeper/deep.py'] }, 1],
      [{ mode: 'since', since: null }, 0],
    ]) {
      h.engine.marks(marks); assert.equal(g.fresh, count); assert.equal(representative.fresh, count);
    }
    h.engine.marks({ mode: 'grep', paths: ['src/nested/deeper/deep.py'] });
    t.mock.method(Math, 'log10', () => assert.fail('件数の対数倍率は構築時に計算し、描画・hover中には計算しない'));
    for (const file of g.files) for (const key of ['path', 'mtime']) Object.defineProperty(file, key, { get() { assert.fail('描画・hover中に全ファイルのメタデータを再走査しない'); } });
    const blockTraversal = node => {
      for (const child of node.d) blockTraversal(child);
      for (const key of ['d', 'f']) Object.defineProperty(node, key, { get() { assert.fail('描画・hover中に走査ツリーを再帰しない'); } });
    };
    blockTraversal(h.state().scan.tree);
    for (let n = 0; n < 5; n++) await h.pump();
    h.canvas.dispatchEvent(event('pointermove', { pointerId: 1, clientX: 30, clientY: 30 }));
    assert.equal(representative.fresh, 1);
  } finally { h.dispose(); }
});

for (const action of ['click', 'double-click', 'approach']) test(`代表星の${action}: 隠れた先行天体があっても正しいフォルダへ移動し、ファイルを開かない`, async t => {
  const h = space(t);
  try {
    await h.ready(); h.engine.marks({ mode: 'since', since: null });
    const world = h.engine.world, g = world.galaxies[0], representative = world.byPath.get('src/nested');
    Object.assign(g, { x: 200, y: 0, z: 0 });
    Object.assign(world.galaxies[1], { x: -10000, y: 0, z: 0 });
    Object.assign(world.planets[0], { x: -10000, y: 0, z: 0 });
    Object.assign(world.byPath.get('src/main.js'), { x: 0, y: 0, z: -1000 });
    Object.assign(representative, { x: 180, y: 30, z: 0 });
    Object.assign(world.byPath.get('src/empty'), { x: 200, y: -50, z: 0 });
    h.camera(); await h.pump();
    const pointer = { pointerId: 1, clientX: 892, clientY: 358 };
    h.canvas.dispatchEvent(event('pointermove', pointer));
    assert.equal(h.tipNodes['.t-name'].textContent, 'src/nested'); assert.match(h.tipNodes['.t-sub'].textContent, /フォルダ.*ファイル 2.*クリックで開く/);
    if (action === 'click') { h.canvas.dispatchEvent(event('pointerdown', pointer)); h.canvas.dispatchEvent(event('pointerup', pointer)); }
    else if (action === 'double-click') h.canvas.dispatchEvent(event('dblclick', pointer));
    else await h.finish(h.engine.approach(representative));
    await h.until(() => h.engine.trail.join('/') === 'src/nested' && h.idle());
    assert.equal(h.engine.selected, null); assert.equal(h.location.hash, '#/src/nested');
    assert.equal(h.state().journal[0].type, 'dir'); assert.equal(h.state().journal[0].path, 'src/nested');
    assert.ok(h.requests.every(request => request.url.startsWith('/api/galaxy')));
    assert.deepEqual(h.engine.world.planets.map(body => body.path), ['src/nested/note.txt']);
    assert.equal(h.engine.world.byPath.get('src/nested/deeper/deep.py').isDirectory, undefined, '入った階層では子の直下ファイルを個別の星に戻す');
  } finally { h.dispose(); }
});

test('空の代表星も移動でき、深い検索・閲覧履歴・latest・新規/削除パスは本来の親へ解決する', async t => {
  const h = space(t);
  try {
    await h.ready(); h.engine.setFastWarp(true);
    await h.finish(h.engine.approach(h.engine.world.byPath.get('src/empty')));
    assert.deepEqual(h.engine.trail, ['src', 'empty']); assert.equal(h.engine.world.stars.length, 0); assert.equal(h.engine.selected, null);
    for (const source of ['grep', 'ai', 'history', 'latest']) {
      await h.finish(h.engine.goTo({ type: 'dir', path: '' }));
      const entry = { type: 'file', path: 'src/nested/deeper/deep.py', source, line: 9, column: 2, query: 'needle', matchMtime: 300, matchLength: 6 };
      assert.equal(await h.finish(h.engine.goTo(entry)), true);
      assert.deepEqual(h.engine.trail, ['src', 'nested', 'deeper']);
      assert.equal(h.engine.selected.path, entry.path); assert.equal(h.engine.selected.isDirectory, undefined); assert.equal(h.engine.selected.line, 9);
      assert.equal(h.state().journal[0].type, 'file'); assert.equal(h.state().journal[0].path, entry.path);
      await h.engine.refresh(); assert.equal(h.engine.selected.line, 9);
    }
    const data = fixture(); data.tree.d[0].d[0].d.push(dir('new', [], [dir('inner', [['created.js', 200, 700]])])); h.data(data);
    const path = 'src/nested/new/inner/created.js';
    assert.equal(await h.finish(h.engine.goTo({ type: 'file', path, source: 'latest', mtime: 700 })), true);
    assert.deepEqual(h.engine.trail, ['src', 'nested', 'new', 'inner']); assert.equal(h.engine.selected.path, path); assert.match(h.requests.at(-1).url, /fresh=1/);
    data.tree.d[0].d[0].d.pop(); h.data(data); await h.engine.refresh();
    assert.deepEqual(h.engine.trail, ['src', 'nested']); assert.equal(h.engine.selected, null);
    assert.equal(await h.finish(h.engine.goTo({ type: 'file', path, source: 'history' })), false);
    assert.deepEqual(h.engine.trail, ['src', 'nested']); assert.match(h.errors().at(-1), /見つかりません/);
    h.engine.setViewMode('2d');
    assert.equal(await h.engine.goTo({ type: 'file', path: 'src/nested/deeper/deep.py', source: 'grep', line: 3 }), true);
    assert.deepEqual(h.engine.trail, ['src', 'nested', 'deeper']); assert.equal(h.engine.selected.line, 3); assert.equal(h.frames.size, 0);
  } finally { h.dispose(); }
});

for (const count of [10, 12000]) test(`深い${count}ファイル: 描画天体・投影・drawImage・hover走査は浅い項目数に限定する`, async t => {
  const deep = branch => dir(branch, [], [dir('deep', Array.from({ length: count / 2 }, (_, i) => [`file-${i}.js`, 40, 100]))]);
  const h = space(t, snapshot(dir('project', ['root.js'], [dir('src', ['a.js', 'b.js', 'c.js'], [deep('one'), deep('two')])])));
  try {
    await h.ready(); h.engine.marks({ mode: 'since', since: null });
    const { world } = h.engine, g = world.galaxies[0];
    assert.equal(g.files.length, count + 3); assert.equal(world.stars.length, 5); assert.equal(world.planets.length, 1); assert.equal(world.byPath.size, 6);
    assert.deepEqual([...g.representatives.values()].map(body => body.fileCount), [count / 2, count / 2]);
    Object.assign(g, { x: 200, y: 0, z: 0 });
    Object.assign(world.planets[0], { x: -250, y: -100, z: 0 });
    world.stars.forEach((body, i) => Object.assign(body, { x: 180 + (i % 2) * 35, y: 90 - i * 40, z: 0 }));
    let projections = 0, hitVisits = 0;
    for (const body of world.stars) {
      const x = body.x;
      Object.defineProperty(body, 'x', { get() { projections++; return x; } });
      Object.defineProperty(body, 'isPlanet', { get() { hitVisits++; return false; } });
    }
    // 全ファイルのメタデータを読まず、表示用5天体だけを描画・当たり判定する。
    for (const file of g.files) for (const key of ['path', 'mtime']) Object.defineProperty(file, key, { get() { assert.fail('フレーム中に深いファイルを再走査しない'); } });
    h.camera(); h.draws.length = 0; await h.pump();
    assert.equal(projections, 5); assert.equal(h.draws.length, 10, '星5+銀河2+惑星1+ゲート2のdrawImage');
    hitVisits = 0;
    h.canvas.dispatchEvent(event('pointermove', { pointerId: 1, clientX: 30, clientY: 30 }));
    assert.equal(hitVisits, 5, 'hoverは表示中の星5個だけを調べる');
    t.diagnostic(`${count + 3} descendant files -> 5 stars; 5 star projections, 10 drawImage calls, 5 star hit checks per tested frame/move (CPU% is not measured)`);
  } finally { h.dispose(); }
});


test('保存済みの深い航路: 正確なパス区切りで代表星へ結び、削除・種類変更済みパスは復活しない', async t => {
  const data = fixture(); data.tree.d[0].d.push(dir('nested-extra', ['other.py']));
  const h = space(t, data);
  try {
    h.storage.set('aidiy_ide:/project', JSON.stringify({ voyages: { '': [
      'f:root.js', 'f:src/nested/deeper/deep.py', 'f:src/nested-extra/other.py',
      'f:src/nested/deleted.py', 'f:src/nested', 'g:root.js',
    ] }, journal: [] }));
    await h.ready(); h.engine.marks({ mode: 'since', since: null });
    const root = h.engine.world.byPath.get('root.js'), nested = h.engine.world.byPath.get('src/nested'), sibling = h.engine.world.byPath.get('src/nested-extra');
    Object.assign(root, { x: -250, y: -100, z: 0 }); Object.assign(nested, { x: 180, y: 30, z: 0 }); Object.assign(sibling, { x: 200, y: -50, z: 0 });
    h.camera(); h.routeLines.length = 0; await h.pump();
    assert.deepEqual(h.routeLines, [[892, 358], [920, 470]], '似た名前の隣接フォルダを混同しない');
    data.tree.d[0].d.pop(); h.data(data); await h.engine.refresh();
    Object.assign(h.engine.world.byPath.get('root.js'), { x: -250, y: -100, z: 0 });
    Object.assign(h.engine.world.byPath.get('src/nested'), { x: 180, y: 30, z: 0 });
    h.routeLines.length = 0; await h.pump(); assert.deepEqual(h.routeLines, [[892, 358]]);
  } finally { h.dispose(); }
});

test('古い代表星: 削除後は移動せず、航行中の新しいファイル選択が最後に残る', async t => {
  const h = space(t);
  try {
    await h.ready(); const previous = h.engine.world.byPath.get('src/nested');
    const data = fixture(); data.tree.d[0].d.shift(); h.data(data); await h.engine.refresh();
    assert.equal(await h.finish(h.engine.approach(previous)), false);
    assert.deepEqual(h.engine.trail, []); assert.equal(h.engine.selected, null);
    h.data(fixture()); await h.engine.refresh();
    const first = h.engine.approach(h.engine.world.byPath.get('src/nested'));
    const latest = h.engine.goTo({ type: 'file', path: 'root.js' });
    const result = await h.finish(Promise.all([first, latest]));
    assert.notEqual(result[0], true); assert.equal(result[1], true);
    assert.deepEqual(h.engine.trail, []); assert.equal(h.engine.selected.path, 'root.js');
    for (let n = 0; n < 20; n++) await h.pump(); assert.equal(h.engine.selected.path, 'root.js');
  } finally { h.dispose(); }
});
