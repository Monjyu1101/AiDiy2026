// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('aidiyWindow',{
 title:()=>ipcRenderer.invoke('development:window','title'),
 copyFilePath:path=>ipcRenderer.invoke('development:copy-file-path',path),
 openFile:path=>ipcRenderer.invoke('development:open-file',path),
 draftTargets:()=>ipcRenderer.invoke('development:draft-targets'),
 insertDraft:value=>ipcRenderer.invoke('development:draft-insert',value),
 registerDraftTarget:value=>ipcRenderer.invoke('development:draft-target-register',value),
 onDraftHandoff:callback=>{
  if(typeof callback!=='function')return()=>{};
  const listener=(_event,data)=>{
   if(!data||typeof data.requestId!=='string'||data.requestId.length>128)return;
   try{
    // 同期した下書き更新の成否だけを返す。Electronのeventや任意のIPCは公開しない。
    const result=callback(data);
    ipcRenderer.send('development:draft-result',{requestId:data.requestId,ok:result?.ok===true,error:typeof result?.error==='string'?result.error.slice(0,500):undefined});
   }catch{ipcRenderer.send('development:draft-result',{requestId:data.requestId,ok:false,error:'下書きを追加できませんでした。'});}
  };
  ipcRenderer.on('development:draft-handoff',listener);
  return()=>ipcRenderer.removeListener('development:draft-handoff',listener);
 },
 childWindows:()=>ipcRenderer.invoke('development:child-windows'),endSession:()=>ipcRenderer.invoke('development:end-session'),openApp:kind=>ipcRenderer.invoke('development:open-app',kind),openViewer:path=>ipcRenderer.invoke('development:open-viewer',path),maximize:()=>ipcRenderer.invoke('development:window','maximize'),isMaximized:()=>ipcRenderer.invoke('development:window','isMaximized'),minimize:()=>ipcRenderer.invoke('development:window','minimize'),close:()=>ipcRenderer.invoke('development:window','close')});
