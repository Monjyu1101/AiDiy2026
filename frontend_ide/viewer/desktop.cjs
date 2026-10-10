// -*- coding: utf-8 -*-
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026

const { app, BrowserWindow, shell, ipcMain } = require('electron');
const { join, basename } = require('node:path');
const { audioRequest, audioCheck } = require('./panel-permissions.cjs');

const url = process.env.AIDIY_DEV_URL;
if (!url || !/^http:\/\/127\.0\.0\.1:\d+\/$/.test(url)) throw new Error('起動元の URL が不正です。aidiy_ide から起動してください。');
app.setName('aidiy_ide');
app.setPath('userData', join(app.getPath('appData'), 'aidiy_ide'));
if (process.platform === 'win32') app.setAppUserModelId('AiDiy.aidiy_ide');
process.on('disconnect', () => app.quit());
app.on('window-all-closed', () => app.quit());

app.whenReady().then(async () => {
  const window = new BrowserWindow({
    title: `AiDiy IDE — ${basename(process.env.AIDIY_DEV_PROJECT || '')}`,
    width: 1400, height: 900, minWidth: 800, minHeight: 600,
    show: false, backgroundColor: '#02030a', autoHideMenuBar: true,
    frame: false, roundedCorners: false, icon: join(__dirname, 'web/AiDiy.png'),
    webPreferences: { preload: join(__dirname, 'preload.cjs'), nodeIntegration: false, contextIsolation: true, sandbox: true },
  });
  window.setMenu(null);
  ipcMain.handle('aidiy-ide:window', (event, action) => {
    if (event.sender !== window.webContents || event.senderFrame !== window.webContents.mainFrame
      || event.senderFrame.url.split('#')[0] !== url) return;
    if (action === 'minimize') window.minimize();
    else if (action === 'close') window.close();
  });
  window.webContents.on('will-navigate', (event, target) => {
    if (target.split('#')[0] !== url) event.preventDefault();
  });
  window.webContents.on('will-redirect', event => event.preventDefault());
  window.webContents.on('will-attach-webview', event => event.preventDefault());
  window.webContents.setWindowOpenHandler(({ url: target }) => {
    if (/^https?:\/\//i.test(target)) void shell.openExternal(target);
    return { action: 'deny' };
  });
  const origin = new URL(url).origin;
  window.webContents.session.setPermissionRequestHandler((contents, permission, callback, details) =>
    callback(audioRequest(contents, window.webContents, permission, details, origin)));
  window.webContents.session.setPermissionCheckHandler((contents, permission, requestingOrigin, details) =>
    (contents === window.webContents && permission === 'clipboard-sanitized-write' && requestingOrigin === origin)
    || audioCheck(contents, window.webContents, permission, requestingOrigin, details, origin));
  await window.loadURL(url);
  // Windows では show() 直後の isVisible() がまだ false のことがある。
  // 実際の show イベントを待ってから起動完了を通知する。
  await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('Electron のウィンドウを表示できませんでした。')), 5000);
    window.once('show', () => { clearTimeout(timer); resolve(); });
    window.show();
  });
  process.send?.({ windowShown: true });
}).catch(error => { console.error(error); process.exitCode = 1; app.quit(); });
