// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1". See LICENSE.
const motions=new WeakMap();
// click の currentTarget はイベント終了後に消えるため、受付コールバック作成時に保持する。
// 光の一周は起動要求の受付を示すだけで、起動成功や完了を表さない。
export function 起動モーション(event){
 const button=event?.currentTarget,disabledAtClick=button?.disabled;
 return ()=>{
  try{
   if(!button||disabledAtClick||globalThis.matchMedia?.('(prefers-reduced-motion: reduce)').matches)return;
   const icon=button.querySelector?.('.launch-trace-light');if(!icon?.animate)return;
   motions.get(icon)?.cancel();
   // 全区間を同じ加速曲線で進める。フェード境界でも周回速度をリセットしない。
   // x=t, y=t² に近い曲線で、最初はゆっくり、最後まで連続的に速くする。
   const animation=icon.animate([
    {offset:0,strokeDashoffset:'0',opacity:0},
    {offset:0.02,strokeDashoffset:'-2',opacity:1},
    {offset:0.9,strokeDashoffset:'-90',opacity:1},
    {offset:1,strokeDashoffset:'-100',opacity:0}
   ],{duration:900,easing:'cubic-bezier(0.333333,0,0.666667,0.333333)',iterations:1});
   motions.set(icon,animation);
   const cleanup=()=>{if(motions.get(icon)===animation)motions.delete(icon);};
   animation.finished.then(cleanup,cleanup);
  }catch{/* 演出の非対応・失敗で起動要求を止めない。 */}
 };
}
