'use strict';
// aidiy_code / aidiy_live / aidiy_discord の専用ウィンドウと frontend_avatar の主ウィンドウ（ログイン・コア）の初回演出（中央から拡大）。
// 実ウィンドウを毎フレーム setBounds で広げると、Windows では描画が追いつく前の新しい縁が白く見える。
// そこで、最終位置・最終サイズの透明なキャンバス用ウィンドウを先に広げておき、その中で矩形を CSS で拡大する。
// 実ウィンドウは大きさを変えず、透明のまま表示して実際に描画されてから見せる（表示直後の未描画フレームも白くなる）。
// 注意: キャンバス用ウィンドウに setIgnoreMouseEvents / focusable: false を付けると、Windows では
// 透明部分が白く描かれる環境がある。付けずに showInactive で表示し、演出後すぐ閉じる。
const 演出時間 = 750, 開始倍率 = .55;

function 演出HTML(color) {
  return `<!doctype html><html><head><meta charset="utf-8"><style>
html,body{margin:0;height:100%;overflow:hidden;background:transparent}
div{position:absolute;inset:0;background:${color};transform:scale(${開始倍率})}
.go div{animation:grow ${演出時間}ms cubic-bezier(.33,1,.68,1) forwards}
@keyframes grow{to{transform:scale(1)}}
</style></head><body><div></div></body></html>`;
}

const 待機 = ms => new Promise(resolve => setTimeout(resolve, ms));
// 描画を2フレーム待つ。ページが応答しない場合でも表示が止まらないよう、上限を設ける。
const 描画待ち = contents => Promise.race([
  contents.executeJavaScript('new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))').catch(() => {}),
  待機(300),
]);

/** 実ウィンドウ（show: false で作成し、最終位置・サイズ・内容まで準備済み）を拡大演出の後に表示する。 */
async function 拡大表示(BrowserWindow, window, { background = '#000' } = {}) {
  let canvas;
  try {
    canvas = new BrowserWindow({
      ...window.getBounds(), frame: false, transparent: true, backgroundColor: '#00000000', hasShadow: false,
      resizable: false, skipTaskbar: true, show: false,
      webPreferences: { sandbox: true, contextIsolation: true, nodeIntegration: false },
    });
    await canvas.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(演出HTML(background))}`);
    canvas.showInactive();
    await 描画待ち(canvas.webContents);
    await canvas.webContents.executeJavaScript("document.body.classList.add('go')");
    await 待機(演出時間);
  } catch { /* 演出なしで表示する */ }
  if (window.isDestroyed()) { if (canvas && !canvas.isDestroyed()) canvas.destroy(); return false; }
  // 透明のまま表示し、実際に描画されてから見せる。キャンバスは実ウィンドウが見えてから閉じる。
  window.setOpacity(0);
  window.show(); window.focus();
  await 描画待ち(window.webContents);
  await 待機(50);
  if (!window.isDestroyed()) window.setOpacity(1);
  if (canvas && !canvas.isDestroyed()) setTimeout(() => { if (!canvas.isDestroyed()) canvas.destroy(); }, 100);
  return !window.isDestroyed();
}

module.exports = { 拡大表示, 演出時間, 開始倍率 };
