'use strict';
const {app,BrowserWindow,session}=require('electron');
let window;
function validUrl(value) {
  const url=new URL(value);
  if(url.protocol!=='http:' || url.hostname!=='127.0.0.1' || !url.port || url.username || url.password || url.search || !/^#token=[A-Za-z0-9_-]{43}$/.test(url.hash)) throw new Error('invalid URL');
  return url;
}
async function start(value) {
  const url=validUrl(value);await app.whenReady();
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
  window.once('ready-to-show',()=>window.show());
  window.webContents.once('did-fail-load',()=>app.exit(1));
  await window.loadURL(url.href);
}
let input='';const timer=setTimeout(()=>app.exit(1),10000);
process.stdin.setEncoding('utf8');process.stdin.on('data',chunk=>{input+=chunk;if(input.length>4096)app.exit(1);});
process.stdin.on('end',()=>{clearTimeout(timer);try{const {url}=JSON.parse(input);input='';start(url).catch(()=>app.exit(1));}catch{app.exit(1);}});
app.on('window-all-closed',()=>app.quit());
