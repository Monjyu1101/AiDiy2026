// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import vm from 'node:vm';
import { tmpdir } from 'node:os';
import { startTerminal } from '../terminal.mjs';
import { createSpace, ORBIT_PATH_SCALE } from '../src/engines/space.js';
import { createTextWidthCache } from '../src/engines/text-width-cache.js';
const require=createRequire(import.meta.url);
const vue=require('vue'),{parse,compileScript}=require('@vue/compiler-sfc'),{transformSync}=require('esbuild');
const flush=async()=>{for(let n=0;n<12;n++)await Promise.resolve();};

function component(name,{props={},fetcher=async()=>({ok:true,json:async()=>({active:true})})}={}){
  const {descriptor}=parse(readFileSync(new URL(`../src/${name}.vue`,import.meta.url),'utf8'));
  const script=compileScript(descriptor,{id:name,genDefaultAs:'component'});
  const {code}=transformSync(`${script.content}\nmodule.exports=component;`,{format:'cjs'});
  const mounted=[],unmounted=[],timers=new Map(),document=new EventTarget(),window=new EventTarget();
  document.hidden=false;let id=0;
  const module={exports:{}};
  vm.runInNewContext(code,{
    module,document,window,fetch:fetcher,AbortSignal,AbortController,Date,location:{hash:''},
    setInterval:(callback,ms)=>{timers.set(++id,{callback,ms});return id;},clearInterval:key=>timers.delete(key),
    require:id=>id==='vue'?{...vue,provide(){},onMounted:callback=>mounted.push(callback),onBeforeUnmount:callback=>unmounted.push(callback)}:{},
  });
  const reactive=vue.reactive(props),scope=vue.effectScope();
  const state=scope.run(()=>module.exports.setup(reactive,{expose(){}}));
  return {state,timers,document,props:reactive,async mount(){for(const callback of mounted)await callback();},dispose(){for(const callback of unmounted)callback();scope.stop();}};
}

test('IDE: 初回即時・以後10秒の状態取得、手動開始は待たず、破棄中の初回応答でタイマーを残さない',async()=>{
  const calls=[];
  const fixture=component('App',{props:{config:{kind:'ide'}},fetcher:async(url)=>{calls.push(url);return{ok:true,json:async()=>({active:true,startedAt:1,mode:'online'})};}});
  try{
    await fixture.mount();assert.deepEqual(calls,['/api/connection']);
    assert.deepEqual([...fixture.timers.values()].map(timer=>timer.ms),[10000]);
    await fixture.state.start('connect');assert.equal(calls.at(-1),'/api/connection/connect');
  }finally{fixture.dispose();}
  assert.equal(fixture.timers.size,0);
  let release;
  const delayed=component('App',{props:{config:{kind:'ide'}},fetcher:()=>new Promise(resolve=>{release=resolve;})});
  const mounting=delayed.mount();delayed.dispose();release({ok:true,json:async()=>({active:true})});await mounting;
  assert.equal(delayed.timers.size,0);
});

test('ピン留めビューア: 10秒間隔、遅い応答を重ねず、閉じた後の応答を捨てる',async()=>{
  let release,calls=0,signal;
  const fixture=component('components/ViewerWindow',{props:{path:'file.txt'},fetcher:(_url,options)=>{calls++;signal=options.signal;return new Promise(resolve=>{release=resolve;});}});
  await fixture.mount();const [timer]=fixture.timers.values();assert.equal(timer.ms,10000);assert.equal(calls,1);
  await timer.callback();assert.equal(calls,1);
  release({ok:true,json:async()=>({active:true,connected:true})});await flush();assert.equal(fixture.state.state.value.active,true);
  const pending=timer.callback();assert.equal(calls,2);fixture.dispose();assert.equal(signal.aborted,true);
  release({ok:true,json:async()=>({active:false})});await pending;assert.equal(fixture.state.state.value.active,true);
  assert.equal(fixture.timers.size,0);
});

test('Term: toolsの初回確認は即時、既定10秒、遅い確認は重複せず終了で止まる',async t=>{
  t.mock.timers.enable({apis:['setInterval']});let calls=0,release;
  const app=await startTerminal(tmpdir(),{spawnTerminal(){throw Error('PTYを起動しない');},checkTools:()=>{calls++;return new Promise(resolve=>{release=resolve;});}});
  try{
    assert.equal(calls,1);release(true);await flush();
    t.mock.timers.tick(9999);assert.equal(calls,1);t.mock.timers.tick(1);assert.equal(calls,2);
    t.mock.timers.tick(10000);assert.equal(calls,2);release(true);await flush();
    t.mock.timers.tick(10000);assert.equal(calls,3);
  }finally{await app.close();release?.(true);await flush();}
  t.mock.timers.tick(30000);assert.equal(calls,3);
});

test('接続バー: 未接続・非表示は20Hzタイマー0個、表示復帰は時刻同期して1個だけ再開',async()=>{
  const fixture=component('components/StatusBar',{props:{clockPulse:true,connected:false,mode:'online'}});
  await fixture.mount();assert.equal(fixture.timers.size,0);
  fixture.props.connected=true;await vue.nextTick();assert.equal(fixture.timers.size,1);assert.equal([...fixture.timers.values()][0].ms,50);
  fixture.document.hidden=true;fixture.document.dispatchEvent(new Event('visibilitychange'));assert.equal(fixture.timers.size,0);
  fixture.document.hidden=false;fixture.document.dispatchEvent(new Event('visibilitychange'));assert.equal(fixture.timers.size,1);
  fixture.document.dispatchEvent(new Event('visibilitychange'));assert.equal(fixture.timers.size,1);
  fixture.props.connected=false;await vue.nextTick();assert.equal(fixture.timers.size,0);
  fixture.props.mode='offline';await vue.nextTick();assert.equal(fixture.timers.size,1);
  fixture.dispose();assert.equal(fixture.timers.size,0);
  fixture.document.dispatchEvent(new Event('visibilitychange'));assert.equal(fixture.timers.size,0);
});

test('Canvas文字幅: 同一ラベル600フレームを1回の計測にまとめ、フォント変更・明示無効化で再計測',t=>{
  let calls=0;const context={font:'12px sans-serif',measureText:text=>{calls++;return{width:text.length*6};}};
  const cache=createTextWidthCache(context);
  for(let n=0;n<600;n++)assert.equal(cache.measure('日本語.txt'),42);
  assert.equal(calls,1);t.diagnostic('同一ラベルの600回の幅取得: 実measureTextは1回（従来600回）。CPU使用率の計測ではない。');
  context.font='14px sans-serif';cache.measure('日本語.txt');assert.equal(calls,2);
  cache.clear();cache.measure('日本語.txt');assert.equal(calls,3);
});

test('IDE描画: 非表示ではフレーム/DOM計測を止め、復帰・再非表示・破棄でもループは増殖しない',async t=>{
  const old=new Map();let frameId=0,clock=0,layoutCalls=0;
  const frames=new Map(),window=new EventTarget(),document=new EventTarget();
  Object.assign(window,{devicePixelRatio:1,requestAnimationFrame:callback=>{frames.set(++frameId,callback);return frameId;},cancelAnimationFrame:id=>frames.delete(id)});
  const context=new Proxy({font:'',createRadialGradient:()=>({addColorStop(){}}),measureText:text=>({width:text.length*6})},{get:(object,key)=>key in object?object[key]:()=>{}});
  const canvas=new EventTarget();canvas.getContext=()=>context;canvas.classList={add(){},remove(){}};
  document.hidden=false;document.createElement=()=>({getContext:()=>context});
  for(const [key,value] of Object.entries({window,document,innerWidth:1280,innerHeight:800})){old.set(key,Object.getOwnPropertyDescriptor(globalThis,key));Object.defineProperty(globalThis,key,{configurable:true,writable:true,value});}
  t.mock.method(performance,'now',()=>clock);
  let engine;
  try{
    engine=createSpace(canvas,{tooltip:{}},{layout:()=>{layoutCalls++;return{};}});
    const frame=()=>{clock+=1000/60;const callbacks=[...frames.values()];frames.clear();for(const callback of callbacks)callback(clock);};
    for(let n=0;n<60;n++)frame();assert.equal(layoutCalls,60);assert.equal(frames.size,1);
    document.hidden=true;document.dispatchEvent(new Event('visibilitychange'));assert.equal(frames.size,0);
    for(let n=0;n<600;n++)frame();assert.equal(layoutCalls,60);
    document.hidden=false;document.dispatchEvent(new Event('visibilitychange'));document.dispatchEvent(new Event('visibilitychange'));assert.equal(frames.size,1);
    frame();assert.equal(layoutCalls,61);assert.equal(frames.size,1);
    document.hidden=true;document.dispatchEvent(new Event('visibilitychange'));assert.equal(frames.size,0);
    document.hidden=false;document.dispatchEvent(new Event('visibilitychange'));engine.dispose();assert.equal(frames.size,0);
    document.dispatchEvent(new Event('visibilitychange'));assert.equal(frames.size,0);
    t.diagnostic('非表示の600フレーム相当: Canvasフレーム0回・layout取得0回。表示復帰後は1ループ。');
  }finally{engine?.dispose();for(const [key,descriptor] of old)if(descriptor)Object.defineProperty(globalThis,key,descriptor);else delete globalThis[key];}
});

test('軌道案内線は元軌道の90%を描画し、船の飛行座標を変更しない',()=>{
  assert.equal(ORBIT_PATH_SCALE,.9);
  const point={x:100,y:-200,z:300};assert.deepEqual(Object.values(point).map(value=>value*ORBIT_PATH_SCALE),[90,-180,270]);
  assert.deepEqual(point,{x:100,y:-200,z:300});
  const source=readFileSync(new URL('../src/engines/space.js',import.meta.url),'utf8');
  assert.match(source,/project\(point\.x\*ORBIT_PATH_SCALE,point\.y\*ORBIT_PATH_SCALE,point\.z\*ORBIT_PATH_SCALE\)/);
});
