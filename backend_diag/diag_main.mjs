// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1". See LICENSE.
import http from 'node:http';
import { randomBytes, timingSafeEqual } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import { catalog, scan, cancelProbes } from './probes.mjs';
import {browserMode,desktopBinary,openDesktop,closeDesktop} from './desktop.mjs';
import {createPublicModelCache} from './public_models.mjs';
import {getKeyStatus,testKey,KEY_PROVIDERS,cancelKeyProbes} from './key_status.mjs';
import {verify as verifyUi} from './ui/verify.mjs';
import {stopRevision,watchStop} from './lifecycle.mjs';

// 外部例外の本文・パス・引数はログへ出さず、固定の原因分類だけを表示する。
const STARTUP_MESSAGES=Object.freeze({
  ARGUMENTS:'起動引数が不正です。aidiy_diag --help で指定方法を確認してください。',
  UI:'Vue UI のソースと配布物が一致しないか不足しています。同じ版の backend_diag を取得し直してください。UI を編集した場合は backend_diag/ui で npm ci && npm run build を実行してください。',
  ELECTRON:'Electron が未準備です。python backend_diag/_setup.py を実行するか --browser を指定してください。',
  DESKTOP:'Electron を起動できません。--browser でブラウザ起動できます。',
  CATALOG:'catalog.json または coverage.json を読み込めません。同じ版の backend_diag を取得し直してください。',
  EADDRINUSE:'指定ポートは使用中です。--port 0 で空きポートを使用してください。',
  EACCES:'ローカル待受の権限がありません。--port 0 または OS のアクセス設定を確認してください。'
});
function startupError(code){return Object.assign(new Error('Diagnostic startup failed'),{diagCode:code});}
export function startupMessage(error){return '診断を起動できません。'+((Object.hasOwn(STARTUP_MESSAGES,error?.diagCode) && STARTUP_MESSAGES[error.diagCode]) || (Object.hasOwn(STARTUP_MESSAGES,error?.code) && STARTUP_MESSAGES[error.code]) || '起動処理でエラーが発生しました。診断ファイルの配置とアクセス権を確認してください。');}

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
  const options = {port:0, prefix:'/', noOpen:false, browser:false, help:false};
  for (let i=0;i<args.length;i++) {
    const arg = args[i];
    if (arg === '--browser') {options.browser = true;continue;}
    if (arg === '--no-open') options.noOpen = true;
    else if (arg === '--help' || arg === '-h') options.help = true;
    else if (arg === '--port') { const value = args[++i]; if (!/^\d+$/.test(value || '') || Number(value)>65535) throw new Error('port は 0〜65535 で指定してください。'); options.port=Number(value); }
    else if (arg === '--base-path') options.prefix = basePath(args[++i] || '');
    else throw new Error(`不明な引数: ${arg}`);
  }
  return options;
}
export function createHandler({token, prefix='/', entries=[], coverage={}, scanFn=scan, keyStatusFn=getKeyStatus, keyTestFn=testKey, publicCache=createPublicModelCache()}) {
  let results = [], busy = false, keyBusy = false;

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
      if (req.method === 'GET' && route === 'api/キー設定') return reply(200,{...await keyStatusFn(),公開モデル:publicCache.snapshot()});
      if (req.method === 'GET' && route === 'api/公開モデル') return reply(200,publicCache.snapshot());
      if (req.method === 'POST' && route === 'api/公開モデル/再取得') {
        if (req.headers['transfer-encoding'] || (req.headers['content-length'] && req.headers['content-length'] !== '0')) return reply(400,{エラー:'公開モデル取得への引数は指定できません。'});
        return reply(200,await publicCache.refresh());
      }
      if (req.method === 'POST' && route?.startsWith('api/キーテスト/')) {
        const id=route.slice('api/キーテスト/'.length);
        if (!KEY_PROVIDERS.some(provider=>provider.id===id)) return reply(404,{エラー:'未対応の項目です。'});
        if (req.headers['transfer-encoding'] || (req.headers['content-length'] && req.headers['content-length'] !== '0')) return reply(400,{エラー:'キーテストへの引数は指定できません。'});
        if (keyBusy) return reply(409,{エラー:'キーテスト実行中です。完了後に再試行してください。'});
        keyBusy=true;
        try {reply(200,await keyTestFn(id,{publicCache:publicCache.input()}));} finally {keyBusy=false;}
        return;
      }
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
  let options;try {options=parseArgs(args);}catch {throw startupError('ARGUMENTS');}
  if (options.help) { console.log('AiDiy 診断: aidiy_diag [--browser] [--no-open] [--port 8097] [--base-path /proxy/8097/]'); return; }
  if (!await verifyUi()) throw startupError('UI');
  const useBrowser=browserMode(options);
  let executable;
  if (!useBrowser) {
    try {executable=await desktopBinary();}
    catch {throw startupError('ELECTRON');}
  }
  const initialStop=await stopRevision();
  const token=randomBytes(32).toString('base64url');
  let entries,coverage;
  try {entries=await catalog();coverage=JSON.parse(await readFile(new URL('./coverage.json',import.meta.url),'utf8'));}
  catch {throw startupError('CATALOG');}
  const publicCache=createPublicModelCache();
  const server=createServer({token,prefix:options.prefix,entries,coverage,publicCache});
  await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(options.port,'127.0.0.1',resolve);});
  // 公開一覧だけを起動時に取得。キー設定や他 provider の API は自動で呼ばない。
  void publicCache.refresh();
  const url=publicUrl(server.address().port,options.prefix)+'#token='+token;
  let stopWatching=()=>{}, desktop;
  const close=()=>{stopWatching();cancelProbes();cancelKeyProbes();closeDesktop(desktop);server.close();server.closeAllConnections();};
  if (useBrowser) {
    console.log('AiDiy 診断: '+url);
    console.log('この起動中のみ有効な認証 URL です。共有せず、転送ポートは非公開にしてください。Ctrl+C で終了。');
    if (!options.noOpen && process.env.CODESPACES !== 'true') openBrowser(url);
  } else {
    console.log('AiDiy 診断: Electron ウィンドウを開きます。Ctrl+C で終了。');
    try {desktop=openDesktop(executable,url,close);} catch {close();throw startupError('DESKTOP');}
  }
  stopWatching=watchStop(initialStop,close);
  server.once('close',()=>stopWatching());
  process.once('SIGINT',close);process.once('SIGTERM',close);
  return server;
}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) main().catch(error=>{console.error(startupMessage(error));process.exitCode=1;});
