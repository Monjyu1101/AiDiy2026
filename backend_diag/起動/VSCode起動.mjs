// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1". See LICENSE.
import {spawn} from 'node:child_process';
import {stat,realpath} from 'node:fs/promises';
import path from 'node:path';
import {catalog,resolveProgram} from '../診断/probes.mjs';
const fail=(message,status=400)=>Object.assign(new Error(message),{status});
// 導入タブと同じ探索。Windows の cmd はシェル実行せず、同梱の実体を開く。
export async function resolveVSCode({platform=process.platform,env=process.env,resolveFn=resolveProgram,statFn=stat}={}){
 const entry=(await catalog()).find(item=>item.id==='code');
 const executable=await resolveFn(entry,{platform,env});
 if(!executable)return null;
 if(platform!=='win32'||! /\.(cmd|bat)$/i.test(executable))return executable;
 const p=path.win32,root=p.dirname(p.dirname(executable));
 const names=/insiders/i.test(p.basename(executable))?['Code - Insiders.exe']:['Code.exe'];
 for(const name of names){const candidate=p.join(root,name);try{if((await statFn(candidate)).isFile())return candidate;}catch{}}
 return null;
}
export function createVSCodeLauncher({spawnFn=spawn,resolveFn=resolveVSCode,env=process.env,platform=process.platform,realpathFn=realpath,statFn=stat}={}){
 async function catalog(){let available=false;try{available=Boolean(await resolveFn({platform,env}));}catch{}
  return {id:'vscode',名前:'VS Code',種類:'editor',モード:'プロジェクトフォルダを開く',利用可能:available};
 }
 async function launch(project){
  if(typeof project!=='string'||!project.trim()||project.length>4096||/[\0\r\n]/.test(project)||!(platform==='win32'?path.win32:path).isAbsolute(project))throw fail('プロジェクトフォルダを選択してください。');
  let cwd;try{cwd=await realpathFn(project);if(!(await statFn(cwd)).isDirectory())throw Error();}catch{throw fail('フォルダが見つからないか、アクセスできません。');}
  let executable;try{executable=await resolveFn({platform,env});}catch{}
  if(!executable)throw fail('VS Code の実行ファイルが見つかりません。導入状況を確認してください。',503);
  const childEnv={...env};
  for(const key of Object.keys(childEnv))if(/^(ELECTRON_RUN_AS_NODE|NODE_OPTIONS|NODE_PATH|AIDIY_(?:DIAG_LAUNCHER_CHILD|LAUNCHER_CHILD|DIAG_SETTINGS|DIAG_RUN))$/i.test(key))delete childEnv[key];
  try{
   const child=spawnFn(executable,['--new-window',cwd],{cwd,env:childEnv,detached:true,windowsHide:true,shell:false,stdio:'ignore'});
   await new Promise((resolve,reject)=>{child.once('spawn',resolve);child.once('error',reject);});child.unref();
  }catch{throw fail('VS Code を起動できませんでした。導入状況を確認してください。',503);}
  return {受付:true,通知:''};
 }
 return {catalog,launch};
}
