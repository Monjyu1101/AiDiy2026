const test=require('node:test'),assert=require('node:assert/strict');
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
