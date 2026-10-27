import test from 'node:test';
import assert from 'node:assert/strict';
import {setImmediate as flush} from 'node:timers/promises';
import {readFile} from 'node:fs/promises';
import {起動状態を作成} from '../ui/src/起動/起動状態.mjs';
const progress=(id,kind='start',state='running',message='Tools を起動しています。')=>({実行ID:id,種別:kind,状態:state,通知:message});
function fixture(t){
 const data={対象:[{id:'tools',名前:'Tools',状態:'未起動',設定:{起動対象:true}}],実行中:false,一括停止中:false,一括進捗:null};
 const calls=[],timers=[];let handler=async()=>({受理:true}),portError=false;
 const state=起動状態を作成({setTimer:(fn,ms)=>{timers.push({fn,ms});return timers.length;},clearTimer:()=>{},api:async(route,method,signal)=>{
  calls.push(route);
  if(route==='api/起動')return structuredClone(data);
  if(route==='api/起動/ポート'){if(portError)throw Error('ポート確認失敗');return {対象:[{id:'tools',開放:false}]};}
  if(route==='api/起動/ログ')return {ログ:'',位置:0};
  return handler(route,signal);
 }});
 t.after(()=>state.終了());
 return {state,data,calls,timers,setHandler:fn=>handler=fn,failPorts:()=>portError=true,async refresh(logs=false){state.表示(true,logs);await flush();await flush();}};
}
test('auto progress is visible off-tab without log polling, and completion can be dismissed until next run',async t=>{
 const f=fixture(t);f.data.実行中=true;f.data.一括進捗=progress('auto');await f.refresh();
 assert.equal(f.state.進捗表示.value.実行ID,'auto');assert.equal(f.calls.includes('api/起動/ログ'),false);assert.equal(f.timers.at(-1).ms,800);
 f.state.進捗を閉じる();assert.ok(f.state.進捗表示.value,'進行中は閉じない');
 f.data.実行中=false;f.data.一括進捗=progress('auto','start','done','起動処理が完了しました。');await f.refresh();
 f.state.進捗を閉じる();await f.refresh();assert.equal(f.state.進捗表示.value,null);
 f.data.一括進捗=progress('next','stop');await f.refresh();assert.equal(f.state.進捗表示.value.種別,'stop');
});
test('manual batch shows acceptance immediately, rejects repeated clicks, survives tab changes and follows server result',async t=>{
 const f=fixture(t);await f.refresh(true);let release;
 f.setHandler(()=>new Promise(resolve=>{release=resolve;}));const first=f.state.一括操作();
 assert.equal(f.state.進捗表示.value.種別,'start');assert.equal(f.state.進捗表示.value.状態,'running');
 await f.state.一括操作();assert.equal(f.calls.filter(x=>x==='api/起動/再起動').length,1);
 await f.refresh(false);assert.match(f.state.進捗表示.value.通知,/受け付け/);
 f.data.一括進捗=progress('accepted');f.data.実行中=true;release({受理:true});assert.equal(await first,'start');await flush();
 assert.equal(f.state.進捗表示.value.実行ID,'accepted');
 f.data.実行中=false;f.data.一括進捗=progress('accepted','start','error','起動失敗');await f.refresh();
 assert.equal(f.state.進捗表示.value.状態,'error');
});
test('force stop progress replaces running start and request failure remains visible across polling',async t=>{
 const f=fixture(t);f.data.実行中=true;f.data.一括進捗=progress('start');await f.refresh();
 f.setHandler(async()=>{throw Error('停止を受理できません');});await f.state.一括操作();
 assert.equal(f.state.進捗表示.value.種別,'stop');assert.equal(f.state.進捗表示.value.状態,'error');
 await f.refresh();assert.match(f.state.進捗表示.value.通知,/受理できません/);
 f.data.一括進捗=progress('stop','stop');f.data.一括停止中=true;await f.refresh();assert.equal(f.state.進捗表示.value.実行ID,'stop');
 f.data.一括進捗=progress('stop','stop','done','すべて停止しました。');f.data.一括停止中=false;f.data.実行中=false;await f.refresh();assert.equal(f.state.進捗表示.value.状態,'done');
});
test('disconnect/unmount discards pending responses; progress is available even when port checks fail',async t=>{
 const f=fixture(t);await f.refresh();let release;f.setHandler(()=>new Promise(resolve=>{release=resolve;}));
 const work=f.state.一括操作();f.state.終了();release({受理:true});await work;
 assert.equal(f.state.進捗表示.value,null);assert.equal(f.state.処理中.value,false);
 f.data.一括進捗=progress('auto');f.failPorts();await f.refresh();
 assert.equal(f.state.進捗表示.value.実行ID,'auto');assert.equal(f.state.更新失敗.value,true);
});
test('dialog is a nonmodal in-flow region, shared outside tabs and compact views without navigation locks',async()=>{
 const text=await readFile(new URL('../ui/src/起動/一括進捗表示.vue',import.meta.url),'utf8');
 const css=await readFile(new URL('../ui/src/起動/一括進捗表示.css',import.meta.url),'utf8');
 const app=await readFile(new URL('../ui/src/App.vue',import.meta.url),'utf8');
 assert.match(text,/role="status" aria-live="polite"/);assert.doesNotMatch(text,/aria-modal|showModal|autofocus|\.focus\(/);
 assert.doesNotMatch(css,/position\s*:\s*(fixed|absolute)|inset\s*:\s*0/);
 assert.match(app,/起動\.表示\(online,value==='start'&&!mini\)/);
 assert.match(app,/v-if="connected&&!ミニ表示" :is="一括進捗表示"/);
 const nav=app.match(/<nav[\s\S]*?<\/nav>/)[0];assert.doesNotMatch(nav,/<nav[^>]*(?:inert|disabled)/);
 assert.doesNotMatch(app,/changeTab\(value\)\{[^}]*進捗/);
});

test('progress component renders pending, stop, completion and error text with a close button only after finishing',async()=>{
 const {createRequire}=await import('node:module');const require=createRequire(import.meta.url);
 const {render}=require('./ui-components.cjs');
 const state={進捗表示:{value:progress('run')},更新失敗:{value:false},進捗を閉じる(){}};
 let html=await render('起動/一括進捗表示.vue',{state});
 assert.match(html,/一括起動中/);assert.match(html,/Tools を起動しています/);assert.doesNotMatch(html,/<button/);
 state.進捗表示.value=progress('stop','stop','running','Web を停止しています。');
 html=await render('起動/一括進捗表示.vue',{state,compact:true});assert.match(html,/強制停止中/);assert.match(html,/Web を停止/);
 state.進捗表示.value=progress('stop','stop','error','停止できませんでした。');
 html=await render('起動/一括進捗表示.vue',{state});assert.match(html,/停止できません/);assert.match(html,/進行状況を閉じる/);
 state.進捗表示.value=progress('done','start','done','起動処理が完了しました。');
 html=await render('起動/一括進捗表示.vue',{state});assert.match(html,/一括起動完了/);assert.match(html,/閉じる/);
});
