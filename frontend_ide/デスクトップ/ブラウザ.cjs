// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
const HOME='https://www.google.com/';
const {pathToFileURL,fileURLToPath}=require('node:url');
const {relative,isAbsolute,sep}=require('node:path');
const {previewFile}=require('./native-preview-actions.cjs');
function browserFileURL(root,path){return pathToFileURL(previewFile(root,path).full).href;}
// Browser で開けるのは HTML と音声・動画。
async function browserOpenable(path){
 const {MEDIA_PATTERN}=await import('../viewer/media-types.mjs');
 return /\.html?$/i.test(path)||MEDIA_PATTERN.test(path);
}
// AiDiy 保守中の登録HTML・public の音声・動画は正式なリンク、それ以外は file:// で開く。
async function browserFileTarget(root,path){
 const fileURL=browserFileURL(root,path);
 const [{registeredHTMLURL,publicMediaURL},{MEDIA_PATTERN}]=await Promise.all([import('../viewer/登録HTMLルート.mjs'),import('../viewer/media-types.mjs')]);
 if(MEDIA_PATTERN.test(path))return await publicMediaURL(root,path)||fileURL;
 return await registeredHTMLURL(root,path)||fileURL;
}
function browserURL(value){
 if(typeof value!=='string'||value.length>8192)throw Error('URLまたは検索語を入力してください。');
 const text=value.trim();if(!text)return HOME;if(text==='about:blank')return text;
 if(isAbsolute(text))return pathToFileURL(text).href;
 if(/^file:/i.test(text)){const url=new URL(text);fileURLToPath(url);return url.href;}
 if(/^[a-z][a-z\d+.-]*:/i.test(text)&&!/^https?:/i.test(text)&&! /^(localhost|[\w-]+(?:\.[\w-]+)+):\d+(?:[/?#]|$)/i.test(text))throw Error('http / https のURLを指定してください。');
 const address=/^https?:\/\//i.test(text)?text:/^(localhost(?::\d+)?|\[[\da-f:]+\]|[\w-]+(?:\.[\w-]+)+)(?::\d+)?(?:[/?#]|$)/i.test(text)&&! /\s/.test(text)?(/^(localhost|127\.)/i.test(text)?'http://':'https://')+text:HOME+'search?q='+encodeURIComponent(text);
 const url=new URL(address);if(!['http:','https:'].includes(url.protocol)||url.username||url.password)throw Error('このURLは開けません。');return url.href;
}
function createBrowserViews({WebContentsView,session,trustedEvent,projectRoot}){
 const entries=new Map(),blockedOrigins=new Set();
 const localFileAllowed=url=>{try{const path=relative(projectRoot,fileURLToPath(url)).split(sep).join('/');browserFileURL(projectRoot,path);return true;}catch{return false;}};
 const isolated=session.fromPartition('aidiy-browser');
 isolated.setPermissionRequestHandler((_contents,_permission,callback)=>callback(false));
 isolated.setPermissionCheckHandler(()=>false);
 isolated.webRequest.onBeforeRequest((details,callback)=>{
  let blocked=false;try{const url=new URL(details.url);blocked=blockedOrigins.has(url.origin)||(url.protocol==='file:'&&!localFileAllowed(url));}catch{}
  callback({cancel:blocked});
 });
 const allowed=url=>{if(url==='about:blank')return true;try{const parsed=new URL(url);if(parsed.protocol==='file:')return localFileAllowed(parsed);return ['http:','https:'].includes(parsed.protocol)&&!parsed.username&&!parsed.password&&!blockedOrigins.has(parsed.origin);}catch{return false;}};
 function attach(record,target=HOME,available=true){
  blockedOrigins.add(new URL(record.url).origin);
  const view=new WebContentsView({webPreferences:{session:isolated,sandbox:true,contextIsolation:true,nodeIntegration:false,nodeIntegrationInSubFrames:false,webSecurity:true}});
  const contents=view.webContents,entry={view,error:'',rect:null,run:0,available,pendingTarget:available?null:target};entries.set(record,entry);
  record.window.contentView.addChildView(view);view.setVisible(false);
  const snapshot=()=>({url:contents.getURL()||target,title:contents.getTitle(),session:record.browserSession,available:entry.available,loading:contents.isLoading(),back:contents.navigationHistory.canGoBack(),forward:contents.navigationHistory.canGoForward(),error:entry.available?entry.error:'toolsとの接続が切れています。再接続後に操作できます。'});
  const notify=()=>{if(!record.window.isDestroyed()&&!contents.isDestroyed())record.window.webContents.send('development:browser-changed',snapshot());};
  entry.snapshot=snapshot;entry.notify=notify;
  entry.navigate=async value=>{
   const url=browserURL(value);if(!entry.available||!allowed(url))throw Error('このURLはブラウザパネルでは開けません。');
   const run=++entry.run;entry.error='';
   // 読み込み完了を待たず窓を表示する。失敗は同じパネルの操作欄へ通知する。
   void contents.loadURL(url).catch(error=>{if(run===entry.run&&!contents.isDestroyed()&&error.code!=='ERR_ABORTED'){entry.error='ページを読み込めませんでした。URLや接続を確認して再読み込みしてください。';notify();}});
   notify();
  };
  const guard=(event,url)=>{if(!entry.available||!allowed(url||event.url)){event.preventDefault();entry.error='このリンクはブラウザパネルでは開けません。';notify();}};
  contents.on('will-navigate',guard);contents.on('will-redirect',guard);contents.on('will-frame-navigate',guard);
  contents.on('will-attach-webview',event=>event.preventDefault());
  contents.setWindowOpenHandler(({url})=>{void entry.navigate(url).catch(error=>{entry.error=error.message;notify();});return{action:'deny'};});
  for(const name of ['did-navigate','did-navigate-in-page','did-start-loading','did-stop-loading','page-title-updated'])contents.on(name,notify);
  contents.on('render-process-gone',()=>{entry.error='ページの表示が停止しました。再読み込みしてください。';notify();});
  function layout(){
   if(!entry.rect||record.window.isDestroyed())return;
   const zoom=record.window.webContents.getZoomFactor(),bounds=record.window.getContentBounds(),r=entry.rect;
   const x=Math.max(0,Math.round(r.left*zoom)),y=Math.max(0,Math.round(r.top*zoom));
   view.setBounds({x,y,width:Math.max(0,Math.min(Math.round(r.width*zoom),bounds.width-x)),height:Math.max(0,Math.min(Math.round(r.height*zoom),bounds.height-y))});
   view.setVisible(entry.available);
  }
  entry.layout=layout;record.window.on('resize',layout);
  record.window.once('closed',()=>{entries.delete(record);if(!contents.isDestroyed())contents.close({waitForBeforeUnload:false});});
  if(available)void entry.navigate(target).catch(error=>{entry.error=error.message;notify();});
  return contents;
 }
 async function action(event,name,value){
  const record=trustedEvent(event),entry=record?.kind==='browser'?entries.get(record):null;
  if(!entry)return{ok:false,error:'ブラウザパネルから操作してください。'};
  const contents=entry.view.webContents;
  try{
   if(name==='navigate')await entry.navigate(value);
   else if(name==='home')await entry.navigate(HOME);
   else if(name==='back'){if(contents.navigationHistory.canGoBack())contents.navigationHistory.goBack();}
   else if(name==='forward'){if(contents.navigationHistory.canGoForward())contents.navigationHistory.goForward();}
   else if(name==='reload'){entry.error='';contents.reload();}
   else if(name==='stop')contents.stop();
   else if(name==='bounds'){
    if(!value||!['left','top','width','height'].every(key=>Number.isFinite(value[key])&&value[key]>=0&&value[key]<100000))throw Error('表示領域が不正です。');
    entry.rect=value;entry.layout();
   }else if(name!=='state')throw Error('対応していない操作です。');
   return{ok:true,...entry.snapshot()};
  }catch(error){return{ok:false,error:error.message};}
 }
 function setAvailable(owner,available){for(const [record,entry]of entries)if((record===owner||record.owner===owner)&&entry.available!==available){entry.available=available;if(!available)entry.view.webContents.stop();else if(entry.pendingTarget!==null){const target=entry.pendingTarget;entry.pendingTarget=null;void entry.navigate(target).catch(error=>{entry.error=error.message;entry.notify();});}entry.layout();entry.notify();}}
 return{attach,action,setAvailable,allowedURL:allowed};
}
module.exports={HOME,browserURL,browserFileURL,browserFileTarget,browserOpenable,createBrowserViews};
