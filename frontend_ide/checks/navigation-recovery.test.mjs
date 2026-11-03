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
 const api=vm.runInNewContext(source+`;({navigate,refresh,busy,job,error,visible,availability})`,{
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
