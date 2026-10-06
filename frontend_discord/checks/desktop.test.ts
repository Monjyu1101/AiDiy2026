import { test } from 'node:test';
import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import { readFileSync } from 'node:fs';
import { dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import * as path from 'node:path';
import * as url from 'node:url';
import { runInNewContext } from 'node:vm';

async function desktop(platform = 'win32') {
  const file = fileURLToPath(new URL('../panel/desktop.cjs', import.meta.url));
  const timers = new Map<number, { at: number; callback: () => void }>();
  const files = new Map<string, any>(), requests: any[] = [], kills: any[] = [], states: any[] = [];
  const handlers = new Map<string, (...args: any[]) => any>();
  let clock = 0, sequence = 0, window: any, exited = false, locked = false;
  const worker = Object.assign(new EventEmitter(), {
    pid: 1234 as number | undefined, connected: true, exitCode: null as number | null, signalCode: null as string | null,
    send(message: any, callback: (error?: Error) => void) { requests.push(message); callback(); },
    kill(signal?: string) { kills.push(['worker', signal]); },
  });
  const app = Object.assign(new EventEmitter(), {
    setName() {}, setPath() {}, setAppUserModelId() {}, getPath: () => '/tmp', whenReady: async () => {},
    requestSingleInstanceLock() { locked = true; return true; },
    quit() {
      let prevented = false;
      app.emit('before-quit', { preventDefault() { prevented = true; } });
      if (!prevented) { exited = true; locked = false; if (window) window.destroyed = true; }
    },
  });
  class Window extends EventEmitter {
    destroyed = false;
    webContents = Object.assign(new EventEmitter(), {
      mainFrame: { url: url.pathToFileURL(path.join(dirname(file), 'index.html')).href },
      send(_name: string, state: any) { states.push(state); },
      session: { setPermissionCheckHandler() {}, setPermissionRequestHandler() {} }, setWindowOpenHandler() {},
    });
    constructor(_options: any) { super(); window = this; }
    setMenu() {} setPosition() {} show() {} focus() {} restore() {} minimize() {}
    getBounds() { return { width: 476 }; }
    isDestroyed() { return this.destroyed; } isMinimized() { return false; } isVisible() { return !this.destroyed; }
    async loadURL() {}
    close() {
      let prevented = false;
      this.emit('close', { preventDefault() { prevented = true; } });
      if (!prevented) { this.destroyed = true; app.emit('window-all-closed'); }
    }
  }
  runInNewContext(readFileSync(file, 'utf8'), {
    __dirname: dirname(file), console,
    process: { platform, pid: 999, env: { AIDIY_DISCORD_READY: '/first-ready' }, kill: (...args: any[]) => { kills.push(args); } },
    setTimeout(callback: () => void, ms: number) { const id = ++sequence; timers.set(id, { at: clock + ms, callback }); return id; },
    clearTimeout(id: number) { timers.delete(id); },
    require(name: string) {
      if (name === 'node:path') return path;
      if (name === 'node:url') return url;
      if (name === 'node:fs') return { writeFileSync(file: string, value: string) { files.set(file, JSON.parse(value)); } };
      if (name === 'node:child_process') return { fork: () => worker, spawn: (...args: any[]) => {
        kills.push(args); return Object.assign(new EventEmitter(), { kill() {} });
      } };
      if (name === 'electron') return { app, BrowserWindow: Window, ipcMain: { handle(name: string, callback: (...args: any[]) => any) { handlers.set(name, callback); } },
        screen: { getCursorScreenPoint: () => ({}), getDisplayNearestPoint: () => ({ workArea: { x: 0, y: 0, width: 1920, height: 1080 } }) } };
      throw new Error(name);
    },
  });
  const flush = () => new Promise(resolve => setImmediate(resolve));
  await flush();
  return { app, worker, window, files, requests, kills, states, timers, flush,
    exited: () => exited, locked: () => locked,
    exitWorker(code: number | null, signal: string | null = null) {
      worker.exitCode = code; worker.signalCode = signal; worker.connected = false; worker.emit('exit', code, signal);
    },
    async advance(ms: number) {
      const end = clock + ms;
      while (true) {
        const entry = [...timers.entries()].filter(([, value]) => value.at <= end).sort((a, b) => a[1].at - b[1].at)[0];
        if (!entry) break;
        clock = entry[1].at; timers.delete(entry[0]); entry[1].callback(); await flush();
      }
      clock = end;
    },
  };
}

test('閉じる連打でも接続回収は1回、完了までは画面を保持し、終了後に起動ロックを解放する', async () => {
  const f = await desktop();
  f.window.close(); f.window.close(); f.app.quit();
  assert.equal(f.window.destroyed, false); assert.equal(f.exited(), false);
  assert.equal(f.requests.filter(item => item.action === 'shutdown').length, 1);
  assert.equal(f.states.at(-1).phase, 'stopping');
  f.app.emit('second-instance', {}, [], '', { readyFile: '/reopen-ready', autoConnect: true });
  assert.deepEqual(f.files.get('/reopen-ready'), { closing: true, pid: 999 });
  f.exitWorker(0); await f.flush();
  assert.equal(f.exited(), true); assert.equal(f.locked(), false); assert.equal(f.timers.size, 0);
});

test('workerが先にシグナル終了・起動失敗していても存在しないexitイベントを待たない', async () => {
  for (const failedToSpawn of [false, true]) {
    const f = await desktop();
    if (failedToSpawn) { f.worker.pid = undefined; f.worker.emit('error', new Error('spawn failed')); }
    else f.exitWorker(null, 'SIGTERM');
    f.window.close(); await f.flush();
    assert.equal(f.exited(), true); assert.equal(f.locked(), false); assert.equal(f.timers.size, 0);
  }
});

test('workerが応答しない場合は対象だけを強制終了し、exit通知が来なくても無期限に待たない', async () => {
  for (const platform of ['win32', 'linux']) {
    const f = await desktop(platform);
    f.window.close(); await f.advance(15000);
    assert.equal(f.exited(), false);
    if (platform === 'win32') {
      assert.equal(f.kills[0][0], 'taskkill'); assert.deepEqual(Array.from(f.kills[0][1]), ['/PID', '1234', '/T', '/F']);
    } else assert.deepEqual(f.kills[0], [-1234, 'SIGKILL']);
    await f.advance(3000);
    assert.equal(f.exited(), true); assert.equal(f.locked(), false);
  }
});
