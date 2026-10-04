import { spawn } from 'node:child_process';
import { createRequire } from 'node:module';
import { existsSync, mkdirSync, readFileSync, writeFileSync, openSync, closeSync, statSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { randomUUID } from 'node:crypto';
const root = fileURLToPath(new URL('..', import.meta.url));
const projectRoot = resolve(process.env.AIDIY_LIVE_PROJECT || process.cwd());
const args = process.argv.slice(2);
let backend = 'http://127.0.0.1:8091', mode = 'desktop', foreground = false;
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--backend' && args[i + 1]) backend = args[++i];
  else if (args[i] === '--browser') mode = 'browser';
  else if (args[i] === '--serve') mode = 'serve';
  else if (args[i] === '--foreground') foreground = true;
  else if (args[i] === '--help') {
    console.log('aidiy_live [--browser | --serve] [--backend http://127.0.0.1:8091] [--foreground]'); process.exit(0);
  } else { console.error(`不明な引数: ${args[i]}`); process.exit(1); }
}
function electronExecutable() {
  const error = new Error('Electron が未配置です。python frontend_vscode/_setup.py を実行するか、--browser を指定してください。');
  try {
    const packagePath = createRequire(import.meta.url).resolve('electron/package.json');
    const folder = dirname(packagePath), metadata = JSON.parse(readFileSync(packagePath, 'utf8'));
    const expected = process.platform === 'win32' ? 'electron.exe' : process.platform === 'darwin' ? 'Electron.app/Contents/MacOS/Electron' : 'electron';
    if (readFileSync(join(folder, 'path.txt'), 'utf8').trim() !== expected) throw error;
    if (readFileSync(join(folder, 'dist/version'), 'utf8').trim().replace(/^v/, '') !== metadata.version) throw error;
    const executable = join(folder, 'dist', expected);
    if (!statSync(executable).isFile()) throw error;
    return executable;
  } catch { throw error; }
}
async function main() {
  if (!existsSync(join(root, 'dist/aidiy_live/server.cjs')) || !existsSync(join(root, 'dist/aidiy_live/view.js'))) await import('./build.mjs');
  async function startBrowser(open = true) {
    const { ライブ起動 } = createRequire(import.meta.url)('../dist/aidiy_live/server.cjs');
    const server = await ライブ起動(root, backend, false, projectRoot);
    console.log(`aidiy_live: ${server.url}\n接続先: ${backend}\n終了: Ctrl+C`);
    let idle;
    const close = () => { void server.close().then(() => process.exit(0)); };
    process.once('SIGINT', close); process.once('SIGTERM', close);
    if (open) {
      let command = process.platform === 'win32' ? 'explorer.exe' : process.platform === 'darwin' ? 'open' : 'xdg-open';
      let browserArgs = [server.url];
      if (process.platform === 'win32') {
        const candidates = [
          [process.env.PROGRAMFILES, 'Google/Chrome/Application/chrome.exe'],
          [process.env['PROGRAMFILES(X86)'], 'Google/Chrome/Application/chrome.exe'],
          [process.env.LOCALAPPDATA, 'Google/Chrome/Application/chrome.exe'],
          [process.env['PROGRAMFILES(X86)'], 'Microsoft/Edge/Application/msedge.exe'],
          [process.env.PROGRAMFILES, 'Microsoft/Edge/Application/msedge.exe'],
        ].filter(([base]) => base).map(([base, tail]) => join(base, tail));
        const executable = candidates.find(existsSync);
        if (executable) {
          command = executable;
          browserArgs = [`--app=${server.url}`, `--user-data-dir=${join(root, 'out/aidiy_live/browser-profile')}`, '--no-first-run', '--no-default-browser-check', '--window-size=420,650'];
        }
      }
      const browser = spawn(command, browserArgs, { stdio: 'ignore', windowsHide: false, detached: true });
      try { await new Promise((resolve, reject) => { browser.once('spawn', resolve); browser.once('error', reject); }); }
      catch (error) { await server.close(); throw new Error(`ブラウザを開けません: ${error.message}`); }
      browser.unref();
      idle = setInterval(() => { if (server.idleMilliseconds() >= 60000) { clearInterval(idle); close(); } }, 5000);
      if (process.env.AIDIY_LIVE_BROWSER_READY) writeFileSync(process.env.AIDIY_LIVE_BROWSER_READY, JSON.stringify({ url: server.url, pid: process.pid }));
    }
    return;
  }
  async function startBrowserDetached() {
    const runRoot = join(root, 'out/aidiy_live'); mkdirSync(runRoot, { recursive: true });
    const run = randomUUID(), ready = join(runRoot, `${run}.browser.json`), log = join(runRoot, `${run}.browser.log`);
    const descriptor = openSync(log, 'w');
    let child;
    try { child = spawn(process.execPath, [fileURLToPath(import.meta.url), '--browser', '--foreground', '--backend', backend], {
      cwd: root, detached: true, windowsHide: true, stdio: ['ignore', descriptor, descriptor],
      env: { ...process.env, AIDIY_LIVE_BROWSER_READY: ready, AIDIY_LIVE_PROJECT: projectRoot },
    }); } finally { closeSync(descriptor); }
    let failure; child.once('error', error => { failure = error; }); child.unref();
    const deadline = Date.now() + 15000;
    while (!existsSync(ready)) {
      if (failure || child.exitCode !== null || Date.now() >= deadline) {
        try { child.kill(); } catch { /* 終了済み */ }
        throw new Error(`ブラウザ版を起動できません: ${failure?.message || `終了コード ${child.exitCode}`}\nログ: ${log}\n${readFileSync(log, 'utf8').slice(-2000)}`);
      }
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    const info = JSON.parse(readFileSync(ready, 'utf8'));
    console.log(`ブラウザ版を起動しました: ${info.url}\n接続先: ${backend}\n画面を閉じるとサーバーも自動終了します。`);
  }
  if (mode !== 'desktop') return mode === 'browser' && !foreground ? startBrowserDetached() : startBrowser(mode === 'browser');
  async function startDesktop() {
    const executable = electronExecutable(), runRoot = join(root, 'out/aidiy_live'); mkdirSync(runRoot, { recursive: true });
    const run = randomUUID(), ready = join(runRoot, `${run}.json`), log = join(runRoot, `${run}.log`);
    const descriptor = openSync(log, 'w');
    const env = { ...process.env, ELECTRON_ENABLE_LOGGING: '1', AIDIY_LIVE_BACKEND: backend, AIDIY_LIVE_READY: ready, AIDIY_LIVE_PROJECT: projectRoot }; delete env.ELECTRON_RUN_AS_NODE;
    let child;
    // Chromium にアプリの設定ファイルを解釈させないよう、起動設定は環境変数で渡す。
    try { child = spawn(executable, [join(root, 'aidiy_live/desktop.cjs')], { cwd: root, detached: !foreground, stdio: foreground ? 'inherit' : ['ignore', descriptor, descriptor], windowsHide: false, env }); }
    finally { closeSync(descriptor); }
    let failure; child.on('error', error => { failure = error; }); if (!foreground) child.unref();
    const deadline = Date.now() + 15000;
    while (!existsSync(ready)) {
      if (failure || child.exitCode !== null || Date.now() > deadline) {
        try { child.kill(); } catch { /* 終了済み */ }
        throw new Error(`専用ウィンドウを起動できません (${failure?.message || `終了コード: ${child.exitCode}, signal: ${child.signalCode}`})。ログ: ${log}\n${readFileSync(log, 'utf8').slice(-2000)}`);
      }
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    if (JSON.parse(readFileSync(ready, 'utf8')).windowShown !== true) throw new Error(`表示を確認できません。ログ: ${log}`);
    console.log(`aidiy_live を起動しました。接続先: ${backend}`);
  }
  try { await startDesktop(); }
  catch (error) {
    console.warn(`${error.message}\nブラウザの専用ウィンドウに切り替えます。`);
    return foreground ? startBrowser() : startBrowserDetached();
  }
}
if (mode !== 'serve') console.log('AiDiy (Live) を起動しています…');
main().catch(error => { console.error(error.message || String(error)); process.exitCode = 1; });
