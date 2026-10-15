import test from 'node:test';
import assert from 'node:assert/strict';
import {getKeyStatus,testKey,KEY_PROVIDERS,runModels} from '../key_status.mjs';
const now=new Date('2026-10-15T12:00:00Z');
const reader=value=>async filename=>{assert.match(String(filename),/[\\/]_config[\\/]AiDiy_key\.json$/);return JSON.stringify(value);};
const forbidden=()=>assert.fail('Unexpected configuration read or network call');

test('Node status uses only bounded config reader and never contacts a provider',async()=>{
 const response=await runModels('status',undefined,{reader:reader({openai_key_id:'fixture-secret',gemini_key_id:' < placeholder > ',ollama_key_id:'ollama'}),fetch:forbidden});
 assert.equal(response.data.設定状態,'読込済み');
 const rows=Object.fromEntries(response.data.項目.map(row=>[row.id,row]));
 assert.equal(rows.openai.設定済み,true);assert.equal(rows.gemini.設定済み,false);assert.equal(rows.ollama.設定済み,null);assert.equal(rows.ollama.ローカル,true);assert.equal(rows.ollama.キー不要,true);assert.equal(rows.ollama.テスト可能,true);assert.equal(rows.openrt.キー不要,false);
 assert.ok(!JSON.stringify(response).includes('fixture-secret'));
});
test('unknown and unsupported IDs never read config or fetch',async()=>{
 for(const id of ['../arbitrary','azure','discord'])assert.equal((await testKey(id,{run:forbidden})).状態,'未実施');
 assert.equal((await runModels('test','bad',{reader:forbidden,fetch:forbidden})).error,'unsupported');
});
test('safe runner schema discards unknown fields and formats model details',async()=>{
 const status=await getKeyStatus({run:async()=>({data:{設定状態:'読込済み',項目:[null,{id:'openrt',設定済み:false,キー不要:true,テスト可能:true,secret:'hidden'}]}})});
 assert.equal(status.項目.length,KEY_PROVIDERS.length);assert.equal(status.項目.find(row=>row.id==='openrt').キー不要,true);assert.ok(!JSON.stringify(status).includes('hidden'));
 const tested=await testKey('openai',{run:async()=>({data:{id:'openai',状態:'OK',説明:'fixture',モデル:['model','<script>','model'],モデル詳細:[{model_id:'model',作成日:'2026/10/01',トークン数:'100',モダリティ:'text',secret:'hidden'}],警告:['補完未確認'],確認日時:'2026-10-15T00:00:00Z',secret:'hidden'}})});
 assert.deepEqual(tested.モデル,['model']);assert.equal(tested.モデル詳細[0].作成日,'2026/10/01');assert.deepEqual(tested.警告,['補完未確認']);assert.ok(!JSON.stringify(tested).includes('hidden'));
});
test('runner errors leave status unknown and probes untested without leaked text',async()=>{
 for(const error of ['timeout','output','busy','stopped','invalid']){
  const status=await getKeyStatus({run:async()=>({error})});assert.equal(status.設定状態,'確認不可');assert.ok(status.項目.every(row=>row.設定済み===null&&!row.テスト可能));
  const result=await testKey('openai',{run:async()=>({error})});assert.equal(result.状態,'未実施');assert.doesNotMatch(result.説明,/Python/);
 }
});
test('public acquisition uses anonymous fetch, never configuration',async()=>{
 const result=await runModels('public',undefined,{reader:forbidden,now,fetch:async(provider,headers)=>{
  assert.equal(provider,'openrouter');assert.deepEqual(headers,{});return {data:[{id:'other/new',created:now.getTime()/1000}]};
 }});
 assert.equal(result.data.状態,'OK');assert.deepEqual(Object.keys(result.data.公開モデル),['other/new']);
});
test('OpenRouter individual test verifies key and preserves authentication marker',async()=>{
 const input={公開状態:'取得済',公開モデル:{example:{model_id:'example',作成日:'2026/10/15',トークン数:'100',モダリティ:'text'}},確認日時:now.toISOString()};
 const result=await runModels('test','openrt',{input,reader:reader({openrt_key_id:'fixture-key'}),fetch:async provider=>{assert.equal(provider,'openrouter-key');return {data:{is_free_tier:false}};}});
 assert.equal(result.data.認証確認,true);
 const safe=await testKey('openrt',{run:async()=>result});assert.equal(safe.認証確認,true);
 const {currentOpenRouterProof}=await import('../runtime/model_probe.mjs');
 assert.equal(await currentOpenRouterProof(safe,reader({openrt_key_id:'fixture-key'})),true);
 assert.equal(await currentOpenRouterProof(safe,reader({openrt_key_id:'changed-key'})),false);
 assert.ok(!JSON.stringify(safe).includes('fixture-key'));
 assert.equal(result.data.状態,'OK');assert.deepEqual(result.data.モデル,['example']);
});
test('oversized cache is rejected before configuration or network',async()=>{
 const result=await runModels('test','openai',{input:{large:'x'.repeat(1048577)},reader:forbidden,fetch:forbidden});assert.equal(result.error,'input');
});
test('deadline aborts provider operation and returns a safe error',async()=>{
 let signal;
 const result=await runModels('test','openai',{timeout:15,reader:reader({openai_key_id:'fixture-secret'}),fetch:async(_provider,_headers,_pageToken,abortSignal)=>{signal=abortSignal;return new Promise(()=>{});}});
 assert.equal(result.error,'timeout');assert.equal(signal.aborted,true);assert.ok(!JSON.stringify(result).includes('fixture-secret'));
});
test('isolated runners bound concurrency and shutdown cancels every operation',async()=>{
 const {createModelRunner}=await import('../key_status.mjs');const runner=createModelRunner();let started=0;const signals=[];
 const options={reader:reader({openai_key_id:'fixture-secret'}),fetch:async(_p,_h,_t,signal)=>{started++;signals.push(signal);return new Promise(()=>{});}};
 const first=runner.run('test','openai',options),second=runner.run('test','openai',options);
 while(started<2)await new Promise(resolve=>setImmediate(resolve));
 assert.equal((await runner.run('status',undefined,{reader:forbidden})).error,'busy');
 runner.cancel();assert.equal((await first).error,'stopped');assert.equal((await second).error,'stopped');assert.ok(signals.every(signal=>signal.aborted));
 assert.equal((await runner.run('status',undefined,{reader:forbidden})).error,'stopped');
});
test('external abort prevents startup and aborts an active request',async()=>{
 const {createModelRunner}=await import('../key_status.mjs');const runner=createModelRunner();const early=new AbortController();early.abort();
 assert.equal((await runner.run('status',undefined,{signal:early.signal,reader:forbidden})).error,'stopped');
 const controller=new AbortController();let started;
 const ready=new Promise(resolve=>{started=resolve;});let requestSignal;
 const pending=runner.run('test','openai',{signal:controller.signal,reader:reader({openai_key_id:'fixture-secret'}),fetch:async(_p,_h,_t,signal)=>{requestSignal=signal;started();return new Promise(()=>{});}});
 await ready;controller.abort();assert.equal((await pending).error,'stopped');assert.equal(requestSignal.aborted,true);
});
