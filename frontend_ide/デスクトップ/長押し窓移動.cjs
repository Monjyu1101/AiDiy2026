// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
const movableKinds=new Set(['ide','code','live','term','browser','viewer','explorer','panel-viewer','panel-routes']);
const {showWindowMoveFeedback}=require('./窓移動表示.cjs');

// DOMやページの権限に依存せず、Browser本文・別originのiframeも同じ入力境界で扱う。
// 押下は一旦保留し、短押しならup時、通常の選択dragなら移動開始時に元の入力を渡す。
function installNativeWindowMove({record,contents=record.window.webContents,drag,screen,setTimer=setTimeout,clearTimer=clearTimeout,setTick=setInterval,clearTick=clearInterval}){
 if(!movableKinds.has(record.kind))return()=>{};
 const control=drag.forRecord(record),win=record.window,listeners=[];
 let current=null,disposed=false,replaying=0,suppressUp=false;
 const listen=(target,event,fn)=>{target.on(event,fn);listeners.push(()=>target.removeListener(event,fn));};
 const replay=input=>{if(disposed||contents.isDestroyed())return;replaying++;try{contents.sendInputEvent(input);}finally{replaying--;}};
 function finish(){
  const state=current;current=null;if(!state)return;
  clearTimer(state.timer);clearTick(state.tick);
  if(state.token)control.end(state.token);
  if(state.feedback)void state.feedback.remove().then(()=>{if(!current)replay({type:'mouseMove',x:state.mouse.x,y:state.mouse.y,modifiers:[]});});
 }
 function cancel(){if(current)suppressUp=true;finish();}
 function moved(state){const point=screen.getCursorScreenPoint();return point.x!==state.point.x||point.y!==state.point.y;}
 function activate(state){
  if(current!==state||disposed)return;
  if(moved(state)){finish();replay(state.down);return;}
  state.token=control.begin();
  if(!state.token){cancel();return;}
  suppressUp=true;
  const zoom=contents.getZoomFactor();
  state.center=control.isCenterMove?.();state.zoom=zoom;state.origin=screen.getCursorScreenPoint();
  state.feedback=showWindowMoveFeedback(contents,{x:state.down.x/zoom,y:state.down.y/zoom});
  // mouseMoveを遮断していても、表示面の作成後にChromiumのカーソルを更新する。
  void state.feedback.ready.then(()=>{if(current===state)replay({type:'mouseMove',x:state.down.x,y:state.down.y,modifiers:[]});});
  state.tick=setTick(()=>{if(current===state)move(state);},16);state.tick?.unref?.();
 }
 function move(state){
  if(!control.move(state.token)){cancel();return;}
  if(state.center){const point=screen.getCursorScreenPoint();state.feedback.move({x:(state.down.x+point.x-state.origin.x)/state.zoom,y:(state.down.y+point.y-state.origin.y)/state.zoom});}
 }
 listen(contents,'before-mouse-event',(event,mouse)=>{
  if(disposed||replaying)return;
  if(mouse.type==='mouseDown'){
   if(mouse.button!=='left'){cancel();return;}
   finish();suppressUp=false;
   if(win.isDestroyed()||win.isMaximized()||win.isFullScreen())return;
   event.preventDefault();
   const down={type:'mouseDown',x:mouse.x,y:mouse.y,button:'left',clickCount:mouse.clickCount||1,modifiers:mouse.modifiers||[]};
   const state={down,mouse:down,point:screen.getCursorScreenPoint()};current=state;
   state.timer=setTimer(()=>activate(state),500);state.timer?.unref?.();return;
  }
  if(mouse.type==='mouseUp'&&mouse.button==='left'){
   const state=current;if(state)state.mouse=mouse;
   if(state||suppressUp)event.preventDefault();
   if(state?.token)move(state);
   const click=state&&!state.token&&!suppressUp;finish();suppressUp=false;
   if(click){replay(state.down);replay({type:'mouseUp',x:mouse.x,y:mouse.y,button:'left',clickCount:mouse.clickCount||1,modifiers:mouse.modifiers||[]});}
   return;
  }
  if(!current)return;
  if(mouse.type==='mouseMove'){
   current.mouse=mouse;
   if(current.token){event.preventDefault();move(current);}
   else if(moved(current)){const down=current.down;finish();replay(down);}
  }else if(['mouseWheel','contextMenu'].includes(mouse.type))cancel();
 });
 listen(contents,'before-input-event',(event,input)=>{if(input.key==='Escape'){if(current?.token)event.preventDefault?.();cancel();}});
 listen(win,'blur',cancel);
 listen(contents,'did-start-navigation',(_event,_url,inPlace,mainFrame)=>{if(mainFrame&&!inPlace)cancel();});
 listen(contents,'render-process-gone',cancel);
 const dispose=()=>{if(disposed)return;disposed=true;cancel();for(const remove of listeners)remove();};
 listen(contents,'destroyed',dispose);listen(win,'closed',dispose);
 return dispose;
}
module.exports={installNativeWindowMove};
