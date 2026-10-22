// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1". See LICENSE.
'use strict';
// 40px正方形の対角線より広い中心間隔。向きを保って回転しても画像が重ならない。
const 最小半径=80,中心間隔=58,外周余白=38;
function 円周配置(count){
 if(!Number.isInteger(count)||count<0||count>32)return null;
 const 半径=Math.max(最小半径,count>1?Math.ceil(中心間隔/(2*Math.sin(Math.PI/count))):0);
 return {半径,幅:2*(半径+外周余白)};
}
module.exports={円周配置,最小半径,中心間隔};
