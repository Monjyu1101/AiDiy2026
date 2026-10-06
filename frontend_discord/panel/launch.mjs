import { spawn, spawnSync } from 'node:child_process';
import { closeSync, existsSync, mkdirSync, openSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { randomUUID } from 'node:crypto';
import { createRequire } from 'node:module';

const root = fileURLToPath(new URL('..', import.meta.url));
const args = process.argv.slice(2);
if (args.includes('--help')) {
  console.log('aidiy_discord [--check] [--connect]\nLive・コードの前回の選択でパネルを開きます。単独起動は未接続、--connect は自動接続です。');
  process.exit(0);
}
if (args.some(arg => !['--check', '--connect', '--wait'].includes(arg))) { console.error('使用方法: aidiy_discord [--check] [--connect]'); process.exit(1); }
// 通常起動・自動接続とも、Electron を探す／起動する前に共通の設定検証を通す。
// --check 以外は成功ログを省略し、入力したトークン自体はどの出力にも含めない。
const checkOnly = args.includes('--check');
const result = spawnSync(process.execPath, ['--import', pathToFileURL(join(root, 'node_modules/tsx/dist/loader.mjs')).href, join(root, 'src/main.ts'), '--check'], {
  cwd: root, stdio: ['ignore', checkOnly ? 'inherit' : 'ignore', 'inherit'], windowsHide: true, timeout: 30_000,
});
if (result.error) console.error('Discord の起動前チェックを実行できませんでした。セットアップを確認してください。');
if (result.status !== 0 || checkOnly) process.exit(result.status ?? 1);
try {
  const electronRoot = dirname(createRequire(import.meta.url).resolve('electron/package.json'));
  const expected = process.platform === 'win32' ? 'electron.exe' : process.platform === 'darwin' ? 'Electron.app/Contents/MacOS/Electron' : 'electron';
  const version = JSON.parse(readFileSync(join(electronRoot, 'package.json'), 'utf8')).version;
  if (readFileSync(join(electronRoot, 'path.txt'), 'utf8') !== expected || readFileSync(join(electronRoot, 'dist/version'), 'utf8').trim().replace(/^v/, '') !== version) throw new Error();
  const executable = join(electronRoot, 'dist', expected);
  if (!existsSync(executable)) throw new Error();
  const logs = join(root, 'out', 'aidiy_discord'); mkdirSync(logs, { recursive: true });
  const id = randomUUID(), ready = join(logs, `${id}.ready.json`);
  const stdout = openSync(join(logs, `${id}.stdout.log`), 'a'), stderr = openSync(join(logs, `${id}.stderr.log`), 'a');
  const env = { ...process.env, AIDIY_DISCORD_NODE: process.execPath, AIDIY_DISCORD_READY: ready, AIDIY_DISCORD_CONNECT: args.includes('--connect') ? '1' : '0' };
  delete env.ELECTRON_RUN_AS_NODE;
  // Windows の GUI アプリには SW_HIDE を渡さず、パネルの表示を許可する。
  const child = spawn(executable, [join(root, 'panel/desktop.cjs')], { cwd: root, env, detached: !args.includes('--wait'), stdio: ['ignore', stdout, stderr], windowsHide: false });
  closeSync(stdout); closeSync(stderr);
  let failed = false; child.on('error', () => { failed = true; });
  if (!args.includes('--wait')) child.unref();
  const limit = Date.now() + 15_000;
  while (Date.now() < limit && !failed) {
    if (existsSync(ready) && JSON.parse(readFileSync(ready, 'utf8')).windowShown) {
      console.log(args.includes('--connect') ? 'AiDiy (Discord) パネルを開き、自動接続を開始しました。' : 'AiDiy (Discord) パネルを開きました。「開始」で接続します。');
      if (args.includes('--wait') && child.exitCode === null) await new Promise(resolve => child.once('exit', resolve));
      process.exit(child.exitCode ?? 0);
    }
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  console.error(`パネルの表示を確認できませんでした。ログ: ${logs}`); process.exitCode = 1;
} catch {
  console.error(`Discord パネルの準備ができていません。python "${join(root, '_setup.py')}" を実行してください。`); process.exitCode = 1;
}
