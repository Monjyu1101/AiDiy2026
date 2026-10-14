// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import layout from '../window-layout.cjs';
const {windowBounds,windowMinimumSize}=layout;
for(const area of [{x:0,y:0,width:1920,height:1040},{x:-1600,y:80,width:1600,height:900},{x:0,y:-900,width:1024,height:728},{x:0,y:0,width:640,height:480}]){
 test(`配置が画面内に収まり、IDEに余白を残す: ${JSON.stringify(area)}`,()=>{
  const ide=windowBounds('ide',area);
  assert.ok(ide.x>area.x&&ide.y>area.y);
  assert.ok(ide.width>area.width*.9&&ide.height>area.height*.9);
  for(const owner of [undefined,ide,{x:area.x-150,y:area.y-100,width:900,height:800}]){
   const code=windowBounds('code',area,owner),live=windowBounds('live',area,owner);
   assert.equal(code.width,480);assert.equal(live.width,480);
   assert.equal(code.height,Math.min(600,area.height-16));assert.equal(live.height,code.height);
   if(!owner){assert.equal(code.x,area.x+8);assert.equal(live.x,area.x+area.width-480-8);assert.equal(code.y,area.y+8);assert.equal(live.y,code.y);}
   for(const b of [ide,code,live,windowBounds('term',area,owner),windowBounds('term',area,owner,3)]){
    assert.ok(b.x>=area.x&&b.y>=area.y);
    assert.ok(b.x+b.width<=area.x+area.width&&b.y+b.height<=area.y+area.height);
   }
   const term=windowBounds('term',area,owner),next=windowBounds('term',area,owner,1);
   assert.equal(term.width,Math.round(area.width*2/3));assert.equal(term.height,Math.round(area.height/2));
   assert.ok(Math.abs(term.x+(term.width/2)-(area.x+area.width/2))<=1);
   assert.equal(term.y+term.height,area.y+area.height-8);
   assert.equal(next.x,term.x+28);assert.equal(next.y,term.y-28);
   if(area.width>1000&&owner===ide){
    assert.equal(code.x,ide.x+24);assert.equal(live.x+live.width,ide.x+ide.width-24);
    assert.ok(code.x<live.x);assert.equal(code.y,live.y);assert.equal(code.height,live.height);
   }
  }
 });
}
test('最小寸法: Termだけ高さ180、横幅・Code/Live/IDE/ビューアは従来どおり',()=>{
 const bounds={width:1000,height:900};
 for(const [kind,minWidth,minHeight] of [['term',360,180],['code',360,480],['live',360,480],['ide',400,550],['viewer',360,480]]){
  assert.deepEqual(windowMinimumSize(kind,bounds),{minWidth,minHeight});
  for(const small of [{width:320,height:160},{width:360,height:180},{width:1,height:1}]){
   assert.deepEqual(windowMinimumSize(kind,small),{minWidth:Math.min(minWidth,small.width),minHeight:Math.min(minHeight,small.height)});
  }
 }
});
test('Electron生成: 単独Term・IDE子Termの双方へ最小寸法を渡し、初期サイズを維持する',async()=>{
 const source=readFileSync(new URL('../desktop.cjs',import.meta.url),'utf8');
 const body=source.slice(source.indexOf('async function createWindow(kind,url,server,owner,linkKey){'),source.indexOf("process.on('disconnect'"));
 const area={x:0,y:0,width:1920,height:1040},windows=new Map();
 class Window{
  constructor(options){this.options=options;this.webContents={on(){},setWindowOpenHandler(){},async executeJavaScript(){}};}
  once(){} on(){} setBounds(bounds){this.bounds=bounds;} getBounds(){return this.bounds;} setAlwaysOnTop(){} isDestroyed(){return false;} async loadURL(){}
 }
 const context={BrowserWindow:Window,windows,windowBounds,windowMinimumSize,screen:{getDisplayMatching:()=>({workArea:area}),getDisplayNearestPoint:()=>({workArea:area}),getCursorScreenPoint:()=>({x:0,y:0})},reserveTermSlot:async()=>({slot:0,close(){}}),quitting:false,join:(...parts)=>parts.join('/'),__dirname:'/fixture',拡大表示:async()=>true,setInterval:()=>({unref(){}})};
 vm.runInNewContext(body+';globalThis.create=createWindow;',context);
 const owner={window:{getBounds:()=>windowBounds('ide',area),isDestroyed:()=>false},revision:0};
 for(const parent of [undefined,owner])for(const kind of ['term','code','live','ide','viewer']){
  const window=await context.create(kind,'http://127.0.0.1:1234/',undefined,parent,'offline:1');
  const bounds=windowBounds(kind,area,parent?.window.getBounds());
  assert.deepEqual(window.bounds,bounds);
  assert.equal(window.options.minHeight,kind==='term'?180:kind==='ide'?550:480);
  assert.equal(window.options.minWidth,kind==='ide'?400:360);
  assert.equal(window.options.height,bounds.height);assert.equal(window.options.width,bounds.width);
  assert.equal(window.options.frame,false);assert.notEqual(window.options.resizable,false);
 }
});
