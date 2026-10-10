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

'use strict';
// aidiy_code / aidiy_live / aidiy_discord の専用ウィンドウと frontend_avatar の主ウィンドウ（ログイン・コア）の初回演出（中央から拡大）。
// 実ウィンドウを毎フレーム setBounds で広げると、Windows では描画が追いつく前の新しい縁が白く見える。
// そこで、最終位置・最終サイズの透明なキャンバス用ウィンドウを先に広げておき、その中で矩形を CSS で拡大する。
// 実ウィンドウは大きさを変えず、透明のまま表示して実際に描画されてから見せる（表示直後の未描画フレームも白くなる）。
// 注意: キャンバス用ウィンドウに setIgnoreMouseEvents / focusable: false を付けると、Windows では
// 透明部分が白く描かれる環境がある。付けずに showInactive で表示し、演出後すぐ閉じる。
const 演出時間 = 750, 開始倍率 = .55;

function 演出HTML(color, { width, height }) {
  return `<!doctype html><html><head><meta charset="utf-8"><style>
html,body{margin:0;height:100%;overflow:hidden;background:transparent}
div{position:absolute;left:0;top:0;width:${width}px;height:${height}px;max-width:100%;max-height:100%;background:${color};transform:scale(${開始倍率})}
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
    const bounds = window.getContentBounds();
    canvas = new BrowserWindow({
      ...bounds, frame: false, transparent: true, backgroundColor: '#00000000', hasShadow: false,
      resizable: false, skipTaskbar: true, show: false,
      webPreferences: { sandbox: true, contextIsolation: true, nodeIntegration: false },
    });
    // WindowsのDPI補正で作成時の寸法が膨らむため、実画面の表示領域へ明示的に揃える。
    canvas.setBounds(bounds);
    await canvas.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(演出HTML(background, bounds))}`);
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
