/*!
 * -*- coding: utf-8 -*-
 *
 * -------------------------------------------------------------------------
 * COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
 * Licensed under "AiDiy 公開利用ライセンス v1.1".
 * Commercial use requires prior written consent from all copyright holders.
 * See LICENSE for full terms. Thank you for keeping the rules.
 * https://github.com/monjyu1101/AiDiy2026
 * -------------------------------------------------------------------------
 */

const assert = require('node:assert/strict');
const { EventEmitter } = require('node:events');
const { readFileSync } = require('node:fs');
const path = require('node:path');
const { test } = require('node:test');
const vm = require('node:vm');

async function launch({ loadError, visible = true, module = 'aidiy_code', env = {}, owned = true } = {}) {
  const calls = [];
  const written = [];
  const errors = [];
  const sizes = [], minimums = [], states = [], canvases = [], opacities = [];
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
      // 初回演出のキャンバス用ウィンドウ（透明・最終位置・最終サイズ）。
      this.canvas = !!options.transparent;
      if (this.canvas) canvases.push(JSON.parse(JSON.stringify(options)));
      assert.equal(options.frame, false);
      if (!live && !this.canvas) assert.equal(options.roundedCorners, false);
      assert.equal(options.x, live ? 1528 : 100); assert.equal(options.y, 200);
      this.bounds = { x: options.x, y: options.y, width: options.width, height: options.height };
      this.webContents = new EventEmitter();
      Object.assign(this.webContents, {
        send(_channel, state) { states.push(JSON.parse(JSON.stringify(state))); }, setWindowOpenHandler() {},
        session: { setPermissionRequestHandler() {}, setPermissionCheckHandler() {} },
        executeJavaScript: async () => {},
      });
    }
    setMenu() {}
    getBounds() { return this.bounds; }
    setBounds(bounds) { this.bounds = bounds; sizes.push(JSON.parse(JSON.stringify(bounds))); }
    setMinimumSize(width, height) { minimums.push([width, height]); }
    isDestroyed() { return !!this.destroyed; }
    isMinimized() { return false; }
    restore() { calls.push('restore'); }
    isMaximized() { return false; }
    async loadURL() { if (this.canvas) { calls.push('canvas'); return; } calls.push('load'); if (loadError) throw new Error(loadError); }
    showInactive() { calls.push('canvas-show'); }
    setOpacity(value) { opacities.push(value); }
    destroy() { calls.push('canvas-close'); this.destroyed = true; }
    show() { calls.push('show'); }
    focus() { calls.push('focus'); }
    isVisible() { return visible && calls.includes('show'); }
  }
  const filename = path.resolve(__dirname, '..', module, 'desktop.cjs');
  const fakeProcess = { argv: live ? ['electron', filename] : ['electron', filename, '/project', '/ready.json'], env, platform: 'win32', pid: 123, cwd: () => '/project' };
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
      if (name === '../scripts/single-instance.cjs') return { 起動ロック: async () => owned ? { close: async () => {} } : null };
      // 初回演出は実物を、時刻だけ模擬した環境で動かす。
      if (name === '../scripts/window-opening.cjs') {
        const loaded = { exports: {} };
        vm.runInNewContext(readFileSync(path.join(__dirname, '../scripts/window-opening.cjs'), 'utf8'), {
          module: loaded, exports: loaded.exports, setTimeout: (callback, milliseconds) => { clock += milliseconds; return setImmediate(callback); },
        });
        return loaded.exports;
      }
      return require(name);
    },
  });
  for (let i = 0; i < 100 && !written.length && !errors.length; i++) await new Promise(resolve => setImmediate(resolve));
  return { calls, written, errors, fakeProcess, sizes, minimums, states, serverArgs, files, canvases, opacities };
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
    AIDIY_LIVE_PROJECT: '日本語 project', AIDIY_LIVE_MODELS: JSON.stringify(models), AIDIY_LIVE_CONNECT: '1',
  } });
  assert.deepEqual(result.errors, []);
  assert.deepEqual(result.serverArgs[0].slice(1), ['http://127.0.0.1:9091', false, '日本語 project', models, null, true]);
  assert.deepEqual(result.files, ['/ready with spaces.json']);
  assert.equal(result.written[0].windowShown, true);
});

test('Live: 既存プロセスがあると画面と接続を作らず、ランチャーへ起動済みを通知する', async () => {
  const result = await launch({ module: 'aidiy_live', owned: false, env: { AIDIY_LIVE_READY: '/repeat.json' } });
  assert.deepEqual(result.serverArgs, []);
  assert.deepEqual(result.canvases, []);
  assert.deepEqual(result.written, [{ alreadyRunning: true }]);
  assert.ok(result.calls.includes('quit'));
  assert.deepEqual(result.errors, []);
});

test('window is shown and focused without waiting for ready-to-show, before notifying launcher', async () => {
  const result = await launch();
  // 透明なキャンバスで拡大した後、実ウィンドウを透明のまま表示し、描画後に見せる（大きさは変えない）。
  assert.deepEqual(result.calls.filter(call => call !== 'canvas-close'), ['load', 'canvas', 'canvas-show', 'show', 'focus', 'ready']);
  assert.equal(result.written[0].windowShown, true);
  assert.deepEqual(result.errors, []);
  assert.equal(result.canvases.length, 1);
  const canvas = result.canvases[0];
  assert.deepEqual([canvas.x, canvas.y, canvas.width, canvas.height], [100, 200, 476, 602]);
  assert.equal(canvas.backgroundColor, '#00000000');
  assert.equal(canvas.focusable, undefined, '透明部分が白くなるため focusable: false は付けない');
  assert.deepEqual(result.sizes, [], '実ウィンドウは拡大のために大きさを変えない');
  assert.deepEqual(result.minimums, []);
  assert.deepEqual(result.opacities, [0, 1]);
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
