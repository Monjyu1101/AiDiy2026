const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm');
const {縮小窓を作成,適用,準備script,cleanupScript}=require('../起動/縮小表示.cjs');
const {createWindowPins}=require('../../frontend_ide/デスクトップ/最前面ピン.cjs');
const from={x:10,y:20,width:800,height:600},target={x:10,y:20,width:384,height:200};
function dom(){
 const nodes=new Map(),decodes=[];
 const context=vm.createContext({document:{getElementById:id=>nodes.get(id),createElement:tag=>({style:{},decode:()=>new Promise(resolve=>decodes.push(resolve)),remove(){nodes.delete(this.id);}}),head:{append(node){nodes.set(node.id,node);}},body:{append(node){nodes.set(node.id,node);}}}});
 return {nodes,decodes,run:script=>vm.runInContext(script,context)};
}
test('shrink DOM cleanup invalidates a pending decode and does not reinsert hidden-app styles',async()=>{
 const d=dom(),pending=d.run(準備script('data:image/png;base64,test',from,target));
 assert.equal(d.nodes.size,0);d.run(cleanupScript);d.decodes.shift()();await pending;assert.equal(d.nodes.size,0);
});
test('late previous decode cannot replace a newer shrink layer and cleanup restores document',async()=>{
 const d=dom(),first=d.run(準備script('old',from,target)),second=d.run(準備script('new',from,target));
 d.decodes[1]();await second;const image=d.nodes.get('aidiy-size-image');assert.equal(image.src,'new');
 assert.match(d.nodes.get('aidiy-size-style').textContent,/visibility:hidden/);
 assert.match(d.nodes.get('aidiy-size-style').textContent,/background:transparent/);
 d.decodes[0]();await first;assert.equal(d.nodes.get('aidiy-size-image'),image);
 d.run(cleanupScript);d.run(cleanupScript);assert.equal(d.nodes.size,0);
});
test('geometry proxy binds native receivers and coalesces final native bounds exactly once',()=>{
 const calls=[],raw={isDestroyed(){assert.equal(this,raw);return false;},getNormalBounds(){assert.equal(this,raw);return {...from};},native(){assert.equal(this,raw);return 42;}};
 for(const method of ['unmaximize','setMinimumSize','setResizable','setMaximizable','setBounds'])raw[method]=function(...args){assert.equal(this,raw);calls.push([method,...args]);};
 const state={self:true,bounds:{...from},target,ops:new Map()},proxy=縮小窓を作成(raw,()=>state);
 assert.equal(proxy.native(),42);proxy.setBounds(target);proxy.setMinimumSize(384,180);proxy.setBounds({...target,height:180});
 assert.equal(calls.length,0);assert.equal(proxy.getBounds().height,180);assert.deepEqual(proxy.getMinimumSize(),[384,180]);
 適用(raw,state);適用(raw,state);assert.deepEqual(calls.map(c=>c[0]),['setMinimumSize','setBounds']);assert.equal(calls[1][1].height,180);
});
test('micro pin facade preserves native WeakMap identity while geometry uses a proxy',()=>{
 const raw={isDestroyed:()=>false,on(){},once(){},setAlwaysOnTop(value){assert.equal(this,raw);this.top=value;}};
 const pins=createWindowPins();pins.register(raw,{pinned:true});const proxy=縮小窓を作成(raw,()=>null);
 const facade={setLocked:(_window,value)=>pins.setLocked(raw,value),state:()=>pins.state(raw)};
 assert.equal(pins.state(proxy).pinned,false);facade.setLocked(proxy,true);assert.deepEqual(facade.state(proxy),{pinned:true,locked:true});
 facade.setLocked(proxy,false);assert.deepEqual(pins.state(raw),{pinned:true,locked:false});
});
test('post-flush ResizeObserver bounds updates reach native window instead of a spent queue',()=>{
 const raw={bounds:{...from},isDestroyed:()=>false,getBounds(){return {...this.bounds};},setBounds(bounds){this.bounds={...bounds};}};
 const state={self:true,bounds:{...from},target,ops:new Map()},proxy=縮小窓を作成(raw,()=>state);
 proxy.setBounds(target);適用(raw,state);
 proxy.setBounds({...target,height:220});assert.equal(raw.bounds.height,220);assert.equal(proxy.getBounds().height,220);
});
test('miniからmicroへ連続変更した時も予約済み通常寸法を保存する',()=>{
 const raw={getNormalBounds:()=>({x:10,y:20,width:384,height:180}),isDestroyed:()=>false};
 const state={self:true,bounds:{x:10,y:20,width:384,height:180},target:{x:10,y:20,width:104,height:104},ops:new Map()};
 const proxy=縮小窓を作成(raw,()=>state);
 proxy.setBounds(from);assert.deepEqual(proxy.getNormalBounds(),from);
 proxy.setBounds(state.target);assert.deepEqual(proxy.getBounds(),state.target);
});
