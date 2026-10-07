const { app, BrowserWindow, ipcMain, screen } = require('electron');
const { join } = require('node:path');
const { writeFileSync } = require('node:fs');
const { audioPermission, audioRequest } = require('./permissions.cjs');
const { ライブ起動 } = require('../dist/aidiy_live/server.cjs');
const backend = process.env.AIDIY_LIVE_BACKEND || process.argv[2];
const ready = process.env.AIDIY_LIVE_READY || process.argv[3];
const projectRoot = process.env.AIDIY_LIVE_PROJECT || process.argv[4] || process.cwd();
const initialModels = process.env.AIDIY_LIVE_MODELS || process.argv[5];
app.setName('aidiy_live');
app.setPath('userData', join(app.getPath('appData'), 'aidiy_live'));
if (process.platform === 'win32') app.setAppUserModelId('AiDiy.aidiy_live');
let server, window, closing = false, opening = true;
app.on('before-quit', event => {
  if (!server || closing) return;
  event.preventDefault(); closing = true;
  void server.close().finally(() => app.quit());
});
app.on('window-all-closed', () => app.quit());
app.whenReady().then(async () => {
  server = await ライブ起動(join(__dirname, '..'), backend, false, projectRoot, initialModels ? JSON.parse(initialModels) : {}, undefined, process.env.AIDIY_LIVE_CONNECT === '1');
  const workArea = screen.getDisplayNearestPoint(screen.getCursorScreenPoint()).workArea;
  window = new BrowserWindow({
    title: 'AiDiy (Live)', width: 476, height: 602, minWidth: 360, minHeight: 480,
    x: workArea.x + Math.max(0, workArea.width - 476 - 8), y: workArea.y + 8,
    frame: false, roundedCorners: false, show: false, backgroundColor: '#000', autoHideMenuBar: true,
    icon: join(__dirname, '../media/AiDiy.png'),
    webPreferences: { preload: join(__dirname, 'preload.cjs'), nodeIntegration: false, contextIsolation: true, sandbox: true },
  });
  window.setMenu(null);
  const trusted = contents => contents === window.webContents;
  window.webContents.session.setPermissionCheckHandler((contents, permission, requestingOrigin, details) =>
    audioPermission(contents, window.webContents, permission, requestingOrigin, details, server.url));
  window.webContents.session.setPermissionRequestHandler((contents, permission, callback, details) =>
    callback(audioRequest(contents, window.webContents, permission, details, server.url)));
  ipcMain.handle('aidiy-live:window', (event, action) => {
    if (!trusted(event.sender) || event.senderFrame !== window.webContents.mainFrame || event.senderFrame.url !== server.url) return;
    if (action === 'minimize') window.minimize();
    else if (action === 'close') window.close();
  });
  window.webContents.on('will-navigate', (event, url) => { if (url !== server.url) event.preventDefault(); });
  window.webContents.on('will-redirect', event => event.preventDefault());
  window.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
  const sendState = () => window.webContents.send('aidiy-live:window-state', { opening });
  window.webContents.on('did-finish-load', sendState);
  await window.loadURL(server.url);
  // Code と同じ初回演出。拡大が終わってから内容をフェード表示する。
  const bounds = window.getBounds();
  const resize = scale => {
    const width = Math.round(bounds.width * scale), height = Math.round(bounds.height * scale);
    window.setBounds({ x: Math.round(bounds.x + (bounds.width - width) / 2), y: Math.round(bounds.y + (bounds.height - height) / 2), width, height });
  };
  window.setMinimumSize(0, 0);
  resize(.55);
  window.show(); window.focus();
  if (!window.isVisible()) throw new Error('ウィンドウの表示を確認できませんでした。');
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
  // Windows の拡大率による丸めを含め、実際の幅で右端を合わせる。
  window.setBounds({ x: workArea.x + Math.max(0, workArea.width - window.getBounds().width - 8), y: workArea.y + 8 });
  opening = false;
  sendState();
  if (ready) writeFileSync(ready, JSON.stringify({ url: server.url, windowShown: true }));
}).catch(error => { console.error(error); app.quit(); process.exitCode = 1; });
