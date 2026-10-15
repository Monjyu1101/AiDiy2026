import test from 'node:test';import assert from 'node:assert/strict';import {readFile} from 'node:fs/promises';
import {createPublicModelCache} from '../public_models.mjs';
const success={data:{状態:'OK',公開モデル:{'google/example':{model_id:'google/example',作成日:'2026/10/01',トークン数:'100',モダリティ:'text'}},確認日時:'2026-10-15T00:00:00Z'}};
test('public cache stays independent, uses anonymous-only action once and reuses snapshot',async()=>{
 const calls=[];const cache=createPublicModelCache({run:async(...args)=>{calls.push(args);return success;}});
 assert.equal(cache.snapshot().状態,'未取得');assert.deepEqual(cache.input(),{公開モデル:{},公開状態:'未取得',確認日時:null});
 await cache.refresh();assert.deepEqual(calls,[['public']]);assert.equal(cache.snapshot().状態,'取得済');assert.equal(cache.snapshot().件数,1);assert.equal(cache.input().確認日時,cache.snapshot().確認日時);assert.equal(cache.input().公開モデル['google/example'].作成日,'2026/10/01');
 for(let i=0;i<4;i++)cache.input();assert.equal(calls.length,1);
});
test('startup retrieval is nonblocking, single-flight and distinguishable while pending',async()=>{
 let release,calls=0;const cache=createPublicModelCache({run:()=>{calls++;return new Promise(resolve=>{release=resolve;});}});
 const first=cache.refresh();assert.equal(cache.snapshot().状態,'取得中');assert.equal(cache.refresh(),first);assert.equal(calls,1);assert.deepEqual(cache.input().公開モデル,{});
 release(success);await first;assert.equal(cache.snapshot().状態,'取得済');assert.equal(cache.snapshot().世代,2);
 const source=await readFile(new URL('../diag_main.mjs',import.meta.url),'utf8');assert.equal((source.match(/void publicCache.refresh\(\)/g)||[]).length,1);
});
test('failure invalidates old success and explicit retry can recover',async()=>{
 let result=success;const cache=createPublicModelCache({run:async()=>result});await cache.refresh();result={error:'timeout'};await cache.refresh();assert.equal(cache.snapshot().状態,'失敗');assert.equal(cache.snapshot().件数,0);assert.deepEqual(cache.input().公開モデル,{});
 result=success;await cache.refresh();assert.equal(cache.snapshot().状態,'取得済');
});
test('malformed or failed data never shows successful acquisition',async()=>{
 for(const result of [{data:{状態:'NG',公開モデル:{}}},{data:{状態:'OK',公開モデル:[]}},{data:{状態:'OK'}}]){const cache=createPublicModelCache({run:async()=>result});await cache.refresh();assert.equal(cache.snapshot().状態,'失敗');}
});
