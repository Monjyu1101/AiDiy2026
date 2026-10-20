import test from 'node:test';
import assert from 'node:assert/strict';
import {EventEmitter} from 'node:events';
import {mkdtemp,mkdir,rm,readFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createCliLauncher} from '../起動/CLI起動.mjs';
import {createServer} from '../diag_main.mjs';
const ids=['claude','codex','copilot','agy','grok','opencode','aidiy_hermes'];
async function fixture(t,options={}){
 const root=await mkdtemp(join(tmpdir(),'diag-cli-fixture-')),project=join(root,`日本語 project ' & $ % ;`);await mkdir(project);
 t.after(()=>rm(root,{recursive:true,force:true,maxRetries:5}));
 const calls=[],resolved=[];
 const manager=createCliLauncher({root,resolveCli:async(id,value)=>{resolved.push({id,value});if(options.missing===id)throw Error('private path');return {executable:'/fixture/'+id};},spawnFn(command,args,opts){
  const child=new EventEmitter();child.connected=true;child.disconnect=()=>{child.connected=false;};child.kill=()=>{child.killed=true;};child.unref=()=>{};
  calls.push({command,args,opts,child});if(!options.pending)queueMicrotask(()=>child.emit('message',options.error?{launchError:'sensitive internal error'}:{launchReady:true}));return child;
 },timeout:options.timeout??500});
 return {root,project,calls,resolved,manager};
}
test('CLI catalog is fixed; availability uses resolver only, no process execution',async t=>{
 const f=await fixture(t,{missing:'grok'}),result=await f.manager.catalog();assert.deepEqual(result.対象.map(x=>x.id),ids);assert.equal(result.対象.find(x=>x.id==='grok').利用可能,false);assert.equal(f.calls.length,0);assert.equal(f.resolved.length,7);assert.ok(f.resolved.every(x=>x.value.autoApprove===true));assert.doesNotMatch(JSON.stringify(result),/executable|private path/);
});
test('all CLI launches pass only fixed id, approval, and exact cwd; omit models and shell strings',async t=>{
 const f=await fixture(t);
 for(const id of ids){const result=await f.manager.launch(id,f.project,true);assert.equal(result.受付,true);const c=f.calls.at(-1);assert.equal(c.opts.cwd,f.project);assert.equal(c.opts.shell,false);assert.equal(c.opts.detached,true);assert.equal(c.opts.env.AIDIY_LAUNCHER_CHILD,'1');assert.deepEqual(c.args,[join(f.root,'frontend_ide','launch.mjs'),'--app','term','--project',f.project,'--new-window','--cli',id,'--cli-auto-approve','--foreground']);assert.equal(c.opts.stdio.at(-1),'ipc');assert.equal(c.child.connected,false);assert.doesNotMatch(c.args.join(' '),/--model|--provider|--prompt/);}
});
test('invalid ids, unconfirmed mode, missing project and missing executable never spawn',async t=>{
 const f=await fixture(t,{missing:'grok'});
 for(const [id,path,approved,status] of [['injected;sh',f.project,true,400],['copilot',f.project,false,400],['copilot',f.project,'true',400],['copilot','',true,400],['copilot','relative',true,400],['copilot',join(f.root,'missing'),true,400],['copilot',f.project+'\n',true,400],['grok',f.project,true,503]])await assert.rejects(f.manager.launch(id,path,approved),{status});
 assert.equal(f.calls.length,0);
});
test('pending and already-open CLI duplicates are rejected or reported; closing permits a new window',async t=>{
 const f=await fixture(t,{pending:true});const first=f.manager.launch('copilot',f.project,true);while(!f.calls.length)await new Promise(resolve=>setImmediate(resolve));
 await assert.rejects(f.manager.launch('copilot',f.project,true),{status:409});f.calls[0].child.emit('message',{launchReady:true});await first;
 assert.equal((await f.manager.launch('copilot',f.project,true)).起動済み,true);assert.equal(f.calls.length,1);
 f.calls[0].child.emit('exit',0);const second=f.manager.launch('copilot',f.project,true);while(f.calls.length<2)await new Promise(resolve=>setImmediate(resolve));f.calls[1].child.emit('message',{launchReady:true});await second;assert.equal(f.calls.length,2);
});
test('startup errors and timeout fail closed, kill unfinished child and permit retry',async t=>{
 for(const options of [{error:true},{pending:true,timeout:5}]){
  const f=await fixture(t,options);for(let i=0;i<2;i++)await assert.rejects(f.manager.launch('codex',f.project,true),error=>[503,504].includes(error.status)&&!error.message.includes('sensitive'));
  assert.equal(f.calls.length,2);assert.ok(f.calls.every(x=>x.child.killed));
 }
});
test('authenticated CLI API limits body fields, confirmation, asset names and methods',async t=>{
 const f=await fixture(t);const server=createServer({token:'fixture',cliLauncher:f.manager,modelTrials:{close(){}},startManager:{close(){}}});await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));t.after(()=>new Promise(resolve=>{server.close(resolve);server.closeAllConnections();}));
 const base=`http://127.0.0.1:${server.address().port}/`,headers={Authorization:'Bearer fixture','Content-Type':'application/json'};
 assert.equal((await fetch(base+'api/CLI起動')).status,401);assert.equal((await fetch(base+'api/CLI起動',{headers})).status,200);
 for(const id of ids){const response=await fetch(base+`CLI_${id}.png`);assert.equal(response.status,200);assert.equal(response.headers.get('content-type'),'image/png');assert.deepEqual(Buffer.from(await response.arrayBuffer()),await readFile(new URL(`../ui/src/アプリ起動/CLIアイコン/${id}.png`,import.meta.url)));}
 for(const name of ['LICENSE-Octicons.txt','LICENSE-LobeHub.txt','LICENSE-OpenCode.txt']){const license=await fetch(base+name);assert.equal(license.status,200);assert.equal(license.headers.get('content-type'),'text/plain; charset=utf-8');assert.equal(await license.text(),await readFile(new URL('../ui/src/アプリ起動/CLIアイコン/'+name,import.meta.url),'utf8'));}
 const citations=await fetch(base+'LICENSE_ICONS.md');assert.equal(citations.status,200);assert.equal(await citations.text(),await readFile(new URL('../ui/src/アプリ起動/CLIアイコン/LICENSE_ICONS.md',import.meta.url),'utf8'));
 assert.equal((await fetch(base+'CLI_bad.png')).status,404);
 for(const [body,status] of [[{対象:'copilot',フォルダ:f.project},400],[{対象:'copilot',フォルダ:f.project,自動承認確認:true,model:'bad'},400],[{対象:'copilot',フォルダ:'x'.repeat(9000),自動承認確認:true},413]])assert.equal((await fetch(base+'api/CLI起動/開始',{method:'POST',headers,body:JSON.stringify(body)})).status,status);
 assert.equal((await fetch(base+'api/CLI起動/開始',{headers})).status,404);assert.equal(f.calls.length,0);
 assert.equal((await fetch(base+'api/CLI起動/開始',{method:'POST',headers,body:JSON.stringify({対象:'copilot',フォルダ:f.project,自動承認確認:true})})).status,202);assert.equal(f.calls.length,1);
});

test('missing optional Term files do not prevent Diag construction and fail only on CLI use',async()=>{
 let loads=0;const manager=createCliLauncher({loadDefinitions:async()=>{loads++;throw Error('private missing module path');}});assert.equal(loads,0);
 await assert.rejects(manager.catalog(),error=>error.status===503&&!error.message.includes('private'));assert.equal(loads,1);
});
test('missing shared CLI module returns safe actionable 503 through authenticated API',async t=>{
 const server=createServer({token:'fixture',cliLauncher:createCliLauncher({loadDefinitions:async()=>{throw Error('private filepath');}}),modelTrials:{close(){}},startManager:{close(){}}});await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));t.after(()=>new Promise(resolve=>{server.close(resolve);server.closeAllConnections();}));
 const response=await fetch(`http://127.0.0.1:${server.address().port}/api/CLI起動`,{headers:{Authorization:'Bearer fixture'}});assert.equal(response.status,503);const body=await response.json();assert.match(body.エラー,/frontend_ide/);assert.doesNotMatch(body.エラー,/private/);
});


test('Copilot uses original Octicons path geometry and retains the MIT notice separately from its label',async()=>{
 const iconRoot=new URL('../ui/src/アプリ起動/CLIアイコン/',import.meta.url);
 const source=await readFile(new URL('upstream/copilot-24.svg',iconRoot),'utf8'),display=await readFile(new URL('copilot.svg',iconRoot),'utf8');
 const paths=value=>[...value.matchAll(/<path d="([^"]+)"/g)].map(item=>item[1]);assert.equal(paths(source).length,2);assert.deepEqual(paths(display),paths(source));assert.match(display,/width="96" height="96" viewBox="0 0 24 24"/);assert.doesNotMatch(display,/<script|<image|<text|href=/i);
 const license=await readFile(new URL('LICENSE-Octicons.txt',iconRoot),'utf8');assert.match(license,/Copyright \(c\) 2026 GitHub Inc\./);assert.match(license,/Permission is hereby granted/);assert.match(license,/THE SOFTWARE IS PROVIDED "AS IS"/);
});


test('実製品アイコンは保存原本の形状と色を維持し、Hermesだけ既存AiDiy画像を使う',async()=>{
 const root=new URL('../ui/src/アプリ起動/CLIアイコン/',import.meta.url),text=async path=>(await readFile(new URL(path,root),'utf8')).replace(/\r\n/g,'\n');
 for(const [id,original] of [['claude','claude-code-color-lobe.svg'],['codex','codex-color-lobe.svg'],['grok','Grok_Logomark_Light.svg'],['opencode','opencode-logo-dark-square.svg']])assert.equal(await text(id+'.svg'),await text('upstream/'+original),id);
 const hermes=await readFile(new URL('aidiy_hermes.png',root)),original=await readFile(new URL('../../frontend_web/public/icons/AiDiy.png',import.meta.url));assert.deepEqual(hermes,original);assert.deepEqual(hermes,await readFile(new URL('upstream/AiDiy.png',root)));assert.match(await text('aidiy_hermes.svg'),/data:image\/png;base64,/);
 const notes=await text('LICENSE_ICONS.md');for(const label of ['Copilot','Claude','Codex','Grok','OpenCode','aidiy_hermes','LobeHub'])assert.ok(notes.includes(label),label);assert.doesNotMatch(notes,/取得・確認待ち|独自仮ピクトグラム/);
});
