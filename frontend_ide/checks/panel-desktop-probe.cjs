// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
const assert=require('node:assert/strict');
const {app,BrowserWindow,screen}=require('electron');
const {mkdirSync,writeFileSync}=require('node:fs');
const {join}=require('node:path');
app.setPath('appData',process.env.AIDIY_TEST_PROFILE);
const showInactive=BrowserWindow.prototype.showInactive;
// 非表示の専用プロファイルで実ElectronのDOM/IPC/配置/終了を検証する。
BrowserWindow.prototype.show=function(){};BrowserWindow.prototype.showInactive=function(){};BrowserWindow.prototype.focus=function(){};
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const evaluate=(window,source)=>window.webContents.executeJavaScript(source,true).catch(error=>{throw Error('Expression: '+source+'\n'+error.message);});
async function until(check,label){for(let i=0;i<150;i++){if(await check())return;await sleep(100);}throw Error('Electron確認タイムアウト: '+label);}
const output=join(__dirname,'../../temp/panel-pin-check');mkdirSync(output,{recursive:true});
const results=[];let running=false;
const nearBounds=(actual,expected)=>{for(const key of ['x','y','width','height'])assert.ok(Math.abs(actual[key]-expected[key])<=2,`${key}: ${actual[key]} / ${expected[key]}`);};
app.on('browser-window-created',(_,owner)=>{
 owner.webContents.setBackgroundThrottling(false);
 if(running)return;running=true;
 owner.webContents.once('did-finish-load',async()=>{
  try{
   await until(()=>evaluate(owner,`!!document.querySelector('.component-toolbar')&&!document.documentElement.classList.contains('desktop-opening')`),'起動');
   await evaluate(owner,`Array.from(document.querySelectorAll('button')).find(b=>b.textContent==='オフライン利用').click()`);
   await until(()=>evaluate(owner,`!!window.aidiyIDE`),'利用');
   await evaluate(owner,`aidiyIDE.setAutoSpin(false);aidiyIDE.interact();Array.from(document.querySelectorAll('.ide-view-modes button')).find(b=>b.textContent==='2D').click()`);
   await evaluate(owner,`aidiyIDE.goTo({type:'file',path:'sample.txt'})`);
   await until(()=>evaluate(owner,`!!document.querySelector('.viewer-popup .viewer-meta')`),'Viewer');
   await evaluate(owner,`document.querySelector('.explorer-toggle').click()`);
   for(const zoom of [1,1.25]){
    console.log('Explorer zoom',zoom);
    owner.webContents.setZoomFactor(zoom);await sleep(150);
    const rect=await evaluate(owner,`(()=>{const r=document.querySelector('.explorer-panel').getBoundingClientRect();return {left:r.left,top:r.top,width:r.width,height:r.height}})()`);
    const expected=require('../デスクトップ/panel-windows.cjs').panelBounds(rect,{window:owner},screen);
    await evaluate(owner,`(()=>{window.originalExplorer=document.querySelector('.explorer-panel');const pin=document.querySelector('[aria-label="エクスプローラーをピン留め"]');pin.click();pin.click()})()`);
    await until(()=>evaluate(owner,`!document.querySelector('.explorer-panel')`),'Explorer移動');
    const child=BrowserWindow.getAllWindows().find(w=>w!==owner&&w.webContents.getURL()==='about:blank');assert.ok(child);
    await until(()=>evaluate(child,`!!document.querySelector('.explorer-panel')`),'Explorer DOM');
    nearBounds(child.getBounds(),expected);
    await evaluate(child,`document.querySelector('input[value="grep"]').click()`);
    await evaluate(child,`const input=document.querySelector('input[type=search]');input.value='Electron';input.dispatchEvent(new Event('input',{bubbles:true}));Array.from(document.querySelectorAll('form button')).find(b=>b.textContent==='検索').click()`);
    await until(()=>evaluate(child,`document.querySelector('form [role=status]')?.textContent.includes('1ファイル一致')`),'検索結果');
    const reloaded=new Promise(resolve=>child.webContents.once('did-finish-load',resolve));child.webContents.reload();await reloaded;
    await until(()=>evaluate(child,`document.querySelector('input[type=search]')?.value==='Electron'`),'再読込復帰');
    await until(()=>evaluate(child,`(()=>{const panel=document.querySelector('.explorer-panel'),style=getComputedStyle(panel);return style.visibility==='visible'&&style.opacity==='1'&&panel.getBoundingClientRect().height>100})()`),'再読込後の可視性');
    await sleep(300);
    // about:blank再読み込み後の隠れた窓はChromiumが描画を省くため、画像確認時だけ非アクティブ表示。
    if(process.env.AIDIY_TEST_VISIBLE==='1'){
     showInactive.call(child);await sleep(300);
     writeFileSync(join(output,`electron-explorer-${zoom}.png`),(await child.webContents.capturePage()).toPNG());child.hide();
    }
    child.close();await until(()=>evaluate(owner,`getComputedStyle(originalExplorer).display==='none'`),'X折畳み');
    await evaluate(owner,`document.querySelector('.explorer-toggle').click()`);await until(()=>evaluate(owner,`getComputedStyle(originalExplorer).display!=='none'`),'再表示');
    assert.equal(await evaluate(owner,`document.querySelector('.explorer-panel')===originalExplorer`),true);
    results.push({kind:'explorer',zoom,bounds:expected,reload:true,restore:true});
   }
   for(const zoom of [1,1.25]){
    console.log('Viewer zoom',zoom);
    owner.webContents.setZoomFactor(zoom);await sleep(150);
    const rect=await evaluate(owner,`(()=>{const r=document.querySelector('.viewer-popup').getBoundingClientRect();return {left:r.left,top:r.top,width:r.width,height:r.height}})()`);
    const expected=require('../デスクトップ/panel-windows.cjs').panelBounds(rect,{window:owner},screen);
    await evaluate(owner,`document.querySelector('[aria-label="ピン留め"]').click()`);
    await until(()=>evaluate(owner,`!document.querySelector('.viewer-popup')`),'Viewer移動');
    const child=BrowserWindow.getAllWindows().find(w=>w!==owner&&w.webContents.getURL()==='about:blank');assert.ok(child);
    nearBounds(child.getBounds(),expected);await until(()=>evaluate(child,`!!document.querySelector('.viewer-pinned .viewer-meta')`),'Viewer表示');
    writeFileSync(join(output,`electron-viewer-${zoom}.png`),(await child.webContents.capturePage()).toPNG());
    child.close();await until(()=>evaluate(owner,`!document.querySelector('.viewer-session')`),'Viewer X終了');
    await evaluate(owner,`aidiyIDE.goTo({type:'file',path:'sample.txt'})`);await until(()=>evaluate(owner,`!!document.querySelector('.viewer-popup .viewer-meta')`),'Viewer再open');
    results.push({kind:'viewer',zoom,bounds:expected,dismiss:true,reopen:true});
   }
   await evaluate(owner,`document.querySelector('[aria-label="エクスプローラーをピン留め"]').click()`);await until(()=>evaluate(owner,`!document.querySelector('.explorer-panel')`),'終了前pin');
   const child=BrowserWindow.getAllWindows().find(w=>w!==owner&&w.webContents.getURL()==='about:blank');
   await evaluate(owner,`Array.from(document.querySelectorAll('.component-toolbar button')).find(b=>b.textContent==='終了').click()`);
   await until(()=>child.isDestroyed(),'利用終了');
   writeFileSync(join(output,'electron-result.json'),JSON.stringify(results,null,2));process.send?.({testPassed:true,results});app.exit(0);
  }catch(error){console.error(error);try{console.error(await evaluate(owner,'document.body.innerText'));}catch{}app.exit(1);}
 });
});
setTimeout(()=>{console.error('Electron確認期限');app.exit(1);},60000).unref();
require('../desktop.cjs');
