// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026

// 全Electronアプリで同じ最前面層を使う。別プロセスの窓同士もOSの選択順に従う。
// 起動元との関係はrecord.ownerで管理し、ピン状態からOSの親子関係を作らない。
// 各パネルを独立して選択できるよう、フォーカス奪取や定期再固定はしない。
function createWindowPins({onChanged=()=>{}}={}) {
 const entries=new WeakMap();
 const alive=window=>window&&!window.isDestroyed();
 function state(window) {
  const entry=alive(window)&&entries.get(window);
  return {pinned:!!entry&&(entry.requested||entry.locked),locked:!!entry?.locked};
 }
 function raiseSelected(window) {
  const entry=entries.get(window);
  if(!alive(window)||!entry||entry.raising||!state(window).pinned)return;
  entry.raising=true;
  try{window.moveTop?.();}finally{entry.raising=false;}
 }
 function apply(window) {
  const entry=entries.get(window);
  if(!alive(window)||!entry)return state(window);
  const value=state(window);
  if(entry.applied!==value.pinned){
   // pop-up-menu / screen-saver 等の上位層を使わず、全アプリを floating に揃える。
   if(value.pinned)window.setAlwaysOnTop(true,'floating');
   else window.setAlwaysOnTop(false);
   entry.applied=value.pinned;
  }
  onChanged(window,value);
  return value;
 }
 function unregister(window) {
  const entry=entries.get(window);if(!entry)return;
  window.removeListener('focus',entry.focus);
  window.removeListener('closed',entry.closed);
  entries.delete(window);
 }
 function register(window,{pinned=false,locked=false}={}) {
  if(!alive(window))return state(window);
  if(entries.has(window))return state(window);
  const entry={requested:pinned===true,locked:locked===true,applied:undefined,raising:false,
   focus:()=>raiseSelected(window),closed:()=>unregister(window)};
  entries.set(window,entry);
  window.on('focus',entry.focus);window.once('closed',entry.closed);
  return apply(window);
 }
 function toggle(window) {
  const entry=entries.get(window);
  if(!alive(window)||!entry||entry.locked)return state(window);
  entry.requested=!entry.requested;
  const value=apply(window);
  if(value.pinned&&window.isFocused?.())raiseSelected(window);
  return value;
 }
 function setLocked(window,locked) {
  const entry=entries.get(window);
  if(!alive(window)||!entry||entry.locked===(locked===true))return state(window);
  // VR前のユーザー選択を保持し、解除した時にその状態へ戻す。
  entry.locked=locked===true;
  return apply(window);
 }
 return {register,state,toggle,setLocked,unregister};
}
module.exports={createWindowPins};
