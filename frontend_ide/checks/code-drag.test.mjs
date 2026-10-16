// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import test from 'node:test';
import assert from 'node:assert/strict';
import {EventEmitter} from 'node:events';
import {createRequire} from 'node:module';
import {installCodeMove,codeMoveTarget} from '../src/コード/長押し窓移動.js';
const {createCodeDrag}=createRequire(import.meta.url)('../デスクトップ/code-drag.cjs');
const flush=async()=>{for(let i=0;i<10;i++)await Promise.resolve();};
function native(){
 const window=new EventEmitter(),webContents=new EventEmitter(),positions=[],timers=new Map();let id=0,cursor={x:-1900,y:-200};
 Object.assign(window,{webContents,isDestroyed:()=>false,isMaximized:()=>false,isFullScreen:()=>false,isFocused:()=>true,getBounds:()=>({x:-1800,y:-100,width:900,height:700}),setPosition:(...args)=>positions.push(args)});
 const record={window,kind:'code',revision:1};
 const api=createCodeDrag({trustedEvent:event=>event.record,screen:{getCursorScreenPoint:()=>({...cursor})},setTimer:fn=>{timers.set(++id,fn);return id;},clearTimer:id=>timers.delete(id)});
 return{api,record,window,webContents,positions,timers,event:{record},cursor:value=>cursor=value};
}
test('native: Code本人だけを同じDIP座標の差分で移動し、負座標・倍率境界を丸め誤差なく保つ',()=>{
 const f=native(),token=f.api.begin(f.event);assert.equal(typeof token,'string');f.cursor({x:-1875,y:-170});assert.equal(f.api.move(f.event,token),true);assert.deepEqual(f.positions,[[-1775,-70,false]]);
 f.cursor({x:30,y:40});f.api.move(f.event,token);assert.deepEqual(f.positions[1],[130,140,false]);
 assert.equal(f.api.move({record:{...f.record}},token),false);assert.equal(f.api.move(f.event,'fake'),false);
 f.api.end(f.event,token);assert.equal(f.timers.size,0);assert.equal(f.window.listenerCount('blur'),0);assert.equal(f.api.move(f.event,token),false);
 for(const kind of ['ide','live','term','viewer','panel-viewer','explorer']){f.record.kind=kind;assert.equal(f.api.begin(f.event),null);}
});
for(const reason of ['blur','closed','did-start-navigation','render-process-gone','lease','revision','maximized','fullscreen'])test(`native終了: ${reason}`,()=>{
 const f=native(),token=f.api.begin(f.event);
 if(reason==='lease')[...f.timers.values()][0]();else if(reason==='revision')f.record.revision++;else if(reason==='maximized')f.window.isMaximized=()=>true;else if(reason==='fullscreen')f.window.isFullScreen=()=>true;else(reason==='blur'||reason==='closed'?f.window:f.webContents).emit(reason);
 assert.equal(f.api.move(f.event,token),false);assert.equal(f.positions.length,0);assert.equal(f.timers.size,0);assert.equal(f.webContents.listenerCount('did-start-navigation'),0);
});
class Surface{
 listeners=new Map();children=[];style={setProperty:(key,value)=>{this.style[key]=value;}};classes=new Set();classList={add:name=>this.classes.add(name),remove:name=>this.classes.delete(name)};
 addEventListener(type,fn){const set=this.listeners.get(type)||new Set();set.add(fn);this.listeners.set(type,set);}
 removeEventListener(type,fn){this.listeners.get(type)?.delete(fn);}
 emit(type,extra={}){const event={type,button:0,buttons:1,isPrimary:true,pointerType:'mouse',pointerId:1,clientX:50,clientY:50,screenX:150,screenY:150,target:this,preventDefault(){this.prevented=true;},stopPropagation(){this.stopped=true;},...extra};for(const fn of this.listeners.get(type)||[])fn(event);return event;}
 closest(){return this.excluded?this:null;}getBoundingClientRect(){return{left:0,top:0,width:500,height:500};}setAttribute(){}append(child){child.parent=this;this.children.push(child);}remove(){this.parent.children=this.parent.children.filter(x=>x!==this);}setPointerCapture(){this.capture=true;}hasPointerCapture(){return this.capture;}releasePointerCapture(){this.capture=false;}
}
function browser(options={}){
 const win=new Surface(),doc=new Surface(),target=new Surface(),tasks=new Map(),intervals=new Map(),calls=[];let id=0,time=0,randoms=0,selections=0;
 doc.documentElement=new Surface();doc.body=new Surface();doc.createElement=()=>new Surface();doc.getSelection=()=>({removeAllRanges:()=>selections++});win.document=doc;win.getComputedStyle=()=>({webkitAppRegion:''});
 win.setTimeout=(fn,delay)=>{tasks.set(++id,{fn,at:time+delay});return id;};win.clearTimeout=id=>tasks.delete(id);win.setInterval=fn=>{intervals.set(++id,fn);return id;};win.clearInterval=id=>intervals.delete(id);win.requestAnimationFrame=fn=>win.setTimeout(fn,16);win.cancelAnimationFrame=win.clearTimeout;
 const api={beginCodeMove:async()=>{calls.push('begin');return 'token';},moveCode:async token=>{calls.push(['move',token]);return true;},endCodeMove:async token=>{calls.push(['end',token]);},...options.api};
 const dispose=installCodeMove({kind:'code',win,random:()=>{randoms++;return .5;},...options,api:options.api===null?{}:api});
 return{win,doc,target,tasks,intervals,calls,dispose,get randoms(){return randoms;},get selections(){return selections;},async advance(ms){time+=ms;for(const [id,t]of [...tasks])if(t.at<=time){tasks.delete(id);t.fn();}await flush();},emit:(type,extra={})=>doc.emit(type,{target,...extra})};
}
test('長押し: 1秒前は選択維持、成立後4矢印2ペア、移動は方向表示、解放で全解除',async()=>{
 const f=browser();const down=f.emit('pointerdown');await f.advance(999);assert.equal(down.prevented,undefined);assert.equal(f.selections,0);assert.equal(f.calls.length,0);
 await f.advance(1);assert.equal(f.selections,1);assert.equal(f.target.capture,true);assert.equal(f.doc.body.children[0].children.length,3);assert.equal(f.doc.body.children[0].children[0].children.length,2);assert.equal(f.randoms,4);
 const move=f.emit('pointermove',{screenX:170,clientX:70});assert.equal(move.prevented,true);assert.equal(f.doc.body.children[0].classes.has('moving'),true);await f.advance(16);assert.equal(f.calls.filter(x=>Array.isArray(x)&&x[0]==='move').length,1);assert.equal(f.randoms,4);
 f.emit('pointerup');assert.equal(f.doc.body.children.length,0);assert.equal(f.target.capture,false);assert.equal(f.intervals.size,0);assert.equal(f.tasks.size,0);assert.deepEqual(f.calls.at(-1),['end','token']);f.dispose();
});
test('通常ドラッグ・入力・ボタン・scrollbarは長押し移動にしない',async()=>{
 const f=browser();f.emit('pointerdown');const move=f.emit('pointermove',{screenX:157});await f.advance(1000);assert.equal(f.calls.length,0);assert.equal(move.prevented,undefined);
 f.target.excluded=true;f.emit('pointerdown');await f.advance(1000);assert.equal(f.calls.length,0);f.target.excluded=false;
 Object.assign(f.target,{offsetWidth:500,clientWidth:485,clientLeft:0,offsetHeight:500,clientHeight:500,clientTop:0});assert.equal(codeMoveTarget(f.target,490,50,f.win),false);assert.equal(codeMoveTarget(f.target,100,50,f.win),true);f.dispose();
});
for(const reason of ['pointercancel','lostpointercapture','blur','pagehide','escape','outside-release','dispose'])test(`長押し終了: ${reason}`,async()=>{
 const f=browser();f.emit('pointerdown');await f.advance(1000);
 if(reason==='dispose')f.dispose();else if(reason==='blur'||reason==='pagehide')f.win.emit(reason);else if(reason==='escape')f.emit('keydown',{key:'Escape'});else if(reason==='outside-release')f.emit('pointermove',{buttons:0});else f.emit(reason);
 assert.equal(f.doc.body.children.length,0);assert.equal(f.intervals.size,0);assert.equal(f.tasks.size,0);assert.equal(f.doc.documentElement.classes.size,0);f.dispose();assert.equal([...f.doc.listeners.values()].reduce((sum,set)=>sum+set.size,0),0);
});
test('遅い開始応答はキャンセル後に表示せずnativeも終了、Web/他アプリ/VSCodeには導入しない',async()=>{
 let resolve;const f=browser({api:{beginCodeMove:()=>new Promise(done=>{resolve=done;})}});f.emit('pointerdown');await f.advance(1000);f.emit('pointerup');resolve('late');await flush();assert.equal(f.doc.body.children.length,0);assert.deepEqual(f.calls,[['end','late']]);f.dispose();
 for(const options of [{kind:'ide'},{kind:'live'},{kind:'term'},{kind:'viewer'},{host:true},{api:null}]){const g=browser(options);g.emit('pointerdown');await g.advance(1000);assert.equal(g.calls.length,0);assert.equal(g.doc.listeners.size,0);g.dispose();}
});
test('native開始拒否・既存選択dragは選択を消さず、古いleaseが次の移動を終了しない',async()=>{
 const f=browser({api:{beginCodeMove:async()=>null}});f.emit('pointerdown');await f.advance(1000);assert.equal(f.selections,0);f.dispose();
 const g=browser();g.emit('pointerdown');const drag=g.emit('dragstart');await g.advance(1000);assert.equal(drag.prevented,undefined);assert.equal(g.calls.length,0);g.dispose();
 const n=native();n.api.begin(n.event);const old=[...n.timers.values()][0];const token=n.api.begin(n.event);old();assert.equal(n.api.move(n.event,token),true);n.api.end(n.event,token);
});
