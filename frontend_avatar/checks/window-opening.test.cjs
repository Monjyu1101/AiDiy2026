// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
const test=require('node:test'),assert=require('node:assert/strict');
const {EventEmitter}=require('node:events');
const {readFileSync}=require('node:fs');
const path=require('node:path'),vm=require('node:vm');
const {createRequire}=require('node:module');
const filename=path.join(__dirname,'../dist-electron/main.js'),load=createRequire(filename);
function fixture(){
 const windows=[],openings=[];let gate=Promise.resolve();
 class Window extends EventEmitter{
  constructor(options){super();this.bounds={x:0,y:0,...options};this.visible=options.show;windows.push(this);this.id=windows.length;this.webContents=Object.assign(new EventEmitter(),{isLoading:()=>false,isDestroyed:()=>false,send(){}});}
  async loadURL(url){this.role=new URL(url).searchParams.get('role');queueMicrotask(()=>{this.emit('ready-to-show');this.webContents.emit('did-finish-load');});}
  setAlwaysOnTop(value,level){this.alwaysOnTop=value;this.topLevel=level;}
  setMinimumSize(){}setResizable(){}setPosition(x,y){Object.assign(this.bounds,{x,y});}setBounds(bounds){Object.assign(this.bounds,bounds);}center(){}focus(){}
  show(){this.visible=true;}hide(){this.visible=false;}isVisible(){return this.visible;}isDestroyed(){return !!this.dead;}isMinimized(){return false;}
  destroy(){this.dead=true;this.visible=false;this.emit('closed');}close(){this.destroy();}
  static getAllWindows(){return windows.filter(window=>!window.dead);}
 }
 const context={__dirname:path.dirname(filename),exports:{},console,process:{platform:'win32',env:{}},URL,
  require:id=>id==='electron'?{BrowserWindow:Window,app:{getAppPath:()=>path.join(__dirname,'..'),requestSingleInstanceLock:()=>true,whenReady:()=>({then(){}}),on(){}},screen:{getPrimaryDisplay:()=>({workArea:{x:0,y:0,width:1920,height:1080}})}}
  :id.endsWith('window-opening.cjs')?{拡大表示:async(_Constructor,window,options)=>{assert.equal(window.visible,false);openings.push(window);await gate;if(window.dead||!options.canShow())return false;window.show();return true;}}
  :id.endsWith('長押し窓移動.cjs')?{attachNativeWindowMove(){}}:load(id)};
 vm.runInNewContext(readFileSync(filename,'utf8')+'\nglobalThis.probe={createLoginWindow,createCoreWindow,createPanelWindow,setPanelVisibility,openSettingsWindow,ウィンドウ表示,ウィンドウ非表示};',context);
 return{...context.probe,windows,openings,flush:()=>new Promise(resolve=>setImmediate(resolve)),hold(){let release;gate=new Promise(resolve=>release=resolve);return release;}};
}
test('全12種類の公開表示経路は読込・配置後に共通ズームし、表示中の再要求では繰り返さない',async()=>{
 const f=fixture();f.createLoginWindow();f.createCoreWindow();
 for(const role of ['chat','file','image','code1','code2','code3','code4','code5','code6']){f.createPanelWindow(role);await f.setPanelVisibility(role,true);}
 f.openSettingsWindow('test-session');await f.flush();
 assert.equal(f.windows.length,12);assert.equal(f.openings.length,12);assert.equal(new Set(f.openings).size,12);
 assert.ok(f.windows.every(window=>window.visible));
 for(const window of f.windows)await f.ウィンドウ表示(window);
 assert.equal(f.openings.length,12);
});
test('表示連打を一つへまとめ、ズーム待ちの非表示要求を優先し、次の表示は再開できる',async()=>{
 const f=fixture(),window=f.createPanelWindow('chat'),release=f.hold();
 const first=f.setPanelVisibility('chat',true),second=f.setPanelVisibility('chat',true);await f.flush();assert.equal(f.openings.length,1);
 await f.setPanelVisibility('chat',false);release();await Promise.all([first,second]);assert.equal(window.visible,false);
 await f.setPanelVisibility('chat',true);assert.equal(window.visible,true);assert.equal(f.openings.length,2);
});
test('設定画面のズーム待ちに閉じた場合も再表示せず、読み込み中の窓破棄で待機を解除する',async()=>{
 const f=fixture(),release=f.hold();f.openSettingsWindow('test-session');await f.flush();const window=f.windows[0];
 f.ウィンドウ非表示(window);release();await f.flush();assert.equal(window.visible,false);
 const panel=f.createPanelWindow('file');await f.flush();panel.webContents.isLoading=()=>true;
 const showing=f.ウィンドウ表示(panel);panel.destroy();assert.equal(await showing,false);assert.equal(panel.listenerCount('ready-to-show'),0);
});
