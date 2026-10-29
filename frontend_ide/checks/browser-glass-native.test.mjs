// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import test from 'node:test';
import assert from 'node:assert/strict';
import {EventEmitter} from 'node:events';
import native from '../デスクトップ/ブラウザ縁屈折.cjs';
import headerNative from '../デスクトップ/ブラウザ全画面パネル.cjs';
const {browserGlassGeometry,createBrowserGlass}=native;
const png='data:image/png;base64,iVBORw0KGgo=';
const flush=async()=>{for(let i=0;i<6;i++)await Promise.resolve();};

function fixture(){
 const timers=new Map(),calls=[],sent=[],normalized=[];let clock=0,next=0;
 const state={header:{x:-1500,y:90,width:1200,height:100},owner:{x:-1600,y:40,width:1600,height:900},view:{x:0,y:0,width:1600,height:900},shown:true,fullscreen:true,minimized:false,destroyed:false,pageDestroyed:false,url:'https://example.test/page'};
 const source=Object.assign(new EventEmitter(),{isDestroyed:()=>state.pageDestroyed,getURL:()=>state.url,
  capturePage(rect,options){return new Promise((resolve,reject)=>calls.push({rect,options,resolve,reject}));},
  getZoomFactor(){throw Error('DIPに倍率を二重適用しない');},
 });
 const window=Object.assign(new EventEmitter(),{isDestroyed:()=>state.destroyed,isFullScreen:()=>state.fullscreen,isMinimized:()=>state.minimized,getContentBounds:()=>({...state.owner}),webContents:{getZoomFactor(){throw Error('DIPに倍率を二重適用しない');}}});
 const entry={run:1,available:true,dialogOpen:false,view:{webContents:source,getBounds:()=>({...state.view})}};
 const glass=createBrowserGlass({record:{window},entry,getFrame:()=>state.shown?{...state.header}:null,send:value=>sent.push(value),now:()=>clock,
  setTimer:(fn,interval)=>{assert.equal(interval,250);const id=++next;timers.set(id,fn);return id;},clearTimer:id=>timers.delete(id),
 });
 const image=(value=png)=>({isEmpty:()=>false,resize(options){normalized.push(options);return{toDataURL(options){assert.equal(options.scaleFactor,1);return value;}};}});
 return{glass,state,entry,window,source,calls,sent,timers,normalized,image,tick(ms=250){clock+=ms;for(const fn of [...timers.values()])fn();},resolve(index=calls.length-1,value=image()){calls[index].resolve(value);},close(){glass.dispose();}};
}

test('Browser縁屈折: 負原点・本文オフセットはDIPのまま切り出す',()=>{
 assert.deepEqual(browserGlassGeometry({x:-1500,y:90,width:1200,height:100},{x:-1600,y:40,width:1600,height:900},{x:10,y:20,width:1500,height:800}),{
  rect:{x:90,y:30,width:1200,height:100},width:1200,height:100,x:0,y:0,captureWidth:1200,captureHeight:100,
 });
});
test('Browser縁屈折: 画面外との交差だけを取得し、板の中の配置オフセットを保つ',()=>{
 assert.deepEqual(browserGlassGeometry({x:-1610,y:30,width:100,height:80},{x:-1600,y:40,width:1600,height:900},{x:0,y:0,width:1600,height:900}),{
  rect:{x:0,y:0,width:90,height:70},width:100,height:80,x:10,y:10,captureWidth:90,captureHeight:70,
 });
 assert.deepEqual(browserGlassGeometry({x:90,y:90,width:100,height:80},{x:0,y:0,width:100,height:100},{x:0,y:0,width:100,height:100}),{
  rect:{x:90,y:90,width:10,height:10},width:100,height:80,x:0,y:0,captureWidth:10,captureHeight:10,
 });
});
test('Browser縁屈折: 無交差・不正値・過大な画像は取得しない',()=>{
 const owner={x:0,y:0,width:100,height:100};
 for(const header of [{x:200,y:0,width:100,height:100},{x:0,y:200,width:100,height:100},{x:0,y:0,width:0,height:100},{x:NaN,y:0,width:100,height:100},{x:0,y:0,width:1201,height:100},{x:0,y:0,width:100,height:1001}])assert.equal(browserGlassGeometry(header,owner,owner),null);
});
test('Browser縁屈折: 最大4fps・同時1枚、DIPへ正規化し非表示で標本とtimerを破棄する',async()=>{
 const f=fixture();try{
  f.glass.start();for(let i=0;i<5;i++)f.glass.start();assert.equal(f.calls.length,1);assert.equal(f.timers.size,1);
  f.tick(100);assert.equal(f.calls.length,1);
  f.resolve();await flush();assert.deepEqual(f.calls[0].rect,{x:100,y:50,width:1200,height:100});
  assert.deepEqual(f.calls[0].options,{stayHidden:true,stayAwake:false});
  assert.deepEqual(f.normalized[0],{width:1200,height:100,quality:'good'});
  assert.deepEqual(f.sent[0],{src:png,width:1200,height:100,x:0,y:0,captureWidth:1200,captureHeight:100});
  f.tick(150);assert.equal(f.calls.length,2);f.tick(250);assert.equal(f.calls.length,2,'前の非同期取得中は新しく開始しない');
  f.glass.pause();assert.equal(f.sent.at(-1),null);assert.equal(f.timers.size,0);
  f.resolve();await flush();assert.equal(f.sent.length,2,'非表示後の取得結果を復活させない');
  f.tick(1000);assert.equal(f.calls.length,2);
 }finally{f.close();}
});

for(const change of ['move','resize','navigation','run','url','unavailable','dialog','fullscreen','minimize','hide','close'])test(`Browser縁屈折: ${change}後に届いた画素は使わない`,async()=>{
 const f=fixture();try{
  f.glass.start();f.resolve();await flush();f.tick();assert.equal(f.calls.length,2);
  if(change==='move'){f.state.header.x+=20;f.glass.invalidate();}
  if(change==='resize'){f.state.header.width=1100;f.glass.invalidate();}
  if(change==='navigation')f.source.emit('did-start-navigation');
  if(change==='run')f.entry.run++;
  if(change==='url')f.state.url='https://example.test/other';
  if(change==='unavailable')f.entry.available=false;
  if(change==='dialog')f.entry.dialogOpen=true;
  if(change==='fullscreen'){f.state.fullscreen=false;f.window.emit('leave-full-screen');}
  if(change==='minimize'){f.state.minimized=true;f.window.emit('minimize');}
  if(change==='hide'){f.state.shown=false;f.glass.pause();}
  if(change==='close'){f.state.destroyed=true;f.window.emit('closed');}
  f.resolve();await flush();assert.equal(f.sent.at(-1),null);assert.equal(f.sent.filter(Boolean).length,1);
 }finally{f.close();}
});
test('Browser縁屈折: 失敗・空画像は装飾だけを取り消し、次の取得で回復する',async()=>{
 const f=fixture();try{
  f.glass.start();f.resolve();await flush();
  f.tick();f.calls.at(-1).reject(Error('capture unavailable'));await flush();assert.equal(f.sent.at(-1),null);
  f.tick();f.resolve(undefined,{isEmpty:()=>true});await flush();assert.equal(f.sent.filter(Boolean).length,1);
  f.tick();f.resolve();await flush();assert.equal(f.sent.filter(Boolean).length,2);
  f.tick();f.resolve(undefined,f.image('https://example.test/image.png'));await flush();assert.equal(f.sent.at(-1),null);
 }finally{f.close();}
});
test('Browser縁屈折: 復元で再開し、破棄時はページ・所有窓の購読も解除する',async()=>{
 const f=fixture();f.glass.start();f.resolve();await flush();
 f.state.minimized=true;f.window.emit('minimize');assert.equal(f.timers.size,0);
 f.state.minimized=false;f.tick();f.window.emit('restore');assert.equal(f.timers.size,1);assert.equal(f.calls.length,2);
 f.state.pageDestroyed=true;f.source.emit('destroyed');assert.equal(f.timers.size,0);
 assert.deepEqual(f.source.eventNames(),[]);assert.deepEqual(f.window.eventNames(),[]);
 f.resolve();await flush();assert.equal(f.sent.at(-1),null);f.glass.start();assert.equal(f.timers.size,0);
});

test('Browser実ヘッダー: frosted材質なし・表示完了後のみ屈折標本を送り、収納/サイズ変更/終了で消す',async t=>{
 t.mock.timers.enable({apis:['setInterval','Date']});
 const f=fixture(),headers=new Map();let nativeWindow;
 class Window extends EventEmitter{
  constructor(options){super();nativeWindow=this;this.options=options;this.bounds={x:options.x,y:options.y,width:options.width,height:options.height};this.webContents=Object.assign(new EventEmitter(),{sent:[],send(channel,value){this.sent.push([channel,value]);},setZoomFactor(){},setWindowOpenHandler(){},getZoomFactor:()=>1,isDestroyed:()=>this.destroyed,executeJavaScriptInIsolatedWorld:async()=>false});}
  isDestroyed(){return!!this.destroyed;}getBounds(){return{...this.bounds};}setBounds(value){this.bounds={...value};}setAlwaysOnTop(){}showInactive(){}moveTop(){}hide(){}
  async loadURL(){}destroy(){this.destroyed=true;this.emit('closed');this.webContents.emit('destroyed');}
 }
 // 上の単体fixtureに付いている標本取得部品とは独立して、実ヘッダーから作成する。
 f.glass.dispose();f.window.webContents.getZoomFactor=()=>1.5;
 const header=headerNative.createBrowserHeader({BrowserWindow:Window,screen:{getCursorScreenPoint:()=>({x:0,y:0})},record:{window:f.window,url:'http://127.0.0.1:1234'},entry:f.entry,notify(){},fullscreenKey(){},headers});
 try{
  header.show(true);await flush();assert.equal(f.calls.length,0,'スライド中は標本を取得しない');
  assert.equal(nativeWindow.options.backgroundMaterial,undefined);assert.equal(nativeWindow.options.vibrancy,undefined);
  assert.equal(nativeWindow.options.transparent,true);assert.equal(nativeWindow.options.roundedCorners,false,'OS側にも角丸を付けない');
  t.mock.timers.tick(240);assert.equal(f.calls.length,1);f.resolve();await flush();
  const messages=()=>nativeWindow.webContents.sent.filter(([channel])=>channel==='development:browser-header-glass').map(([,value])=>value);
  assert.equal(messages().at(-1).src,png);assert.equal(messages().at(-1).width,1200);assert.equal(messages().at(-1).zoom,1.5,'CSS縁幅用の倍率はメタデータだけに付け、取得矩形を拡大しない');
  header.measure(120);assert.equal(messages().at(-1),null);t.mock.timers.tick(250);assert.equal(f.calls.length,2);
  header.show(false);f.resolve();await flush();assert.equal(messages().filter(Boolean).length,1,'収納開始後の古い取得結果は送らない');
  t.mock.timers.tick(300);assert.equal(f.calls.length,2);header.show(true);await flush();t.mock.timers.tick(240);
  assert.equal(f.calls.length,3);header.close();f.resolve();await flush();
  assert.equal(messages().filter(Boolean).length,1);assert.deepEqual(f.source.eventNames(),[]);assert.deepEqual(f.window.eventNames(),[]);
 }finally{header.close();f.close();}
});
