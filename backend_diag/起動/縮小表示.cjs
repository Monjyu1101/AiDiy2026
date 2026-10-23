'use strict';

const layerId='aidiy-size-image',styleId='aidiy-size-style';
const cleanupScript=`delete globalThis.__aidiySizeLayer;document.getElementById('${layerId}')?.remove();document.getElementById('${styleId}')?.remove()`;
const contains=(outer,inner)=>inner.x>=outer.x&&inner.y>=outer.y&&inner.x+inner.width<=outer.x+outer.width&&inner.y+inner.height<=outer.y+outer.height;
// 元の大きな窓を演出面として使う。フォームは非表示でも測定できるため、
// miniのResizeObserverが返す最終高さまでnative寸法を変えずに取り込める。
function 縮小窓を作成(window,getState){
 const methods=new Set(['setBounds','setMinimumSize','setMaximizable','setResizable','unmaximize']);
 return new Proxy(window,{get(target,key){
  const state=getState(),small=state?.self&&!state.applied;
  if(small){
   if(key==='getBounds'||key==='getContentBounds')return ()=>({...state.bounds});
   if(key==='getNormalBounds'&&(state.ops.has('unmaximize')||state.ops.has('setBounds')))return ()=>({...state.bounds});
   if(key==='isMaximized'&&state.ops.has('unmaximize'))return ()=>false;
   const setter={getMinimumSize:'setMinimumSize',isMaximizable:'setMaximizable',isResizable:'setResizable'}[key];
   if(setter&&state.ops.has(setter))return ()=>setter==='setMinimumSize'?[...state.ops.get(setter)]:state.ops.get(setter)[0];
   if(methods.has(key))return (...args)=>{
    if(key==='setBounds')state.bounds={...state.bounds,...args[0]};
    if(key==='unmaximize')state.bounds={...state.target};
    state.ops.set(key,args);
   };
  }
  const value=Reflect.get(target,key,target);return typeof value==='function'?value.bind(target):value;
 }});
}
function 適用(window,state){
 if(!state.self||state.applied||window.isDestroyed())return;
 state.applied=true;
 // 中間setBoundsをまとめ、最小寸法・最大化解除を先に適用して最後に一度だけ確定する。
 for(const key of ['unmaximize','setMinimumSize','setResizable','setMaximizable'])if(state.ops.has(key))window[key](...state.ops.get(key));
 if(state.ops.has('setBounds')||state.ops.has('unmaximize'))window.setBounds(state.bounds,false);
}
function 準備script(snapshot,from,target){
 return `(async()=>{${cleanupScript};const token={};globalThis.__aidiySizeLayer=token;const image=document.createElement('img');image.id='${layerId}';image.src=${JSON.stringify(snapshot)};image.style.cssText='position:fixed;left:0;top:0;width:${from.width}px;height:${from.height}px;z-index:2147483647;pointer-events:none;transform-origin:0 0;';await image.decode();if(globalThis.__aidiySizeLayer!==token)return;const style=document.createElement('style');style.id='${styleId}';style.textContent='html,body{background:transparent!important}body>*:not(#${layerId}):not(#${styleId}){visibility:hidden!important}#app{width:${target.width}px!important;max-width:none!important}';document.head.append(style);document.body.append(image);})()`;
}
function 演出script(from,to,duration){
 const end=`translate(${to.x-from.x}px,${to.y-from.y}px) scale(${to.width/from.width},${to.height/from.height})`;
 return `(async()=>{const image=document.getElementById('${layerId}');if(!image)return;const motion=image.animate([{transform:'translate(0px,0px) scale(1,1)'},{transform:${JSON.stringify(end)}}],{duration:${duration},easing:'cubic-bezier(.33,1,.68,1)',fill:'forwards'});await motion.finished.catch(()=>{});})()`;
}
module.exports={contains,縮小窓を作成,適用,準備script,演出script,cleanupScript};
