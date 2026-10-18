import {readFile,writeFile,mkdir,rename} from 'node:fs/promises';
import {spawn,execFile} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {join} from 'node:path';
import {randomUUID} from 'node:crypto';
import {stripVTControlCharacters} from 'node:util';

const ROOT=fileURLToPath(new URL('../../',import.meta.url));
const failure=(message,status=400)=>Object.assign(new Error(message),{status});
export function validateSettings(target,value){
 const keys=Object.keys(target.初期設定);
 if(!value||typeof value!=='object'||Array.isArray(value)||Object.keys(value).length!==keys.length||keys.some(key=>typeof value[key]!=='boolean'))throw failure('起動設定は指定の項目を真偽値で設定してください。');
 return Object.fromEntries(keys.map(key=>[key,value[key]]));
}
export function createStartManager({root=ROOT,spawnFn=spawn,python,readyTimeout=180000,stopTimeout=30000}={}){
 let targets,settings,loading,writing=Promise.resolve(),busy=false,closed=false,operation='',work=Promise.resolve(),focus=null;
 const sessions=new Map(),cancelled=new Set(),logs=new Map();
 const settingsFile=join(root,'_config','AiDiy_diag_start.json'),runtime=join(root,'_AIDIY','aidiy_diag','起動');
 const log=(id,text)=>{const old=logs.get(id)||{text:'',offset:0};old.text+=stripVTControlCharacters(String(text));if(old.text.length>120000){const size=old.text.length-120000;old.offset+=size;old.text=old.text.slice(size);}logs.set(id,old);};
 async function load(){
  if(loading)return loading;
  loading=(async()=>{
   targets=JSON.parse(await readFile(join(root,'scripts','起動対象.json'),'utf8')).filter(target=>target.起動管理!==false);
   settings=Object.fromEntries(targets.map(target=>[target.id,{...target.初期設定}]));
   let saved;try{saved=JSON.parse(await readFile(settingsFile,'utf8'));}catch(error){if(error.code==='ENOENT')return;throw failure('起動設定を読み込めません。_config/AiDiy_diag_start.json を確認してください。',500);}
   if(saved?.version!==1||!saved.設定||typeof saved.設定!=='object')throw failure('保存済みの起動設定が不正です。',500);
   for(const target of targets)if(Object.hasOwn(saved.設定,target.id)){
    const value={...target.初期設定,...saved.設定[target.id]};
    if(target.id==='web')delete value['chrome_devtoolsで開く']; // 統合前の保存設定との互換。
    settings[target.id]=validateSettings(target,value);
   }
  })();
  try{return await loading;}catch(error){loading=undefined;throw error;}
 }
 function targetFor(id){const target=targets?.find(item=>item.id===id);if(!target)throw failure('起動対象が不正です。');return target;}
 async function snapshot(){await load();return {対象:targets.map(target=>({...target,設定:{...settings[target.id]},状態:sessions.get(target.id)?.state||'未起動'})),実行中:busy,通知:operation,起動表示:focus?{...focus}:null,終了時停止あり:busy||[...sessions.values()].some(session=>session.child&&!session.exited)};}
 async function save(id,value){
  await load();const target=targetFor(id),validated=validateSettings(target,value);
  const task=writing.catch(()=>{}).then(async()=>{
   const updated={...settings,[id]:validated};
   await mkdir(join(root,'_config'),{recursive:true});
   const temp=settingsFile+'.'+randomUUID()+'.tmp';
   await writeFile(temp,JSON.stringify({version:1,設定:updated},null,2)+'\n',{encoding:'utf8',flag:'wx'});
   await rename(temp,settingsFile);settings=updated;return {設定:{...validated}};
  });writing=task;return task;
 }
 async function pythonCommand(){
  if(python)return [python,[]];
  for(const [command,args] of [[process.env.DIAG_START_PYTHON||'python',[]],['python3',[]],['py',['-3']]]){
   if(await new Promise(resolve=>execFile(command,[...args,'--version'],{windowsHide:true,timeout:5000},(error,stdout)=>resolve(!error&&/^Python 3\./.test(stdout.trim())))))return [command,args];
  }throw failure('Python 3 が見つかりません。Python を導入してターミナルを開き直してください。',503);
 }
 async function stop(id,{cancel=true}={}){
  await load();targetFor(id);if(cancel)cancelled.add(id);
  const session=sessions.get(id);if(!session?.child||session.exited)return {停止済み:true};
  session.stopping=true;session.state='停止中';
  try{session.child.stdin.write(JSON.stringify({action:'stop'})+'\n');}catch{}
  let timer;
  await Promise.race([session.done,new Promise(resolve=>{timer=setTimeout(async()=>{
   if(process.platform==='win32')await new Promise(done=>execFile('taskkill.exe',['/F','/T','/PID',String(session.child.pid)],{windowsHide:true,timeout:10000},done));
   else try{process.kill(-session.child.pid,'SIGTERM');}catch{}
   resolve();
  },stopTimeout);})]);clearTimeout(timer);
  if(!session.exited){let grace;await Promise.race([session.done,new Promise(resolve=>{grace=setTimeout(resolve,5000);})]);clearTimeout(grace);}
  if(!session.exited)throw failure('停止の完了を確認できませんでした。コンソールを確認してください。',500);
  return {停止済み:true};
 }
 async function startOne(id,runSettings){
  const target=targetFor(id);await stop(id,{cancel:false});
  if(closed||cancelled.has(id))return;
  const [command,args]=await pythonCommand();if(closed||cancelled.has(id))return;
  const run=randomUUID();await mkdir(runtime,{recursive:true});
  const temp=join(runtime,id+'.'+run+'.tmp');await writeFile(temp,JSON.stringify({run}),'utf8');await rename(temp,join(runtime,id+'.json'));
  if(closed||cancelled.has(id))return;
  const session={state:'起動中',child:null,exited:false,stopping:false};sessions.set(id,session);
  log(id,'\n──────── '+new Date().toLocaleString('ja-JP')+' 再起動 ────────\npython '+target.フォルダ+'/_start.py\n');
  let readyResolve,readyReject,doneResolve,ready=false;
  const started=new Promise((resolve,reject)=>{readyResolve=resolve;readyReject=reject;});
  session.done=new Promise(resolve=>{doneResolve=resolve;});
  const env={...process.env,PYTHONIOENCODING:'utf-8',PYTHONUNBUFFERED:'1',AIDIY_DIAG_RUN:run,AIDIY_DIAG_SETTINGS:JSON.stringify(runSettings)};
  delete env.ELECTRON_RUN_AS_NODE;
  const child=spawnFn(command,[...args,'-u','-X','utf8',join(root,target.フォルダ,'_start.py'),'--diag-start',id],{cwd:root,env,stdio:['pipe','pipe','pipe'],shell:false,windowsHide:true,detached:process.platform!=='win32'});session.child=child;
  let pending='';child.stdout.setEncoding('utf8');child.stderr.setEncoding('utf8');
  child.stdout.on('data',chunk=>{
   pending+=chunk;
   if(pending.length>256000){pending='';session.state='エラー';log(id,'起動ログの形式が不正です。\n');readyReject(failure('起動ログを読み込めませんでした。',500));return;}
   let index;while((index=pending.indexOf('\n'))>=0){const line=pending.slice(0,index);pending=pending.slice(index+1);if(!line)continue;
    let event;try{event=JSON.parse(line);}catch{log(id,line+'\n');continue;}
    if(event.type==='log')log(id,event.data);
    else if(event.type==='status'&&['確認中','再起動中','起動中','稼働中','再起動待ち','停止中','停止済み'].includes(event.state))session.state=event.state;
    else if(event.type==='ready'){session.state='稼働中';ready=true;readyResolve();}
    else if(event.type==='error'){session.state='エラー';log(id,'エラー: '+event.message+'\n');readyReject(failure(event.message||'起動に失敗しました。',500));}
   }
  });
  child.stderr.on('data',chunk=>log(id,chunk));
  child.stdin.on('error',()=>{});
  child.once('error',()=>{session.state='エラー';log(id,'Python の起動に失敗しました。\n');readyReject(failure('Python の起動に失敗しました。',503));});
  child.once('close',code=>{session.exited=true;if(session.state!=='エラー')session.state=session.stopping||code===0?'停止済み':'エラー';if(!ready)readyReject(failure('起動が完了する前にプロセスが終了しました。',500));log(id,'\n[コンソール終了: '+String(code)+']\n');doneResolve();});
  const timeout=setTimeout(()=>readyReject(failure('起動完了の確認がタイムアウトしました。',504)),readyTimeout);
  try{await started;}catch(error){await stop(id);throw error;}finally{clearTimeout(timeout);}
 }
 async function restart(id){
  await load();await writing.catch(()=>{});if(closed)throw failure('起動画面を終了しています。',409);if(busy)throw failure('起動処理の完了を待ってください。',409);
  const ids=id?[targetFor(id).id]:targets.filter(target=>settings[target.id].起動対象).map(target=>target.id);
  if(!ids.length)throw failure('起動対象を選択してください。');
  if(id){const old=logs.get(id)||{text:'',offset:0};logs.set(id,{text:'',offset:old.offset+old.text.length+1});}
  const selected=structuredClone(settings);cancelled.clear();busy=true;operation='設定した順序で起動します。';
  work=(async()=>{
   try{for(const current of ids){if(closed)break;if(cancelled.has(current))continue;focus={対象:current,実行ID:randomUUID()};operation=targetFor(current).名前+' を再起動しています。';await startOne(current,selected[current]);}if(!closed)operation='起動処理が完了しました。';}
   catch(error){operation=error.message||'起動に失敗したため後続の起動を中止しました。';}
   finally{busy=false;}
  })();return {受理:true};
 }
 async function logSnapshot(id,cursor=0){await load();targetFor(id);if(!Number.isSafeInteger(cursor)||cursor<0)throw failure('ログ位置が不正です。');const value=logs.get(id)||{text:'',offset:0},end=value.offset+value.text.length;return {対象:id,ログ:value.text.slice(Math.max(0,Math.min(cursor,end)-value.offset)),位置:end,切替:cursor<value.offset||cursor>end};}
 async function close(){closed=true;await Promise.allSettled([...sessions.keys()].map(stop));await work;}
 return {snapshot,save,restart,stop,logSnapshot,close,settled:()=>work};
}
