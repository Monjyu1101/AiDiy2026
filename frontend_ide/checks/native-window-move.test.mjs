// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import test from 'node:test';
import assert from 'node:assert/strict';
import {EventEmitter} from 'node:events';
import nativeMove from '../デスクトップ/長押し窓移動.cjs';
function fixture(kind='viewer'){
 const contents=new EventEmitter(),window=new EventEmitter(),timers=new Map(),ticks=new Map(),inputs=[],calls=[];
 let cursor={x:100,y:100},serial=0;
 const emit=(type,extra={})=>{const event={preventDefault(){this.prevented=true;}},mouse={type,x:20,y:30,button:'left',clickCount:1,...extra};contents.emit('before-mouse-event',event,mouse);if(!event.prevented)inputs.push(mouse);return event;};
 Object.assign(contents,{isDestroyed:()=>false,getZoomFactor:()=>1,executeJavaScript:async()=>{},sendInputEvent:input=>emit(input.type,input),insertCSS:async()=> 'move-css',removeInsertedCSS:async key=>calls.push(['css-remove',key])});
 Object.assign(window,{webContents:contents,isDestroyed:()=>false,isMaximized:()=>false,isFullScreen:()=>false});
 const record={kind,window};
 const dispose=nativeMove.installNativeWindowMove({record,screen:{getCursorScreenPoint:()=>({...cursor})},drag:{forRecord:r=>{assert.equal(r,record);return{begin:()=>{calls.push(['begin']);return'token';},move:()=>{calls.push(['move']);return true;},end:()=>calls.push(['end'])};}},setTimer:(fn,delay)=>{assert.equal(delay,500);timers.set(++serial,fn);return serial;},clearTimer:id=>timers.delete(id),setTick:fn=>{ticks.set(++serial,fn);return serial;},clearTick:id=>ticks.delete(id)});
 return{emit,contents,window,timers,ticks,inputs,calls,dispose,advance:async()=>{for(const fn of [...timers.values()])fn();await Promise.resolve();},cursor:value=>cursor=value};
}
test('全パネル: 押下で選択せず、短押しを離した時だけdown/upを一度渡す',()=>{
 for(const kind of ['ide','code','live','term','browser','viewer','explorer','panel-viewer','panel-routes']){
  const f=fixture(kind);assert.equal(f.emit('mouseDown').prevented,true);assert.equal(f.inputs.length,0);assert.equal(f.calls.length,0);
  assert.equal(f.emit('mouseUp').prevented,true);assert.deepEqual(f.inputs.map(i=>i.type),['mouseDown','mouseUp']);assert.equal(f.timers.size,0);f.dispose();
 }
});
test('長押し移動: button/linkの押下・クリック・upをページへ流さず、解除後の次のクリックは有効',async()=>{
 const f=fixture('browser');f.emit('mouseDown');f.emit('mouseMove');await f.advance();assert.deepEqual(f.calls,[['begin']]);
 f.cursor({x:-300,y:70});f.emit('mouseMove');assert.ok(f.calls.some(c=>c[0]==='move'));f.emit('mouseUp');assert.ok(f.inputs.every(i=>i.type==='mouseMove'));f.inputs.length=0;assert.equal(f.ticks.size,0);
 f.emit('mouseDown');f.emit('mouseUp');assert.deepEqual(f.inputs.map(i=>i.type),['mouseDown','mouseUp']);f.dispose();
});
test('通常の文字選択・スライダーdragとダブルクリックは維持',async()=>{
 const f=fixture();f.emit('mouseDown');f.cursor({x:101,y:100});f.emit('mouseMove',{x:21});f.cursor({x:100,y:100});await f.advance();f.emit('mouseUp',{x:20});
 assert.deepEqual(f.inputs.map(i=>i.type),['mouseDown','mouseMove','mouseUp']);assert.equal(f.calls.length,0);
 f.inputs.length=0;for(const count of [1,2]){f.emit('mouseDown',{clickCount:count});f.emit('mouseUp',{clickCount:count});}
 assert.deepEqual(f.inputs.map(i=>i.clickCount),[1,1,2,2]);f.dispose();
});
test('Esc・フォーカス喪失・破棄・遷移で解除し、離した時に選択を起こさない',async()=>{
 for(const cancel of [f=>f.window.emit('blur'),f=>f.contents.emit('before-input-event',{}, {key:'Escape'}),f=>f.contents.emit('did-start-navigation',{},'https://example.org',false,true)]){
  const f=fixture();f.emit('mouseDown');await f.advance();cancel(f);f.emit('mouseUp');assert.ok(f.inputs.every(i=>i.type==='mouseMove'));assert.equal(f.ticks.size,0);f.dispose();assert.equal(f.contents.listenerCount('before-mouse-event'),0);
 }
 const f=fixture();f.emit('mouseDown');f.contents.emit('destroyed');assert.equal(f.timers.size,0);assert.equal(f.contents.listenerCount('before-mouse-event'),0);
});
test('最大化中は通常入力をそのまま渡す',()=>{
 const g=fixture();g.window.isMaximized=()=>true;g.emit('mouseDown');assert.equal(g.inputs.length,1);assert.equal(g.timers.size,0);g.dispose();
});
