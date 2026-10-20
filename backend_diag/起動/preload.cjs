'use strict';
const {contextBridge,ipcRenderer}=require('electron');
// 固定ウィンドウ操作だけ。ミニ表示の幅や汎用 invoke は公開せず、高さも範囲を限定する。
contextBridge.exposeInMainWorld('aidiyWindow',Object.freeze({
 initialMini:process.argv.includes('--aidiy-diag-initial-mini'),
 minimize:()=>ipcRenderer.invoke('diag:window','minimize'),
 maximize:()=>ipcRenderer.invoke('diag:window','maximize'),
 isMaximized:()=>ipcRenderer.invoke('diag:window','isMaximized'),
 close:()=>ipcRenderer.invoke('diag:window','close'),
 selectProject:()=>ipcRenderer.invoke('diag:window','selectProject'),
 startMini:enabled=>typeof enabled==='boolean'?ipcRenderer.invoke('diag:window','startMini',enabled):Promise.resolve(false),
 resizeMini:height=>Number.isInteger(height)&&height>=80&&height<=360?ipcRenderer.invoke('diag:window','resizeMini',height):Promise.resolve(false),
}));
