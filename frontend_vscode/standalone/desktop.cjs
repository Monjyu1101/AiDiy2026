const { app, BrowserWindow, ipcMain, shell } = require('electron');
const { join, resolve } = require('node:path');
const { writeFileSync } = require('node:fs');
const { 単独起動 } = require('../dist/standalone.cjs');
const entryIndex = process.argv.findIndex(arg => resolve(arg) === __filename);
const args = process.argv.slice(entryIndex >= 0 ? entryIndex + 1 : 2);

app.setName('AiDiy');
app.setPath('userData', join(app.getPath('appData'), 'AiDiy-vscode'));
if (process.platform === 'win32') app.setAppUserModelId('AiDiy.vscode.standalone');

let server, window, closing = false, opening = true;
app.on('before-quit', event => {
  if (!server || closing) return;
  event.preventDefault();
  closing = true;
  void server.close().finally(() => app.quit());
});
app.on('window-all-closed', () => app.quit());

app.whenReady().then(async () => {
  server = await 単独起動(resolve(args[0] || process.cwd()));
  window = new BrowserWindow({
    title: 'AiDiy', width: 476, height: 602, minWidth: 360, minHeight: 480,
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
  // 初回だけ、黒いウィンドウを最終位置の中心から拡大する。
  const bounds = window.getBounds();
  const resize = scale => {
    const width = Math.round(bounds.width * scale), height = Math.round(bounds.height * scale);
    window.setBounds({ x: Math.round(bounds.x + (bounds.width - width) / 2), y: Math.round(bounds.y + (bounds.height - height) / 2), width, height });
  };
  window.setMinimumSize(0, 0);
  resize(.55);
  window.show();
  window.focus();
  if (!window.isVisible()) throw new Error('専用ウィンドウを表示できませんでした。');
  const expanded = await new Promise(resolve => {
    const started = Date.now();
    const tick = () => {
      if (window.isDestroyed()) { resolve(false); return; }
      const progress = Math.min(1, (Date.now() - started) / 750);
      resize(.55 + .45 * (1 - Math.pow(1 - progress, 3)));
      if (progress < 1) setTimeout(tick, 16);
      else resolve(true);
    };
    tick();
  });
  if (!expanded) return;
  window.setBounds(bounds);
  window.setMinimumSize(360, 480);
  opening = false;
  sendState();
  if (args[1]) writeFileSync(args[1], JSON.stringify({ url: server.url, pid: process.pid, windowShown: true }), 'utf8');
}).catch(error => { console.error(String(error)); app.quit(); process.exitCode = 1; });
