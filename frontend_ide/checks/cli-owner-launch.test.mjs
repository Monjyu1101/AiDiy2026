// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import * as path from 'node:path';
import * as url from 'node:url';
import { parseArgs } from 'node:util';
import { EventEmitter } from 'node:events';
import vm from 'node:vm';
import { transformSync } from 'esbuild';

// 実launch関数を使い、ブラウザ・Electron・HTTPサーバー・CLIは全てmockする。
function fixture(opened) {
  let closed = 0, armed = 0, disposed = 0, openCalls = 0, options;
  const messages = [], process = new EventEmitter();
  Object.assign(process, { argv: [], env: { AIDIY_LAUNCHER_CHILD: '1' }, cwd: () => '/fixture', pid: 123, send: value => messages.push(value) });
  const app = { url: 'http://127.0.0.1:9999/', publicUrl: 'http://127.0.0.1:9999/', close: async () => { closed++; } };
  const modules = {
    'node:child_process': { spawn() { throw Error('process spawning is forbidden in fixture'); } },
    'node:fs': { existsSync: () => true }, 'node:path': path, 'node:url': url, 'node:util': { parseArgs },
    './server.mjs': { startDevelopment: async (_project, value) => { options = value; return app; } },
    './aidiy_term/cli-launch.mjs': { validateCliOptions() {}, resolveCliLaunch: async () => ({}) },
    './aidiy_term/cli-session.mjs': { createCliOwnerLifetime: () => ({ arm: () => armed++, dispose: () => disposed++, started() {} }) },
    './viewer/launch-options.mjs': { projectFolder: () => '/fixture', useBrowser: () => true },
    './host/scripts/launch-project.mjs': { ブラウザで開く: async () => { openCalls++; return opened; } },
    './デスクトップ/desktop-process.mjs': { spawnDesktop() { throw Error('desktop forbidden in fixture'); } },
    './デスクトップ/project-profile.cjs': { projectIdentity: value => ({ path: value }) },
  };
  let source = readFileSync(new URL('../launch.mjs', import.meta.url), 'utf8');
  source = source.slice(0, source.indexOf('if(process.argv[1]'));
  const module = { exports: {} };
  vm.runInNewContext(transformSync(source, { format: 'cjs', define: { 'import.meta.url': JSON.stringify(new URL('../launch.mjs', import.meta.url).href) } }).code,
    { module, exports: module.exports, process, URL, console: { log() {}, warn() {} }, require: id => { if (!(id in modules)) throw Error(id); return modules[id]; } });
  return { launch: module.exports.launch, messages, process, stats: () => ({ closed, armed, disposed, openCalls, options }) };
}

test('CLIのブラウザ起動失敗: 所有サーバーを閉じ、launchReadyを返さない', async () => {
  const f = fixture(false);
  await assert.rejects(f.launch('term', ['--cli', 'copilot', '--cli-auto-approve', '--browser', '--foreground']), /ブラウザで開けません/);
  assert.equal(f.stats().closed, 1); assert.equal(f.stats().disposed, 1); assert.equal(f.stats().armed, 0); assert.equal(f.stats().openCalls, 1);
  assert.equal(f.messages.length, 0);
});

test('CLIのブラウザ起動成功: 初回開始期限を設け、放棄通知で所有サーバーを閉じる', async () => {
  const f = fixture(true);
  await f.launch('term', ['--cli', 'copilot', '--cli-auto-approve', '--browser', '--foreground']);
  assert.equal(f.stats().armed, 1); assert.equal(f.messages[0].launchReady, true); assert.equal(f.stats().closed, 0);
  await f.stats().options.onCliAbandoned(); assert.equal(f.stats().closed, 1); assert.equal(f.stats().disposed, 1);
});

test('通常Termのブラウザ起動失敗は既存のURL手動表示を維持する', async () => {
  const f = fixture(false);
  await f.launch('term', ['--browser', '--foreground']);
  assert.equal(f.messages[0].launchReady, true); assert.equal(f.stats().closed, 0); assert.equal(f.stats().armed, 0);
  f.process.emit('SIGTERM'); await Promise.resolve(); assert.equal(f.stats().closed, 1);
});
