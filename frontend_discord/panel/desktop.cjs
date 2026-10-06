const { app, BrowserWindow, ipcMain, screen } = require('electron');
const { fork, spawn } = require('node:child_process');
const { join } = require('node:path');
const { pathToFileURL } = require('node:url');
const { writeFileSync } = require('node:fs');

const root = join(__dirname, '..');
const page = pathToFileURL(join(__dirname, 'index.html')).href;
app.setName('aidiy_discord');
app.setPath('userData', join(app.getPath('appData'), 'aidiy_discord'));
if (process.platform === 'win32') app.setAppUserModelId('AiDiy.aidiy_discord');
let window, worker, quitting = false, shutdownComplete = false, shutdown;
let sequence = 0;
const pending = new Map();
const readyFile = process.env.AIDIY_DISCORD_READY;
const autoConnect = process.env.AIDIY_DISCORD_CONNECT === '1';
function ready(file = readyFile) { if (file) writeFileSync(file, JSON.stringify({ windowShown: true })); }
function request(action, value) {
  return new Promise((resolve, reject) => {
    if (!worker?.connected || quitting) { reject(new Error('接続処理を開始できません。パネルを開き直してください。')); return; }
    const id = ++sequence;
    const timer = setTimeout(() => { pending.delete(id); reject(new Error('処理が完了しません。パネルを閉じて開き直してください。')); }, 60_000);
    pending.set(id, { resolve, reject, timer });
    worker.send({ id, action, value }, error => {
      if (error && pending.has(id)) { pending.delete(id); clearTimeout(timer); reject(new Error('接続処理との通信が切れました。')); }
    });
  });
}
function stopWorker() {
  if (shutdown) return shutdown;
  shutdown = new Promise(resolve => {
    if (!worker || !worker.pid || worker.exitCode !== null || worker.signalCode !== null) { resolve(); return; }
    let deadline;
    const done = () => { clearTimeout(timer); clearTimeout(deadline); resolve(); };
    const killWorker = () => { try { worker.kill('SIGKILL'); } catch {} };
    const timer = setTimeout(() => {
      // 通常は IPC で CLI・音声を回収。応答しない場合だけ、この worker の子孫を停止する。
      console.error('Discord の終了応答がないため、接続処理プロセスを停止します。');
      if (process.platform === 'win32') {
        const kill = spawn('taskkill', ['/PID', String(worker.pid), '/T', '/F'], { windowsHide: true, stdio: 'ignore' });
        kill.on('error', killWorker);
        kill.on('exit', code => { if (code !== 0) killWorker(); });
        // taskkill 自身が応答しなくても Electron の終了を無期限に止めない。
        deadline = setTimeout(() => { kill.kill(); killWorker(); done(); }, 3000);
      }
      else {
        try { process.kill(-worker.pid, 'SIGKILL'); } catch { killWorker(); }
        deadline = setTimeout(done, 3000);
      }
    }, 15_000);
    worker.once('exit', done);
    try {
      if (worker.connected) worker.send({ action: 'shutdown' }, () => {});
      else worker.kill();
    } catch { killWorker(); }
  });
  return shutdown;
}
if (!app.requestSingleInstanceLock({ readyFile, autoConnect })) {
  app.quit();
} else {
  app.on('second-instance', (_event, _argv, _cwd, data) => {
    // 起動側はこのプロセスの終了後に再試行する。消える画面を起動成功と通知しない。
    if (quitting) {
      if (data.readyFile) writeFileSync(data.readyFile, JSON.stringify({ closing: true, pid: process.pid }));
      return;
    }
    if (!window || window.isDestroyed()) return;
    if (window.isMinimized()) window.restore();
    window.show(); window.focus(); ready(data.readyFile);
    if (data.autoConnect) void request('start').catch(() => {});
  });
  app.on('before-quit', event => {
    if (shutdownComplete) return;
    event.preventDefault();
    if (quitting) return;
    quitting = true;
    for (const job of pending.values()) { clearTimeout(job.timer); job.reject(new Error('パネルを終了しています。')); }
    pending.clear();
    if (window && !window.isDestroyed()) window.webContents.send('discord:state', { phase: 'stopping', message: '接続を終了しています…', fatal: true });
    void stopWorker().finally(() => { shutdownComplete = true; app.quit(); });
  });
  app.on('window-all-closed', () => app.quit());
  app.whenReady().then(async () => {
    worker = fork(join(root, 'src/panel-worker.ts'), [], {
      cwd: root, execPath: process.env.AIDIY_DISCORD_NODE,
      execArgv: ['--import', pathToFileURL(join(root, 'node_modules/tsx/dist/loader.mjs')).href],
      stdio: ['ignore', 'inherit', 'inherit', 'ipc'], windowsHide: true, detached: process.platform !== 'win32',
    });
    worker.on('message', message => {
      if (message.type === 'state') { if (!quitting && !window?.isDestroyed()) window?.webContents.send('discord:state', message.state); return; }
      const job = pending.get(message.id); if (!job) return;
      clearTimeout(job.timer); pending.delete(message.id);
      if (message.error) job.reject(new Error(message.error)); else job.resolve(message.result);
    });
    const failed = () => {
      for (const job of pending.values()) { clearTimeout(job.timer); job.reject(new Error('接続処理が終了しました。パネルを開き直してください。')); }
      pending.clear();
      if (!quitting && window && !window.isDestroyed()) window.webContents.send('discord:state', { phase: 'error', message: '接続処理が終了しました。パネルを開き直してください。', fatal: true });
    };
    worker.on('exit', failed); worker.on('error', failed);
    const area = screen.getDisplayNearestPoint(screen.getCursorScreenPoint()).workArea;
    const width = Math.min(476, area.width), height = Math.min(414, area.height);
    window = new BrowserWindow({
      title: 'AiDiy (Discord)', width, height, minWidth: 380, minHeight: 414,
      x: area.x + Math.round((area.width - width) / 2), y: area.y + 8,
      frame: false, roundedCorners: false, show: false, backgroundColor: '#101217', autoHideMenuBar: true,
      icon: join(root, '../frontend_vscode/media/AiDiy.png'),
      webPreferences: { preload: join(__dirname, 'preload.cjs'), nodeIntegration: false, contextIsolation: true, sandbox: true },
    });
    window.setMenu(null);
    window.on('close', event => {
      if (shutdownComplete) return;
      event.preventDefault(); app.quit();
    });
    window.webContents.session.setPermissionCheckHandler(() => false);
    window.webContents.session.setPermissionRequestHandler((_contents, _permission, callback) => callback(false));
    const trusted = event => event.sender === window.webContents && event.senderFrame === window.webContents.mainFrame && event.senderFrame.url === page;
    ipcMain.handle('discord:request', (event, action, value) => {
      if (!trusted(event) || !['initial', 'select', 'select-code', 'catalog-code', 'start', 'stop'].includes(action)) throw new Error('許可されていない操作です。');
      return request(action, value);
    });
    ipcMain.handle('discord:window', (event, action) => {
      if (!trusted(event)) return;
      if (action === 'minimize') window.minimize();
      else if (action === 'close') window.close();
    });
    window.webContents.on('will-navigate', event => event.preventDefault());
    window.webContents.on('will-redirect', event => event.preventDefault());
    window.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
    await window.loadURL(page);
    window.show(); window.focus();
    if (!window.isVisible()) throw new Error();
    // Windows の画面拡大率による丸め後の幅で中央を合わせる。
    window.setPosition(area.x + Math.round((area.width - window.getBounds().width) / 2), area.y + 8);
    ready();
    if (autoConnect) void request('start').catch(() => {});
  }).catch(error => { console.error(`Discord パネルを開けませんでした: ${error.message}`); app.quit(); process.exitCode = 1; });
}
