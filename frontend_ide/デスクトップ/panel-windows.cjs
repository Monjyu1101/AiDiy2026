// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
const {randomUUID}=require('node:crypto');

// getContentBounds / screen.workArea はDIP。CSS pxにzoomだけ掛け、OSのDPI倍率は掛けない。
function panelBounds(rect,owner,screen){
 if(!rect||!['left','top','width','height'].every(key=>Number.isFinite(rect[key]))||rect.width<=0||rect.height<=0)return null;
 const origin=owner.window.getContentBounds(),zoom=owner.window.webContents.getZoomFactor();
 const desired={x:Math.round(origin.x+rect.left*zoom),y:Math.round(origin.y+rect.top*zoom),width:Math.round(Math.max(300,rect.width)*zoom),height:Math.round(Math.max(320,rect.height)*zoom)};
 // 別画面へまたがるパネルは、そのパネルが最も重なるディスプレイを選ぶ。
 const area=screen.getDisplayMatching(desired).workArea,margin=8;
 const width=Math.min(desired.width,Math.max(1,area.width-margin*2)),height=Math.min(desired.height,Math.max(1,area.height-margin*2));
 return {x:Math.max(area.x+margin,Math.min(desired.x,area.x+area.width-width-margin)),y:Math.max(area.y+margin,Math.min(desired.y,area.y+area.height-height-margin)),width,height};
}

// Explorerは同じDOMを親から移すため、許可したabout:blankだけwindow.openで作る。
// 任意URL・別フレーム・別セッションからの要求は許可しない。
function createPanelWindows({windows,trustedEvent,readState,sessionKey,screen,BrowserWindow,拡大表示,isQuitting}){
 const requests=new WeakMap();
 async function prepare(event,rect){
  const owner=trustedEvent(event);if(!owner||owner.kind!=='ide')return{ok:false,error:'この画面からは開けません。'};
  const revision=owner.revision;
  try{
   const state=await readState(owner);
   if(!state.active||isQuitting()||owner.window.isDestroyed()||revision!==owner.revision||trustedEvent(event)!==owner)throw Error('IDEの利用状態が変わりました。');
   const bounds=panelBounds(rect,owner,screen);if(!bounds)throw Error('パネルの位置を取得できません。');
   const existing=[...windows.values()].find(item=>item.owner===owner&&item.kind==='explorer'&&!item.window.isDestroyed());
   if(existing)throw Error('Explorerはすでに別窓で開いています。');
   const name='aidiy-explorer-'+randomUUID();
   requests.set(owner,{name,bounds,key:sessionKey(state),revision,expires:Date.now()+10000});return{ok:true,name};
  }catch(error){return{ok:false,error:error.message};}
 }
 function open(owner,details){
  const request=requests.get(owner);
  if(!request||request.used||details.url!=='about:blank'||details.frameName!==request.name||Date.now()>request.expires||request.revision!==owner.revision||isQuitting())return null;
  request.used=true;
  return{action:'allow',overrideBrowserWindowOptions:{...request.bounds,show:false,frame:true,title:'AiDiy IDE / Explorer',backgroundColor:'#080c1a',autoHideMenuBar:true,webPreferences:{sandbox:true,contextIsolation:true,nodeIntegration:false}}};
 }
 function created(owner,window,details){
  const request=requests.get(owner);requests.delete(owner);
  if(!request?.used||request.name!==details.frameName||owner.window.isDestroyed()||owner.revision!==request.revision||isQuitting()){window.destroy();return;}
  window.setBounds(request.bounds);window.setAlwaysOnTop(true);
  const contents=window.webContents;
  const record={window,owner,kind:'explorer',url:'about:blank',linkKey:request.key,revision:0,pending:new Map(),name:request.name};windows.set(contents,record);
  contents.setWindowOpenHandler(()=>({action:'deny'}));
  contents.on('will-navigate',(event,url)=>{if(url!=='about:blank')event.preventDefault();});
  contents.on('will-redirect',event=>event.preventDefault());contents.on('will-attach-webview',event=>event.preventDefault());
  window.once('closed',()=>{clearTimeout(record.timeout);windows.delete(contents);});
  record.timeout=setTimeout(()=>{if(!record.shown&&!window.isDestroyed())window.destroy();},12000);record.timeout.unref?.();
 }
 async function show(event,name,reduced){
  const owner=trustedEvent(event),child=[...windows.values()].find(item=>item.kind==='explorer'&&item.owner===owner&&item.name===name&&!item.window.isDestroyed());
  if(!owner||owner.kind!=='ide'||!child||isQuitting())return{ok:false,error:'Explorerの利用が終了しました。'};
  try{if(child.linkKey!==sessionKey(await readState(owner))||owner.window.isDestroyed()||child.window.isDestroyed())return{ok:false,error:'IDEの利用状態が変わりました。'};}catch{return{ok:false,error:'IDEの利用状態を確認できません。'};}
  if(!child.shown){child.shown=true;clearTimeout(child.timeout);if(reduced===true){child.window.show();child.window.focus();}else await 拡大表示(BrowserWindow,child.window,{background:'#080c1a'});}
  return{ok:!child.window.isDestroyed()};
 }
 return{prepare,open,created,show};
}
module.exports={panelBounds,createPanelWindows};
