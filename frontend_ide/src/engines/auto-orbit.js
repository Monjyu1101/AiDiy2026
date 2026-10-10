// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026

export const MANUAL_PAUSE_MS = 60_000;
const TAU = Math.PI * 2;
const dot = (a, b) => a.reduce((sum, x, i) => sum + x * b[i], 0);
const unit = v => { const length = Math.hypot(...v); return v.map(x => x / length); };
const cross = (a, b) => [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
const mix = (a, b, amount) => a.map((x, i) => x * (1 - amount) + b[i] * amount);
const direction = view => [Math.sin(view.yaw)*Math.cos(view.pitch), Math.sin(view.pitch), Math.cos(view.yaw)*Math.cos(view.pitch)];
const nearAngle = (angle, reference) => reference + Math.atan2(Math.sin(angle-reference), Math.cos(angle-reference));
const smoothstep = t => { const x = Math.max(0,Math.min(1,t)); return x*x*(3-2*x); };

// 遠点を起点にしたケプラー方程式 M = E + e sin(E)。軌道形状を求め、進行速度は別に調整する。
function eccentricAnomaly(mean, eccentricity) {
  let angle = mean;
  for (let i=0;i<8;i++) {
    const correction = (angle+eccentricity*Math.sin(angle)-mean)/(1+eccentricity*Math.cos(angle));
    angle -= correction;
    if (Math.abs(correction)<1e-12) break;
  }
  return angle;
}

// Euler角の±π境界と手動で上下反転した視点でも、直前に近い表現を選ぶ。
function angles(vector, reference) {
  const yaw = Math.atan2(vector[0], vector[2]), pitch = Math.asin(Math.max(-1, Math.min(1, vector[1])));
  return [[yaw, pitch], [yaw + Math.PI, Math.PI - pitch]]
    .map(([y,p]) => ({yaw:nearAngle(y,reference.yaw),pitch:nearAngle(p,reference.pitch)}))
    .sort((a,b) => Math.hypot(a.yaw-reference.yaw,a.pitch-reference.pitch)-Math.hypot(b.yaw-reference.yaw,b.pitch-reference.pitch))[0];
}

/** 中心を焦点とする楕円。遠点だけで次の反対側への接近角・軌道面を更新する。 */
export function createAutoOrbit(random = Math.random) {
  let leg = null, pausedUntil = -Infinity, start = null, elapsed = 0;
  const between = (a,b) => a + (b-a)*random();
  function next(farDirection, distance, previousTangent, previousLeg) {
    const horizontal = Math.hypot(farDirection[0],farDirection[2]) > 0.01
      ? unit(cross([0,1,0],farDirection)) : [1,0,0];
    const tangent = previousTangent
      ? unit(previousTangent.map((x,i)=>x-dot(previousTangent,farDirection)*farDirection[i])) : horizontal;
    const normal = unit(cross(farDirection,tangent)), tilt = between(-0.32,0.32);
    // 最接近を全景の約1/4まで縮め、半径1500の星々の内側を通過する。
    const near = distance*between(0.18,0.26), duration = between(48,64);
    // 次の楕円でも面積速度を引き継ぎ、遠点で急停止・急加速させない。
    const area = (distance+near)/2*Math.sqrt(distance*near);
    const previousArea = previousLeg && (previousLeg.far+previousLeg.near)/2*Math.sqrt(previousLeg.far*previousLeg.near);
    return {u:farDirection,v:unit(tangent.map((x,i)=>x*Math.cos(tilt)+normal[i]*Math.sin(tilt))),entryTangent:tangent,
      far:distance,near,duration:previousLeg?previousLeg.duration*area/previousArea:duration,drift:between(-0.22,0.22),time:0};
  }
  function reset() { leg = null; start = null; elapsed = 0; }
  return {
    reset,
    resume() { pausedUntil = -Infinity; reset(); },
    interact(now) { pausedUntil = now + MANUAL_PAUSE_MS; reset(); },
    get pausedUntil() { return pausedUntil; },
    step(now, dt, view, overview, blocked = false) {
      if (blocked || now < pausedUntil) { reset(); return null; }
      if (!leg) { start = {...view}; leg = next(direction(view), overview*1.15); }
      const seconds = Math.max(0, Math.min(dt,0.25)) / 3;
      const eccentricity = (leg.far-leg.near)/(leg.far+leg.near);
      const currentPhase = eccentricAnomaly(TAU*leg.time/leg.duration,eccentricity);
      // 速度差を圧縮して加速感を残す。遠点は1/3速、近点は従来の1/6速でも、
      // 接近中の実速度は単調に増え、近点直前で減速へ転じない。
      const radius = (leg.far+leg.near)/2 * (1+eccentricity*Math.cos(currentPhase));
      const inverseA = 2/(leg.far+leg.near);
      const speedRatio = Math.sqrt((2/radius-inverseA)/(2/leg.far-inverseA));
      const nearSpeed = Math.pow(speedRatio,-Math.log(2)/Math.log(leg.far/leg.near));
      elapsed += seconds; leg.time += seconds * nearSpeed;
      if (leg.time >= leg.duration) {
        const farDirection = unit(leg.u.map((x,i)=>x*Math.cos(leg.drift)+leg.v[i]*Math.sin(leg.drift)));
        const remainder = leg.time-leg.duration;
        const tangent = leg.u.map((x,i)=>-x*Math.sin(leg.drift)+leg.v[i]*Math.cos(leg.drift));
        leg = next(farDirection,leg.far,tangent,leg);
        leg.time = remainder;
      }
      const progress = leg.time/leg.duration;
      const a = (leg.far+leg.near)/2, e = (leg.far-leg.near)/(leg.far+leg.near);
      const phase = eccentricAnomaly(TAU*progress,e);
      const x = a*(Math.cos(phase)+e), y = a*Math.sqrt(1-e*e)*Math.sin(phase);
      // 軌道のランダムな向き変更は演出として別に補間し、遠点での接線を保つ。
      const drift = leg.drift*(progress-Math.sin(TAU*progress)/TAU);
      const tangent = unit(mix(leg.entryTangent,leg.v,smoothstep(progress/.2)));
      const dx = x*Math.cos(drift)-y*Math.sin(drift), dy = x*Math.sin(drift)+y*Math.cos(drift);
      const point = leg.u.map((value,i)=>value*dx+tangent[i]*dy), distance = Math.hypot(...point);
      const blend = Math.min(1,elapsed/5), smooth = blend*blend*(3-2*blend);
      const aim = unit(mix(direction(start),unit(point), smooth));
      return {...angles(aim,view),dist:Math.exp(Math.log(start.dist)*(1-smooth)+Math.log(distance)*smooth),
        tx:start.tx*(1-smooth),ty:start.ty*(1-smooth),tz:start.tz*(1-smooth)};
    },
  };
}
