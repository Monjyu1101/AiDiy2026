import { ref } from 'vue';
import { モデル試行音声を作成 } from './モデル試行音声.mjs';

// 試行は明示操作だけで開始し、サーバー指定順に一件ずつ待つ。共有判定はサーバーだけが行う。
export function モデル試行状態を作成({ api, 接続可能 }) {
 const 設定=ref(null),結果=ref({}),読込中=ref(false),実行中=ref(false),選択=ref(''),通知=ref('');
 let 世代=0,制御,実行ID='',破棄済み=false;
 const 有効=()=>!破棄済み&&接続可能();
 const 音声=モデル試行音声を作成({api,接続可能:有効});
 async function サーバー中止(id){if(id)try{await api(`api/モデル試行/${encodeURIComponent(id)}`,'DELETE');}catch{/* 切断時も表示は無効化し、サーバー側の期限・切断処理に委ねる。 */}}
 function 中止(理由='試行を中止しました。'){
  音声.破棄();++世代;制御?.abort();制御=undefined;const id=実行ID;実行ID='';
  if(実行中.value){結果.value=Object.fromEntries(Object.entries(結果.value).map(([key,value])=>[key,value.状態==='実行中'?{...value,状態:'中止',説明:理由}:value]));通知.value=理由;}
  実行中.value=false;読込中.value=false;void サーバー中止(id);
 }
 async function 読込(){
  if(!有効()||読込中.value||実行中.value)return;
  中止();const 現在=++世代;制御=new AbortController();読込中.value=true;設定.value=null;結果.value={};通知.value='';
  try{const data=await api('api/モデル試行','GET',制御.signal);if(現在!==世代||!有効())return;設定.value=data;選択.value=data.項目?.[0]?.id||'';}
  catch(error){if(現在===世代)通知.value=error.message||'設定を取得できませんでした。';}
  finally{if(現在===世代){読込中.value=false;制御=undefined;}}
 }
 async function 開始(){
  if(!有効()||実行中.value||読込中.value||!設定.value?.項目?.length)return;
  中止();const 現在=++世代;制御=new AbortController();実行中.value=true;結果.value={};通知.value='設定を確認して試行します…';
  let id='';
  try{
   const data=await api('api/モデル試行/開始','POST',制御.signal);id=data.実行ID;
   if(現在!==世代||!有効()){void サーバー中止(id);return;}
   実行ID=id;設定.value=data;
   for(const item of data.項目||[]){
    if(現在!==世代||!有効())return;
    選択.value=item.id;通知.value=`${item.id} を確認中…`;結果.value={...結果.value,[item.id]:{状態:'実行中'}};
    const result=await api(`api/モデル試行/${encodeURIComponent(id)}/${encodeURIComponent(item.id)}`,'POST',制御.signal);
    if(現在!==世代||!有効())return;
    結果.value={...結果.value,[item.id]:result};
    if(result.状態==='中止'){通知.value=result.説明||'試行を中止しました。';return;}
   }
   通知.value='試行が完了しました。';
  }catch(error){
   if(現在===世代){通知.value=error.message||'通信に失敗しました。設定を再読込してください。';const row=選択.value;if(row&&結果.value[row]?.状態==='実行中')結果.value={...結果.value,[row]:{状態:'ERR',説明:通知.value}};}
  }finally{
   if(現在===世代){実行中.value=false;制御=undefined;実行ID='';await サーバー中止(id);}
  }
 }
 function 切断(){中止('Tools または診断への接続が切れたため、試行を中止しました。');設定.value=null;結果.value={};選択.value='';}
 function 終了(){中止();破棄済み=true;}
 return {音声状態:音声.音声状態,音声読込:音声.読込,音声再生失敗:音声.再生失敗,設定,結果,読込中,実行中,選択,通知,読込,開始,中止,切断,終了};
}
