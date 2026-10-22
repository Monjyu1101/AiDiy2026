// 実Electronで本番ログイン窓の終了を検証する起動時プローブ。通常起動では読み込まない。
const { app, BrowserWindow } = require('electron');
const send = process.send.bind(process);
process.send = (message, ...args) => {
  const result = send(message, ...args);
  if (message?.avatarShown) {
    setTimeout(() => {
      const login = BrowserWindow.getAllWindows().find(window => new URL(window.webContents.getURL()).searchParams.get('role') === 'login');
      if (!login?.isVisible()) { app.exit(2); return; }
      // 設定窓などの残存時にも、ログインのclosedから全体終了することを確認。
      new BrowserWindow({ show: false });
      login.close();
    }, 1500);
  }
  return result;
};
