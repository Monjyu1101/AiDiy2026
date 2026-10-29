// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import test from 'node:test';
import assert from 'node:assert/strict';
import {EventEmitter} from 'node:events';
import motion from '../デスクトップ/ブラウザサイズ演出.cjs';
import sizing from '../デスクトップ/ブラウザ表示領域.cjs';
import opening from '../host/scripts/window-opening.cjs';
const deferred=()=>{let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return{promise,resolve,reject};};
const image=name=>({isEmpty:()=>false,toDataURL:()=>`data:image/png;base64,${name}`});
const tick=async()=>{for(let i=0;i<30;i++)await Promise.resolve();};
function fixture({settled=()=>true}={}){
 const canvases=[],captures=[],keys=[],opacity=[];
 const contents=name=>Object.assign(new EventEmitter(),{name,isDestroyed(){return !!this.destroyed;},isFocused:()=>name==='host',focus(){this.focused=true;},getZoomFactor:()=>1,capturePage:async(rect,options)=>{captures.push({name,rect,options});return image(name);},executeJavaScript:async()=>{}});
 const host=contents('host'),page=contents('page');
 const window=Object.assign(new EventEmitter(),{bounds:{x:200,y:100,width:1000,height:700},webContents:host,opacity:1,boundsCalls:[],isDestroyed(){return !!this.destroyed;},isMinimized:()=>false,isAlwaysOnTop:()=>true,isFullScreen(){return !!this.fullscreen;},isMaximized(){return !!this.maximized;},getBounds(){return{...this.bounds};},getContentBounds(){return{...this.bounds};},setBounds(value){this.bounds={...value};this.boundsCalls.push(value);this.emit('resize');},getOpacity(){return this.opacity;},setOpacity(value){opacity.push(value);this.opacity=value;},focus(){this.focused=true;},maximize(){this.normal={...this.bounds};this.maximized=true;this.setBounds({x:0,y:0,width:1600,height:900});this.emit('maximize');},unmaximize(){this.maximized=false;this.setBounds(this.normal);this.emit('unmaximize');},setFullScreen(value){if(value){this.normal={...this.bounds};this.fullscreen=true;this.setBounds({x:0,y:0,width:1600,height:1000});}else{this.fullscreen=false;this.setBounds(this.normal);}this.emit(value?'enter-full-screen':'leave-full-screen');}});
 const view={bounds:{x:1,y:101,width:998,height:598},webContents:page,getBounds(){return {...this.bounds};},setBounds(value){this.bounds={...value};},getVisible:()=>true};
 class Canvas extends EventEmitter{
  constructor(options){super();this.options=options;this.webContents=contents('canvas');this.webContents.setWindowOpenHandler=fn=>{this.popup=fn;};this.webContents.executeJavaScript=async code=>{if(code.includes('frame.animate')){this.animation=deferred();this.code=code;return this.animation.promise;}};canvases.push(this);}
  setBounds(value){(this.boundsCalls??=[]).push(value);this.bounds=value;}async loadURL(value){this.url=value;}showInactive(){this.visible=true;}setAlwaysOnTop(value){this.top=value;}isDestroyed(){return !!this.destroyed;}destroy(){this.destroyed=true;this.emit('closed');}
 }
 const control=motion.createBrowserResizeMotion({BrowserWindow:Canvas,window,view,isSettled:settled,fullscreenKey:(event,input)=>{if(input.key==='F11'){event.preventDefault();keys.push(input);}},wait:async()=>{}});
 const change=(width=1920,height=945)=>{window.setBounds({x:0,y:0,width:width+2,height:height+102});view.setBounds({x:1,y:101,width,height});return 'changed';};
 const keyEvent=()=>({defaultPrevented:false,preventDefault(){this.defaultPrevented=true;}});
 return{window,host,page,view,control,canvases,captures,opacity,keys,change,keyEvent,close:()=>control.dispose()};
}

test('Browserサイズ演出: 操作欄+本文を合成、最終窓へ一度変更して画像だけ750msズーム',async()=>{
 const f=fixture();try{
  const result=f.control.run(()=>f.change());await tick();const canvas=f.canvases[0];
  assert.ok(canvas.animation);assert.equal(f.window.boundsCalls.length,1);assert.deepEqual(f.view.bounds,{x:1,y:101,width:1920,height:945});
  assert.equal(canvas.options.transparent,true);assert.equal(canvas.options.backgroundColor,'#00000000');assert.equal(canvas.options.focusable,undefined);assert.equal(canvas.options.enableLargerThanScreen,true);assert.equal(canvas.options.alwaysOnTop,true);
  const html=decodeURIComponent(canvas.url.split(',').slice(1).join(','));assert.match(html,/data:image\/png;base64,host/);assert.match(html,/data:image\/png;base64,page/);assert.match(html,/left:1px;top:101px;width:998px;height:598px/);
  assert.match(canvas.code,new RegExp(`duration:${opening.演出時間}`));assert.match(canvas.code,/scale\(1\.922,1\.495714/);assert.equal(canvas.boundsCalls.length,2);
  assert.deepEqual(f.captures.map(c=>c.name),['host','page']);assert.deepEqual(f.captures[1].options,{stayHidden:true,stayAwake:true});assert.equal(f.window.opacity,0);
  canvas.animation.resolve();assert.equal(await result,'changed');assert.equal(f.window.opacity,1);assert.equal(canvas.destroyed,true);assert.equal(f.window.focused,undefined,'通常の完了でフォーカスを奪わない');
 }finally{f.close();}
});
test('Browserサイズ演出: 縮小は旧→新の比率を使い、ページzoomや入力APIを変更しない',async()=>{
 const f=fixture();try{
  f.page.setZoomFactor=()=>assert.fail('演出でpage zoomを変えない');f.page.sendInputEvent=()=>assert.fail('入力座標をリプレイしない');
  const pending=f.control.run(()=>f.change(500,300));await tick();const c=f.canvases[0];assert.match(c.code,/scale\(0\.502,0\.574285/);c.animation.resolve();await pending;assert.equal(f.view.bounds.width,500);
 }finally{f.close();}
});
test('Browserサイズ演出: 撮影待ちの操作を順に確定し、遅い画像が新しい操作を上書きしない',async()=>{
 const f=fixture();try{
  const old=deferred();let n=0,first=0,second=0;f.host.capturePage=()=>++n===1?old.promise:Promise.resolve(image('host'));
  const a=f.control.run(()=>{first++;f.change(1080,1785);}),b=f.control.run(()=>{second++;f.change();});await tick();
  const c=f.canvases[0];assert.ok(c.animation);old.resolve(image('host'));await a;assert.equal(first,1);assert.equal(second,1);assert.equal(c.destroyed,undefined);assert.equal(f.window.opacity,0);
  c.animation.resolve();await b;
 }finally{f.close();}
});
test('Browserサイズ演出: 連続切替で古いanimation完了が新しい透明度/窓を上書きしない',async()=>{
 const f=fixture();try{
  const a=f.control.run(()=>f.change());await tick();const old=f.canvases[0];
  const b=f.control.run(()=>f.change(1080,1785));await tick();const next=f.canvases[1];assert.equal(old.destroyed,true);assert.equal(f.window.opacity,0);
  old.animation.resolve();await a;assert.equal(f.window.opacity,0);assert.equal(next.destroyed,undefined);assert.equal(f.view.bounds.height,1785);
  next.animation.resolve();await b;assert.equal(f.window.opacity,1);
 }finally{f.close();}
});
test('Browserサイズ演出: 一時パネルのクリックは即終了・実窓復帰、位置リプレイなし',async()=>{
 const f=fixture();try{
  const pending=f.control.run(()=>f.change());await tick();const c=f.canvases[0],event=f.keyEvent();
  c.webContents.emit('before-mouse-event',event,{type:'mouseDown'});assert.equal(event.defaultPrevented,true);assert.equal(c.destroyed,true);assert.equal(f.window.opacity,1);assert.equal(f.host.focused,true);
  c.animation.resolve();await pending;
 }finally{f.close();}
});
test('Browserサイズ演出: F11は演出を終了して既存切替へ渡し、長押し反復を無視',async()=>{
 const f=fixture();try{
  const pending=f.control.run(()=>f.change());await tick();const c=f.canvases[0];
  f.host.emit('before-input-event',f.keyEvent(),{type:'keyDown',key:'F11',isAutoRepeat:true});assert.equal(c.destroyed,undefined);
  c.webContents.emit('before-input-event',f.keyEvent(),{type:'keyDown',key:'F11',isAutoRepeat:true});assert.equal(c.destroyed,undefined);
  c.webContents.emit('before-input-event',f.keyEvent(),{type:'keyDown',key:'F11'});assert.equal(f.keys.length,1);assert.equal(c.destroyed,true);assert.equal(f.window.opacity,1);
  c.animation.resolve();await pending;
 }finally{f.close();}
});
for(const event of ['did-start-loading','render-process-gone'])test(`Browserサイズ演出: 本文${event}で破棄し、古い完了では再表示しない`,async()=>{
 const f=fixture();try{
  const pending=f.control.run(()=>f.change());await tick();const c=f.canvases[0];f.page.emit(event);assert.equal(c.destroyed,true);assert.equal(f.window.opacity,1);c.animation.resolve();await pending;
 }finally{f.close();}
});
test('Browserサイズ演出: 閉鎖中・破棄後の非同期結果を捨て、購読を回収',async()=>{
 const f=fixture(),capture=deferred();f.host.capturePage=()=>capture.promise;let changed=0;
 const pending=f.control.run(()=>changed++);f.window.destroyed=true;f.close();capture.resolve(image('host'));await pending;
 assert.equal(changed,0);assert.equal(f.canvases.length,0);assert.equal(f.host.listenerCount('before-input-event'),0);assert.equal(f.page.listenerCount('before-mouse-event'),0);
});
test('Browserサイズ演出: 撮影失敗は代用品を出さずサイズ操作だけ一度実行',async()=>{
 const f=fixture();try{
  f.page.capturePage=async()=>{throw Error('capture unavailable');};let count=0;
  await f.control.run(()=>{count++;return f.change();});assert.equal(count,1);assert.equal(f.canvases.length,0);assert.equal(f.window.opacity,1);
 }finally{f.close();}
});
test('Browserサイズ演出: サイズ操作の失敗は隠さず、透明度と一時窓を必ず復元',async()=>{
 const f=fixture();try{
  await assert.rejects(f.control.run(()=>{throw Error('size failed');}),/size failed/);assert.equal(f.window.opacity,1);assert.equal(f.canvases[0].destroyed,true);
 }finally{f.close();}
});
test('Browserサイズ演出: OS遷移の未完了では演出を止めて実窓を復元する',async()=>{
 const f=fixture({settled:()=>false});try{
  await f.control.run(()=>f.change());assert.equal(f.window.opacity,1);assert.equal(f.canvases[0].destroyed,true);assert.equal(f.canvases[0].animation,undefined);assert.equal(f.view.bounds.width,1920);
 }finally{f.close();}
});
test('Browserサイズ演出: 本文非表示のダイアログ中は撮影せずサイズ操作を維持',async()=>{
 const f=fixture();try{f.view.getVisible=()=>false;await f.control.run(()=>f.change());assert.equal(f.canvases.length,0);assert.equal(f.view.bounds.width,1920);}finally{f.close();}
});
test('Browserサイズ演出: FHD/縦/最大化/通常/F11を通して最終viewportを変更しない',async()=>{
 const f=fixture();const s=sizing.createBrowserSizing({window:f.window,view:f.view,screen:{getDisplayMatching:()=>({workArea:{x:0,y:0,width:1600,height:900}})}});
 try{
  s.measure({left:1,top:101,width:998,height:598,viewportWidth:1000,viewportHeight:700,fullscreen:false});
  for(const [change,width,height]of [[()=>s.preset('fhd'),1920,945],[()=>s.preset('portrait'),1080,1785],[()=>s.maximize(),1598,798],[()=>s.maximize(),1080,1785],[()=>s.toggleFullscreen(),1600,1000],[()=>s.toggleFullscreen(),1080,1785]]){
   const p=f.control.run(change);await tick();const c=f.canvases.at(-1);assert.equal(f.view.bounds.width,width);assert.equal(f.view.bounds.height,height);c.animation.resolve();await p;
  }
 }finally{s.dispose();f.close();}
});
test('Browserサイズ演出: 破棄した旧パネルの遅い入力で新しい演出を止めない',async()=>{
 const f=fixture();try{
  const a=f.control.run(()=>f.change());await tick();const old=f.canvases[0];const b=f.control.run(()=>f.change(1080,1785));await tick();const next=f.canvases[1];
  old.webContents.emit('before-mouse-event',f.keyEvent(),{type:'mouseDown'});old.webContents.emit('before-input-event',f.keyEvent(),{type:'keyDown',key:'F11'});
  assert.equal(next.destroyed,undefined);assert.equal(f.window.opacity,0);assert.equal(f.keys.length,0);
  old.animation.resolve();next.animation.resolve();await Promise.all([a,b]);
 }finally{f.close();}
});
test('Browserサイズ演出: 撮影待ち中のF11/🔲二回押下を一回に減らさない',async()=>{
 for(const kind of ['F11','maximize']){
  const f=fixture();try{
   const capture=deferred();let n=0,toggles=0,active=false;f.host.capturePage=()=>++n===1?capture.promise:Promise.resolve(image('host'));
   const toggle=()=>{toggles++;active=!active;f.change(active?1080:998,active?1785:598);};
   const a=f.control.run(toggle),b=f.control.run(toggle);await tick();capture.resolve(image('host'));await a;
   assert.equal(toggles,2,kind);assert.equal(active,false,kind);f.canvases[0].animation.resolve();await b;
  }finally{f.close();}
 }
});
test('Browserサイズ演出: 撮影中のnavigationは画像を捨てても最後のサイズ要求を落とさない',async()=>{
 const f=fixture();try{
  const capture=deferred();f.host.capturePage=()=>capture.promise;let count=0;
  const p=f.control.run(()=>{count++;return f.change();});f.page.emit('did-start-loading');assert.equal(count,1);assert.equal(f.view.bounds.width,1920);
  capture.resolve(image('host'));await p;assert.equal(count,1);assert.equal(f.canvases.length,0);
 }finally{f.close();}
});
for(const event of ['closed','render-process-gone'])test(`Browserサイズ演出: 一時パネル${event}で実窓の透明度を即復元`,async()=>{
 const f=fixture();try{
  const p=f.control.run(()=>f.change());await tick();const c=f.canvases[0];
  if(event==='closed')c.destroy();else c.webContents.emit(event);
  assert.equal(f.window.opacity,1);assert.equal(c.destroyed,true);c.animation.resolve();await p;
 }finally{f.close();}
});
test('Browserサイズ演出: setOpacityがno-opなら演出だけ省略し、次回の撮影も省く',async()=>{
 const f=fixture();try{
  f.window.setOpacity=value=>f.opacity.push(value);let count=0;
  await f.control.run(()=>{count++;return f.change();});
  assert.equal(count,1);assert.equal(f.view.bounds.width,1920);assert.equal(f.window.opacity,1);assert.equal(f.canvases[0].destroyed,true);assert.equal(f.canvases[0].animation,undefined);
  const captures=f.captures.length;
  await f.control.run(()=>{count++;return f.change(1080,1785);});
  assert.equal(count,2);assert.equal(f.view.bounds.height,1785);assert.equal(f.captures.length,captures);assert.equal(f.canvases.length,1);
 }finally{f.close();}
});
