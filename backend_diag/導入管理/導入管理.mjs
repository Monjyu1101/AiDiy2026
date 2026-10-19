// 明示操作専用の導入管理。登録済みの固定プロバイダーだけを実行します。
import {spawn,execFile} from 'node:child_process';
import {readFile,realpath,stat,lstat,mkdtemp,writeFile,rm,open,unlink} from 'node:fs/promises';
import {randomUUID,createHash} from 'node:crypto';
import {stripVTControlCharacters} from 'node:util';
import {StringDecoder} from 'node:string_decoder';
import path from 'node:path';
import os from 'node:os';
import {resolveProgram,probe} from '../診断/probes.mjs';
import {WINGET_PACKAGES,inspectWinget,executeWinget} from './winget.mjs';
import {inspectAntigravity,executeAntigravity} from './antigravity.mjs';

// _setup.py の共通セットアップと同じ4パッケージ。クライアントから名前・コマンドを受け取らない。
export const NPM_PACKAGES=Object.freeze({claude:'@anthropic-ai/claude-code',codex:'@openai/codex',copilot:'@github/copilot',opencode:'opencode-ai'});
const packageFor=id=>typeof id==='string'&&Object.hasOwn(NPM_PACKAGES,id)?NPM_PACKAGES[id]:null;
const ACTIONS=['導入','再導入','削除'];
const providerFor=id=>packageFor(id)?'npm':typeof id==='string'&&Object.hasOwn(WINGET_PACKAGES,id)?'winget':id==='agy'?'antigravity':null;
const affectedIds=id=>['ffmpeg','ffprobe','ffplay'].includes(id)?['ffmpeg','ffprobe','ffplay']:[id];
const failure=(message,status=400)=>Object.assign(new Error(message),{status});
const noop=()=>{};
export const LOG_LIMIT=120000;

// 複数の Diag からも同じ導入先を同時変更しない。異常終了で残ったロックを推測で削除しない。
export async function acquireInstallLock(prefix,{platform=process.platform,directory=os.tmpdir()}={}) {
  const resolved=await realpath(prefix).catch(()=>path.resolve(prefix));
  const key=createHash('sha256').update(platform==='win32'?resolved.toLowerCase():resolved).digest('hex').slice(0,32);
  const file=path.join(directory,`aidiy-npm-${key}.lock`);
  let handle;
  try{handle=await open(file,'wx',0o600);await handle.writeFile(String(process.pid));}
  catch(error){if(handle){await handle.close();await unlink(file).catch(noop);}throw failure(error.code==='EEXIST'?'同じ導入先で別の操作が実行中、または前回の停止確認が必要です。':'導入操作の排他ロックを作成できません。',409);}
  let released=false;return async()=>{if(released)return;released=true;await handle.close();await unlink(file);};
}

export function installEnvironment(env=process.env,{discovery=false}={}) {
  const output={};
  for(const [key,value] of Object.entries(env))if(/^(PATH|PATHEXT|HOME|USERPROFILE|APPDATA|LOCALAPPDATA|TEMP|TMP|TMPDIR|SYSTEMROOT|WINDIR|SYSTEMDRIVE|COMSPEC|PROGRAMFILES(?:\(X86\))?|HTTPS?_PROXY|ALL_PROXY|NO_PROXY|NODE_EXTRA_CA_CERTS|NODE_USE_ENV_PROXY)$/i.test(key)||(discovery&&/^NPM_CONFIG_(PREFIX|USERCONFIG|GLOBALCONFIG)$/i.test(key)))output[key]=value;
  return {...output,NO_COLOR:'1',CI:'1',DO_NOT_TRACK:'1'};
}
export function safeInstallLog(text,env=process.env) {
  let value=stripVTControlCharacters(String(text)).replace(/\r(?!\n)/g,'\n').replace(/[\x00-\x08\x0b-\x1f\x7f]/g,'');
  for(const [key,secret] of Object.entries(env))if(/token|secret|password|api.?key|authorization/i.test(key)&&typeof secret==='string'&&secret.length>=6)value=value.split(secret).join('[非表示]');
  return value.replace(/(https?:\/\/)[^\s/@]+@/gi,'$1[非表示]@').replace(/(Bearer\s+)[\w.+/=-]+/gi,'$1[非表示]').replace(/((?:_authToken|password|token)\s*[=:]\s*)[^\s]+/gi,'$1[非表示]');
}

// shell は使用しない。中止・期限超過後も終了確認まで待ち、停止未確認では排他を解除しない。
export function runInstallCommand({executable,args,cwd,env,signal,onData=noop,onUncertain=noop,timeout=300000,outputLimit=4*1024*1024,spawnFn=spawn,platform=process.platform,killTree,isTreeRunning,windowsVerbatimArguments=false}) {
  return new Promise(resolve=>{
    let child,done=false,timedOut=false,stopped=false,overflow=false,processError=false,parentClosed=false,treeKilled=false,closeCode=null,bytes=0,timer,forceTimer,uncertainTimer,treeTimer;
    const treeGone=()=>{
      if(!child?.pid)return true;
      if(isTreeRunning){try{return !isTreeRunning(child);}catch{return false;}}
      if(platform==='win32')return !stopped||treeKilled;
      try{process.kill(-child.pid,0);return false;}catch(error){return error.code==='ESRCH';}
    };
    const check=()=>{
      if(done||!parentClosed)return;
      if(treeGone()){finish(closeCode,processError);return;}
      clearTimeout(treeTimer);treeTimer=setTimeout(check,100);
    };
    const kill=force=>{
      if(!child?.pid)return;
      if(killTree){try{Promise.resolve(killTree(child,force)).then(result=>{if(result!==false)treeKilled=true;check();},noop);}catch{}return;}
      if(platform==='win32'){
        const taskkill=path.join(env?.SystemRoot||env?.SYSTEMROOT||process.env.SystemRoot||'C:\\Windows','System32','taskkill.exe');
        execFile(taskkill,['/PID',String(child.pid),'/T','/F'],{windowsHide:true,timeout:5000},error=>{if(!error)treeKilled=true;check();});
      }else try{process.kill(-child.pid,force?'SIGKILL':'SIGTERM');}catch{}
    };
    const stop=()=>{if(done||stopped)return;stopped=true;kill(false);forceTimer=setTimeout(()=>kill(true),1000);uncertainTimer=setTimeout(()=>{if(!done)onUncertain();},6000);};
    const finish=(code,error=false)=>{if(done)return;done=true;clearTimeout(timer);clearTimeout(forceTimer);clearTimeout(uncertainTimer);clearTimeout(treeTimer);signal?.removeEventListener('abort',stop);resolve({code,error,cancelled:Boolean(signal?.aborted),timedOut,overflow});};
    if(signal?.aborted){finish(null);return;}
    try{child=spawnFn(executable,args,{cwd,env,shell:false,windowsHide:true,...(platform==='win32'&&windowsVerbatimArguments?{windowsVerbatimArguments:true}:{}),detached:platform!=='win32',stdio:['ignore','pipe','pipe']});}
    catch{finish(null,true);return;}
    signal?.addEventListener('abort',stop,{once:true});
    for(const stream of [child.stdout,child.stderr])if(stream){
      const decoder=new StringDecoder('utf8');
      stream.on('data',chunk=>{bytes+=Buffer.byteLength(chunk);if(bytes>outputLimit){overflow=true;stop();return;}onData(decoder.write(Buffer.isBuffer(chunk)?chunk:Buffer.from(chunk)));});
      stream.once('end',()=>{if(!overflow)onData(decoder.end());});
    }
    child.once('error',()=>{processError=true;if(child.pid)stop();else finish(null,true);});
    child.once('close',code=>{parentClosed=true;closeCode=code;check();});
    timer=setTimeout(()=>{timedOut=true;stop();},timeout);
    if(signal?.aborted)stop();
  });
}

export async function findNpm({env=process.env,platform=process.platform,resolve=resolveProgram,run=runInstallCommand}={}) {
  const selected=await resolve({id:'npm',commands:['npm','npm.cmd']},{env,platform});
  if(!selected)throw failure('npm が見つかりません。Node.js / npm を導入してから再確認してください。',409);
  const cli=platform==='win32'?path.join(path.dirname(selected),'node_modules','npm','bin','npm-cli.js'):await realpath(selected);
  if(path.basename(cli)!=='npm-cli.js')throw failure('npm の固定 CLI 本体を確認できません。',409);
  const manifest=JSON.parse(await readFile(path.join(path.dirname(cli),'..','package.json'),'utf8'));
  if(manifest.name!=='npm')throw failure('npm の配置を確認できません。',409);
  const environment=installEnvironment(env,{discovery:true});
  const read=async args=>{
    let text='';const result=await run({executable:process.execPath,args:[cli,...args],cwd:os.tmpdir(),env:environment,timeout:10000,outputLimit:65536,onData:chunk=>text+=chunk});
    if(result.code!==0||result.error||result.timedOut||result.overflow)throw failure('npm の導入先を確認できません。',409);
    const value=text.trim();if(!path.isAbsolute(value)||value.includes('\n')||value.includes('\r'))throw failure('npm の導入先が不正です。',409);
    return value;
  };
  const prefix=await read(['prefix','--global','--loglevel=error']);
  const root=await read(['root','--global','--loglevel=error']);
  // 異なる導入先を推測で操作しない。
  const expected=platform==='win32'?path.join(prefix,'node_modules'):path.join(prefix,'lib','node_modules');
  if(path.resolve(root)!==path.resolve(expected))throw failure('npm の導入先が標準構成ではないため、自動操作しません。',409);
  return {executable:process.execPath,cli,prefix,root};
}

export async function npmCapability(entry,npm,{env=process.env,platform=process.platform,resolve=resolveProgram}={}) {
  const pkg=packageFor(entry.id);
  if(!pkg)return {id:entry.id,操作:[],理由:'安全な導入・削除コマンドが登録されていません。'};
  const base={id:entry.id,パッケージ:pkg,説明:'npm のグローバルパッケージだけを操作します。認証・設定・履歴は削除しません。'};
  const executable=await resolve(entry,{env,platform});
  const directory=path.join(npm.root,...pkg.split('/'));
  let manifest;
  try{manifest=JSON.parse(await readFile(path.join(directory,'package.json'),'utf8'));}
  catch(error){
    if(error.code==='ENOENT'&&!executable){
      try{await lstat(directory);}catch(missing){if(missing.code==='ENOENT')return {...base,操作:['導入']};}
    }
    return {...base,操作:[],理由:executable?'npm 管理外の実行ファイルのため、自動操作しません。':'導入済みパッケージの所有情報を確認できません。'};
  }
  if(manifest.name!==pkg)return {...base,操作:[],理由:'パッケージの所有情報が一致しません。'};
  const realRoot=await realpath(npm.root),realDirectory=await realpath(directory);
  const relativeDirectory=path.relative(realRoot,realDirectory);
  if(!relativeDirectory||relativeDirectory.startsWith('..')||path.isAbsolute(relativeDirectory))return {...base,操作:[],理由:'npm link 等の外部配置は自動操作しません。'};
  // 欠損したランチャーも、所有が確認できるパッケージとして再導入・削除できる。
  if(!executable)return {...base,操作:['再導入','削除']};
  const bins=typeof manifest.bin==='string'?{[pkg.split('/').pop()]:manifest.bin}:manifest.bin;
  if(!bins||typeof bins!=='object')return {...base,操作:[],理由:'実行ファイルの所有元を確認できません。'};
  for(const [name,relative] of Object.entries(bins)){
    if(typeof relative!=='string'||!/^[-\w.]+$/.test(name)||path.isAbsolute(relative))continue;
    const target=path.resolve(directory,relative),within=path.relative(directory,target);
    if(within.startsWith('..')||path.isAbsolute(within))continue;
    try{
      const realTarget=await realpath(target),relativeTarget=path.relative(realDirectory,realTarget);
      if(!relativeTarget||relativeTarget.startsWith('..')||path.isAbsolute(relativeTarget))continue;
      if(await realpath(executable)===realTarget)return {...base,操作:['再導入','削除']};
      if(platform==='win32'&&['', '.cmd', '.ps1'].some(ext=>path.resolve(executable).toLowerCase()===path.join(npm.prefix,name+ext).toLowerCase())){
        const shim=(await readFile(executable,'utf8')).split(/\r?\n/).filter(line=>!/^\s*(?:@?rem\b|::|#)/i.test(line)).join('\n').replaceAll('\\','/').toLowerCase();
        const packageTarget=`node_modules/${pkg}/${relative.replaceAll('\\','/')}`.toLowerCase();
        const pattern=executable.toLowerCase().endsWith('.cmd')?/"%(?:~dp0|dp0%)\/([^"\r\n]+)"\s+%\*/g:executable.toLowerCase().endsWith('.ps1')?/"\$basedir\/([^"\r\n]+)"\s+\$args/g:/"\$basedir\/([^"\r\n]+)"\s+"\$@"/g;
        const targets=[...shim.matchAll(pattern)].map(match=>match[1]);
        if((await stat(target)).isFile()&&targets.length&&targets.every(value=>value===packageTarget))return {...base,操作:['再導入','削除']};
      }
    }catch{}
  }
  return {...base,操作:[],理由:'検出された実行ファイルは別の導入元です。元の方法で管理してください。'};
}

export function npmCommands(npm,id,action,configFile) {
  const pkg=packageFor(id);if(!pkg||!ACTIONS.includes(action))throw failure('未対応の導入操作です。');
  const options=['--global',`--prefix=${npm.prefix}`,'--registry=https://registry.npmjs.org/',`--userconfig=${configFile}`,`--globalconfig=${configFile}.global`,'--no-audit','--no-fund','--no-update-notifier','--foreground-scripts'];
  const steps=action==='再導入'?['uninstall','install']:[action==='削除'?'uninstall':'install'];
  return steps.map(step=>({executable:npm.executable,args:[npm.cli,step,...options,pkg],表示:`npm ${step} --global ${pkg}`}));
}

export function createInstallManager({entries,probeFn=probe,onResult=()=>({}),env=process.env,platform=process.platform,findNpmFn=findNpm,capabilityFn=npmCapability,inspectWingetFn=inspectWinget,executeWingetFn=executeWinget,inspectAntigravityFn=inspectAntigravity,executeAntigravityFn=executeAntigravity,run=runInstallCommand,timeout=300000,acquireLock=acquireInstallLock}={}) {
  let current=null,controller=null,task=null,closed=false,cache=null,loading=null,generation=0;
  const busy=()=>Boolean(current?.実行中);
  const append=text=>{if(current)current.raw=(current.raw+String(text)).slice(-LOG_LIMIT*2);};
  async function inspect(){
    let npm,reason,winget,antigravity;
    if(entries.some(entry=>packageFor(entry.id)))try{npm=await findNpmFn({env,platform,run});}catch(error){reason=error.status?error.message:'npm の導入先を確認できません。';}
    const windowsEntries=entries.filter(entry=>providerFor(entry.id)==='winget');
    if(windowsEntries.length)try{winget=await inspectWingetFn({entries:windowsEntries,env:installEnvironment(env),platform,run});}catch{winget={items:windowsEntries.map(entry=>({id:entry.id,操作:[],理由:'WinGet の導入元を確認できません。'}))};}
    const agy=entries.find(entry=>entry.id==='agy');
    if(agy)try{antigravity=await inspectAntigravityFn(agy,{env:installEnvironment(env),platform,run});}catch{antigravity={item:{id:'agy',操作:[],理由:'Antigravity の導入元を確認できません。'}};}
    const items=await Promise.all(entries.map(async entry=>{
      const provider=providerFor(entry.id);
      if(provider==='winget')return winget.items.find(item=>item.id===entry.id)||{id:entry.id,操作:[],理由:'WinGet の導入元を確認できません。'};
      if(provider==='antigravity')return antigravity.item;
      if(provider!=='npm')return {id:entry.id,操作:[],理由:'安全な導入・削除コマンドが登録されていません。'};
      if(!npm)return {id:entry.id,パッケージ:NPM_PACKAGES[entry.id],操作:[],理由:reason};
      try{return await capabilityFn(entry,npm,{env,platform});}catch{return {id:entry.id,操作:[],理由:'導入元を確認できません。'};}
    }));
    return {npm,winget:winget?.context,antigravity:antigravity?.context,items};
  }
  async function capabilities(){
    if(cache)return cache;
    if(!loading){const version=generation;loading=inspect().then(value=>{if(version===generation)cache=value;}).finally(()=>{loading=null;});}
    await loading;return cache||capabilities();
  }
  function publicJob(){if(!current)return null;const {raw,...rest}=current;return {...rest,ログ:safeInstallLog(raw,env).slice(-LOG_LIMIT)};}
  async function snapshot(){
    const state=busy()?cache:await capabilities();
    return {項目:state?.items||entries.map(entry=>({id:entry.id,操作:[],理由:'導入元を確認しています。'})),実行:publicJob()};
  }
  function invalidate(){if(!busy()){cache=null;generation++;}}
  const ensureAllowed=(state,entry,action)=>{
    if(!state.items.find(item=>item.id===entry.id)?.操作?.includes(action))throw failure('導入状況または所有元が変わりました。操作せず再確認します。',409);
  };
  async function execute(entry,action){
    let directory,releaseLock,status='完了',message='操作が完了しました。';
    const provider=providerFor(entry.id);
    const onUncertain=()=>{current.状態='停止未確認';current.説明='停止の完了を確認できません。実行中の処理が終了するまで新しい操作はできません。';};
    const operationRun=async command=>{
      if(command.表示)append(`$ ${command.表示}\n`);
      const result=await run({...command,platform,cwd:command.cwd||directory,env:command.env||installEnvironment(env),signal:controller.signal,timeout:command.timeout??timeout,onData:command.onData||append,onUncertain});
      // 変更後の読み取り照会（未導入等のコード）で、実操作の終了コードを上書きしない。
      if(command.表示||!command.onData||command.onData===append)current.終了コード=result.code;
      return result;
    };
    const checkedRun=async command=>{
      const result=await operationRun(command);
      if(result.cancelled||controller.signal.aborted)throw failure('操作を中止しました。');
      if(result.timedOut)throw failure('実行時間の上限に達したため停止しました。');
      if(result.overflow)throw failure('出力の上限に達したため停止しました。');
      if(result.error||result.code!==0)throw failure(`コマンドが失敗しました（終了コード ${result.code??'起動不可'}）。`);
      return result;
    };
    try{
      await loading;
      let fresh=await inspect();cache=fresh;ensureAllowed(fresh,entry,action);
      if(controller.signal.aborted)throw failure('操作を中止しました。');
      const context=fresh[provider],lockKey=context?.lockKey||context?.prefix;
      if(!lockKey)throw failure('導入先の排他を確認できません。',409);
      releaseLock=await acquireLock(lockKey,{platform});
      // ロック取得を待つ間に別の操作が完了していても、古い所有判定では実行しない。
      if(provider==='npm'){
        const lockedCapability=await capabilityFn(entry,fresh.npm,{env,platform});
        if(!lockedCapability.操作?.includes(action))throw failure('導入状況または所有元が変わりました。操作せず再確認します。',409);
      }else{
        fresh=await inspect();cache=fresh;ensureAllowed(fresh,entry,action);
        const lockedKey=fresh[provider]?.lockKey||fresh[provider]?.prefix;
        if(lockedKey!==lockKey)throw failure('導入先が変わりました。操作せず再確認します。',409);
      }
      if(controller.signal.aborted)throw failure('操作を中止しました。');
      directory=await mkdtemp(path.join(os.tmpdir(),'aidiy-install-'));
      if(provider==='npm'){
        const configFile=path.join(directory,'npmrc');await writeFile(configFile,'',{mode:0o600});await writeFile(configFile+'.global','',{mode:0o600});
        for(const command of npmCommands(fresh.npm,entry.id,action,configFile))await checkedRun(command);
      }else{
        const executeProvider=provider==='winget'?executeWingetFn:executeAntigravityFn;
        // 実コマンドは共通の期限・中止・終了確認を通す。プロバイダー内の照会も実行中として排他する。
        const result=await executeProvider(entry,action,fresh[provider],{env:installEnvironment(env),platform,run:operationRun,signal:controller.signal,timeout,cwd:directory,onData:append,onUncertain});
        if(result?.code!==undefined)current.終了コード=result.code;
        if(controller.signal.aborted)throw failure('操作を中止しました。');
      }
    }catch(error){status=controller.signal.aborted?'中止':'失敗';message=error.status?error.message:'導入操作でエラーが発生しました。';}
    finally{
      if(directory)await rm(directory,{recursive:true,force:true}).catch(()=>append('一時ファイルの後片付けに失敗しました。\n'));
      current.状態='確認中';append(`\n${message}\n導入状況を再確認します。\n`);
      const checked=[];
      // FFmpeg は一度のパッケージ操作の後、3つとも個別確認と全く同じ probe / 結果反映を呼ぶ。
      for(const target of entries.filter(item=>affectedIds(entry.id).includes(item.id))){
        try{
          const result=await probeFn(target);checked.push(result);Object.assign(current,onResult(result));
          if(target.id===entry.id)current.結果=result;
          append(`確認結果 [${target.name||target.id}]: ${result.状態}\n${result.説明||''}\n`);
          if(status==='完了'&&((action==='削除'&&result.パス)||(action!=='削除'&&result.状態!=='OK'))){status='失敗';message=action==='削除'?'別の導入先を含め、実行ファイルが残っています。確認結果を参照してください。':'コマンドは終了しましたが、導入を確認できませんでした。PATH の反映や確認結果を参照してください。';append(`${message}\n`);}
        }catch{status='失敗';message='操作後の導入確認に失敗しました。確認ボタンで再試行してください。';append(`${target.name||target.id}: ${message}\n`);}
      }
      current.結果一覧=checked;
      cache=null;try{await capabilities();}catch{}
      if(releaseLock)await releaseLock().catch(()=>{status='失敗';message='導入操作の排他ロックを解除できませんでした。';append(`${message}\n`);});
      current.状態=status;current.説明=message;current.終了日時=new Date().toISOString();current.実行中=false;
    }
  }
  async function start(id,action){
    const entry=entries.find(item=>item.id===id);
    if(!entry||!providerFor(id)||!ACTIONS.includes(action))throw failure('未対応の導入操作です。',404);
    if(closed||busy())throw failure('導入操作の実行中です。完了後に再試行してください。',409);
    controller=new AbortController();current={実行ID:randomUUID(),対象:id,関連項目:affectedIds(id),操作:action,状態:'実行中',実行中:true,開始日時:new Date().toISOString(),終了日時:null,raw:`${entry.name||id}: ${action}\n導入元を確認しています。\n`};
    task=execute(entry,action);return snapshot();
  }
  async function cancel(id){
    if(!current||current.実行ID!==id)throw failure('実行が見つかりません。',404);
    if(busy()){append('\n中止を要求しました。終了確認後に導入状況を再確認します。\n');controller.abort();}
    return snapshot();
  }
  async function close(){closed=true;controller?.abort();await task;}
  return {snapshot,start,cancel,busy,invalidate,close};
}
