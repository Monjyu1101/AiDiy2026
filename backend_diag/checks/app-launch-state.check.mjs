import test from 'node:test';
import assert from 'node:assert/strict';
import {アプリ状態を作成} from '../ui/src/アプリ起動/アプリ状態.mjs';

test('native folder cancel never selects cwd, chosen real folder feeds launch and clear disables it',async()=>{
 const calls=[];let selected=null;
 const state=アプリ状態を作成({picker:async()=>selected,api:async(route,_method,_signal,_format,body)=>{
  calls.push({route,body});return route.endsWith('/フォルダ')?{フォルダ:'/resolved/project'}:{通知:'Code の起動を要求しました。',受付:true};
 }});
 await state.起動('code');assert.equal(calls.length,0);await state.選択();assert.equal(state.フォルダ.value,'');assert.equal(calls.length,0);
 selected='/alias/project';await state.選択();assert.equal(state.フォルダ.value,'/resolved/project');assert.equal(state.選択中.value,false);
 await state.起動('code');assert.deepEqual(calls.at(-1).body,{対象:'code',フォルダ:'/resolved/project'});
 assert.equal(state.結果.value.code.種別,'accepted');state.解除();await state.起動('code');assert.equal(calls.length,2);
});
test('browser folder cancel discards late navigation and never reopens the picker',async()=>{
 let release;const state=アプリ状態を作成({picker:()=>undefined,api:()=>new Promise(resolve=>release=resolve)});
 const selected=state.選択();await Promise.resolve();assert.equal(state.参照中.value,true);
 state.取消();release({フォルダ:'/late',親:'/',子フォルダ:[]});await selected;
 assert.equal(state.一覧.value,null);assert.equal(state.フォルダ.value,'');assert.equal(state.参照中.value,false);assert.equal(state.選択中.value,false);
});
test('pending launch locks repeats and failures allow retry without reporting success',async()=>{
 let release,calls=0;const state=アプリ状態を作成({api:()=>{calls++;return new Promise((resolve,reject)=>release={resolve,reject});}});state.フォルダ.value='/project';
 const one=state.起動('live');await state.起動('live');assert.equal(calls,1);
 release.reject(Error('起動中のタスクを確認できませんでした。'));await one;assert.equal(state.結果.value.live.種別,'error');assert.equal(state.処理中.value,'');
 const two=state.起動('live');release.resolve({起動済み:true,通知:'Live は起動済みです。'});await two;assert.equal(state.結果.value.live.種別,'existing');assert.equal(calls,2);
});
