import { spawn, spawnSync } from 'node:child_process';
import { randomUUID } from 'node:crypto';
import { closeSync, existsSync, mkdirSync, openSync, readFileSync, statSync } from 'node:fs';
import { delimiter, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const extensionRoot = fileURLToPath(new URL('..', import.meta.url));
const projectRoot = resolve(process.argv[2] || process.cwd());
const bundle = join(extensionRoot, 'dist', 'standalone.cjs');
const runRoot = join(extensionRoot, 'out', 'standalone');

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
  if (!existsSync(bundle)) {
    const npm = process.platform === 'win32' ? 'npm.cmd' : 'npm';
    const compiled = spawnSync(npm, ['run', 'compile'], { cwd: extensionRoot, stdio: 'inherit', shell: process.platform === 'win32' });
    if (compiled.status !== 0 || !existsSync(bundle)) throw new Error('コンパイルに失敗しました。frontend_vscode で npm ci を実行してください。');
  }
  mkdirSync(runRoot, { recursive: true });
  const runId = randomUUID().replaceAll('-', '');
  const readyPath = join(runRoot, `${runId}.json`);
  const stdout = openSync(join(runRoot, `${runId}.stdout.log`), 'w');
  const stderr = openSync(join(runRoot, `${runId}.stderr.log`), 'w');
  let server;
  try {
    server = spawn(process.execPath, [bundle, projectRoot, readyPath], {
      cwd: projectRoot, detached: true, stdio: ['ignore', stdout, stderr], windowsHide: true,
    });
  } finally {
    closeSync(stdout); closeSync(stderr);
  }
  let startupError;
  server.on('error', error => { startupError = error; });
  server.unref();
  const deadline = Date.now() + 15000;
  while (!existsSync(readyPath)) {
    if (startupError) throw startupError;
    if (server.exitCode !== null) throw new Error(`サーバー起動に失敗しました: ${join(runRoot, `${runId}.stderr.log`)}`);
    if (Date.now() > deadline) {
      try { process.kill(server.pid); } catch { /* already exited */ }
      throw new Error('サーバー起動がタイムアウトしました。');
    }
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  const { url } = JSON.parse(readFileSync(readyPath, 'utf8'));
  if (!openBrowser(url)) console.log(`ブラウザで開いてください: ${url}`);
  console.log(`AiDiy - Project folder: ${projectRoot}`);
  console.log('ウィンドウを閉じて60秒後にサーバーが停止します。');
}

main().catch(error => { console.error(error.message || String(error)); process.exitCode = 1; });
