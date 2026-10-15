import test from 'node:test';
import assert from 'node:assert/strict';
import {EventEmitter} from 'node:events';
import {mkdtemp,mkdir,writeFile,rm,readFile} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import vm from 'node:vm';
import {browserMode,desktopBinary,openDesktop} from '../desktop.mjs';
test('desktop default; explicit browser, Codespaces, headless remain Node-only',()=>{
 assert.equal(browserMode({}, {DISPLAY:':1'},'linux'),false);
 assert.equal(browserMode({}, {},'win32'),false);
 for(const [options,env] of [[{browser:true},{}],[{noOpen:true},{}],[{},{CODESPACES:'true'}],[{},{}]])assert.equal(browserMode(options,env,'linux'),true);
});
test('desktop binary requires matching installed package and dist',async()=>{
 const root=await mkdtemp(path.join(os.tmpdir(),'diag-electron-'));const folder=path.join(root,'node_modules/electron');
 try {await mkdir(path.join(folder,'dist'),{recursive:true});await writeFile(path.join(folder,'package.json'),JSON.stringify({version:'1.2.3'}));await writeFile(path.join(folder,'dist/version'),'1.2.3');await writeFile(path.join(folder,'path.txt'),'electron');await writeFile(path.join(folder,'dist/electron'),'fixture',{mode:0o755});assert.equal(await desktopBinary(root,'linux'),path.join(folder,'dist/electron'));await writeFile(path.join(folder,'dist/version'),'9.9.9');await assert.rejects(desktopBinary(root,'linux'));}finally{await rm(root,{recursive:true,force:true});}
});
test('desktop auth URL only travels stdin, not argv or environment',()=>{
 let call,payload;const child=new EventEmitter();child.stdin=new EventEmitter();child.stdin.end=value=>{payload=value;};
 openDesktop('/fixture/electron','http://127.0.0.1:1234/#token=secret',()=>{},(...args)=>{call=args;return child;});
 assert.ok(!JSON.stringify(call).includes('#token=secret'));assert.equal(JSON.parse(payload).url,'http://127.0.0.1:1234/#token=secret');assert.equal(call[2].shell,false);assert.equal(call[2].env.ELECTRON_RUN_AS_NODE,undefined);
});
test('Electron window uses sandboxed renderer, isolated session and rejects navigation/permissions',async()=>{
 const source=await readFile(new URL('../electron-main.cjs',import.meta.url),'utf8');const stdin=new EventEmitter();stdin.setEncoding=()=>{};const app=new EventEmitter();app.whenReady=async()=>{};app.quit=()=>{};
 const policy={};let options,win,loaded;
 const session={fromPartition(name){assert.ok(!name.startsWith('persist:'));return {setPermissionRequestHandler(fn){policy.permission=fn;},setPermissionCheckHandler(fn){policy.check=fn;},webRequest:{onBeforeRequest(fn){policy.request=fn;}}};}};
 class Window extends EventEmitter {constructor(value){super();options=value;win=this;this.webContents=new EventEmitter();this.webContents.setWindowOpenHandler=fn=>{policy.window=fn;};}setMenuBarVisibility(){}show(){}async loadURL(url){loaded=url;}}
 vm.runInNewContext(source,{require:()=>({app,BrowserWindow:Window,session}),process:{stdin,pid:42},URL,setTimeout:()=>1,clearTimeout(){}});
 stdin.emit('data',JSON.stringify({url:'http://127.0.0.1:1234/#token='+'a'.repeat(43)}));stdin.emit('end');await new Promise(r=>setImmediate(r));
 assert.equal(options.webPreferences.nodeIntegration,false);assert.equal(options.webPreferences.contextIsolation,true);assert.equal(options.webPreferences.sandbox,true);assert.ok(loaded);assert.equal(policy.check(),false);policy.permission(null,'camera',allowed=>assert.equal(allowed,false));assert.equal(policy.window().action,'deny');
 let blocked=false;win.webContents.emit('will-navigate',{preventDefault(){blocked=true;}});assert.ok(blocked);policy.request({url:'https://outside.test/'},value=>assert.equal(value.cancel,true));
});
test('Electron unexpected exit is failure; intentional close is quiet',()=>{
 const original=process.exitCode;const originalError=console.error;let errors=0;console.error=()=>errors++;
 try {for(const closing of [false,true]) {
  const child=new EventEmitter();child.stdin=new EventEmitter();child.stdin.end=()=>{};
  openDesktop('/fixture','http://127.0.0.1:1/#token=fixture',()=>{},()=>child);child.diagClosing=closing;process.exitCode=0;child.emit('exit',7,null);assert.equal(process.exitCode,closing?0:1);
 }assert.equal(errors,1);}finally{process.exitCode=original;console.error=originalError;}
});
test('desktop teardown escalates after bounded grace period',async()=>{
 const {closeDesktop}=await import('../desktop.mjs');const signals=[];const child=new EventEmitter();child.kill=signal=>signals.push(signal);
 closeDesktop(child,15);await new Promise(r=>setTimeout(r,35));assert.deepEqual(signals,['SIGTERM','SIGKILL']);assert.equal(child.diagClosing,true);
});
