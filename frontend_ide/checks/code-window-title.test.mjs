// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {EventEmitter} from 'node:events';
import vm from 'node:vm';
import routerModule from '../デスクトップ/draft-router.cjs';
import panelModule from '../デスクトップ/panel-windows.cjs';
import codeDragModule from '../デスクトップ/code-drag.cjs';
const tick=()=>new Promise(resolve=>setImmediate(resolve));

async function desktopFixture(){
 const reserved=new Set();
 const handlers=new Map(),state={active:true,mode:'online',startedAt:10,project:{path:'/project'}};
 class Window extends EventEmitter{
  constructor(options){super();this.options=options;this.title=options.title;this.bounds=options;this.webContents=new EventEmitter();this.webContents.mainFrame={url:''};this.webContents.setWindowOpenHandler=()=>{};this.webContents.executeJavaScript=async()=>{};}
  isDestroyed(){return !!this.destroyed;}
  getBounds(){return this.bounds;}
  setBounds(bounds){this.bounds=bounds;}
  setAlwaysOnTop(){}
  setTitle(title){this.title=title;}
  getTitle(){return this.title;}
  async loadURL(url){this.webContents.mainFrame.url=url.split('#')[0];}
  destroy(){this.destroyed=true;this.emit('closed');}
  isMinimized(){return false;}
  show(){}
  focus(){this.emit('focus');}
 }
 const app={setName(){},getPath:()=>'/tmp',setPath(){},requestSingleInstanceLock:()=>true,on(){},whenReady:()=>Promise.resolve(),quit(){}};
 const modules={
  electron:{app,BrowserWindow:Window,ipcMain:{handle:(name,fn)=>handlers.set(name,fn),on(){}},shell:{},clipboard:{},session:{defaultSession:{setPermissionCheckHandler(){},setPermissionRequestHandler(){}}},screen:{getDisplayMatching:()=>({workArea:{}}),getDisplayNearestPoint:()=>({workArea:{}}),getCursorScreenPoint:()=>({})},dialog:{}},
  'node:path':{join:(...parts)=>parts.join('/')},'node:fs':{mkdirSync(){}},
  './デスクトップ/project-profile.cjs':{projectProfile:()=>'/tmp/test'},'./デスクトップ/window-layout.cjs':{windowBounds:()=>({}),windowMinimumSize:()=>({})},'./デスクトップ/term-window-slot.cjs':{reserveTermSlot:async()=>{let slot=0;while(reserved.has(slot))slot++;reserved.add(slot);return{slot,close(){reserved.delete(slot);}};}},
  './host/scripts/window-opening.cjs':{拡大表示:async(_Window,window)=>{window.focus();return true;}},
  './デスクトップ/draft-router.cjs':routerModule,'./デスクトップ/desktop-session.cjs':{readDevelopmentState:async()=>structuredClone(state)},
  './デスクトップ/native-preview-actions.cjs':{createNativePreviewActions:()=>({invalidate(){}})},
  './デスクトップ/panel-windows.cjs':panelModule,'./デスクトップ/code-drag.cjs':codeDragModule,
 };
 const source=readFileSync(new URL('../desktop.cjs',import.meta.url),'utf8');
 const api=vm.runInNewContext(`(()=>{${source}\nreturn {createWindow,windows,draftRouter};})()`,{require:id=>{if(!(id in modules))throw Error(id);return modules[id];},process:{env:{AIDIY_DEVELOPMENT_URL:'http://127.0.0.1:1234/',AIDIY_DEVELOPMENT_KIND:'ide'},cwd:()=>'/project',on(){}},__dirname:'/fixture',console,setInterval:()=>({unref(){}}),clearInterval(){}});
 await tick();const owner=[...api.windows.values()][0];
 return{...api,owner,handlers,event:record=>({sender:record.window.webContents,senderFrame:record.window.webContents.mainFrame}),
  async code(){const window=await api.createWindow('code','http://127.0.0.1:5678/',undefined,owner,'online:10');const record=api.windows.get(window.webContents);api.draftRouter.register(record,{kind:'code',contextId:`context-${record.slot}`,projectPath:'/project',label:'Code'});return record;}};
}

test('IDE Code番号: 実createWindowのslotをタイトル・限定IPC・連携先一覧で共有し、閉鎖後の再利用も一致する',async()=>{
 const f=await desktopFixture();const first=await f.code(),second=await f.code(),third=await f.code();
 const verify=async records=>{
  const snapshot=await f.draftRouter.list(f.owner);
  for(const record of records){const label=`Code ${record.slot+1}`;
   assert.equal(record.window.getTitle(),`AiDiy IDE / ${label}`);
   assert.equal(f.handlers.get('development:window')(f.event(record),'title'),`AiDiy IDE / ${label}`);
   assert.equal(snapshot.targets.find(target=>target.id===record.draftId).label,label);
  }
 };
 await verify([first,second,third]);assert.deepEqual([first.slot,second.slot,third.slot],[0,1,2]);
 second.window.destroy();const reopened=await f.code();assert.equal(reopened.slot,1);assert.notEqual(reopened.draftId,second.draftId);
 await verify([first,third,reopened]);
 first.window.destroy();third.window.destroy();reopened.window.destroy();const restarted=await f.code();assert.equal(restarted.slot,0);await verify([restarted]);
 assert.equal(f.handlers.get('development:window')({sender:{},senderFrame:{}},'title'),undefined);
 const standalone=await f.createWindow('code','http://127.0.0.1:6789/');assert.equal(standalone.getTitle(),'AiDiy Code');
});

test('preloadタイトル: 任意IPCを公開せずホストの同一ウィンドウタイトルだけを取得する',async()=>{
 let api;const calls=[];
 vm.runInNewContext(readFileSync(new URL('../デスクトップ/preload.cjs',import.meta.url),'utf8'),{require:()=>({contextBridge:{exposeInMainWorld(_name,value){api=value;}},ipcRenderer:{invoke:(...args)=>{calls.push(args);return Promise.resolve('AiDiy IDE / Code 2');}}})});
 assert.equal(await api.title(),'AiDiy IDE / Code 2');assert.deepEqual(calls,[['development:window','title']]);assert.equal(api.invoke,undefined);
});


test('IDE Term番号: 共有配置slot・タイトルIPC・閉鎖後の再利用が一致し、単独Termは従来タイトルを保つ',async()=>{
 const f=await desktopFixture();
 const create=async owner=>{const window=await f.createWindow('term','http://127.0.0.1:6789/',undefined,owner,'online:10');return f.windows.get(window.webContents);};
 const standalone=await create();assert.equal(standalone.slot,0);assert.equal(standalone.window.getTitle(),'AiDiy Term');
 const terms=await Promise.all([create(f.owner),create(f.owner),create(f.owner)]);
 assert.deepEqual(terms.map(record=>record.slot),[1,2,3]);
 const verify=record=>{
  const title=`AiDiy IDE / Term ${record.slot+1}`;
  assert.equal(record.window.getTitle(),title);
  assert.equal(f.handlers.get('development:window')(f.event(record),'title'),title);
  let prevented=false;record.window.title='shell title';record.window.webContents.emit('page-title-updated',{preventDefault(){prevented=true;}});
  assert.equal(prevented,true);assert.equal(record.window.getTitle(),title);
 };
 terms.forEach(verify);
 terms[1].window.destroy();const reopened=await create(f.owner);assert.equal(reopened.slot,2);verify(reopened);
 standalone.window.destroy();const first=await create(f.owner);assert.equal(first.slot,0);verify(first);
 assert.equal(f.handlers.get('development:window')({...f.event(first),senderFrame:{url:first.url}},'title'),undefined);
 for(const record of [...terms,reopened,first])if(!record.window.isDestroyed())record.window.destroy();
 const restarted=await create(f.owner);assert.equal(restarted.slot,0);verify(restarted);
 restarted.window.destroy();
});
