// 透過ウィンドウの実画面撮影用。backend_diag の Electron で実行する。
const { app, BrowserWindow, screen } = require('electron');
app.whenReady().then(() => {
  const window = new BrowserWindow({
    ...screen.getPrimaryDisplay().bounds,
    title: 'AiDiy 撮影用白背景', frame: false, backgroundColor: '#ffffff',
    skipTaskbar: true, show: true,
    webPreferences: { sandbox: true, contextIsolation: true, nodeIntegration: false },
  });
  window.loadURL('data:text/html;charset=utf-8,<html><head><title>AiDiy 撮影用白背景</title></head><body style="margin:0;background:white"></body></html>');
  window.webContents.on('before-input-event', (_event, input) => {
    if (input.type === 'keyDown' && input.key === 'Escape') window.close();
  });
});
app.on('window-all-closed', () => app.quit());
