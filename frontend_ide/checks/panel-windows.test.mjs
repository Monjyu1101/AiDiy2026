// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import test from 'node:test';
import assert from 'node:assert/strict';
import {EventEmitter} from 'node:events';
import native from '../デスクトップ/panel-windows.cjs';
import {popupFeatures,fadePanel} from '../src/ファイル閲覧/パネル別窓.js';
const {panelBounds,createPanelWindows}=native;
test('表示開始フェード: opacityだけ260ms、再実行で古い演出解除、reduced-motionは演出なし',()=>{
 let reduced=false,cancelled=0;const calls=[];
 const element={ownerDocument:{defaultView:{matchMedia:()=>({matches:reduced})}},animate:(frames,options)=>{calls.push({frames,options});return{cancel:()=>cancelled++};}};
 fadePanel(element);assert.deepEqual(calls,[{frames:[{opacity:0},{opacity:1}],options:{duration:260,easing:'ease-out'}}]);
 fadePanel(element);assert.equal(cancelled,1);reduced=true;fadePanel(element);assert.equal(cancelled,2);assert.equal(calls.length,2);
});
for(const zoom of [.8,1,1.25,2])test(`パネル配置: zoom=${zoom}、負座標・別画面・画面外をDIPへ変換`,()=>{
 const area={x:-1600,y:-100,width:1600,height:1000};let requested;
 const screen={getDisplayMatching:rect=>{requested=rect;return{workArea:area};}};
 const owner={window:{getContentBounds:()=>({x:-1400,y:0}),webContents:{getZoomFactor:()=>zoom}}};
 const rect={left:200,top:100,width:380,height:500},bounds=panelBounds(rect,owner,screen);
 assert.equal(requested.x,-1400+200*zoom);assert.equal(requested.y,100*zoom);
 assert.equal(bounds.width,Math.round(380*zoom));
 for(const input of [rect,{left:-9000,top:9000,width:9000,height:9000}]){
  const result=panelBounds(input,owner,screen);assert.ok(result.x>=area.x&&result.y>=area.y);assert.ok(result.x+result.width<=area.x+area.width);assert.ok(result.y+result.height<=area.y+area.height);
 }
 assert.equal(panelBounds({...rect,width:NaN},owner,screen),null);
});
test('ブラウザー配置: 負座標画面でも範囲内、OSのdevicePixelRatioで二重拡大しない',()=>{
 const win={screen:{availLeft:-1600,availTop:-100,availWidth:1600,availHeight:1000},screenX:-1500,screenY:0,innerWidth:1000,outerWidth:1020,innerHeight:700,outerHeight:780,devicePixelRatio:2};
 const input={left:100,top:100,width:380,height:500},features=popupFeatures(input,win);
 assert.equal(features,'popup,left=-1390,top=170,width=380,height=500');
 assert.equal(features,popupFeatures(input,{...win,devicePixelRatio:1}));
 assert.equal(popupFeatures({...input,left:5000,top:5000},win),'popup,left=-388,top=340,width=380,height=500');
});
function fixture(){
 const windows=new Map();let state={active:true,mode:'offline',startedAt:1},animations=0,quitting=false;
 class Window extends EventEmitter{
  constructor(){super();this.webContents=new EventEmitter();Object.assign(this.webContents,{getZoomFactor:()=>1,setWindowOpenHandler:fn=>{this.handler=fn;}});}
  isDestroyed(){return !!this.dead;}destroy(){this.dead=true;this.emit('closed');}setBounds(value){this.bounds=value;}setAlwaysOnTop(){}getContentBounds(){return this.bounds||{x:100,y:100,width:420,height:360};}getBounds(){return this.getContentBounds();}show(){this.shown=true;}focus(){}
 }
 const owner={window:new Window(),kind:'ide',revision:0},event={owner},key=state=>state.active?`${state.mode}:${state.startedAt}`:'';
 const controller=createPanelWindows({windows,trustedEvent:e=>e.owner,readState:async()=>state,sessionKey:key,screen:{getDisplayMatching:()=>({workArea:{x:0,y:0,width:1920,height:1040}})},BrowserWindow:Window,拡大表示:async()=>{animations++;},isQuitting:()=>quitting});
 return{windows,Window,owner,event,controller,rect:{left:16,top:78,width:380,height:650},state:next=>{state=next;},animations:()=>animations,quit:()=>{quitting=true;}};
}
test('Explorer: 承認済みabout:blankを一回だけ許可し、同じ親の子窓として登録',async()=>{
 const f=fixture(),request=await f.controller.prepare(f.event,f.rect);assert.equal(request.ok,true);
 assert.equal(f.controller.open(f.owner,{url:'https://example.invalid',frameName:request.name}),null);
 assert.equal(f.controller.open(f.owner,{url:'about:blank',frameName:'wrong'}),null);
 const details={url:'about:blank',frameName:request.name},result=f.controller.open(f.owner,details);assert.equal(result.action,'allow');assert.equal(result.overrideBrowserWindowOptions.webPreferences.nodeIntegration,false);
 assert.equal(f.controller.open(f.owner,details),null);
 const child=new f.Window();f.controller.created(f.owner,child,details);
 assert.equal(f.windows.get(child.webContents).owner,f.owner);assert.equal(f.windows.get(child.webContents).linkKey,'offline:1');
 assert.equal((await f.controller.show(f.event,request.name,false)).ok,true);assert.equal(f.animations(),1);
 await f.controller.show(f.event,request.name,false);assert.equal(f.animations(),1,'子リロードでネイティブ演出を重複しない');
 child.destroy();assert.equal(f.windows.size,0);
});
test('Explorer: reduced-motionでは演出なし、終了済み・別親のshowを拒否',async()=>{
 const f=fixture(),request=await f.controller.prepare(f.event,f.rect),details={url:'about:blank',frameName:request.name};
 f.controller.open(f.owner,details);const child=new f.Window();f.controller.created(f.owner,child,details);
 assert.equal((await f.controller.show({owner:{kind:'ide'}},request.name,true)).ok,false);
 assert.equal((await f.controller.show(f.event,request.name,true)).ok,true);assert.equal(child.shown,true);assert.equal(f.animations(),0);
 f.state({active:false});assert.equal((await f.controller.show(f.event,request.name,true)).ok,false);child.destroy();
});
test('Explorer: 非IDE・無効位置・セッション終了・古い起動予約を拒否',async()=>{
 const f=fixture();assert.equal((await f.controller.prepare({owner:{kind:'viewer'}},f.rect)).ok,false);
 assert.equal((await f.controller.prepare(f.event,{...f.rect,height:-1})).ok,false);
 const request=await f.controller.prepare(f.event,f.rect);f.owner.revision++;
 assert.equal(f.controller.open(f.owner,{url:'about:blank',frameName:request.name}),null);
 f.state({active:false});assert.equal((await f.controller.prepare(f.event,f.rect)).ok,false);
});
test('Viewer/比較/軌跡: Explorerと共存し、同じ予約・配置・ズーム・終了境界を使う',async()=>{
 const f=fixture(),children=[];
 for(const kind of ['explorer','panel-viewer','panel-viewer','panel-routes']){
  const request=await f.controller.prepare(f.event,f.rect,kind);assert.equal(request.ok,true);
  const details={url:'about:blank',frameName:request.name};assert.equal(f.controller.open(f.owner,details).action,'allow');
  const child=new f.Window();f.controller.created(f.owner,child,details);children.push(child);
  assert.equal(f.windows.get(child.webContents).kind,kind);
  assert.equal((await f.controller.show(f.event,request.name,false)).ok,true);
 }
 assert.equal(f.windows.size,4);assert.equal(f.animations(),3,'軌跡の展開は共通UIで行い、不透明なnative zoomを使わない');
 assert.equal((await f.controller.prepare(f.event,f.rect,'explorer')).ok,false);
 assert.equal((await f.controller.prepare(f.event,f.rect,'untrusted')).ok,false);
 for(const child of children)child.destroy();assert.equal(f.windows.size,0);
});

test('軌跡: 透明枠なしの小さいバーから先に領域確保、上端維持・画面下端制限・閉じると縮小',async()=>{
 const f=fixture(),request=await f.controller.prepare(f.event,{left:16,top:78,width:360,height:68},'panel-routes');
 const details={url:'about:blank',frameName:request.name},options=f.controller.open(f.owner,details).overrideBrowserWindowOptions;
 assert.equal(options.height,68);assert.equal(options.frame,false);assert.equal(options.transparent,true);assert.equal(options.backgroundColor,'#00000000');
 const child=new f.Window();f.controller.created(f.owner,child,details);child.setBounds({x:116,y:900,width:360,height:68});
 const expanded=f.controller.resizeRoutes(f.event,request.name,368);assert.equal(expanded.ok,true);assert.equal(child.bounds.y,900);assert.equal(child.bounds.height,132);assert.equal(expanded.height,132);
 f.controller.resizeRoutes(f.event,request.name,68);assert.equal(child.bounds.y,900);assert.equal(child.bounds.height,68);
 assert.equal(f.controller.resizeRoutes({owner:{kind:'ide'}},request.name,360).ok,false);
 assert.equal(f.controller.resizeRoutes(f.event,request.name,NaN).ok,false);assert.equal(f.controller.resizeRoutes(f.event,request.name,9000).ok,false);
 f.owner.revision++;assert.equal(f.controller.resizeRoutes(f.event,request.name,360).ok,false);child.destroy();
});

test('小さな軌跡パネル: 負座標の実画面内へ収め、DPI倍率を二重適用しない',()=>{
 const screens=[{x:-1600,y:200,width:1500,height:860},{x:0,y:0,width:1920,height:1040}];
 for(const zoom of [.8,1,1.5,2]){
  const owner={window:{getContentBounds:()=>({x:-1500,y:220}),webContents:{getZoomFactor:()=>zoom}}};
  const result=panelBounds({left:1400,top:800,width:420,height:360},owner,{getDisplayMatching:()=>({workArea:screens[0]})});
  assert.ok(result.x>=-1600&&result.x+result.width<=-100);assert.ok(result.y>=200&&result.y+result.height<=1060);
  assert.equal(result.width,420*zoom);assert.equal(result.height,360*zoom);
 }
});
