'use strict';
const {setWindowBounds}=require('../../frontend_ide/デスクトップ/全画面横断.cjs');

// Windowsの透明フレームレス窓ではmaximize後もisMaximizedがfalseとなる
// 環境がある。復元寸法を保持し、既存のDPI補正で作業領域へ広げる。
function 通常窓サイズを作成(window,screen,platform=process.platform){
 if(platform!=='win32')return window;
 let normal;
 return new Proxy(window,{get(target,key){
  if(key==='isMaximized')return ()=>!!normal||target.isMaximized();
  if(key==='getNormalBounds')return ()=>normal?{...normal}:target.getNormalBounds();
  if(key==='maximize')return ()=>{if(normal)return;normal=target.getNormalBounds();setWindowBounds(target,screen.getDisplayMatching(target.getBounds()).workArea);};
  if(key==='unmaximize')return ()=>{if(!normal)return target.unmaximize();const saved=normal;normal=undefined;setWindowBounds(target,saved);};
  const value=target[key];return typeof value==='function'?value.bind(target):value;
 }});
}
module.exports={通常窓サイズを作成};
