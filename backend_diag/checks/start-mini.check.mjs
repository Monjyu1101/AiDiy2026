import test from 'node:test';
import assert from 'node:assert/strict';
import {setTimeout as delay} from 'node:timers/promises';
import miniWindow from '../起動/ミニ表示.cjs';
import {起動ミニ表示を作成} from '../ui/src/ウィンドウ/起動ミニ表示.mjs';
import {起動状態を作成} from '../ui/src/起動/起動状態.mjs';

function fakeWindow(maximized=false){
 const window={bounds:{x:140,y:100,width:1160,height:820},minimum:[420,320],maximized,maximizable:true,
  isDestroyed(){return !!this.destroyed;},getNormalBounds(){return {...this.bounds};},getMinimumSize(){return [...this.minimum];},isMaximized(){return this.maximized;},isMaximizable(){return this.maximizable;},
  unmaximize(){this.maximized=false;},maximize(){this.maximized=true;},setMinimumSize(...value){this.minimum=value;},setMaximizable(value){this.maximizable=value;},setBounds(value){this.bounds={...value};}};
 return window;
}
test('mini window has fixed dimensions and restores original bounds and minimum',()=>{
 const window=fakeWindow(),controller=miniWindow.ミニ表示を作成(window),original=structuredClone(window.bounds);
 assert.equal(controller.set(true),true);assert.equal(controller.active,true);assert.deepEqual(window.bounds,{...original,width:340,height:320});assert.deepEqual(window.minimum,[300,280]);assert.equal(window.maximizable,false);
 controller.set(true);controller.set(false);assert.deepEqual(window.bounds,original);assert.deepEqual(window.minimum,[420,320]);assert.equal(window.maximizable,true);assert.equal(controller.active,false);
});
test('maximized windows restore their normal bounds and maximized state',()=>{
 const window=fakeWindow(true),controller=miniWindow.ミニ表示を作成(window);controller.set(true);assert.equal(window.maximized,false);controller.set(false);assert.equal(window.maximized,true);assert.equal(window.bounds.width,1160);
});
test('invalid requests and destroyed windows cannot change bounds',()=>{
 const window=fakeWindow(),controller=miniWindow.ミニ表示を作成(window);assert.equal(controller.set({width:999}),false);assert.equal(window.bounds.width,1160);window.destroyed=true;assert.equal(controller.set(true),false);
});
test('mini view can be entered only from the connected startup screen',async()=>{
 const calls=[];let allowed=false;const state=起動ミニ表示を作成({利用可能:()=>allowed,切替:async value=>{calls.push(value);return true;}});
 await state.変更(true);assert.equal(state.表示中.value,false);assert.deepEqual(calls,[]);
 allowed=true;await state.変更(true);assert.equal(state.表示中.value,true);await state.変更(false);assert.equal(state.表示中.value,false);assert.deepEqual(calls,[true,false]);
});
test('leaving startup during a pending native resize restores the full window',async()=>{
 let release,allowed=true;const calls=[];const state=起動ミニ表示を作成({利用可能:()=>allowed,切替:value=>{calls.push(value);return value?new Promise(resolve=>release=resolve):Promise.resolve(true);}});
 const pending=state.変更(true);allowed=false;await state.変更(false);release(true);await pending;assert.equal(state.表示中.value,false);assert.equal(state.切替中.value,false);assert.deepEqual(calls,[true,false]);
});
test('failed native switch keeps UI in the current mode and exposes a message',async()=>{
 const state=起動ミニ表示を作成({利用可能:()=>true,切替:async()=>false});assert.equal(await state.変更(true),false);assert.equal(state.表示中.value,false);assert.ok(state.エラー.value);
});
test('mini polling refreshes statuses without reading logs or mutating services',async t=>{
 const calls=[],state=起動状態を作成({api:async route=>{calls.push(route);return route==='api/起動'?{対象:[{id:'core',名前:'Core',状態:'稼働中',設定:{起動対象:true}}],実行中:false}: {ログ:'fixture',位置:7};}});
 t.after(()=>state.終了());state.表示(true,false);await delay(30);state.表示(false);
 assert.equal(state.項目.value[0].状態,'稼働中');assert.ok(calls.length);assert.ok(calls.every(route=>route==='api/起動'));
 state.表示(true,true);await delay(30);state.表示(false);assert.ok(calls.includes('api/起動/ログ'));assert.ok(!calls.some(route=>/設定|再起動|停止/.test(route)));
});
