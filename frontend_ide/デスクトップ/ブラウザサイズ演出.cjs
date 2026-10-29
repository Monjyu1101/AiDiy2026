// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
const {演出時間}=require('../host/scripts/window-opening.cjs');
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
function bounded(promise,ms){return new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('サイズ演出の待機時間を超えました。')),ms);Promise.resolve(promise).then(value=>{clearTimeout(timer);resolve(value);},error=>{clearTimeout(timer);reject(error);});});}
const paint=contents=>bounded(contents.executeJavaScript('new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))'),300).catch(()=>{});
function union(a,b){const x=Math.min(a.x,b.x),y=Math.min(a.y,b.y);return{x,y,width:Math.max(a.x+a.width,b.x+b.width)-x,height:Math.max(a.y+a.height,b.y+b.height)-y};}
function snapshotHTML(host,page,bounds,rect){
 return `<!doctype html><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'"><style>html,body{margin:0;width:100%;height:100%;overflow:hidden;background:transparent}#frame{position:absolute;left:0;top:0;width:${bounds.width}px;height:${bounds.height}px;transform-origin:0 0}img{position:absolute;display:block;object-fit:fill;user-select:none;-webkit-user-drag:none}#host{inset:0;width:100%;height:100%}#page{left:${rect.x}px;top:${rect.y}px;width:${rect.width}px;height:${rect.height}px}</style><div id="frame"><img id="host" alt="" src="${host}"><img id="page" alt="" src="${page}"></div>`;
}
// 実窓を毎フレーム動かさず、操作欄とWebContentsView本文の画像を透明な一時窓で合成する。
// 入力透過/focusable:falseはWindowsで白い面になる既知条件なので使わない。
function createBrowserResizeMotion({BrowserWindow,window,view,isSettled=()=>true,fullscreenKey,wait=pause,duration=演出時間}){
 let generation=0,current,disposed=false,opacityUnavailable=false;
 const listeners=[];
 const listen=(target,event,fn)=>{target.on(event,fn);listeners.push(()=>target.removeListener(event,fn));};
 function cleanup(state,focus=false){
  if(!state)return;state.finished=true;
  if(state.dimmed&&!window.isDestroyed()){window.setOpacity(state.opacity);state.dimmed=false;}
  if(state.canvas&&!state.canvas.isDestroyed())state.canvas.destroy();
  if(focus&&!disposed&&!window.isDestroyed()&&!window.isMinimized?.()){window.focus();if(!state.focused?.isDestroyed?.())state.focused?.focus?.();}
 }
 function outcome(state){if(state.changeError)throw state.changeError;return state.result;}
 function applyChange(state){if(state.applied)return outcome(state);state.applied=true;try{return state.result=state.change();}catch(error){state.changeError=error;throw error;}}
 // 撮影待ちでも受け付け済み操作は順に確定する。F11/🔲連打の偶奇を失わない。
 function cancel(focus=false,commit=true){generation++;const state=current;current=undefined;if(commit&&state&&!state.applied&&!disposed&&!window.isDestroyed())try{applyChange(state);}catch{/* 元の要求Promiseからエラーを返す。 */}cleanup(state,focus);}
 const valid=state=>!state.finished&&!disposed&&current===state&&state.generation===generation&&!window.isDestroyed();
 const input=(_event,value)=>{if(value.key==='F11'&&value.isAutoRepeat)return;if(value.type==='mouseDown'||value.type==='mouseWheel'||value.type==='keyDown')cancel();};
 for(const contents of [window.webContents,view.webContents]){
  listen(contents,'before-input-event',input);listen(contents,'before-mouse-event',input);
  for(const event of ['did-start-loading','render-process-gone','destroyed'])listen(contents,event,()=>cancel());
 }
 for(const event of ['will-resize','will-move','minimize','hide','close'])listen(window,event,()=>cancel(false,false));
 async function settled(state){
  let previous='',stable=0;
  for(let i=0;i<75&&valid(state);i++){
   const value=JSON.stringify([window.getContentBounds(),view.getBounds()]);
   stable=isSettled()&&value===previous?stable+1:0;previous=value;
   if(stable>=2)return true;
   await wait(16);
  }
  return false;
 }
 async function run(change){
  cancel();
  if(disposed||window.isDestroyed())return;
  // 画像が取得できない環境は演出だけ省略し、サイズ操作をそのまま実行する。
  if(opacityUnavailable||!BrowserWindow||!window.webContents.capturePage||!view.webContents.capturePage||!view.getBounds||!window.setOpacity||window.isMinimized?.()||view.getVisible?.()===false)return change();
  const state={generation,opacity:window.getOpacity?.()??1,focused:window.webContents.isFocused?.()?window.webContents:view.webContents,applied:false,change};current=state;
  let result;
  try{
   const before=window.getContentBounds(),rect=view.getBounds();
   const [host,page]=await bounded(Promise.all([window.webContents.capturePage(undefined,{stayHidden:true,stayAwake:true}),view.webContents.capturePage(undefined,{stayHidden:true,stayAwake:true})]),700);
   if(!valid(state))return outcome(state);
   if(host.isEmpty()||page.isEmpty()||before.width<=0||before.height<=0)throw Error('表示画像が空です。');
   const canvas=state.canvas=new BrowserWindow({title:'AiDiy Browser サイズ変更',...before,frame:false,transparent:true,backgroundColor:'#00000000',hasShadow:false,resizable:false,skipTaskbar:true,show:false,enableLargerThanScreen:true,alwaysOnTop:window.isAlwaysOnTop?.()===true,webPreferences:{sandbox:true,contextIsolation:true,nodeIntegration:false}});
   canvas.isAiDiyOpeningCanvas=true;
   canvas.setBounds(before);
   canvas.once('closed',()=>{if(valid(state))cancel();});
   canvas.webContents.on('render-process-gone',()=>{if(valid(state))cancel();});
   canvas.webContents.setWindowOpenHandler(()=>({action:'deny'}));
   canvas.webContents.on('will-navigate',event=>event.preventDefault());
   canvas.webContents.on('before-mouse-event',(event,value)=>{if(valid(state)&&(value.type==='mouseDown'||value.type==='mouseWheel')){event.preventDefault();cancel(true);}});
   canvas.webContents.on('before-input-event',(event,value)=>{if(valid(state)&&value.type==='keyDown'&&!value.isAutoRepeat){cancel(true);fullscreenKey?.(event,value);if(!event.defaultPrevented)event.preventDefault();}});
   await bounded(canvas.loadURL('data:text/html;charset=utf-8,'+encodeURIComponent(snapshotHTML(host.toDataURL(),page.toDataURL(),before,rect))),700);
   if(!valid(state))return outcome(state);
   canvas.showInactive();await paint(canvas.webContents);
   if(!valid(state))return outcome(state);
   state.dimmed=true;window.setOpacity(0);
   // Linux等ではsetOpacityがno-op。実窓との二重表示を避け、以後は演出だけ省略する。
   if((window.getOpacity?.()??0)>0){opacityUnavailable=true;throw Error('この環境ではウィンドウの透明度を変更できません。');}
   result=applyChange(state);
   if(!await settled(state)||!valid(state))return outcome(state);
   const after=window.getContentBounds(),area=union(before,after);
   canvas.setAlwaysOnTop(window.isAlwaysOnTop?.()===true);
   canvas.setBounds(area);
   // キャンバス外枠はここで確定。各フレームで変えるのは画像のtransformだけ。
   const from=`translate(${before.x-area.x}px,${before.y-area.y}px) scale(1,1)`,to=`translate(${after.x-area.x}px,${after.y-area.y}px) scale(${after.width/before.width},${after.height/before.height})`;
   await bounded(canvas.webContents.executeJavaScript(`(()=>{const frame=document.getElementById('frame');frame.style.transform=${JSON.stringify(from)};return frame.animate([{transform:${JSON.stringify(from)}},{transform:${JSON.stringify(to)}}],{duration:${duration},easing:'cubic-bezier(.33,1,.68,1)',fill:'forwards'}).finished.catch(()=>{});})()`),duration+1000);
   if(valid(state))await paint(window.webContents);
   return result;
  }catch(error){
   if(state.changeError)throw state.changeError;
   if(valid(state)&&!state.applied)return applyChange(state);
   return result;
  }finally{
   cleanup(state);if(current===state)current=undefined;
  }
 }
 function dispose(){if(disposed)return;disposed=true;cancel(false,false);for(const remove of listeners)remove();}
 return{run,cancel,dispose};
}
module.exports={createBrowserResizeMotion,snapshotHTML,union};
