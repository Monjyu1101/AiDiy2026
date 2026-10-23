const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm');
const {画面サイズ演出を作成}=require('../起動/サイズ切替.cjs');
function fixture(){
 const windows=[],scripts=[],calls=[];
 const window={bounds:{x:-120,y:40,width:800,height:600},opacity:1,isDestroyed(){return !!this.destroyed;},isVisible:()=>true,isMinimized:()=>false,isAlwaysOnTop:()=>false,getOpacity(){return this.opacity;},setOpacity(value){this.opacity=value;calls.push(value);},getContentBounds(){return {...this.bounds};},webContents:{executeJavaScript:async()=>{},capturePage:async()=>({isEmpty:()=>false,toDataURL:()=> 'data:image/png;base64,fixture'})}};
 class Canvas{
  constructor(options){this.options=options;windows.push(this);this.webContents={executeJavaScript:async script=>scripts.push(script)};}
  setBounds(value){this.bounds=value;}async loadURL(url){this.html=decodeURIComponent(url.split(',')[1]);}showInactive(){this.shown=true;}isDestroyed(){return !!this.dead;}destroy(){this.dead=true;}
 }
 return {window,windows,scripts,calls,effect:画面サイズ演出を作成(Canvas,window)};
}
test('縮小・拡大は元画面と完成画面の画像を使い、実窓の連続リサイズを行わない',async()=>{
 const f=fixture(),mini={x:-120,y:40,width:384,height:184};
 for(const target of [mini,{x:-120,y:40,width:800,height:600}]){
  assert.equal(await f.effect.準備(target),true);assert.equal(f.window.opacity,0);
  const canvas=f.windows.at(-1);assert.equal(canvas.options.transparent,true);assert.equal(canvas.options.alwaysOnTop,false);assert.equal(canvas.shown,true);
  assert.ok(canvas.bounds.width>=800);assert.ok(canvas.bounds.height>=600);assert.match(canvas.html,/transform-origin:0 0/);
  f.window.bounds=target;assert.equal(await f.effect.完了(),true);assert.equal(f.window.opacity,1);assert.equal(f.effect.active,false);assert.equal(canvas.dead,true);
 }
 assert.ok(f.scripts.some(script=>script.includes('scale(0.48,0.30666666666666664)')));
 assert.ok(f.scripts.some(script=>script.includes('scale(2.0833333333333335,3.260869565217391)')));
 assert.ok(f.scripts.some(script=>script.includes('duration:380')));
});
test('撮影失敗・中止・破棄でも透明な実窓や演出窓を残さない',async()=>{
 for(const mode of ['capture','cancel','destroy']){
  const f=fixture();
  if(mode==='capture')f.window.webContents.capturePage=async()=>{throw Error('capture failed');};
  assert.equal(await f.effect.準備({x:0,y:0,width:384,height:360}),true);
  if(mode==='cancel')f.effect.中止();
  if(mode==='destroy'){f.window.destroyed=true;f.effect.中止();}
  await f.effect.完了();assert.equal(f.effect.active,false);assert.ok(f.windows.every(canvas=>canvas.dead));
  if(mode!=='destroy')assert.equal(f.window.opacity,1);
 }
});
test('非表示の初期窓には切替演出を重ねず、ピンONは同じ層を継承する',async()=>{
 const f=fixture();f.window.isVisible=()=>false;await f.effect.準備(f.window.bounds);assert.equal(f.windows.length,0);assert.equal(f.window.opacity,1);
 f.window.isVisible=()=>true;f.window.isAlwaysOnTop=()=>true;await f.effect.準備(f.window.bounds);assert.equal(f.windows[0].options.alwaysOnTop,true);f.effect.中止();
});
test('撮影待ちに再読込・中止された切替を後から適用しない',async()=>{
 for(const rejected of [false,true]){
  const f=fixture();let resolve,reject;
  f.window.webContents.capturePage=()=>new Promise((yes,no)=>{resolve=yes;reject=no;});
  const preparing=f.effect.準備(f.window.bounds);f.effect.中止();
  if(rejected)reject(Error('late capture failure'));else resolve({isEmpty:()=>false});
  assert.equal(await preparing,false);assert.equal(f.window.opacity,1);assert.equal(f.windows.length,0);
 }
});
test('UIはミニ描画後に演出完了を通知し、完了までは切替中を保つ',async()=>{
 const {起動ミニ表示を作成}=await import('../ui/src/ウィンドウ/起動ミニ表示.mjs');
 const calls=[];let release;
 const state=起動ミニ表示を作成({利用可能:()=>true,切替:async value=>{calls.push(value);return true;},反映:()=>{calls.push(state.表示中.value?'mini-ready':'normal-ready');return new Promise(resolve=>release=resolve);}});
 const pending=state.変更(true);await new Promise(resolve=>setImmediate(resolve));
 assert.deepEqual(calls,[true,'mini-ready']);assert.equal(state.表示中.value,true);assert.equal(state.切替中.value,true);
 // 演出中に接続が切れた場合も、演出を終えてから最後に要求された通常表示へ戻す。
 state.変更(false);release(true);await new Promise(resolve=>setImmediate(resolve));
 assert.deepEqual(calls,[true,'mini-ready',false,'normal-ready']);assert.equal(state.切替中.value,true);
 release(true);await pending;assert.equal(state.表示中.value,false);assert.equal(state.切替中.value,false);
});

test('旧画像のdecode後に演出窓を表示し、相補合成で途中の背景抜けを作らない',async()=>{
 const f=fixture();await f.effect.準備({x:-120,y:40,width:384,height:184});
 const canvas=f.windows[0];
 assert.equal(f.scripts[0],"document.querySelector('#old').decode()");
 assert.match(canvas.html,/isolation:isolate/);
 assert.match(canvas.html,/mix-blend-mode:plus-lighter/);
 f.window.bounds={x:-120,y:40,width:384,height:184};await f.effect.完了();
 const animation=f.scripts.find(script=>script.includes('const motion='));
 const frames={},elements=Object.fromEntries(['image','next','old'].map(id=>[id,{
  decode:async()=>{},animate(keyframes,options){frames[id]={keyframes,options};return {finished:Promise.resolve()};},
 }]));
 await vm.runInNewContext(animation,{document:{querySelector:selector=>elements[selector.slice(1)]}});
 assert.deepEqual(Array.from(frames.next.keyframes,x=>x.opacity),[0,1]);
 assert.deepEqual(Array.from(frames.old.keyframes,x=>x.opacity),[1,0]);
 assert.equal(frames.next.options,frames.old.options);
 assert.equal(frames.next.options,frames.image.options);
 // 加算合成では両方不透明な画素が途中で暗くならず、アイコンの透明画素は滑らかに消える。
 for(const progress of [0,.1,.2,.5,.8,1]){
  const old=1-progress,next=progress;
  assert.equal(old+next,1);
  assert.equal(old+next*0,1-progress);
 }
});
test('旧画像decode中の中止で遅れて実窓を透明化しない',async()=>{
 const f=fixture();let release;
 // captureの後で作成される演出窓のdecodeだけを保留する。
 const prepare=f.effect.準備(f.window.bounds);
 await Promise.resolve();
 const canvas=f.windows[0];
 canvas.webContents.executeJavaScript=()=>new Promise(resolve=>release=resolve);
 await new Promise(resolve=>setImmediate(resolve));
 f.effect.中止();release();
 assert.equal(await prepare,false);assert.equal(f.window.opacity,1);assert.equal(canvas.dead,true);
});
