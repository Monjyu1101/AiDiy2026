// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
const {randomUUID}=require('node:crypto');
// カーソルと窓位置を同じDIP座標で扱う。rendererから窓IDや座標は受け取らない。
function createCodeDrag({trustedEvent,screen,setTimer=setTimeout,clearTimer=clearTimeout}){
 const active=new Map();
 function stop(record){
  const drag=active.get(record);if(!drag)return;
  active.delete(record);clearTimer(drag.timer);
  for(const [target,event,listener]of drag.listeners)target.removeListener(event,listener);
 }
 function lease(record,drag){const generation=drag.lease=(drag.lease||0)+1;clearTimer(drag.timer);drag.timer=setTimer(()=>{if(active.get(record)===drag&&drag.lease===generation)stop(record);},2000);drag.timer?.unref?.();}
 function valid(event,token){
  const record=trustedEvent(event),drag=active.get(record);
  if(!record||record.kind!=='code'||!drag||drag.token!==token)return null;
  if(record.revision!==drag.revision||record.window.isDestroyed()||record.window.isMaximized()||record.window.isFullScreen()||!record.window.isFocused()){stop(record);return null;}
  return{record,drag};
 }
 return{
  begin(event){
   const record=trustedEvent(event);
   if(!record||record.kind!=='code'||record.window.isDestroyed()||record.window.isMaximized()||record.window.isFullScreen()||!record.window.isFocused())return null;
   stop(record);
   const drag={token:randomUUID(),revision:record.revision,cursor:screen.getCursorScreenPoint(),bounds:record.window.getBounds(),listeners:[]};
   active.set(record,drag);
   for(const [target,name]of [[record.window,'blur'],[record.window,'closed'],[record.window.webContents,'did-start-navigation'],[record.window.webContents,'render-process-gone']]){
    const listener=()=>stop(record);target.on(name,listener);drag.listeners.push([target,name,listener]);
   }
   lease(record,drag);return drag.token;
  },
  move(event,token){
   const current=valid(event,token);if(!current)return false;
   const {record,drag}=current,cursor=screen.getCursorScreenPoint();
   record.window.setPosition(Math.round(drag.bounds.x+cursor.x-drag.cursor.x),Math.round(drag.bounds.y+cursor.y-drag.cursor.y),false);
   lease(record,drag);return true;
  },
  end(event,token){const current=valid(event,token);if(current)stop(current.record);},
 };
}
module.exports={createCodeDrag};
