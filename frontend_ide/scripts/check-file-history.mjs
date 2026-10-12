// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {existsSync,mkdtempSync,mkdirSync,writeFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join,resolve,sep} from 'node:path';
import {startDevelopment} from '../server.mjs';
const project=mkdtempSync(join(tmpdir(),'aidiy-history-ui-')),profile=mkdtempSync(join(tmpdir(),'aidiy-history-chrome-'));
const lines=Array.from({length:220},(_,i)=>`export const value${i+1} = ${i+1};`);
const previous=[...lines];previous.splice(4,0,'// 旧版だけの行','export const removed = true;');previous[25]='export const value24 = "以前の値";';
mkdirSync(join(project,'src'),{recursive:true});mkdirSync(join(project,'backup/20261010/100000.all/src'),{recursive:true});mkdirSync(join(project,'src/backup/20261011/120000'),{recursive:true});
writeFileSync(join(project,'src/sample.ts'),lines.join('\n'));
writeFileSync(join(project,'backup/20261010/100000.all/src/sample.ts'),lines.join('\n'));
writeFileSync(join(project,'src/backup/20261011/120000/sample.ts'),previous.join('\n'));
writeFileSync(join(project,'no-history.ts'),'export const empty=true;');
const app=await startDevelopment(project);await fetch(app.url+'api/connection/offline',{method:'POST'});
const chromePath=[process.env.PROGRAMFILES,process.env['PROGRAMFILES(X86)'],process.env.LOCALAPPDATA].filter(Boolean).flatMap(base=>['Google/Chrome/Application/chrome.exe','Microsoft/Edge/Application/msedge.exe'].map(tail=>join(base,tail))).find(existsSync);
if(!chromePath)throw Error('Chrome / Edge が見つかりません。');
const port=9500+Math.floor(Math.random()*400),chrome=spawn(chromePath,['--headless=new',`--remote-debugging-port=${port}`,`--user-data-dir=${profile}`,'--window-size=1280,800','about:blank'],{stdio:'ignore',windowsHide:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));let ws;
try{
 let target;for(let i=0;i<50&&!target;i++){try{target=(await fetch(`http://127.0.0.1:${port}/json/list`).then(r=>r.json())).find(t=>t.type==='page');}catch{}if(!target)await sleep(200);}
 if(!target)throw Error('検証ブラウザーに接続できません。');
 ws=new WebSocket(target.webSocketDebuggerUrl);await new Promise(r=>ws.addEventListener('open',r,{once:true}));let id=0;const pending=new Map(),errors=[];
 ws.addEventListener('message',event=>{const message=JSON.parse(event.data);if(pending.has(message.id)){pending.get(message.id)(message);pending.delete(message.id);}if(message.method==='Runtime.exceptionThrown')errors.push(message.params.exceptionDetails.text);});
 const send=(method,params={})=>new Promise(r=>{pending.set(++id,r);ws.send(JSON.stringify({id,method,params}));});
 const evaluate=async expression=>{const result=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(result.error||result.result.exceptionDetails)throw Error(JSON.stringify(result));return result.result.result.value;};
 async function until(expression,message){for(let i=0;i<200;i++){if(await evaluate(expression))return;await sleep(100);}throw Error(message);}
 const stamp=new Intl.DateTimeFormat('sv-SE',{timeZone:'Asia/Tokyo',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).format(new Date()).replace(/\D/g,'');let number=0;
 async function shot(name){const result=await send('Page.captureScreenshot',{format:'png'});const dir=resolve('temp/file-history-check');mkdirSync(dir,{recursive:true});const path=join(dir,`${stamp}_${String(++number).padStart(2,'0')}_${name}.png`);writeFileSync(path,Buffer.from(result.result.data,'base64'));console.log(path);}
 await send('Runtime.enable');await send('Emulation.setDeviceMetricsOverride',{width:1280,height:800,deviceScaleFactor:1,mobile:false});
 await send('Page.navigate',{url:app.url+'#viewer=src/sample.ts'});
 await until(`!!document.querySelector('.viewer-history')`,'バックアップありのボタン');
 // Monaco の実インスタンスを検証側だけで捕捉する。
 await until(`!!window.monaco?.editor`,'Monaco準備');
 // 5分タイマーだけ仮想時計に置き換え、実際のダイアログの操作・破棄を検証する。
 await evaluate(`{const timeout=window.setTimeout.bind(window),clear=window.clearTimeout.bind(window);window.historyClock={now:0,timers:new Map(),id:-1,advance(ms){this.now+=ms;for(const [id,timer] of [...this.timers])if(timer.at<=this.now){this.timers.delete(id);timer.fn();}}};window.setTimeout=(fn,ms,...args)=>{if(ms!==300000)return timeout(fn,ms,...args);const id=historyClock.id--;historyClock.timers.set(id,{at:historyClock.now+ms,fn:()=>fn(...args)});return id;};window.clearTimeout=id=>{if(!historyClock.timers.delete(id))clear(id);};}`);
 await evaluate(`{const create=monaco.editor.createDiffEditor;monaco.editor.createDiffEditor=(...args)=>(window.historyDiff=create(...args));document.querySelector('.viewer-history').click();}`);
 await until(`window.historyDiff?.getLineChanges()?.length>0`,'差分計算完了');
 assert.equal(await evaluate(`document.querySelectorAll('.file-history-toolbar option').length`),2);
 assert.equal(await evaluate(`historyDiff.getOriginalEditor().getModel().getLineContent(5)`),'// 旧版だけの行');
 assert.equal(await evaluate(`historyDiff.getModifiedEditor().getModel().getLineContent(5)`),lines[4]);
 assert.equal(await evaluate(`historyDiff.getOriginalEditor().getOption(monaco.editor.EditorOption.readOnly)&&historyDiff.getModifiedEditor().getOption(monaco.editor.EditorOption.readOnly)`),true);
 const align=await evaluate(`({old:historyDiff.getOriginalEditor().getTopForLineNumber(42),current:historyDiff.getModifiedEditor().getTopForLineNumber(40)})`);
 assert.ok(Math.abs(align.old-align.current)<1,'未変更行が同じ高さに揃う '+JSON.stringify(align));
 await evaluate(`historyDiff.getOriginalEditor().setScrollTop(900)`);await sleep(250);
 assert.equal(await evaluate(`Math.abs(historyDiff.getOriginalEditor().getScrollTop()-historyDiff.getModifiedEditor().getScrollTop())<1`),true,'左→右の同期');
 await evaluate(`historyDiff.getModifiedEditor().setScrollTop(300)`);await sleep(250);
 assert.equal(await evaluate(`Math.abs(historyDiff.getOriginalEditor().getScrollTop()-historyDiff.getModifiedEditor().getScrollTop())<1`),true,'右→左の同期');
 await evaluate(`historyDiff.getModifiedEditor().setScrollTop(0)`);await shot('history-landscape');
 await send('Emulation.setDeviceMetricsOverride',{width:768,height:1000,deviceScaleFactor:1,mobile:false});await sleep(400);
 assert.equal(await evaluate(`(()=>{const a=historyDiff.getOriginalEditor().getDomNode().getBoundingClientRect(),b=historyDiff.getModifiedEditor().getDomNode().getBoundingClientRect();return a.right<=b.left+5&&a.width>200&&b.width>200})()`),true,'縦表示でも左右比較');await shot('history-portrait');
 await evaluate(`{const select=document.querySelector('[aria-label="比較するバックアップ"]');select.selectedIndex=1;select.dispatchEvent(new Event('change',{bubbles:true}));}`);
 await until(`document.querySelector('.file-history-toolbar')?.textContent.includes('差分はありません')`,'履歴選択を切り替えて同一内容を確認');
 await evaluate(`document.querySelector('[aria-label="更新履歴を閉じる"]').click()`);
 await until(`!document.querySelector('.file-history-dialog')`,'比較を閉じる');
 assert.equal(await evaluate(`monaco.editor.getModels().length`),1,'比較モデルを解放');
 assert.equal(await evaluate(`historyClock.timers.size`),0,'手動で閉じるとタイマーを解除');
 await evaluate(`document.querySelector('.viewer-history').click()`);
 await until(`!!document.querySelector('.file-history-changes')`,'再表示');
 await evaluate(`historyClock.advance(299000);document.querySelector('.file-history-dialog').dispatchEvent(new WheelEvent('wheel',{deltaY:100,bubbles:true}));historyClock.advance(299000)`);
 assert.equal(await evaluate(`!!document.querySelector('.file-history-dialog[open]')`),true,'ホイール操作で5分延長');
 await evaluate(`historyDiff.getModifiedEditor().setScrollTop(600)`);await sleep(200);
 await evaluate(`historyClock.advance(299000)`);
 assert.equal(await evaluate(`!!document.querySelector('.file-history-dialog[open]')`),true,'Monacoスクロールで5分延長');
 await evaluate(`document.querySelector('.file-history-toolbar>button').click()`);
 await until(`!!document.querySelector('.file-history-changes')`,'再読み込み完了');
 await evaluate(`historyClock.advance(299000)`);
 assert.equal(await evaluate(`!!document.querySelector('.file-history-dialog[open]')`),true,'再読み込みで5分延長');
 await evaluate(`historyClock.advance(1000)`);
 await until(`!document.querySelector('.file-history-dialog')`,'無操作5分で自動消去');
 assert.equal(await evaluate(`monaco.editor.getModels().length`),1,'自動消去でも比較モデルを解放');
 assert.equal(await evaluate(`historyClock.timers.size`),0,'自動消去後タイマーが残らない');
 await send('Page.navigate',{url:app.url+'#viewer=no-history.ts'});await send('Page.reload');
 await until(`!!document.querySelector('.monaco-editor')`,'履歴なしのソース表示');await sleep(250);
 assert.equal(await evaluate(`!!document.querySelector('.viewer-history')`),false);
 assert.deepEqual(errors,[]);console.log('FILE HISTORY PASS: 履歴有無・日時選択・左右比較・未変更行の位置合わせ・双方向同期スクロール・縦画面・読み取り専用・破棄');
}finally{
 ws?.close();chrome.kill();await app.close();await sleep(300);
 for(const path of [project,profile]){if(!resolve(path).startsWith(resolve(tmpdir())+sep))throw Error('一時パスが不正です');try{rmSync(path,{recursive:true,force:true});}catch{}}
}
