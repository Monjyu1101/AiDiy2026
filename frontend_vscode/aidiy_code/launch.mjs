import { spawn, spawnSync } from 'node:child_process';
import { randomUUID } from 'node:crypto';
import { closeSync, existsSync, mkdirSync, openSync, readFileSync, statSync } from 'node:fs';
import { delimiter, dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const extensionRoot = fileURLToPath(new URL('..', import.meta.url));
const args = process.argv.slice(2);
if (args.includes('--help')) {
  console.log('aidiy_code [作業フォルダ] [--browser]');
  process.exit(0);
}
const browserMode = args.includes('--browser');
const projectRoot = resolve(args.find(arg => arg !== '--browser') || process.cwd());
const bundle = join(extensionRoot, 'dist', 'aidiy_code', 'server.cjs');
const runRoot = join(extensionRoot, 'out', 'aidiy_code');

function electronExecutable() {
  const setupMessage = `専用ウィンドウにはセットアップ済みの Electron が必要です。python "${join(extensionRoot, '_setup.py')}" を実行してください。ブラウザで開く場合は --browser を指定します。`;
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

function commandOnPath(name) {
  return (process.env.PATH || '').split(delimiter).filter(Boolean).map(folder => join(folder, name)).find(existsSync);
}

function launchDetached(command, args) {
  const child = spawn(command, args, { detached: true, stdio: 'ignore' });
  child.on('error', error => console.error(`ブラウザを開けません: ${error.message}`));
  child.unref();
}

function openBrowser(url) {
  if (process.platform === 'win32') {
    const candidates = [
      [process.env.PROGRAMFILES, 'Google/Chrome/Application/chrome.exe'],
      [process.env['PROGRAMFILES(X86)'], 'Google/Chrome/Application/chrome.exe'],
      [process.env.LOCALAPPDATA, 'Google/Chrome/Application/chrome.exe'],
      [process.env['PROGRAMFILES(X86)'], 'Microsoft/Edge/Application/msedge.exe'],
      [process.env.PROGRAMFILES, 'Microsoft/Edge/Application/msedge.exe'],
    ].filter(([base]) => Boolean(base)).map(([base, tail]) => join(base, tail));
    const browser = candidates.find(existsSync);
    if (browser) {
      launchDetached(browser, [`--app=${url}`, `--user-data-dir=${join(runRoot, 'browser-profile')}`, '--no-first-run', '--no-default-browser-check', '--window-size=640,820']);
    } else {
      launchDetached('explorer.exe', [url]);
    }
    return true;
  }
  const opener = process.platform === 'darwin' ? 'open' : 'xdg-open';
  if (!commandOnPath(opener)) return false;
  launchDetached(opener, [url]);
  return true;
}

async function main() {
  if (!existsSync(projectRoot) || !statSync(projectRoot).isDirectory()) throw new Error(`作業フォルダがありません: ${projectRoot}`);
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
  // VS Code のターミナルから起動しても Electron を通常のデスクトップモードで動かす。
  if (!browserMode) delete env.ELECTRON_RUN_AS_NODE;
  const stdout = openSync(join(runRoot, `${runId}.stdout.log`), 'w');
  const stderrPath = join(runRoot, `${runId}.stderr.log`);
  const stderr = openSync(stderrPath, 'w');
  try {
    server = spawn(executable, [entry, projectRoot, readyPath], {
      cwd: projectRoot, detached: true, stdio: ['ignore', stdout, stderr], windowsHide: browserMode, env,
    });
  } finally {
    closeSync(stdout); closeSync(stderr);
  }
  let startupError;
  server.on('error', error => { startupError = error; });
  server.unref();
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
  const { url, windowShown } = JSON.parse(readFileSync(readyPath, 'utf8'));
  if (!browserMode && windowShown !== true) {
    try { process.kill(server.pid); } catch { /* already exited */ }
    throw startupFailure('専用ウィンドウの表示を確認できませんでした。');
  }
  if (browserMode && !openBrowser(url)) console.log(`ブラウザで開いてください: ${url}`);
  console.log(`AiDiy (Code) - Project folder: ${projectRoot}`);
}

main().catch(error => { console.error(error.message || String(error)); process.exitCode = 1; });
