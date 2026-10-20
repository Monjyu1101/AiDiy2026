// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import test from 'node:test';
import assert from 'node:assert/strict';
import {EventEmitter} from 'node:events';
import vm from 'node:vm';
import nativeMove from '../デスクトップ/長押し窓移動.cjs';
const deferred=()=>{let resolve,reject;const promise=new Promise((yes,no)=>{resolve=yes;reject=no;});return{promise,resolve,reject};};
function fixture(kind='viewer',target=()=>Promise.resolve(1),arm=()=>Promise.resolve(true)){
 const contents=new EventEmitter(),window=new EventEmitter(),timers=new Map(),ticks=new Map(),inputs=[],calls=[],sent=[],queries=[];
 let cursor={x:100,y:100},serial=0;
 const emit=(type,extra={})=>{const event={preventDefault(){this.prevented=true;}},mouse={type,x:20,y:30,button:'left',clickCount:1,...extra};contents.emit('before-mouse-event',event,mouse);if(!event.prevented)inputs.push(mouse);return event;};
 Object.assign(contents,{isDestroyed:()=>false,getZoomFactor:()=>1,executeJavaScript:async()=>{},executeJavaScriptInIsolatedWorld:(world,scripts)=>{const action=scripts[0].code.match(/\)\("(install|query|arm|disarm|dispose)",/)[1];queries.push({world,scripts,action});return action==='query'?target():action==='arm'?arm():Promise.resolve(true);},sendInputEvent:input=>{sent.push(input);return emit(input.type,input);},insertCSS:async()=> 'move-css',removeInsertedCSS:async key=>calls.push(['css-remove',key])});
 Object.assign(window,{webContents:contents,isDestroyed:()=>false,isMaximized:()=>false,isFullScreen:()=>false});
 const record={kind,window};
 const dispose=nativeMove.installNativeWindowMove({record,screen:{getCursorScreenPoint:()=>({...cursor})},drag:{forRecord:r=>{assert.equal(r,record);return{begin:()=>{calls.push(['begin']);return'token';},move:()=>{calls.push(['move']);return true;},end:()=>calls.push(['end'])};}},setTimer:(fn,delay)=>{assert.equal(delay,500);timers.set(++serial,fn);return serial;},clearTimer:id=>timers.delete(id),setTick:fn=>{ticks.set(++serial,fn);return serial;},clearTick:id=>ticks.delete(id)});
 return{emit,contents,window,timers,ticks,inputs,calls,sent,queries,dispose,advance:async()=>{for(const fn of [...timers.values()])fn();for(let i=0;i<12;i++)await Promise.resolve();},cursor:value=>cursor=value};
}
test('全パネル: nativeのdown/upを直ちに一度だけ渡し、短押しを再送しない',async()=>{
 for(const kind of ['ide','code','live','term','browser','viewer','explorer','panel-viewer','panel-routes','diag','avatar','discord']){
  const f=fixture(kind);assert.notEqual(f.emit('mouseDown').prevented,true);assert.deepEqual(f.inputs.map(i=>i.type),['mouseDown']);assert.equal(f.calls.length,0);
  assert.notEqual(f.emit('mouseUp').prevented,true);await f.advance();assert.deepEqual(f.inputs.map(i=>i.type),['mouseDown','mouseUp']);assert.equal(f.timers.size,0);assert.deepEqual(f.sent,[]);assert.deepEqual(f.calls,[]);f.dispose();
 }
});
test('背景の長押しだけ移動し、移動後もnative upを渡して次のクリックを妨げない',async()=>{
 for(const kind of ['browser','diag','avatar','discord']){
 const f=fixture(kind);f.emit('mouseDown');f.emit('mouseMove');await f.advance();assert.deepEqual(f.calls,[['begin']]);
 f.cursor({x:-300,y:70});f.emit('mouseMove');assert.ok(f.calls.some(c=>c[0]==='move'));assert.notEqual(f.emit('mouseUp').prevented,true);assert.equal(f.inputs.filter(i=>i.type==='mouseDown').length,1);assert.equal(f.inputs.filter(i=>i.type==='mouseUp').length,1);f.inputs.length=0;assert.equal(f.ticks.size,0);
 f.emit('mouseDown');f.emit('mouseUp');assert.deepEqual(f.inputs.map(i=>i.type),['mouseDown','mouseUp']);f.dispose();
 }
});
test('操作部品では長押しでもnative入力を遮断・再送せず、移動を開始しない',async()=>{
 for(const kind of ['code','live','diag','avatar','discord']){
  const f=fixture(kind,async()=>false);assert.notEqual(f.emit('mouseDown').prevented,true);await f.advance();
  assert.notEqual(f.emit('mouseUp').prevented,true);assert.deepEqual(f.inputs.map(i=>i.type),['mouseDown','mouseUp']);assert.deepEqual(f.sent,[]);assert.deepEqual(f.calls,[]);assert.equal(f.timers.size,0);f.dispose();
 }
});
test('通常の文字選択・スライダーdragとダブルクリックは維持',async()=>{
 const f=fixture();f.emit('mouseDown');f.cursor({x:101,y:100});f.emit('mouseMove',{x:21});f.cursor({x:100,y:100});await f.advance();f.emit('mouseUp',{x:20});
 assert.deepEqual(f.inputs.map(i=>i.type),['mouseDown','mouseMove','mouseUp']);assert.equal(f.calls.length,0);
 f.inputs.length=0;for(const count of [1,2]){f.emit('mouseDown',{clickCount:count});f.emit('mouseUp',{clickCount:count});}
 assert.deepEqual(f.inputs.map(i=>i.clickCount),[1,1,2,2]);f.dispose();
});
test('移動成立後のEsc・フォーカス喪失・破棄・遷移で解除してもnative upを渡す',async()=>{
 for(const cancel of [f=>f.window.emit('blur'),f=>f.contents.emit('before-input-event',{}, {key:'Escape'}),f=>f.contents.emit('did-start-navigation',{},'https://example.org',false,true)]){
  const f=fixture();f.emit('mouseDown');await f.advance();cancel(f);f.emit('mouseUp');assert.equal(f.inputs.filter(i=>i.type==='mouseDown').length,1);assert.equal(f.inputs.filter(i=>i.type==='mouseUp').length,1);assert.equal(f.ticks.size,0);f.dispose();assert.equal(f.contents.listenerCount('before-mouse-event'),0);
 }
 const f=fixture();f.emit('mouseDown');f.contents.emit('destroyed');assert.equal(f.timers.size,0);assert.equal(f.contents.listenerCount('before-mouse-event'),0);
});
test('最大化・全画面・未対応の窓は通常入力をそのまま渡す',()=>{
 for(const mode of ['maximized','fullscreen','unsupported']){
  const f=fixture(mode==='unsupported'?'unknown':'code');f.window.isMaximized=()=>mode==='maximized';f.window.isFullScreen=()=>mode==='fullscreen';
  f.emit('mouseDown');f.emit('mouseUp');assert.equal(f.inputs.length,2);assert.equal(f.timers.size,0);assert.equal(f.queries.filter(q=>q.action!=='install').length,0);assert.equal(f.sent.length,0);f.dispose();
 }
});
test('非同期の対象確認が遅くても500ms未満・解放後・取消後には移動を開始しない',async()=>{
 for(const action of [f=>f.emit('mouseUp'),f=>f.window.emit('blur'),f=>f.contents.emit('before-input-event',{}, {key:'Escape'}),f=>f.contents.emit('did-start-navigation',{},'https://example.org',false,true),f=>f.contents.emit('render-process-gone'),f=>f.contents.emit('dom-ready'),f=>f.emit('mouseLeave'),f=>{f.cursor({x:101,y:100});f.emit('mouseMove');},f=>f.contents.emit('destroyed')]){
  const pending=deferred(),f=fixture('code',()=>pending.promise);f.emit('mouseDown');await f.advance();assert.deepEqual(f.calls,[]);action(f);pending.resolve(1);await f.advance();assert.deepEqual(f.calls,[]);assert.equal(f.timers.size,0);assert.equal(f.ticks.size,0);assert.equal(f.sent.length,0);f.dispose();
 }
 const f=fixture();f.emit('mouseDown');await Promise.resolve();assert.deepEqual(f.calls,[]);f.emit('mouseUp');await f.advance();assert.deepEqual(f.calls,[]);f.dispose();
});
test('対象確認失敗は窓移動だけを取り消し、native入力を妨げない',async()=>{
 for(const target of [()=>{throw Error('frame destroyed');},()=>Promise.reject(Error('navigation')),async()=>undefined]){
  const f=fixture('code',target);f.emit('mouseDown');await f.advance();assert.notEqual(f.emit('mouseUp').prevented,true);assert.deepEqual(f.inputs.map(i=>i.type),['mouseDown','mouseUp']);assert.deepEqual(f.calls,[]);assert.deepEqual(f.sent,[]);f.dispose();
 }
});
test('古い対象確認・別窓の結果は現在の操作に混ざらず、待機中の最大化も移動しない',async()=>{
 const first=deferred(),second=deferred(),pending=[first,second],f=fixture('code',()=>pending.shift().promise),g=fixture('discord',async()=>false);
 f.emit('mouseDown');f.emit('mouseUp');f.emit('mouseDown');g.emit('mouseDown');await f.advance();await g.advance();
 first.resolve(1);await Promise.resolve();assert.deepEqual(f.calls,[]);assert.deepEqual(g.calls,[]);
 f.window.isMaximized=()=>true;second.resolve(1);await f.advance();assert.deepEqual(f.calls,[]);f.emit('mouseUp');g.emit('mouseUp');assert.equal(f.sent.length,0);assert.equal(g.sent.length,0);f.dispose();g.dispose();
});
test('gestureの確認とarmは権限のない隔離worldだけを使い、DOM座標で対象を判定する',async()=>{
 const f=fixture();f.contents.getZoomFactor=()=>1.25;f.emit('mouseDown',{x:25,y:50});await f.advance();
 assert.deepEqual(f.queries.map(q=>q.action),['install','query','arm']);
 for(const query of f.queries){assert.equal(query.world,1004);assert.doesNotMatch(query.scripts[0].code,/ipcRenderer|require\(|fetch\(|postMessage/);}
 assert.match(f.queries[0].scripts[0].code,/eligible\(event.clientX,event.clientY\)/);f.emit('mouseUp');f.dispose();
});
test('armの待機中の解放・別押下・失敗では移動せず、新gestureに古い結果を使わない',async()=>{
 for(const action of [f=>f.emit('mouseUp'),f=>{f.emit('mouseUp');f.emit('mouseDown');},f=>f.window.emit('blur'),f=>f.contents.emit('destroyed')]){
  const arm=deferred(),f=fixture('code',async()=>1,()=>arm.promise);f.emit('mouseDown');await f.advance();assert.deepEqual(f.calls,[]);action(f);arm.resolve(true);for(let i=0;i<12;i++)await Promise.resolve();assert.deepEqual(f.calls,[]);f.dispose();
 }
 for(const arm of [()=>{throw Error('frame destroyed');},()=>Promise.reject(Error('gone')),async()=>false]){
  const f=fixture('code',async()=>1,arm);f.emit('mouseDown');await f.advance();f.emit('mouseUp');assert.deepEqual(f.calls,[]);assert.deepEqual(f.inputs.map(i=>i.type),['mouseDown','mouseUp']);f.dispose();
 }
});
test('native操作部品・ラベル・編集欄・iframe・shadow内の部品を背景移動から除く',()=>{
 const selectors=[];
 const element=(tag,parent=null,extra={})=>({parentElement:parent,isContentEditable:false,matches:query=>{selectors.push(query);return query.split(',').includes(tag);},getRootNode:()=>({}),...extra});
 const allowed=(node,extra={})=>vm.runInNewContext(`(${nativeMove.backgroundMoveTarget.toString()})(10,20)`,{document:{elementFromPoint:()=>node,querySelector:()=>null,querySelectorAll:()=>[],...extra},getComputedStyle:node=>({visibility:node.visibility||'visible'})});
 assert.equal(allowed(null),false);assert.equal(allowed(element('div')),true);
 for(const control of ['select','option','optgroup','datalist','input','textarea','button','a[href]','label','summary','iframe','object','embed','audio[controls]','video[controls]','[role="combobox"]','[role="listbox"]','[role="option"]','.monaco-editor','.xterm','[data-aidiy-no-window-move]']){
  const node=element(control);assert.equal(allowed(node),false,control);assert.equal(allowed(element('span',node)),false,control+'内の子要素');
 }
 assert.equal(allowed(element('div',null,{isContentEditable:true})),false);
 const input=element('input'),host=element('div',null,{shadowRoot:{elementFromPoint:()=>input}});assert.equal(allowed(host),false);
 const button=element('button'),inside=element('span',null,{getRootNode:()=>({host:button})});assert.equal(allowed(inside),false);
 assert.equal(allowed(element('div'),{querySelector:()=>element('select')}),false,'native popup表示中は背景も動かさない');
 for(const tag of ['select','input[list]','[role="combobox"]'])assert.equal(allowed(element('div'),{activeElement:element(tag)}),false,'popup操作中は背景も動かさない');
 assert.equal(allowed(element('div'),{activeElement:{shadowRoot:{activeElement:element('select')}}}),false,'shadow内のselect操作中も動かさない');
 assert.equal(allowed(element('div'),{querySelectorAll:()=>[{getClientRects:()=>[{}]}]}),false,'modal/展開popup表示中は背景も動かさない');
 assert.equal(allowed(element('div'),{querySelectorAll:()=>[{getClientRects:()=>[]}]}),true,'非表示popupは背景を妨げない');
 assert.equal(allowed(element('div'),{querySelectorAll:()=>[{getClientRects:()=>[{}],visibility:'hidden'}]}),true,'visibility hiddenのpopupは背景を妨げない');
 assert.ok(selectors.length>0);
});

function rendererFixture(){
 const listeners=new Map(),events=[],released=[];let allowed=true,dragging=false;
 const target={dispatchEvent(event){events.push(event.type);if(event.type==='pointercancel')dragging=false;},hasPointerCapture:()=>true,releasePointerCapture:id=>released.push(id)};
 const context=vm.createContext({window:{addEventListener(type,fn){if(!listeners.has(type))listeners.set(type,new Set());listeners.get(type).add(fn);},removeEventListener(type,fn){listeners.get(type)?.delete(fn);}},PointerEvent:class{constructor(type,init){Object.assign(this,init,{type,isTrusted:false});}},backgroundTarget:()=>allowed});
 const run=(action,id=null,owner='owner')=>vm.runInContext(`(${nativeMove.rendererMoveGesture.toString()})(${JSON.stringify(action)},${JSON.stringify(owner)},${JSON.stringify(id)},backgroundTarget)`,context);
 const emit=(type,extra={})=>{const event={type,isTrusted:true,button:0,detail:1,pointerId:7,clientX:20,clientY:30,target,preventDefault(){this.prevented=true;},stopImmediatePropagation(){this.stopped=true;},...extra};for(const fn of listeners.get(type)||[])fn(event);events.push(type);return event;};
 const down=()=>{dragging=true;emit('pointerdown');emit('mousedown');};
 run('install');return{run,emit,down,events,released,listeners,target,allow:value=>allowed=value,dragging:()=>dragging};
}
test('renderer: 成立した背景gestureだけをpointercancelし、実upを通してclickだけ抑止',()=>{
 const f=rendererFixture();f.down();const id=f.run('query');assert.ok(id>0);assert.equal(f.run('arm',id),true);
 assert.equal(f.dragging(),false);assert.deepEqual(f.released,[7]);assert.ok(f.events.includes('pointercancel'));
 assert.notEqual(f.emit('pointerup').prevented,true);assert.notEqual(f.emit('mouseup').prevented,true);
 const click=f.emit('click');assert.equal(click.prevented,true);assert.equal(click.stopped,true);
 f.down();f.emit('pointerup');f.emit('mouseup');assert.notEqual(f.emit('click').prevented,true);
});
test('renderer: 解放・移動・新しい押下をまたぐ古いarmは新しいclickを奪わない',()=>{
 for(const cancel of [f=>f.emit('mouseup'),f=>f.emit('mousemove',{clientX:21}),f=>f.emit('pointercancel'),f=>f.down()]){
  const f=rendererFixture();f.down();const old=f.run('query');cancel(f);assert.equal(f.run('arm',old),false);f.emit('mouseup');assert.notEqual(f.emit('click').prevented,true);
 }
 const f=rendererFixture();f.down();const old=f.run('query');f.run('arm',old);f.emit('mouseup');
 assert.notEqual(f.emit('click',{detail:0}).prevented,true,'keyboard clickは抑止しない');
 f.down();f.emit('mouseup');assert.notEqual(f.emit('click').prevented,true,'失われたrelease後でも次の押下は通常操作');
});
test('renderer: controls・途中で開いたpopup・別owner・破棄・未導入はfail closed',()=>{
 const f=rendererFixture();f.allow(false);f.down();assert.equal(f.run('query'),null);assert.equal(f.run('arm',1),false);f.emit('mouseup');assert.notEqual(f.emit('click').prevented,true);assert.equal(f.events.includes('pointercancel'),false);
 f.allow(true);f.down();const id=f.run('query');f.allow(false);assert.equal(f.run('arm',id),false,'長押し中にpopupが開いた場合');
 assert.equal(f.run('arm',id,'wrong-window'),false);assert.equal(f.run('dispose'),true);assert.equal(f.run('query'),false);assert.ok([...f.listeners.values()].every(set=>set.size===0));
});

test('navigation後に同じ連番になっても古いdocument ownerではarmしない',()=>{
 const f=rendererFixture();f.down();const old=f.run('query');f.run('install',null,'new-document');f.down();
 assert.equal(f.run('query',null,'new-document'),old,'連番が一致する条件');assert.equal(f.run('arm',old),false);assert.equal(f.events.includes('pointercancel'),false);f.emit('mouseup');assert.notEqual(f.emit('click').prevented,true);
 const main=fixture();const first=main.queries[0].scripts[0].code;main.contents.emit('dom-ready');assert.notEqual(main.queries[1].scripts[0].code,first,'documentごとにownerを更新');main.dispose();
});

test('隔離world APIが使えない場合でも取り付け・再読込を失敗させず通常入力を渡す',async()=>{
 const f=fixture();delete f.contents.executeJavaScriptInIsolatedWorld;assert.doesNotThrow(()=>f.contents.emit('dom-ready'));f.emit('mouseDown');await f.advance();f.emit('mouseUp');assert.deepEqual(f.calls,[]);assert.deepEqual(f.inputs.map(i=>i.type),['mouseDown','mouseUp']);f.dispose();
});
