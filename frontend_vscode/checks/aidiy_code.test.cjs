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
const fake = resolve('checks/fake-cli.cjs');
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
test('Code: 手動選択をJSONへ保存し、再起動・別フォルダで復元、起動引数では上書きしない', async () => {
  const file = join(preferences, 'remember.json');
  const launch = { 実行ファイル: process.execPath, 引数: [fake, 'echo'] };
  let app = await 単独起動(process.cwd(), launch, {}, file), stream = await connect(app);
  try {
    await stream.wait(p => p.type === 'state');
    assert.equal((await post(app, { type: 'model', provider: 'freeai', model: '手動-model' })).status, 200);
    assert.deepEqual(JSON.parse(readFileSync(file, 'utf8')), { provider: 'freeai', model: '手動-model' });
  } finally { await stream.close(); await app.close(); }
  for (const [project, initial, provider, model] of [
    [preferences, {}, 'freeai', '手動-model'],
    [process.cwd(), { provider: 'freeai' }, 'freeai', '手動-model'],
    [process.cwd(), { provider: 'copilot-cli' }, 'copilot-cli', 'auto'],
    [process.cwd(), { provider: 'codex-cli', model: 'explicit' }, 'codex-cli', 'explicit'],
    [process.cwd(), {}, 'freeai', '手動-model'],
  ]) {
    app = await 単独起動(project, launch, initial, file); stream = await connect(app);
    try {
      const state = await stream.wait(p => p.type === 'state');
      assert.equal(state.provider, provider); assert.equal(state.model, model);
      assert.equal(JSON.parse(readFileSync(file, 'utf8')).model, '手動-model');
    } finally { await stream.close(); await app.close(); }
  }
  app = await 単独起動(process.cwd(), launch, {}, file); stream = await connect(app);
  try { await post(app, { type: 'model', provider: '', model: '' }); }
  finally { await stream.close(); await app.close(); }
  app = await 単独起動(process.cwd(), launch, {}, file); stream = await connect(app);
  try {
    const state = await stream.wait(p => p.type === 'state');
    assert.equal(state.provider, ''); assert.equal(state.model, '');
  } finally { await stream.close(); await app.close(); }
  writeFileSync(file, '{broken', 'utf8');
  app = await 単独起動(process.cwd(), launch, {}, file); stream = await connect(app);
  try {
    const state = await stream.wait(p => p.type === 'state');
    assert.equal(state.provider, 'openai_oauth'); assert.equal(state.model, 'gpt-6.1-sol');
    assert.equal(readFileSync(file, 'utf8'), '{broken');
  } finally { await stream.close(); await app.close(); }
});
test('単独画面: 起動時の Provider / モデルを表示・実行・新規会話に反映する', async t => {
  for (const [provider, model] of [['copilot-cli', 'claude-sonnet-5.5'], ['openai_oauth', 'gpt-6-astra'], ['claude-code', 'auto'], ['codex-cli', 'auto'], ['copilot-cli', 'auto']]) {
    await t.test(provider, async () => {
      const app = await 単独起動(process.cwd(), {実行ファイル:process.execPath, 引数:[fake,'echo']}, { provider: ` ${provider} `, model: ` ${model} ` });
      const stream = await connect(app);
      try {
        const initial = await stream.wait(p=>p.type==='state');
        assert.equal(initial.provider, provider); assert.equal(initial.model, model);
        await post(app, {メッセージ識別:'input_text', メッセージ内容:'起動時の選択を確認'});
        const completed = await stream.wait(p=>p.type==='state' && !p.実行中 && p.メッセージ.some(m=>m.種別==='assistant'));
        const reply = JSON.parse(completed.メッセージ.find(m=>m.種別==='assistant').本文);
        assert.equal(reply.args[reply.args.indexOf('--provider')+1], provider);
        if (model === 'auto') assert.ok(!reply.args.includes('--model'));
        else assert.equal(reply.args[reply.args.indexOf('--model')+1], model);
        await post(app, {type:'new'});
        const reset = await stream.wait(p=>p.type==='state' && p.会話ID!==initial.会話ID);
        assert.equal(reset.provider, provider); assert.equal(reset.model, model);
      } finally { await stream.close(); await app.close(); }
    });
  }
});
test('単独画面: 接続制限・送信・継続・履歴選択と削除・最終モデル', async () => {
  const app = await 単独起動(process.cwd(), {実行ファイル:process.execPath, 引数:[fake,'echo']});
  const stream = await connect(app);
  try {
    const initial = await stream.wait(p=>p.type==='state');
    assert.equal(initial.provider,'openai_oauth'); assert.equal(initial.model,'gpt-6.1-sol');
    assert.equal((await fetch(new URL('/events',app.url))).status,404);
    assert.equal((await post(app,{type:'new'},'https://example.com')).status,403);
    assert.equal((await post(app,{メッセージ識別:'input_text',メッセージ内容:'日本語で確認'})).status,200);
    const completed = await stream.wait(p=>p.type==='state' && !p.実行中 && p.メッセージ.some(m=>m.種別==='assistant'));
    const reply = JSON.parse(completed.メッセージ.find(m=>m.種別==='assistant').本文);
    assert.equal(reply.input,'日本語で確認'); assert.equal(reply.cwd,process.cwd());
    assert.ok(reply.args.includes('gpt-6.1-sol')); assert.ok(reply.args.includes('openai_oauth'));
    assert.ok(stream.packets.some(p=>p.メッセージ識別==='output_stream' && p.メッセージ内容.includes('日本語の進捗')));
    assert.ok(completed.進捗.every(line=>!/[\u0002\u0003\u0018]/.test(line)));
    assert.equal(completed.履歴[0].題名,'日本語で確認');
    const lastMessageAt = completed.履歴[0].更新日時;
    await post(app,{type:'model',provider:'freeai',model:'custom-model'});
    const modelChanged = await stream.wait(p=>p.type==='state' && p.model==='custom-model');
    assert.equal(modelChanged.履歴[0].更新日時,lastMessageAt);
    await post(app,{メッセージ識別:'input_text',メッセージ内容:'続き'});
    const resumed = await stream.wait(p=>p.type==='state' && !p.実行中 && p.メッセージ.filter(m=>m.種別==='assistant').length===2);
    const second = JSON.parse(resumed.メッセージ.at(-1).本文);
    assert.ok(second.args.includes('--resume')); assert.ok(second.args.includes('test-session-001'));
    assert.ok(second.args.includes('custom-model'));
    assert.equal(resumed.履歴[0].題名,'日本語で確認');
    await post(app,{type:'new'});
    const reset = await stream.wait(p=>p.type==='state' && p.会話ID!==initial.会話ID);
    assert.equal(reset.メッセージ.length,0); assert.equal(reset.セッションID,undefined);
    assert.equal(reset.model,'custom-model');
    assert.equal(reset.履歴.length,1);
    assert.match(reset.履歴[0].題名,/日本語で確認/);
    await post(app,{type:'selectHistory',id:initial.会話ID});
    const reopened = await stream.wait(p=>p.type==='state' && p.会話ID===initial.会話ID && p.メッセージ.length>=4);
    assert.equal(reopened.セッションID,'test-session-001');
    await post(app,{type:'deleteHistory',id:initial.会話ID});
    const deleted = await stream.wait(p=>p.type==='state' && p.会話ID!==initial.会話ID && p.履歴.length===0);
    assert.equal(deleted.メッセージ.length,0);
    assert.equal((await post(app,{type:'selectHistory',id:initial.会話ID})).status,404);
  } finally { await stream.close(); await app.close(); }
});
test('単独画面: 実行中のモデル変更を拒否して停止できる', async () => {
  const dir = mkdtempSync(join(tmpdir(),'aidiy-standalone-'));
  const app = await 単独起動(process.cwd(),{実行ファイル:process.execPath,引数:[fake,'wait',join(dir,'pid.json')]});
  const stream = await connect(app);
  try {
    await post(app,{メッセージ識別:'input_text',メッセージ内容:'待機'});
    await stream.wait(p=>p.メッセージ識別==='output_stream' && p.メッセージ内容==='waiting');
    assert.equal((await post(app,{type:'model',provider:'freeai',model:''})).status,409);
    await post(app,{メッセージ識別:'cancel_run'});
    await stream.wait(p=>p.type==='state' && !p.実行中 && p.メッセージ.some(m=>m.種別==='error' && m.本文.includes('停止')));
  } finally { await stream.close(); await app.close(); rmSync(dir,{recursive:true,force:true}); }
});
