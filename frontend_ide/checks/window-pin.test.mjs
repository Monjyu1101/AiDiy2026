// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import test from 'node:test';
import assert from 'node:assert/strict';
import {EventEmitter} from 'node:events';
import native from '../デスクトップ/最前面ピン.cjs';
import allNative from '../デスクトップ/全画面横断.cjs';
const {createWindowPins}=native;
function windowFixture(name='window',order=[]){
 const window=new EventEmitter();
 Object.assign(window,{
  isDestroyed:()=>!!window.destroyed,isFocused:()=>!!window.focused,
  setAlwaysOnTop(value,level){this.top=value;this.level=level;this.calls.push([value,level]);},
  moveTop(){order.push(name);},calls:[],
  setParentWindow(value){this.parent?.children.delete(this);this.parent=value;value?.children.add(this);},getParentWindow(){return this.parent||null;},isAlwaysOnTop(){return !!this.top;},children:new Set(),
  focus(){this.focused=true;this.emit('focus');},
  destroy(){this.destroyed=true;this.emit('closed');},
 });
 return window;
}
test('通常起動OFF、IDE由来ON、登録は一度だけで明示選択を消さない',()=>{
 const changed=[],pins=createWindowPins({onChanged:(_window,state)=>changed.push(state)});
 const normal=windowFixture(),child=windowFixture();
 assert.deepEqual(pins.register(normal),{pinned:false,locked:false});assert.equal(normal.top,false);
 assert.deepEqual(pins.register(child,{pinned:true}),{pinned:true,locked:false});assert.equal(child.top,true);assert.equal(child.level,'floating');
 pins.toggle(child);pins.register(child,{pinned:true});assert.equal(child.top,false);
 assert.equal(child.listenerCount('focus'),1);assert.equal(changed.length,3);
});
test('VRはユーザー選択を変更せず強制ON、ロック中の連打を拒否、終了で元状態へ復元',()=>{
 for(const initial of [false,true]){
  const pins=createWindowPins(),window=windowFixture();pins.register(window,{pinned:initial});
  assert.deepEqual(pins.setLocked(window,true),{pinned:true,locked:true});
  const calls=window.calls.length;
  for(let i=0;i<10;i++){assert.equal(pins.toggle(window).pinned,true);pins.setLocked(window,true);}
  assert.equal(window.calls.length,calls,'監視・VR領域変更で再固定しない');
  assert.deepEqual(pins.setLocked(window,false),{pinned:initial,locked:false});
  assert.equal(pins.toggle(window).pinned,!initial);
 }
 const pins=createWindowPins(),during=windowFixture();pins.register(during,{pinned:true,locked:true});
 assert.deepEqual(pins.setLocked(during,false),{pinned:true,locked:false},'VR中にIDEから起動した窓は通常のIDE由来ONへ戻る');
});
test('IDE由来の全モジュールはON中だけIDEのOS子窓となり、OFF・VR復帰・購読解除で外れる',()=>{
 for(const kind of ['term','code','live','viewer','browser','explorer','compare','routes']){
  const pins=createWindowPins(),ide=windowFixture('ide'),child=windowFixture(kind);
  pins.register(ide);pins.register(child,{owner:ide,pinned:true});assert.equal(child.getParentWindow(),ide,kind);
  ide.focus();assert.equal(child.getParentWindow(),ide,'IDE選択でも所属が外れない');
  pins.toggle(ide);pins.toggle(ide);assert.equal(pins.state(child).pinned,true);assert.equal(child.getParentWindow(),ide,'本体のON/OFFでもIDEより手前の関係を維持する');
  pins.toggle(child);assert.equal(child.getParentWindow(),null);assert.equal(child.top,false);
  pins.setLocked(child,true);assert.equal(child.getParentWindow(),ide);assert.equal(child.top,true);
  pins.setLocked(child,false);assert.equal(child.getParentWindow(),null);assert.equal(child.top,false);
  pins.toggle(child);assert.equal(child.getParentWindow(),ide);pins.unregister(child);assert.equal(child.getParentWindow(),null);
 }
});
test('別アプリ相当の管理器でも同じ層、選択されたON窓だけ持上げ、OFF・blurは何もしない',()=>{
 const order=[],a=createWindowPins(),b=createWindowPins(),one=windowFixture('one',order),two=windowFixture('two',order),off=windowFixture('off',order);
 a.register(one,{pinned:true});b.register(two,{pinned:true});a.register(off);
 one.focus();two.focus();off.focus();one.emit('blur');one.focus();
 assert.deepEqual(order,['one','two','one']);assert.equal(one.level,two.level);
 a.toggle(one);two.focus();one.focus();assert.deepEqual(order,['one','two','one','two']);
 const calls=two.calls.length;for(let i=0;i<10;i++)two.focus();assert.equal(two.calls.length,calls,'選択のたびにtopmost属性を再設定しない');
});
test('moveTopがfocusを再入してもフォーカス奪い合いを起こさず、破棄・解除で購読を回収',()=>{
 const pins=createWindowPins(),window=windowFixture();let count=0;
 window.moveTop=()=>{count++;window.emit('focus');};pins.register(window,{pinned:true});window.focus();assert.equal(count,1);
 window.destroy();assert.equal(window.listenerCount('focus'),0);assert.equal(window.listenerCount('closed'),0);
 assert.deepEqual(pins.toggle(window),{pinned:false,locked:false});pins.setLocked(window,true);assert.equal(count,1);
 const removed=windowFixture();pins.register(removed);pins.unregister(removed);assert.equal(removed.listenerCount('focus'),0);
});
test('実VR管理器のF11・最大化解除・画面再構成でも各所属窓だけロックして復元',()=>{
 const pins=createWindowPins(),screen=new EventEmitter(),rect={x:0,y:0,width:1920,height:1080};
 Object.assign(screen,{getAllDisplays:()=>[{id:1,bounds:rect,workArea:rect}],getPrimaryDisplay:()=>({workArea:rect}),getDisplayMatching:()=>({workArea:rect})});
 const owner={kind:'ide',window:windowFixture()},foreign={kind:'ide',window:windowFixture()},child={kind:'code',owner,window:windowFixture()};
 const records=[owner,child,foreign];
 const window=owner.window;window.bounds={x:10,y:10,width:900,height:700};
 Object.assign(window,{webContents:new EventEmitter(),getBounds:()=>window.bounds,getNormalBounds:()=>window.bounds,setBounds:value=>window.bounds=value,
  isMinimized:()=>false,isMaximized:()=>!!window.maximized,maximize(){window.maximized=true;},unmaximize(){window.maximized=false;},
  isMovable:()=>true,isResizable:()=>true,setMovable(){},setResizable(){}});
 window.webContents.send=()=>{};
 const all=allNative.createAllDisplays({screen,trustedEvent:event=>event.record,syncChildren:owner=>{
  for(const record of records)if(record===owner||record.owner===owner)pins.setLocked(record.window,all.isActive(owner));
 }});
 all.register(owner);for(const record of records)pins.register(record.window);
 const toggle=()=>all.handle({record:owner},'toggle');
 toggle();for(const record of [owner,child])assert.equal(pins.state(record.window).locked,true);
 assert.equal(pins.state(foreign.window).pinned,false);
 const calls=child.window.calls.length;screen.emit('display-metrics-changed');assert.equal(child.window.calls.length,calls);
 const contents=new EventEmitter();all.attachExitKey(child,contents);
 contents.emit('before-input-event',{preventDefault(){}},{type:'keyDown',key:'F11'});
 for(const record of [owner,child])assert.deepEqual(pins.state(record.window),{pinned:false,locked:false});
 toggle();assert.equal(all.leave(owner,{maximize:true}),true);assert.equal(pins.state(child.window).locked,false);
 window.destroy();contents.emit('destroyed');assert.equal(screen.listenerCount('display-metrics-changed'),0);
});
