// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026

// 各階層では入口（中央）から直下のフォルダ・ファイルをAIの順番で結ぶ。
// 関係のない階層へは線を出さない。別枝への経路はそれぞれの親フォルダに現れる。
export function aiRouteTargets(route,trail,world) {
  const prefix=trail.length?trail.join('/')+'/':'';
  const targets=[];
  for(const path of route) {
    if(!path.startsWith(prefix))continue;
    const rest=path.slice(prefix.length),slash=rest.indexOf('/');
    const target=slash<0?world.byPath.get(path):world.galaxies.find(g=>g.path===prefix+rest.slice(0,slash));
    if(target&&targets.at(-1)!==target)targets.push(target);
  }
  return targets.length?[{x:0,y:0,z:0},...targets]:[];
}
