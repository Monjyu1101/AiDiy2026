// 実Electronで初期表示と復元を検証する。ユーザーのフォーカスやマウスを奪わない。
'use strict';
const assert=require('node:assert/strict');
const {writeFileSync}=require('node:fs');
const {app,BrowserWindow,screen}=require('electron');
const {holdMove}=require('../../frontend_ide/checks/window-move-probe.cjs');
app.setPath('appData',process.env.DIAG_TEST_PROFILE);
app.setPath('userData',process.env.DIAG_TEST_PROFILE);
app.setPath('sessionData',process.env.DIAG_TEST_PROFILE);
app.disableHardwareAcceleration();
let checks=0;
require('../起動/ポート接続.cjs').checkPort=async port=>{checks++;assert.equal(port,8095);return true;};
const show=BrowserWindow.prototype.showInactive,opacity=BrowserWindow.prototype.setOpacity;
BrowserWindow.prototype.setOpacity=function(value){opacity.call(this,this.isAiDiyOpeningCanvas?value:.01);};
BrowserWindow.prototype.show=BrowserWindow.prototype.showInactive=function(){if(!this.isAiDiyOpeningCanvas){this.setOpacity(.01);this.setIgnoreMouseEvents(true);this.setSkipTaskbar(true);}show.call(this);};
BrowserWindow.prototype.focus=function(){};
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function until(check){for(let i=0;i<150;i++){if(await check())return;await sleep(50);}throw Error('initial mini timeout');}
const near=(actual,expected)=>{for(const key of ['x','y','width','height'])assert.ok(Math.abs(actual[key]-expected[key])<=2,`${key}: ${actual[key]} / ${expected[key]}`);};
let owner,openingMeasurement,openingCheck;
app.on('browser-window-created',(_event,window)=>{
 if(owner){
  openingCheck=(async()=>{
   await until(()=>window.webContents.executeJavaScript("!!document.getAnimations().length"));
   const before=window.getBounds();
   const timing=await window.webContents.executeJavaScript(`(async()=>{const a=document.getAnimations()[0],start=performance.now(),current=a.currentTime,duration=a.effect.getTiming().duration;await a.finished;return{duration,elapsedEstimateMs:current+performance.now()-start};})()`);
   assert.equal(timing.duration,750);assert.ok(Math.abs(timing.elapsedEstimateMs-750)<150,JSON.stringify(timing));
   assert.deepEqual(window.getBounds(),before);return{...timing,bounds:before,boundsStable:true};
  })();openingCheck.catch(()=>{});return;
 }
 owner=window;const original=window.getNormalBounds();
 window.webContents.once('did-finish-load',async()=>{
  try{
   await until(()=>window.isVisible()&&window.webContents.executeJavaScript("!!document.querySelector('.start-mini .mini-app-button')&&!document.documentElement.classList.contains('desktop-opening')"));
   assert.equal(checks,1);const area=screen.getPrimaryDisplay().workArea,bounds=window.getBounds();
   near(bounds,{x:area.x,y:area.y,width:384,height:248});assert.equal(window.isAlwaysOnTop(),true);
   assert.equal(await window.webContents.executeJavaScript('window.aidiyWindow.initialMini'),true);
   assert.equal(await window.webContents.executeJavaScript("document.querySelector('#app-project-folder').value"),'');
   await sleep(650);window.webContents.invalidate();
   writeFileSync(process.env.DIAG_TEST_SHOT,(await window.webContents.capturePage(undefined,{stayHidden:true,stayAwake:true})).toPNG());
   openingMeasurement=await openingCheck;assert.ok(openingMeasurement);
   const miniMove=await holdMove(window,window.webContents,'.mini-service','Diagミニ');
   assert.equal(await window.webContents.executeJavaScript("!!document.querySelector('.start-mini')"),true);
   await window.webContents.executeJavaScript("document.querySelector('.mini-restore').click()");
   try{await until(()=>Math.abs(window.getBounds().width-original.width)<=2&&window.webContents.executeJavaScript("!document.querySelector('.start-mini')"));}
   catch(error){throw Error(JSON.stringify({bounds:window.getBounds(),original,ui:await window.webContents.executeJavaScript("({mini:!!document.querySelector('.start-mini'),message:document.querySelector('#message')?.textContent})")}),{cause:error});}
   assert.equal(window.isAlwaysOnTop(),false);near(window.getNormalBounds(),original);
   const normalMove=await holdMove(window,window.webContents,'.start-targets button','Diag通常','escape');
   process.send({testPassed:true,bounds,alwaysOnTop:true,restored:true,openingMeasurement,miniMove,normalMove,shot:process.env.DIAG_TEST_SHOT},()=>process.disconnect());
  }catch(error){console.error(error);app.exit(1);}
 });
});
setTimeout(()=>app.exit(1),20000).unref();
require('../起動/electron-main.cjs');
