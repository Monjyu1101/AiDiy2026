// -*- coding: utf-8 -*-

// -------------------------------------------------------------------------
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
// -------------------------------------------------------------------------

// AiDiy Dev の画面確認用スクリーンショット。ヘッドレス Chrome を DevTools Protocol で操作し、実時間で待ってから撮る。
// （--screenshot の仮想時間ではアニメーションが進まず、Claude のブラウザペインは拡大率がずれるため）
// 使い方: node frontend_dev/scripts/shot.mjs URL 出力.png [待機ms=8000] [撮影前に実行するJS] [JS後の待機ms=3000]
// 例:     node frontend_dev/scripts/shot.mjs "http://127.0.0.1:<起動ログのポート>/#/frontend_web" out.png 8000 "aidiyDev.flyHome()"
// JS は Runtime.evaluate で評価し、戻り値（Promise なら解決値）を標準出力へ JSON で出す。
import { spawn } from 'node:child_process';
import { existsSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { startServer } from '../server.mjs';

const app = await startServer(resolve('.'));
const url = app.url;
const chromePath = [
  [process.env.PROGRAMFILES, 'Google/Chrome/Application/chrome.exe'],
  [process.env['PROGRAMFILES(X86)'], 'Google/Chrome/Application/chrome.exe'],
  [process.env.LOCALAPPDATA, 'Google/Chrome/Application/chrome.exe'],
  [process.env['PROGRAMFILES(X86)'], 'Microsoft/Edge/Application/msedge.exe'],
  [process.env.PROGRAMFILES, 'Microsoft/Edge/Application/msedge.exe'],
].filter(([base]) => base).map(([base, tail]) => join(base, tail)).find(existsSync)
  ?? ['/usr/bin/google-chrome', '/usr/bin/chromium', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'].find(existsSync);
if (!chromePath) { console.error('Chrome / Edge が見つかりません。'); process.exit(1); }

const port = 9333 + Math.floor(Math.random() * 500);
const profile = mkdtempSync(join(tmpdir(), 'aidiy_dev_shot-'));
const chrome = spawn(chromePath, [
  '--headless=new', `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`,
  '--window-size=1280,800', '--hide-scrollbars', 'about:blank',
], { stdio: 'ignore', windowsHide: true });
const sleep = ms => new Promise(r => setTimeout(r, ms));
try {
  let target;
  for (let i = 0; i < 50 && !target; i++) {
    try { target = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(t => t.type === 'page'); } catch { await sleep(200); }
  }
  if (!target) throw new Error('ヘッドレス Chrome に接続できませんでした。');
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise(r => ws.addEventListener('open', r, { once: true }));
  let id = 0;
  const pending = new Map();
  ws.addEventListener('message', e => { const m = JSON.parse(e.data); if (pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } });
  const send = (method, params = {}) => new Promise(r => { pending.set(++id, r); ws.send(JSON.stringify({ id, method, params })); });
  await send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 800, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url });
  const errors = [];
  ws.addEventListener('message', e => { const m = JSON.parse(e.data); if (m.method === 'Runtime.exceptionThrown') errors.push(m.params.exceptionDetails.text); });
  await send('Runtime.enable');
  async function evaluate(expression) {
    const response = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
    if (response.result?.exceptionDetails) throw new Error(JSON.stringify(response.result.exceptionDetails));
    return response.result?.result?.value;
  }
  async function capture(name) {
    const shot = await send('Page.captureScreenshot', { format: 'png' });
    writeFileSync(name, Buffer.from(shot.result.data, 'base64'));
    console.log(name);
  }
  await sleep(8200);
  await capture('nn-01-start.png');
  const mode = await evaluate(`(async()=>{
    const wait=ms=>new Promise(r=>setTimeout(r,ms));
    document.getElementById('core-connect').click();
    for(let i=0;i<40&&document.getElementById('workspace').hidden;i++)await wait(200);
    if(document.getElementById('workspace').hidden) document.getElementById('offline-start').click();
    for(let i=0;i<150&&!document.getElementById('loading').classList.contains('done');i++)await wait(200);
    if(!document.getElementById('loading').classList.contains('done'))throw Error('ファイル一覧が読み込めません');
    return document.getElementById('connection-status').textContent;
  })()`);
  await sleep(3000);
  await capture('nn-02-space.png');
  await evaluate(`document.getElementById('explorer-toggle').click()`);
  await sleep(1000);
  await capture('nn-03-explorer.png');
  await evaluate(`aidiyDev.goTo({type:'file',path:'frontend_dev/README.md'})`);
  await sleep(7000);
  await capture('nn-04-preview.png');
  console.log(JSON.stringify({mode, errors, preview: await evaluate(`document.getElementById('viewer-name').textContent`)}));
  ws.close();
} finally {
  chrome.kill();
  app.server.closeAllConnections();
  await new Promise(done => app.server.close(done));
  await sleep(300);
  if (!resolve(profile).startsWith(resolve(tmpdir()) + (process.platform === 'win32' ? '\\' : '/'))) throw new Error('一時パスが不正です');
  try { rmSync(profile, { recursive: true, force: true }); } catch { /* Chrome が掴んでいれば残す */ }
}
