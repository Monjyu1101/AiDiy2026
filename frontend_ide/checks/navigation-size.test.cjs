const test=require('node:test');const assert=require('node:assert/strict');
const {windowBounds}=require('../デスクトップ/window-layout.cjs');
const {panelBounds}=require('../デスクトップ/panel-windows.cjs');
test('Navigator initial DIP and screen-edge clamp',()=>{
 for(const area of [{x:0,y:0,width:1920,height:1040},{x:-900,y:-50,width:900,height:700},{x:0,y:0,width:400,height:480}]){
  const expected=[Math.min(500,area.width-16),Math.min(600,area.height-16)];
  const standalone=windowBounds('navi',area);assert.deepEqual([standalone.width,standalone.height],expected);
  for(const zoom of [1,1.25,1.5,2]){
   const b=panelBounds({left:1900,top:900,width:400,height:700},{window:{getContentBounds:()=>area,webContents:{getZoomFactor:()=>zoom}}},{getDisplayMatching:()=>({workArea:area})},'panel-navigation');
   assert.deepEqual([b.width,b.height],expected);assert.ok(b.x>=area.x&&b.y>=area.y&&b.x+b.width<=area.x+area.width&&b.y+b.height<=area.y+area.height);
  }
 }
});
