// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {ref,computed} from 'vue';
const source=readFileSync(new URL('../src/components/開発スペース/Navigationパネル.vue',import.meta.url),'utf8').split('<script setup>')[1].split('</script>')[0].replace(/^import .*;\n/gm,'');
function fixture(){
 const calls=[],pending=[],timers=new Map();let serial=0;
 const api=vm.runInNewContext(source+`;({navigate,refresh,selectHistory,goal,recommendedPrompt,nextItem,copy,panel,busy,job,error,visible,availability,result,overall})`,{
  ref,computed,watch(){},onMounted(){},onBeforeUnmount(){},nextTick:async()=>{},defineProps:()=>({instance:'navi-1',standalone:false}),defineEmits:()=>()=>{},window:{},DEFAULT_NAVIGATION_GOAL:'目標',AbortController,AbortSignal,
  setTimeout:fn=>{timers.set(++serial,fn);return serial;},clearTimeout:id=>timers.delete(id),
  fetch:(url,options)=>{calls.push(options.method);return new Promise((resolve,reject)=>pending.push({resolve,reject}));},
 });
 api.visible.value=true;api.availability.value={available:true};
 const settle=async()=>{for(let n=0;n<15;n++)await Promise.resolve();};
 const answer=async(data)=>{pending.shift().resolve({ok:true,json:async()=>data});await settle();};
 return {api,calls,pending,timers,settle,answer};
}
const state=job=>({result:null,job,availability:{available:true},selection:{provider:'aidiy_hermes',model:'auto'}});
test('開始応答を失っても状態確認を再開し、確認前・実行中の再送を防止する',async()=>{
 const f=fixture();const request=f.api.navigate();assert.deepEqual(f.calls,['POST']);
 f.pending.shift().reject(Error('response lost'));await request;await f.settle();
 assert.deepEqual(f.calls,['POST','GET']);assert.equal(f.api.busy.value,true);
 await f.api.navigate();assert.deepEqual(f.calls,['POST','GET']);
 await f.answer(state({id:'accepted',status:'running'}));assert.equal(f.api.busy.value,true);assert.equal(f.timers.size,1);
 await f.api.navigate();assert.equal(f.calls.filter(x=>x==='POST').length,1);
 const poll=[...f.timers.values()][0];f.timers.clear();void poll();await f.answer(state({id:'accepted',status:'complete'}));
 assert.equal(f.api.busy.value,false);assert.equal(f.api.job.value.status,'complete');assert.equal(f.timers.size,1);
});
test('状態取得も失敗した場合は再送禁止のまま定期確認し、未受理確認後だけ再試行できる',async()=>{
 const f=fixture();const request=f.api.navigate();f.pending.shift().reject(Error('POST failed'));await request;
 f.pending.shift().reject(Error('GET failed'));await f.settle();assert.equal(f.api.busy.value,true);assert.equal(f.timers.size,1);
 await f.api.navigate();assert.equal(f.calls.filter(x=>x==='POST').length,1);
 const poll=[...f.timers.values()][0];f.timers.clear();void poll();await f.answer(state(null));
 assert.equal(f.api.busy.value,false);
 const retry=f.api.navigate();assert.equal(f.calls.filter(x=>x==='POST').length,2);
 await f.answer({job:{id:'retry',status:'running'}});await retry;await f.answer(state({id:'retry',status:'running'}));
 assert.equal(f.api.busy.value,true);assert.equal(f.timers.size,1);
});

test('総合評価はAIの値・根拠を直接表示し、等分平均や項目からの再計算を行わない',()=>{
 const {api}=fixture();
 api.result.value={schemaVersion:3,items:[{progress:100,weight:90},{progress:0,weight:10}],overall:{progress:90,reason:'主要作業の比率90%を完了'}};
 assert.equal(api.overall.value.progress,90);assert.equal(api.overall.value.reason,'主要作業の比率90%を完了');
 // API検証済み値が画面の唯一の情報源。画面側では再計算しない。
 api.result.value.overall.progress=73;assert.equal(api.overall.value.progress,73);
 api.result.value.overall={progress:0,reason:'未着手を確認'};assert.equal(api.overall.value.progress,0);
 delete api.result.value.overall;assert.equal(api.overall.value,undefined);
 api.result.value=null;assert.equal(api.overall.value,undefined);
 assert.doesNotMatch(source,/Math\.round|items\.reduce/);
});


test('旧記録の取得失敗後も新規操作で即座に実行可能状態と既定目標へ戻る',async()=>{
 const f=fixture();f.api.availability.value={available:false,reason:'実行環境を確認しています…'};f.api.goal.value='旧目標';
 const refresh=f.api.refresh();
 f.pending.shift().resolve({ok:false,json:async()=>({error:'旧形式です。「＋ 新規」で記録を切り替えてから「ナビ」で再作成してください。'})});
 await refresh;assert.match(f.api.error.value,/旧形式/);assert.equal(f.api.availability.value.available,false);
 const fresh=f.api.selectHistory();assert.deepEqual(f.calls,['GET','POST']);
 await f.answer(state(null));await fresh;
 assert.equal(f.api.goal.value,'目標');assert.equal(f.api.result.value,null);assert.equal(f.api.job.value,null);assert.equal(f.api.error.value,'');
 assert.equal(f.api.availability.value.available,true);assert.equal(f.api.busy.value,false);
 // 定期GETを実行する前にナビを送信できることを確認する。
 const navigate=f.api.navigate();assert.deepEqual(f.calls,['GET','POST','POST']);
 await f.answer({job:{id:'recreated',status:'running'}});await navigate;await f.answer(state({id:'recreated',status:'running'}));
 assert.equal(f.api.busy.value,true);
});


for(const [name,result] of [['総合null',{schemaVersion:3,items:[{progress:0}],overall:{progress:null}}],['総合欠損',{schemaVersion:3,items:[{progress:0}]}],['項目null',{schemaVersion:3,items:[{progress:null}],overall:{progress:0}}],['旧形式',{items:[{progress:0}],overall:{progress:0}}]])test('旧APIや不正応答を数値のない成功表示へ流さない: '+name,async()=>{
 const f=fixture(),saved={schemaVersion:3,items:[{progress:25}],overall:{progress:25}};f.api.result.value=saved;
 const refresh=f.api.refresh();await f.answer({...state(null),result});await refresh;assert.deepEqual(f.api.result.value,saved);assert.match(f.api.error.value,/数値評価/);
 const select=f.api.selectHistory('old');await f.answer({...state(null),result});await select;assert.deepEqual(f.api.result.value,saved);assert.match(f.api.error.value,/数値評価/);
});
test('初回の不正API応答を0%へ補完せず明示的に拒否する',async()=>{
 const f=fixture();const refresh=f.api.refresh();await f.answer({...state(null),result:{overall:{progress:null}}});await refresh;assert.equal(f.api.result.value,null);assert.match(f.api.error.value,/数値評価/);
});

test('完了応答の評価が不正でも実行中ロックを解放し新規作成で復帰できる',async()=>{
 const f=fixture();f.api.job.value={id:'old',status:'running'};assert.equal(f.api.busy.value,true);
 const refresh=f.api.refresh();await f.answer({...state({id:'old',status:'complete'}),result:{schemaVersion:3,items:[{progress:0}],overall:{progress:null}}});await refresh;
 assert.match(f.api.error.value,/数値評価/);assert.equal(f.api.busy.value,false);
 const fresh=f.api.selectHistory();await f.answer(state(null));await fresh;assert.equal(f.api.result.value,null);assert.equal(f.api.error.value,'');assert.equal(f.api.busy.value,false);
});

test('AI生成本文は入力編集で変わらず、履歴・コピーでも加筆しない',async()=>{
 const f=fixture();assert.equal(f.api.recommendedPrompt.value,'');
 f.api.result.value={schemaVersion:3,goal:'保存済みの目標',items:[{id:'1',name:'最初の項目',progress:0}],overall:{progress:0},nextItemId:'1',nextPrompt:'今回の目標: 保存済みの意図\n対処しようとしている内容: 未確認の表示\n今回の作業: <確認>を行ってください。  '};
 f.api.goal.value='編集中の別目標';assert.equal(f.api.recommendedPrompt.value,'今回の目標: 保存済みの意図\n対処しようとしている内容: 未確認の表示\n今回の作業: <確認>を行ってください。  ');
 const texts=[];f.api.panel.value={ownerDocument:{defaultView:{navigator:{clipboard:{writeText:async text=>texts.push(text)}}}}};
 await f.api.copy();assert.deepEqual(texts,['今回の目標: 保存済みの意図\n対処しようとしている内容: 未確認の表示\n今回の作業: <確認>を行ってください。  ']);
 const select=f.api.selectHistory('history');await f.answer({...state(null),result:{schemaVersion:3,goal:'履歴の目標',items:[{id:'2',name:'履歴の項目',progress:0}],overall:{progress:0},nextItemId:'2',nextPrompt:'履歴の提案'}});await select;
 assert.equal(f.api.recommendedPrompt.value,'履歴の提案');
 const fresh=f.api.selectHistory();await f.answer(state(null));await fresh;assert.equal(f.api.recommendedPrompt.value,'');
});

test('先頭未完了のAI本文だけを表示・コピーし、全件完了で提案をなくす',()=>{
 const {api}=fixture();api.result.value={goal:'目的',items:[{id:'a',name:'完了',progress:100},{id:'b',name:'対象',progress:99},{id:'c',name:'後続',progress:0}],nextItemId:'b',nextPrompt:'対象だけ確認'};
 assert.equal(api.nextItem.value.id,'b');assert.equal(api.recommendedPrompt.value,'対象だけ確認');
 api.result.value.items.forEach(item=>item.progress=100);api.result.value.nextItemId=null;api.result.value.nextPrompt='';assert.equal(api.nextItem.value,undefined);assert.equal(api.recommendedPrompt.value,'');
});
test('APIから対象不一致の提案が届いても表示に採用しない',async()=>{
 const f=fixture();const refresh=f.api.refresh();await f.answer({...state(null),result:{schemaVersion:3,goal:'目標',items:[{id:'1',progress:0},{id:'2',progress:50}],overall:{progress:25},nextItemId:'2',nextPrompt:'後続の作業'}});await refresh;
 assert.equal(f.api.result.value,null);assert.match(f.api.error.value,/対象が一致しません/);
});
