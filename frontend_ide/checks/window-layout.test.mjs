// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import test from 'node:test';
import assert from 'node:assert/strict';
import layout from '../window-layout.cjs';
const {windowBounds}=layout;
for(const area of [{x:0,y:0,width:1920,height:1040},{x:-1600,y:80,width:1600,height:900},{x:0,y:-900,width:1024,height:728},{x:0,y:0,width:640,height:480}]){
 test(`配置が画面内に収まり、IDEに余白を残す: ${JSON.stringify(area)}`,()=>{
  const ide=windowBounds('ide',area);
  assert.ok(ide.x>area.x&&ide.y>area.y);
  assert.ok(ide.width>area.width*.9&&ide.height>area.height*.9);
  for(const owner of [undefined,ide,{x:area.x-150,y:area.y-100,width:900,height:800}]){
   const code=windowBounds('code',area,owner),live=windowBounds('live',area,owner);
   assert.equal(code.width,480);assert.equal(live.width,480);
   assert.equal(code.height,Math.min(600,area.height-16));assert.equal(live.height,code.height);
   if(!owner){assert.equal(code.x,area.x+8);assert.equal(live.x,area.x+area.width-480-8);assert.equal(code.y,area.y+8);assert.equal(live.y,code.y);}
   for(const b of [ide,code,live]){
    assert.ok(b.x>=area.x&&b.y>=area.y);
    assert.ok(b.x+b.width<=area.x+area.width&&b.y+b.height<=area.y+area.height);
   }
   if(area.width>1000&&owner===ide){
    assert.equal(code.x,ide.x+24);assert.equal(live.x+live.width,ide.x+ide.width-24);
    assert.ok(code.x<live.x);assert.equal(code.y,live.y);assert.equal(code.height,live.height);
   }
  }
 });
}
