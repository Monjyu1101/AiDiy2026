// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import { startServer } from './viewer/server.mjs';
import { createCoreConnection, coreTarget } from './viewer/core-connection.mjs';
import { createPanels } from './viewer/panels.mjs';
import { createRequire } from 'node:module';
import { readFile } from 'node:fs/promises';
import { basename,join } from 'node:path';
import { fileURLToPath } from 'node:url';
const require=createRequire(import.meta.url),root=fileURLToPath(new URL('.',import.meta.url)),vscodeRoot=fileURLToPath(new URL('./host/',import.meta.url));
export async function startDevelopment(project,{kind='ide',linked=false,port=0,strict=false,offline=false,provider,model,autoConnect=false,env=process.env,connection}={}){
 if(!['code','live','ide'].includes(kind))throw Error('アプリはcode / live / ideから指定してください。');
 const backend=coreTarget(root,project);
 const standalone={active:true,mode:offline?'offline':'online',connected:false,startedAt:Date.now(),backend,project:{name:basename(project),path:project}};
 connection??=kind==='ide'?createCoreConnection(project):{state:()=>standalone,close(){standalone.active=false;},connect:async()=>standalone,disconnect:()=>standalone,offline:()=>standalone};
 const files={'/':['index.html','text/html; charset=utf-8'],'/development/app.js':['app.js','text/javascript; charset=utf-8'],'/development/app.css':['app.css','text/css; charset=utf-8'],'/development/AiDiy.png':['AiDiy.png','image/png'],'/development/sending.png':['sending.png','image/png'],'/development/abort.png':['abort.png','image/png'],'/development/speaker.png':['speaker.png','image/png'],'/development/microphone.png':['microphone.png','image/png'],'/development/THIRD_PARTY_NOTICES.txt':['THIRD_PARTY_NOTICES.txt','text/plain; charset=utf-8'],'/development/LICENSE':['LICENSE','text/plain; charset=utf-8']};
 return startServer(project,port,{strict,env,connection,
  requestHandler:async(req,res,url)=>{
   if(url.pathname==='/development/config'){
    res.writeHead(200,{'content-type':'application/json','cache-control':'no-store'}).end(JSON.stringify({kind,linked,host:false,icon:'/development/AiDiy.png'}));return true;
   }
   const asset=files[url.pathname];if(!asset)return false;
   if(req.method!=='GET'){res.writeHead(405).end();return true;}
   const content=await readFile(join(root,'dist',asset[0]));
   res.writeHead(200,{'content-type':asset[1],'cache-control':'no-store','x-content-type-options':'nosniff'}).end(content);return true;
  },
  panelsFactory:(project,state)=>createPanels(project,state,async(type,folder,snapshot)=>{
   if(kind!=='ide'&&type!==kind)throw Error('このアプリでは利用できません。');
   const bundle=require(join(vscodeRoot,'dist',`aidiy_${type}`,'server.cjs'));
   if(type==='code')return bundle.単独起動(folder,backend,{offline:snapshot.mode==='offline',lockedMode:kind==='ide'||linked,keepAlive:true,provider,model});
   const vendor=provider==='openai_live'?'OPENAI':provider==='freeai_live'?'FREEAI':'GEMINI';
   const settings={...(provider?{LIVE_AI_NAME:provider}:{}),...(model?{[`LIVE_${vendor}_MODEL`]:model}:{})};
   return bundle.ライブ起動(vscodeRoot,backend,false,folder,settings,undefined,autoConnect);
  })
 });
}
