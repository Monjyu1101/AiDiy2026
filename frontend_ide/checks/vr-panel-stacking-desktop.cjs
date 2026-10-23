// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
// 実行: frontend_avatar/node_modules/.bin/electron --ozone-platform=headless frontend_ide/checks/vr-panel-stacking-desktop.cjs
// APIの実呼出し・独立窓・イベント後の制御を確認する。headlessはWindowsの実Z-orderを証明しない。
const {app,BrowserWindow}=require('electron');
const assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {createWindowPins}=require('../デスクトップ/最前面ピン.cjs');
const {createVRPanelStacking}=require('../デスクトップ/VRパネル前面.cjs');
const directory=fs.mkdtempSync(path.join(os.tmpdir(),'aidiy-vr-stacking-'));
app.setPath('userData',path.join(directory,'profile'));app.disableHardwareAcceleration();
app.on('window-all-closed',()=>{});
app.once('quit',()=>{fs.rmSync(directory,{recursive:true,force:true,maxRetries:2});});
setTimeout(()=>{console.error('VR stacking smoke timed out');app.exit(1);},20000).unref();
const pause=()=>new Promise(resolve=>setTimeout(resolve,100));
app.whenReady().then(async()=>{
 const windows=new Map(),calls=[],errors=[];let active=false;
 const pins=createWindowPins(),stack=createVRPanelStacking({windows,isActive:()=>active,onError:error=>errors.push(error.message)});
 async function create(kind,owner){
  const window=new BrowserWindow({show:false,width:640,height:400,frame:false,webPreferences:{sandbox:true,contextIsolation:true,nodeIntegration:false}});
  const record={kind,owner,window};windows.set(window.webContents,record);
  const moveAbove=window.moveAbove.bind(window);window.moveAbove=id=>{calls.push([kind,id]);moveAbove(id);};
  pins.register(window,{pinned:!!owner,locked:!!owner&&active});stack.register(record);
  await window.loadURL('data:text/html,'+encodeURIComponent(`<body style="background:#142139;color:white;font:24px sans-serif"><h1>${kind}</h1>VR relative stacking API fixture. Not a production UI or OS stacking-order proof.</body>`));
  window.show();await pause();return record;
 }
 try{
  const ide=await create('ide'),explorer=await create('explorer',ide),routes=await create('panel-routes',ide);
  assert.equal(calls.length,0);active=true;
  for(const record of windows.values())pins.setLocked(record.window,true);
  stack.refresh(ide);await pause();assert.ok(calls.some(([kind])=>kind==='explorer'));assert.ok(calls.some(([kind])=>kind==='panel-routes'));
  for(const event of ['focus','show','restore','maximize','unmaximize']){const before=calls.length;ide.window.emit(event);await pause();assert.ok(calls.length>before,event);}
  for(const record of [ide,explorer,routes])assert.equal(record.window.getParentWindow(),null);
  const originalFocus=BrowserWindow.getFocusedWindow();stack.refresh(ide);await pause();assert.equal(BrowserWindow.getFocusedWindow(),originalFocus,'相対順変更でフォーカスを盗まない');
  active=false;for(const record of windows.values())pins.setLocked(record.window,false);
  const before=calls.length;ide.window.emit('focus');await pause();assert.equal(calls.length,before);
  assert.equal(errors.length,0,errors.join('\n'));
  console.log(JSON.stringify({passed:true,platform:process.platform,relativeMoves:calls.length,scope:'Native Electron API smoke only; Windows desktop Z-order not verified.'}));
 }finally{for(const record of windows.values())record.window.destroy();}
 app.quit();
}).catch(error=>{console.error(error);app.exit(1);});
