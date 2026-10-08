const { test } = require('node:test');
const assert = require('node:assert/strict');
const { runInNewContext } = require('node:vm');
const { readFileSync } = require('node:fs');
const { transformSync } = require('esbuild');
const { core } = require('./fake-core.cjs');
const flush = async () => { for (let i=0;i<8;i++) await new Promise(resolve=>setImmediate(resolve)); };

test('Code 拡張: AIコアへ接続、モデル選択と送信、切断中の拒否、非表示からの復帰と破棄', async t => {
  const backend = core(); backend.install(t);
  const posts = [], saved = [], context = { extensionPath: process.cwd(), extensionUri: {fsPath:process.cwd()}, subscriptions:[],
    workspaceState:{get(){},update(key,value){saved.push(value);return Promise.resolve();}}, globalState:{get(){},update(){return Promise.resolve();}} };
  const uri = { scheme:'file',fsPath:'/project',toString:()=> 'file:///project' }, folder = {uri,name:'project'};
  let provider, receive, disposed, visibility, selected;
  const subscription = {dispose(){}};
  const vscode = { workspace:{isTrusted:true,workspaceFolders:[folder],getConfiguration:()=>({get:(_key,fallback)=>fallback}),
    getWorkspaceFolder:()=>folder,onDidChangeWorkspaceFolders:()=>subscription},
    window:{activeTextEditor:undefined,onDidChangeActiveTextEditor:()=>subscription,
      createOutputChannel:()=>({appendLine(){},clear(){},dispose(){}}),registerWebviewViewProvider(_id,object){provider=object;return subscription;}},
    Uri:{joinPath:(_uri,path)=>({fsPath:path})},commands:{registerCommand:()=>subscription,executeCommand:async()=>{}},
  };
  const loaded = {exports:{}};
  runInNewContext(transformSync(readFileSync('src/extension.ts','utf8'),{loader:'ts',format:'cjs'}).code,{
    exports:loaded.exports,module:loaded,require(name){
      if(name==='vscode') return vscode;
      if(name==='./code-connection') return require('../out/code-connection.cjs');
      if(name==='./model-preferences') return {コードモデル読込:()=>undefined,コードモデル保存:value=>(selected=value)};
      if(name==='./runner') return require('../out/runner.cjs');
      if(name==='./protocol') return require('../out/protocol.cjs');
      if(name==='../aidiy_live/local-backend.cjs') return {ローカル接続先:()=> 'http://127.0.0.1:18091'};
      return require(name);
    },setTimeout,clearTimeout,console,
  });
  loaded.exports.activate(context);
  const view = {visible:true,webview:{options:{},cspSource:'self',asWebviewUri:uri=>uri.fsPath,
    postMessage(packet){posts.push(JSON.parse(JSON.stringify(packet)));return Promise.resolve();},
    onDidReceiveMessage(callback){receive=callback;return subscription;}},
    onDidDispose(callback){disposed=callback;return subscription;}, onDidChangeVisibility(callback){visibility=callback;return subscription;}};
  provider.resolveWebviewView(view);
  try {
    receive({type:'ready'});await flush();
    assert.equal(posts.findLast(p=>p.type==='state').接続済み,true);
    receive({type:'chooseModel',provider:'aidiy_hermes'});await flush();
    assert.ok(posts.findLast(p=>p.type==='modelCatalog').items.some(m=>m.id==='openai_oauth/gpt-6.1-sol'));
    receive({type:'setModel',provider:'copilot_cli',model:'gpt-6-sol'});await flush();
    assert.deepEqual(selected,{provider:'copilot_cli',model:'gpt-6-sol'});
    receive({メッセージ識別:'input_text',メッセージ内容:'調査'});await flush();
    const state=posts.findLast(p=>p.type==='state');assert.equal(state.メッセージ.at(-1).種別,'assistant');
    assert.ok(state.コアセッションID); assert.equal(state.メッセージ.filter(p=>p.種別==='user').length,1);
    view.visible=false;visibility();view.visible=true;visibility();assert.equal(posts.findLast(p=>p.type==='state').接続済み,true);
    receive({type:'disconnect'});await flush();receive({メッセージ識別:'input_text',メッセージ内容:'切断中'});await flush();
    assert.equal(posts.findLast(p=>p.type==='state').接続済み,false);
    assert.match(posts.findLast(p=>p.type==='state').メッセージ.at(-1).本文,/未接続/);
    receive({type:'connect'});await flush();assert.equal(posts.findLast(p=>p.type==='state').接続済み,true);
    disposed();assert.ok(backend.sockets.every(s=>s.readyState===3));
  } finally { provider.dispose(); }
});
