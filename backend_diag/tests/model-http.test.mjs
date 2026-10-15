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
