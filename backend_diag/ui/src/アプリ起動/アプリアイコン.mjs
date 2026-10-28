// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1". See LICENSE.
export const アプリアイコン=Object.freeze({chrome:'Chrome.svg',browser:'AiDiy.png',...Object.fromEntries(['avatar','task','team','ide','console','code','live','discord'].map(id=>[id,`AiDiy_${id}.${['task','team'].includes(id)?'svg':'png'}`])),});
