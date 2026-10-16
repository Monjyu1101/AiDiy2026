// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('aidiyWindow',{
 beginCodeMove:()=>ipcRenderer.invoke('development:code-move-begin'),
 moveCode:token=>ipcRenderer.invoke('development:code-move',token),
 endCodeMove:token=>ipcRenderer.invoke('development:code-move-end',token),
 prepareExplorer:(rect,kind)=>ipcRenderer.invoke('development:prepare-explorer',rect,kind),
 resizeRoutes:(name,height)=>ipcRenderer.invoke('development:resize-routes',name,height),
 showExplorer:(name,reduced)=>ipcRenderer.invoke('development:show-explorer',name,reduced),
 onViewerClosed:callback=>{const listener=(_event,path)=>callback(path);ipcRenderer.on('development:viewer-closed',listener);return()=>ipcRenderer.removeListener('development:viewer-closed',listener);},
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
 childWindows:()=>ipcRenderer.invoke('development:child-windows'),endSession:()=>ipcRenderer.invoke('development:end-session'),openApp:kind=>ipcRenderer.invoke('development:open-app',kind),openViewer:(path,rect)=>ipcRenderer.invoke('development:open-viewer',path,rect),maximize:()=>ipcRenderer.invoke('development:window','maximize'),isMaximized:()=>ipcRenderer.invoke('development:window','isMaximized'),minimize:()=>ipcRenderer.invoke('development:window','minimize'),close:()=>ipcRenderer.invoke('development:window','close')});
