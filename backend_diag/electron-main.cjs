'use strict';
const {app,BrowserWindow,session}=require('electron');
let window, failed=false;
function fail(code) {
  if(failed)return;failed=true;
  // 例外本文や loadURL の URL は返さず、固定の原因コードだけを IPC へ送る。
  if(process.connected && process.send){
    const fallback=setTimeout(()=>app.exit(1),250);fallback.unref?.();
    try{process.send({type:'diag-failed',code},()=>{clearTimeout(fallback);app.exit(1);});}catch{app.exit(1);}
  }else app.exit(1);
}
function validUrl(value) {
  const url=new URL(value);
  if(url.protocol!=='http:' || url.hostname!=='127.0.0.1' || !url.port || url.username || url.password || url.search || !/^#token=[A-Za-z0-9_-]{43}$/.test(url.hash)) throw new Error('invalid URL');
  return url;
}
async function start(value) {
  let url;try{url=validUrl(value);}catch{fail('URL');return;}
  await app.whenReady();
  // 非永続 session、preload/Node公開なし。外部遷移・権限要求は許可しない。
  const isolated=session.fromPartition('aidiy-diag-'+process.pid,{cache:false});
  isolated.setPermissionRequestHandler((_wc,_permission,callback)=>callback(false));
  isolated.setPermissionCheckHandler(()=>false);
  isolated.webRequest.onBeforeRequest((details,callback)=>{
    try {const target=new URL(details.url);callback({cancel:target.origin!==url.origin});} catch {callback({cancel:true});}
  });
  window=new BrowserWindow({width:1160,height:820,title:'AiDiy 診断',show:false,webPreferences:{session:isolated,nodeIntegration:false,contextIsolation:true,sandbox:true,webSecurity:true}});
  window.setMenuBarVisibility(false);
  window.webContents.setWindowOpenHandler(()=>({action:'deny'}));
  window.webContents.on('will-navigate',event=>event.preventDefault());
  window.webContents.on('will-redirect',event=>event.preventDefault());
  window.webContents.on('will-attach-webview',event=>event.preventDefault());
  window.once('ready-to-show',()=>{window.show();if(process.connected)process.send({type:'diag-shown'},error=>{if(error)fail('IPC');});});
  window.webContents.once('did-fail-load',(_event,_code,_description,_url,isMainFrame)=>{if(isMainFrame!==false)fail('LOAD');});
  window.webContents.once('render-process-gone',()=>fail('RENDERER'));
  try{await window.loadURL(url.href);}catch{fail('LOAD');}
}
// Electron on Windows replaces stdin with an empty EOF stream. Use the inherited Node IPC channel.
const timer=setTimeout(()=>fail('TIMEOUT'),10000);
process.once('message',message=>{
  clearTimeout(timer);
  if(message?.type!=='diag-start' || typeof message.url!=='string' || message.url.length>4096){fail('IPC');return;}
  start(message.url).catch(()=>fail('WINDOW'));
});
process.once('disconnect',()=>{clearTimeout(timer);app.quit();});
if(process.connected && process.send){
  try{process.send({type:'diag-ready'},error=>{if(error)fail('IPC');});}catch{fail('IPC');}
}else{clearTimeout(timer);fail('IPC');}
app.on('window-all-closed',()=>app.quit());
