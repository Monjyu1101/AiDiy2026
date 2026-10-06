const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { test } = require('node:test');

function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'aidiy-launcher-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const scripts = path.join(root, 'aidiy_code');
  const electron = path.join(root, 'node_modules', 'electron');
  fs.mkdirSync(scripts);
  fs.mkdirSync(electron, { recursive: true });
  fs.copyFileSync(path.join(__dirname, '..', 'aidiy_code', 'launch.mjs'), path.join(scripts, 'launch.mjs'));
  fs.writeFileSync(path.join(electron, 'package.json'), JSON.stringify({ version: '44.5.1', main: 'index.js' }));
  fs.writeFileSync(path.join(electron, 'index.js'), 'throw new Error("UNEXPECTED_ELECTRON_DOWNLOAD");');
  const executable = process.platform === 'win32' ? 'electron.exe'
    : process.platform === 'darwin' ? 'Electron.app/Contents/MacOS/Electron' : 'electron';
  const binary = path.join(electron, 'dist', executable);
  const env = { ...process.env };
  delete env.ELECTRON_OVERRIDE_DIST_PATH;
  env.ELECTRON_RUN_AS_NODE = '1';
  const launch = (...args) => spawnSync(process.execPath, [path.join(scripts, 'launch.mjs'), root, ...args], {
    encoding: 'utf8', timeout: 20000, env,
  });
  function desktop(source) {
    fs.mkdirSync(path.dirname(binary), { recursive: true });
    try { fs.linkSync(process.execPath, binary); }
    catch { fs.copyFileSync(process.execPath, binary); }
    fs.writeFileSync(path.join(electron, 'path.txt'), executable);
    fs.writeFileSync(path.join(electron, 'dist', 'version'), '44.5.1');
    fs.mkdirSync(path.join(root, 'dist', 'aidiy_code'), { recursive: true });
    fs.writeFileSync(path.join(root, 'dist', 'aidiy_code', 'server.cjs'), '');
    fs.writeFileSync(path.join(root, 'aidiy_code', 'desktop.cjs'), source);
  }
  return { root, electron, executable, binary, launch, desktop };
}

test('Code 起動引数: 指定した Provider / モデルを専用ウィンドウへ渡す', t => {
  const f = fixture(t);
  f.desktop(`const assert = require('node:assert/strict');
    assert.equal(process.argv.length, 2);
    assert.equal(process.env.ELECTRON_RUN_AS_NODE, undefined);
    assert.equal(process.env.AIDIY_CODE_PROJECT, ${JSON.stringify(f.root)});
    assert.deepEqual(JSON.parse(process.env.AIDIY_CODE_MODEL), { provider: 'copilot-cli', model: 'claude-sonnet-5.5' });
    require('node:fs').writeFileSync(process.env.AIDIY_CODE_READY, JSON.stringify({ url: 'http://127.0.0.1:1234/', windowShown: true }));`);
  const result = f.launch('--provider=copilot_cli', '--model', 'claude-sonnet-5.5');
  assert.equal(result.status, 0, result.stderr);
});

test('Code 起動引数: 未指定モデルを自動へ置き換えず、保存済み設定の復元へ渡す', t => {
  const f = fixture(t);
  f.desktop(`const assert = require('node:assert/strict');
    const settings = JSON.parse(process.env.AIDIY_CODE_MODEL);
    assert.deepEqual(settings, settings.provider ? { provider: 'copilot-cli' } : {});
    require('node:fs').writeFileSync(process.env.AIDIY_CODE_READY, JSON.stringify({ url: 'http://127.0.0.1:1234/', windowShown: true }));`);
  for (const args of [[], ['--provider', 'copilot-cli']]) {
    const result = f.launch(...args);
    assert.equal(result.status, 0, result.stderr);
  }
});

test('Code 起動引数: 値不足と未知の引数を起動前に拒否する', t => {
  const f = fixture(t);
  for (const args of [['--model'], ['--provider', ''], ['--unknown']]) {
    const result = f.launch(...args);
    assert.equal(result.status, 1);
    assert.doesNotMatch(result.stderr, /_setup\.py/);
  }
});

test('missing Electron gives setup guidance without downloading', t => {
  const { launch } = fixture(t);
  const result = launch();
  assert.equal(result.status, 1);
  assert.match(result.stderr, /_setup\.py/);
  assert.doesNotMatch(result.stdout + result.stderr, /Downloading|UNEXPECTED_ELECTRON_DOWNLOAD/);
});

test('outdated Electron requires setup before compiling or launching', t => {
  const f = fixture(t);
  fs.mkdirSync(path.dirname(f.binary), { recursive: true });
  fs.writeFileSync(f.binary, 'old binary');
  fs.writeFileSync(path.join(f.electron, 'path.txt'), f.executable);
  fs.writeFileSync(path.join(f.electron, 'dist', 'version'), '44.5.0');
  const result = f.launch();
  assert.equal(result.status, 1);
  assert.match(result.stderr, /_setup\.py/);
  assert.doesNotMatch(result.stdout + result.stderr, /Downloading|UNEXPECTED_ELECTRON_DOWNLOAD/);
});

test('prepared Electron launches without loading its downloading entry point', t => {
  const f = fixture(t);
  f.desktop('require("node:fs").writeFileSync(process.env.AIDIY_CODE_READY, JSON.stringify({ url: "http://127.0.0.1:1234/", windowShown: true }));');
  const result = f.launch();
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /Project folder/);
  assert.doesNotMatch(result.stdout + result.stderr, /Downloading|UNEXPECTED_ELECTRON_DOWNLOAD/);
  assert.doesNotMatch(result.stdout, /ウィンドウを閉じる|サーバー.*停止/);
});

test('server readiness alone does not report a visible desktop window', t => {
  const f = fixture(t);
  f.desktop('require("node:fs").writeFileSync(process.env.AIDIY_CODE_READY, JSON.stringify({ url: "http://127.0.0.1:1234/" }));');
  const result = f.launch();
  assert.equal(result.status, 1);
  assert.match(result.stderr, /専用ウィンドウの表示を確認できません/);
  assert.doesNotMatch(result.stdout, /Project folder/);
});

test('startup failures show the child error and log location', t => {
  const f = fixture(t);
  f.desktop('console.error("画面の読み込みに失敗しました"); process.exitCode = 1;');
  const result = f.launch();
  assert.equal(result.status, 1);
  assert.match(result.stderr, /画面の読み込みに失敗しました/);
  assert.match(result.stderr, /stderr\.log/);
  assert.doesNotMatch(result.stdout, /Project folder/);
});
