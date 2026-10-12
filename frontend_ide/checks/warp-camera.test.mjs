// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026

import test from 'node:test';
import assert from 'node:assert/strict';
import {cameraPosition,turnToTarget,cameraAt,interpolateCamera,cockpitLook,orbitAround} from '../src/engines/warp-camera.js';
const near=(a,b)=>assert.ok(Math.abs(a-b)<1e-8,`${a} != ${b}`);
const target={x:1200,y:-600,z:350};
for(const pitch of [.35,Math.PI+0.2,-Math.PI*2-.4])test(`旋回中の船体位置を固定し、完了後の前進は目的地への直線になる: ${pitch}`,()=>{
  const from={tx:200,ty:100,tz:-80,dist:4000,yaw:Math.PI*2+0.6,pitch};
  const eye=cameraPosition(from);
  for(const t of [0,.1,.5,.9,1]){
    const view=turnToTarget(from,target,t),position=cameraPosition(view);
    for(const key of ['x','y','z'])near(position[key],eye[key]);
    if(t<1)near(view.dist,from.dist);
    assert.ok(Math.abs(view.yaw-from.yaw)<=Math.PI);
    assert.ok(Math.abs(view.pitch-from.pitch)<=Math.PI);
  }
  const facing=turnToTarget(from,target,1);
  near(facing.tx,target.x);near(facing.ty,target.y);near(facing.tz,target.z);
  // 実際の描画座標式でも、目的地が正面（横・縦とも0）にあることを確認。
  const dx=target.x-eye.x,dy=target.y-eye.y,dz=target.z-eye.z;
  near(dx*Math.cos(facing.yaw)-dz*Math.sin(facing.yaw),0);
  near(dy*Math.cos(facing.pitch)-(dx*Math.sin(facing.yaw)+dz*Math.cos(facing.yaw))*Math.sin(facing.pitch),0);
  const halfway=cameraPosition({...facing,dist:facing.dist/2});
  for(const key of ['x','y','z'])near(halfway[key],(eye[key]+target[key])/2);
});
test('目的地と船体が同位置でも有限値を維持する',()=>{
  const from={tx:0,ty:0,tz:0,dist:100,yaw:0,pitch:0};
  assert.deepEqual(turnToTarget(from,cameraPosition(from),1),from);
});

test('航行旋回の補間中も船体位置は固定され、ズームは船首方向の直線を進む',()=>{
  const from={tx:500,ty:-300,tz:200,dist:4000,yaw:7,pitch:3.5}, eye=cameraPosition(from);
  const rotated=cameraAt(eye,{...from,yaw:from.yaw+.5,pitch:from.pitch-.2});
  for(const t of [.01,.25,.5,1]) {
    const view=interpolateCamera(from,rotated,t);
    for(const key of ['x','y','z'])near(cameraPosition(view)[key],eye[key]);
  }
  const to={...rotated,dist:rotated.dist/2};
  const end=cameraPosition(to), midway=cameraPosition(interpolateCamera(rotated,to,.5));
  const delta=Object.keys(eye).map(key=>end[key]-eye[key]);
  const moved=Object.keys(eye).map(key=>midway[key]-eye[key]);
  near(Math.hypot(delta[1]*moved[2]-delta[2]*moved[1],delta[2]*moved[0]-delta[0]*moved[2],delta[0]*moved[1]-delta[1]*moved[0]),0);
});

test('パネルの中央調整は平行移動ではなく視線の回転で、角度と距離を保存する',()=>{
  for(const [x,y] of [[0,0],[-300,10],[160,-220]]) {
    const look=cockpitLook(x,y,800), ahead=look(0,0,1);
    near(ahead[0]/ahead[2]*800,x);near(-ahead[1]/ahead[2]*800,y);
    const a=[1,2,3], b=[-4,5,6], ar=look(...a),br=look(...b);
    near(Math.hypot(...ar),Math.hypot(...a));
    near(ar.reduce((sum,v,i)=>sum+v*br[i],0),a.reduce((sum,v,i)=>sum+v*b[i],0));
  }
});

test('ドラッグは中心星を周回し、その後の航行は回り込んだ船体位置から旋回する',()=>{
  const pivot={x:100,y:-200,z:300};
  const from={tx:100,ty:-200,tz:300,dist:2500,yaw:.6,pitch:.3};
  let view={...from};
  for(let i=0;i<20;i++) {
    view=orbitAround(view,pivot,.025,-.01);
    const eye=cameraPosition(view);
    near(Math.hypot(eye.x-pivot.x,eye.y-pivot.y,eye.z-pivot.z),2500);
    near(view.tx,pivot.x);near(view.ty,pivot.y);near(view.tz,pivot.z);
  }
  const departure=cameraPosition(view);
  assert.ok(Math.hypot(...['x','y','z'].map(key=>departure[key]-cameraPosition(from)[key]))>100);
  for(const progress of [0,.2,.5,1]) {
    const turned=turnToTarget(view,target,progress);
    for(const key of ['x','y','z'])near(cameraPosition(turned)[key],departure[key]);
  }
});
