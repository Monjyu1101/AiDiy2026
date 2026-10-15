import test from 'node:test';
import assert from 'node:assert/strict';
import {probe,publicCatalog,status,safeDetails,validatedCache} from '../runtime/model_probe.mjs';
const now=new Date('2026-10-15T12:00:00Z'),created=now.getTime()/1000;
const reader=value=>async()=>JSON.stringify(value);
const forbidden=()=>assert.fail('Unexpected config/network operation');
test('invalid configuration is unknown; unset and unsupported keys never fetch',async()=>{
 assert.equal((await status({reader:async()=> '[]'})).設定状態,'読込不可');
 assert.equal((await probe('gemini',{reader:reader({freeai_key_id:'fixture-key'}),fetch:forbidden})).状態,'未実施');
 assert.equal((await probe('azure',{reader:forbidden,fetch:forbidden})).状態,'未実施');
});
test('selected Google credential only, pagination completes before cache filtering',async()=>{
 const calls=[];
 const result=await probe('freeai',{now,reader:reader({gemini_key_id:'other-secret',freeai_key_id:'selected-secret'}),cache:{公開状態:'取得済',公開モデル:{'google/second':{作成日:'2026/10/01'}}},fetch:async(provider,headers,token)=>{
  calls.push({provider,headers,token});return {models:[{name:`models/${token?'second':'first'}`,supportedGenerationMethods:['generateContent'],inputTokenLimit:222}],...(token?{}:{nextPageToken:'page2'})};
 }});
 assert.equal(result.状態,'OK');assert.deepEqual(result.モデル,['second']);assert.equal(result.モデル詳細[0].作成日,'2026/10/01');assert.equal(calls.length,2);
 for(const call of calls){assert.equal(call.provider,'google');assert.deepEqual(call.headers,{'x-goog-api-key':'selected-secret'});}
 assert.equal(calls[1].token,'page2');assert.ok(!JSON.stringify(result).includes('secret'));
});
test('pagination is bounded and malformed responses fail closed',async()=>{
 let count=0;
 const result=await probe('gemini',{reader:reader({gemini_key_id:'fixture-key'}),fetch:async()=>{count++;return {models:[],nextPageToken:'again'};}});
 assert.equal(result.状態,'NG');assert.equal(count,20);
 for(const body of [{data:{}},{data:null},{models:[]}]){
  const response=await probe('openai',{reader:reader({openai_key_id:'fixture-key'}),fetch:async()=>body});assert.equal(response.状態,'NG');
 }
});
test('all configured secrets and organization are redacted from metadata',async()=>{
 const result=await probe('openai',{now,reader:reader({openai_key_id:'fixture-key',gemini_key_id:'other-secret',openai_organization:'fixture-org'}),fetch:async(provider,headers)=>{
  assert.equal(provider,'openai');assert.equal(headers['OpenAI-Organization'],'fixture-org');assert.equal(headers.Authorization,'Bearer fixture-key');
  return {data:[{id:'safe-model',created},{id:'fixture-org',created},{id:'other-secret',created}]};
 }});
 assert.equal(result.状態,'OK');assert.deepEqual(result.モデル,['safe-model']);assert.ok(result.警告.length);
 assert.ok(!JSON.stringify(result).includes('fixture-org'));assert.ok(!JSON.stringify(result).includes('other-secret'));
 assert.deepEqual(safeDetails({'safe-model':{作成日:'other-secret',トークン数:'fixture-key',モダリティ:'prefix-other-secret'}},['fixture-key','other-secret']),[{model_id:'safe-model',作成日:null,トークン数:null,モダリティ:null}]);
});
test('public failure does not leak provider errors and cache validation fails closed',async()=>{
 const result=await publicCatalog({now,fetch:async()=>{throw Error('secret-error');}});
 assert.equal(result.状態,'NG');assert.ok(!JSON.stringify(result).includes('secret-error'));
 for(const cache of [null,[],{公開状態:'取得中',公開モデル:{}},{公開状態:'取得済',公開モデル:{bad:null}}]){
  const result=await probe('openrt',{reader:forbidden,fetch:forbidden,cache});assert.equal(result.状態,'未実施');
 }
});
test('configuration bounds, UTF-8 BOM, unreadable and missing states',async()=>{
 const {readConfig,CONFIG_LIMIT}=await import('../runtime/model_probe.mjs');
 assert.equal((await readConfig(async()=> '\uFEFF{"openai_key_id":"fixture-key"}'))[0],'読込済み');
 assert.equal((await readConfig(async()=> 'x'.repeat(CONFIG_LIMIT+1)))[0],'読込不可');
 assert.equal((await readConfig(async()=> Buffer.from([0xff,0xfe])))[0],'読込不可');
 assert.equal((await readConfig(async()=> {throw Object.assign(Error('fixture-secret'),{code:'ENOENT'});}))[0],'未作成');
 assert.equal((await readConfig(async()=> {throw Error('fixture-secret');}))[0],'読込不可');
});
test('public details are unlimited but individual display is capped at 500',async()=>{
 const data=Array.from({length:501},(_,i)=>({id:`other/model-${i}`,created}));
 const result=await publicCatalog({now,fetch:async()=>({data})});assert.equal(Object.keys(result.公開モデル).length,501);
 const selected=await probe('openrt',{reader:forbidden,fetch:forbidden,cache:{公開状態:'取得済',公開モデル:result.公開モデル}});assert.equal(selected.モデル.length,500);
});
