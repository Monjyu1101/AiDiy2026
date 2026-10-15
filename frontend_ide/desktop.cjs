// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
const {app,BrowserWindow,ipcMain,shell,clipboard,session,screen,dialog}=require('electron');
const {join}=require('node:path');
const {mkdirSync,mkdtempSync,rmSync}=require('node:fs');
const {projectProfile}=require('./デスクトップ/project-profile.cjs');
const url=process.env.AIDIY_DEVELOPMENT_URL,kind=process.env.AIDIY_DEVELOPMENT_KIND;
if(!url||!/^http:\/\/127\.0\.0\.1:\d+\/$/.test(url)||!['code','live','ide','term'].includes(kind))throw Error('起動元が不正です。');
app.setName(`aidiy_${kind}`);
// ランチャーが引数を解決したプロジェクトで、ロック取得より先にIDEのプロファイルを分ける。
const profile=kind==='ide'?projectProfile(app.getPath('appData'),process.env.AIDIY_DEVELOPMENT_PROJECT||process.cwd()):join(app.getPath('appData'),`aidiy_${kind}_vue`);
if(kind==='ide')mkdirSync(profile,{recursive:true});
app.setPath('userData',profile);
if(kind==='ide')app.setPath('sessionData',profile);
if(kind==='term'){
 const temporaryProfile=mkdtempSync(join(app.getPath('temp'),'aidiy-term-profile-'));
 app.setPath('userData',temporaryProfile);
 app.on('quit',()=>{try{rmSync(temporaryProfile,{recursive:true,force:true,maxRetries:2,retryDelay:100});}catch{}});
}
const {windowBounds,windowMinimumSize}=require('./デスクトップ/window-layout.cjs');
const {reserveTermSlot}=require('./デスクトップ/term-window-slot.cjs');
const {拡大表示}=require('./host/scripts/window-opening.cjs');
// IDEは同じプロジェクトだけ既存窓へ戻す。Code / Liveは種別ごと、Termは複数起動する。
if(kind!=='term'&&!app.requestSingleInstanceLock()){
 if(process.send)process.send({existingWindow:true},()=>app.exit(0));else app.exit(0);
 return;
}
const windows=new Map(),closing=new Set(),closedServers=new WeakSet();
const {createDraftRouter}=require('./デスクトップ/draft-router.cjs');
const {readDevelopmentState}=require('./デスクトップ/desktop-session.cjs');
const draftRouter=createDraftRouter({records:windows,readState,sessionKey:state=>sessionKey(state),focusWindow,isQuitting:()=>quitting});
const {createNativePreviewActions}=require('./デスクトップ/native-preview-actions.cjs');
const nativePreviewActions=createNativePreviewActions({records:windows,trustedEvent,readState,sessionKey:state=>sessionKey(state),clipboard,shell,dialog,isQuitting:()=>quitting});
let quitting=false;
function focusWindow(window){
 if(!window||window.isDestroyed())return;
 if(window.isMinimized())window.restore();window.show();window.focus();
}
app.on('second-instance',()=>focusWindow([...windows.values()].find(record=>!record.owner)?.window));
app.on('activate',()=>focusWindow([...windows.values()].find(record=>!record.owner)?.window));
function closeServer(server){
 if(!server||closedServers.has(server))return;closedServers.add(server);
 const pending=server.close().catch(error=>console.error(error));closing.add(pending);
 void pending.finally(()=>closing.delete(pending));
}
const sessionKey=state=>state.active?`${state.mode}:${state.startedAt}`:'';
async function readState(record){return readDevelopmentState(record);}
function closeChildren(owner){
 owner.revision++;draftRouter.invalidate(owner);
 for(const child of [...windows.values()])if(child.owner===owner&&!child.window.isDestroyed())child.window.destroy();
}
async function checkChildren(owner){
 if(owner.checking||owner.window.isDestroyed()||![...windows.values()].some(child=>child.owner===owner))return;
 owner.checking=true;const revision=owner.revision;
 try{
  const state=await readState(owner);
  if(owner.window.isDestroyed()||owner.revision!==revision)return;
  if(!sessionKey(state)||[...windows.values()].some(child=>child.owner===owner&&child.linkKey!==sessionKey(state)))closeChildren(owner);
 }catch{ /* 一時的な通信断・不正応答は終了の根拠にせず、次回の監視で再確認する。 */ }finally{owner.checking=false;}
}
function trustedEvent(event){
 const record=windows.get(event.sender),frame=event.senderFrame;
 return record&&!record.window.isDestroyed()&&frame&&frame===event.sender.mainFrame&&typeof frame.url==='string'&&frame.url.split('#')[0]===record.url?record:null;
}
function audioAllowed(contents,permission,details){
 const record=windows.get(contents);
 return !!record&&record.kind==='live'&&permission==='media'&&details?.isMainFrame===true&&details.requestingUrl?.split('#')[0]===record.url;
}
async function createWindow(kind,url,server,owner,linkKey){
 // ピン留めのビューアは #viewer=ファイル で開く。照合・遷移の判定は # より前の URL で行う。
 const [base,hash='']=url.split('#');
 const viewerPath=kind==='viewer'&&hash.startsWith('viewer=')?decodeURIComponent(hash.slice('viewer='.length)):'';
 const ownerBounds=owner?.window.getBounds();
 const area=(ownerBounds?screen.getDisplayMatching(ownerBounds):screen.getDisplayNearestPoint(screen.getCursorScreenPoint())).workArea;
 const used=new Set([...windows.values()].filter(item=>item.owner===owner&&item.kind===kind&&!item.window.isDestroyed()).map(item=>item.slot));
 const ownerRevision=owner?.revision;
 const placement=kind==='term'?await reserveTermSlot():null;
 if(quitting||owner&&(owner.window.isDestroyed()||owner.revision!==ownerRevision)){placement?.close();throw Error('起動元の利用が終了しました。');}
 let slot=placement?.slot||0;if(owner&&(kind==='code'||kind==='viewer'))while(used.has(slot))slot++;
 const bounds=windowBounds(kind,area,ownerBounds,slot);
 const title=kind==='viewer'?`AiDiy IDE / Viewer - ${viewerPath.split('/').at(-1)}`:`AiDiy ${owner?'IDE / ':''}${kind==='ide'?'IDE':kind==='code'?`Code${owner?' '+(slot+1):''}`:kind==='term'?`Term${owner?' '+(slot+1):''}`:'Live'}`;
 let window;
 try{window=new BrowserWindow({title,...bounds,...windowMinimumSize(kind,bounds),show:false,frame:false,roundedCorners:false,backgroundColor:'#000',autoHideMenuBar:true,icon:join(__dirname,'dist/AiDiy.png'),webPreferences:{preload:join(__dirname,'デスクトップ/preload.cjs'),sandbox:true,contextIsolation:true,nodeIntegration:false,autoplayPolicy:'no-user-gesture-required'}});}catch(error){placement?.close();throw error;}
 window.once('closed',()=>placement?.close());
 // autoplayPolicy: ビューアの「表示」で開いた HTML（ナレーション付きの動画ページなど）の音声を、クリックなしで再生できるようにする。
 // Windowsのフレームレス窓も、外枠の論理座標を明示してDPI差を補正する。
 window.setBounds(bounds);
 // IDEから開いたCode / Liveは、IDEや他アプリを操作中も手前に保つ。
 if(owner)window.setAlwaysOnTop(true);
 const contents=window.webContents;
 contents.on('page-title-updated',event=>{event.preventDefault();window.setTitle(title);});
 const record={window,kind,url:base,viewerPath,server,owner,linkKey,slot,revision:0,pending:new Map()};windows.set(contents,record);
 window.on('focus',()=>draftRouter.focused(record));
 // IDEの×・Alt+F4は、利用中（接続利用・オフライン利用の開始後）だけ確認してから全体を閉じる。
 // 初期画面と「終了」で起動画面へ戻った後は、守る作業がないので確認しない（状態が不明な時は作業を守るため確認する）。利用終了は子窓だけを閉じる。
 if(kind==='ide'){
  let confirming=false,approved=false;
  window.on('close',event=>{
   if(quitting||approved)return;
   event.preventDefault();if(confirming)return;confirming=true;
   void (async()=>{
    const active=await readState(record).then(state=>state.active,()=>true);
    if(window.isDestroyed())return;
    if(!active){approved=true;window.close();return;}
    const {response}=await dialog.showMessageBox(window,{type:'question',title:'AiDiy IDE',message:'AiDiy IDE を終了しますか？',buttons:['終了する','キャンセル'],defaultId:1,cancelId:1,noLink:true});
    if(response===0&&!window.isDestroyed()){approved=true;window.close();}
   })().catch(error=>console.error(error)).finally(()=>{confirming=false;});
  });
 }
 const monitor=kind==='ide'?setInterval(()=>void checkChildren(record),400):undefined;monitor?.unref();
 window.once('closed',()=>{clearInterval(monitor);draftRouter.invalidate(record);nativePreviewActions.invalidate(record);closeChildren(record);windows.delete(contents);closeServer(server);});
 contents.on('did-start-navigation',(_event,_url,isInPlace,isMainFrame)=>{if(isMainFrame){nativePreviewActions.invalidate(record);if(!isInPlace)draftRouter.invalidate(record);}});
 contents.on('render-process-gone',()=>{draftRouter.invalidate(record);nativePreviewActions.invalidate(record);});
 contents.on('will-navigate',(event,target)=>{if(target.split('#')[0]!==base)event.preventDefault();});
 contents.on('will-redirect',event=>event.preventDefault());contents.on('will-attach-webview',event=>event.preventDefault());
 contents.setWindowOpenHandler(({url})=>{if(/^https?:\/\//i.test(url))void shell.openExternal(url);return{action:'deny'};});
 try{
  await window.loadURL(url);
  if(!window.isDestroyed()){
   await contents.executeJavaScript("document.documentElement.classList.add('desktop-opening')");
   if(await 拡大表示(BrowserWindow,window,{background:'#000'}))await contents.executeJavaScript("document.documentElement.classList.remove('desktop-opening')");
  }
  return window;
 }
 catch(error){if(!window.isDestroyed())window.destroy();throw error;}
}
process.on('disconnect',()=>app.quit());
app.on('window-all-closed',()=>app.quit());
app.on('before-quit',event=>{
 if(quitting)return;
 event.preventDefault();quitting=true;
 for(const {window} of windows.values())window.destroy();
 void Promise.allSettled([...closing]).finally(()=>app.quit());
});
app.whenReady().then(async()=>{
 // 同一Electronプロセスの複数窓を識別し、Liveのメインフレームだけ音声入力を許可する。
 session.defaultSession.setPermissionCheckHandler((contents,permission,origin,details)=>{
  const record=windows.get(contents);if(!record)return false;
  let sameOrigin=false;try{sameOrigin=new URL(origin).origin===new URL(record.url).origin;}catch{}
  if(permission==='clipboard-sanitized-write')return sameOrigin;
  return sameOrigin&&audioAllowed(contents,permission,details)&&details.mediaType==='audio';
 });
 session.defaultSession.setPermissionRequestHandler((contents,permission,callback,details)=>callback(audioAllowed(contents,permission,details)&&details.mediaTypes?.length===1&&details.mediaTypes[0]==='audio'));
 ipcMain.handle('development:window',(event,action)=>{
  const record=trustedEvent(event);if(!record)return;
  if(action==='minimize')record.window.minimize();else if(action==='close')record.window.close();
  else if(action==='maximize'){if(record.window.isMaximized())record.window.unmaximize();else record.window.maximize();}
  if(action==='title')return record.window.getTitle();
  if(action==='maximize'||action==='isMaximized')return record.window.isMaximized();
 });
 ipcMain.handle('development:draft-target-register',(event,value)=>draftRouter.register(trustedEvent(event),value));
 ipcMain.handle('development:copy-file-path',(event,path)=>nativePreviewActions.copyFilePath(event,path));
 ipcMain.handle('development:open-file',(event,path)=>nativePreviewActions.openFile(event,path));
 ipcMain.handle('development:draft-targets',event=>draftRouter.list(trustedEvent(event)));
 ipcMain.handle('development:draft-insert',(event,value)=>draftRouter.insert(trustedEvent(event),value));
 ipcMain.on('development:draft-result',(event,value)=>draftRouter.acknowledge(trustedEvent(event),value));
 ipcMain.handle('development:end-session',async event=>{
  const record=trustedEvent(event);if(!record||record.kind!=='ide')return;
  closeChildren(record);await Promise.allSettled([...closing]);
 });
 ipcMain.handle('development:child-windows',event=>{
  const owner=trustedEvent(event);
  return{live:!!owner&&owner.kind==='ide'&&[...windows.values()].some(child=>child.owner===owner&&child.kind==='live'&&!child.window.isDestroyed())};
 });
 ipcMain.handle('development:open-app',async(event,type)=>{
  const source=trustedEvent(event),record=source?.kind==='viewer'?source.owner:source;
  if(!record||record.kind!=='ide'||!['ide','viewer'].includes(source.kind)||!['code','live','term'].includes(type))return{ok:false,error:'この画面からは開けません。'};
  // ピン留めからの明示起動も、元のIDEと同じ利用セッションだけに限定する。
  const revision=record.revision;let state;
  try{
   state=await readState(record);
   if(quitting||trustedEvent(event)!==source||source.window.isDestroyed()||record.window.isDestroyed()||record.revision!==revision||!state.active||!state.project?.path||(source!==record&&source.linkKey!==sessionKey(state)))throw Error('IDEの利用状態が変わりました。');
   if(type==='live'&&state.mode!=='online')throw Error('LiveはAiDiy接続利用で開けます。');
  }catch(error){return{ok:false,error:error.message};}
  // Codeは依頼ごとに別窓。Liveだけ初期化中も共有して1窓にする。
  if(type==='live'&&record.pending.has(type))return record.pending.get(type);
  const opening=(async()=>{
   let child;
   try{
    const key=sessionKey(state);
    const existing=[...windows.values()].find(item=>item.owner===record&&item.kind===type&&item.linkKey===key&&!item.window.isDestroyed());
    if(type==='live'&&existing){focusWindow(existing.window);return{ok:true,reused:true};}
    const {startDevelopment}=await import('./server.mjs');
    child=await startDevelopment(state.project.path,{kind:type,offline:state.mode==='offline',linked:true});
    const current=await readState(record);
    if(quitting||trustedEvent(event)!==source||source.window.isDestroyed()||record.revision!==revision||record.window.isDestroyed()||!current.active||current.project?.path!==state.project.path||sessionKey(current)!==key||(source!==record&&source.linkKey!==key))throw Error('IDEの利用状態が変わりました。もう一度開いてください。');
    await createWindow(type,child.url,child,record,key);child=undefined;
    return{ok:true};
   }catch(error){closeServer(child);return{ok:false,error:error.message};}
  })();
  if(type==='live')record.pending.set(type,opening);
  try{return await opening;}finally{if(record.pending.get(type)===opening)record.pending.delete(type);}
 });
 // ピン留め: IDEのプレビューを、同じIDEサーバーのファイルAPIを使う独立ウィンドウ（IDEの子ウィンドウ）で開く。
 // 同じファイルは既存の窓を前面へ出す。利用終了・セッション切り替えでは他の子ウィンドウと一緒に閉じる。
 ipcMain.handle('development:open-viewer',async(event,path)=>{
  const record=trustedEvent(event);
  if(!record||record.kind!=='ide'||typeof path!=='string'||!path||path.length>4096||path.includes('\0'))return{ok:false,error:'この画面からは開けません。'};
  try{
   const state=await readState(record);
   if(!state.active)throw Error('IDEの利用を開始してください。');
   const existing=[...windows.values()].find(item=>item.owner===record&&item.kind==='viewer'&&item.viewerPath===path&&!item.window.isDestroyed());
   if(existing){focusWindow(existing.window);return{ok:true,reused:true};}
   if(quitting||record.window.isDestroyed())throw Error('IDEが終了しています。');
   await createWindow('viewer',`${record.url}#viewer=${encodeURIComponent(path)}`,undefined,record,sessionKey(state));
   return{ok:true};
  }catch(error){return{ok:false,error:error.message};}
 });
 await createWindow(kind,url);process.send?.({windowShown:true});
}).catch(error=>{console.error(error);app.quit();});
