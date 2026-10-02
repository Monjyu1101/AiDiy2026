const assert = require('node:assert/strict');
const { EventEmitter } = require('node:events');
const { readFileSync } = require('node:fs');
const path = require('node:path');
const { test } = require('node:test');
const vm = require('node:vm');

async function launch({ loadError, visible = true } = {}) {
  const calls = [];
  const written = [];
  const errors = [];
  const app = new EventEmitter();
  Object.assign(app, {
    setName() {}, setPath() {}, setAppUserModelId() {}, getPath: () => '/tmp',
    whenReady: async () => {}, quit: () => calls.push('quit'),
  });
  class Window extends EventEmitter {
    constructor(options) {
      super();
      assert.equal(options.frame, false);
      this.webContents = new EventEmitter();
      Object.assign(this.webContents, {
        send() {}, setWindowOpenHandler() {},
        session: { setPermissionRequestHandler() {}, setPermissionCheckHandler() {} },
      });
    }
    setMenu() {}
    async loadURL() { calls.push('load'); if (loadError) throw new Error(loadError); }
    show() { calls.push('show'); }
    focus() { calls.push('focus'); }
    isVisible() { return visible && calls.includes('show'); }
  }
  const filename = path.resolve(__dirname, '../standalone/desktop.cjs');
  const fakeProcess = { argv: ['electron', filename, '/project', '/ready.json'], platform: 'win32', pid: 123 };
  vm.runInNewContext(readFileSync(filename, 'utf8'), {
    __filename: filename, __dirname: path.dirname(filename), process: fakeProcess,
    console: { error: error => errors.push(String(error)) },
    require(name) {
      if (name === 'electron') return { app, BrowserWindow: Window, ipcMain: { handle() {} }, shell: {} };
      if (name === 'node:fs') return { writeFileSync: (file, value) => { calls.push('ready'); written.push(JSON.parse(value)); } };
      if (name === '../dist/standalone.cjs') return { 単独起動: async () => ({ url: 'http://127.0.0.1:1234/', close: async () => {} }) };
      return require(name);
    },
  });
  await new Promise(resolve => setImmediate(resolve));
  return { calls, written, errors, fakeProcess };
}

test('window is shown and focused without waiting for ready-to-show, before notifying launcher', async () => {
  const result = await launch();
  assert.deepEqual(result.calls, ['load', 'show', 'focus', 'ready']);
  assert.equal(result.written[0].windowShown, true);
  assert.deepEqual(result.errors, []);
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
