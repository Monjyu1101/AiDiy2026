import test from 'node:test';
import assert from 'node:assert/strict';
import {EventEmitter,once} from 'node:events';
import {mkdtemp,mkdir,writeFile,rm,readFile} from 'node:fs/promises';
import {Readable} from 'node:stream';
import {spawn} from 'node:child_process';
import os from 'node:os';
import path from 'node:path';
import vm from 'node:vm';
import {browserMode,desktopBinary,openDesktop,closeDesktop} from '../desktop.mjs';
const url='http://127.0.0.1:1234/#token='+'a'.repeat(43);
function childFixture(){const child=new EventEmitter();child.stderr=new EventEmitter();child.send=()=>{};child.kill=()=>{};return child;}
async function mainFixture(){
 const source=await readFile(new URL('../electron-main.cjs',import.meta.url),'utf8');
 const stdin=Readable.from([]),proc=new EventEmitter(),app=new EventEmitter(),policy={},sent=[],exits=[],handlers={};
 Object.assign(proc,{stdin,pid:42,platform:'win32',connected:true,send:(message,callback)=>{sent.push(message);callback?.();}});
 let options,win,loaded;app.whenReady=async()=>{};app.quit=()=>{app.quitting=true;};app.exit=code=>exits.push(code);
 const session={fromPartition(name){assert.ok(!name.startsWith('persist:'));return {setPermissionRequestHandler(fn){policy.permission=fn;},setPermissionCheckHandler(fn){policy.check=fn;},webRequest:{onBeforeRequest(fn){policy.request=fn;}}};}};
 class Window extends EventEmitter {constructor(value){super();options=value;win=this;this.webContents=new EventEmitter();this.webContents.mainFrame={};this.webContents.setWindowOpenHandler=fn=>{policy.window=fn;};}isDestroyed(){return false;}isMaximized(){return !!this.maximized;}maximize(){this.maximized=true;}unmaximize(){this.maximized=false;}minimize(){this.minimized=true;}close(){this.closed=true;}setMenuBarVisibility(){}show(){this.shown=true;}async loadURL(value){loaded=value;}}
 vm.runInNewContext(source,{__dirname:'/fixture',require:id=>id==='node:path'?path:({app,BrowserWindow:Window,session,ipcMain:{handle:(name,fn)=>handlers[name]=fn}}),process:proc,URL,setTimeout:()=>({unref(){}}),clearTimeout(){}});
 return {stdin,proc,app,policy,sent,exits,handlers,get options(){return options;},get win(){return win;},get loaded(){return loaded;}};
}
test('desktop default; explicit browser, Codespaces, headless remain Node-only',()=>{
 assert.equal(browserMode({}, {DISPLAY:':1'},'linux'),false);assert.equal(browserMode({}, {},'win32'),false);
 for(const [options,env] of [[{browser:true},{}],[{noOpen:true},{}],[{},{CODESPACES:'true'}],[{},{}]])assert.equal(browserMode(options,env,'linux'),true);
});
test('desktop binary requires matching installed package and dist',async()=>{
 const root=await mkdtemp(path.join(os.tmpdir(),'diag-electron-'));const folder=path.join(root,'node_modules/electron');
 try {await mkdir(path.join(folder,'dist'),{recursive:true});await writeFile(path.join(folder,'package.json'),JSON.stringify({version:'1.2.3'}));await writeFile(path.join(folder,'dist/version'),'1.2.3');await writeFile(path.join(folder,'path.txt'),'electron');await writeFile(path.join(folder,'dist/electron'),'fixture',{mode:0o755});assert.equal(await desktopBinary(root,'linux'),path.join(folder,'dist/electron'));await writeFile(path.join(folder,'dist/version'),'9.9.9');await assert.rejects(desktopBinary(root,'linux'));}finally{await rm(root,{recursive:true,force:true});}
});
test('desktop auth travels IPC only after readiness, never stdin/argv/env',()=>{
 let call,payload,sends=0;const child=childFixture();child.send=value=>{payload=value;sends++;};
 openDesktop('/fixture/electron',url,()=>{},(...args)=>{call=args;return child;});
 assert.equal(payload,undefined);assert.ok(!JSON.stringify(call).includes('#token='));assert.deepEqual(call[2].stdio,['ignore','ignore','pipe','ipc']);assert.equal(call[2].shell,false);assert.equal(call[2].env.ELECTRON_RUN_AS_NODE,undefined);
 child.emit('message',{type:'diag-ready'});assert.equal(payload.url,url);child.emit('message',{type:'diag-ready'});assert.equal(sends,1);child.emit('message',{type:'diag-shown'});child.emit('exit',0,null);
});
test('Windows EOF stdin no longer exits; IPC starts a secure Electron window',async()=>{
 const f=await mainFixture();f.stdin.resume();await once(f.stdin,'end');assert.deepEqual(f.exits,[]);assert.equal(f.sent[0].type,'diag-ready');assert.equal(f.options,undefined);
 f.proc.emit('message',{type:'diag-start',url});await new Promise(r=>setImmediate(r));
 assert.equal(f.options.webPreferences.nodeIntegration,false);assert.equal(f.options.webPreferences.contextIsolation,true);assert.equal(f.options.webPreferences.sandbox,true);assert.equal(f.loaded,url);
 const {policy,win}=f;assert.equal(policy.check(),false);policy.permission(null,'camera',allowed=>assert.equal(allowed,false));assert.equal(policy.window().action,'deny');
 let blocked=false;win.webContents.emit('will-navigate',{preventDefault(){blocked=true;}});assert.ok(blocked);policy.request({url:'https://outside.test/'},value=>assert.equal(value.cancel,true));
 win.emit('ready-to-show');assert.equal(win.shown,true);assert.equal(f.sent.at(-1).type,'diag-shown');
 f.proc.emit('disconnect');assert.equal(f.app.quitting,true);
});
test('Electron invalid message / URL and page failure emit fixed secret-free causes',async()=>{
 for(const [message,code] of [[{type:'other',url},'IPC'],[{type:'diag-start',url:'https://private.test/SECRET'},'URL'],[{type:'diag-start',url:'x'.repeat(4097)},'IPC']]){
  const f=await mainFixture();f.proc.emit('message',message);await new Promise(r=>setImmediate(r));assert.equal(f.sent.at(-1).code,code);assert.deepEqual(f.exits,[1]);assert.ok(!JSON.stringify(f.sent).includes('SECRET'));
 }
 const f=await mainFixture();f.proc.emit('message',{type:'diag-start',url});await new Promise(r=>setImmediate(r));f.win.webContents.emit('did-fail-load',{},-2,'SECRET',url,true);assert.equal(f.sent.at(-1).code,'LOAD');assert.deepEqual(f.exits,[1]);
});
test('unexpected exit is failure; normal disconnect/exit and intentional close stay quiet',()=>{
 const original=process.exitCode,originalError=console.error;const errors=[];console.error=value=>errors.push(value);
 try {for(const mode of ['failure','normal','closing']) {
  const child=childFixture();let closes=0;openDesktop('/fixture',url,()=>closes++,()=>child);process.exitCode=0;
  if(mode==='normal'){child.emit('message',{type:'diag-ready'});child.emit('message',{type:'diag-shown'});child.emit('disconnect');}
  if(mode==='closing')child.diagClosing=true;
  child.emit('exit',mode==='normal'?0:7,null);assert.equal(process.exitCode,mode==='failure'?1:0);assert.equal(closes,1);
 }assert.equal(errors.length,1);assert.match(errors[0],/exit=7/);}finally{process.exitCode=original;console.error=originalError;}
});
test('startup timeout and send errors stop children once; stderr secrets never escape',async()=>{
 const original=process.exitCode,originalError=console.error;const errors=[];console.error=value=>errors.push(value);
 try {for(const mode of ['timeout','send']){
  const child=childFixture();let closes=0;openDesktop('/fixture',url,()=>closes++,()=>child,10);
  child.stderr.emit('data','SECRET '+url+' error while loading shared libraries');
  if(mode==='send'){child.send=(_value,callback)=>callback(Error('SECRET'));child.emit('message',{type:'diag-ready'});}
  await new Promise(r=>setTimeout(r,25));assert.equal(child.diagClosing,true);assert.equal(closes,1);child.emit('exit',1,null);assert.equal(closes,1);
 }assert.equal(errors.length,2);assert.ok(!errors.join('').includes('SECRET'));assert.ok(!errors.join('').includes('#token'));}finally{process.exitCode=original;console.error=originalError;}
});
test('real child-process IPC readiness and secret transport smoke',{timeout:10000},async()=>{
 const root=await mkdtemp(path.join(os.tmpdir(),'diag-ipc-'));let child;
 try{
  const file=path.join(root,'child.cjs');await writeFile(file,`process.send({type:'diag-ready'});process.once('message',m=>{if(m.type!=='diag-start'||!m.url.includes('#token=')||JSON.stringify(process.argv).includes('#token=')||JSON.stringify(process.env).includes('#token='))process.exit(1);process.send({type:'diag-shown'},()=>process.exit(0));});`);
  let done;const closed=new Promise(resolve=>done=resolve);
  child=openDesktop('/fixture',url,done,(_exe,_args,options)=>spawn(process.execPath,[file],options));await closed;assert.equal(child.exitCode,0);
 }finally{if(child?.exitCode===null)child.kill('SIGKILL');await rm(root,{recursive:true,force:true});}
});
test('desktop teardown escalates after bounded grace period',async()=>{
 const signals=[],child=childFixture();child.kill=signal=>signals.push(signal);closeDesktop(child,15);await new Promise(r=>setTimeout(r,35));assert.deepEqual(signals,['SIGTERM','SIGKILL']);assert.equal(child.diagClosing,true);
});

test('spawn errors expose only allowlisted OS code and finish once',()=>{
 const original=process.exitCode,originalError=console.error;const errors=[];console.error=value=>errors.push(value);
 try{const child=childFixture();let closes=0;openDesktop('/fixture',url,()=>closes++,()=>child);child.emit('error',Object.assign(Error('SECRET'),{code:'ENOENT'}));child.emit('exit',1,null);assert.equal(closes,1);assert.equal(errors.length,1);assert.match(errors[0],/ENOENT/);assert.ok(!errors[0].includes('SECRET'));}
 finally{process.exitCode=original;console.error=originalError;}
});
test('mixed-case Windows Node bootstrap environment cannot change Electron mode',()=>{
 const names=['electron_run_as_node','Node_Options','node_path'],saved=names.map(name=>process.env[name]);
 try{for(const name of names)process.env[name]='untrusted';let options;const child=childFixture();openDesktop('/fixture',url,()=>{},(_exe,_args,value)=>{options=value;return child;});for(const name of names)assert.equal(options.env[name],undefined);child.diagClosing=true;child.emit('exit',0,null);}
 finally{names.forEach((name,index)=>{if(saved[index]===undefined)delete process.env[name];else process.env[name]=saved[index];});}
});

test('frameless controls are fixed, main-frame-only and preserve sandbox',async()=>{
 const f=await mainFixture();f.proc.emit('message',{type:'diag-start',url});await new Promise(r=>setImmediate(r));
 assert.equal(f.options.frame,false);assert.equal(f.options.webPreferences.preload,'/fixture/preload.cjs');
 const control=f.handlers['diag:window'],event={sender:f.win.webContents,senderFrame:f.win.webContents.mainFrame};
 control({...event,senderFrame:{}},'close');assert.equal(f.win.closed,undefined);
 control({...event,sender:{}},'close');assert.equal(f.win.closed,undefined);
 control(event,'openFile');assert.equal(f.win.closed,undefined);
 control(event,'minimize');assert.equal(f.win.minimized,true);control(event,'maximize');assert.equal(control(event,'isMaximized'),true);control(event,'maximize');assert.equal(control(event,'isMaximized'),false);control(event,'close');assert.equal(f.win.closed,true);
 const exposed={};vm.runInNewContext(await readFile(new URL('../preload.cjs',import.meta.url),'utf8'),{require:()=>({contextBridge:{exposeInMainWorld:(name,api)=>exposed[name]=api},ipcRenderer:{invoke:(...args)=>args}})});
 assert.deepEqual(Object.keys(exposed.aidiyWindow).sort(),['close','isMaximized','maximize','minimize']);assert.deepEqual(Array.from(exposed.aidiyWindow.close()),['diag:window','close']);
});
