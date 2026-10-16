// DIAG_TEST_PYTHON must have backend_tools' MCP 2.x, FastAPI and uvicorn dependencies.
import test from 'node:test';
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {createInterface} from 'node:readline';
import {callMcp,createModelTrials,localRequest} from '../モデル試行/trials.mjs';

test('actual MCP SDK and production Chat/Code registrations return successful string results', {skip:!process.env.DIAG_TEST_PYTHON,timeout:20000},async()=>{
 const child=spawn(process.env.DIAG_TEST_PYTHON,[fileURLToPath(new URL('./fixtures/model_trials_tools.py',import.meta.url))],{stdio:['ignore','pipe','pipe'],windowsHide:true});
 let errors='';child.stderr.on('data',chunk=>errors+=chunk);
 const lines=createInterface({input:child.stdout});
 try{
  const port=await new Promise((resolve,reject)=>{
   const timer=setTimeout(()=>reject(new Error(`fixture startup: ${errors}`)),10000);
   lines.once('line',line=>{clearTimeout(timer);resolve(JSON.parse(line).port);});
   child.once('error',error=>{clearTimeout(timer);reject(error);});
   child.once('exit',()=>{clearTimeout(timer);reject(new Error(`fixture exit: ${errors}`));});
  });
  const config={PORT_TOOLS:port,CHAT_AI_NAME:'freeai_chat',CHAT_FREEAI_MODEL:'chat-test',CODE_AI1_NAME:'codex_cli',CODE_AI1_MODEL:'auto',LIVE_AI_NAME:'freeai_live',LIVE_FREEAI_MODEL:'live-test',LIVE_FREEAI_VOICE:'Zephyr'};
  const wire=[];
  const request=async options=>{const response=await localRequest(options);wire.push({options,response});return response;};
  for(const [区分,プロバイダ,モデル] of [['CHAT','freeai_chat','chat-test'],['CODE','codex_cli','auto']]){
   const result=await callMcp({区分,プロバイダ,モデル},config,{request});
   assert.equal(result.status,'OK');assert.equal(result.result,'おはようございます');
  }
  const calls=wire.filter(x=>x.options.body?.method==='tools/call');
  assert.equal(calls.length,2);
  for(const {options,response} of calls){
   assert.equal(typeof response.body.result.structuredContent.result,'string');
   assert.ok(options.headers['Mcp-Session-Id']);
   assert.equal(options.headers['MCP-Protocol-Version'],'2024-11-05');
  }
  assert.equal(wire.filter(x=>x.options.method==='DELETE').length,2);
  const trials=createModelTrials({reader:async()=>JSON.stringify(config),statusFn:async()=>({online:true})});
  try{const start=await trials.start();for(const row of start.項目){const result=await trials.next(start.実行ID,row.id);if(['CHAT','CODE1','LIVE'].includes(row.id))assert.equal(result.状態,'OK',`${row.id}: ${result.説明}`);}}
  finally{await trials.close();}
 }finally{lines.close();child.kill();}
});
