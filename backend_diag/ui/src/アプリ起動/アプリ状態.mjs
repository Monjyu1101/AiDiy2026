// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1". See LICENSE.
import {ref} from 'vue';
export function アプリ状態を作成({api,picker=()=>globalThis.aidiyWindow?.selectProject?.()}){
 const 項目=ref([]),フォルダ=ref(''),処理中=ref(''),通知=ref(''),結果=ref({}),選択中=ref(false),参照中=ref(false),一覧=ref(null),パス入力=ref(''),参照エラー=ref('');
 let folderVersion=0;
 async function 読込(){if(項目.value.length)return;try{項目.value=(await api('api/アプリ起動')).対象;}catch(error){通知.value=error.message;}}
 async function 参照(path){
  if(参照中.value)return;const version=++folderVersion;参照中.value=true;参照エラー.value='';
  try{const data=await api('api/アプリ起動/フォルダ','POST',undefined,'json',{フォルダ:path});if(version!==folderVersion)return;一覧.value=data;パス入力.value=data.フォルダ;}
  catch(error){if(version===folderVersion)参照エラー.value=error.message;}finally{if(version===folderVersion)参照中.value=false;}
 }
 async function 選択(){
  if(選択中.value||処理中.value)return;
  選択中.value=true;通知.value='';
  try{
   const selected=await picker();
   if(selected===undefined){await 参照(フォルダ.value);if(!一覧.value)通知.value=参照エラー.value;return;}
   if(selected){const data=await api('api/アプリ起動/フォルダ','POST',undefined,'json',{フォルダ:selected});フォルダ.value=data.フォルダ;結果.value={};}
  }catch(error){通知.value=error.message;}
  finally{if(!一覧.value)選択中.value=false;}
 }
 function 決定(){if(!一覧.value||参照中.value)return;フォルダ.value=一覧.value.フォルダ;結果.value={};一覧.value=null;選択中.value=false;}
 function 取消(){folderVersion++;一覧.value=null;選択中.value=false;参照中.value=false;}
 function 解除(){if(処理中.value||選択中.value)return;フォルダ.value='';結果.value={};通知.value='';}
 async function 起動(id,{開始時}={}){
  if(!フォルダ.value||処理中.value||選択中.value)return;処理中.value=id;通知.value='';
  try{開始時?.();const data=await api('api/アプリ起動/開始','POST',undefined,'json',{対象:id,フォルダ:フォルダ.value});結果.value={...結果.value,[id]:{通知:data.通知,種別:data.起動済み?'existing':'accepted',ログ:data.ログ}};}
  catch(error){結果.value={...結果.value,[id]:{通知:error.message,種別:'error'}};}
  finally{処理中.value='';}
 }
 return {項目,フォルダ,処理中,通知,結果,選択中,参照中,一覧,パス入力,参照エラー,読込,参照,選択,決定,取消,解除,起動};
}
