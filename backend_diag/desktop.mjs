import {readFile,access} from 'node:fs/promises';
import {constants} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {spawn} from 'node:child_process';
export function browserMode(options, env=process.env, platform=process.platform) {
  return options.browser || options.noOpen || env.CODESPACES==='true' || env.CI==='true' || (platform==='linux' && !env.DISPLAY && !env.WAYLAND_DISPLAY);
}
export async function desktopBinary(root=fileURLToPath(new URL('.',import.meta.url)), platform=process.platform) {
  const suffix=platform==='win32'?'electron.exe':platform==='darwin'?'Electron.app/Contents/MacOS/Electron':'electron';
  const electron=path.join(root,'node_modules','electron');
  const metadata=JSON.parse(await readFile(path.join(electron,'package.json'),'utf8'));
  if ((await readFile(path.join(electron,'dist','version'),'utf8')).trim().replace(/^v/,'')!==metadata.version || (await readFile(path.join(electron,'path.txt'),'utf8'))!==suffix) throw new Error('Electron not ready');
  const executable=path.join(electron,'dist',suffix);await access(executable,platform==='win32'?constants.F_OK:constants.X_OK);return executable;
}
export function openDesktop(executable, url, onClose, spawnFn=spawn) {
  // URL/token は argv・環境変数・ログへ書かず、単発 stdin pipe で main process へ渡す。
  const env={...process.env};delete env.ELECTRON_RUN_AS_NODE;delete env.NODE_OPTIONS;delete env.NODE_PATH;
  const child=spawnFn(executable,[fileURLToPath(new URL('./electron-main.cjs',import.meta.url))],{shell:false,stdio:['pipe','ignore','ignore'],env,windowsHide:false,detached:process.platform!=='win32'});
  child.stdin.on('error',()=>{});child.stdin.end(JSON.stringify({url}));
  child.once('error',()=>{console.error('Electron を起動できません。セットアップを確認するか --browser を指定してください。');process.exitCode=1;onClose();});
  child.once('exit',(code,signal)=>{
    if (!child.diagClosing && (code !== 0 || signal)) {console.error('Electron が異常終了しました。実行環境を確認するか --browser を指定してください。');process.exitCode=1;}
    if (process.platform!=='win32' && child.pid) {try {process.kill(-child.pid,'SIGKILL');} catch {}}
    onClose();
  });return child;
}

export function closeDesktop(child, timeout=1000) {
  if (!child || child.diagClosing) return;
  child.diagClosing=true;
  const kill=signal=>{try {if(process.platform!=='win32' && child.pid)process.kill(-child.pid,signal);else child.kill(signal);}catch{}};
  kill('SIGTERM');
  const timer=setTimeout(()=>kill('SIGKILL'),timeout);timer.unref();
  child.once('exit',()=>clearTimeout(timer));
}
