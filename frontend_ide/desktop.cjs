// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
const {app,BrowserWindow,WebContentsView,ipcMain,shell,clipboard,session,screen,dialog}=require('electron');
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
const {windowBounds,windowMinimumSize,allWindowBounds}=require('./デスクトップ/window-layout.cjs');
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
const {panelBounds,createPanelWindows}=require('./デスクトップ/panel-windows.cjs');
const panelWindows=createPanelWindows({windows,trustedEvent,readState,sessionKey:state=>sessionKey(state),screen,BrowserWindow,拡大表示,isQuitting:()=>quitting,isAllDisplays:record=>allDisplays.state(record).active,attachWindowMove});
const {createCodeDrag}=require('./デスクトップ/code-drag.cjs');
const codeDrag=createCodeDrag({trustedEvent,screen,resolvePanel:panelWindows.dragTarget,isCenterMove:record=>allDisplays.isActive(record)});
const {installNativeWindowMove}=require('./デスクトップ/長押し窓移動.cjs');
function attachWindowMove(record,contents){
 const stopMove=installNativeWindowMove({record,contents,drag:codeDrag,screen});
 const stopExit=allDisplays.attachExitKey(record,contents);
 return()=>{stopExit();stopMove();};
}
const {createAllDisplays}=require('./デスクトップ/全画面横断.cjs');
const {keepInFront}=require('./デスクトップ/前面維持.cjs');
const {createVRPanelPlacement}=require('./デスクトップ/VRパネル配置.cjs');
const vrPanels=createVRPanelPlacement({windows,screen,isActive:owner=>allDisplays.isActive(owner)});
const allDisplays=createAllDisplays({screen,trustedEvent,panels:vrPanels,syncChildren:owner=>{for(const child of windows.values())if(child.owner===owner)keepInFront(child.window);}});
const {createBrowserViews,browserFileTarget,browserOpenable,HOME}=require('./デスクトップ/ブラウザ.cjs');
const {validPreviewPath}=require('./デスクトップ/native-preview-actions.cjs');
let browserViews;
const browserBridges=new WeakMap();
const browserConnected=state=>state.active&&state.mode==='online'&&state.connected===true;
async function ensureBrowserBridge(owner){
 if(browserBridges.has(owner))return browserBridges.get(owner);
 const pending=(async()=>{
  const {createBrowserCDP}=require('./デスクトップ/ブラウザCDP.cjs');
  const bridge=await createBrowserCDP({directory:process.env.AIDIY_BROWSER_SESSIONS_DIR||join(__dirname,'../backend_tools/temp/_ide_browser_sessions'),
   canUse:async()=>!quitting&&!owner.window.isDestroyed()&&browserConnected(await readState(owner)),
   allowedURL:url=>browserViews.allowedURL(url),
   openPanel:async target=>{
    const state=await readState(owner);if(!browserConnected(state)||owner.window.isDestroyed())throw Error('tools接続中のみ起動できます。');
    const window=await createWindow('browser',owner.url+'#browser',undefined,owner,sessionKey(state),undefined,undefined,target);return windows.get(window.webContents);
   }});
  if(owner.window.isDestroyed()){bridge.close();throw Error('IDEの利用が終了しました。');}
  owner.window.once('closed',()=>bridge.close());return bridge;
 })();
 browserBridges.set(owner,pending);
 try{return await pending;}catch(error){browserBridges.delete(owner);throw error;}
}
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
  browserViews?.setAvailable(owner,browserConnected(state));
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
function selectedAllDisplay(owner,displayId){
 if(displayId===undefined)return null;
 if(!owner||!allDisplays.state(owner).active||!Number.isInteger(displayId))throw Error('VRモードの表示状態が変わりました。');
 const display=screen.getAllDisplays().find(display=>display.id===displayId);
 if(!display)throw Error('選んだディスプレイが見つかりません。');
 return display;
}
async function createWindow(kind,url,server,owner,linkKey,anchor,displayId,browserTarget){
 // ピン留めのビューアは #viewer=ファイル で開く。照合・遷移の判定は # より前の URL で行う。
 const [base,hash='']=url.split('#');
 const viewerPath=kind==='viewer'&&hash.startsWith('viewer=')?decodeURIComponent(hash.slice('viewer='.length)):'';
 const ownerBounds=owner?.window.getBounds();
 const area=(ownerBounds?screen.getDisplayMatching(ownerBounds):screen.getDisplayNearestPoint(screen.getCursorScreenPoint())).workArea;
 const used=new Set([...windows.values()].filter(item=>item.owner===owner&&item.kind===kind&&!item.window.isDestroyed()).map(item=>item.slot));
 const ownerRevision=owner?.revision;
 const placement=kind==='term'?await reserveTermSlot():null;
 if(quitting||owner&&(owner.window.isDestroyed()||owner.revision!==ownerRevision)){placement?.close();throw Error('起動元の利用が終了しました。');}
 let slot=placement?.slot||0;if(owner&&['code','viewer','browser'].includes(kind))while(used.has(slot))slot++;
 let bounds,displaySlot;
 try{
  const display=selectedAllDisplay(owner,displayId);
  if(display){displaySlot=0;const occupied=new Set([...windows.values()].filter(item=>item.owner===owner&&item.kind===kind&&item.displayId===displayId&&!item.window.isDestroyed()).map(item=>item.displaySlot));while(occupied.has(displaySlot))displaySlot++;}
  bounds=display?allWindowBounds(kind,display.workArea,displaySlot):(anchor&&owner?panelBounds(anchor,owner,screen):null)||windowBounds(kind,area,ownerBounds,slot);
 }catch(error){placement?.close();throw error;}
 const title=kind==='browser'?`AiDiy IDE / Browser ${slot+1}`:kind==='viewer'?`AiDiy IDE / Viewer - ${viewerPath.split('/').at(-1)}`:`AiDiy ${owner?'IDE / ':''}${kind==='ide'?'IDE':kind==='code'?`Code${owner?' '+(slot+1):''}`:kind==='term'?`Term${owner?' '+(slot+1):''}`:'Live'}`;
 let window;
 try{window=new BrowserWindow({title,...bounds,...windowMinimumSize(kind,bounds),...(owner?{parent:owner.window}:{}),show:false,frame:false,roundedCorners:false,backgroundColor:'#000',autoHideMenuBar:true,icon:join(__dirname,'public',`AiDiy_${['code','live','term'].includes(kind)?kind:'ide'}.png`),webPreferences:{preload:join(__dirname,'デスクトップ/preload.cjs'),sandbox:true,contextIsolation:true,nodeIntegration:false,autoplayPolicy:'no-user-gesture-required'}});}catch(error){placement?.close();throw error;}
 window.once('closed',()=>placement?.close());
 // autoplayPolicy: ビューアの「表示」で開いた HTML（ナレーション付きの動画ページなど）の音声を、クリックなしで再生できるようにする。
 // Windowsのフレームレス窓も、外枠の論理座標を明示してDPI差を補正する。
 window.setBounds(bounds);
 // IDEから開いたCode / Liveは、IDEや他アプリを操作中も手前に保つ。
 if(owner)keepInFront(window);
 const contents=window.webContents;
 contents.on('page-title-updated',event=>{event.preventDefault();window.setTitle(title);});
 // 窓番号は全体で一意、重ね位置は選択した画面ごとに数える。
 const record={window,kind,url:base,viewerPath,server,owner,linkKey,slot,displayId,displaySlot,revision:0,pending:new Map()};windows.set(contents,record);
 attachWindowMove(record);
 if(kind==='ide')allDisplays.register(record);
 window.on('focus',()=>{
  draftRouter.focused(record);
  // ALLの拡張・復帰やWindowsの透明窓の再配置後も、IDEへのクリックでパネルを隠さない。
  if(kind==='ide')for(const child of windows.values())if(child.owner===record)keepInFront(child.window);
 });
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
 window.once('closed',()=>{clearInterval(monitor);draftRouter.invalidate(record);nativePreviewActions.invalidate(record);closeChildren(record);windows.delete(contents);closeServer(server);if(kind==='viewer'&&owner&&!owner.window.isDestroyed())owner.window.webContents.send('development:viewer-closed',viewerPath);});
 contents.on('did-start-navigation',(_event,_url,isInPlace,isMainFrame)=>{if(isMainFrame){nativePreviewActions.invalidate(record);if(!isInPlace)draftRouter.invalidate(record);}});
 contents.on('render-process-gone',()=>{draftRouter.invalidate(record);nativePreviewActions.invalidate(record);});
 contents.on('will-navigate',(event,target)=>{if(target.split('#')[0]!==base)event.preventDefault();});
 contents.on('will-redirect',event=>event.preventDefault());contents.on('will-attach-webview',event=>event.preventDefault());
 contents.setWindowOpenHandler(details=>{const allowed=kind==='ide'?panelWindows.open(record,details):null;if(allowed)return allowed;if(/^https?:\/\//i.test(details.url))void shell.openExternal(details.url);return{action:'deny'};});
 contents.on('did-create-window',(child,details)=>panelWindows.created(record,child,details));
 try{
  if(kind==='browser'){
   browserViews??=createBrowserViews({WebContentsView,session,trustedEvent,projectRoot:process.env.AIDIY_DEVELOPMENT_PROJECT||process.cwd()});
   const bridge=await ensureBrowserBridge(owner);
   const current=await readState(owner);
   if(window.isDestroyed()||owner.window.isDestroyed()||owner.revision!==ownerRevision||sessionKey(current)!==linkKey||!browserConnected(current))throw Error('tools接続中のみBrowserを起動できます。');
   record.browserSession=bridge.name;const page=browserViews.attach(record,browserTarget);attachWindowMove(record,page);bridge.add(record,page);
  }
  await window.loadURL(url);
  if(!window.isDestroyed()){
   await contents.executeJavaScript("document.documentElement.classList.add('desktop-opening')");
   const reduced=await contents.executeJavaScript("matchMedia('(prefers-reduced-motion: reduce)').matches");
   if(reduced){window.show();window.focus();}
   if(reduced||await 拡大表示(BrowserWindow,window,{background:'#000'}))await contents.executeJavaScript("document.documentElement.classList.remove('desktop-opening');window.dispatchEvent(new Event('aidiy-window-shown'))");
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
  else if(action==='maximize'){if(!allDisplays.leave(record,{maximize:true})){if(record.window.isMaximized())record.window.unmaximize();else record.window.maximize();}}
  if(action==='title')return record.window.getTitle();
  if(action==='maximize'||action==='isMaximized')return record.window.isMaximized();
 });
 ipcMain.handle('development:all-displays',(event,action)=>allDisplays.handle(event,action));
 ipcMain.handle('development:browser-action',async(event,action,value)=>{
  const record=trustedEvent(event);
  if(record?.kind==='browser'&&!['bounds','state'].includes(action)){
   try{if(!browserConnected(await readState(record.owner)))return{ok:false,error:'tools接続中のみBrowserを操作できます。'};}catch{return{ok:false,error:'toolsの接続を確認できません。'};}
  }
  return browserViews?.action(event,action,value)||{ok:false,error:'ブラウザが起動していません。'};
 });
 ipcMain.handle('development:open-browser',async(event,path,displayId)=>{
  const source=trustedEvent(event),owner=source?.kind==='viewer'?source.owner:source;
  if(!owner||owner.kind!=='ide'||owner.owner||!['ide','viewer'].includes(source.kind))return{ok:false,error:'IDEから開いてください。'};
  if(path!==undefined&&(!validPreviewPath(path)||!await browserOpenable(path)))return{ok:false,error:'HTML / HTM・音声・動画ファイルを選んでください。'};
  const revision=owner.revision;
  try{
   if(displayId!==undefined&&source!==owner)throw Error('画面の選択はIDE本体から行ってください。');
   selectedAllDisplay(owner,displayId);
   const state=await readState(owner),key=sessionKey(state);
   const valid=()=>!quitting&&!owner.window.isDestroyed()&&!source.window.isDestroyed()&&trustedEvent(event)===source&&owner.revision===revision;
   if(!valid()||!key||!state.project?.path||(source!==owner&&source.linkKey!==key))throw Error('IDEの利用を開始してください。');
   if(!browserConnected(state))throw Error('tools接続中のみBrowserを起動できます。');
   let target=HOME;
   if(path!==undefined){
    target=await browserFileTarget(state.project.path,path);
   }
   const current=await readState(owner);
   if(!valid()||sessionKey(current)!==key||current.project?.path!==state.project.path||!browserConnected(current))throw Error('IDEの利用状態が変わりました。');
   await createWindow('browser',owner.url+'#browser',undefined,owner,key,undefined,displayId,target);
   return{ok:true};
  }catch(error){return{ok:false,error:error.message};}
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
 ipcMain.handle('development:open-app',async(event,type,displayId)=>{
  const source=trustedEvent(event),record=source?.kind==='viewer'?source.owner:source;
  if(!record||record.kind!=='ide'||!['ide','viewer'].includes(source.kind)||!['code','live','term'].includes(type))return{ok:false,error:'この画面からは開けません。'};
  // ピン留めからの明示起動も、元のIDEと同じ利用セッションだけに限定する。
  const revision=record.revision;let state;
  try{
   if(displayId!==undefined&&source!==record)throw Error('画面の選択はIDE本体から行ってください。');
   selectedAllDisplay(record,displayId);
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
    await createWindow(type,child.url,child,record,key,undefined,displayId);child=undefined;
    return{ok:true};
   }catch(error){closeServer(child);return{ok:false,error:error.message};}
  })();
  if(type==='live')record.pending.set(type,opening);
  try{return await opening;}finally{if(record.pending.get(type)===opening)record.pending.delete(type);}
 });
 ipcMain.handle('development:code-move-begin',event=>codeDrag.begin(event));
 ipcMain.handle('development:code-move',(event,token)=>codeDrag.move(event,token));
 ipcMain.handle('development:code-move-end',(event,token)=>codeDrag.end(event,token));
 ipcMain.handle('development:window-move-begin',(event,name)=>codeDrag.begin(event,name));
 ipcMain.handle('development:window-move',(event,token,name)=>codeDrag.move(event,token,name));
 ipcMain.handle('development:window-move-end',(event,token,name)=>codeDrag.end(event,token,name));
 ipcMain.handle('development:prepare-explorer',(event,rect,kind,previewRect)=>panelWindows.prepare(event,rect,kind,previewRect));
 ipcMain.handle('development:show-explorer',(event,name,reduced)=>panelWindows.show(event,name,reduced));
 ipcMain.handle('development:resize-routes',(event,name,height)=>panelWindows.resizeRoutes(event,name,height));
 ipcMain.handle('development:panel-action',(event,name,action)=>panelWindows.action(event,name,action));
 // ピン留め: IDEのプレビューを、同じIDEサーバーのファイルAPIを使う独立ウィンドウ（IDEの子ウィンドウ）で開く。
 // 同じファイルは既存の窓を前面へ出す。利用終了・セッション切り替えでは他の子ウィンドウと一緒に閉じる。
 ipcMain.handle('development:open-viewer',async(event,path,anchor)=>{
  const record=trustedEvent(event);
  if(!record||record.kind!=='ide'||typeof path!=='string'||!path||path.length>4096||path.includes('\0'))return{ok:false,error:'この画面からは開けません。'};
  const pendingKey='viewer:'+path;if(record.pending.has(pendingKey))return record.pending.get(pendingKey);
  const revision=record.revision;
  const opening=(async()=>{try{
   const state=await readState(record);
   if(record.revision!==revision||trustedEvent(event)!==record)throw Error('IDEの利用状態が変わりました。');
   if(!state.active)throw Error('IDEの利用を開始してください。');
   const existing=[...windows.values()].find(item=>item.owner===record&&item.kind==='viewer'&&item.viewerPath===path&&!item.window.isDestroyed());
   if(existing){focusWindow(existing.window);return{ok:true,reused:true};}
   if(quitting||record.window.isDestroyed())throw Error('IDEが終了しています。');
   await createWindow('viewer',`${record.url}#viewer=${encodeURIComponent(path)}`,undefined,record,sessionKey(state),anchor);
   return{ok:true};
  }catch(error){return{ok:false,error:error.message};}})();
  record.pending.set(pendingKey,opening);
  try{return await opening;}finally{if(record.pending.get(pendingKey)===opening)record.pending.delete(pendingKey);}
 });
 await createWindow(kind,url);process.send?.({windowShown:true});
}).catch(error=>{console.error(error);app.quit();});
