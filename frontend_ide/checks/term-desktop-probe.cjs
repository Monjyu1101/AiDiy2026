// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
const assert = require('node:assert/strict');
const { app, BrowserWindow } = require('electron');
const { writeFileSync, mkdirSync } = require('node:fs');
const { join } = require('node:path');
app.setPath('appData', process.env.AIDIY_TEST_PROFILE);
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const evaluate = (window, source) => window.webContents.executeJavaScript(source, true);
async function until(check) { for (let i = 0; i < 150; i++) { if (await check()) return; await sleep(100); } throw Error('Electron端末確認タイムアウト'); }
const main = process.env.AIDIY_DEVELOPMENT_URL;
let running = false;
app.on('browser-window-created', (_, owner) => {
  if (running) return; running = true;
  owner.webContents.once('did-finish-load', async () => {
    try {
      await until(() => evaluate(owner, `!!document.querySelector('.component-toolbar')&&!document.documentElement.classList.contains('desktop-opening')`));
      await evaluate(owner, `Array.from(document.querySelectorAll('button')).find(b=>b.textContent==='オフライン利用').click()`);
      await until(() => evaluate(owner, `!!document.querySelector('.ai-launchers')`));
      assert.equal((await evaluate(owner, `window.aidiyWindow.openApp('term')`)).ok, true);
      const first = BrowserWindow.getAllWindows().find(w => w.getTitle() === 'AiDiy IDE / Term');
      await until(() => evaluate(first, `document.querySelector('.term-component')?.textContent.includes('実行中')&&!document.documentElement.classList.contains('desktop-opening')`));
      await until(() => evaluate(first, `document.querySelector('.xterm-rows')?.textContent.includes('PS ')`));
      assert.equal(await evaluate(first, `!!document.querySelector('.term-welcome') && document.querySelector('.term-screen').getBoundingClientRect().height<100`), true);
      await evaluate(first, `document.querySelector('.xterm-helper-textarea').focus()`);
      first.webContents.insertText("Write-Output ('ELECTRON_'+'日本語_OK')");
      first.webContents.sendInputEvent({ type: 'keyDown', keyCode: 'Return' }); first.webContents.sendInputEvent({ type: 'keyUp', keyCode: 'Return' });
      await until(() => evaluate(first, `document.querySelector('.xterm-rows')?.textContent.includes('ELECTRON_日本語_OK')`));
      assert.equal(await evaluate(first, `!document.querySelector('.term-welcome') && document.querySelector('.term-screen').getBoundingClientRect().height>100`), true);
      const dir = join(__dirname, '../../temp/term-check'); mkdirSync(dir, { recursive: true });
      const stamp = new Intl.DateTimeFormat('sv-SE', { timeZone: 'Asia/Tokyo', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23' }).format(new Date()).replace(/\D/g, '');
      const shot = join(dir, `${stamp}_3_electron-term.png`); writeFileSync(shot, (await first.webContents.capturePage()).toPNG()); console.log(shot);
      const originalBounds = first.getBounds();
      assert.deepEqual(first.getMinimumSize(), [360, 180]);
      first.setBounds({ ...originalBounds, height: 180 });
      await until(() => first.getBounds().height === 180);
      await evaluate(first, `Array.from(document.querySelectorAll('button')).find(b=>b.textContent==='表示クリア').click()`);
      await until(() => evaluate(first, `getComputedStyle(document.querySelector('.term-welcome')).display==='none' && document.querySelectorAll('.xterm-rows>div').length>=3 && document.querySelectorAll('.xterm-rows>div').length<=5`));
      await evaluate(first, `document.querySelector('.xterm-helper-textarea').focus()`);
      first.webContents.insertText("Write-Output ('COMPACT_'+'OK')");
      first.webContents.sendInputEvent({ type: 'keyDown', keyCode: 'Return' }); first.webContents.sendInputEvent({ type: 'keyUp', keyCode: 'Return' });
      await until(() => evaluate(first, `document.querySelector('.xterm-rows')?.textContent.includes('COMPACT_OK')`));
      first.setBounds({ ...originalBounds, width: 360, height: 180 });
      await until(() => evaluate(first, `(()=>{const view=document.querySelector('.term-viewport').getBoundingClientRect(),screen=document.querySelector('.xterm-screen').getBoundingClientRect();return window.innerWidth===360&&window.innerHeight===180&&screen.width>0&&screen.right<=view.right+1&&screen.bottom<=view.bottom+1})()`));
      assert.equal(await evaluate(first, `Array.from(document.querySelectorAll('.window-actions button,.component-toolbar button')).every(button=>{const r=button.getBoundingClientRect();return r.width>0&&r.height>0&&r.left>=0&&r.right<=window.innerWidth&&r.top>=0&&r.bottom<=window.innerHeight})`), true);
      const compactShot = join(dir, `${stamp}_4_electron-term-compact.png`); writeFileSync(compactShot, (await first.webContents.capturePage()).toPNG()); console.log(compactShot);
      first.setBounds(originalBounds);
      await until(() => evaluate(first, `document.querySelectorAll('.xterm-rows>div').length>5`));
      console.log('Termの2窓目を起動');
      assert.equal((await evaluate(owner, `window.aidiyWindow.openApp('term')`)).ok, true);
      await until(() => BrowserWindow.getAllWindows().filter(w => w.getTitle() === 'AiDiy IDE / Term').length === 2);
      const second = BrowserWindow.getAllWindows().find(w => w !== first && w.getTitle() === 'AiDiy IDE / Term');
      assert.ok(Math.abs(second.getBounds().x-first.getBounds().x-28)<=2);assert.ok(Math.abs(second.getBounds().y-first.getBounds().y+28)<=2);
      const urls = [first.webContents.getURL(), second.webContents.getURL()]; assert.notEqual(...urls);
      console.log('Termの1窓目を終了');
      first.close(); await until(() => first.isDestroyed());
      await until(async () => { try { await fetch(urls[0]); return false; } catch { return true; } });
      console.log('IDEの利用終了');
      await evaluate(owner, `Array.from(document.querySelectorAll('.component-toolbar button')).find(b=>b.textContent==='終了').click()`);
      await until(() => second.isDestroyed()); await until(() => evaluate(owner, `document.body.textContent.includes('オフライン利用')`));
      // 画面は先に起動画面へ戻るため、サーバーの利用終了を待ってから×で閉じる。
      await until(async () => !(await fetch(new URL('api/connection', main)).then(r => r.json())).active);
      process.send?.({ testPassed: true, urls }); owner.close();
    } catch (error) { console.error(error); app.exit(1); }
  });
});
setTimeout(() => { console.error('Electron確認期限'); app.exit(1); }, 45000).unref();
require('../desktop.cjs');
