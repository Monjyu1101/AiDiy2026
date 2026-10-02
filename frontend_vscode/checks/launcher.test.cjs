const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { test } = require('node:test');

function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'aidiy-launcher-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const scripts = path.join(root, 'scripts');
  const electron = path.join(root, 'node_modules', 'electron');
  fs.mkdirSync(scripts);
  fs.mkdirSync(electron, { recursive: true });
  fs.copyFileSync(path.join(__dirname, '..', 'scripts', 'launch-standalone.mjs'), path.join(scripts, 'launch-standalone.mjs'));
  fs.writeFileSync(path.join(electron, 'package.json'), JSON.stringify({ version: '44.5.1', main: 'index.js' }));
  fs.writeFileSync(path.join(electron, 'index.js'), 'throw new Error("UNEXPECTED_ELECTRON_DOWNLOAD");');
  const executable = process.platform === 'win32' ? 'electron.exe'
    : process.platform === 'darwin' ? 'Electron.app/Contents/MacOS/Electron' : 'electron';
  const binary = path.join(electron, 'dist', executable);
  const env = { ...process.env };
  delete env.ELECTRON_OVERRIDE_DIST_PATH;
  const launch = () => spawnSync(process.execPath, [path.join(scripts, 'launch-standalone.mjs'), root], {
    encoding: 'utf8', timeout: 20000, env,
  });
  return { root, electron, executable, binary, launch };
}

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
  fs.mkdirSync(path.dirname(f.binary), { recursive: true });
  try { fs.linkSync(process.execPath, f.binary); }
  catch { fs.copyFileSync(process.execPath, f.binary); }
  fs.writeFileSync(path.join(f.electron, 'path.txt'), f.executable);
  fs.writeFileSync(path.join(f.electron, 'dist', 'version'), '44.5.1');
  fs.mkdirSync(path.join(f.root, 'dist'));
  fs.writeFileSync(path.join(f.root, 'dist', 'standalone.cjs'), '');
  fs.mkdirSync(path.join(f.root, 'standalone'));
  fs.writeFileSync(path.join(f.root, 'standalone', 'desktop.cjs'),
    'require("node:fs").writeFileSync(process.argv[3], JSON.stringify({ url: "http://127.0.0.1:1234/" }));');
  const result = f.launch();
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /Project folder/);
  assert.doesNotMatch(result.stdout + result.stderr, /Downloading|UNEXPECTED_ELECTRON_DOWNLOAD/);
});
