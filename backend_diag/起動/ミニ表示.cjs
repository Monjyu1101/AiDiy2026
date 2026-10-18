'use strict';

// 元の位置・サイズ・最大化状態を保持し、固定のミニ寸法だけを公開する。
function ミニ表示を作成(window){
 let original;
 return {
  get active(){return !!original;},
  set(enabled){
   if(typeof enabled!=='boolean'||!window||window.isDestroyed())return false;
   if(enabled===!!original)return true;
   if(enabled){
    original={bounds:window.getNormalBounds(),minimum:window.getMinimumSize(),maximized:window.isMaximized(),maximizable:window.isMaximizable()};
    if(original.maximized)window.unmaximize();
    window.setMinimumSize(300,280);
    window.setMaximizable(false);
    window.setBounds({...original.bounds,width:340,height:320});
   }else{
    const saved=original;original=undefined;
    window.setMinimumSize(...saved.minimum);
    window.setMaximizable(saved.maximizable);
    window.setBounds(saved.bounds);
    if(saved.maximized)window.maximize();
   }
   return true;
  },
 };
}
module.exports={ミニ表示を作成};
