// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
const test=require('node:test');
const assert=require('node:assert/strict');
const {通常窓サイズを作成}=require('../起動/通常窓サイズ.cjs');
const {ミニ表示を作成}=require('../起動/ミニ表示.cjs');
function fixture(){
 let bounds={x:48,y:48,width:800,height:600},minimum=[420,320],maximizable=true;
 const raw={getBounds:()=>({...bounds}),getNormalBounds:()=>({...bounds}),setBounds:v=>{bounds={...v};},isMaximized:()=>false,isDestroyed:()=>false,getMinimumSize:()=>minimum,setMinimumSize:(...v)=>{minimum=v;},isMaximizable:()=>maximizable,setMaximizable:v=>{maximizable=v;},unmaximize(){throw Error('native maximize flags are unreliable in this fixture');}};
 const area={x:-1920,y:28,width:1920,height:1052},screen={getDisplayMatching:()=>({workArea:area}),getPrimaryDisplay:()=>({workArea:area})};
 return {raw,screen,area,window:通常窓サイズを作成(raw,screen,'win32')};
}
test('Windows透明窓のnative最大化フラグがfalseでも寸法と復元状態を保持する',()=>{
 const f=fixture(),original=f.window.getBounds();
 for(let i=0;i<3;i++){
  f.window.maximize();assert.equal(f.window.isMaximized(),true);assert.deepEqual(f.raw.getBounds(),f.area);assert.deepEqual(f.window.getNormalBounds(),original);
  f.window.maximize();f.window.unmaximize();assert.equal(f.window.isMaximized(),false);assert.deepEqual(f.raw.getBounds(),original);
 }
});
test('最大化からミニへ切替後は現在の左肩で元の通常寸法へ戻る',()=>{
 const f=fixture(),mini=ミニ表示を作成(f.window,{screen:f.screen});f.window.maximize();mini.set(true);mini.set(false);
 assert.equal(f.window.isMaximized(),false);assert.deepEqual(f.window.getBounds(),{x:f.area.x,y:f.area.y,width:800,height:600});
});
test('Windows以外では既存のnative窓をそのまま使用する',()=>{
 const f=fixture();for(const platform of ['linux','darwin'])assert.equal(通常窓サイズを作成(f.raw,f.screen,platform),f.raw);
});
