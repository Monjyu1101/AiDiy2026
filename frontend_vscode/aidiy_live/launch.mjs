import { spawn } from 'node:child_process';
import { createRequire } from 'node:module';
import { existsSync, mkdirSync, readFileSync, writeFileSync, openSync, closeSync, statSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { randomUUID } from 'node:crypto';
import { parseArgs } from 'node:util';
import localBackend from './local-backend.cjs';
import buildState from './build-state.cjs';
const root = fileURLToPath(new URL('..', import.meta.url));
let options;
try {
  options = parseArgs({ options: {
    provider: { type: 'string' }, model: { type: 'string' },
    project: { type: 'string' }, 'ready-file': { type: 'string' },
    browser: { type: 'boolean' }, serve: { type: 'boolean' }, foreground: { type: 'boolean' }, connect: { type: 'boolean' }, help: { type: 'boolean' },
  } }).values;
  for (const name of ['provider', 'model', 'project', 'ready-file']) {
    if (options[name] !== undefined && !options[name].trim()) throw new Error(`--${name} に値を指定してください。`);
  }
  if (options.model && !options.provider) throw new Error('Live の --model には --provider も指定してください。');
} catch (error) { console.error(error.message); process.exit(1); }
if (options.help) {
  console.log('aidiy_live [--provider freeai|gemini|openai] [--model モデル名] [--project 作業フォルダ] [--browser | --serve] [--foreground] [--connect]');
  console.log('モデル未指定: 前回の手動選択（未保存ならバックエンドの既定設定）で起動。画面の「モデル」から変更できます。'); process.exit(0);
}
const providerAliases = { freeai: 'freeai_live', gemini: 'gemini_live', openai: 'openai_live', freeai_live: 'freeai_live', gemini_live: 'gemini_live', openai_live: 'openai_live' };
const requestedProvider = options.provider?.trim();
if (requestedProvider && !Object.hasOwn(providerAliases, requestedProvider)) {
  console.error('Live の Provider は freeai / gemini / openai を指定してください。'); process.exit(1);
}
const provider = providerAliases[requestedProvider], model = options.model?.trim();
const projectRoot = resolve(options.project || process.cwd());
const backend = localBackend.ローカル接続先(root, projectRoot);
const mode = options.serve ? 'serve' : options.browser ? 'browser' : 'desktop';
const foreground = !!options.foreground;
const autoConnect = !!options.connect;
const modelArgs = [...(provider ? ['--provider', provider] : []), ...(model ? ['--model', model] : [])];
const modelKeys = { freeai_live: 'LIVE_FREEAI_MODEL', gemini_live: 'LIVE_GEMINI_MODEL', openai_live: 'LIVE_OPENAI_MODEL' };
const modelSettings = provider ? { LIVE_AI_NAME: provider, ...(model ? { [modelKeys[provider]]: model } : {}) } : {};
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
  if (buildState.ビルド更新が必要(root)) {
    console.log('Live の画面・接続処理を更新しています…');
    await import('./build.mjs');
  }
  async function startBrowser(open = true) {
    const { ライブ起動 } = createRequire(import.meta.url)('../dist/aidiy_live/server.cjs');
    const server = await ライブ起動(root, backend, false, projectRoot, modelSettings, undefined, autoConnect);
    console.log(`aidiy_live: ${server.url}\n終了: Ctrl+C`);
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
          browserArgs = [`--app=${server.url}`, `--user-data-dir=${join(root, 'out/aidiy_live/browser-profile')}`, '--no-first-run', '--no-default-browser-check', '--window-size=640,820'];
        }
      }
      const browser = spawn(command, browserArgs, { stdio: 'ignore', windowsHide: false, detached: true });
      try { await new Promise((resolve, reject) => { browser.once('spawn', resolve); browser.once('error', reject); }); }
      catch (error) { await server.close(); throw new Error(`ブラウザを開けません: ${error.message}`); }
      browser.unref();
      idle = setInterval(() => { if (server.idleMilliseconds() >= 60000) { clearInterval(idle); close(); } }, 5000);
      if (options['ready-file']) writeFileSync(options['ready-file'], JSON.stringify({ url: server.url, pid: process.pid }));
    }
    return;
  }
  async function startBrowserDetached() {
    const runRoot = join(root, 'out/aidiy_live'); mkdirSync(runRoot, { recursive: true });
    const run = randomUUID(), ready = join(runRoot, `${run}.browser.json`), log = join(runRoot, `${run}.browser.log`);
    const descriptor = openSync(log, 'w');
    let child;
    try { child = spawn(process.execPath, [fileURLToPath(import.meta.url), '--browser', '--foreground', '--project', projectRoot, '--ready-file', ready, ...modelArgs, ...(autoConnect ? ['--connect'] : [])], {
      cwd: root, detached: true, windowsHide: true, stdio: ['ignore', descriptor, descriptor],
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
    console.log(`ブラウザ版を起動しました: ${info.url}\n画面を閉じるとサーバーも自動終了します。`);
  }
  if (mode !== 'desktop') return mode === 'browser' && !foreground ? startBrowserDetached() : startBrowser(mode === 'browser');
  async function startDesktop() {
    const executable = electronExecutable(), runRoot = join(root, 'out/aidiy_live'); mkdirSync(runRoot, { recursive: true });
    const run = randomUUID(), ready = join(runRoot, `${run}.json`), log = join(runRoot, `${run}.log`);
    const descriptor = openSync(log, 'w');
    const env = { ...process.env }; delete env.ELECTRON_RUN_AS_NODE;
    // Chromium に接続先・ファイルパス・JSON を起動引数として解釈させない。
    env.AIDIY_LIVE_BACKEND = backend;
    env.AIDIY_LIVE_READY = ready;
    env.AIDIY_LIVE_PROJECT = projectRoot;
    env.AIDIY_LIVE_MODELS = JSON.stringify(modelSettings);
    env.AIDIY_LIVE_CONNECT = autoConnect ? '1' : '0';
    let child;
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
    console.log(`aidiy_live を起動しました。`);
  }
  try { await startDesktop(); }
  catch (error) {
    console.warn(`${error.message}\nブラウザの専用ウィンドウに切り替えます。`);
    return foreground ? startBrowser() : startBrowserDetached();
  }
}
if (mode !== 'serve') console.log('AiDiy (Live) を起動しています…');
main().catch(error => { console.error(error.message || String(error)); process.exitCode = 1; });
