import test from 'node:test';
import assert from 'node:assert/strict';
import {cp,mkdtemp,mkdir,writeFile,rm} from 'node:fs/promises';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import os from 'node:os';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
test('default Node runtime starts without Python on PATH and serves anonymous models plus config status',{timeout:15000},async()=>{
 const root=await mkdtemp(path.join(os.tmpdir(),'diag-node-only-'));let child;
 try {
  const diag=path.join(root,'backend_diag');
  await cp(new URL('../',import.meta.url),diag,{recursive:true,filter:source=>!/(?:^|[/\\])(?:node_modules|tests|__pycache__)(?:[/\\]|$)/.test(source)});
  await mkdir(path.join(root,'_config'));await writeFile(path.join(root,'_config/AiDiy_key.json'),JSON.stringify({gemini_key_id:'synthetic-gemini-key'}));
  await mkdir(path.join(root,'empty-path'));
  // Keep production startup/cache/runner/catalog. Replace HTTPS transport alone, not model behavior.
  const preload=path.join(root,'mock-public.mjs');
  await writeFile(preload,`import https from 'node:https';import {EventEmitter} from 'node:events';
https.request=(options,callback)=>{if(options.hostname!=='openrouter.ai'||options.path!=='/api/v1/models'||options.headers.Authorization)throw new Error('unexpected request');const request=new EventEmitter();request.destroy=()=>{};request.end=()=>queueMicrotask(()=>{const response=new EventEmitter();response.statusCode=200;callback(response);response.emit('data',Buffer.from(JSON.stringify({data:[{id:'openai/synthetic-model',created:Math.floor(Date.now()/1000),context_length:100,architecture:{modality:'text->text'}}]})));response.emit('end');});return request;};`);
  child=spawn(process.execPath,['--import',pathToFileURL(preload).href,path.join(diag,'diag_main.mjs'),'--no-open','--port','0'],{env:{...process.env,PATH:path.join(root,'empty-path'),NODE_OPTIONS:'',CODESPACES:'',CI:'1'},stdio:['ignore','pipe','pipe']});
  const exited=once(child,'exit');let output='',stderr='';child.stderr.on('data',chunk=>stderr+=chunk);
  const url=await new Promise((resolve,reject)=>{child.stdout.on('data',chunk=>{output+=chunk;const match=output.match(/http:\/\/127\.0\.0\.1:\d+\/#token=[^\s]+/);if(match)resolve(new URL(match[0]));});child.once('exit',()=>reject(new Error('Unexpected startup exit')));});
  const token=new URLSearchParams(url.hash.slice(1)).get('token');url.hash='';
  const api=async(route,method='GET')=>{const result=await fetch(new URL('api/'+route,url),{method,headers:{Authorization:'Bearer '+token}});assert.equal(result.status,200);return result.json();};
  assert.equal((await fetch(url)).status,200);
  let publicStatus;for(let i=0;i<100;i++){publicStatus=await api(encodeURIComponent('公開モデル'));if(publicStatus.状態==='取得済')break;await new Promise(resolve=>setTimeout(resolve,10));}
  assert.equal(publicStatus.状態,'取得済');assert.equal(publicStatus.件数,1);
  const status=await api(encodeURIComponent('キー設定'));assert.equal(status.設定状態,'読込済み');assert.equal(status.項目.find(row=>row.id==='gemini').設定済み,true);assert.ok(!JSON.stringify(status).includes('synthetic-gemini-key'));
  const result=await api(encodeURIComponent('キーテスト')+'/openrt','POST');assert.equal(result.状態,'OK');assert.deepEqual(result.モデル,['openai/synthetic-model']);
  child.kill('SIGTERM');await exited;assert.equal(child.exitCode,0);assert.equal(stderr,'');
 }finally{if(child?.exitCode===null)child.kill('SIGKILL');await rm(root,{recursive:true,force:true});}
});
