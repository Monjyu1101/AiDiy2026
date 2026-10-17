// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
const assert=require('node:assert/strict');
const {screen}=require('electron');
const {mkdirSync,writeFileSync}=require('node:fs');
const {join}=require('node:path');
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function until(fn,label){for(let i=0;i<160;i++){if(await fn())return;await sleep(50);}throw Error('長押し確認: '+label);}
async function point(contents,selector){return contents.executeJavaScript(`(()=>{const r=document.querySelector(${JSON.stringify(selector)}).getBoundingClientRect();return{x:Math.round(r.x+Math.min(30,r.width/2)),y:Math.round(r.y+r.height/2)}})()`);}
async function holdMove(window,contents,selector,label,ending='release'){
 const focus=window.isFocused,cursorRead=screen.getCursorScreenPoint;let cursor=cursorRead();
 window.isFocused=()=>true;screen.getCursorScreenPoint=()=>cursor;
 try{
  await until(()=>contents.executeJavaScript(`!!document.querySelector(${JSON.stringify(selector)})`),label+'対象');
  const cssPoint=await point(contents,selector),zoom=contents.getZoomFactor(),p={x:Math.round(cssPoint.x*zoom),y:Math.round(cssPoint.y*zoom)},before=window.getBounds(),url=contents.getURL();
  await contents.executeJavaScript(`window.moveInputs=[];window.moveInput=e=>moveInputs.push(e.type);for(const type of ['pointerdown','mousedown','pointerup','mouseup','click'])document.addEventListener(type,moveInput,true)`);
  contents.sendInputEvent({type:'mouseDown',...p,button:'left',clickCount:1});
  await sleep(400);assert.deepEqual(await contents.executeJavaScript('moveInputs'),[],label+'押下で選択しない');
  assert.deepEqual(window.getBounds(),before,label+'0.5秒未満は移動しない');
  await until(()=>contents.executeJavaScript(`!!document.querySelector('[data-aidiy-window-move]:popover-open')`),label+'移動表示');
  assert.equal(await contents.executeJavaScript(`(()=>{const node=document.elementFromPoint(${cssPoint.x},${cssPoint.y});return node.hasAttribute('data-aidiy-window-move')&&getComputedStyle(node).cursor==='move';})()`),true,label+'押している場所を移動カーソルで覆う');
  const marker=await contents.executeJavaScript(`(()=>{const r=document.querySelector('[data-aidiy-move-marker]').getBoundingClientRect();return{x:r.x,y:r.y,width:r.width,height:r.height}})()`);
  assert.ok(Math.abs(marker.width-28)<.01&&Math.abs(marker.height-28)<.01);assert.ok(marker.x>=0&&marker.y>=0);
  const directory=join(__dirname,'../../temp/window-move-check/markers');mkdirSync(directory,{recursive:true});const markerShot=join(directory,label.replace(/[^a-zA-Z0-9一-龠ぁ-んァ-ン]/g,'_')+'.png');writeFileSync(markerShot,(await contents.capturePage()).toPNG());
  for(let i=0;i<4;i++){cursor={x:cursor.x+12,y:cursor.y+7};contents.sendInputEvent({type:'mouseMove',...p,button:'left',modifiers:['leftButtonDown']});await sleep(35);}
  await until(()=>Math.abs(window.getBounds().x-before.x-48)<=2,label+'窓移動');
  if(ending==='escape'){contents.sendInputEvent({type:'keyDown',keyCode:'Escape'});contents.sendInputEvent({type:'keyUp',keyCode:'Escape'});}
  if(ending==='blur')window.emit('blur');
  if(ending!=='release')await until(()=>contents.executeJavaScript(`!document.querySelector('[data-aidiy-window-move]')`),label+'取消で表示解除');
  contents.sendInputEvent({type:'mouseUp',...p,button:'left',clickCount:1});
  await until(()=>contents.executeJavaScript(`!document.querySelector('[data-aidiy-window-move]')`),label+'移動表示解除');
  assert.deepEqual(await contents.executeJavaScript('moveInputs'),[],label+'移動後の選択・リンクを抑止');assert.equal(contents.getURL(),url);
  const after=window.getBounds();assert.ok(Math.abs(before.width-after.width)<=1&&Math.abs(before.height-after.height)<=1,label+'サイズ維持');
  await contents.executeJavaScript(`for(const type of ['pointerdown','mousedown','pointerup','mouseup','click'])document.removeEventListener(type,moveInput,true)`);
  return{label,before,after,noSelectionOnRelease:true,markerShot,ending};
 }finally{window.isFocused=focus;screen.getCursorScreenPoint=cursorRead;}
}
async function shortClick(contents,selector){const p=await point(contents,selector);contents.sendInputEvent({type:'mouseDown',...p,button:'left',clickCount:1});await sleep(80);contents.sendInputEvent({type:'mouseUp',...p,button:'left',clickCount:1});await sleep(80);}
module.exports={holdMove,shortClick,until,sleep};
