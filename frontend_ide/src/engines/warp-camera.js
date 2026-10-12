// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026

const forward = ({yaw,pitch}) => ({x:Math.sin(yaw)*Math.cos(pitch),y:Math.sin(pitch),z:Math.cos(yaw)*Math.cos(pitch)});
const nearAngle = (angle,reference) => reference+Math.atan2(Math.sin(angle-reference),Math.cos(angle-reference));

/** 注視点と距離で表しているカメラの、実際の宇宙内の位置。 */
export function cameraPosition(view) {
  const direction=forward(view);
  return {x:view.tx-direction.x*view.dist,y:view.ty-direction.y*view.dist,z:view.tz-direction.z*view.dist};
}

/** 実座標と船首方向から、既存描画用の注視点表現を作る。 */
export function cameraAt(position, view) {
  const direction = forward(view);
  return {...view, tx:position.x+direction.x*view.dist, ty:position.y+direction.y*view.dist, tz:position.z+direction.z*view.dist};
}

/** 手動ドラッグの例外: 星を軸に船体と視線を一緒に回す。自動航行の旋回には使わない。 */
export function orbitAround(view, pivot, yaw, pitch) {
  const eye=cameraPosition(view), dx=eye.x-pivot.x,dy=eye.y-pivot.y,dz=eye.z-pivot.z;
  const x=dx*Math.cos(yaw)+dz*Math.sin(yaw),z=-dx*Math.sin(yaw)+dz*Math.cos(yaw);
  const next={...view,yaw:view.yaw+yaw,pitch:view.pitch+pitch};
  const right=x*Math.cos(next.yaw)-z*Math.sin(next.yaw),ahead=x*Math.sin(next.yaw)+z*Math.cos(next.yaw);
  const up=dy*Math.cos(pitch)+ahead*Math.sin(pitch),forward=ahead*Math.cos(pitch)-dy*Math.sin(pitch);
  return cameraAt({x:pivot.x+right*Math.cos(next.yaw)+forward*Math.sin(next.yaw),y:pivot.y+up,
    z:pivot.z-right*Math.sin(next.yaw)+forward*Math.cos(next.yaw)},next);
}

/** 注視点同士を補間すると旋回中に船が弧を描くため、実座標を補間する。 */
export function interpolateCamera(from, to, amount) {
  const a=cameraPosition(from), b=cameraPosition(to);
  const view={...from, yaw:from.yaw+(to.yaw-from.yaw)*amount, pitch:from.pitch+(to.pitch-from.pitch)*amount,
    dist:from.dist+(to.dist-from.dist)*amount};
  return cameraAt({x:a.x+(b.x-a.x)*amount,y:a.y+(b.y-a.y)*amount,z:a.z+(b.z-a.z)*amount},view);
}

/** パネルの空き領域へ視線だけを振る。投影面の平行移動や船体の移動はしない。 */
export function cockpitLook(x, y, focal) {
  const pitch=Math.atan2(y,focal), yaw=-Math.atan(x/focal*Math.cos(pitch));
  const cy=Math.cos(yaw),sy=Math.sin(yaw),cp=Math.cos(pitch),sp=Math.sin(pitch);
  return (x,y,z) => {
    const right=x*cy-z*sy, ahead=x*sy+z*cy;
    return [right,y*cp-ahead*sp,y*sp+ahead*cp];
  };
}

/** 船体の位置を固定して旋回する。旋回完了時だけ目的地基準へ表現を変え、その後は距離だけで前進できる。 */
export function turnToTarget(from,target,progress) {
  const eye=cameraPosition(from),dx=target.x-eye.x,dy=target.y-eye.y,dz=target.z-eye.z;
  const distance=Math.hypot(dx,dy,dz);
  if(distance<1e-6)return {...from};
  const yaw=Math.atan2(dx,dz),pitch=Math.atan2(dy,Math.hypot(dx,dz));
  // 上下反転している時も、最も近い角度表現で旋回し、境界で一周しない。
  const aim=[[yaw,pitch],[yaw+Math.PI,Math.PI-pitch]]
    .map(([y,p])=>({yaw:nearAngle(y,from.yaw),pitch:nearAngle(p,from.pitch)}))
    .sort((a,b)=>Math.hypot(a.yaw-from.yaw,a.pitch-from.pitch)-Math.hypot(b.yaw-from.yaw,b.pitch-from.pitch))[0];
  const t=Math.max(0,Math.min(1,progress)),ease=t*t*(3-2*t);
  const view={...from,yaw:from.yaw+(aim.yaw-from.yaw)*ease,pitch:from.pitch+(aim.pitch-from.pitch)*ease};
  const direction=forward(view);
  if(t===1)return {...view,tx:target.x,ty:target.y,tz:target.z,dist:distance};
  return {...view,tx:eye.x+direction.x*view.dist,ty:eye.y+direction.y*view.dist,tz:eye.z+direction.z*view.dist};
}
