// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
const controls='input,textarea,select,button,a,summary,[contenteditable]:not([contenteditable="false"]),[role="button"],[role="slider"],[role="textbox"],[draggable="true"],.scrollbar,.slider,.monaco-editor';
export function codeMoveTarget(target,x,y,win){
 if(!target?.closest||target.closest(controls))return false;
 for(let node=target;node&&node!==win.document.documentElement;node=node.parentElement){
  if(win.getComputedStyle(node).webkitAppRegion==='drag')return false;
  const rect=node.getBoundingClientRect();
  if(node.offsetWidth>node.clientWidth+2&&(x>=rect.left+node.clientLeft+node.clientWidth||x<rect.left+node.clientLeft))return false;
  if(node.offsetHeight>node.clientHeight+2&&y>=rect.top+node.clientTop+node.clientHeight)return false;
 }
 return true;
}
export function installCodeMove({kind,host=false,win=window,api=win.aidiyWindow,random=Math.random}){
 if(kind!=='code'||host||!api?.beginCodeMove||!api?.moveCode||!api?.endCodeMove)return()=>{};
 const doc=win.document,listeners=[];let current=null,disposed=false,sequence=0;
 const listen=(target,type,fn)=>{target.addEventListener(type,fn,true);listeners.push(()=>target.removeEventListener(type,fn,true));};
 const finish=()=>{
  sequence++;const drag=current;current=null;if(!drag)return;
  win.clearTimeout(drag.timer);win.clearInterval(drag.heartbeat);win.cancelAnimationFrame(drag.frame);
  drag.indicator?.remove();if(drag.active)doc.documentElement.classList.remove('code-window-moving');
  try{if(drag.target.hasPointerCapture?.(drag.id))drag.target.releasePointerCapture(drag.id);}catch{}
  if(drag.token)void Promise.resolve(api.endCodeMove(drag.token)).catch(()=>{});
 };
 const send=async drag=>{
  if(current!==drag||!drag.token||drag.sending)return;
  drag.sending=true;
  try{if(!await api.moveCode(drag.token)&&current===drag)finish();}catch{if(current===drag)finish();}
  finally{drag.sending=false;}
 };
 const place=(el,x,y)=>{el.style.left=`${Math.max(34,Math.min(x,(win.innerWidth||x+34)-34))}px`;el.style.top=`${Math.max(34,Math.min(y,(win.innerHeight||y+34)-34))}px`;};
 function indicator(drag){
  const el=doc.createElement('div');el.className='code-move-indicator';el.setAttribute('aria-hidden','true');
  for(let pair=0;pair<2;pair++){
   const orbit=doc.createElement('span');orbit.className='code-move-pair';
   orbit.style.setProperty('--move-duration',`${5+pair*2+random()}s`);
   orbit.style.setProperty('--move-phase',`${-pair*3-random()*2}s`);
   orbit.style.animationDirection=pair?'reverse':'normal';
   for(let n=0;n<2;n++){const arrow=doc.createElement('i');arrow.textContent='↑';arrow.style.setProperty('--arrow-angle',`${n*180+pair*90}deg`);orbit.append(arrow);}
   el.append(orbit);
  }
  const direction=doc.createElement('span');direction.className='code-move-direction';direction.textContent='↑';el.append(direction);
  place(el,drag.x,drag.y);doc.body.append(el);drag.indicator=el;
 }
 async function activate(drag,run){
  if(current!==drag||disposed||sequence!==run)return;
  try{
   drag.target.setPointerCapture(drag.id);
   const token=await api.beginCodeMove();
   if(current!==drag||disposed||sequence!==run){if(token)await api.endCodeMove(token);return;}
   if(!token){finish();return;}
   // nativeが拒否した場合は選択を維持する。成功後だけ通常の選択/dragを止める。
   drag.token=token;drag.active=true;doc.documentElement.classList.add('code-window-moving');doc.getSelection()?.removeAllRanges();
   indicator(drag);drag.heartbeat=win.setInterval(()=>void send(drag),250);
  }catch{if(current===drag)finish();}
 }
 listen(doc,'pointerdown',event=>{
  if(current)finish();
  if(event.button!==0||event.isPrimary===false||event.pointerType!=='mouse'||!codeMoveTarget(event.target,event.clientX,event.clientY,win))return;
  const drag={id:event.pointerId,target:event.target,x:event.clientX,y:event.clientY,sx:event.screenX,sy:event.screenY,lastX:event.screenX,lastY:event.screenY};
  current=drag;const run=++sequence;drag.timer=win.setTimeout(()=>void activate(drag,run),1000);
 });
 listen(doc,'pointermove',event=>{
  const drag=current;if(!drag||event.pointerId!==drag.id)return;
  if(!(event.buttons&1)){finish();return;}
  if(!drag.active){if(Math.hypot(event.screenX-drag.sx,event.screenY-drag.sy)>6)finish();return;}
  event.preventDefault();event.stopPropagation();
  const dx=event.screenX-drag.lastX,dy=event.screenY-drag.lastY;drag.lastX=event.screenX;drag.lastY=event.screenY;
  if(drag.indicator){
   place(drag.indicator,event.clientX,event.clientY);
   if(Math.hypot(dx,dy)>0.5){drag.indicator.classList.add('moving');drag.indicator.style.setProperty('--move-angle',`${Math.atan2(dy,dx)*180/Math.PI+90}deg`);}
  }
  if(!drag.frame)drag.frame=win.requestAnimationFrame(()=>{drag.frame=0;void send(drag);});
 });
 for(const type of ['pointerup','pointercancel','lostpointercapture'])listen(doc,type,event=>{if(current&&event.pointerId===current.id)finish();});
 listen(doc,'dragstart',event=>{if(current?.active){event.preventDefault();event.stopPropagation();}else finish();});
 for(const type of ['selectstart','click','contextmenu'])listen(doc,type,event=>{if(current?.active){event.preventDefault();event.stopPropagation();}});
 listen(doc,'keydown',event=>{if(event.key==='Escape')finish();});
 listen(doc,'wheel',()=>{if(current&&!current.active)finish();});
 listen(win,'blur',finish);listen(win,'pagehide',finish);
 listen(doc,'visibilitychange',()=>{if(doc.hidden)finish();});
 return()=>{if(disposed)return;disposed=true;finish();for(const remove of listeners)remove();};
}
