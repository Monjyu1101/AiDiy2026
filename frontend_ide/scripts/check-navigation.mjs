// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026

// 模擬AIと実ブラウザで複数Naviの入力・結果・モデル・終了の独立を確認する。
// ルートから node frontend_ide/scripts/check-navigation.mjs。CHROME_PATHでブラウザを指定可能。
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { createServer } from 'node:http';
import { existsSync, mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { createCoreConnection } from '../viewer/core-connection.mjs';
import { startDevelopment } from '../server.mjs';

const chromePath = process.env.CHROME_PATH || [process.env.PROGRAMFILES, process.env['PROGRAMFILES(X86)'], process.env.LOCALAPPDATA]
  .filter(Boolean).flatMap(base => ['Google/Chrome/Application/chrome.exe', 'Microsoft/Edge/Application/msedge.exe'].map(tail => join(base, tail))).find(existsSync)
  || ['/usr/bin/google-chrome', '/usr/bin/chromium', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'].find(existsSync);
if (!chromePath) throw Error('Chrome / Edge が見つかりません。CHROME_PATH を指定してください。');
const temporary = mkdtempSync(join(tmpdir(), 'aidiy-connection-check-'));
const project = join(temporary, 'project'); mkdirSync(project);
writeFileSync(join(project, 'README.md'), '# 接続表示の検証\n', 'utf8');
const calls = [], replies = new Set(); let healthy = true;
const core = createServer((req, res) => {
  assert.equal(req.url, '/aidiy_code_agents/ping'); assert.equal(req.method, 'GET');
  calls.push(Date.now()); req.resume();
  const reply = () => {
    if (res.destroyed) return;
    res.writeHead(healthy ? 200 : 503, { 'content-type': 'application/json' });
    res.end(JSON.stringify({ status: healthy ? 'ok' : 'error', name: 'aidiy_code_agents' }));
  };
  if (calls.length === 1 || !healthy) reply();
  else { const timer = setTimeout(() => { replies.delete(timer); reply(); }, 800); replies.add(timer); }
});
await new Promise(done => core.listen(0, '127.0.0.1', done));
const connection = createCoreConnection(project, { target: `http://127.0.0.1:${core.address().port}` });
let aiCalls=0,failNext=false;
const app = await startDevelopment(project, { connection, navigationOptions:{stateRoot:join(temporary,'navigation-state'),runAgent:async({prompt})=>{
 aiCalls++;if(failNext){failNext=false;await new Promise(r=>setTimeout(r,800));throw Error('表示試験の失敗');}const shape=JSON.parse(prompt.slice(prompt.lastIndexOf('\n')+1).replace(/^出力形式: /,''));
 shape.items=[{id:'one',name:'検索画面の入力を整える',progress:65,reason:'入力欄を確認。空入力の検証を次に行います。'},{id:'two',name:'操作ガイドを整える',progress:20,reason:'既存の章に追記する方針です。'}];shape.nextPrompt='検索画面の空入力とエラー表示を確認し、必要なテストを追加してください。';
 await new Promise(r=>setTimeout(r,1000));return {content:JSON.stringify(shape)};
}} });
const chrome = spawn(chromePath, ['--headless=new', '--remote-debugging-port=0', `--user-data-dir=${join(temporary, 'browser')}`,
  '--window-size=1280,800', ...(process.platform === 'linux' ? ['--no-sandbox'] : []), 'about:blank'], { stdio: 'ignore', windowsHide: true });
const sleep = ms => new Promise(done => setTimeout(done, ms));
async function until(check, label) { const end = Date.now() + 30000; while (Date.now() < end) { if (await check()) return; await sleep(100); } throw Error(`待機タイムアウト: ${label}`); }
let socket,standalone;
try {
  const activePort = join(temporary, 'browser', 'DevToolsActivePort');
  await until(() => existsSync(activePort), 'ブラウザ起動');
  const { readFileSync } = await import('node:fs');
  const port = readFileSync(activePort, 'utf8').split('\n')[0];
  const target = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(item => item.type === 'page');
  socket = new WebSocket(target.webSocketDebuggerUrl); await once(socket, 'open');
  let id = 0; const pending = new Map(), errors = [];
  socket.addEventListener('message', event => {
    const message = JSON.parse(event.data);
    if (pending.has(message.id)) { pending.get(message.id)(message); pending.delete(message.id); }
    if (message.method === 'Runtime.exceptionThrown') errors.push(message.params.exceptionDetails.text);
  });
  const send = (method, params = {}) => new Promise(done => { pending.set(++id, done); socket.send(JSON.stringify({ id, method, params })); });
  const evaluate = async expression => {
    const result = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true,userGesture:true });
    assert.equal(result.result?.exceptionDetails, undefined, JSON.stringify(result.result?.exceptionDetails));
    return result.result?.result?.value;
  };
  await send('Runtime.enable');
  await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 800, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate',{url:app.url});
  await until(()=>evaluate(`!![...document.querySelectorAll('button')].find(b=>b.textContent==='AiDiy接続利用')`),'開始');
  await evaluate(`[...document.querySelectorAll('button')].find(b=>b.textContent==='AiDiy接続利用').click()`);
  await until(()=>evaluate(`!!window.aidiyIDE`),'IDE');
  await evaluate(`aidiyIDE.setAutoSpin(false);window.testNavi=[];const originalOpen=window.open;window.open=(...args)=>{const child=originalOpen.apply(window,args);testNavi.push(child);return child;};document.querySelector('.navigation-launch').click()`);
  const child=(index,expression)=>evaluate(`testNavi[${index}].eval(${JSON.stringify(expression)})`);
  await until(()=>evaluate(`!!testNavi[0]?.document.querySelector('textarea')`),'Navi 1');
  await child(0,`(()=>{const t=document.querySelector('textarea');t.value='検索画面を整える';t.dispatchEvent(new Event('input',{bubbles:true}));document.querySelector('.navigation-start').click();})()`);
  await until(()=>child(0,`!!document.querySelector('.navigation-display.running')`),'nav busy');
  assert.equal(await child(0,`getComputedStyle(document.querySelector('.navigation-display'),'::before').animationName`),'prompt-reflect');
  await until(()=>child(0,`document.querySelectorAll('.navigation-progress').length===2`),'Navi 1 result');
  assert.equal(aiCalls,1);
  await evaluate(`document.querySelector('.navigation-launch').click()`);
  await until(()=>evaluate(`!!testNavi[1]?.document.querySelector('textarea')`),'Navi 2');
  assert.equal(await child(1,`document.querySelector('textarea').value.startsWith('最近更新したファイル')`),true);
  assert.ok(await child(0,`document.body.textContent.includes('AiDiy IDE / Navigator 1')`));
  assert.ok(await child(1,`document.body.textContent.includes('AiDiy IDE / Navigator 2')`));
  assert.equal(await child(1,`document.querySelectorAll('.navigation-progress').length`),0);
  await child(1,`document.querySelector('.navigation-model-line button').click()`);
  await child(1,`(()=>{const input=document.querySelector('.navigation-model-choice');input.value='auto';input.dispatchEvent(new Event('change',{bubbles:true}));document.querySelector('.navigation-model-picker').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));})()`);
  await until(()=>child(1,`document.querySelector('.navigation-model-line>span').textContent.includes('auto')`),'モデル保存');
  assert.ok(await child(0,`document.querySelector('.navigation-model-line>span').textContent.includes('aidiy_hermes')`));
  await child(0,`document.querySelector('.navigation-evaluate').click()`);
  await until(()=>child(0,`!!document.querySelector('.navigation-display.running')`),'evaluate busy');
  assert.equal(await child(1,`!!document.querySelector('.navigation-display.running')`),false);
  await until(()=>child(0,`!document.querySelector('.navigation-evaluate').disabled`),'評価完了');
  assert.equal(aiCalls,2);
  assert.equal(await child(0,`!!document.querySelector('.navigation-display.running')`),false);
  assert.equal(await child(1,`!!document.querySelector('.navigation-display.running')`),false);
  await child(0,`document.querySelector('.navigation-project nav button:last-child').click()`);
  await until(()=>child(0,`document.querySelectorAll('.navigation-history>button').length===1`),'history list');
  await child(0,`document.querySelector('.navigation-history>button').click()`);
  await until(()=>child(0,`!document.querySelector('.navigation-history')`),'history selected');
  assert.equal(aiCalls,2);
  assert.equal(await child(1,`document.querySelectorAll('.navigation-progress').length`),0);
  assert.equal(await evaluate(`document.querySelectorAll('.navigation-toggle').length`),0);
  await evaluate(`document.querySelector('.explorer-toggle').click()`);
  assert.equal(await evaluate(`document.querySelector('.space-view').classList.contains('navigation-open')`),false);
  failNext=true;
  await child(0,`document.querySelector('.navigation-start').click()`);
  await until(()=>child(0,`!!document.querySelector('.navigation-display.running')`),'failure busy');
  await until(()=>child(0,`document.body.textContent.includes('表示試験の失敗')`),'failure');
  assert.equal(await child(0,`!!document.querySelector('.navigation-display.running')`),false);
  await child(0,`document.querySelector('.navigation-start').click()`);
  await until(()=>child(0,`!!document.querySelector('.navigation-display.running')`),'closing busy');
  await child(0,`document.querySelector('[aria-label="Navigatorを閉じる"]').click()`);
  await until(()=>evaluate(`testNavi[0].closed`),'Navi 1 close');
  assert.equal(await child(1,`document.querySelector('textarea').value.startsWith('最近更新したファイル')`),true);
  await child(1,`document.querySelector('[aria-label="Navigatorを閉じる"]').click()`);
  standalone=await startDevelopment(project,{kind:'navi',navigationOptions:{stateRoot:join(temporary,'standalone-state'),runAgent:()=>{throw Error('No standalone AI expected');}}});
  await send('Page.navigate',{url:standalone.url});
  await until(()=>evaluate(`!!document.querySelector('.navigation-panel.standalone textarea')`),'standalone Navigation');
  assert.ok(await evaluate(`document.body.textContent.includes('AiDiy Navigator')`));
  assert.ok(await evaluate(`document.querySelector('.navigation-project').textContent.includes('project')`));
  await evaluate(`document.querySelector('.navigation-model-line button').click()`);
  await until(()=>evaluate(`!!document.querySelector('.navigation-model-picker')`),'standalone model dialog');
  assert.ok(await evaluate(`document.querySelector('.navigation-model-picker').textContent.includes('same')`));
  const capture=await send('Page.captureScreenshot',{format:'png'});
  mkdirSync(resolve('temp/navigation-ui-check'),{recursive:true});writeFileSync(resolve('temp/navigation-ui-check/standalone.png'),Buffer.from(capture.result.data,'base64'));
  assert.deepEqual(errors,[]);console.log(JSON.stringify({pass:true,ai:'mock only',aiCalls,checks:['two popup windows','independent model/result/evaluation','Explorer unchanged','close isolation']}));

} finally {
  socket?.close(); const exited = once(chrome, 'exit'); chrome.kill(); await exited;
  await standalone?.close();await app.close(); connection.close(); for (const timer of replies) clearTimeout(timer);
  core.closeAllConnections(); await new Promise(done => core.close(done));
  rmSync(temporary, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 });
}
