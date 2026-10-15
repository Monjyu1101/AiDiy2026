// 起動中だけ保持する匿名公開メタデータ。キー設定・認証試験結果とは別管理。
import {runPython} from './key_status.mjs';
export function createPublicModelCache({run=runPython}={}) {
 let state='未取得',models={},checked=null,message='公開モデルはまだ取得していません。',revision=0,pending=null;
 const snapshot=()=>({状態:state,件数:Object.keys(models).length,確認日時:checked,説明:message,世代:revision});
 const input=()=>({公開モデル:state==='取得済'?models:{},公開状態:state,確認日時:checked});
 const refresh=()=>{
  if(pending)return pending;
  state='取得中';models={};checked=null;message='キーなしで公開モデル一覧を取得しています。';revision++;
  pending=(async()=>{
   try {
    const response=await run('public');const data=response.data;
    if(response.error || data?.状態!=='OK' || !data.公開モデル || typeof data.公開モデル!=='object' || Array.isArray(data.公開モデル))throw new Error('invalid');
    const safe={};for(const [id,details] of Object.entries(data.公開モデル).slice(0,5000)){
     if(!/^[A-Za-z0-9][A-Za-z0-9._:/@+\-]{0,199}$/.test(id) || !details || typeof details!=='object')continue;
     safe[id]={model_id:id,作成日:typeof details.作成日==='string'?details.作成日.slice(0,20):null,トークン数:String(details.トークン数 ?? '').slice(0,30),モダリティ:typeof details.モダリティ==='string'?details.モダリティ.slice(0,200):null};
    }
    models=safe;state='取得済';checked=new Date().toISOString();message='公開モデル取得済。キーの有効性は確認していません。';
   } catch {models={};state='失敗';message='公開モデルを取得できませんでした。再取得できます。キーの有効性とは別の結果です。';}
   finally {revision++;pending=null;}
   return snapshot();
  })();
  return pending;
 };
 return {snapshot,input,refresh};
}
