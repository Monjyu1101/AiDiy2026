import test from 'node:test';
import assert from 'node:assert/strict';
import {ref} from '../ui/node_modules/vue/index.mjs';
import {CLI状態を作成} from '../ui/src/アプリ起動/CLI状態.mjs';
function fixture(overrides={}){
 const requests=[],confirmations=[],アプリ={フォルダ:ref('/日本語 path & ;'),処理中:ref(''),選択中:ref(false)};
 const state=CLI状態を作成({アプリ,確認:async text=>{confirmations.push(text);return true;},api:async(route,_method,_signal,_format,body)=>{requests.push({route,body});return route==='api/CLI起動'?{対象:[{id:'copilot',名前:'GitHub Copilot CLI',モード:'YOLO',利用可能:true},{id:'grok',名前:'Grok',利用可能:false}]}:{通知:'Term を開きました'};},...overrides});
 return {state,アプリ,requests,confirmations};
}
test('only available CLI entries appear and idle loading cannot launch anything',async()=>{const f=fixture();await f.state.読込();assert.deepEqual(f.state.項目.value.map(x=>x.id),['copilot']);assert.equal(f.requests.length,1);assert.equal(f.confirmations.length,0);});
test('explicit risk confirmation includes chosen project/mode/model default; payload has no model/command',async()=>{
 const f=fixture();await f.state.読込();await f.state.起動('copilot');assert.equal(f.confirmations.length,1);for(const value of ['YOLO','指定なし','ファイルの変更','コマンド実行','サンドボックス','/日本語 path & ;'])assert.ok(f.confirmations[0].includes(value));
 assert.deepEqual(f.requests.at(-1).body,{対象:'copilot',フォルダ:f.アプリ.フォルダ.value,自動承認確認:true});assert.equal(f.state.通知.value,'Term を開きました');assert.equal(f.アプリ.処理中.value,'');
});
test('cancel/no project/offline/unknown/picker busy do not launch',async()=>{
 const f=fixture({確認:async()=>false});await f.state.読込();await f.state.起動('copilot');await f.state.起動('bad');f.アプリ.フォルダ.value='';await f.state.起動('copilot');assert.equal(f.requests.length,1);
 const offline=fixture({接続可能:()=>false});await offline.state.読込();await offline.state.起動('copilot');assert.equal(offline.requests.length,0);
 const busy=fixture();await busy.state.読込();busy.アプリ.選択中.value=true;await busy.state.起動('copilot');assert.equal(busy.requests.length,1);
});
test('repeated clicks lock while confirmation pending; changed project invalidates approval',async()=>{
 let release;const f=fixture({確認:()=>new Promise(resolve=>release=resolve)});await f.state.読込();const one=f.state.起動('copilot');await f.state.起動('copilot');assert.equal(f.アプリ.処理中.value,'cli:copilot');f.アプリ.フォルダ.value='/changed';release(true);await one;assert.equal(f.requests.length,1);assert.equal(f.アプリ.処理中.value,'');
});
test('failed launch is visible and retry remains possible; disconnect discards late catalog',async()=>{
 let calls=0;const f=fixture({api:async()=>{calls++;throw Error('実行ファイルなし');}});f.state.項目.value=[{id:'copilot',名前:'Copilot',モード:'YOLO'}];await f.state.起動('copilot');assert.equal(f.state.失敗.value,true);assert.equal(f.state.通知.value,'実行ファイルなし');await f.state.起動('copilot');assert.equal(calls,2);
 let release;const slow=fixture({api:()=>new Promise(resolve=>release=resolve)});const pending=slow.state.読込();slow.state.切断();release({対象:[{id:'old',利用可能:true}]});await pending;assert.equal(slow.state.項目.value.length,0);
});
