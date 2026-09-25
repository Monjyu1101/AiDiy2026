import { createServer, type ServerResponse } from 'node:http';
import { readFileSync, writeFileSync, statSync } from 'node:fs';
import { join, resolve, basename } from 'node:path';
import { randomBytes, randomUUID } from 'node:crypto';
import { CLI実行, 会話引数, 起動解決, type 起動設定 } from './runner';
import { コード要求実行, streamControlOf, visibleStreamContent } from './protocol';

// 単独試用も拡張と同じ CLI・メッセージ形式・描画を使う。
export async function 単独起動(project: string, launch?: 起動設定) {
  const root = resolve(__dirname, '..');
  const folder = resolve(project);
  if (!statSync(folder).isDirectory()) throw new Error('作業フォルダがありません。');
  const defaults = JSON.parse(readFileSync(join(root, 'package.json'), 'utf8')).contributes.configuration.properties;
  const state = {
    type: 'state', 会話ID: randomUUID() as string, 作業URI: folder, 信頼済み: true,
    作業フォルダ: { 名前: basename(folder), パス: folder },
    provider: String(defaults['aidiyHermes.provider'].default), model: String(defaults['aidiyHermes.model'].default),
    メッセージ: [] as { 種別: string; 本文: string }[], 進捗: [] as string[], 実行中: false,
    セッションID: undefined as string | undefined,
    履歴: [] as { id: string; 題名: string; 更新日時: number }[]
  };
  type 保存会話 = { id: string; メッセージ: typeof state.メッセージ; セッションID?: string; provider: string; model: string; 更新日時: number };
  let history: 保存会話[] = [];
  let lastModel = { provider: state.provider, model: state.model };
  const clients = new Set<ServerResponse>();
  let job: ReturnType<typeof コード要求実行> | undefined;
  const catalogJobs = new Set<ReturnType<typeof CLI実行>>();
  const token = randomBytes(24).toString('hex');
  const prefix = `/${token}/`;
  let origin = '';
  let idle: NodeJS.Timeout | undefined;
  const broadcast = (packet: unknown) => { for (const client of clients) client.write(`data: ${JSON.stringify(packet)}\n\n`); };
  const notify = () => broadcast(state);
  const save = () => {
    if (!state.メッセージ.length && !state.セッションID) return;
    const entry: 保存会話 = { id: state.会話ID, メッセージ: [...state.メッセージ], セッションID: state.セッションID,
      provider: state.provider, model: state.model, 更新日時: Date.now() };
    history = [entry, ...history.filter(item => item.id !== entry.id)];
    state.履歴 = history.map(item => ({ id: item.id, 題名: item.メッセージ.find(message => message.種別 === 'user')?.本文.replace(/\s+/g, ' ').slice(0, 80) || '新しい会話', 更新日時: item.更新日時 }));
  };
  const trimHistory = () => {
    let size = 0;
    state.メッセージ = state.メッセージ.slice(-60).reverse().filter(item => (size += item.本文.length) <= 2_000_000).reverse();
  };
  const execute = async (text: string) => {
    state.実行中 = true; state.進捗 = [];
    state.メッセージ.push({ 種別: 'user', 本文: text }); trimHistory();
    save(); broadcast({type:'accepted'}); notify();
    try {
      job = コード要求実行({ セッションID: state.会話ID, チャンネル: 'code1', メッセージ識別: 'input_text', メッセージ内容: text }, {
        起動: launch ?? 起動解決('aidiy_hermes', '', folder), 作業フォルダ: folder,
        引数: 会話引数(state.provider, state.model, 30, state.セッションID), 制限時間: 900_000
      }, packet => {
        broadcast(packet);
        if (packet.メッセージ識別 === 'output_stream') {
          if (streamControlOf(packet.メッセージ内容)) return;
          const line = visibleStreamContent(packet.メッセージ内容);
          if (!line) return;
          state.進捗 = [...state.進捗, line.slice(0, 4000)].slice(-100); notify();
        }
      });
      const result = await job.完了;
      if (result.セッションID) state.セッションID = result.セッションID;
      if (result.回答) state.メッセージ.push({ 種別: 'assistant', 本文: result.回答 });
      if (result.停止理由 || result.終了コード !== 0 || !result.回答) {
        state.メッセージ.push({ 種別: 'error', 本文: result.停止理由 || `CLI が回答を完了できませんでした。\n${result.ログ.slice(-3000)}` });
      }
    } catch (error) { state.メッセージ.push({ 種別: 'error', 本文: String(error) }); }
    finally { state.実行中 = false; job = undefined; trimHistory(); save(); notify(); }
  };
  const server = createServer(async (req, res) => {
    res.setHeader('Cache-Control', 'no-store');
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('Referrer-Policy', 'no-referrer');
    const reply = (code: number, value: unknown) => { res.writeHead(code, {'Content-Type':'application/json; charset=utf-8'}); res.end(JSON.stringify(value)); };
    try {
      // ローカル専用。別サイトからの CLI 実行、DNS rebinding を受け付けない。
      if (req.headers.host !== origin.slice(7) || !req.url?.startsWith(prefix)) { reply(404, {error:'Not found'}); return; }
      if (req.headers.origin && req.headers.origin !== origin) { reply(403, {error:'Forbidden'}); return; }
      const url = new URL(req.url, origin);
      const route = url.pathname.slice(prefix.length);
      if (req.method === 'GET' && route === 'events') {
        clearTimeout(idle);
        res.writeHead(200, {'Content-Type':'text/event-stream', Connection:'keep-alive'});
        clients.add(res); res.write(`data: ${JSON.stringify(state)}\n\n`);
        const heartbeat = setInterval(() => res.write(': heartbeat\n\n'), 15000);
        res.on('close', () => {
          clearInterval(heartbeat); clients.delete(res);
          if (!clients.size) idle = setTimeout(() => { void close(); }, 60_000);
        });
        return;
      }
      if (req.method === 'GET' && route === 'catalog') {
        const provider = url.searchParams.get('provider') ?? '';
        if (provider.length > 200) { reply(400, {error:'Provider too long'}); return; }
        const cli = launch ?? 起動解決('aidiy_hermes', '', folder);
        if (!cli.引数[0]?.endsWith('.py')) throw new Error('候補取得には AiDiy の CLI が必要です。');
        const task = CLI実行({ 起動: {実行ファイル:cli.実行ファイル, 引数:[join(root,'scripts/model-catalog.py'),cli.引数[0],provider]}, 作業フォルダ:folder, 本文:'', 引数:[], 制限時間:30000 });
        catalogJobs.add(task);
        try {
          const result = await task.完了;
          if (result.終了コード !== 0) throw new Error('モデル候補を取得できません。');
          reply(200, JSON.parse(result.回答)); return;
        } finally { catalogJobs.delete(task); }
      }
      if (req.method === 'POST' && route === 'message') {
        if (req.headers.origin !== origin || !req.headers['content-type']?.startsWith('application/json')) { reply(403, {error:'Forbidden'}); return; }
        req.setEncoding('utf8');
        let body = '';
        for await (const chunk of req) { body += chunk.toString(); if (body.length > 1_000_000) { reply(413, {error:'Message too long'}); return; } }
        const data = JSON.parse(body);
        const type = data.メッセージ識別 ?? data.type;
        if (type === 'cancel_run') job?.停止();
        else if (state.実行中) { reply(409, {error:'実行中です。'}); return; }
        else if (type === 'input_text') {
          if (typeof data.メッセージ内容 !== 'string' || !data.メッセージ内容.trim() || data.メッセージ内容.length > 200000) { reply(400, {error:'入力が空か長すぎます。'}); return; }
          void execute(data.メッセージ内容);
        } else if (type === 'new') {
          state.会話ID = randomUUID(); state.メッセージ = []; state.進捗 = []; state.セッションID = undefined;
          state.provider = lastModel.provider; state.model = lastModel.model; notify();
        } else if (type === 'selectHistory') {
          const entry = history.find(item => item.id === data.id);
          if (!entry) { reply(404, {error:'会話がありません。'}); return; }
          state.会話ID = entry.id; state.メッセージ = [...entry.メッセージ]; state.セッションID = entry.セッションID;
          state.provider = entry.provider; state.model = entry.model; state.進捗 = []; notify();
        } else if (type === 'deleteHistory') {
          const entry = history.find(item => item.id === data.id);
          if (!entry) { reply(404, {error:'会話がありません。'}); return; }
          history = history.filter(item => item.id !== data.id);
          state.履歴 = state.履歴.filter(item => item.id !== data.id);
          if (state.会話ID === data.id) {
            state.会話ID = randomUUID(); state.メッセージ = []; state.進捗 = []; state.セッションID = undefined;
            state.provider = lastModel.provider; state.model = lastModel.model;
          }
          notify();
        } else if (type === 'model') {
          if (typeof data.provider !== 'string' || typeof data.model !== 'string' || data.provider.length > 200 || data.model.length > 300) { reply(400, {error:'モデル指定が不正です。'}); return; }
          state.provider = data.provider.trim(); state.model = data.model.trim(); lastModel = { provider: state.provider, model: state.model }; save(); notify();
        } else { reply(400, {error:'Unknown message'}); return; }
        reply(200, {ok:true}); return;
      }
      const assets: Record<string, [string, string]> = {
        'chat.css':['media/chat.css','text/css'], 'theme.css':['standalone/theme.css','text/css'], 'sending.png':['media/sending.png','image/png'],
        'bridge.js':['standalone/bridge.js','text/javascript'], 'webview.js':['dist/webview.js','text/javascript']
      };
      if (req.method === 'GET' && Object.hasOwn(assets, route)) {
        const [file, type] = assets[route]; res.writeHead(200, {'Content-Type':`${type}; charset=utf-8`}); res.end(readFileSync(join(root,file))); return;
      }
      if (req.method === 'GET' && route === '') {
        const nonce = randomBytes(16).toString('hex');
        const html = readFileSync(join(root,'media/chat.html'),'utf8')
          .replaceAll('{{CSP}}', "'self'").replaceAll('{{NONCE}}',nonce)
          .replaceAll('{{STYLE}}','chat.css').replaceAll('{{SCRIPT}}','webview.js').replaceAll('{{SEND_ICON}}','sending.png')
          .replace("connect-src 'none'", "connect-src 'self'")
          .replace('</head>', '<link rel="stylesheet" href="theme.css"></head>')
          .replace('<script nonce=', `<script nonce="${nonce}" src="bridge.js"></script><script nonce=`);
        res.setHeader('Content-Security-Policy', "frame-ancestors 'none'");
        res.writeHead(200, {'Content-Type':'text/html; charset=utf-8'}); res.end(html); return;
      }
      reply(404, {error:'Not found'});
    } catch (error) { if (!res.headersSent) reply(500, {error: error instanceof Error ? error.message : '処理に失敗しました。'}); else res.end(); }
  });
  async function close() {
    clearTimeout(idle); job?.停止(); for (const task of catalogJobs) task.停止();
    for (const client of clients) client.end(); clients.clear();
    server.closeAllConnections(); await new Promise<void>(resolve => server.close(() => resolve()));
    clearTimeout(idle);
  }
  await new Promise<void>((resolve, reject) => { server.once('error',reject); server.listen(0,'127.0.0.1',resolve); });
  const address = server.address();
  if (!address || typeof address === 'string') throw new Error('起動できません。');
  origin = `http://127.0.0.1:${address.port}`;
  idle = setTimeout(() => { void close(); }, 120_000);
  return {url:origin+prefix, close};
}

if (require.main === module) {
  const project = process.argv[2] || process.cwd();
  void 単独起動(project).then(app => {
    if (process.argv[3]) writeFileSync(process.argv[3], JSON.stringify({url:app.url, pid:process.pid}), 'utf8');
    else console.log(`AiDiy: ${app.url}`);
    process.on('SIGINT', () => { void app.close(); });
    process.on('SIGTERM', () => { void app.close(); });
  }).catch(error => { console.error(String(error)); process.exitCode = 1; });
}
