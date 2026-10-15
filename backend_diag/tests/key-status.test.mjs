import test from 'node:test';
import assert from 'node:assert/strict';
import {EventEmitter} from 'node:events';
import {PassThrough} from 'node:stream';
import {mkdtemp,writeFile,mkdir,chmod,rm} from 'node:fs/promises';
import os from 'node:os';import path from 'node:path';
import {getKeyStatus,testKey,KEY_PROVIDERS,runPython,pythonEnvironment,resolvePython} from '../key_status.mjs';
function fakeSpawn(callback){return (...args)=>{const child=new EventEmitter();child.pid=123456;child.stdin=new PassThrough();child.stdout=new PassThrough();child.stderr=new PassThrough();child.unref=()=>{};child.kill=()=>{};setImmediate(()=>callback(child,args));return child;};}
test('Node never reads config or sends keys; fixed isolated Python action only',async()=>{
 let killed=0;
 const result=await runPython('test','openai',{resolve:async()=>'/fixture/python',kill:()=>killed++,spawn:fakeSpawn((child,[exe,args,options])=>{
  assert.equal(exe,'/fixture/python');assert.deepEqual(args.slice(0,3),['-I','-S','-B']);assert.match(args[3],/backend_diag[\\/]model_probe.py$/);assert.deepEqual(args.slice(4),['test','openai']);
  assert.equal(options.shell,false);assert.equal(options.stdio[0],'pipe');assert.ok(options.cwd.startsWith(os.tmpdir()));assert.equal(options.env.PYTHONPATH,undefined);assert.equal(options.env.OPENAI_API_KEY,undefined);
  child.stdout.write(JSON.stringify({id:'openai',状態:'OK',モデル:['model']}));child.emit('close',0);
 })});assert.equal(result.data.状態,'OK');assert.ok(killed>0);
});
test('child environment excludes secrets, proxies, Python hooks and home config',()=>{
 const env=pythonEnvironment('/isolated',{PATH:'/bin',OPENAI_API_KEY:'hidden',HTTP_PROXY:'hidden',PYTHONPATH:'hidden',PYTHONSTARTUP:'hidden',HOME:'/private'});
 assert.equal(env.PATH,'/bin');assert.equal(env.HOME,'/isolated');assert.ok(!JSON.stringify(env).includes('hidden'));assert.ok(!JSON.stringify(env).includes('/private'));
});
test('missing Python is untested and never treated as unset or OK',async()=>{
 const result=await runPython('status',undefined,{resolve:async()=>null});assert.equal(result.error,'missing');
 const status=await getKeyStatus({run:async()=>result});assert.equal(status.設定状態,'確認不可');assert.ok(status.項目.every(row=>row.設定済み===null&&!row.テスト可能));assert.match(status.説明,/Python/);
 const tested=await testKey('openai',{run:async()=>result});assert.equal(tested.状態,'未実施');assert.match(tested.説明,/Python/);
});
test('unknown and unsupported IDs never launch bridge',async()=>{
 for(const id of ['../arbitrary','azure','discord'])assert.equal((await testKey(id,{run:()=>assert.fail('spawn')})).状態,'未実施');
 assert.equal((await runPython('test','bad',{resolve:()=>assert.fail('resolve')})).error,'unsupported');
});
test('timeouts, output bounds, stderr and malformed output never leak child text',async()=>{
 for(const scenario of ['timeout','stdout','stderr','invalid','exit','error']){
  let killed=0;const result=await runPython('test','openai',{resolve:async()=>'/fixture/python',timeout:15,outputLimit:30,kill:()=>killed++,spawn:fakeSpawn(child=>{
   if(scenario==='timeout')return;
   if(scenario==='stdout'||scenario==='stderr')child[scenario].write('fixture-secret'.repeat(10));
   else if(scenario==='invalid')child.stdout.write('fixture-secret');
   else if(scenario==='error')child.emit('error',Error('fixture-secret'));
   child.emit('close',scenario==='exit'?1:0);
  })});assert.ok(result.error);assert.ok(killed);assert.ok(!JSON.stringify(result).includes('fixture-secret'));
 }
});
test('safe bridge schema discards unknown fields and formats model details',async()=>{
 const status=await getKeyStatus({run:async()=>({data:{設定状態:'読込済み',項目:[null,{id:'openrt',設定済み:false,キー不要:true,テスト可能:true,secret:'hidden'}]}})});
 assert.equal(status.項目.length,KEY_PROVIDERS.length);assert.equal(status.項目.find(row=>row.id==='openrt').キー不要,true);assert.ok(!JSON.stringify(status).includes('hidden'));
 const tested=await testKey('openai',{run:async()=>({data:{id:'openai',状態:'OK',説明:'fixture',モデル:['model','<script>','model'],モデル詳細:[{model_id:'model',作成日:'2026/10/01',トークン数:'100',モダリティ:'text',secret:'hidden'}],警告:['補完未確認'],確認日時:'2026-10-15T00:00:00Z',secret:'hidden'}})});
 assert.deepEqual(tested.モデル,['model']);assert.equal(tested.モデル詳細[0].作成日,'2026/10/01');assert.deepEqual(tested.警告,['補完未確認']);assert.ok(!JSON.stringify(tested).includes('hidden'));
});
test('Python resolution is diag-owned virtualenv then PATH, never backend dependency',async()=>{
 const root=await mkdtemp(path.join(os.tmpdir(),'diag-python-resolve-'));
 try{const diag=path.join(root,'backend_diag/.venv/bin/python'),backend=path.join(root,'backend_server/.venv/bin/python'),system=path.join(root,'path/python3');
 for(const file of [diag,backend,system]){await mkdir(path.dirname(file),{recursive:true});await writeFile(file,'fixture');await chmod(file,0o755);}
 const options={root,platform:'linux',env:{PATH:path.dirname(system)}};assert.equal(await resolvePython(options),diag);await rm(diag);assert.equal(await resolvePython(options),system);await rm(system);assert.equal(await resolvePython(options),null);
 }finally{await rm(root,{recursive:true,force:true});}
});
test('real synthetic child terminates on deadline without reading config',async()=>{
 const {spawn}=await import('node:child_process');let child;
 const result=await runPython('test','openai',{resolve:async()=>'/fixture/python',timeout:50,spawn:(_executable,_args,options)=>{
  child=spawn(process.execPath,['-e','setInterval(()=>{},1000)'],options);return child;
 }});
 assert.equal(result.error,'timeout');
 await new Promise(resolve=>{if(child.exitCode!==null || child.signalCode)resolve();else child.once('exit',resolve);});
 assert.ok(child.signalCode || child.exitCode!==null);
});
test('public startup is fixed anonymous action and cached input has EOF and byte limit',async()=>{
 const publicResult=await runPython('public',undefined,{resolve:async()=>'/fixture/python',kill:()=>{},spawn:fakeSpawn((child,[_exe,args,options])=>{
  assert.deepEqual(args.slice(4),['public']);assert.equal(options.stdio[0],'ignore');child.stdout.write(JSON.stringify({状態:'OK',公開モデル:{}}));child.emit('close',0);
 })});assert.equal(publicResult.data.状態,'OK');
 const input={公開モデル:{example:{model_id:'example'}},公開状態:'取得済',確認日時:'2026-10-15T00:00:00Z'};
 await runPython('test','openai',{input,resolve:async()=>'/fixture/python',kill:()=>{},spawn:fakeSpawn(child=>{
  assert.equal(child.stdin.writableEnded,true);assert.deepEqual(JSON.parse(child.stdin.read().toString()),input);child.stdout.write('{}');child.emit('close',0);
 })});
 const oversized=await runPython('test','openai',{input:{large:'x'.repeat(1048577)},resolve:async()=>'/fixture/python',spawn:()=>assert.fail('oversize must not spawn')});assert.equal(oversized.error,'input');
});
test('parallel bridge limit and shutdown cancel active children',async()=>{
 const {cancelKeyProbes}=await import('../key_status.mjs');let killed=0,started=0;
 const options={resolve:async()=>'/fixture/python',kill:()=>killed++,spawn:fakeSpawn(()=>{started++;})};
 const first=runPython('status',undefined,options),second=runPython('test','openai',options);
 while(started<2)await new Promise(resolve=>setTimeout(resolve,1));
 assert.equal((await runPython('status',undefined,options)).error,'busy');
 cancelKeyProbes();assert.equal((await first).error,'stopped');assert.equal((await second).error,'stopped');assert.equal(killed,2);
 assert.equal((await runPython('status',undefined,options)).error,'stopped');
});
