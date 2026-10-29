// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026

// mainが所有するWeb本文の部分画像だけを使う。外部URL・SVG・任意HTMLは受け取らない。
export function browserGlassFrame(value){
 if(!value||typeof value.src!=='string'||!value.src.startsWith('data:image/png;base64,')||value.src.length>8*1024*1024)return null;
 const keys=['width','height','x','y','captureWidth','captureHeight'];
 if(!keys.every(key=>Number.isFinite(value[key])))return null;
 if(value.zoom!==undefined&&(!Number.isFinite(value.zoom)||value.zoom<.1||value.zoom>10))return null;
 if(value.width<1||value.width>1200||value.height<1||value.height>1000||value.x<0||value.y<0||value.captureWidth<1||value.captureHeight<1||value.x+value.captureWidth>value.width||value.y+value.captureHeight>value.height)return null;
 return{...Object.fromEntries(['src',...keys].map(key=>[key,value[key]])),zoom:value.zoom??1};
}

// 縁から内側へ滑らかに屈折する方向場。ノイズやぼかしは加えない。
// R=横、G=縦、B=中立。中央の画像は別途マスクで完全に取り除く。
export function browserGlassMap(length,axis,edge=8){
 const stop=Math.min(.49,edge/Math.max(1,length))*100;
 const colors=axis==='x'?['#ff8080','#808080','#008080']:['#80ff80','#808080','#800080'];
 const direction=axis==='x'?'x2="1" y2="0"':'x2="0" y2="1"';
 const svg=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1" preserveAspectRatio="none"><defs><linearGradient id="bend" x1="0" y1="0" ${direction}><stop stop-color="${colors[0]}"/><stop offset="${stop}%" stop-color="${colors[1]}"/><stop offset="${100-stop}%" stop-color="${colors[1]}"/><stop offset="100%" stop-color="${colors[2]}"/></linearGradient></defs><rect width="1" height="1" fill="url(#bend)"/></svg>`;
 return 'data:image/svg+xml;charset=utf-8,'+encodeURIComponent(svg);
}
