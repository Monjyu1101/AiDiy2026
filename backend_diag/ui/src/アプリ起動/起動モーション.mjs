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
   const animation=icon.animate([{strokeDashoffset:'0',opacity:1},{strokeDashoffset:'-100',opacity:1}],{duration:800,easing:'linear',iterations:1});
   motions.set(icon,animation);
   const cleanup=()=>{if(motions.get(icon)===animation)motions.delete(icon);};
   animation.finished.then(cleanup,cleanup);
  }catch{/* 演出の非対応・失敗で起動要求を止めない。 */}
 };
}
