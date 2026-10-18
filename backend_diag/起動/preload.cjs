'use strict';
const {contextBridge,ipcRenderer}=require('electron');
// 固定ウィンドウ操作だけ。ミニ表示も真偽値だけを受け取り、寸法や汎用 invoke は公開しない。
contextBridge.exposeInMainWorld('aidiyWindow',Object.freeze({
 minimize:()=>ipcRenderer.invoke('diag:window','minimize'),
 maximize:()=>ipcRenderer.invoke('diag:window','maximize'),
 isMaximized:()=>ipcRenderer.invoke('diag:window','isMaximized'),
 close:()=>ipcRenderer.invoke('diag:window','close'),
 startMini:enabled=>typeof enabled==='boolean'?ipcRenderer.invoke('diag:window','startMini',enabled):Promise.resolve(false),
}));
