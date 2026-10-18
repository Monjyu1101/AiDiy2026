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

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import { readFileSync } from 'node:fs';
import { posix } from 'node:path';
// テスト内の模擬パスは / 区切りのため、Windows でも posix の結合を使う。
const { dirname, join } = posix;
import { fileURLToPath, pathToFileURL } from 'node:url';
import { runInNewContext } from 'node:vm';
import { parseArgs } from 'node:util';

type 起動記録 = { executable: string; args: string[]; options: any };

// 起動コード全体を実行し、Electron・時刻・ファイル・共通の起動処理だけを置き換える。
async function 起動実行(options: { argv: string[]; electron: boolean; ready: (count: number) => object }) {
  const moduleUrl = new URL('../panel/launch.mjs', import.meta.url).href;
  const source = readFileSync(fileURLToPath(moduleUrl), 'utf8').replace(/^import .*;\r?\n/gm, '')
    .replaceAll('import.meta.url', 'moduleUrl').replaceAll('process.exit(', 'return process.exit(');
  const files = new Map<string, string>(), starts: number[] = [], spawned: 起動記録[] = [];
  const messages: string[] = [], warnings: string[] = [], opened: string[] = [];
  let clock = 0, probes = 0, exitCode: number | undefined;
  await runInNewContext(`(async () => { ${source} })()`, {
    moduleUrl, dirname, join, fileURLToPath, pathToFileURL, URL, parseArgs,
    プロジェクト引数書式: '[作業フォルダ]', プロジェクトフォルダ決定: () => '/project', ブラウザ自動判定: () => false,
    ブラウザ版表示: async (url: string) => { opened.push(url); return true; },
    ブラウザ版へ切替: (error: Error) => { warnings.push(error.message); }, ウィンドウ: { パネル高さ: 414 },
    Date: class extends Date { static now() { return clock; } },
    process: { argv: ['node', 'launch.mjs', ...options.argv], execPath: '/node', platform: 'linux', env: {},
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
    existsSync: (file: string) => (options.electron && file === '/electron/dist/electron') || files.has(file),
    unlinkSync(file: string) { files.delete(file); },
    readFileSync(file: string) {
      if (file === '/electron/package.json') return '{"version":"1.0.0"}';
      if (file === '/electron/path.txt') return 'electron';
      if (file === '/electron/dist/version') return '1.0.0';
      assert.ok(files.has(file)); return files.get(file);
    },
    spawnSync: () => ({ status: 0 }),
    spawn(executable: string, args: string[], spawnOptions: any) {
      spawned.push({ executable, args, options: spawnOptions });
      starts.push(clock);
      files.set(spawnOptions.env.AIDIY_DISCORD_READY, JSON.stringify(options.ready(starts.length)));
      // --wait でも、シグナル終了済みの子の exit を再度待たない。
      return Object.assign(new EventEmitter(), { exitCode: null, signalCode: 'SIGTERM', unref() {} });
    },
  });
  return { exitCode, starts, spawned, messages, warnings, opened };
}

test('終了中のパネルは起動成功とせず、旧プロセス終了後に再起動して表示を確認する', async () => {
  const result = await 起動実行({ argv: ['--wait', '--connect'], electron: true, ready: count => count === 1 ? { closing: true, pid: 999 } : { windowShown: true } });
  assert.equal(result.exitCode, 0);
  assert.deepEqual(result.starts, [0, 200]);
  assert.equal(result.spawned[0].options.env.AIDIY_DISCORD_CONNECT, '1');
  assert.equal(result.messages.length, 1); assert.match(result.messages[0], /パネルを開き/);
  assert.deepEqual(result.warnings, []); assert.deepEqual(result.opened, []);
});

test('Electron が使えない時は理由を表示してブラウザ版に切り替える（3本共通の規則）', async () => {
  const result = await 起動実行({ argv: ['--connect'], electron: false,
    ready: () => ({ windowShown: true, url: 'http://127.0.0.1:1/local/', publicUrl: 'https://example-1.app.github.dev/local/' }) });
  assert.equal(result.exitCode, 0);
  assert.equal(result.warnings.length, 1); assert.match(result.warnings[0], /_setup\.py/);
  assert.equal(result.spawned.length, 1);
  const [server] = result.spawned;
  assert.equal(server.executable, '/node');
  assert.match(server.args.at(-1)!, /src\/web-server\.ts$/);
  assert.equal(server.options.windowsHide, true, 'ブラウザ版のサーバーは画面を持たない');
  assert.equal(server.options.env.AIDIY_DISCORD_CONNECT, '1');
  assert.deepEqual(result.opened, ['https://example-1.app.github.dev/local/'], 'Codespaces では転送先の URL を開く');
});

test('既存ブラウザ版を検出したら、別の画面を開かず成功終了する', async () => {
  const result = await 起動実行({ argv: ['--browser'], electron: false, ready: () => ({ alreadyRunning: true }) });
  assert.equal(result.exitCode, 0);
  assert.equal(result.spawned.length, 1);
  assert.match(result.messages[0], /起動済み/);
  assert.deepEqual(result.opened, []);
  assert.deepEqual(result.warnings, []);
});
