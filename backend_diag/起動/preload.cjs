'use strict';
const {contextBridge,ipcRenderer}=require('electron');
// 固定ウィンドウ操作だけ。ミニ表示の幅や汎用 invoke は公開せず、高さも範囲を限定する。
contextBridge.exposeInMainWorld('aidiyWindow',Object.freeze({
 initialMini:process.argv.includes('--aidiy-diag-initial-mini'),
 minimize:()=>ipcRenderer.invoke('diag:window','minimize'),
 maximize:()=>ipcRenderer.invoke('diag:window','maximize'),
 isMaximized:()=>ipcRenderer.invoke('diag:window','isMaximized'),
 getPinState:()=>ipcRenderer.invoke('diag:window','getPinState'),
 togglePin:()=>ipcRenderer.invoke('diag:window','togglePin'),
 onPinState:callback=>{
  if(typeof callback!=='function')return ()=>{};
  const listener=(_event,state)=>{if(state&&typeof state.pinned==='boolean'&&typeof state.locked==='boolean')callback({pinned:state.pinned,locked:state.locked});};
  ipcRenderer.on('diag:pin-state',listener);
  return ()=>ipcRenderer.removeListener('diag:pin-state',listener);
 },
 close:()=>ipcRenderer.invoke('diag:window','close'),
 selectProject:()=>ipcRenderer.invoke('diag:window','selectProject'),
 startMini:enabled=>typeof enabled==='boolean'?ipcRenderer.invoke('diag:window','startMini',enabled):Promise.resolve(false),
 finishMini:()=>ipcRenderer.invoke('diag:window','finishMini'),
 startMicro:enabled=>typeof enabled==='boolean'?ipcRenderer.invoke('diag:window','startMicro',enabled):Promise.resolve(false),
 expandMicro:(expanded,count=13)=>typeof expanded==='boolean'&&Number.isInteger(count)&&count>=0&&count<=32?ipcRenderer.invoke('diag:window','expandMicro',{expanded,count}):Promise.resolve(false),
 beginMicroMove:()=>ipcRenderer.invoke('diag:window','beginMicroMove'),
 moveMicro:token=>typeof token==='string'?ipcRenderer.invoke('diag:window','moveMicro',token):Promise.resolve(false),
 endMicroMove:token=>typeof token==='string'?ipcRenderer.invoke('diag:window','endMicroMove',token):Promise.resolve(false),
 beginDisplay:mode=>['normal','mini','micro'].includes(mode)?ipcRenderer.invoke('diag:window','beginDisplay',mode):Promise.resolve(false),
 finishDisplay:()=>ipcRenderer.invoke('diag:window','finishDisplay'),
 resizeMini:height=>Number.isInteger(height)&&height>=80&&height<=360?ipcRenderer.invoke('diag:window','resizeMini',height):Promise.resolve(false),
}));
