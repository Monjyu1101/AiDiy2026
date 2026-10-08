const { test } = require('node:test');
const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const { join, dirname } = require('node:path');
const { tmpdir } = require('node:os');
let fixtureNumber = 0;

function fixture(t) {
  const root = fs.mkdtempSync(join(tmpdir(), 'aidiy-live-launch-'));
  const app = join(root, 'aidiy_live'), bundle = join(root, 'dist/aidiy_live');
  fs.mkdirSync(app); fs.mkdirSync(bundle, { recursive: true });
  fs.copyFileSync(join(__dirname, '../local-backend.cjs'), join(app, 'local-backend.cjs'));
  fs.copyFileSync(join(__dirname, '../build-state.cjs'), join(app, 'build-state.cjs'));
  fs.mkdirSync(join(root, 'scripts'));
  for (const name of ['launch-project.mjs', 'window-size.cjs']) fs.copyFileSync(join(__dirname, '../../scripts', name), join(root, 'scripts', name));
  const port = 36000 + (process.pid % 20000) + fixtureNumber++;
  fs.writeFileSync(join(root, 'scripts/single-instance.cjs'),
    fs.readFileSync(join(__dirname, '../../scripts/single-instance.cjs'), 'utf8').replace('aidiy_live: 18094', `aidiy_live: ${port}`));
  fs.copyFileSync(join(__dirname, '../launch.mjs'), join(app, 'launch.mjs'));
  fs.writeFileSync(join(bundle, 'view.js'), '');
  fs.writeFileSync(join(bundle, 'server.cjs'), `exports.ライブ起動 = async (root, backend, packaged, project, models, modelFile, autoConnect) => {
    const server = require('node:http').createServer((req, res) => res.end(req.url === '/config' ? JSON.stringify({backend, project, models, autoConnect}) : 'mock live'));
    await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
    return {url: 'http://127.0.0.1:' + server.address().port + '/', idleMilliseconds: () => 0,
      close: () => new Promise(resolve => server.close(resolve))};
  };`);
  fs.mkdirSync(join(app, 'dist'));
  fs.writeFileSync(join(app, 'dist/extension.js'), '');
  fs.writeFileSync(join(app, 'dist/view.js'), '');
  fs.writeFileSync(join(app, 'build.mjs'), `
    import { readFileSync, writeFileSync, existsSync } from 'node:fs';
    import { fileURLToPath } from 'node:url';
    import state from './build-state.cjs';
    const root = fileURLToPath(new URL('..', import.meta.url));
    const count = new URL('../build-count', import.meta.url);
    writeFileSync(count, String((existsSync(count) ? Number(readFileSync(count, 'utf8')) : 0) + 1));
    state.ビルド状態保存(root);
  `);
  require('../build-state.cjs').ビルド状態保存(root);
  const stop = async () => {
    const out = join(root, 'out/aidiy_live');
    if (fs.existsSync(out)) for (const name of fs.readdirSync(out).filter(name => name.endsWith('.json'))) {
      const { pid } = JSON.parse(fs.readFileSync(join(out, name), 'utf8'));
      if (pid) try { process.kill(pid); } catch { /* 終了済み */ }
    }
    await new Promise(resolve => setTimeout(resolve, 150));
  };
  t.after(async () => {
    await stop();
    await fs.promises.rm(root, { recursive: true, force: true, maxRetries: 10, retryDelay: 100 });
  });
  // OS のブラウザ起動だけを $BROWSER（共通の起動処理が最優先で使う）で代替し、
  // 親子の起動・常駐・通知処理は実コードで検証する。node に URL を渡すだけなので何も開かない。
  const env = { ...process.env, BROWSER: process.execPath };
  delete env.CODESPACES;
  env.DISPLAY ||= ':0'; // 画面のない Linux もブラウザ判定になるため、仮の表示先を与える。
  return { root, app, env, stop, launch: (...args) => spawnSync(process.execPath, [join(app, 'launch.mjs'), ...args], {
    cwd: tmpdir(), env, encoding: 'utf8', timeout: 20000,
  }) };
}

test('Live ランチャー: Electron が常駐しても表示確認後に CMD へ戻れる', t => {
  const f = fixture(t), electron = join(f.root, 'node_modules/electron');
  fs.mkdirSync(join(electron, 'dist'), { recursive: true });
  const executable = process.platform === 'win32' ? 'electron.exe' : process.platform === 'darwin' ? 'Electron.app/Contents/MacOS/Electron' : 'electron';
  const binary = join(electron, 'dist', executable); fs.mkdirSync(dirname(binary), { recursive: true });
  try { fs.linkSync(process.execPath, binary); } catch { fs.copyFileSync(process.execPath, binary); }
  fs.writeFileSync(join(electron, 'package.json'), JSON.stringify({ version: '44.5.1', main: 'index.js' }));
  fs.writeFileSync(join(electron, 'index.js'), 'throw new Error("Electron download must not run");');
  fs.writeFileSync(join(electron, 'path.txt'), executable);
  fs.writeFileSync(join(electron, 'dist/version'), '44.5.1');
  fs.writeFileSync(join(f.app, 'desktop.cjs'), `const assert = require('node:assert/strict');
    assert.equal(process.argv.length, 2);
    assert.equal(process.env.ELECTRON_RUN_AS_NODE, undefined);
    assert.equal(process.env.AIDIY_LIVE_BACKEND, 'http://127.0.0.1:8091');
    assert.equal(process.env.AIDIY_LIVE_PROJECT, ${JSON.stringify(tmpdir())});
    assert.equal(process.env.AIDIY_LIVE_CONNECT, '1');
    assert.deepEqual(JSON.parse(process.env.AIDIY_LIVE_MODELS), { LIVE_AI_NAME: 'openai_live', LIVE_OPENAI_MODEL: 'gpt-realtime-2.1-mini' });
    require('node:fs').writeFileSync(process.env.AIDIY_LIVE_READY, JSON.stringify({windowShown:true,pid:process.pid}));
    setInterval(() => {}, 10000);`);
  f.env.ELECTRON_RUN_AS_NODE = '1';
  const result = f.launch('--provider', 'openai', '--model', 'gpt-realtime-2.1-mini', '--connect');
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /aidiy_live を起動しました/);
  assert.doesNotMatch(result.stderr, /ブラウザ/);
});

test('Live 全体起動: --connect をモデルなしでブラウザ・Electron失敗時へ引き継ぐ', async t => {
  const f = fixture(t);
  for (const args of [['--browser', '--connect'], ['--connect']]) {
    const result = f.launch(...args);
    assert.equal(result.status, 0, result.stderr);
    const url = result.stdout.match(/ブラウザ版を起動しました: (http[^\r\n]+)/)[1];
    const config = await (await fetch(new URL('config', url))).json();
    assert.equal(config.autoConnect, true);
    assert.deepEqual(config.models, {});
    await f.stop();
  }
});

test('Live ランチャー: Electron 失敗時もブラウザサーバーを分離して CMD へ戻れる', async t => {
  const f = fixture(t), result = f.launch('--provider', 'freeai', '--model', 'launch-model', '--project', tmpdir());
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stderr, /ブラウザ版に切り替えます/);
  assert.match(result.stdout, /ブラウザ版を起動しました/);
  const out = join(f.root, 'out/aidiy_live');
  const ready = fs.readdirSync(out).find(name => name.endsWith('.browser.json'));
  const { url } = JSON.parse(fs.readFileSync(join(out, ready), 'utf8'));
  assert.equal(await (await fetch(url)).text(), 'mock live');
  const config = await (await fetch(new URL('config', url))).json();
  assert.equal(config.project, tmpdir());
  assert.deepEqual(config.models, { LIVE_AI_NAME: 'freeai_live', LIVE_FREEAI_MODEL: 'launch-model' });
});

test('Live 起動引数: 未指定時は既定設定、Provider だけの指定も反映する', async t => {
  const f = fixture(t);
  for (const [args, expected] of [[[], {}], [['--provider=gemini'], { LIVE_AI_NAME: 'gemini_live' }]]) {
    const result = f.launch('--browser', ...args);
    assert.equal(result.status, 0, result.stderr);
    const url = result.stdout.match(/ブラウザ版を起動しました: (http[^\r\n]+)/)[1];
    const config = await (await fetch(new URL('config', url))).json();
    assert.deepEqual(config.models, expected);
    await f.stop();
  }
});

test('Live 起動引数: 値不足・未知の引数・不正な Provider を起動前に拒否する', t => {
  const f = fixture(t);
  for (const args of [['--model'], ['--model', 'test-model'], ['--provider', ''], ['--provider', 'invalid'], ['--unknown']]) {
    const result = f.launch(...args);
    assert.equal(result.status, 1);
    assert.doesNotMatch(result.stdout, /起動しました/);
  }
});

test('Live 二重起動: ブラウザを増やさず、既存の接続・モデルを保持する', async t => {
  const f = fixture(t);
  const first = f.launch('--browser', '--provider', 'freeai', '--model', 'first-model');
  assert.equal(first.status, 0, first.stderr);
  const url = first.stdout.match(/ブラウザ版を起動しました: (http[^\r\n]+)/)[1];
  const second = f.launch('--browser', '--provider', 'gemini', '--model', 'second-model');
  assert.equal(second.status, 0, second.stderr);
  assert.match(second.stdout, /起動済み/);
  assert.doesNotMatch(second.stdout, /ブラウザ版を起動しました/);
  assert.deepEqual((await (await fetch(new URL('config', url))).json()).models,
    { LIVE_AI_NAME: 'freeai_live', LIVE_FREEAI_MODEL: 'first-model' });
  const ready = fs.readdirSync(join(f.root, 'out/aidiy_live')).filter(name => name.endsWith('.browser.json'))
    .map(name => JSON.parse(fs.readFileSync(join(f.root, 'out/aidiy_live', name), 'utf8')));
  assert.equal(ready.filter(state => state.pid).length, 1);
  assert.equal(ready.filter(state => state.alreadyRunning).length, 1);
});

test('Live 接続先: 共通PORT_COREを自動参照し、接続先の指定を要求しない', async t => {
  const f = fixture(t);
  fs.mkdirSync(join(f.root, '_config'));
  fs.writeFileSync(join(f.root, '_config/AiDiy_key.json'), JSON.stringify({ PORT_CORE: '9091' }));
  const result = f.launch('--browser');
  assert.equal(result.status, 0, result.stderr);
  assert.doesNotMatch(result.stdout, /接続先:/);
  const url = result.stdout.match(/ブラウザ版を起動しました: (http[^\r\n]+)/)[1];
  assert.equal((await (await fetch(new URL('config', url))).json()).backend, 'http://127.0.0.1:9091');
  assert.doesNotMatch(f.launch('--help').stdout, /--backend/);
  assert.equal(f.launch('--backend', 'https://example.test').status, 1);
});

test('Live 更新: 旧生成物が残っていても画面変更を検知し、更新後だけ起動する', async t => {
  const f = fixture(t);
  fs.mkdirSync(join(f.app, 'media'));
  fs.writeFileSync(join(f.app, 'media/index.html'), '<html>接続先欄のない新画面</html>');
  const first = f.launch('--browser');
  assert.equal(first.status, 0, first.stderr);
  assert.match(first.stdout, /画面・接続処理を更新/);
  assert.equal(fs.readFileSync(join(f.root, 'build-count'), 'utf8'), '1');
  const next = f.launch('--browser');
  assert.equal(next.status, 0, next.stderr);
  assert.doesNotMatch(next.stdout, /画面・接続処理を更新/);
  assert.equal(fs.readFileSync(join(f.root, 'build-count'), 'utf8'), '1');
  await f.stop();
  // 記録のない従来の配置からの初回起動も更新する。
  fs.unlinkSync(join(f.root, 'dist/aidiy_live/build-state.json'));
  assert.equal(f.launch('--browser').status, 0);
  assert.equal(fs.readFileSync(join(f.root, 'build-count'), 'utf8'), '2');
});
