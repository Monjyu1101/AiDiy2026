import test from 'node:test';
import assert from 'node:assert/strict';
import {cp,mkdtemp,readFile,writeFile,rm} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {launchDetached} from '../起動/launch.mjs';
import {parseArgs} from '../diag_main.mjs';
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function until(fn){for(let n=0;n<150;n++){const value=await fn();if(value)return value;await pause(20);}throw Error('fixture readiness timeout');}
async function fixture(mode='normal') {
 const root=await mkdtemp(path.join(os.tmpdir(),'diag-launch-'));
 await cp(new URL('../',import.meta.url),root,{recursive:true,filter:source=>!/(?:^|[/\\])(?:node_modules|tests|__pycache__)(?:[/\\]|$)/.test(source)});
 // ネットワーク API と UI build のみ fixture 化。HTTP、CLI、IPC、所有関係は実プロセス。
 await writeFile(path.join(root,'モデル情報/public_models.mjs'),`export function createPublicModelCache(){return {refresh:async()=>({}),snapshot:()=>({}),input:()=>({})};}`);
 await writeFile(path.join(root,'ui/verify.mjs'),'export async function verify(){return true;}');
 const desktop=path.join(root,'起動/desktop.mjs');
 await writeFile(desktop,(await readFile(desktop,'utf8')).replace(/export async function desktopBinary[\s\S]*?\nconst failures=/,"export async function desktopBinary(){return process.execPath;}\nconst failures="));
 await writeFile(path.join(root,'起動/electron-main.cjs'),`
 const fs=require('node:fs');
 process.on('disconnect',()=>process.exit(0));
 process.send({type:'diag-ready'});
 process.once('message',async m=>{
   if(m.type!=='diag-start'||JSON.stringify(process.argv).includes('#token=')||JSON.stringify(process.env).includes('#token='))process.exit(9);
   const url=new URL(m.url),token=url.hash.slice(7);url.hash='';
   const result=await fetch(url+'api/'+encodeURIComponent('一覧'),{headers:{Authorization:'Bearer '+token}});
   if(result.status!==200)process.exit(8);
   fs.writeFileSync(${JSON.stringify(path.join(root,'state.json'))},JSON.stringify({pid:process.pid,parent:process.ppid,url:String(url)}));
   if(${JSON.stringify(mode)}==='fail')process.exit(7);
   if(${JSON.stringify(mode)}!=='hang')process.send({type:'diag-shown'});
 });
 `);
 return root;
}
function start(root,args=[]){
 const child=spawn(process.execPath,[path.join(root,'diag_main.mjs'),...args],{env:{...process.env,DISPLAY:':fixture',CI:'false',CODESPACES:'false'},stdio:['ignore','pipe','pipe']});
 child.output='';child.errors='';child.stdout.on('data',x=>child.output+=x);child.stderr.on('data',x=>child.errors+=x);child.finished=once(child,'exit');return child;
}
async function state(root){return until(async()=>{try{return JSON.parse(await readFile(path.join(root,'state.json'),'utf8'));}catch{return null;}});}
async function gone(url){await until(async()=>{try{await fetch(url);return false;}catch{return true;}});}
async function cleanup(root,child,info){
 if(child?.exitCode===null && child?.signalCode===null)child.kill('SIGTERM');
 if(info)for(const pid of [info.pid,info.parent]){if(pid===child?.pid)continue;try{process.kill(pid,'SIGTERM');}catch{}}
 await rm(root,{recursive:true,force:true});
}
test('foreground/wait options are explicit; browser/no-open retain foreground mode',()=>{
 assert.equal(parseArgs(['--foreground']).foreground,true);assert.equal(parseArgs(['--wait']).foreground,true);
 assert.equal(parseArgs([]).foreground,undefined);
});
test('real desktop launcher returns after shown while supervisor owns HTTP and Electron',{timeout:10000},async()=>{
 const root=await fixture();let child,info;
 try{
  child=start(root);info=await state(root);const [code]=await child.finished;
  assert.equal(code,0,child.errors);assert.notEqual(info.parent,child.pid);
  assert.equal((await fetch(info.url)).status,200);assert.ok(!child.output.includes('#token='));assert.equal(child.errors,'');
  process.kill(info.pid,'SIGTERM');await gone(info.url);
 }finally{await cleanup(root,child,info);}
});
for(const flag of ['--foreground','--wait'])test(`real ${flag} stays attached until Electron closes`,{timeout:10000},async()=>{
 const root=await fixture();let child,info;
 try{child=start(root,[flag]);info=await state(root);await pause(100);assert.equal(child.exitCode,null);assert.equal(info.parent,child.pid);
 process.kill(info.pid,'SIGTERM');await child.finished;await gone(info.url);
 }finally{await cleanup(root,child,info);}
});
test('real no-open HTTP process stays in foreground and stops on SIGTERM',{timeout:10000},async()=>{
 const root=await fixture();let child;
 try{child=start(root,['--browser','--no-open']);const url=await until(()=>child.output.match(/http:\/\/127\.0\.0\.1:\d+\//)?.[0]);
 assert.equal(child.exitCode,null);assert.equal((await fetch(url)).status,200);child.kill('SIGTERM');assert.equal((await child.finished)[0],0);await gone(url);
 }finally{await cleanup(root,child);}
});
test('real desktop failure returns nonzero and cleans HTTP without exposing token',{timeout:10000},async()=>{
 const root=await fixture('fail');let child,info;
 try{child=start(root);info=await state(root);assert.equal((await child.finished)[0],1);assert.ok(!child.errors.includes('#token='));await gone(info.url);}
 finally{await cleanup(root,child,info);}
});
test('launcher death before readiness cleans pending supervisor and desktop',{timeout:10000},async()=>{
 const root=await fixture('hang');let child,info;
 try{child=start(root);info=await state(root);child.kill('SIGTERM');await child.finished;await gone(info.url);}
 finally{await cleanup(root,child,info);}
});
test('detached startup timeout and early child failure reject and reap fixture processes',{timeout:10000},async()=>{
 const root=await mkdtemp(path.join(os.tmpdir(),'diag-launch-fail-'));
 try{for(const script of ['process.exit(4);','setInterval(()=>{},1000);']){
 const entry=path.join(root,'child.cjs');await writeFile(entry,script);let child;
 await assert.rejects(launchDetached([],{entry,timeout:150,spawnFn:(...args)=>{child=spawn(...args);return child;}}),{diagCode:'DESKTOP'});
 if(child.exitCode===null && child.signalCode===null)await once(child,'exit');
 }}finally{await rm(root,{recursive:true,force:true});}
});

test('safe diagnostic log accepts only fixed codes and stays within 64 KiB',async()=>{
 const {recordDesktopFailure}=await import('../起動/desktop-log.mjs');
 const root=await mkdtemp(path.join(os.tmpdir(),'diag-safe-log-')),file=path.join(root,'errors.log');
 try{
  assert.equal(recordDesktopFailure('SECRET #token=private',file),false);
  await writeFile(file,'x'.repeat(65530));assert.equal(recordDesktopFailure('LOAD',file),true);
  const text=await readFile(file,'utf8');assert.match(text,/^\d{4}-.* Electron LOAD\n$/);assert.ok(text.length<65536);assert.ok(!text.includes('SECRET'));
 }finally{await rm(root,{recursive:true,force:true});}
});
test('failure after detach leaves a fixed safe log and closes the server',{timeout:10000},async()=>{
 const root=await fixture();let child,info;
 try{
  child=start(root);info=await state(root);assert.equal((await child.finished)[0],0);
  process.kill(info.pid,'SIGTERM');await gone(info.url);
  const text=await readFile(path.join(root,'.desktop-errors.log'),'utf8');assert.match(text,/Electron EXIT/);assert.ok(!text.includes('#token='));
  assert.match(child.output,/--foreground/);assert.match(child.output,/\.desktop-errors\.log/);
 }finally{await cleanup(root,child,info);}
});
test('probe diagnostic log retains safe structured failure fields only',async()=>{
 const {recordProbeFailure}=await import('../起動/desktop-log.mjs');
 const root=await mkdtemp(path.join(os.tmpdir(),'diag-probe-log-')),file=path.join(root,'errors.log');
 try{
  assert.equal(recordProbeFailure({reason:'SECRET'},file),false);
  assert.equal(recordProbeFailure({id:'node',reason:'nonzero_exit',args:['/private/path','--version','SECRET'],exitCode:7,signal:'SIGTERM',stderr:'SECRET',token:'SECRET'},file),true);
  const text=await readFile(file,'utf8');const record=JSON.parse(text.split('[aidiy-diag:probe] ')[1]);
  assert.deepEqual(record,{id:'node',reason:'nonzero_exit',args:['--version'],exitCode:7,signal:'SIGTERM'});
  assert.ok(!text.includes('SECRET'));assert.ok(!text.includes('/private'));
 }finally{await rm(root,{recursive:true,force:true});}
});
test('detached-mode real version failure writes safe log as well as stderr',{timeout:10000},async()=>{
 const root=await fixture();let child;
 try {
  const script=path.join(root,'probe-fixture.mjs');
  await writeFile(script,`import {runVersion} from './診断/probes.mjs';await runVersion('/definitely/missing/SECRET',['--version'],process.cwd(),{probeId:'fixture'});`);
  child=spawn(process.execPath,[script],{env:{...process.env,AIDIY_DIAG_LAUNCHER_CHILD:'1'},stdio:['ignore','ignore','pipe']});let stderr='';child.stderr.on('data',x=>stderr+=x);
  assert.equal((await once(child,'exit'))[0],0);const log=await readFile(path.join(root,'.desktop-errors.log'),'utf8');
  for(const text of [log,stderr]){assert.match(text,/aidiy-diag:probe/);assert.match(text,/spawn_error/);assert.match(text,/ENOENT/);assert.ok(!text.includes('SECRET'));}
 }finally{await cleanup(root,child);}
});

test('safe diagnostic log rejects FIFO and directory without blocking',{skip:process.platform==='win32',timeout:3000},async()=>{
 const {recordDesktopFailure}=await import('../起動/desktop-log.mjs');const root=await mkdtemp(path.join(os.tmpdir(),'diag-log-fifo-'));
 try{const fifo=path.join(root,'fifo');const command=spawn('mkfifo',[fifo]);assert.equal((await once(command,'exit'))[0],0);assert.equal(recordDesktopFailure('EXIT',fifo),false);assert.equal(recordDesktopFailure('EXIT',root),false);}finally{await rm(root,{recursive:true,force:true});}
});

test('failed launcher escalates when real supervisor ignores SIGTERM',{skip:process.platform==='win32',timeout:5000},async()=>{
 const root=await mkdtemp(path.join(os.tmpdir(),'diag-stubborn-'));let child;
 try{const entry=path.join(root,'stubborn.mjs');await writeFile(entry,"process.on('SIGTERM',()=>{});setInterval(()=>{},1000);");
 await assert.rejects(launchDetached([],{entry,timeout:150,spawnFn:(exe,args,options)=>{child=spawn(exe,args,options);return child;}}));
 assert.equal(child.signalCode,'SIGKILL');
 }finally{if(child?.exitCode===null&&!child.signalCode)child.kill('SIGKILL');await rm(root,{recursive:true,force:true});}
});
