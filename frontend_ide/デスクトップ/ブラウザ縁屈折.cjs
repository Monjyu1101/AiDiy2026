// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026

// 別BrowserWindowのCSSからは本文の画素を参照できないため、縁だけに使う標本をmainで取得する。
// 座標はすべてElectronのDIP。OS倍率やrendererのzoomをここで重ねない。
function browserGlassGeometry(header,owner,view){
 for(const rect of [header,owner,view]){
  if(!rect||!['x','y','width','height'].every(key=>Number.isFinite(rect[key]))||rect.width<=0||rect.height<=0)return null;
 }
 if(header.width>1200||header.height>1000)return null;
 const origin={x:owner.x+view.x,y:owner.y+view.y};
 const x=Math.max(0,Math.ceil(header.x-origin.x)),y=Math.max(0,Math.ceil(header.y-origin.y));
 const right=Math.min(Math.floor(view.width),Math.floor(header.x+header.width-origin.x));
 const bottom=Math.min(Math.floor(view.height),Math.floor(header.y+header.height-origin.y));
 if(right<=x||bottom<=y)return null;
 const rect={x,y,width:right-x,height:bottom-y};
 return{rect,width:header.width,height:header.height,x:origin.x+x-header.x,y:origin.y+y-header.y,captureWidth:rect.width,captureHeight:rect.height};
}

function createBrowserGlass({record,entry,getFrame,send,now=Date.now,setTimer=setInterval,clearTimer=clearInterval}){
 const source=entry.view.webContents,interval=250,listeners=[];
 let disposed=false,active=false,timer,busy=false,revision=0,navigation=0,key='',published=false,lastCapture=-Infinity;
 function emit(value){try{send(value);}catch{/* 装飾の配送失敗を窓操作へ伝播させない。 */}}
 function clear(){if(published){published=false;emit(null);}}
 function invalidate(){revision++;key='';clear();}
 function listen(target,name,listener){target?.on?.(name,listener);listeners.push(()=>target?.removeListener?.(name,listener));}
 function state(){
  try{
   if(disposed||!active||record.window.isDestroyed()||!record.window.isFullScreen()||record.window.isMinimized?.()||source.isDestroyed()||!entry.available||entry.dialogOpen||typeof source.capturePage!=='function')return null;
   const frame=getFrame(),view=entry.view.getBounds?.();
   if(!frame||!view)return null;
   const geometry=browserGlassGeometry(frame,record.window.getContentBounds(),view);
   if(!geometry)return null;
   return{geometry,key:JSON.stringify([geometry,source.getURL(),entry.run,navigation])};
  }catch{return null;}
 }
 async function sample(){
  if(disposed||!active)return;
  const current=state();
  if(!current){if(key||published)invalidate();return;}
  if(key!==current.key){invalidate();key=current.key;}
  if(busy||now()-lastCapture<interval)return;
  busy=true;lastCapture=now();const run=revision;
  try{
   const image=await source.capturePage(current.geometry.rect,{stayHidden:true,stayAwake:false});
   const latest=state();
   if(!latest||run!==revision||latest.key!==current.key){if(!disposed&&run===revision)invalidate();return;}
   if(image.isEmpty())throw Error('empty glass sample');
   const {rect,...geometry}=current.geometry;
   // 高DPI画像もDIP寸法に正規化して転送量を制限する。保存・外部送信は行わない。
   const src=image.resize({width:rect.width,height:rect.height,quality:'good'}).toDataURL({scaleFactor:1});
   if(!src.startsWith('data:image/png;base64,')||src.length>8*1024*1024)throw Error('invalid glass sample');
   emit({src,...geometry});published=true;
  }catch{if(!disposed&&run===revision)clear();}
  finally{busy=false;}
 }
 function start(){
  if(disposed)return;active=true;
  if(timer===undefined){timer=setTimer(()=>{void sample();},interval);timer?.unref?.();}
  void sample();
 }
 function pause(){active=false;if(timer!==undefined)clearTimer(timer);timer=undefined;invalidate();}
 function dispose(){if(disposed)return;pause();disposed=true;for(const stop of listeners)stop();}
 const navigated=()=>{navigation++;invalidate();};
 for(const event of ['did-start-navigation','did-navigate-in-page','render-process-gone'])listen(source,event,navigated);
 listen(source,'destroyed',dispose);
 for(const event of ['move','resize'])listen(record.window,event,invalidate);
 for(const event of ['minimize','leave-full-screen'])listen(record.window,event,pause);
 listen(record.window,'restore',()=>{if(getFrame())start();});
 listen(record.window,'closed',dispose);
 return{start,pause,invalidate,dispose};
}
module.exports={browserGlassGeometry,createBrowserGlass};
