/*!
 * -*- coding: utf-8 -*-
 *
 * -------------------------------------------------------------------------
 * COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
 * Licensed under "AiDiy 公開利用ライセンス v1.1".
 * Commercial use requires prior written consent from all copyright holders.
 * See LICENSE for full terms. Thank you for keeping the rules.
 * https://github.com/monjyu1101/AiDiy2026
 * -------------------------------------------------------------------------
 */

const { app, BrowserWindow, ipcMain, shell, screen } = require('electron');
const { join, resolve } = require('node:path');
const { writeFileSync } = require('node:fs');
const size = require('../scripts/window-size.cjs');
const { 拡大表示 } = require('../scripts/window-opening.cjs');
const { 単独起動 } = require('../dist/aidiy_code/server.cjs');
const entryIndex = process.argv.findIndex(arg => resolve(arg) === __filename);
const args = process.argv.slice(entryIndex >= 0 ? entryIndex + 1 : 2);
const projectRoot = process.env.AIDIY_CODE_PROJECT || args[0] || process.cwd();
const ready = process.env.AIDIY_CODE_READY || args[1];
const initialModel = process.env.AIDIY_CODE_MODEL || args[2];

app.setName('aidiy_code');
app.setPath('userData', join(app.getPath('appData'), 'aidiy_code'));
if (process.platform === 'win32') app.setAppUserModelId('AiDiy.aidiy_code');

let server, window, closing = false, opening = true;
app.on('before-quit', event => {
  if (!server || closing) return;
  event.preventDefault();
  closing = true;
  void server.close().finally(() => app.quit());
});
app.on('window-all-closed', () => app.quit());

app.whenReady().then(async () => {
  server = await 単独起動(resolve(projectRoot), undefined, initialModel ? JSON.parse(initialModel) : {});
  const workArea = screen.getDisplayNearestPoint(screen.getCursorScreenPoint()).workArea;
  window = new BrowserWindow({
    title: 'AiDiy Code', width: size.幅, height: size.会話高さ, minWidth: size.最小幅, minHeight: size.会話最小高さ,
    x: workArea.x + 8, y: workArea.y + 8,
    frame: false, roundedCorners: false, show: false, backgroundColor: '#000',
    icon: join(__dirname, '../media/AiDiy.png'), autoHideMenuBar: true,
    webPreferences: {
      preload: join(__dirname, 'preload.cjs'),
      nodeIntegration: false, contextIsolation: true, sandbox: true,
    },
  });
  window.setMenu(null);
  const trusted = event => event.sender === window.webContents
    && event.senderFrame === window.webContents.mainFrame
    && event.senderFrame.url === server.url;
  ipcMain.handle('aidiy:window', (event, action) => {
    if (!trusted(event)) return;
    if (action === 'minimize') window.minimize();
    else if (action === 'maximize') window.isMaximized() ? window.unmaximize() : window.maximize();
    else if (action === 'close') window.close();
  });
  const sendState = () => window.webContents.send('aidiy:window-state', { maximized: window.isMaximized(), opening });
  window.on('maximize', sendState);
  window.on('unmaximize', sendState);
  window.webContents.on('did-finish-load', sendState);
  window.webContents.on('will-navigate', (event, url) => {
    if (url !== server.url) event.preventDefault();
  });
  window.webContents.on('will-redirect', event => event.preventDefault());
  window.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:\/\//i.test(url)) void shell.openExternal(url);
    return { action: 'deny' };
  });
  window.webContents.session.setPermissionRequestHandler((_contents, _permission, callback) => callback(false));
  window.webContents.session.setPermissionCheckHandler((_contents, permission, origin) =>
    permission === 'clipboard-sanitized-write' && origin === new URL(server.url).origin);
  await window.loadURL(server.url);
  // 初回だけ、最終位置の中心から黒い矩形を拡大してから表示する（3本共通: scripts/window-opening.cjs）。
  if (!(await 拡大表示(BrowserWindow, window, { background: '#000' }))) return;
  if (!window.isVisible()) throw new Error('専用ウィンドウを表示できませんでした。');
  opening = false;
  sendState();
  if (ready) writeFileSync(ready, JSON.stringify({ url: server.url, pid: process.pid, windowShown: true }), 'utf8');
}).catch(error => { console.error(String(error)); app.quit(); process.exitCode = 1; });
