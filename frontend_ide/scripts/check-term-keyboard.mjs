// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
// 実Vue / xterm / Chromiumのキー・clipboardを検証。PTYだけはfixtureとし、コマンドは実行しない。
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {mkdtempSync,readFileSync,writeFileSync,rmSync,existsSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {startDevelopment} from '../server.mjs';
const project=mkdtempSync(join(tmpdir(),'aidiy-keyboard-project-')),profile=mkdtempSync(join(tmpdir(),'aidiy-keyboard-browser-'));
const app=await startDevelopment(project,{kind:'term'});
const executable=process.env.CHROME_PATH||['/usr/bin/chromium',...[process.env.PROGRAMFILES,process.env['PROGRAMFILES(X86)'],process.env.LOCALAPPDATA].filter(Boolean).map(base=>join(base,'Google/Chrome/Application/chrome.exe'))].find(existsSync);
const browser=spawn(executable,['--headless=new',...(process.platform==='linux'?['--no-sandbox']:[]),'--remote-debugging-port=0',`--user-data-dir=${profile}`,'about:blank'],{stdio:['ignore','ignore','inherit']});
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));let ws;
try{
 let port;for(let i=0;i<100&&!port;i++){if(browser.exitCode!==null)throw Error(`Chrome exited: ${browser.exitCode}`);try{port=readFileSync(join(profile,'DevToolsActivePort'),'utf8').split('\n')[0];}catch{}if(!port)await sleep(100);}assert.ok(port,'Chrome did not start');
 const target=(await fetch(`http://127.0.0.1:${port}/json/list`).then(r=>r.json())).find(t=>t.type==='page');
 ws=new WebSocket(target.webSocketDebuggerUrl);await new Promise(r=>ws.addEventListener('open',r,{once:true}));let id=0;const pending=new Map();
 ws.addEventListener('message',event=>{const message=JSON.parse(event.data);if(pending.has(message.id)){pending.get(message.id)(message);pending.delete(message.id);}});
 const send=(method,params={})=>new Promise(resolve=>{pending.set(++id,resolve);ws.send(JSON.stringify({id,method,params}));});
 const evaluate=async expression=>{const result=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true,userGesture:true});if(result.error||result.result.exceptionDetails)throw Error(JSON.stringify(result));return result.result.result.value;};
 const until=async expression=>{for(let i=0;i<100;i++){if(await evaluate(expression))return;await sleep(50);}throw Error(expression);};
 await send('Page.addScriptToEvaluateOnNewDocument',{source:`window.inputs=[];window.WebSocket=class {static OPEN=1;readyState=1;constructor(){window.termSocket=this;setTimeout(()=>this.onopen?.(),0);}send(raw){const packet=JSON.parse(raw);if(packet.type==='input')inputs.push(packet.data);if(packet.type==='start')setTimeout(()=>this.receive({type:'ready',project:'/fixture',shell:'fixture',completion:false}),0);}receive(packet){this.onmessage?.({data:JSON.stringify(packet)});}close(){this.readyState=3;this.onclose?.();}};`});
 await send('Browser.grantPermissions',{origin:new URL(app.url).origin,permissions:['clipboardReadWrite','clipboardSanitizedWrite']});
 await send('Page.navigate',{url:app.url});await until(`document.querySelector('.term-component')?.textContent.includes('実行中')`);
 const press=async(key,code,keyCode,modifiers=0)=>{await evaluate(`document.querySelector('.xterm-helper-textarea').focus()`);for(const type of ['keyDown','keyUp'])await send('Input.dispatchKeyEvent',{type,key,code,windowsVirtualKeyCode:keyCode,modifiers});await sleep(40);};
 await evaluate(`navigator.clipboard.writeText('貼り付け日本語\nsecond line')`);
 await press('v','KeyV',86,2);assert.deepEqual(await evaluate('inputs.splice(0)'),['貼り付け日本語\rsecond line']);
 await evaluate(`termSocket.receive({type:'data',data:'\\x1b[?2004h'})`);await sleep(60);
 await press('v','KeyV',86,2);assert.deepEqual(await evaluate('inputs.splice(0)'),['\x1b[200~貼り付け日本語\rsecond line\x1b[201~']);
 for(const [modifiers,expected] of [[0,'\r'],[1,'\x1b\r'],[8,'\x1b[13;2u'],[9,'\x1b[13;4u']]){await press('Enter','Enter',13,modifiers);assert.deepEqual(await evaluate('inputs.splice(0)'),[expected]);}
 await press('c','KeyC',67,2);assert.deepEqual(await evaluate('inputs.splice(0)'),[]);
 await press('d','KeyD',68,2);assert.deepEqual(await evaluate('inputs.splice(0)'),['\x04']);
 await press('ArrowUp','ArrowUp',38);assert.deepEqual(await evaluate('inputs.splice(0)'),['\x1b[A']);
 await evaluate(`Array.from(document.querySelectorAll('button')).find(b=>b.textContent==='Ctrl+C送信').click()`);assert.deepEqual(await evaluate('inputs.splice(0)'),['\x03']);
 // ネイティブcopy経路も実xtermの選択モデルで確認する。
 await evaluate(`termSocket.receive({type:'data',data:'copy selection test'})`);await sleep(100);
 const point=await evaluate(`(()=>{const r=document.querySelector('.xterm-screen').getBoundingClientRect();return{x:r.left+20,y:r.top+8};})()`);
 for(const type of ['mousePressed','mouseReleased'])await send('Input.dispatchMouseEvent',{type,...point,button:'left',clickCount:3});
 await press('c','KeyC',67,2);
 assert.ok((await evaluate('navigator.clipboard.readText()')).includes('copy selection test'));
 assert.deepEqual(await evaluate('inputs.splice(0)'),[]);
 await evaluate(`document.querySelector('.xterm-helper-textarea').dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',keyCode:229,shiftKey:true,isComposing:true,bubbles:true,cancelable:true}))`);
 assert.deepEqual(await evaluate('inputs.splice(0)'),[]);
 const screenshot=await send('Page.captureScreenshot',{format:'png'});const screenshotPath=join(tmpdir(),'aidiy-term-keyboard.png');writeFileSync(screenshotPath,Buffer.from(screenshot.result.data,'base64'));
 console.log('PASS: native Ctrl+V, bracketed paste, native copy, modified Enter, button-only Ctrl+C, Ctrl+D, arrows, IME guard. Screenshot:',screenshotPath);
}finally{ws?.close();browser.kill();await app.close();await sleep(200);for(const folder of [profile,project])rmSync(folder,{recursive:true,force:true,maxRetries:5,retryDelay:200});}
