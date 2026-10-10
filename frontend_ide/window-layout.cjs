// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
// ElectronのworkArea（タスクバーを除いた論理座標）に収める。
const size=require('./host/scripts/window-size.cjs');
function windowBounds(kind,area,owner,slot=0){
 const margin=kind==='ide'?Math.min(32,Math.max(12,Math.round(Math.min(area.width,area.height)*.025))):8;
 const available={x:area.x+margin,y:area.y+margin,width:Math.max(1,area.width-margin*2),height:Math.max(1,area.height-margin*2)};
 if(kind==='ide')return available;
 const base=owner||available;
 const inset=owner?24:0;
 const width=Math.min(size.幅,available.width);
 const height=Math.min(size.会話高さ,available.height);
 const offset=owner&&kind==='code'?(slot%6)*24:0;
 const x=kind==='code'?base.x+inset+offset:base.x+base.width-width-inset;
 const y=base.y+(owner?36:0)+offset;
 return{x:Math.round(Math.max(available.x,Math.min(x,available.x+available.width-width))),y:Math.round(Math.max(available.y,Math.min(y,available.y+available.height-height))),width,height};
}
module.exports={windowBounds};
