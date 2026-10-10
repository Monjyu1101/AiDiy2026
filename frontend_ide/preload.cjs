// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('aidiyWindow',{childWindows:()=>ipcRenderer.invoke('development:child-windows'),endSession:()=>ipcRenderer.invoke('development:end-session'),openApp:kind=>ipcRenderer.invoke('development:open-app',kind),maximize:()=>ipcRenderer.invoke('development:window','maximize'),isMaximized:()=>ipcRenderer.invoke('development:window','isMaximized'),minimize:()=>ipcRenderer.invoke('development:window','minimize'),close:()=>ipcRenderer.invoke('development:window','close')});
