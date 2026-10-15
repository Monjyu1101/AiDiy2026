// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1". See LICENSE.
import http from 'node:http';
import { randomBytes, timingSafeEqual } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import { catalog, scan, cancelProbes } from './probes.mjs';
import {stopRevision,watchStop} from './lifecycle.mjs';

export function basePath(value) {
  if (value === '/') return '/';
  if (!/^\/[A-Za-z0-9_/-]+\/?$/.test(value) || value.includes('//')) throw new Error('base-path は /proxy/8097/ のように指定してください。');
  return value.replace(/\/+$/, '') + '/';
}
export function publicUrl(port, prefix, env = process.env) {
  const name = env.CODESPACE_NAME || '', domain = env.GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN || '';
  if (env.CODESPACES === 'true' && /^[a-zA-Z0-9-]+$/.test(name) && /^[a-zA-Z0-9.-]+$/.test(domain)) return `https://${name}-${port}.${domain}${prefix}`;
  return `http://127.0.0.1:${port}${prefix}`;
}
export function parseArgs(args) {
  const options = {port:0, prefix:'/', noOpen:false, help:false};
  for (let i=0;i<args.length;i++) {
    const arg = args[i];
    if (arg === '--browser') continue;
    if (arg === '--no-open') options.noOpen = true;
    else if (arg === '--help' || arg === '-h') options.help = true;
    else if (arg === '--port') { const value = args[++i]; if (!/^\d+$/.test(value || '') || Number(value)>65535) throw new Error('port は 0〜65535 で指定してください。'); options.port=Number(value); }
    else if (arg === '--base-path') options.prefix = basePath(args[++i] || '');
    else throw new Error(`不明な引数: ${arg}`);
  }
  return options;
}
export function createHandler({token, prefix='/', entries=[], coverage={}, scanFn=scan}) {
  let results = [], busy = false;
  const assets = new Map([['',['index.html','text/html; charset=utf-8']],['app.js',['app.js','text/javascript; charset=utf-8']],['style.css',['style.css','text/css; charset=utf-8']]]);
  return async (req,res) => {
    const reply = (status, body, type='application/json; charset=utf-8') => {
      if (res.destroyed) return;
      const content = Buffer.isBuffer(body) ? body : Buffer.from(JSON.stringify(body));
      res.writeHead(status, {'Content-Type':type,'Content-Length':content.length,'Cache-Control':'no-store',
        'X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer',
        'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"});
      res.end(content);
    };
    let route;
    try { const url = new URL(req.url,'http://localhost'); const pathname = decodeURIComponent(url.pathname); route = pathname.startsWith(prefix) ? pathname.slice(prefix.length) : null; if (url.search) return reply(400,{エラー:'クエリ引数は指定できません。'}); }
    catch { return reply(400,{エラー:'URL が不正です。'}); }
    const auth = Buffer.from(req.headers.authorization || ''), expected = Buffer.from('Bearer ' + token);
    const authorized = auth.length === expected.length && timingSafeEqual(auth,expected);
    try {
      if (route?.startsWith('api/') && !authorized) return reply(401,{エラー:'起動時の認証キーを入力してください。'});
      if (req.method === 'GET' && route === 'api/一覧') return reply(200,{項目:entries,結果:results,調査:coverage});
      if (req.method === 'POST' && route === 'api/診断') {
        if (req.headers['transfer-encoding'] || (req.headers['content-length'] && req.headers['content-length'] !== '0')) return reply(400,{エラー:'診断への引数は指定できません。'});
        if (busy) return reply(409,{エラー:'診断実行中です。完了後に再試行してください。'});
        busy=true;
        try { results=await scanFn(entries); reply(200,{結果:results}); } finally { busy=false; }
        return;
      }
      if (req.method === 'GET' && assets.has(route)) {
        const [file,type] = assets.get(route); return reply(200,await readFile(new URL('./static/'+file,import.meta.url)),type);
      }
      reply(404,{エラー:'見つかりません。'});
    } catch { reply(500,{エラー:'診断処理でエラーが発生しました。'}); }
  };
}
export function createServer(options) {
  const server=http.createServer({maxHeaderSize:8192,requestTimeout:10000,headersTimeout:10000,connectionsCheckingInterval:1000},createHandler(options));
  server.maxConnections=16; server.maxRequestsPerSocket=20; server.keepAliveTimeout=2000;
  // 診断は最大 4 並列 × 登録数分。slow connection は下の期限で切断する。
  server.setTimeout(Math.max(10000,Math.ceil((options.entries?.length || 0)/4)*5000+5000),socket=>socket.destroy());
  server.on('clientError',(_err,socket)=>socket.destroy());
  return server;
}
function openBrowser(url) {
  // 固定 OS opener + 単一 URL 引数。Windows shell を必要とする start は使わない。
  let command,args;
  if (process.platform === 'darwin') { command='open';args=[url]; }
  else if (process.platform === 'win32') { command='rundll32.exe';args=['url.dll,FileProtocolHandler',url]; }
  else { command='xdg-open';args=[url]; }
  const child=spawn(command,args,{stdio:'ignore',shell:false,windowsHide:true});
  child.on('error',()=>console.log('自動で開けない場合は、上の URL をブラウザで開いてください。')); child.unref();
}
export async function main(args=process.argv.slice(2)) {
  const options=parseArgs(args);
  if (options.help) { console.log('AiDiy 診断: aidiy_diag [--browser] [--no-open] [--port 8097] [--base-path /proxy/8097/]'); return; }
  const initialStop=await stopRevision();
  const token=randomBytes(32).toString('base64url'), entries=await catalog();
  const coverage=JSON.parse(await readFile(new URL('./coverage.json',import.meta.url),'utf8'));
  const server=createServer({token,prefix:options.prefix,entries,coverage});
  await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(options.port,'127.0.0.1',resolve);});
  const url=publicUrl(server.address().port,options.prefix)+'#token='+token;
  console.log('AiDiy 診断: '+url);
  console.log('この起動中のみ有効な認証 URL です。共有せず、転送ポートは非公開にしてください。Ctrl+C で終了。');
  if (!options.noOpen && process.env.CODESPACES !== 'true') openBrowser(url);
  let stopWatching=()=>{};
  const close=()=>{stopWatching();cancelProbes();server.close();server.closeAllConnections();};
  stopWatching=watchStop(initialStop,close);
  server.once('close',()=>stopWatching());
  process.once('SIGINT',close);process.once('SIGTERM',close);
  return server;
}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) main().catch(()=>{console.error('診断を起動できません。引数、ポートの使用状況、catalog.json を確認してください。');process.exitCode=1;});
