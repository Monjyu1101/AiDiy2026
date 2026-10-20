// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1". See LICENSE.
import {ref} from 'vue';
export function CLI状態を作成({api,アプリ,接続可能=()=>true,確認=message=>globalThis.confirm(message)}){
 const 項目=ref([]),全項目=ref([]),読込中=ref(false),処理中=ref(''),通知=ref(''),失敗=ref(false);let revision=0;
 const 起動待ち=new Map();let 起動番号=0,確認待ち=0,接続番号=0;
 function 処理を反映(){
  処理中.value=[...起動待ち.values()].at(-1)||'';
  if(!アプリ.処理中.value||アプリ.処理中.value.startsWith('cli:'))アプリ.処理中.value=処理中.value?'cli:'+処理中.value:'';
 }
 async function 読込(){
  if(読込中.value||!接続可能())return;const version=++revision;読込中.value=true;
  try{const data=await api('api/CLI起動');if(version===revision){全項目.value=data.対象;項目.value=data.対象.filter(item=>item.利用可能===true);if(失敗.value){失敗.value=false;通知.value='';}}}
  catch(error){if(version===revision){全項目.value=[];項目.value=[];通知.value=error.message;失敗.value=true;}}
  finally{if(version===revision)読込中.value=false;}
 }
 async function 起動(id,{確認省略=false}={}){
  if(!接続可能()||確認待ち||アプリ.処理中.value&&!アプリ.処理中.value.startsWith('cli:')||アプリ.選択中.value||!アプリ.フォルダ.value)return;
  const item=項目.value.find(value=>value.id===id);if(!item||item.利用可能===false)return;
  const project=アプリ.フォルダ.value,run=++起動番号,connection=接続番号;
  起動待ち.set(run,id);処理を反映();通知.value='';失敗.value=false;
  if(確認省略!==true)確認待ち=run;
  try{
   // 確認ダイアログだけは重ねない。確認後の起動は同じCLIも並行して受け付ける。
   // 通常画面・ミニの明示クリックは確認を省き、固定の起動条件は共用する。
   const accepted=確認省略===true?true:await 確認(`${item.名前} を aidiy_term で開始しますか？\n\nプロジェクト: ${project}\nモード: ${item.モード}\nモデル: 指定なし（CLI の既定設定）\n\nファイルの変更やコマンド実行が自動承認されます。CLIによってはサンドボックスも解除されます。信頼できるプロジェクトだけで使用してください。CLIの契約や設定によって利用料金が発生する場合があります。ログイン・組織の制限・初回の信頼確認はCLI側に残る場合があります。`);
   if(確認待ち===run)確認待ち=0;
   if(accepted!==true||!接続可能()||connection!==接続番号||project!==アプリ.フォルダ.value)return;
   // 成功通知は保持しない。古いサーバーが通知文を返しても画面を押し下げない。
   await api('api/CLI起動/開始','POST',undefined,'json',{対象:id,フォルダ:project,自動承認確認:true});
  }catch(error){if(run===起動番号&&connection===接続番号){通知.value=error.message;失敗.value=true;}}
  finally{if(確認待ち===run)確認待ち=0;起動待ち.delete(run);処理を反映();}
 }
 function 切断(){revision++;接続番号++;全項目.value=[];項目.value=[];読込中.value=false;}
 return {項目,全項目,読込中,処理中,通知,失敗,読込,起動,切断};
}
