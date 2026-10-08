import { createServer, type ServerResponse } from 'node:http';
import { readFileSync, writeFileSync, statSync } from 'node:fs';
import { join, resolve, basename } from 'node:path';
import { randomBytes, randomUUID } from 'node:crypto';
import { CodeConnection, コード選択 } from '../../src/code-connection';
import { ローカル接続先 } from '../../aidiy_live/local-backend.cjs';
import { streamControlOf, visibleStreamContent } from '../../src/protocol';
import { コードモデル読込, コードモデル保存, モデル保存先 } from '../../src/model-preferences';
import { 接続元許可 } from '../../src/forwarded-origin';

// 単独画面と拡張で AIコア接続・メッセージ形式・描画を共用する。
export async function 単独起動(project: string, backend?: string, initialModel: { provider?: string; model?: string } = {}, modelFile = モデル保存先('code')) {
  const root = resolve(__dirname, '../..');
  const folder = resolve(project);
  if (!statSync(folder).isDirectory()) throw new Error('作業フォルダがありません。');
  const savedModel = コードモデル読込(modelFile);
  const requestedProvider = initialModel.provider?.trim(), requestedModel = initialModel.model?.trim();
  const remembered = !requestedModel && (!requestedProvider || requestedProvider === savedModel?.provider) ? savedModel : undefined;
  const state = {
    type: 'state', 会話ID: randomUUID() as string, 作業URI: folder, 信頼済み: true,
    作業フォルダ: { 名前: basename(folder), パス: folder },
    ...コード選択({ provider: remembered?.provider ?? requestedProvider ?? '', model: remembered?.model ?? requestedModel ?? '' }),
    接続済み: false, 接続エラー: '', モデル変更中: false,
    メッセージ: [] as { 種別: string; 本文: string }[], 進捗: [] as string[], 実行中: false,
    セッションID: undefined as string | undefined,
    履歴: [] as { id: string; 題名: string; 更新日時: number }[]
  };
  type 保存会話 = { id: string; メッセージ: typeof state.メッセージ; セッションID?: string; provider: string; model: string; 更新日時: number; 初回依頼?: string };
  let history: 保存会話[] = [];
  let lastModel = { provider: state.provider, model: state.model };
  const clients = new Set<ServerResponse>();
  let 接続開始済み = false;
  let closed = false;
  const token = randomBytes(24).toString('hex');
  const prefix = `/${token}/`;
  let origin = '';
  let allowed: 接続元許可 | undefined;
  let idle: NodeJS.Timeout | undefined;
  const broadcast = (packet: unknown) => { for (const client of clients) client.write(`data: ${JSON.stringify(packet)}\n\n`); };
  const notify = () => broadcast(state);
  const save = (更新日時を変更 = true) => {
    if (!state.メッセージ.length && !state.セッションID) return;
    const previous = history.find(item => item.id === state.会話ID);
    const entry: 保存会話 = { id: state.会話ID, メッセージ: [...state.メッセージ], セッションID: state.セッションID,
      provider: state.provider, model: state.model, 更新日時: 更新日時を変更 ? Date.now() : previous?.更新日時 ?? Date.now(),
      初回依頼: previous?.初回依頼 ?? state.メッセージ.find(message => message.種別 === 'user')?.本文.replace(/\s+/g, ' ').slice(0, 160) };
    history = [entry, ...history.filter(item => item.id !== entry.id)];
    state.履歴 = [...history].sort((a, b) => b.更新日時 - a.更新日時)
      .map(item => ({ id: item.id, 題名: item.初回依頼 || '新しい会話', 更新日時: item.更新日時 }));
  };
  const trimHistory = () => {
    let size = 0;
    state.メッセージ = state.メッセージ.slice(-60).reverse().filter(item => (size += item.本文.length) <= 2_000_000).reverse();
  };
  const connection = new CodeConnection(backend || ローカル接続先(root, folder), packet => {
    broadcast(packet);
    const text = typeof packet.メッセージ内容 === 'string' ? packet.メッセージ内容 : '';
    if (packet.メッセージ識別 === 'output_stream') {
      const control = streamControlOf(text);
      if (control === 'start') state.実行中 = true;
      else if (control === 'cancel') state.実行中 = false;
      else if (!control && text) state.進捗 = [...state.進捗, visibleStreamContent(text).slice(0, 4000)].slice(-100);
    } else if (packet.メッセージ識別 === 'output_text' || packet.メッセージ識別 === 'output') {
      if (text) state.メッセージ.push({ 種別: 'assistant', 本文: text });
      state.実行中 = false;
    } else if (['error', 'cancel_run', 'output_end'].includes(packet.メッセージ識別 || '')) {
      if (text) state.メッセージ.push({ 種別: 'error', 本文: text });
      state.実行中 = false;
    } else return;
    trimHistory(); save(); notify();
  }, () => {
    state.モデル変更中 = connection.modelChanging;
    state.接続済み = connection.connected; state.接続エラー = connection.error;
    if (connection.connected) {
      state.セッションID = connection.session;
      state.provider = connection.model.provider; state.model = connection.model.model;
    } else state.実行中 = false;
    notify();
  });
  const reconnect = () => connection.start(folder, { provider: state.provider, model: state.model }, state.セッションID, state.メッセージ);
  const execute = (text: string) => {
    if (!connection.send({ メッセージ識別: 'input_text', メッセージ内容: text })) throw new Error('AIコアが未接続のため送信できません。');
    state.実行中 = true; state.進捗 = [];
    state.メッセージ.push({ 種別: 'user', 本文: text }); trimHistory();
    save(); broadcast({type:'accepted'}); notify();
  };
  const server = createServer(async (req, res) => {
    res.setHeader('Cache-Control', 'no-store');
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('Referrer-Policy', 'no-referrer');
    const reply = (code: number, value: unknown) => { res.writeHead(code, {'Content-Type':'application/json; charset=utf-8'}); res.end(JSON.stringify(value)); };
    try {
      // ローカル（Codespaces ではポート転送先も）専用。別サイトからの CLI 実行、DNS rebinding を受け付けない。
      if (!allowed?.host(req.headers.host) || !req.url?.startsWith(prefix)) { reply(404, {error:'Not found'}); return; }
      if (req.headers.origin && !allowed.origin(req.headers.origin)) { reply(403, {error:'Forbidden'}); return; }
      const url = new URL(req.url, origin);
      const route = url.pathname.slice(prefix.length);
      if (req.method === 'GET' && route === 'events') {
        clearTimeout(idle);
        res.writeHead(200, {'Content-Type':'text/event-stream', Connection:'keep-alive'});
        clients.add(res); res.write(`data: ${JSON.stringify(state)}\n\n`);
        if (!接続開始済み) { 接続開始済み = true; reconnect(); }
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
        const items = await connection.catalog(provider);
        reply(200, provider ? { models: items } : { providers: items }); return;
      }
      if (req.method === 'POST' && route === 'message') {
        if (!allowed.origin(req.headers.origin) || !req.headers['content-type']?.startsWith('application/json')) { reply(403, {error:'Forbidden'}); return; }
        req.setEncoding('utf8');
        let body = '';
        for await (const chunk of req) { body += chunk.toString(); if (body.length > 1_000_000) { reply(413, {error:'Message too long'}); return; } }
        const data = JSON.parse(body);
        const type = data.メッセージ識別 ?? data.type;
        if (type === 'cancel_run') {
          if (!connection.send({ メッセージ識別: 'cancel_run', メッセージ内容: '強制停止！' })) { reply(409, {error:'AIコアが未接続です。'}); return; }
        } else if (type === 'disconnect') connection.disconnect();
        else if (type === 'connect') { 接続開始済み = true; reconnect(); }
        else if (connection.modelChanging) { reply(409, {error:'モデルを変更しています。'}); return; }
        else if (state.実行中) { reply(409, {error:'実行中です。'}); return; }
        else if (type === 'input_text') {
          if (typeof data.メッセージ内容 !== 'string' || !data.メッセージ内容.trim() || data.メッセージ内容.length > 200000) { reply(400, {error:'入力が空か長すぎます。'}); return; }
          if (!state.接続済み) { reply(409, {error:'AIコアが未接続のため送信できません。'}); return; }
          execute(data.メッセージ内容);
        } else if (type === 'new') {
          state.会話ID = randomUUID(); state.メッセージ = []; state.進捗 = []; state.セッションID = undefined;
          state.provider = lastModel.provider; state.model = lastModel.model; reconnect(); notify();
        } else if (type === 'selectHistory') {
          const entry = history.find(item => item.id === data.id);
          if (!entry) { reply(404, {error:'会話がありません。'}); return; }
          state.会話ID = entry.id; state.メッセージ = [...entry.メッセージ]; state.セッションID = entry.セッションID;
          state.provider = entry.provider; state.model = entry.model; state.進捗 = []; reconnect(); notify();
        } else if (type === 'deleteHistory') {
          const entry = history.find(item => item.id === data.id);
          if (!entry) { reply(404, {error:'会話がありません。'}); return; }
          history = history.filter(item => item.id !== data.id);
          state.履歴 = state.履歴.filter(item => item.id !== data.id);
          if (state.会話ID === data.id) {
            state.会話ID = randomUUID(); state.メッセージ = []; state.進捗 = []; state.セッションID = undefined;
            state.provider = lastModel.provider; state.model = lastModel.model; reconnect();
          }
          notify();
        } else if (type === 'model') {
          if (typeof data.provider !== 'string' || typeof data.model !== 'string' || data.provider.length > 200 || data.model.length > 300) { reply(400, {error:'モデル指定が不正です。'}); return; }
          const selected = コード選択({ provider: data.provider, model: data.model });
          await connection.setModel(selected);
          コードモデル保存(selected, modelFile);
          state.provider = selected.provider; state.model = selected.model; lastModel = selected; save(false); notify();
        } else { reply(400, {error:'Unknown message'}); return; }
        reply(200, {ok:true}); return;
      }
      const assets: Record<string, [string, string]> = {
        'AiDiy.png':['media/AiDiy.png','image/png'],
        'chat.css':['media/chat.css','text/css'], 'theme.css':['aidiy_code/theme.css','text/css'], 'sending.png':['media/sending.png','image/png'], 'abort.png':['media/abort.png','image/png'],
        'bridge.js':['aidiy_code/bridge.js','text/javascript'], 'webview.js':['dist/webview.js','text/javascript']
      };
      if (req.method === 'GET' && Object.hasOwn(assets, route)) {
        const [file, type] = assets[route]; res.writeHead(200, {'Content-Type':`${type}; charset=utf-8`}); res.end(readFileSync(join(root,file))); return;
      }
      if (req.method === 'GET' && route === '') {
        const nonce = randomBytes(16).toString('hex');
        const html = readFileSync(join(root,'media/chat.html'),'utf8')
          .replaceAll('{{CSP}}', "'self'").replaceAll('{{NONCE}}',nonce)
          .replaceAll('{{APP_ICON}}','AiDiy.png')
          .replaceAll('{{STYLE}}','chat.css').replaceAll('{{SCRIPT}}','webview.js').replaceAll('{{SEND_ICON}}','sending.png').replaceAll('{{STOP_ICON}}','abort.png')
          .replace("connect-src 'none'", "connect-src 'self'")
          .replace('</head>', '<link rel="icon" type="image/png" href="AiDiy.png"><link rel="stylesheet" href="theme.css"></head>')
          .replace('<script nonce=', `<script nonce="${nonce}" src="bridge.js"></script><script nonce=`);
        res.setHeader('Content-Security-Policy', "frame-ancestors 'none'");
        res.writeHead(200, {'Content-Type':'text/html; charset=utf-8'}); res.end(html); return;
      }
      reply(404, {error:'Not found'});
    } catch (error) { if (!res.headersSent) reply(500, {error: error instanceof Error ? error.message : '処理に失敗しました。'}); else res.end(); }
  });
  async function close() {
    if (closed) return; closed = true;
    clearTimeout(idle);
    if (state.実行中) connection.send({ メッセージ識別: 'cancel_run' });
    connection.dispose();
    for (const client of clients) client.end(); clients.clear();
    server.closeAllConnections(); await new Promise<void>(resolve => server.close(() => resolve()));
    clearTimeout(idle);
  }
  await new Promise<void>((resolve, reject) => { server.once('error',reject); server.listen(0,'127.0.0.1',resolve); });
  const address = server.address();
  if (!address || typeof address === 'string') throw new Error('起動できません。');
  origin = `http://127.0.0.1:${address.port}`;
  allowed = new 接続元許可(address.port);
  if (allowed.初回待機時間 !== undefined) idle = setTimeout(() => { void close(); }, allowed.初回待機時間);
  return {url:origin+prefix, publicUrl:allowed.公開URL(prefix), close};
}

if (require.main === module) {
  const project = process.argv[2] || process.cwd();
  void 単独起動(project, undefined, process.argv[4] ? JSON.parse(process.argv[4]) : {}).then(app => {
    if (process.argv[3]) writeFileSync(process.argv[3], JSON.stringify({url:app.url, publicUrl:app.publicUrl, pid:process.pid}), 'utf8');
    else console.log(`AiDiy (Code): ${app.url}`);
    process.on('SIGINT', () => { void app.close(); });
    process.on('SIGTERM', () => { void app.close(); });
  }).catch(error => { console.error(String(error)); process.exitCode = 1; });
}
