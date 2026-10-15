import test from 'node:test';
import assert from 'node:assert/strict';
import {EventEmitter} from 'node:events';
import https from 'node:https';
import {fetchMetadata,RESPONSE_LIMIT} from '../runtime/model_probe.mjs';
// HTTP transport is replaced locally; these tests never contact real providers.
async function transport(handler,run){
 const original=https.request;let destroyed=0;
 https.request=(options,callback)=>{
  const request=new EventEmitter();request.destroy=()=>{destroyed++;};
  request.end=()=>queueMicrotask(()=>handler(options,callback,request));return request;
 };
 try{await run(()=>destroyed);}finally{https.request=original;}
}
function response(callback,status=200){const value=new EventEmitter();value.statusCode=status;value.destroy=()=>{};callback(value);return value;}
test('model transport has fixed HTTPS hosts, header credentials, no redirects or proxy agent',async()=>{
 await transport((options,callback)=>{
  assert.deepEqual({hostname:options.hostname,path:options.path,port:options.port,method:options.method,agent:options.agent,rejectUnauthorized:options.rejectUnauthorized},{hostname:'generativelanguage.googleapis.com',path:'/v1beta/models?pageToken=next%2Fpage',port:443,method:'GET',agent:false,rejectUnauthorized:true});
  assert.equal(options.headers['x-goog-api-key'],'synthetic-key');assert.ok(!options.path.includes('synthetic-key'));
  const r=response(callback);r.emit('data',Buffer.from('{"models":[]}'));r.emit('end');
 },async destroyed=>{assert.deepEqual(await fetchMetadata('google',{'x-goog-api-key':'synthetic-key'},'next/page'),{models:[]});assert.equal(destroyed(),1);});
});
test('HTTP redirect, oversize, malformed JSON and interrupted response close transport safely',async()=>{
 for(const mode of ['redirect','size','json','error'])await transport((_options,callback)=>{
  const r=response(callback,mode==='redirect'?302:200);
  if(mode==='redirect')return;
  if(mode==='error')return r.emit('error',new Error('synthetic-secret'));
  r.emit('data',Buffer.from(mode==='size'?'x'.repeat(RESPONSE_LIMIT+1):'synthetic-secret'));r.emit('end');
 },async destroyed=>{await assert.rejects(fetchMetadata('openai',{Authorization:'Bearer synthetic-key'}),error=>!error.message.includes('synthetic'));assert.ok(destroyed()>0);});
});
test('abort destroys in-flight request and invalid pagination never constructs a request',async()=>{
 const controller=new AbortController();
 await transport(()=>controller.abort(),async destroyed=>{await assert.rejects(fetchMetadata('openai',{},undefined,controller.signal));assert.equal(destroyed(),1);});
 await transport(()=>assert.fail('unexpected network'),async()=>{
  for(const [provider,token] of [['other',undefined],['openai','token'],['google',{}],['google','x'.repeat(4097)]])await assert.rejects(fetchMetadata(provider,{},token));
  await assert.rejects(fetchMetadata('openai',{},undefined,controller.signal));
 });
});

test('anonymous public catalog accepts multi-MiB metadata and retains bounded sanitized cache',async()=>{
 const {createModelRunner}=await import('../runtime/model_runner.mjs');
 const {createPublicModelCache}=await import('../public_models.mjs');
 const now=new Date('2026-10-15T12:00:00Z');
 const bytes=Buffer.from(JSON.stringify({data:Array.from({length:700},(_,i)=>({id:`google/example-${i}`,created:Math.floor(now.getTime()/1000),context_length:100000,architecture:{modality:'text->text'},description:'public metadata '.repeat(220)}))}));
 assert.ok(bytes.length>2*RESPONSE_LIMIT);
 await transport((options,callback)=>{
  assert.equal(options.hostname,'openrouter.ai');assert.equal(options.path,'/api/v1/models');assert.deepEqual(options.headers,{Accept:'application/json'});
  const r=response(callback);for(let i=0;i<bytes.length;i+=65536)r.emit('data',bytes.subarray(i,i+65536));r.emit('end');
 },async()=>{
  const runner=createModelRunner();
  const cache=createPublicModelCache({run:(action)=>runner.run(action,undefined,{now,reader:()=>assert.fail('public retrieval must not read configuration')})});
  await cache.refresh();assert.equal(cache.snapshot().状態,'取得済');assert.equal(cache.snapshot().件数,700);
  assert.ok(Buffer.byteLength(JSON.stringify(cache.input()))<RESPONSE_LIMIT);
  const result=await runner.run('test','openrt',{input:cache.input()});assert.equal(result.data.状態,'OK');assert.equal(result.data.モデル.length,500);
 });
});
test('larger public cap stays bounded and never expands authenticated-provider cap',async()=>{
 const {PUBLIC_RESPONSE_LIMIT}=await import('../runtime/model_probe.mjs');
 for(const [provider,headers,limit] of [['openrouter',{},PUBLIC_RESPONSE_LIMIT],['openrouter',{Authorization:'Bearer synthetic-key'},RESPONSE_LIMIT],['openai',{},RESPONSE_LIMIT]]) {
  await transport((_options,callback)=>{const r=response(callback);r.emit('data',Buffer.alloc(limit+1,32));r.emit('end');},async()=>assert.rejects(fetchMetadata(provider,headers),{message:'size'}));
 }
});
test('public failures expose only fixed reasons from transport through cache and logs',async()=>{
 const {createModelRunner}=await import('../runtime/model_runner.mjs');
 const {createPublicModelCache}=await import('../public_models.mjs');
 for(const [code,expected] of [['EAI_AGAIN','名前解決'],['UNABLE_TO_GET_ISSUER_CERT_LOCALLY','TLS証明書'],['ECONNRESET','接続できません']])await transport((_options,_callback,request)=>request.emit('error',Object.assign(new Error('synthetic-secret'),{code})),async()=>{
  const logs=[];const runner=createModelRunner(),cache=createPublicModelCache({run:runner.run,warn:message=>logs.push(message)});
  await cache.refresh();assert.equal(cache.snapshot().状態,'失敗');assert.ok(cache.snapshot().説明.includes(expected));assert.equal(logs.length,1);assert.ok(logs[0].includes(expected));assert.ok(!JSON.stringify([cache.snapshot(),logs]).includes('synthetic-secret'));
 });
});
test('public HTTP, JSON, schema and interrupted-body errors remain distinguishable and redacted',async()=>{
 const {publicCatalog}=await import('../runtime/model_probe.mjs');
 for(const [mode,reason] of [['http','http'],['json','json'],['schema','shape'],['aborted','response']])await transport((_options,callback)=>{
  const r=response(callback,mode==='http'?503:200);if(mode==='http')return;
  if(mode==='aborted'){r.emit('aborted');return;}
  r.emit('data',Buffer.from(mode==='json'?'synthetic-secret':JSON.stringify({data:[{id:'google/test',created:'synthetic-secret'}]})));r.emit('end');
 },async()=>{const result=await publicCatalog();assert.equal(result.状態,'NG');assert.equal(result.失敗理由,reason);assert.ok(!JSON.stringify(result).includes('synthetic-secret'));});
});
