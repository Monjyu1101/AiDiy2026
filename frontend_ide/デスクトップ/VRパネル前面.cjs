// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026

// 別rendererのExplorer・軌跡バーもBrowserWindowは同じmainで管理する。
// OS親子関係・上位topmost層・focus()・定期監視は使わず、VR本体との相対順だけ直す。
function createVRPanelStacking({windows,isActive,schedule=setImmediate,cancel=clearImmediate,onError=error=>console.warn('VRパネルの前面配置:',error.message)}){
 const entries=new WeakMap(),pending=new Map(),running=new Set();
 const alive=record=>record&&!record.window.isDestroyed();
 const visible=record=>alive(record)&&record.window.isVisible?.()!==false&&record.window.isMinimized?.()!==true;
 const panel=record=>['explorer','panel-routes'].includes(record.kind);
 function refresh(owner){
  if(!visible(owner)||!isActive(owner)||running.has(owner))return;
  running.add(owner);
  try{
   const children=[...windows.values()].filter(record=>record.owner===owner&&panel(record)&&visible(record));
   // 選択中のパネルが他のパネルに隠れないよう、最後に積む。
   children.sort((a,b)=>Number(!!a.window.isFocused?.())-Number(!!b.window.isFocused?.()));
   let below=owner.window;
   for(const child of children){
    try{child.window.moveAbove(below.getMediaSourceId());below=child.window;}
    catch(error){onError(error);}
   }
  }finally{running.delete(owner);}
 }
 function request(owner){
  if(!alive(owner)||!isActive(owner)||running.has(owner))return;
  refresh(owner);
  // focus/showのOS処理が完了した直後にも一度だけ確認する。ポーリングはしない。
  if(!pending.has(owner))pending.set(owner,schedule(()=>{pending.delete(owner);refresh(owner);}));
 }
 function unregister(record){
  const entry=entries.get(record);if(!entry)return;
  for(const event of entry.events)record.window.removeListener(event,entry.refresh);
  record.window.removeListener('closed',entry.closed);entries.delete(record);
  if(pending.has(record)){cancel(pending.get(record));pending.delete(record);}
 }
 function register(record){
  if(entries.has(record)||!alive(record)||!(record.kind==='ide'&&!record.owner||panel(record)&&record.owner))return;
  const owner=record.owner||record;
  // 本体のfocusリスナーは共通ピン制御のmoveTopより後に登録する。
  const events=record===owner?['focus','show','restore','maximize','unmaximize','enter-full-screen','leave-full-screen']:['show','restore','maximize','unmaximize'];
  const entry={events,refresh:()=>request(owner),closed:()=>unregister(record)};entries.set(record,entry);
  for(const event of events)record.window.on(event,entry.refresh);
  record.window.once('closed',entry.closed);
  request(owner);
 }
 return{register,refresh:request,unregister};
}
module.exports={createVRPanelStacking};
