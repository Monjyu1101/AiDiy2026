// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,readFile,rm,readdir} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {EventEmitter,once} from 'node:events';
import {WebSocket} from 'ws';
import bridgeModule from '../デスクトップ/ブラウザCDP.cjs';
test('Browser CDP: 専用ページだけ公開、tools切断・別ドメイン拒否、所有パネルだけ終了',async t=>{
 const directory=await mkdtemp(join(tmpdir(),'aidiy-cdp-test-'));t.after(()=>rm(directory,{recursive:true,force:true}));
 let connected=true,closed=0,destroyed=false;const commands=[];
 const contents=new EventEmitter();Object.assign(contents,{getTitle:()=> 'test',getURL:()=> 'https://example.com/',isDestroyed:()=>destroyed});
 const debuggerAPI=new EventEmitter();Object.assign(debuggerAPI,{isAttached:()=>true,sendCommand:async(method,params)=>{commands.push({method,params});return{ok:true};}});
 Object.defineProperty(contents,'debugger',{get(){if(destroyed)throw Error('Object has been destroyed');return debuggerAPI;}});
 const record={window:{close(){closed++;destroyed=true;contents.emit('destroyed');},isMinimized:()=>false,show(){},focus(){}}};
 const bridge=await bridgeModule.createBrowserCDP({directory,canUse:async()=>connected,openPanel:async()=>record,allowedURL:url=>/^https?:/.test(url)});t.after(()=>bridge.close());bridge.add(record,contents);
 assert.equal(bridge.name,'aidiy_ide');
 const manifest=JSON.parse(await readFile(join(directory,'aidiy_ide.json'),'utf8')),base=`http://127.0.0.1:${manifest.port}/${manifest.token}`;
 assert.equal((await fetch(base+'/json',{headers:{Origin:'https://untrusted.example'}})).status,403);
 assert.equal((await fetch(`http://127.0.0.1:${manifest.port}/json`)).status,404);
 const tabs=await(await fetch(base+'/json')).json();assert.equal(tabs.length,1);assert.equal(tabs[0].title,'test');assert.equal(tabs[0].type,'page');
 const socket=new WebSocket(tabs[0].webSocketDebuggerUrl);await once(socket,'open');t.after(()=>socket.terminate());
 let id=0;const call=async(method,params={})=>{const pending=once(socket,'message');socket.send(JSON.stringify({id:++id,method,params}));return JSON.parse((await pending)[0]);};
 assert.equal((await call('Runtime.evaluate',{expression:'1+1'})).result.ok,true);
 for(const method of ['Target.getTargets','Browser.close','Page.navigate'])assert.ok((await call(method,{url:'file:///secret'})).error);
 assert.equal(commands.length,1);
 connected=false;assert.equal((await fetch(base+'/json')).status,409);assert.ok((await call('Runtime.evaluate')).error);
 connected=true;const ended=once(socket,'close');await fetch(base+'/close');await ended;assert.equal(closed,1);assert.equal(debuggerAPI.listenerCount('message'),0);
 bridge.close();assert.deepEqual(await readdir(directory),[]);
});
