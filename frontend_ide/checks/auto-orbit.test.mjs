// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createAutoOrbit,MANUAL_PAUSE_MS} from '../src/engines/auto-orbit.js';
const home = () => ({yaw:.6,pitch:.35,dist:4600,tx:0,ty:0,tz:0});
const direction = v => [Math.sin(v.yaw)*Math.cos(v.pitch),Math.sin(v.pitch),Math.cos(v.yaw)*Math.cos(v.pitch)];
test('楕円飛行は中心を保ち、星々の内側へ入り反対側を回って遠点へ戻る',()=>{
 const orbit=createAutoOrbit(()=>.5);let view=home(),closest=Infinity,farthest=0,near;
 for(let i=0;i<1000;i++){
  view=orbit.step(i*250,.25,view,4600);
  if(view.dist<closest){closest=view.dist;near={...view};}farthest=Math.max(farthest,view.dist);
  assert.deepEqual([view.tx,view.ty,view.tz],[0,0,0]);
  assert.ok(Object.values(view).every(Number.isFinite));
 }
 assert.ok(Math.abs(closest-4600*1.15*.22)<1);
 assert.ok(closest<1500,'最接近時は星々の分布半径の内側に入る');
 assert.ok(Math.abs(farthest-4600*1.15)<1);
 assert.ok(direction(near).reduce((s,n,i)=>s+n*direction(home())[i],0)<-.999);
});
test('遠点でだけ次の軌道を決め、再接近方向と傾きを変えても位置が連続する',()=>{
 let seed=321,calls=0;const orbit=createAutoOrbit(()=>{calls++;seed=(seed*1664525+1013904223)>>>0;return seed/2**32;});
 let view=home(),turns=0;
 for(let i=0;i<6400;i++){
  const before={...view},count=calls;view=orbit.step(i*250,.25,view,4600);
  if(i>1&&calls!==count){turns++;assert.ok(Math.abs(view.dist-before.dist)<1);assert.ok(Math.hypot(view.yaw-before.yaw,view.pitch-before.pitch)<.04);}
  assert.ok(Object.values(view).every(Number.isFinite));
 }
 assert.ok(turns>=3);
 assert.ok(Math.hypot(view.yaw-home().yaw,view.pitch-home().pitch)>.1);
});
test('通常速度は従来の1/3、最接近速度はさらに1/2へ滑らかに落とす',()=>{
 const orbit=createAutoOrbit(()=>.5);let view=home(),previous,nearSpeed,farSpeed,closest=Infinity,farthest=0,previousSpeed,previousDistance;
 const dt=.02;
 for(let i=0;i<250/dt;i++){
  view=orbit.step(i*dt*1000,dt,view,4600);
  const point=direction(view).map(n=>n*view.dist);
  if(previous&&i*dt>16){
   const speed=Math.hypot(...point.map((n,j)=>n-previous[j]))/dt;
   if(previousSpeed!==undefined&&view.dist<previousDistance&&view.dist>4600*1.15*.22+1){
    assert.ok(speed>=previousSpeed*.9999,'接近中に減速へ転じず、最接近まで加速する');
   }
   previousSpeed=speed;previousDistance=view.dist;
   if(view.dist<closest){closest=view.dist;nearSpeed=speed;}
   if(view.dist>farthest){farthest=view.dist;farSpeed=speed;}
  }
  previous=point;
 }
 const far=4600*1.15,near=far*.22,e=(far-near)/(far+near),b=Math.sqrt(far*near);
 const oldFarSpeed=b*2*Math.PI/(56*(1+e)),oldNearSpeed=b*2*Math.PI/(56*(1-e));
 assert.ok(Math.abs(farSpeed/oldFarSpeed-1/3)<.001);
 assert.ok(Math.abs(nearSpeed/oldNearSpeed-1/6)<.001);
});
test('手動操作の最終時刻から1分停止し、再開は現在の視点から滑らかに始まる',()=>{
 const orbit=createAutoOrbit(()=>.5);let view=home();
 orbit.step(0,.25,view,4600);orbit.interact(2000);orbit.interact(5000);
 view={...view,tx:500,ty:-200,dist:2000,yaw:8,pitch:4};
 assert.equal(orbit.step(5000+MANUAL_PAUSE_MS-1,.25,view,4600),null);
 const resumed=orbit.step(5000+MANUAL_PAUSE_MS,.016,view,4600);
 assert.ok(Math.abs(resumed.dist-view.dist)<1);
 assert.ok(Math.abs(resumed.yaw-view.yaw)<.01);
 assert.ok(Math.abs(resumed.pitch-view.pitch)<.01);
 assert.ok(resumed.tx>499);
});
test('選択・ドラッグ・ワープ・非表示で停止し、解除しても経過時間分を一気に飛ばない',()=>{
 const orbit=createAutoOrbit(()=>.6),view=home();
 assert.equal(orbit.step(1000,.25,view,4600,true),null);
 assert.equal(orbit.step(180000,.25,view,4600,true),null);
 const resumed=orbit.step(180001,.016,view,4600);
 assert.ok(Math.hypot(resumed.yaw-view.yaw,resumed.pitch-view.pitch)<.001);
 assert.ok(Math.abs(resumed.dist-view.dist)<1);
});
