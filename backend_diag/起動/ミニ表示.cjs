'use strict';

// 元の位置・サイズ・最大化状態を保持し、固定のミニ寸法だけを公開する。
function ミニ表示を作成(window,{screen}={}){
 let original;
 return {
  get active(){return !!original;},
  set(enabled,{topLeft=false}={}){
   if(typeof enabled!=='boolean'||!window||window.isDestroyed())return false;
   if(enabled===!!original)return true;
   if(enabled){
    original={bounds:window.getNormalBounds(),minimum:window.getMinimumSize(),maximized:window.isMaximized(),maximizable:window.isMaximizable(),alwaysOnTop:window.isAlwaysOnTop()};
    if(original.maximized)window.unmaximize();
    window.setMinimumSize(384,248);
    window.setMaximizable(false);
    const area=topLeft?screen.getPrimaryDisplay().workArea:null;
    window.setBounds({...original.bounds,...(area?{x:area.x,y:area.y}:{}),width:384,height:248});
    window.setAlwaysOnTop(true,process.platform==='win32'?'pop-up-menu':'floating');
   }else{
    const saved=original;original=undefined;
    window.setMinimumSize(...saved.minimum);
    window.setMaximizable(saved.maximizable);
    window.setAlwaysOnTop(saved.alwaysOnTop);
    window.setBounds(saved.bounds);
    if(saved.maximized)window.maximize();
   }
   return true;
  },
 };
}
module.exports={ミニ表示を作成};
