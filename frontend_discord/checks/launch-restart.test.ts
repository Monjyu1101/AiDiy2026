import { test } from 'node:test';
import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { runInNewContext } from 'node:vm';

test('終了中のパネルは起動成功とせず、旧プロセス終了後に再起動して表示を確認する', async () => {
  const moduleUrl = new URL('../panel/launch.mjs', import.meta.url).href;
  // 起動コード全体を実行し、Electron・時刻・ファイルだけを置き換える。
  const source = readFileSync(fileURLToPath(moduleUrl), 'utf8').replace(/^import .*;\r?\n/gm, '')
    .replaceAll('import.meta.url', 'moduleUrl').replaceAll('process.exit(', 'return process.exit(');
  const files = new Map<string, string>(), starts: number[] = [], messages: string[] = [];
  let clock = 0, probes = 0, exitCode: number | undefined;
  await runInNewContext(`(async () => { ${source} })()`, {
    moduleUrl, dirname, join, fileURLToPath, pathToFileURL, URL,
    Date: class extends Date { static now() { return clock; } },
    process: { argv: ['node', 'launch.mjs', '--wait', '--connect'], execPath: '/node', platform: 'linux', env: {},
      exit(code: number) { exitCode = code; },
      kill(pid: number, signal: number) {
        assert.equal(pid, 999); assert.equal(signal, 0);
        if (++probes >= 3) throw Object.assign(new Error(), { code: 'ESRCH' });
      },
    },
    console: { log: (value: string) => messages.push(value), error: (value: string) => assert.fail(value) },
    setTimeout(callback: () => void, ms: number) { clock += ms; queueMicrotask(callback); },
    randomUUID: () => 'restart-test', createRequire: () => ({ resolve: () => '/electron/package.json' }),
    mkdirSync() {}, openSync: () => 10, closeSync() {},
    existsSync: (file: string) => file === '/electron/dist/electron' || files.has(file),
    unlinkSync(file: string) { files.delete(file); },
    readFileSync(file: string) {
      if (file === '/electron/package.json') return '{"version":"1.0.0"}';
      if (file === '/electron/path.txt') return 'electron';
      if (file === '/electron/dist/version') return '1.0.0';
      assert.ok(files.has(file)); return files.get(file);
    },
    spawnSync: () => ({ status: 0 }),
    spawn(_executable: string, _args: string[], options: any) {
      assert.equal(options.env.AIDIY_DISCORD_CONNECT, '1');
      starts.push(clock);
      files.set(options.env.AIDIY_DISCORD_READY, JSON.stringify(starts.length === 1 ? { closing: true, pid: 999 } : { windowShown: true }));
      // --wait でも、シグナル終了済みの子の exit を再度待たない。
      return Object.assign(new EventEmitter(), { exitCode: null, signalCode: 'SIGTERM', unref() {} });
    },
  });
  assert.equal(exitCode, 0);
  assert.deepEqual(starts, [0, 200]);
  assert.equal(messages.length, 1); assert.match(messages[0], /パネルを開き/);
});
