// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import { startServer } from './viewer/server.mjs';
import { createCoreConnection, coreTarget } from './viewer/core-connection.mjs';
import { createTaskTeamProxy } from './タスクチーム/api-proxy.mjs';
import { createPanels } from './viewer/panels.mjs';
import { createRequire } from 'node:module';
import { readFile } from 'node:fs/promises';
import { basename,join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createAISearch } from './ファイル機能/ai-search.mjs';
import { createFileAnalysis } from './ファイル機能/file-analysis.mjs';
import { startTerminal } from './aidiy_term/terminal.mjs';
import { validateCliOptions, resolveCliLaunch } from './aidiy_term/cli-launch.mjs';
import { createFileHistory } from './ファイル機能/file-history.mjs';
import { catppuccinAsset } from './src/ファイル閲覧/ファイルアイコン.js';
const require=createRequire(import.meta.url),root=fileURLToPath(new URL('.',import.meta.url)),vscodeRoot=fileURLToPath(new URL('./host/',import.meta.url));
export async function startDevelopment(project,{kind='ide',linked=false,port=0,strict=false,offline=false,provider,model,cli,cliAutoApprove=false,onCliStarted,onCliAbandoned,autoConnect=false,env=process.env,connection,aiSearchOptions,fileAnalysisOptions,explorerOptions}={}){
 if(!['code','live','ide','term','task','team'].includes(kind))throw Error('アプリはcode / live / ide / term / task / teamから指定してください。');
 validateCliOptions(kind,{cli,cliAutoApprove,provider,model});
 if(cli)await resolveCliLaunch(cli,{autoApprove:cliAutoApprove,env});
 const taskTeam=['task','team'].includes(kind);
 const taskTeamProxy=taskTeam?createTaskTeamProxy(root,project):undefined;
 const backend=coreTarget(root,project);
 const standalone={active:true,mode:offline?'offline':'online',connected:false,startedAt:Date.now(),backend,project:{name:basename(project),path:project}};
 connection??=kind==='ide'?createCoreConnection(project):{state:()=>standalone,close(){standalone.active=false;},connect:async()=>standalone,disconnect:()=>standalone,offline:()=>standalone};
 const files={'/':[taskTeam?'taskteam.html':'index.html','text/html; charset=utf-8'],'/development/app.js':['app.js','text/javascript; charset=utf-8'],'/development/app.css':['app.css','text/css; charset=utf-8'],'/development/AiDiy.png':['AiDiy.png','image/png'],'/development/sending.png':['sending.png','image/png'],'/development/abort.png':['abort.png','image/png'],'/development/speaker.png':['speaker.png','image/png'],'/development/microphone.png':['microphone.png','image/png'],'/development/THIRD_PARTY_NOTICES.txt':['THIRD_PARTY_NOTICES.txt','text/plain; charset=utf-8'],'/development/LICENSE':['LICENSE','text/plain; charset=utf-8']};
 files['/development/taskteam.js']=['taskteam.js','text/javascript; charset=utf-8'];
 files['/development/taskteam.css']=['taskteam.css','text/css; charset=utf-8'];
 const aiSearch=createAISearch(project,{...aiSearchOptions,state:connection.state});
 const fileAnalysis=createFileAnalysis(project,{...fileAnalysisOptions,state:connection.state});
 const fileHistory=createFileHistory(project,{state:connection.state});
 const app=await startServer(project,port,{strict,env,connection,explorerOptions,
  requestHandler:async(req,res,url)=>{
   if(taskTeamProxy && await taskTeamProxy.handle(req,res,url))return true;
   if(kind==='ide'&&await aiSearch.handle(req,res,url))return true;
   if(kind==='ide'&&await fileAnalysis.handle(req,res,url))return true;
   if(kind==='ide'&&await fileHistory.handle(req,res,url))return true;
   if(url.pathname==='/development/config'){
    res.writeHead(200,{'content-type':'application/json','cache-control':'no-store'}).end(JSON.stringify({kind,linked,host:false,...(taskTeam?{taskTeamBase:'/taskteam-api'}:{}),icon:'/development/AiDiy.png'}));return true;
   }
   const iconAsset=url.pathname.startsWith('/development/')?catppuccinAsset(url.pathname.slice('/development/'.length)):undefined;
   const asset=Object.hasOwn(files,url.pathname)?files[url.pathname]:iconAsset;if(!asset){if(taskTeam){res.writeHead(404).end();return true;}return false;}
   if(req.method!=='GET'){res.writeHead(405).end();return true;}
   const content=await readFile(join(root,'dist',asset[0]));
   res.writeHead(200,{'content-type':asset[1],'cache-control':'no-store','x-content-type-options':'nosniff',...(iconAsset?{'content-security-policy':"default-src 'none'; sandbox"}:{})}).end(content);return true;
  },
  panelsFactory:(project,state)=>createPanels(project,state,async(type,folder,snapshot)=>{
   if(kind!=='ide'&&type!==kind)throw Error('このアプリでは利用できません。');
   if(type==='term')return startTerminal(folder,{env,cli,cliAutoApprove,onCliStarted,onCliAbandoned});
   const bundle=require(join(vscodeRoot,'dist',`aidiy_${type}`,'server.cjs'));
   if(type==='code')return bundle.単独起動(folder,backend,{offline:snapshot.mode==='offline',lockedMode:kind==='ide'||linked,keepAlive:true,provider,model});
   const vendor=provider==='openai_live'?'OPENAI':provider==='freeai_live'?'FREEAI':'GEMINI';
   const settings={...(provider?{LIVE_AI_NAME:provider}:{}),...(model?{[`LIVE_${vendor}_MODEL`]:model}:{})};
   return bundle.ライブ起動(vscodeRoot,backend,false,folder,settings,undefined,autoConnect);
  })
 });
 app.server.once('close',()=>{taskTeamProxy?.close();aiSearch.close();fileAnalysis.close();});
 const close=app.close;app.close=async()=>{taskTeamProxy?.close();aiSearch.close();fileAnalysis.close();await close();};
 return app;
}
