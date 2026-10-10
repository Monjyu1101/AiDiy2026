// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026

const {app,BrowserWindow}=require('electron');
const {audioCheck,audioRequest}=require('../panel-permissions.cjs');
app.commandLine.appendSwitch('use-fake-device-for-media-stream');

app.whenReady().then(async()=>{
 const {startServer}=await import('../server.mjs');
 const {createCoreConnection}=await import('../core-connection.mjs');
 const project=require('node:path').resolve('frontend_dev');
 const connection=createCoreConnection(project,{fetcher:async()=>({ok:true,json:async()=>({status:'OK',data:{available_models:{},モデル設定:{}}})})});
 const server=await startServer(project,0,{connection});
 const window=new BrowserWindow({show:false,webPreferences:{sandbox:true,contextIsolation:true,nodeIntegration:false}});
 const origin=new URL(server.url).origin;
 const checks=[];
 window.webContents.session.setPermissionCheckHandler((c,p,o,d)=>{const ok=audioCheck(c,window.webContents,p,o,d,origin);if(p==='media')checks.push({kind:'check',ok,details:d});return ok;});
 window.webContents.session.setPermissionRequestHandler((c,p,cb,d)=>{const ok=audioRequest(c,window.webContents,p,d,origin);checks.push({kind:'request',ok,details:d});cb(ok);});
 try {
  await connection.connect();
  await window.loadURL(server.url);
  const result=await window.webContents.executeJavaScript(`(async()=>{
   const wait=ms=>new Promise(r=>setTimeout(r,ms));
   for(let i=0;i<50&&document.getElementById('workspace').hidden;i++)await wait(100);
   document.getElementById('ai-toggle').click();await wait(1000);
   document.getElementById('ai-live-tab').click();await wait(2500);
   const f=document.querySelector('#ai-live iframe');
   const stream=await f.contentWindow.navigator.mediaDevices.getUserMedia({audio:true,video:false});
   const tracks=stream.getTracks(); const audio=tracks.length===1&&tracks[0].kind==='audio';
   document.getElementById('ai-close').click();await wait(200);
   const ended=tracks.every(t=>t.readyState==='ended');tracks.forEach(t=>t.stop());
   return {audio,ended,removed:!document.querySelector('#ai-live iframe')};
  })()`,true);
  require('node:fs').writeFileSync('frontend_dev/out/electron-panels-result.json',JSON.stringify({result,checks}));
  if(!result.audio||!result.removed||!result.ended)process.exitCode=1;
 }catch(e){require('node:fs').writeFileSync('frontend_dev/out/electron-panels-result.json',JSON.stringify({error:String(e),checks}));process.exitCode=1;}
 finally{window.destroy();connection.close();server.server.closeAllConnections();await new Promise(r=>server.server.close(r));app.quit();}
});
