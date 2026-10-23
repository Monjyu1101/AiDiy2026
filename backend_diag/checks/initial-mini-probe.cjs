// 実Electronで初期表示と復元を検証する。ユーザーのフォーカスやマウスを奪わない。
'use strict';
const assert=require('node:assert/strict');
const {writeFileSync}=require('node:fs');
const {app,BrowserWindow,screen}=require('electron');
const {holdMove,checkNativeControls,probeBackground}=require('../../frontend_ide/checks/window-move-probe.cjs');
app.setPath('appData',process.env.DIAG_TEST_PROFILE);
app.setPath('userData',process.env.DIAG_TEST_PROFILE);
app.setPath('sessionData',process.env.DIAG_TEST_PROFILE);
// 描画時間は通常起動と同じGPU設定で測定する。
let checks=0;
require('../起動/ポート接続.cjs').checkPort=async port=>{checks++;assert.equal(port,8095);return true;};
const show=BrowserWindow.prototype.showInactive,opacity=BrowserWindow.prototype.setOpacity;
BrowserWindow.prototype.setOpacity=function(value){opacity.call(this,this.isAiDiyOpeningCanvas?value:.01);};
BrowserWindow.prototype.show=BrowserWindow.prototype.showInactive=function(){if(!this.isAiDiyOpeningCanvas){this.setOpacity(.01);this.setIgnoreMouseEvents(true);this.setSkipTaskbar(true);}show.call(this);};
BrowserWindow.prototype.focus=function(){};
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function until(check){for(let i=0;i<150;i++){if(await check())return;await sleep(50);}throw Error('initial mini timeout');}
const near=(actual,expected)=>{for(const key of ['x','y','width','height'])assert.ok(Math.abs(actual[key]-expected[key])<=2,`${key}: ${actual[key]} / ${expected[key]}`);};
let owner,openingMeasurement,openingCheck;const resizeChecks=[];
app.on('browser-window-created',(_event,window)=>{
 // ほぼ透明な試験窓でも、観測中のアニメーションを省電力抑制しない。
 window.webContents.setBackgroundThrottling(false);
 if(owner){
  openingCheck=(async()=>{
   await sleep(0);
   const resize=window.isAiDiyResizeCanvas===true;
   if(resize)resizeChecks.push(openingCheck);
   await until(()=>window.webContents.executeJavaScript("!!document.getAnimations().length"));
   const before=window.getBounds();
   const timing=await window.webContents.executeJavaScript(`(async()=>{const a=document.getAnimations()[0];await a.ready;const start=performance.now(),current=a.currentTime,duration=a.effect.getTiming().duration,node=document.querySelector('#image')||document.querySelector('div'),samples=[];while(a.playState==='running'){const r=node.getBoundingClientRect();samples.push({width:r.width,height:r.height});await new Promise(requestAnimationFrame);}return{duration,elapsedEstimateMs:current+performance.now()-start,samples};})()`);
   assert.equal(timing.duration,resize?380:750);assert.ok(Math.abs(timing.elapsedEstimateMs-timing.duration)<150,JSON.stringify(timing));
   if(resize){assert.ok(timing.samples.length>=3);assert.ok(Math.abs(timing.samples[0].width-timing.samples.at(-1).width)>10);}
   assert.deepEqual(window.getBounds(),before);return{...timing,bounds:before,boundsStable:true};
  })();openingCheck.catch(()=>{});return;
 }
 owner=window;let original;const nativeSetBounds=window.setBounds.bind(window);window.setBounds=(bounds,...args)=>{if(!original&&bounds.width===384)original=window.getNormalBounds();return nativeSetBounds(bounds,...args);};
 window.webContents.once('did-finish-load',async()=>{
  try{
   await until(()=>window.isVisible()&&window.webContents.executeJavaScript("!!document.querySelector('.start-mini .mini-app-button')&&!document.documentElement.classList.contains('desktop-opening')"));
   assert.equal(checks,1);const area=screen.getPrimaryDisplay().workArea;
   assert.equal(await window.webContents.executeJavaScript('window.aidiyWindow.initialMini'),true);
   assert.equal(await window.webContents.executeJavaScript("document.querySelector('#app-project-folder').value"),'');
   await sleep(650);
   // 検出されたCLIやエラーの有無に合わせ、内容の自然な高さが窓へ反映されるまで待つ。
   let bounds,expectedHeight;
   await until(async()=>{
    const height=await window.webContents.executeJavaScript(`(()=>{const nodes=['.mini-content','.panel-brand','.connection-bar'].map(selector=>document.querySelector(selector));if(nodes.some(node=>!node))return null;const raw=nodes.reduce((sum,node)=>sum+node.getBoundingClientRect().height,0);return Number.isFinite(raw)&&raw>0?Math.max(80,Math.min(360,Math.ceil(raw))):null;})()`);
    const current=window.getBounds();if(height===null||Math.abs(current.height-height)>2)return false;
    bounds=current;expectedHeight=height;return true;
   });
   near(bounds,{x:area.x+8,y:area.y+8,width:384,height:expectedHeight});assert.equal(window.isAlwaysOnTop(),false);
   assert.equal(await window.webContents.executeJavaScript("document.querySelector('.window-pin').getAttribute('aria-pressed')"),'false');
   await window.webContents.executeJavaScript("document.querySelector('.window-pin').click()");
   try{await until(()=>window.isAlwaysOnTop()&&window.webContents.executeJavaScript("document.querySelector('.window-pin').getAttribute('aria-pressed')==='true'"));}catch(error){throw Error(JSON.stringify({top:window.isAlwaysOnTop(),state:await window.webContents.executeJavaScript("({button:document.querySelector('.window-pin').outerHTML})")}),{cause:error});}
   window.webContents.invalidate();
   writeFileSync(process.env.DIAG_TEST_SHOT,(await window.webContents.capturePage(undefined,{stayHidden:true,stayAwake:true})).toPNG());
   openingMeasurement=await openingCheck;assert.ok(openingMeasurement);
   const miniControls=await checkNativeControls(window,window.webContents,'Diagミニ');
   const miniBackground=await probeBackground(window.webContents);
   const miniMove=await holdMove(window,window.webContents,miniBackground,'Diagミニ背景');
   await window.webContents.executeJavaScript(`document.querySelector('#move-probe-background').remove()`);
   assert.equal(await window.webContents.executeJavaScript("!!document.querySelector('.start-mini')"),true);
   const restoreOrigin=window.getBounds();
   await window.webContents.executeJavaScript("document.querySelector('.mini-restore').click()");
   try{await until(()=>Math.abs(window.getBounds().width-original.width)<=2&&window.webContents.executeJavaScript("!document.querySelector('.start-mini')"));}
   catch(error){throw Error(JSON.stringify({bounds:window.getBounds(),original,ui:await window.webContents.executeJavaScript("({mini:!!document.querySelector('.start-mini'),message:document.querySelector('#message')?.textContent})")}),{cause:error});}
   assert.equal(window.isAlwaysOnTop(),true);near(window.getNormalBounds(),{...original,x:restoreOrigin.x,y:restoreOrigin.y});
   await window.webContents.executeJavaScript("document.querySelector('.window-pin').click()");
   await until(()=>!window.isAlwaysOnTop()&&window.webContents.executeJavaScript("document.querySelector('.window-pin').getAttribute('aria-pressed')==='false'"));
   const normalControls=await checkNativeControls(window,window.webContents,'Diag通常');
   const normalMove=await holdMove(window,window.webContents,await probeBackground(window.webContents),'Diag通常背景','escape');
   const movedNormal=window.getNormalBounds();
   await window.webContents.executeJavaScript("document.querySelector('#move-probe-background')?.remove();document.querySelector('.title-mini-switch').click()");
   await until(()=>window.webContents.executeJavaScript("!!document.querySelector('.start-mini')&&!document.querySelector('.mini-restore').disabled"));
   assert.ok(Math.abs(window.getBounds().width-384)<=2);
   await window.webContents.executeJavaScript("document.querySelector('.mini-restore').click()");
   await until(()=>window.webContents.executeJavaScript("!document.querySelector('.start-mini')&&!document.querySelector('.title-mini-switch').disabled"));
   near(window.getNormalBounds(),movedNormal);
   await until(()=>BrowserWindow.getAllWindows().every(candidate=>!candidate.isAiDiyResizeCanvas));
   await window.webContents.executeJavaScript('window.aidiyWindow.maximize()');assert.equal(await window.webContents.executeJavaScript('window.aidiyWindow.isMaximized()'),true);near(window.getBounds(),screen.getDisplayMatching(window.getBounds()).workArea);
   await window.webContents.executeJavaScript('window.aidiyWindow.maximize()');assert.equal(await window.webContents.executeJavaScript('window.aidiyWindow.isMaximized()'),false);near(window.getBounds(),movedNormal);
   const resizeMeasurements=await Promise.all(resizeChecks);assert.equal(resizeMeasurements.length,5);
   assert.ok(BrowserWindow.getAllWindows().every(candidate=>!candidate.isAiDiyResizeCanvas));
   process.send({testPassed:true,bounds,expectedHeight,initialPin:false,pinRoundTrip:true,restored:true,openingMeasurement,resizeMeasurements,miniMove,normalMove,miniControls,normalControls,shot:process.env.DIAG_TEST_SHOT},()=>process.disconnect());
  }catch(error){console.error(error);app.exit(1);}
 });
});
setTimeout(()=>app.exit(1),30000).unref();
require('../起動/electron-main.cjs');
