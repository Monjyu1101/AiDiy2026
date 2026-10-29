// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import test from 'node:test';
import assert from 'node:assert/strict';
import {EventEmitter} from 'node:events';
import {mkdtempSync,mkdirSync,readFileSync,realpathSync,rmSync,symlinkSync,writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {dirname,join} from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import vm from 'node:vm';
import profiles from '../デスクトップ/project-profile.cjs';


const {projectIdentity,projectProfile}=profiles;
const require=createRequire(import.meta.url),desktopPath=fileURLToPath(new URL('../desktop.cjs',import.meta.url));
const desktopRequire=createRequire(desktopPath),desktopSource=readFileSync(desktopPath,'utf8');

function desktop({project,cwd=project,kind='ide',url='http://127.0.0.1:12345/',appData,locks,newWindow=false}){
 const app=new EventEmitter(),process=new EventEmitter(),windows=[],messages=[],paths={appData,temp:appData},order=[];
 const ipcMain=new EventEmitter(),handlers=new Map();ipcMain.handle=(name,handler)=>handlers.set(name,handler);
 let ready=Promise.resolve(),connected=true,bridgeOptions,bridgeClosed=0;const pages=[],availability=[];const bridge={name:'aidiy_browser',add(record,page){pages.push({record,page});},close(){bridgeClosed++;}};
 app.getPath=name=>paths[name];app.setPath=(name,path)=>{paths[name]=path;order.push(name);};app.setName=()=>{};
 app.requestSingleInstanceLock=()=>{
  order.push('lock');const existing=locks.get(paths.userData);
  if(existing){existing.emit('second-instance');return false;}
  locks.set(paths.userData,app);return true;
 };
 app.exit=code=>{app.exitCode=code;if(locks.get(paths.userData)===app)locks.delete(paths.userData);app.emit('quit');};
 app.quit=()=>{let prevented=false;app.emit('before-quit',{preventDefault(){prevented=true;}});if(!prevented)app.exit(0);};
 app.whenReady=()=>({then:callback=>ready=Promise.resolve().then(callback)});
 process.env={AIDIY_DEVELOPMENT_KIND:kind,AIDIY_DEVELOPMENT_URL:url,AIDIY_DEVELOPMENT_NEW_WINDOW:newWindow?'1':'0',...(project?{AIDIY_DEVELOPMENT_PROJECT:project}:{})};
 process.cwd=()=>cwd;process.send=(message,callback)=>{messages.push(message);callback?.();};
 class Window extends EventEmitter{
  constructor(options){super();this.options=options;this.webContents=new EventEmitter();this.webContents.mainFrame={};this.webContents.setWindowOpenHandler=()=>{};this.webContents.executeJavaScript=async()=>{};this.webContents.send=()=>{};windows.push(this);}
  setBounds(bounds){this.bounds=bounds;}getBounds(){return this.bounds;}
  isDestroyed(){return !!this.destroyed;}isMinimized(){return !!this.minimized;}
  minimize(){this.minimized=true;}restore(){this.minimized=false;this.restored=true;}
  show(){this.visible=true;}focus(){this.focused=true;this.focusCount=(this.focusCount||0)+1;}
  async loadURL(url){this.url=url;this.webContents.mainFrame.url=url;}setAlwaysOnTop(){}isAlwaysOnTop(){return false;}
  close(){this.destroy();}destroy(){if(this.destroyed)return;this.destroyed=true;this.emit('closed');}
 }
 const area={x:0,y:0,width:1920,height:1080};
 const electron={app,BrowserWindow:Window,ipcMain,shell:{},dialog:{},session:{defaultSession:{setPermissionCheckHandler(){},setPermissionRequestHandler(){}}},screen:Object.assign(new EventEmitter(),{getCursorScreenPoint:()=>({x:0,y:0}),getDisplayNearestPoint:()=>({workArea:area}),getDisplayMatching:()=>({workArea:area})})};
 const load=name=>name==='electron'?electron:name==='./host/scripts/window-opening.cjs'?{拡大表示:async(_type,window)=>{window.show();window.focus();return true;}}
  :name==='./デスクトップ/desktop-session.cjs'?{readDevelopmentState:async()=>({active:true,mode:'online',connected,startedAt:1,project:{path:project}})}:name==='./デスクトップ/ブラウザCDP.cjs'?{createBrowserCDP:async options=>{bridgeOptions=options;return bridge;}}:name==='./デスクトップ/ブラウザ.cjs'?{HOME:'https://www.google.com/',createBrowserViews:()=>({allowedURL:()=>true,attach:()=>new EventEmitter(),setAvailable:(record,value)=>availability.push({record,value}),action:async()=>({ok:true}),maximize:record=>{record.window.browserMaximized=true;return true;}})}:desktopRequire(name);
 vm.runInNewContext(`(function(require,__dirname,process){${desktopSource}\n})`,{console,setInterval,clearInterval,URL})(load,dirname(desktopPath),process);
 return{app,process,windows,messages,paths,order,pages,availability,setConnected(value){connected=value;},get bridgeOptions(){return bridgeOptions;},get bridgeClosed(){return bridgeClosed;},ready:()=>ready,request:(name,window,...args)=>handlers.get(name)({sender:window.webContents,senderFrame:window.webContents.mainFrame},...args)};
}

test('Standalone Browser: 専用プロファイル、共有CDP、最終窓終了、Tools切断、他プロセス分離',async t=>{
 const root=mkdtempSync(join(tmpdir(),'aidiy-browser-desktop-'));t.after(()=>rmSync(root,{recursive:true,force:true}));
 const a=desktop({kind:'browser',project:root,appData:root,locks:new Map()});await a.ready();
 const b=desktop({kind:'browser',project:root,appData:root,locks:new Map()});await b.ready();
 t.after(()=>{a.app.quit();b.app.quit();});
 assert.equal(a.windows.length,1);assert.equal(a.windows[0].url,'http://127.0.0.1:12345/#browser');
 assert.match(a.windows[0].options.icon,/AiDiy\.png$/);assert.match(a.windows[0].options.title,/AiDiy Browser/);
 assert.equal(a.windows[0].options.enableLargerThanScreen,true);assert.equal(await a.request('development:window',a.windows[0],'maximize'),true);assert.equal(a.windows[0].browserMaximized,true);
 assert.notEqual(a.paths.userData,b.paths.userData);assert.equal(a.paths.userData,a.paths.sessionData);assert.ok(!a.order.includes('lock'));
 assert.equal(a.bridgeOptions.sessionPrefix,'aidiy_browser');assert.equal(await a.bridgeOptions.canUse(),true);
 const second=await a.bridgeOptions.openPanel('https://example.com/');assert.equal(a.windows.length,2);assert.equal(second.owner,undefined);
 assert.equal(a.pages.length,2);assert.equal(a.messages[0].windowShown,true);
 a.setConnected(false);assert.equal(await a.bridgeOptions.canUse(),false);
 assert.equal((await a.request('development:browser-action',a.windows[0],'size','portrait')).ok,true);
 assert.equal((await a.request('development:browser-action',a.windows[0],'fullscreen')).ok,true);
 assert.equal((await a.request('development:browser-action',a.windows[0],'navigate','https://example.com/')).ok,false);
 await assert.rejects(a.bridgeOptions.openPanel('https://example.com/'),/tools/);
 a.setConnected(true);assert.equal((await a.request('development:browser-action',a.windows[0],'navigate','https://example.com/')).ok,true);
 a.windows[0].destroy();await new Promise(resolve=>setImmediate(resolve));assert.equal(a.bridgeClosed,0);assert.equal(await a.bridgeOptions.canUse(),true);
 second.window.destroy();await new Promise(resolve=>setImmediate(resolve));assert.equal(a.bridgeClosed,1);assert.equal(b.bridgeClosed,0);assert.equal(await b.bridgeOptions.canUse(),true);
 b.process.emit('disconnect');await new Promise(resolve=>setImmediate(resolve));assert.equal(b.bridgeClosed,1);assert.equal(b.windows[0].destroyed,true);
});
