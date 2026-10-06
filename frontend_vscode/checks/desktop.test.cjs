const assert = require('node:assert/strict');
const { EventEmitter } = require('node:events');
const { readFileSync } = require('node:fs');
const path = require('node:path');
const { test } = require('node:test');
const vm = require('node:vm');

async function launch({ loadError, visible = true, module = 'aidiy_code', env = {} } = {}) {
  const calls = [];
  const written = [];
  const errors = [];
  const sizes = [], minimums = [], states = [];
  const serverArgs = [], files = [];
  const live = module === 'aidiy_live';
  let clock = 0;
  const app = new EventEmitter();
  Object.assign(app, {
    setName() {}, setPath() {}, setAppUserModelId() {}, getPath: () => '/tmp',
    whenReady: async () => {}, quit: () => calls.push('quit'),
  });
  class Window extends EventEmitter {
    constructor(options) {
      super();
      assert.equal(options.frame, false);
      if (!live) assert.equal(options.roundedCorners, false);
      assert.equal(options.x, live ? 1528 : 100); assert.equal(options.y, 200);
      this.bounds = { x: options.x, y: options.y, width: options.width, height: options.height };
      this.webContents = new EventEmitter();
      Object.assign(this.webContents, {
        send(_channel, state) { states.push(JSON.parse(JSON.stringify(state))); }, setWindowOpenHandler() {},
        session: { setPermissionRequestHandler() {}, setPermissionCheckHandler() {} },
      });
    }
    setMenu() {}
    getBounds() { return this.bounds; }
    setBounds(bounds) { this.bounds = bounds; sizes.push(JSON.parse(JSON.stringify(bounds))); }
    setMinimumSize(width, height) { minimums.push([width, height]); }
    isDestroyed() { return false; }
    isMaximized() { return false; }
    async loadURL() { calls.push('load'); if (loadError) throw new Error(loadError); }
    show() { calls.push('show'); }
    focus() { calls.push('focus'); }
    isVisible() { return visible && calls.includes('show'); }
  }
  const filename = path.resolve(__dirname, '..', module, 'desktop.cjs');
  const fakeProcess = { argv: live ? ['electron', filename] : ['electron', filename, '/project', '/ready.json'], env, platform: 'win32', pid: 123 };
  vm.runInNewContext(readFileSync(filename, 'utf8'), {
    __filename: filename, __dirname: path.dirname(filename), process: fakeProcess,
    Date: class extends Date { static now() { return clock; } },
    setTimeout: (callback, milliseconds) => { clock += milliseconds; return setImmediate(callback); },
    console: { error: error => errors.push(String(error)) },
    require(name) {
      if (name === 'electron') return {
        app, BrowserWindow: Window, ipcMain: { handle() {} }, shell: {},
        screen: {
          getCursorScreenPoint: () => ({ x: 300, y: 400 }),
          getDisplayNearestPoint: () => ({ workArea: { x: 92, y: 192, width: 1920, height: 1080 } }),
        },
      };
      if (name === 'node:fs') return { writeFileSync: (file, value) => { calls.push('ready'); files.push(file); written.push(JSON.parse(value)); } };
      if (name === `../dist/${module}/server.cjs`) return { [live ? 'ライブ起動' : '単独起動']: async (...args) => {
        serverArgs.push(JSON.parse(JSON.stringify(args)));
        return { url: 'http://127.0.0.1:1234/', close: async () => {} };
      } };
      if (name === './permissions.cjs') return require('../aidiy_live/permissions.cjs');
      return require(name);
    },
  });
  for (let i = 0; i < 100 && !written.length && !errors.length; i++) await new Promise(resolve => setImmediate(resolve));
  return { calls, written, errors, fakeProcess, sizes, minimums, states, serverArgs, files };
}

test('Code: 作業フォルダ・モデル・起動完了ファイルを環境変数から読み取る', async () => {
  const project = path.resolve('日本語 project');
  const models = { provider: 'copilot-cli', model: 'claude-sonnet-5.5' };
  const result = await launch({ env: {
    AIDIY_CODE_PROJECT: project, AIDIY_CODE_READY: '/ready with spaces.json', AIDIY_CODE_MODEL: JSON.stringify(models),
  } });
  assert.deepEqual(result.errors, []);
  assert.deepEqual(result.serverArgs[0], [project, null, models]);
  assert.deepEqual(result.files, ['/ready with spaces.json']);
  assert.equal(result.written[0].windowShown, true);
});

test('Live: 追加の起動引数なしで接続先・作業フォルダ・モデル・起動完了ファイルを読み取る', async () => {
  const models = { LIVE_AI_NAME: 'openai_live', LIVE_OPENAI_MODEL: 'gpt-realtime-2.1-mini' };
  const result = await launch({ module: 'aidiy_live', env: {
    AIDIY_LIVE_BACKEND: 'http://127.0.0.1:9091', AIDIY_LIVE_READY: '/ready with spaces.json',
    AIDIY_LIVE_PROJECT: '日本語 project', AIDIY_LIVE_MODELS: JSON.stringify(models),
  } });
  assert.deepEqual(result.errors, []);
  assert.deepEqual(result.serverArgs[0].slice(1), ['http://127.0.0.1:9091', false, '日本語 project', models]);
  assert.deepEqual(result.files, ['/ready with spaces.json']);
  assert.equal(result.written[0].windowShown, true);
});

test('window is shown and focused without waiting for ready-to-show, before notifying launcher', async () => {
  const result = await launch();
  assert.deepEqual(result.calls, ['load', 'show', 'focus', 'ready']);
  assert.equal(result.written[0].windowShown, true);
  assert.deepEqual(result.errors, []);
  assert.deepEqual(result.minimums, [[0, 0], [360, 480]]);
  assert.ok(result.sizes[0].width < 476 && result.sizes[0].height < 602);
  assert.deepEqual(result.sizes.at(-1), { x: 100, y: 200, width: 476, height: 602 });
  result.sizes.forEach((size, index) => {
    assert.ok(Math.abs(size.x + size.width / 2 - 338) <= .5);
    assert.ok(Math.abs(size.y + size.height / 2 - 501) <= .5);
    if (index) assert.ok(size.width >= result.sizes[index - 1].width && size.height >= result.sizes[index - 1].height);
  });
  assert.deepEqual(result.states.at(-1), { maximized: false, opening: false });
});

test('failed page load produces no startup success notification', async () => {
  const result = await launch({ loadError: 'load failed' });
  assert.equal(result.written.length, 0);
  assert.equal(result.fakeProcess.exitCode, 1);
  assert.match(result.errors[0], /load failed/);
});

test('hidden window produces no startup success notification', async () => {
  const result = await launch({ visible: false });
  assert.equal(result.written.length, 0);
  assert.equal(result.fakeProcess.exitCode, 1);
  assert.match(result.errors[0], /専用ウィンドウを表示できません/);
});
