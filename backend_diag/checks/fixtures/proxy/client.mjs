// テスト専用。固定 API hostname を維持して socket の接続先だけ loopback mock へ向ける。
import http from 'node:http';
import https from 'node:https';
import assert from 'node:assert/strict';
import {fetchMetadata,probe,publicCatalog} from '../../../runtime/model_probe.mjs';
const options=JSON.parse(process.argv[2]);
const originalHttps=https.request;
https.request=(request,callback)=>{
 if(request.hostname!=='127.0.0.1'&&request.agent===false){
  assert.ok(options.directPort,'unexpected direct API access');
  return originalHttps({...request,port:options.directPort,lookup:(_host,lookupOptions,callback)=>lookupOptions.all?callback(null,[{address:'127.0.0.1',family:4}]):callback(null,'127.0.0.1',4)},callback);
 }
 return originalHttps(request,callback);
};
if(options.localPort){
 const original=http.request;
 http.request=(request,callback)=>{assert.equal(request.hostname,'127.0.0.1');assert.equal(request.agent,false);return original({...request,port:options.localPort},callback);};
}
const abort=new AbortController();
if(options.abort)setTimeout(()=>abort.abort(),100);
try{
 const data=await fetchMetadata(options.provider||'openai',{Authorization:'Bearer synthetic-api-secret'},undefined,abort.signal);
 assert.equal(options.reason,undefined);assert.deepEqual(data,{data:[]});
 process.stdout.write('ok');
}catch(error){
 assert.equal(error.message,options.reason);
 assert.ok(!JSON.stringify(error).includes('synthetic'));
 // UI/ログに流れる説明も固定分類だけになることを確認。
 const fetch=async()=>{throw error;};
 const result=await probe('openai',{reader:()=>JSON.stringify({openai_key_id:'synthetic-api-secret'}),fetch});
 const publicResult=await publicCatalog({fetch});
 const serialized=JSON.stringify([result,publicResult]);
 assert.ok(!serialized.includes('synthetic'));assert.ok(!serialized.includes('127.0.0.1'));
 assert.equal(publicResult.失敗理由,options.reason);
 process.stdout.write('ok');
}
