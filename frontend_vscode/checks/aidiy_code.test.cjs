const { test, after } = require('node:test');
const assert = require('node:assert/strict');
const { resolve, join } = require('node:path');
const { mkdtempSync, rmSync, readFileSync, writeFileSync } = require('node:fs');
const { tmpdir } = require('node:os');
const { 単独起動: start } = require('../out/aidiy_code/server.cjs');
const preferences = mkdtempSync(join(tmpdir(), 'aidiy-code-model-'));
after(() => rmSync(preferences, { recursive: true, force: true }));
let fileNumber = 0;
const 単独起動 = (project, launch, initial, file = join(preferences, `${++fileNumber}.json`)) => start(project, launch, initial, file);
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
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
test('Code: AIコアのモデル候補・選択値・送信と停止を中継し、未接続では送信を拒否する', async t => {
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
    assert.equal((await post(app,{メッセージ識別:'input_text',メッセージ内容:'切断中'})).status,409);
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
