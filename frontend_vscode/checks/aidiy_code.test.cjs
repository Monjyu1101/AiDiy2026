const { test, after } = require('node:test');
const assert = require('node:assert/strict');
const { resolve, join } = require('node:path');
const { mkdtempSync, mkdirSync, rmSync, readFileSync, writeFileSync } = require('node:fs');
const { tmpdir } = require('node:os');
const { 単独起動: start } = require('../out/aidiy_code/server.cjs');
const { オフライン実行, オフラインモデル保存先, オフラインモデル候補, Hermes既定モデル } = require('../out/offline.cjs');
const preferences = mkdtempSync(join(tmpdir(), 'aidiy-code-model-'));
after(() => rmSync(preferences, { recursive: true, force: true }));
let fileNumber = 0;
const 単独起動 = (project, launch, initial, file = join(preferences, `${++fileNumber}.json`)) => start(project, launch, initial, file);
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
test('Code: Hermes既定モデルを共通設定から読み、モデル候補はbatと同じ固定値に限定する', () => {
  const root = join(preferences, 'configured');
  mkdirSync(join(root, '_config'), {recursive:true});
  const file = join(root, '_config/AiDiy_key.json');
  writeFileSync(file, '\uFEFF' + JSON.stringify({CODE_AIDIY_HERMES_MODEL:'openai_oauth/configured-model'}));
  assert.equal(Hermes既定モデル(join(root, 'frontend_vscode')), 'openai_oauth/configured-model');
  const expected = ['auto','codex_cli/auto','copilot_cli/auto','openai_oauth/gpt-6-astra','openai_oauth/gpt-6.1-sol','openai_oauth/gpt-5.6-terra','openai_oauth/gpt-6-luna'];
  assert.deepEqual(オフラインモデル候補(root).map(p=>p.id), expected);
  assert.deepEqual(オフラインモデル候補(process.cwd()).map(p=>p.id), expected);
  writeFileSync(file, '{}');
  assert.equal(Hermes既定モデル(root), 'auto');
});
async function connect(app) {
  const reader = (await fetch(app.url+'events')).body.getReader();
  const packets = [];
  const pump = (async () => {
    let buffer = ''; const decoder = new TextDecoder();
    while (true) {
      const {value, done} = await reader.read(); if (done) return;
      buffer += decoder.decode(value,{stream:true});
      let end;
      while ((end = buffer.indexOf('\n\n')) >= 0) {
        const block = buffer.slice(0,end); buffer = buffer.slice(end+2);
        if (block.startsWith('data: ')) packets.push(JSON.parse(block.slice(6)));
      }
    }
  })();
  return {packets, close:async()=>{await reader.cancel(); await pump;}, wait:async predicate=>{
    const deadline = Date.now()+7000;
    while (Date.now()<deadline) { const found = packets.find(predicate); if (found) return found; await pause(20); }
    throw new Error('SSE timeout');
  }};
}
function post(app, data, origin = new URL(app.url).origin) {
  return fetch(app.url+'message',{method:'POST',headers:{Origin:origin,'Content-Type':'application/json'},body:JSON.stringify(data)});
}
test('Code: AIコアのモデル候補・選択値・送信と停止を中継する', async t => {
  const backend = require('./fake-core.cjs').core(); backend.install(t);
  const file = join(preferences, 'remember.json');
  const app = await 単独起動(process.cwd(), 'http://127.0.0.1:18091', {}, file);
  const stream = await connect(app);
  try {
    const ready = await stream.wait(p => p.type === 'state' && p.接続済み);
    assert.equal(ready.provider, 'aidiy_hermes'); assert.equal(ready.model, 'openai_oauth/gpt-6.1-sol');
    assert.deepEqual(backend.sockets.map(socket => socket.channel), ['input', '1']);
    assert.ok(backend.sockets.every(socket => socket.sent[0].CODE_BASE_PATH === process.cwd()));
    const providers = await (await fetch(app.url + 'catalog')).json();
    assert.ok(providers.providers.some(item => item.id === 'copilot_cli'));
    const hermes = await (await fetch(app.url + 'catalog?provider=aidiy_hermes')).json();
    assert.ok(hermes.models.some(item => item.id === 'openai_oauth/gpt-6.1-sol'));
    assert.equal((await fetch(new URL('/events', app.url))).status, 404);
    assert.equal((await post(app, {type:'new'}, 'https://example.com')).status, 403);
    await post(app, { type:'model', provider:'copilot_cli', model:'gpt-6-sol' });
    assert.deepEqual(JSON.parse(readFileSync(file, 'utf8')), { provider:'copilot_cli', model:'gpt-6-sol' });
    assert.equal((await post(app, {メッセージ識別:'input_text', メッセージ内容:'日本語で確認'})).status, 200);
    const completed = await stream.wait(p => p.type==='state' && !p.実行中 && p.メッセージ.some(m=>m.種別==='assistant'));
    const reply = JSON.parse(completed.メッセージ.at(-1).本文);
    assert.equal(reply.input, '日本語で確認');
    assert.equal(reply.settings.CODE_AI1_NAME, 'copilot_cli'); assert.equal(reply.settings.CODE_AI1_MODEL, 'gpt-6-sol');
    assert.ok(completed.進捗.every(line=>!/[\u0002\u0003\u0018]/.test(line)));
    await post(app, {type:'new'});
    await stream.wait(p=>p.type==='state' && p.会話ID!==ready.会話ID && p.接続済み);
    await post(app, {type:'selectHistory', id:ready.会話ID});
    const reopened = await stream.wait(p=>p.type==='state' && p.会話ID===ready.会話ID && p.接続済み && p.メッセージ.length===2);
    assert.equal(reopened.セッションID, ready.セッションID);
    await post(app, {type:'disconnect'});
    assert.equal((await post(app,{メッセージ識別:'input_text',メッセージ内容:' '})).status,400);
    await post(app, {type:'connect'});
    await pause(30);
    backend.hold = true;
    await post(app, {メッセージ識別:'input_text',メッセージ内容:'待機'});
    await stream.wait(p=>p.type==='state' && p.実行中 && p.メッセージ.at(-1)?.本文==='待機');
    assert.equal((await post(app,{type:'model',provider:'aidiy_hermes',model:'auto'})).status,409);
    await post(app,{メッセージ識別:'cancel_run'});
    await stream.wait(p=>p.type==='state' && !p.実行中 && p.メッセージ.at(-1)?.本文==='処理中断！');
  } finally { await stream.close(); await app.close(); }
});

test('Code: 単独起動の検証ループ指定をAIコアへ渡し、未指定は1回にする', async t => {
  const backend = require('./fake-core.cjs').core(); backend.install(t);
  const app = await 単独起動(process.cwd(),'http://127.0.0.1:18091',{}), stream = await connect(app);
  try {
    await stream.wait(p=>p.type==='state' && p.接続済み);
    for (const count of [undefined,0,1,2,3]) {
      const text = `検証回数: ${count}`;
      const response = await post(app,{メッセージ識別:'input_text',メッセージ内容:text,self_check_loop:count});
      assert.equal(response.status,200);
      await stream.wait(p=>p.type==='state' && !p.実行中 && p.メッセージ.some(m=>m.種別==='assistant' && JSON.parse(m.本文).input===text));
      const request = backend.sockets.flatMap(socket=>socket.sent).findLast(packet=>packet.メッセージ識別==='input_text');
      assert.equal(request.self_check_loop,count ?? 1);
    }
  } finally { await stream.close(); await app.close(); }
});

test('Code: 最終選択を復元し、旧Hermes Providerを組み合わせモデルへ移行する', async t => {
  const backend = require('./fake-core.cjs').core(); backend.install(t);
  const file = join(preferences,'migration.json');
  writeFileSync(file, JSON.stringify({provider:'openai_oauth',model:'gpt-6.1-sol'}));
  for (const [initial, provider, model] of [
    [{}, 'aidiy_hermes', 'openai_oauth/gpt-6.1-sol'],
    [{provider:'copilot-cli',model:'gpt-6-sol'}, 'copilot_cli', 'gpt-6-sol'],
  ]) {
    const app = await 単独起動(process.cwd(),'http://127.0.0.1:18091',initial,file), stream = await connect(app);
    try {
      const state = await stream.wait(p=>p.type==='state' && p.接続済み);
      assert.equal(state.provider,provider); assert.equal(state.model,model);
      assert.equal(JSON.parse(readFileSync(file,'utf8')).provider,'openai_oauth');
    } finally { await stream.close(); await app.close(); }
  }
});

test('Code offline: コアなしでHermesを直接実行し、モデル保存・継続・新規をオンラインから分離する', async t => {
  const backend = require('./fake-core.cjs').core(); backend.install(t); backend.unavailable = true;
  const file = join(preferences,'offline-models.json');
  const online = {provider:'copilot_cli',model:'gpt-6-sol'};
  writeFileSync(file,JSON.stringify(online));
  const calls = [];
  const run = (...args) => {
    calls.push({model:args[2],session:args[4]});
    return オフライン実行(...args,{実行ファイル:process.execPath,引数:[resolve('checks/fake-cli.cjs'),'echo']});
  };
  const app = await start(process.cwd(),'http://127.0.0.1:18091',{offline:true},file,run), stream = await connect(app);
  try {
    const initial = await stream.wait(p=>p.type==='state' && p.実行モード==='offline');
    assert.equal(initial.provider,'aidiy_hermes'); assert.equal(initial.model,Hermes既定モデル(process.cwd()));
    assert.equal(backend.sockets.length,0); assert.equal(backend.requests.length,0);
    assert.deepEqual((await (await fetch(app.url+'catalog')).json()).providers.map(p=>p.id),['aidiy_hermes']);
    const catalog = await (await fetch(app.url+'catalog?provider=aidiy_hermes')).json();
    const bat=readFileSync(resolve('../scripts/cli_bat/_hermes_cli.bat'),'utf8');
    const expected=[...new Set(['auto',...[...bat.matchAll(/set "MODEL=([^"%\r\n]+)"/g)].map(match=>match[1])])];
    assert.deepEqual(catalog.models.map(p=>p.id),expected);
    assert.equal((await post(app,{type:'model',provider:'copilot_cli',model:'auto'})).status,400);
    assert.equal((await post(app,{type:'model',provider:'aidiy_hermes',model:'openai_oauth/unlisted'})).status,400);
    assert.equal((await post(app,{type:'model',provider:'aidiy_hermes',model:'openai_oauth/gpt-6.1-sol'})).status,200);
    assert.deepEqual(JSON.parse(readFileSync(file,'utf8')),online);
    assert.deepEqual(JSON.parse(readFileSync(オフラインモデル保存先(file),'utf8')),{provider:'aidiy_hermes',model:'openai_oauth/gpt-6.1-sol'});
    for (const text of ['初回','継続']) {
      assert.equal((await post(app,{メッセージ識別:'input_text',メッセージ内容:text,self_check_loop:3})).status,200);
      const done = await stream.wait(p=>p.type==='state' && !p.実行中 && p.セッションID==='test-session-001' && p.メッセージ.some(m=>m.種別==='assistant' && JSON.parse(m.本文).input===text));
      const answer = JSON.parse(done.メッセージ.at(-1).本文);
      assert.ok(answer.args.includes('openai_oauth/gpt-6.1-sol')); assert.equal(answer.cwd,process.cwd());
      assert.ok(!answer.args.includes('--yolo'));
    }
    assert.equal(calls.length,2); assert.equal(calls[0].session,undefined); assert.equal(calls[1].session,'test-session-001');
    await post(app,{type:'new'});
    await post(app,{メッセージ識別:'input_text',メッセージ内容:'新規'});
    await stream.wait(p=>p.type==='state' && !p.実行中 && p.メッセージ.some(m=>m.種別==='assistant' && JSON.parse(m.本文).input==='新規'));
    assert.equal(calls[2].session,undefined);
    assert.equal(backend.sockets.length,0); assert.equal(backend.requests.length,0);
    backend.unavailable=false;
    await post(app,{type:'executionMode',mode:'online'});
    const connected = await stream.wait(p=>p.type==='state' && p.実行モード==='online' && p.接続済み);
    assert.equal(connected.provider,online.provider); assert.equal(connected.model,online.model);
    assert.notEqual(connected.セッションID,'test-session-001');
    await post(app,{type:'executionMode',mode:'offline'});
    await stream.wait(p=>p.type==='state' && p.実行モード==='offline' && p.会話ID!==initial.会話ID && p.model==='openai_oauth/gpt-6.1-sol');
    assert.ok(backend.sockets.every(s=>s.readyState===3));
    await post(app,{type:'selectHistory',id:initial.会話ID});
    const restored = await stream.wait(p=>p.type==='state' && p.会話ID===initial.会話ID && p.セッションID==='test-session-001' && !p.実行中);
    assert.equal(restored.実行モード,'offline');
  } finally { await stream.close(); await app.close(); }
  const reopened = await start(process.cwd(),'http://127.0.0.1:18091',{offline:true},file,run), second = await connect(reopened);
  try {
    const restored = await second.wait(p=>p.type==='state' && p.実行モード==='offline');
    assert.equal(restored.model,'openai_oauth/gpt-6.1-sol');
  } finally { await second.close(); await reopened.close(); }
});

test('Code offline: CLI組み合わせモデルはHermesのCLI Providerへ渡す', async () => {
  for (const provider of ['codex','copilot']) {
    const job = オフライン実行(process.cwd(), process.cwd(), `${provider}_cli/auto`, '引数確認', undefined, ()=>{},
      {実行ファイル:process.execPath,引数:[resolve('checks/fake-cli.cjs'),'echo']});
    const result = await job.完了;
    assert.equal(result.終了コード,0);
    const {args} = JSON.parse(result.回答);
    assert.equal(args[args.indexOf('--provider')+1], `${provider}-cli`);
    assert.ok(!args.includes('--model'));
  }
});

test('Code offline: 候補外の保存値は候補へ追加せず、設定の既定値へ戻す', async t => {
  const backend = require('./fake-core.cjs').core(); backend.install(t);
  const file = join(preferences,'unlisted.json');
  writeFileSync(オフラインモデル保存先(file),JSON.stringify({provider:'aidiy_hermes',model:'openai_oauth/unlisted'}));
  const app = await start(process.cwd(),'http://127.0.0.1:18091',{offline:true},file), stream = await connect(app);
  try {
    const state = await stream.wait(p=>p.type==='state');
    const catalog = await (await fetch(app.url+'catalog?provider=aidiy_hermes')).json();
    assert.ok(catalog.models.some(p=>p.id===state.model));
    assert.ok(!catalog.models.some(p=>p.id==='openai_oauth/unlisted'));
    assert.equal((await post(app,{type:'model',provider:'aidiy_hermes',model:'openai_oauth/unlisted'})).status,400);
    assert.equal((await post(app,{type:'model',provider:'codex_cli',model:'auto'})).status,400);
  } finally { await stream.close(); await app.close(); }
});

test('Code offline: 実行中の切替を拒否し、停止と画面終了でジョブを終了する', async t => {
  const backend = require('./fake-core.cjs').core(); backend.install(t);
  let stopped=0;
  const run = () => {
    let finish;
    return {完了:new Promise(resolve=>{finish=resolve;}),停止:()=>{stopped++;finish({回答:'',ログ:'',終了コード:0,停止理由:'停止しました'});}};
  };
  const app = await start(process.cwd(),'http://127.0.0.1:18091',{offline:true},join(preferences,'stop.json'),run), stream = await connect(app);
  try {
    await post(app,{メッセージ識別:'input_text',メッセージ内容:'待機'});
    assert.equal((await post(app,{type:'executionMode',mode:'online'})).status,409);
    assert.equal((await post(app,{type:'model',provider:'aidiy_hermes',model:'auto'})).status,409);
    await post(app,{メッセージ識別:'cancel_run'});
    await stream.wait(p=>p.type==='state' && !p.実行中 && p.メッセージ.some(m=>m.本文==='停止しました'));
    assert.equal(stopped,1);
    await post(app,{メッセージ識別:'input_text',メッセージ内容:'終了待機'});
  } finally { await stream.close(); await app.close(); }
  assert.equal(stopped,2); assert.equal(backend.sockets.length,0);
});

test('Code: 未接続はHermesへ送信し、実行中も自動再接続、完了後はAIコアへ戻す', async t => {
  const backend = require('./fake-core.cjs').core(); backend.install(t); backend.unavailable = true;
  const file = join(preferences,'automatic-offline.json');
  const online = {provider:'copilot_cli',model:'gpt-6-sol'};
  writeFileSync(file,JSON.stringify(online));
  const jobs = [];
  const run = (_root, _folder, model, text, session, receive) => {
    let finish;
    const done = new Promise(resolve=>{finish=resolve;});
    const job = {model,text,session,stopped:false, finish:()=>{
      receive({メッセージ識別:'output_text',メッセージ内容:`Hermes: ${text}`});
      finish({セッションID:'hermes-session',終了コード:0});
    }};
    jobs.push(job);
    return {完了:done,停止:()=>{job.stopped=true;finish({終了コード:0,停止理由:'停止しました'});}};
  };
  const app = await start(process.cwd(),'http://127.0.0.1:18091',{},file,run), stream = await connect(app);
  try {
    const initial = await stream.wait(p=>p.type==='state' && Boolean(p.接続エラー));
    assert.equal(initial.実行モード,'offline'); assert.equal(initial.provider,'aidiy_hermes');
    assert.equal((await post(app,{メッセージ識別:'input_text',メッセージ内容:' '})).status,400);
    assert.deepEqual((await (await fetch(app.url+'catalog')).json()).providers.map(p=>p.id),['aidiy_hermes']);
    assert.equal((await post(app,{type:'model',provider:'aidiy_hermes',model:'auto'})).status,200);
    assert.deepEqual(JSON.parse(readFileSync(file,'utf8')),online);
    assert.equal(JSON.parse(readFileSync(オフラインモデル保存先(file),'utf8')).model,'auto');
    assert.equal((await post(app,{メッセージ識別:'input_text',メッセージ内容:'未接続の依頼',self_check_loop:3})).status,200);
    assert.equal(jobs.length,1); assert.equal(jobs[0].model,'auto'); assert.equal(jobs[0].session,undefined);
    backend.unavailable = false;
    // 手動接続なしで5秒後の再試行を通す。Hermes実行は接続成功後も保持する。
    await stream.wait(p=>p.type==='state' && p.接続済み && p.実行中 && p.実行モード==='offline');
    assert.equal((await post(app,{メッセージ識別:'input_text',メッセージ内容:'二重送信'})).status,409);
    jobs[0].finish();
    const ready = await stream.wait(p=>p.type==='state' && p.接続済み && !p.実行中 && p.実行モード==='online');
    assert.equal(ready.provider,online.provider); assert.equal(ready.model,online.model);
    assert.notEqual(ready.セッションID,'hermes-session');
    assert.equal((await post(app,{メッセージ識別:'input_text',メッセージ内容:'オンラインの依頼',self_check_loop:2})).status,200);
    await stream.wait(p=>p.type==='state' && !p.実行中 && p.メッセージ.some(m=>m.本文.includes('"input":"オンラインの依頼"')));
    const coreInput = backend.sockets.flatMap(s=>s.sent).filter(p=>p.メッセージ識別==='input_text');
    assert.equal(coreInput.length,1); assert.equal(coreInput[0].self_check_loop,2);
    backend.unavailable = true;
    for (const socket of backend.sockets) socket.close();
    await stream.wait(p=>p.type==='state' && !p.接続済み && p.メッセージ.some(m=>m.本文==='オンラインの依頼'));
    assert.equal((await post(app,{メッセージ識別:'input_text',メッセージ内容:'Hermesの継続'})).status,200);
    assert.equal(jobs[1].session,'hermes-session');
    assert.equal((await post(app,{メッセージ識別:'cancel_run'})).status,200);
    assert.equal(jobs[1].stopped,true);
    await stream.wait(p=>p.type==='state' && !p.実行中 && p.メッセージ.some(m=>m.本文==='停止しました'));
    await post(app,{type:'new'});
    await post(app,{メッセージ識別:'input_text',メッセージ内容:'新規の依頼'});
    assert.equal(jobs[2].session,undefined);
  } finally { await stream.close(); await app.close(); }
  assert.equal(jobs[2].stopped,true);
});

test('Code offline: CLI起動失敗を表示し、再入力可能にする', async t => {
  const backend = require('./fake-core.cjs').core(); backend.install(t);
  const app = await start(process.cwd(),'http://127.0.0.1:18091',{offline:true},join(preferences,'failure.json'),()=>{throw new Error('Hermes未配置');});
  const stream = await connect(app);
  try {
    await post(app,{メッセージ識別:'input_text',メッセージ内容:'依頼'});
    await stream.wait(p=>p.type==='state' && !p.実行中 && p.メッセージ.some(m=>m.種別==='error' && m.本文.includes('Hermes未配置')));
  } finally { await stream.close(); await app.close(); }
});
