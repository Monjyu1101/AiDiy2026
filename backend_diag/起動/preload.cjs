'use strict';
const {contextBridge,ipcRenderer}=require('electron');
// Term と同名の固定4操作だけ。URL、ファイル、汎用 invoke は公開しない。
contextBridge.exposeInMainWorld('aidiyWindow',Object.freeze({
 minimize:()=>ipcRenderer.invoke('diag:window','minimize'),
 maximize:()=>ipcRenderer.invoke('diag:window','maximize'),
 isMaximized:()=>ipcRenderer.invoke('diag:window','isMaximized'),
 close:()=>ipcRenderer.invoke('diag:window','close'),
}));
