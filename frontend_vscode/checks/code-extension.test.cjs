const { test } = require('node:test');
const assert = require('node:assert/strict');
const { runInNewContext } = require('node:vm');
const { readFileSync } = require('node:fs');
const { transformSync } = require('esbuild');
const { core } = require('./fake-core.cjs');
const { screen } = require('./code-screen.cjs');
const flush = async () => { for (let i=0;i<8;i++) await new Promise(resolve=>setImmediate(resolve)); };

test('Code 拡張: 接続状態ごとのモデル保存・復元、Hermes実行、再接続中の維持と停止', async t => {
  t.mock.timers.enable({apis:['setTimeout','setInterval']});
  const backend = core(); backend.install(t);
  const posts = [], saved = [], context = { extensionPath: process.cwd(), extensionUri: {fsPath:process.cwd()}, subscriptions:[],
    workspaceState:{get(){},update(key,value){saved.push(value);return Promise.resolve();}}, globalState:{get(){},update(){return Promise.resolve();}} };
  const uri = { scheme:'file',fsPath:'/project',toString:()=> 'file:///project' }, folder = {uri,name:'project'};
  let provider, receive, disposed, visibility, selected;
  const preferences = new Map([['online.json', {provider:'codex_cli',model:'auto'}],
    ['online_offline.json', {provider:'aidiy_hermes',model:'openai_oauth/gpt-6.1-sol'}]]);
  const runs = [];
  const subscription = {dispose(){}};
  const vscode = { workspace:{isTrusted:true,workspaceFolders:[],getConfiguration:()=>({get:(_key,fallback)=>fallback}),
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
      if(name==='./model-preferences') return {
        モデル保存先:()=> 'online.json', コードモデル読込:(file='online.json')=>preferences.get(file),
        コードモデル保存:(value,file='online.json')=>{ selected=JSON.parse(JSON.stringify(value));preferences.set(file,selected);return selected; },
        コード設定保存先:()=> 'options.json', 検証回数読込:file=>preferences.get(file)?.検証回数,
        検証回数保存:(count,file)=>{ if(![0,1,2,3].includes(count)) throw new Error('検証回数の指定が不正です。'); preferences.set(file,{検証回数:count}); return count; },
      };
      if(name==='./runner') return {起動解決:()=>({実行ファイル:'fake-hermes',引数:[]})};
      if(name==='../aidiy_code/src/offline') return {
        ...require('../out/offline.cjs'),Hermes既定モデル:()=> 'openai_oauth/gpt-6-astra',
        オフライン実行(root,project,model,text,session,receive,launch) {
          let finish;
          const run={root,project,model,text,session,launch,receive,stops:0,
            完了:new Promise(resolve=>{finish=resolve;}),停止(){run.stops++;},finish(result={終了コード:0,セッションID:'hermes-only'}){finish(result);}};
          runs.push(run);receive({メッセージ識別:'output_stream',メッセージ内容:'\x02'});return run;
        }
      };
      if(name==='./protocol') return require('../out/protocol.cjs');
      if(name==='../aidiy_live/local-backend.cjs') return {ローカル接続先:()=> 'http://127.0.0.1:18091'};
      return require(name);
    },setTimeout,clearTimeout,console,
  });
  loaded.exports.activate(context);
  const ui = screen(message => receive?.(message));
  const view = {visible:true,webview:{options:{},cspSource:'self',asWebviewUri:uri=>uri.fsPath,
    postMessage(packet){const state=JSON.parse(JSON.stringify(packet));posts.push(state);ui.notify(state);return Promise.resolve();},
    onDidReceiveMessage(callback){receive=callback;return subscription;}},
    onDidDispose(callback){disposed=callback;return subscription;}, onDidChangeVisibility(callback){visibility=callback;return subscription;}};
  provider.resolveWebviewView(view);
  try {
    visibility();
    let latest = () => posts.findLast(p=>p.type==='state');
    assert.equal(latest().provider,'aidiy_hermes');assert.equal(latest().model,'openai_oauth/gpt-6.1-sol');
    assert.equal(latest().実行モード,'offline');assert.equal(latest().オフライン対応,true);
    assert.equal(ui.element('choose-model').disabled,false);
    ui.element('choose-model').listeners.get('click')();await flush();
    assert.equal(ui.element('model-picker').open,true);
    assert.equal(ui.element('model-select').disabled,false);
    assert.equal(ui.element('apply-model').disabled,false);
    ui.element('model-select').value='auto';ui.element('apply-model').listeners.get('click')();await flush();
    assert.equal(latest().model,'auto');
    // 作業フォルダを開くと、接続失敗・再試行中も入力とモデル選択を許可する。
    vscode.workspace.workspaceFolders=[folder];backend.unavailable=true;
    receive({type:'ready'});await flush();
    assert.equal(ui.element('error').hidden,false);
    assert.match(ui.element('error').textContent,/接続できません/);
    ui.input('未接続で送信');assert.equal(ui.element('send').disabled,false);
    assert.equal(ui.element('choose-model').disabled,false);
    assert.equal(ui.element('self-check-loop').value,'0');
    assert.equal(ui.element('self-check-loop').disabled,true);
    receive({type:'connect'});ui.input('接続試行中も送信');
    assert.equal(ui.element('send').disabled,false);assert.equal(ui.element('choose-model').disabled,false);
    await flush();
    receive({type:'setModel',provider:'aidiy_hermes',model:'openai_oauth/gpt-6.1-sol'});await flush();
    backend.unavailable=false;
    receive({type:'connect'});await flush();
    assert.equal(ui.element('error').hidden,true);assert.equal(ui.element('error').textContent,'');
    receive({type:'ready'});await flush();
    assert.ok(posts.some(p=>p.type==='state' && p.接続中 && !p.接続済み));
    assert.equal(posts.findLast(p=>p.type==='state').接続済み,true);
    assert.equal(latest().provider,'codex_cli');assert.equal(latest().model,'auto');
    assert.equal(latest().自動接続,true);
    const sessionBeforeToggle = latest().コアセッションID;
    const conversationBeforeToggle = latest().会話ID;
    ui.element('auto-connect').listeners.get('click')();await flush();
    assert.equal(latest().自動接続,false);assert.equal(latest().接続済み,false);
    assert.ok(backend.sockets.every(socket=>socket.readyState===3));
    const socketCount = backend.sockets.length;
    receive({type:'ready'});await flush();
    receive({type:'new'});await flush();
    receive({type:'selectHistory',id:conversationBeforeToggle});await flush();
    assert.equal(latest().会話ID,conversationBeforeToggle);
    assert.equal(backend.sockets.length,socketCount);
    ui.element('auto-connect').listeners.get('click')();await flush();
    assert.equal(latest().自動接続,true);assert.equal(latest().接続済み,true);
    assert.equal(latest().コアセッションID,sessionBeforeToggle);
    receive({type:'chooseModel',provider:'aidiy_hermes'});await flush();
    assert.ok(posts.findLast(p=>p.type==='modelCatalog').items.some(m=>m.id==='openai_oauth/gpt-6.1-sol'));
    receive({type:'setModel',provider:'copilot_cli',model:'gpt-6-sol'});await flush();
    assert.deepEqual(selected,{provider:'copilot_cli',model:'gpt-6-sol'});
    let finishCatalog;
    backend.catalogWait=new Promise(resolve=>{finishCatalog=resolve;});
    receive({type:'setModel',provider:'copilot_cli',model:'gpt-6-sol'});await flush();
    assert.equal(latest().モデル変更中,true);
    const beforeModelChange=latest().会話ID, beforeModelSockets=backend.sockets.length;
    for(const data of [{type:'autoConnect',enabled:false},{type:'new'},{type:'disconnect'}]) receive(data);
    await flush();assert.equal(latest().会話ID,beforeModelChange);assert.equal(latest().自動接続,true);
    assert.equal(backend.sockets.length,beforeModelSockets);
    finishCatalog();backend.catalogWait=undefined;await flush();assert.equal(latest().モデル変更中,false);
    receive({メッセージ識別:'input_text',メッセージ内容:'調査'});await flush();
    const state=posts.findLast(p=>p.type==='state');assert.equal(state.メッセージ.at(-1).種別,'assistant');
    assert.ok(state.コアセッションID); assert.equal(state.メッセージ.filter(p=>p.種別==='user').length,1);
    const latestRequest = () => backend.sockets.flatMap(socket=>socket.sent).findLast(packet=>packet.メッセージ識別==='input_text');
    assert.equal(latestRequest().self_check_loop,1);
    for (const count of [0,1,2,3]) {
      receive({メッセージ識別:'input_text',メッセージ内容:`検証${count}回`,self_check_loop:count});await flush();
      assert.equal(latestRequest().self_check_loop,count);
    }
    // 画面で選び直した検証回数を保存し、状態通知で返す（次回の起動で復元する）。
    assert.equal(posts.findLast(p=>p.type==='state').検証回数,0);
    receive({type:'setSelfCheckLoop',count:2});await flush();
    assert.deepEqual(preferences.get('options.json'),{検証回数:2});
    receive({type:'ready'});await flush();
    assert.equal(posts.findLast(p=>p.type==='state').検証回数,2);
    view.visible=false;visibility();view.visible=true;visibility();assert.equal(posts.findLast(p=>p.type==='state').接続済み,true);
    const coreSession = latest().コアセッションID;
    backend.hold=true;
    receive({メッセージ識別:'input_text',メッセージ内容:'スイッチ変更拒否の確認'});await flush();
    receive({type:'autoConnect',enabled:false});await flush();
    assert.equal(latest().自動接続,true);assert.equal(latest().接続済み,true);
    for(const type of ['connect','disconnect']) {receive({type});await flush();assert.equal(latest().接続済み,true);assert.equal(latest().実行中,true);}
    backend.holdCancel=true;
    ui.element('stop').listeners.get('click')();await flush();
    assert.equal(latest().停止中,true);assert.equal(latest().実行中,true);
    assert.equal(ui.element('auto-connect').disabled,true);assert.equal(ui.element('stop').disabled,true);
    const stopsBefore=backend.sockets.flatMap(s=>s.sent).filter(p=>p.メッセージ識別==='cancel_run').length;
    receive({メッセージ識別:'cancel_run'});await flush();
    assert.equal(backend.sockets.flatMap(s=>s.sent).filter(p=>p.メッセージ識別==='cancel_run').length,stopsBefore);
    receive({type:'autoConnect',enabled:false});await flush();assert.equal(latest().自動接続,true);
    backend.sockets.findLast(s=>s.channel==='1' && s.readyState===1).emit({メッセージ識別:'output_end',メッセージ内容:'',実行中:false});await flush();
    assert.equal(latest().停止中,false);assert.equal(latest().実行中,false);
    backend.holdCancel=false;backend.hold=false;
    receive({type:'disconnect'});await flush();
    assert.equal(latest().接続済み,false);assert.equal(latest().provider,'aidiy_hermes');
    assert.equal(latest().model,'openai_oauth/gpt-6.1-sol');
    const requestsBefore = backend.requests.length;
    receive({type:'chooseModel',provider:''});await flush();
    assert.deepEqual(posts.findLast(p=>p.type==='modelCatalog').items.map(m=>m.id),['aidiy_hermes']);
    receive({type:'chooseModel',provider:'aidiy_hermes'});await flush();
    assert.ok(posts.findLast(p=>p.type==='modelCatalog').items.some(m=>m.id==='copilot_cli/auto'));
    receive({type:'setModel',provider:'aidiy_hermes',model:'copilot_cli/auto'});await flush();
    assert.equal(latest().model,'copilot_cli/auto');assert.equal(backend.requests.length,requestsBefore);
    assert.deepEqual(preferences.get('online.json'),{provider:'copilot_cli',model:'gpt-6-sol'});
    assert.deepEqual(preferences.get('online_offline.json'),{provider:'aidiy_hermes',model:'copilot_cli/auto'});
    backend.unavailable=true;receive({type:'autoConnect',enabled:true});await flush();
    ui.input('切断中');assert.equal(ui.element('send').disabled,false);
    ui.element('composer').listeners.get('submit')({preventDefault(){}});await flush();
    assert.equal(runs.length,1);assert.equal(runs[0].model,'copilot_cli/auto');assert.equal(runs[0].session,undefined);
    assert.equal(runs[0].project,'/project');assert.equal(latest().実行中,true);
    backend.unavailable=false;t.mock.timers.tick(5000);await flush();assert.equal(latest().接続済み,true);
    assert.equal(latest().実行モード,'offline');assert.equal(latest().model,'copilot_cli/auto');assert.equal(latest().実行中,true);
    for(const data of [{type:'autoConnect',enabled:false},{type:'autoConnect',enabled:true},{type:'connect'},{type:'disconnect'}]) {
      receive(data);await flush();assert.equal(latest().接続済み,true);assert.equal(latest().実行中,true);
    }
    const id=latest().会話ID;
    receive({type:'new'});receive({type:'setModel',provider:'aidiy_hermes',model:'auto'});
    receive({メッセージ識別:'input_text',メッセージ内容:'重複'});await flush();
    assert.equal(latest().会話ID,id);assert.equal(runs.length,1);
    runs[0].receive({メッセージ識別:'output_text',メッセージ内容:'Hermes回答'});
    assert.equal(latest().実行中,true);
    runs[0].finish();await flush();
    assert.equal(latest().実行中,false);assert.equal(latest().provider,'copilot_cli');assert.equal(latest().model,'gpt-6-sol');
    assert.equal(latest().HermesセッションID,'hermes-only');assert.equal(latest().コアセッションID,coreSession);
    receive({type:'disconnect'});await flush();
    receive({メッセージ識別:'input_text',メッセージ内容:'Hermes続き'});await flush();
    assert.equal(runs[1].session,'hermes-only');assert.equal(runs[1].model,'copilot_cli/auto');
    receive({メッセージ識別:'cancel_run'});await flush();assert.equal(runs[1].stops,1);
    runs[1].receive({メッセージ識別:'output_stream',メッセージ内容:'\x18'});
    receive({メッセージ識別:'cancel_run'});await flush();assert.equal(runs[1].stops,1);
    assert.equal(latest().実行中,true);assert.equal(latest().停止中,true);
    runs[1].finish({終了コード:1,停止理由:'停止しました。'});await flush();assert.equal(latest().実行中,false);
    receive({type:'connect'});await flush();assert.equal(latest().provider,'copilot_cli');
    // 再起動でもモード別の保存値を読む。
    provider.dispose();loaded.exports.activate(context);provider.resolveWebviewView(view);visibility();
    assert.equal(latest().provider,'aidiy_hermes');assert.equal(latest().model,'copilot_cli/auto');
    receive({type:'ready'});await flush();assert.equal(latest().provider,'copilot_cli');assert.equal(latest().model,'gpt-6-sol');
    assert.equal(latest().自動接続,true);
    receive({type:'disconnect'});await flush();vscode.workspace.isTrusted=false;
    receive({メッセージ識別:'input_text',メッセージ内容:'未信頼'});await flush();assert.equal(runs.length,2);
    assert.match(latest().メッセージ.at(-1).本文,/信頼/);vscode.workspace.isTrusted=true;
    receive({メッセージ識別:'input_text',メッセージ内容:'破棄前'});await flush();
    disposed();assert.ok(backend.sockets.every(s=>s.readyState===3));
    assert.equal(runs[2].stops,1);runs[2].finish();await flush();
  } finally { provider.dispose(); }
});
