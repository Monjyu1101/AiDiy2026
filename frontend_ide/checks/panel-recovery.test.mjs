// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
// 実際のVue SFCをコンパイルし、通信と画面資源だけを置き換えて失敗時の状態を確認する。
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { randomUUID } from 'node:crypto';
import { createRequire } from 'node:module';
import vm from 'node:vm';
const require=createRequire(import.meta.url);
const vue=require('vue'),{parse,compileScript}=require('@vue/compiler-sfc'),{transformSync}=require('esbuild');
const MarkdownIt=require('markdown-it');

function setupComponent(name,{props={},modules={},globals={}}={}) {
  const source=readFileSync(new URL(`../src/components/${name}.vue`,import.meta.url),'utf8');
  const {descriptor}=parse(source);
  const script=compileScript(descriptor,{id:name,genDefaultAs:'component'});
  const {code}=transformSync(`${script.content}\nmodule.exports=component;`,{format:'cjs'});
  const mounted=[],unmounted=[],emitted=[],timers=new Map();let timerId=0;
  const module={exports:{}};
  vm.runInNewContext(code,{
    module,URL,URLSearchParams,AbortController,AbortSignal,Response,crypto:{randomUUID},
    location:{href:'http://localhost/',protocol:'http:'},
    setTimeout:callback=>{timers.set(++timerId,callback);return timerId;},clearTimeout:id=>timers.delete(id),
    setInterval:callback=>{timers.set(++timerId,callback);return timerId;},clearInterval:id=>timers.delete(id),
    requestAnimationFrame:()=>0,cancelAnimationFrame(){},
    ResizeObserver:class {observe(){}disconnect(){}},
    require(id){
      if(id==='vue')return {...vue,onMounted:callback=>mounted.push(callback),onBeforeUnmount:callback=>unmounted.push(callback)};
      if(id==='markdown-it')return MarkdownIt;
      if(Object.hasOwn(modules,id))return modules[id];
      throw Error(`予期しない依存: ${id}`);
    },...globals,
  },{filename:`${name}.vue`});
  const scope=vue.effectScope();
  const state=scope.run(()=>module.exports.setup(props,{expose(){},emit:(...args)=>emitted.push(args)}));
  return {state,emitted,timers,async mount(){for(const callback of mounted)await callback();},dispose(){for(const callback of unmounted)callback();scope.stop();}};
}

function liveProtocol() {
  const module={exports:{}};
  const source=readFileSync(new URL('../host/aidiy_live/src/protocol.ts',import.meta.url),'utf8');
  vm.runInNewContext(transformSync(source,{loader:'ts',format:'cjs'}).code,{module,exports:module.exports,setTimeout,clearTimeout});
  return module.exports;
}

async function liveFixture(t,{socketFactory}={}) {
  let apiFailure='',socketFailure='',audioCloses=0,disconnects=0;
  const settings={LIVE_AI_NAME:'freeai_live',LIVE_FREEAI_MODEL:'test-model',LIVE_FREEAI_VOICE:'Zephyr'};
  class Environment {
    host=true;socketUrl='';captureUrl='';
    socket=socketFactory;
    context(){return Promise.resolve({作業フォルダ:{名前:'fixture',パス:'/fixture'},保存モデル設定:settings});}
    async api(path,body){
      if(apiFailure==='all'||(apiFailure==='session'&&body.セッションID))throw Error('モデル取得の試験エラー');
      return {status:'OK',data:{モデル設定:settings,available_models:{live_models:{freeai_live:{'test-model':'試験','other-model':'別モデル'}},live_voices:{freeai_live:{Zephyr:'Zephyr'}}}}};
    }
    async saveModel(value){Object.assign(settings,value);}
    onStop(callback){this.stop=callback;}onFolder(){}onMicrophoneStop(){}ready(){}dispose(){}
  }
  class Connection {
    session='';
    async connect(){if(socketFailure)throw Error(socketFailure);this.session='new-session';}
    disconnect(){disconnects++;this.session='';}send(){return true;}
  }
  const fixture=setupComponent('LivePanel',{
    props:{config:{}},modules:{
      '../transports/live':{LiveEnvironment:Environment},
      '../../host/aidiy_live/src/protocol':socketFactory?liveProtocol():{LiveConnection:Connection,入力レート:()=>16000,音声入力:value=>value,音声操作:(mic,speaker)=>({mic,speaker})},
      '../../host/aidiy_live/src/audio':{LiveAudio:class {async unlock(){}close(){audioCloses++;}mute(){}stop(){}}},
      '../../host/aidiy_live/src/visualizer':{AudioCloud:class {dispose(){}}},
      '../../host/aidiy_live/src/model-catalog':{ライブ選択エラー:()=>''},
      '../../host/aidiy_live/src/microphone-error':{microphoneError:error=>error.message},
      './StatusBar.vue':{},'./TerminalWelcome.vue':{},'./ModalDialog.vue':{},
      '../engines/chat-arrival':{chatArrival:()=>({reset(){},dispose(){},show(){}})},
    },
  });
  t.after(()=>fixture.dispose());await fixture.mount();
  const state=fixture.state;
  state.messages.value=[{role:'user',text:'前の依頼',id:'user'},{role:'assistant',text:'保持する回答',id:'answer'}];
  state.prompt.value='未送信の下書き';state.welcomeVisible.value=false;
  return {...fixture,failAPI:kind=>{apiFailure=kind;},failSocket:message=>{socketFailure=message;},resources:()=>({audioCloses,disconnects})};
}

for(const failure of ['models','socket','sessionModels']){
  test(`Live: モデル再接続の${failure}失敗でも会話・下書きを保持して資源を閉じる`,async t=>{
    const fixture=await liveFixture(t),state=fixture.state;
    state.connected.value=true;state.mic.value=true;
    await state.openModels();state.model.value='other-model';
    const history=JSON.stringify(state.messages.value);
    if(failure==='socket')fixture.failSocket('ソケット接続の試験エラー');
    else fixture.failAPI(failure==='models'?'all':'session');
    await state.applyModel();
    assert.equal(JSON.stringify(state.messages.value),history);
    assert.equal(state.prompt.value,'未送信の下書き');assert.equal(state.welcomeVisible.value,false);
    for(const flag of ['connected','busy','mic','micBusy','changing','modelSaving','picker'])assert.equal(state[flag].value,false,flag);
    assert.match(state.error.value,/試験エラー/);
    assert.equal(state.preferred.value.LIVE_FREEAI_MODEL,'other-model');
    assert.deepEqual(fixture.resources(),{audioCloses:2,disconnects:2});
    await state.newChat();
    assert.equal(state.messages.value.length,0);assert.equal(state.prompt.value,'');assert.equal(state.welcomeVisible.value,true);
  });
}

test('Live: 通常の新規接続失敗は従来どおり初期状態へ戻す',async t=>{
  const fixture=await liveFixture(t),state=fixture.state;fixture.failAPI('all');
  await state.connect();
  assert.equal(state.messages.value.length,0);assert.equal(state.prompt.value,'');
  assert.equal(state.welcomeVisible.value,true);assert.equal(state.busy.value,false);
});

// 接続全体を置き換えず、実際のprotocolが初期化済みソケットの切断を通知する経路を通す。
function interruptedLiveSockets(closedChannel,pendingChannel) {
  const sockets=[];
  class Socket {
    readyState=1;bufferedAmount=0;
    constructor(){sockets.push(this);queueMicrotask(()=>this.onopen?.({}));}
    send(data){
      const packet=JSON.parse(data);if(packet.type!=='connect')return;
      this.channel=packet.ソケット番号;
      if(this.channel===pendingChannel)queueMicrotask(()=>sockets.find(socket=>socket.channel===closedChannel).close());
      else queueMicrotask(()=>this.onmessage?.({data:JSON.stringify({メッセージ識別:'init',セッションID:'new-session'})}));
    }
    close(){if(this.readyState===3)return;this.readyState=3;queueMicrotask(()=>this.onclose?.({}));}
  }
  return {socketFactory:()=>new Socket(),sockets};
}

for(const [closedChannel,pendingChannel] of [['input','0'],['0','audio']]){
  test(`Live: 実protocolの${closedChannel}切断が${pendingChannel}再接続待ちに届いても会話・下書きを保持する`,async t=>{
    const transport=interruptedLiveSockets(closedChannel,pendingChannel);
    const fixture=await liveFixture(t,transport),state=fixture.state;
    state.connected.value=true;state.mic.value=true;
    await state.openModels();state.model.value='other-model';
    const history=JSON.stringify(state.messages.value);
    await state.applyModel();
    assert.equal(JSON.stringify(state.messages.value),history);
    assert.equal(state.prompt.value,'未送信の下書き');assert.equal(state.welcomeVisible.value,false);
    for(const flag of ['connected','busy','mic','micBusy','changing','modelSaving','picker'])assert.equal(state[flag].value,false,flag);
    assert.match(state.error.value,/接続が切れました/);
    assert.equal(state.preferred.value.LIVE_FREEAI_MODEL,'other-model');
    assert.ok(transport.sockets.length>=2);assert.ok(transport.sockets.every(socket=>socket.readyState===3));
    await state.newChat();
    assert.equal(state.messages.value.length,0);assert.equal(state.prompt.value,'');assert.equal(state.welcomeVisible.value,true);
  });
}

test('Live: 実protocolで通常の新規接続中に切断した場合は初期状態へ戻す',async t=>{
  const transport=interruptedLiveSockets('input','0');
  const fixture=await liveFixture(t,transport),state=fixture.state;
  await state.connect();
  assert.equal(state.messages.value.length,0);assert.equal(state.prompt.value,'');
  assert.equal(state.welcomeVisible.value,true);assert.equal(state.busy.value,false);
  assert.ok(transport.sockets.every(socket=>socket.readyState===3));
});

test('Live: モデル再接続成功後には保持方針を解除し、通常の切断処理へ戻る',async t=>{
  const transport=interruptedLiveSockets();
  const fixture=await liveFixture(t,transport),state=fixture.state;
  state.connected.value=true;
  await state.openModels();state.model.value='other-model';await state.applyModel();
  assert.equal(state.connected.value,true);assert.equal(state.prompt.value,'未送信の下書き');
  transport.sockets.find(socket=>socket.channel==='input').close();
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(state.connected.value,false);assert.equal(state.messages.value.length,0);assert.equal(state.prompt.value,'');
  assert.ok(transport.sockets.every(socket=>socket.readyState===3));
});

async function analysisFixture(t) {
  let saved='保存済みの指示',failSave=true,pendingSave,dialogCloses=0,focused='';const requests=[];
  const fixture=setupComponent('FileAnalysisDialog',{
    props:{file:{name:'sample.txt',path:'sample.txt'},root:'/fixture'},
    globals:{fetch:async(url,options)=>{
      requests.push({method:options.method,body:options.body&&JSON.parse(options.body),signal:options.signal});
      if(options.method==='PUT'){
        if(pendingSave)await pendingSave;
        if(failSave)return new Response(JSON.stringify({error:'保存の試験エラー'}),{status:503});
        saved=JSON.parse(options.body).instruction;
        return new Response(JSON.stringify({ok:true}));
      }
      return new Response(JSON.stringify({instruction:saved,result:null,job:null,stale:false}));
    }},
  });
  t.after(()=>fixture.dispose());const state=fixture.state;
  state.dialog.value={close(){dialogCloses++;},showModal(){}};
  state.input.value={focus(){focused='input';}};
  if(state.keepEditingButton)state.keepEditingButton.value={focus(){focused='keepEditing';}};
  await state.load(true);state.instruction.value='失いたくない変更';
  return {...fixture,requests,saves:()=>requests.filter(request=>request.method==='PUT'),saved:()=>saved,focused:()=>focused,dialogCloses:()=>dialogCloses,
    failSave:value=>{failSave=value;},holdSave:()=>{pendingSave=new Promise(resolve=>{fixture.releaseSave=resolve;});return ()=>{fixture.releaseSave();pendingSave=undefined;};}};
}

test('解析: 保存失敗・結果再読込・編集継続では指示を失わず閉じない',async t=>{
  const fixture=await analysisFixture(t),state=fixture.state;
  await state.close();
  assert.match(state.closeError.value,/保存の試験エラー/);assert.equal(state.saving.value,false);
  assert.equal(state.instruction.value,'失いたくない変更');assert.equal(fixture.emitted.length,0);
  assert.equal(fixture.focused(),'keepEditing');assert.equal(fixture.dialogCloses(),0);
  await state.load();
  assert.match(state.closeError.value,/保存の試験エラー/,'結果のポーリングで保存失敗を消さない');
  assert.equal(state.instruction.value,'失いたくない変更');
  await state.keepEditing();
  assert.equal(state.closeError.value,'');assert.equal(state.instruction.value,'失いたくない変更');
  assert.equal(fixture.focused(),'input');assert.equal(fixture.emitted.length,0);assert.equal(fixture.saves().length,1);
  assert.equal(fixture.saved(),'保存済みの指示');
});

test('解析: 保存失敗後の明示破棄は再保存せず一度だけ閉じる',async t=>{
  const fixture=await analysisFixture(t),state=fixture.state;
  await state.close();state.timer=123;fixture.timers.set(123,()=>{});
  state.finishClose();state.finishClose();await state.close();
  assert.deepEqual(fixture.emitted,[['close']]);assert.equal(fixture.dialogCloses(),1);
  assert.equal(fixture.saves().length,1);assert.equal(fixture.saved(),'保存済みの指示');
  assert.equal(state.controller.signal.aborted,true);assert.equal(fixture.timers.has(123),false);
});

test('解析: 保存失敗後の再試行は最新の指示を保存してから閉じる',async t=>{
  const fixture=await analysisFixture(t),state=fixture.state;
  await state.close();fixture.failSave(false);state.instruction.value='再試行前に編集した指示';
  await state.close();
  assert.equal(fixture.saves().length,2);assert.equal(fixture.saved(),'再試行前に編集した指示');
  assert.equal(state.closeError.value,'');assert.equal(state.saving.value,false);
  assert.deepEqual(fixture.emitted,[['close']]);assert.equal(fixture.dialogCloses(),1);
});

test('解析: 保存待ちの連打と破棄は無視し、失敗後は再び操作できる',async t=>{
  const fixture=await analysisFixture(t),state=fixture.state,release=fixture.holdSave();
  const pending=state.close();assert.equal(state.saving.value,true);
  await state.close();state.finishClose();
  assert.equal(fixture.saves().length,1);assert.equal(fixture.emitted.length,0);
  release();await pending;assert.equal(state.saving.value,false);
  assert.equal(state.instruction.value,'失いたくない変更');
  state.finishClose();assert.deepEqual(fixture.emitted,[['close']]);
});

test('解析: 初回読込中に閉じた場合は未取得の指示を上書きしない',async t=>{
  const fixture=await analysisFixture(t),state=fixture.state;state.loading.value=true;
  await state.close();assert.equal(fixture.saves().length,0);assert.deepEqual(fixture.emitted,[['close']]);
});
