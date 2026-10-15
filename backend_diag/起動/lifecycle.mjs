// cleanup がこの作業コピーだけに出す停止通知。PID や認証キーは保存しない。
import {readFile,stat} from 'node:fs/promises';
export const STOP_FILE = new URL('../.stop-request',import.meta.url);
export async function stopRevision(file=STOP_FILE) {
  try { if ((await stat(file)).size>128) return null; const text=(await readFile(file,'utf8')).trim(); return /^[a-f0-9]{32}$/.test(text)?text:null; } catch { return null; }
}
export function watchStop(initial,close,file=STOP_FILE,delay=250) {
  let checking=false;
  const timer=setInterval(async()=>{if(checking)return;checking=true;try {const current=await stopRevision(file);if(current && current!==initial){clearInterval(timer);close();}} finally {checking=false;}},delay);
  timer.unref();return ()=>clearInterval(timer);
}
