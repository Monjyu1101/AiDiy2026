import { spawn, spawnSync } from 'node:child_process';
import { randomUUID } from 'node:crypto';
import { closeSync, existsSync, mkdirSync, openSync, readFileSync, statSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import { parseArgs } from 'node:util';
import { プロジェクト引数書式, プロジェクトフォルダ決定, ブラウザ自動判定, ブラウザ版表示, ブラウザ版へ切替 } from '../scripts/launch-project.mjs';

const extensionRoot = fileURLToPath(new URL('..', import.meta.url));
let options, projectRoot;
try {
  options = parseArgs({ allowPositionals: true, options: {
    provider: { type: 'string' }, model: { type: 'string' }, project: { type: 'string' }, browser: { type: 'boolean' }, wait: { type: 'boolean' }, offline: { type: 'boolean' }, help: { type: 'boolean' },
  } });
  if (!options.values.help) projectRoot = プロジェクトフォルダ決定(options.positionals, options.values.project);
  for (const name of ['provider', 'model']) {
    if (options.values[name] !== undefined && !options.values[name].trim()) throw new Error(`--${name} に値を指定してください。`);
  }
} catch (error) { console.error(error.message); process.exit(1); }
if (options.values.help) {
  console.log(`aidiy_code ${プロジェクト引数書式} [--provider Provider] [--model モデル名] [--offline] [--browser] [--wait]`);
  console.log('--offline: AIコアを使わず aidiy_hermes を直接実行（検証0回）。モデルはオンラインと別保存。');
  console.log('モデル未指定: 前回の手動選択（未保存なら既定設定）で起動。画面の「モデル」から変更できます。');
  console.log('Codespaces・画面のない Linux では --browser を省略してもブラウザ版で開きます。');
  process.exit(0);
}
// 明示しなくても、Codespaces・画面のない Linux ではブラウザ版にする（3本共通の規則は launch-project.mjs）。
const requestedBrowser = !!options.values.browser || ブラウザ自動判定();
const wait = !!options.values.wait;
const provider = options.values.provider?.trim();
const model = options.values.model?.trim();
const bundle = join(extensionRoot, 'dist', 'aidiy_code', 'server.cjs');
const runRoot = join(extensionRoot, 'out', 'aidiy_code');

function electronExecutable() {
  const setupMessage = `専用ウィンドウにはセットアップ済みの Electron が必要です。python "${join(extensionRoot, '_setup.py')}" を実行してください。`;
  try {
    // electron 本体を require すると、未配置時に起動中のダウンロードが始まる。
    // メタデータと実行ファイルだけを読み、取得は事前セットアップに任せる。
    const packagePath = createRequire(import.meta.url).resolve('electron/package.json');
    const electronRoot = dirname(packagePath);
    const packageVersion = JSON.parse(readFileSync(packagePath, 'utf8')).version;
    const expectedPath = process.platform === 'win32' ? 'electron.exe'
      : process.platform === 'darwin' ? 'Electron.app/Contents/MacOS/Electron' : 'electron';
    const pathFile = join(electronRoot, 'path.txt');
    const executablePath = existsSync(pathFile) ? readFileSync(pathFile, 'utf8') : expectedPath;
    const override = process.env.ELECTRON_OVERRIDE_DIST_PATH;
    if (!override) {
      if (!existsSync(pathFile) || executablePath !== expectedPath) throw new Error(setupMessage);
      const binaryVersion = readFileSync(join(electronRoot, 'dist', 'version'), 'utf8').trim().replace(/^v/, '');
      if (binaryVersion !== packageVersion) throw new Error(setupMessage);
    }
    const executable = join(override || join(electronRoot, 'dist'), executablePath);
    if (!statSync(executable).isFile()) throw new Error(setupMessage);
    return executable;
  } catch {
    throw new Error(setupMessage);
  }
}

async function main(browserMode) {
  const executable = browserMode ? process.execPath : electronExecutable();
  if (!existsSync(bundle)) {
    const npm = process.platform === 'win32' ? 'npm.cmd' : 'npm';
    const compiled = spawnSync(npm, ['run', 'compile'], { cwd: extensionRoot, stdio: 'inherit', shell: process.platform === 'win32' });
    if (compiled.status !== 0 || !existsSync(bundle)) throw new Error('コンパイルに失敗しました。frontend_vscode で npm ci を実行してください。');
  }
  mkdirSync(runRoot, { recursive: true });
  const runId = randomUUID().replaceAll('-', '');
  const readyPath = join(runRoot, `${runId}.json`);
  let server;
  let entry = bundle;
  if (!browserMode) {
    entry = join(extensionRoot, 'aidiy_code', 'desktop.cjs');
  }
  const env = { ...process.env };
  const initialModel = { provider, model, ...(options.values.offline ? { offline: true } : {}) };
  // VS Code のターミナルから起動しても Electron を通常のデスクトップモードで動かす。
  if (!browserMode) {
    delete env.ELECTRON_RUN_AS_NODE;
    // Chromium に作業フォルダや JSON を起動引数として解釈させない。
    env.AIDIY_CODE_PROJECT = projectRoot;
    env.AIDIY_CODE_READY = readyPath;
    env.AIDIY_CODE_MODEL = JSON.stringify(initialModel);
  }
  const stdout = openSync(join(runRoot, `${runId}.stdout.log`), 'w');
  const stderrPath = join(runRoot, `${runId}.stderr.log`);
  const stderr = openSync(stderrPath, 'w');
  try {
    const args = browserMode ? [entry, projectRoot, readyPath, JSON.stringify(initialModel)] : [entry];
    server = spawn(executable, args, {
      cwd: projectRoot, detached: !wait, stdio: wait ? 'inherit' : ['ignore', stdout, stderr], windowsHide: browserMode, env,
    });
  } finally {
    closeSync(stdout); closeSync(stderr);
  }
  let startupError;
  server.on('error', error => { startupError = error; });
  if (!wait) server.unref();
  else server.on('exit', (code, signal) => { process.exitCode = code ?? (signal ? 1 : 0); });
  function startupFailure(message) {
    let details = '';
    try { details = readFileSync(stderrPath, 'utf8').trim().slice(-3000); } catch { /* log unavailable */ }
    return new Error(`${message}\nログ: ${stderrPath}${details ? `\n${details}` : ''}`);
  }
  const deadline = Date.now() + 15000;
  while (!existsSync(readyPath)) {
    if (startupError) throw startupFailure(startupError.message);
    if (server.exitCode !== null) throw startupFailure(`起動に失敗しました (終了コード: ${server.exitCode})。`);
    if (Date.now() > deadline) {
      try { process.kill(server.pid); } catch { /* already exited */ }
      throw startupFailure('起動がタイムアウトしました。');
    }
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  const { url, publicUrl, windowShown } = JSON.parse(readFileSync(readyPath, 'utf8'));
  if (!browserMode && windowShown !== true) {
    try { process.kill(server.pid); } catch { /* already exited */ }
    throw startupFailure('専用ウィンドウの表示を確認できませんでした。');
  }
  // Codespaces ではポート転送先の URL を開く。$BROWSER があれば手元の PC のブラウザで開く。
  if (browserMode) await ブラウザ版表示(publicUrl || url, { profile: join(runRoot, 'browser-profile') });
  console.log(`AiDiy (Code) - Project folder: ${projectRoot}`);
}

main(requestedBrowser).catch(error => {
  if (requestedBrowser) throw error;
  // 専用ウィンドウを開けなければ、理由を表示してブラウザ版に切り替える。
  ブラウザ版へ切替(error);
  return main(true);
}).catch(error => { console.error(error.message || String(error)); process.exitCode = 1; });
