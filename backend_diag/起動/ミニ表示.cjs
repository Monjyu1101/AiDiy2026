'use strict';

const ミニ幅=384,初期ミニ高さ=134,最小ミニ高さ=80,最大ミニ高さ=360;
const ミニ高さは有効=height=>Number.isInteger(height)&&height>=最小ミニ高さ&&height<=最大ミニ高さ;
// 元の位置・サイズ・最大化状態を保持し、ミニ表示中だけ内容に合わせて高さを変える。
function ミニ表示を作成(window,{screen}={}){
 let original;
 return {
  get active(){return !!original;},
  set(enabled,{topLeft=false}={}){
   if(typeof enabled!=='boolean'||!window||window.isDestroyed())return false;
   if(enabled===!!original)return true;
   if(enabled){
    original={bounds:window.getNormalBounds(),minimum:window.getMinimumSize(),maximized:window.isMaximized(),maximizable:window.isMaximizable()};
    if(original.maximized)window.unmaximize();
    window.setMinimumSize(ミニ幅,初期ミニ高さ);
    window.setMaximizable(false);
    const area=topLeft?screen.getPrimaryDisplay().workArea:null;
    window.setBounds({...original.bounds,...(area?{x:area.x,y:area.y}:{}),width:ミニ幅,height:初期ミニ高さ});
   }else{
    const saved=original;original=undefined;
    window.setMinimumSize(...saved.minimum);
    window.setMaximizable(saved.maximizable);
    // 最前面は共通ピンの所有。ミニ中の変更を通常表示へ戻しても保持する。
    window.setBounds(saved.bounds);
    if(saved.maximized)window.maximize();
   }
   return true;
  },
  resize(height){
   if(!original||!window||window.isDestroyed()||!ミニ高さは有効(height))return false;
   const bounds=window.getBounds();
   if(bounds.width===ミニ幅&&bounds.height===height)return true;
   // 縮小時は以前の最小高さに阻まれない順序にし、拡大時も現在の位置を保つ。
   window.setMinimumSize(ミニ幅,height);
   window.setBounds({...bounds,width:ミニ幅,height});
   return true;
  },
 };
}
module.exports={ミニ表示を作成,ミニ高さは有効};
