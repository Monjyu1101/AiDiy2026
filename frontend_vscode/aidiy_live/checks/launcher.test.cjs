const { test } = require('node:test');
const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const { join, dirname } = require('node:path');
const { tmpdir } = require('node:os');

function fixture(t) {
  const root = fs.mkdtempSync(join(tmpdir(), 'aidiy-live-launch-'));
  const app = join(root, 'aidiy_live'), bundle = join(root, 'dist/aidiy_live');
  fs.mkdirSync(app); fs.mkdirSync(bundle, { recursive: true });
  const source = fs.readFileSync(join(__dirname, '../launch.mjs'), 'utf8');
  assert.ok(source.includes('spawn(command, browserArgs,'));
  // OS のブラウザ起動だけを代替し、親子の起動・常駐・通知処理は実コードで検証する。
  fs.writeFileSync(join(app, 'launch.mjs'), source.replace('spawn(command, browserArgs,', "spawn(process.execPath, ['-e', 'process.exit(0)'],"));
  fs.writeFileSync(join(bundle, 'view.js'), '');
  fs.writeFileSync(join(bundle, 'server.cjs'), `exports.ライブ起動 = async (root, backend, packaged, project, models) => {
    const server = require('node:http').createServer((req, res) => res.end(req.url === '/config' ? JSON.stringify({backend, project, models}) : 'mock live'));
    await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
    return {url: 'http://127.0.0.1:' + server.address().port + '/', idleMilliseconds: () => 0,
      close: () => new Promise(resolve => server.close(resolve))};
  };`);
  t.after(async () => {
    const out = join(root, 'out/aidiy_live');
    if (fs.existsSync(out)) for (const name of fs.readdirSync(out).filter(name => name.endsWith('.json'))) {
      const { pid } = JSON.parse(fs.readFileSync(join(out, name), 'utf8'));
      if (pid) try { process.kill(pid); } catch { /* 終了済み */ }
    }
    await new Promise(resolve => setTimeout(resolve, 150));
    await fs.promises.rm(root, { recursive: true, force: true, maxRetries: 10, retryDelay: 100 });
  });
  const env = { ...process.env };
  return { root, app, env, launch: (...args) => spawnSync(process.execPath, [join(app, 'launch.mjs'), ...args], {
    cwd: tmpdir(), env, encoding: 'utf8', timeout: 6000,
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
    assert.equal(process.argv[2], 'http://127.0.0.1:8091');
    assert.deepEqual(JSON.parse(process.argv[5]), { LIVE_AI_NAME: 'openai_live', LIVE_OPENAI_MODEL: 'gpt-realtime-2.1-mini' });
    require('node:fs').writeFileSync(process.argv[3], JSON.stringify({windowShown:true,pid:process.pid}));
    setInterval(() => {}, 10000);`);
  const result = f.launch('--provider', 'openai', '--model', 'gpt-realtime-2.1-mini');
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /aidiy_live を起動しました/);
  assert.doesNotMatch(result.stderr, /ブラウザ/);
});

test('Live ランチャー: Electron 失敗時もブラウザサーバーを分離して CMD へ戻れる', async t => {
  const f = fixture(t), result = f.launch('--provider', 'freeai', '--model', 'launch-model', '--project', tmpdir());
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stderr, /ブラウザの専用ウィンドウに切り替えます/);
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
