'use strict';
const {app,BrowserWindow,session,ipcMain,dialog,Menu,screen}=require('electron');
const path=require('node:path');
const {拡大表示}=require('../../frontend_ide/host/scripts/window-opening.cjs');
const {ミニ表示を作成,ミニ高さは有効}=require('./ミニ表示.cjs');
const {checkPort}=require('./ポート接続.cjs');
const {attachNativeWindowMove}=require('../../frontend_ide/デスクトップ/長押し窓移動.cjs');
const {createWindowPins}=require('../../frontend_ide/デスクトップ/最前面ピン.cjs');
const {起動状態を読む,終了確認を作成}=require('./終了確認.cjs');
const {アプリ名,Macメニューを設定}=require('./MacOS-Menu.cjs');
if(process.platform==='darwin')app.setName(アプリ名);
// 単体ファイル起動では既定の Electron プロファイルが Avatar と重なり、
// 相互に別インスタンスと誤認する。排他ロック・キャッシュを Diag 専用にする。
app.setPath('userData',path.join(app.getPath('appData'),'aidiy_diag'));
let window, failed=false,終了確認;
const pins=createWindowPins({onChanged:(target,state)=>{
  if(!target.isDestroyed()&&!target.webContents.isDestroyed())target.webContents.send('diag:pin-state',state);
}});
function fail(code) {
  if(failed)return;failed=true;
  // 例外本文や loadURL の URL は返さず、固定の原因コードだけを IPC へ送る。
  if(process.connected && process.send){
    const fallback=setTimeout(()=>app.exit(1),250);fallback.unref?.();
    try{process.send({type:'diag-failed',code},()=>{clearTimeout(fallback);app.exit(1);});}catch{app.exit(1);}
  }else app.exit(1);
}
function validUrl(value) {
  const url=new URL(value);
  if(url.protocol!=='http:' || url.hostname!=='127.0.0.1' || !url.port || url.username || url.password || url.search || !/^#token=[A-Za-z0-9_-]{43}$/.test(url.hash)) throw new Error('invalid URL');
  return url;
}
async function start(value) {
  let url;try{url=validUrl(value);}catch{fail('URL');return;}
  await app.whenReady();
  const initialMini=await checkPort(8095)===true;
  if(failed||!process.connected)return;
  // 非永続 session。preload は固定ウィンドウ操作だけ公開し、Node・任意IPCは公開しない。
  const isolated=session.fromPartition('aidiy-diag-'+process.pid,{cache:false});
  isolated.setPermissionRequestHandler((_wc,_permission,callback)=>callback(false));
  isolated.setPermissionCheckHandler(()=>false);
  isolated.webRequest.onBeforeRequest((details,callback)=>{
    try {const target=new URL(details.url);callback({cancel:target.origin!==url.origin});} catch {callback({cancel:true});}
  });
  window=new BrowserWindow({width:1160,height:820,title:'AiDiy Diag',icon:path.join(__dirname,'../static/AiDiy_diag.png'),show:false,frame:false,roundedCorners:false,backgroundColor:'#080b10',minWidth:420,minHeight:320,webPreferences:{session:isolated,preload:path.join(__dirname,'preload.cjs'),additionalArguments:initialMini?['--aidiy-diag-initial-mini']:[],nodeIntegration:false,contextIsolation:true,sandbox:true,webSecurity:true}});
  window.setMenuBarVisibility(false);
  pins.register(window);
  attachNativeWindowMove(window,screen,'diag');
  終了確認=終了確認を作成({window,状態取得:()=>起動状態を読む(url.href),確認:(parent,options)=>dialog.showMessageBox(parent,options)});
  Macメニューを設定({app,Menu,window,icon:path.join(__dirname,'../static/AiDiy_diag.png')});
  const mini=ミニ表示を作成(window,{screen});
  let firstLoad=true,opening=false,pendingMiniHeight;
  window.webContents.on('did-start-loading',()=>{
    // 初回の描画より先にミニ状態にし、初期表示の高さ通知を取りこぼさない。
    // 再読込時は従来どおり通常表示へ戻す。
    pendingMiniHeight=undefined;mini.set(firstLoad&&initialMini,{topLeft:true});firstLoad=false;
  });
  let selectingFolder=false;
  ipcMain.handle('diag:window',(event,action,value)=>{
    if(!window || window.isDestroyed() || event.sender!==window.webContents || event.senderFrame!==window.webContents.mainFrame)return false;
    if(action==='selectProject'){
      if(selectingFolder)return null;selectingFolder=true;
      return dialog.showOpenDialog(window,{title:'プロジェクトフォルダを選択',properties:['openDirectory']}).then(result=>result.canceled?null:result.filePaths[0]||null).finally(()=>{selectingFolder=false;});
    }
    if(action==='startMini'){
      if(value===false)pendingMiniHeight=undefined;
      return mini.set(value);
    }
    if(action==='resizeMini'){
      // 表示開始の拡大演出は撮影した寸法を保持し、最新の測定値だけを完了後に反映する。
      if(opening&&mini.active){if(!ミニ高さは有効(value))return false;pendingMiniHeight=value;return true;}
      return mini.resize(value);
    }
    if(action==='isMaximized')return window.isMaximized();
    if(action==='getPinState')return pins.state(window);
    if(action==='togglePin')return pins.toggle(window);
    if(action==='minimize')window.minimize();
    else if(action==='maximize'&&!mini.active){if(window.isMaximized())window.unmaximize();else window.maximize();}
    else if(action==='close')window.close();
    return false;
  });
  window.webContents.setWindowOpenHandler(()=>({action:'deny'}));
  window.webContents.on('will-navigate',event=>event.preventDefault());
  window.webContents.on('will-redirect',event=>event.preventDefault());
  window.webContents.on('will-attach-webview',event=>event.preventDefault());
  window.webContents.once('did-fail-load',(_event,_code,_description,_url,isMainFrame)=>{if(isMainFrame!==false)fail('LOAD');});
  window.webContents.once('render-process-gone',()=>fail('RENDERER'));
  try{await window.loadURL(url.href);}catch{fail('LOAD');return;}
  if(failed || window.isDestroyed())return;
  // Code / Live / Term / IDE と同じ共通演出。内容は拡大完了後にフェード表示する。
  await window.webContents.executeJavaScript("document.documentElement.classList.add('desktop-opening','desktop-window')");
  opening=true;
  const shown=await 拡大表示(BrowserWindow,window,{background:'#080b10'});opening=false;
  if(!shown || failed)return;
  if(pendingMiniHeight!==undefined){mini.resize(pendingMiniHeight);pendingMiniHeight=undefined;}
  await window.webContents.executeJavaScript("document.documentElement.classList.remove('desktop-opening')");
  if(!failed && !window.isDestroyed() && process.connected)process.send({type:'diag-shown'},error=>{if(error)fail('IPC');});
}
// 同じ作業環境の診断ウィンドウは1つだけ。2つ目は既存ウィンドウを前面に出し、起動元へ固定の通知だけ返して終了する。
function existing() {
  const done=()=>app.exit(0);
  if(process.connected && process.send){const fallback=setTimeout(done,250);fallback.unref?.();try{process.send({type:'diag-existing'},()=>{clearTimeout(fallback);done();});}catch{done();}}
  else done();
}
function primary() {
  app.on('second-instance',()=>{
    if(!window || window.isDestroyed())return;
    if(window.isMinimized())window.restore();
    window.show();window.focus();
  });
  // Electron on Windows replaces stdin with an empty EOF stream. Use the inherited Node IPC channel.
  const timer=setTimeout(()=>fail('TIMEOUT'),10000);
  process.once('message',message=>{
    clearTimeout(timer);
    if(message?.type!=='diag-start' || typeof message.url!=='string' || message.url.length>4096){fail('IPC');return;}
    start(message.url).catch(()=>fail('WINDOW'));
  });
  process.once('disconnect',()=>{clearTimeout(timer);終了確認?.許可();app.quit();});
  if(process.connected && process.send){
    try{process.send({type:'diag-ready'},error=>{if(error)fail('IPC');});}catch{fail('IPC');}
  }else{clearTimeout(timer);fail('IPC');}
  app.on('window-all-closed',()=>app.quit());
}
if(app.requestSingleInstanceLock())primary();else existing();
