import { ref } from 'vue';
import { 外部連携か, 確認不要か } from './キー設定表示.mjs';

// 2つの設定画面で取得・試験・公開キャッシュの世代を共有する。認証 API は App から受け取る。
export function キー設定状態を作成({ api, connected, message }) {
const keyData=ref(null),keyBusy=ref(false),keyTesting=ref(''),keyResults=ref({}),latestBusy=ref(false),modelWriteBusy=ref(false),modelWritten=ref(false);
const integrationBusy=ref(false),integrationWriteBusy=ref(false),integrationWritten=ref(false);
let keyGeneration=0, publicPoll=null, publicGeneration=0;
const publicModels=ref({状態:'未取得',件数:0,世代:-1}),publicBusy=ref(false);
function resetPublic(){publicGeneration++;clearTimeout(publicPoll);publicModels.value={状態:'未取得',件数:0,世代:-1};publicBusy.value=false;}
function updatePublic(data){if(data && Number(data.世代)>=Number(publicModels.value.世代))publicModels.value=data;}
async function pollPublic(){clearTimeout(publicPoll);if(!connected.value)return;const generation=publicGeneration;try{const data=await api('api/公開モデル');if(generation!==publicGeneration)return;updatePublic(data);}catch(error){if(generation===publicGeneration)message.value=error.message;return;}if(publicModels.value.状態==='取得中')publicPoll=setTimeout(pollPublic,1000);}
async function refreshPublic(){if(publicBusy.value || !connected.value)return;publicBusy.value=true;const generation=publicGeneration;try{const pending=api('api/公開モデル/再取得','POST');publicPoll=setTimeout(pollPublic,100);const data=await pending;if(generation===publicGeneration)updatePublic(data);}catch(error){if(generation===publicGeneration)message.value=error.message;}finally{if(generation===publicGeneration)publicBusy.value=false;}}
async function loadKeys(){if(!connected.value || keyBusy.value || keyTesting.value || modelWriteBusy.value || integrationWriteBusy.value)return;keyBusy.value=true;modelWritten.value=false;integrationWritten.value=false;const generation=++keyGeneration;keyData.value=null;keyResults.value={};try{const data=await api('api/キー設定');if(generation===keyGeneration){keyData.value=data;updatePublic(data.公開モデル);if(publicModels.value.状態==='取得中')publicPoll=setTimeout(pollPublic,1000);}}catch(error){if(generation===keyGeneration)message.value=error.message;}finally{if(generation===keyGeneration)keyBusy.value=false;}}
async function testKey(id){
 if(!connected.value || keyTesting.value || keyBusy.value || modelWriteBusy.value || integrationWriteBusy.value)return;
 // 外部連携とモデル情報は別ファイルへ保存するため、対象側の書込済み表示だけを消す。
 if(外部連携か({id}))integrationWritten.value=false;else modelWritten.value=false;

 keyTesting.value=id;const generation=keyGeneration;const next={...keyResults.value};delete next[id];keyResults.value=next;
 try{const result=await api(`api/キーテスト/${encodeURIComponent(id)}`,'POST');if(generation===keyGeneration)keyResults.value={...keyResults.value,[id]:result};}catch(error){if(generation===keyGeneration)message.value=error.message;}finally{if(generation===keyGeneration)keyTesting.value='';}
}

// 一覧再取得: 設定状況を読み直し、モデル一覧のテスト可能な行を上から順に取得する。
async function 一覧再取得(){
 if(!connected.value || latestBusy.value || integrationBusy.value || keyBusy.value || keyTesting.value)return;
 latestBusy.value=true;const generation=keyGeneration+1;
 try{await loadKeys();if(generation!==keyGeneration || !keyData.value)return;
  for(const item of keyData.value.項目.filter(item=>!外部連携か(item) && !確認不要か(item) && item.テスト可能)){if(generation!==keyGeneration)return;await testKey(item.id);}}
 finally{latestBusy.value=false;}
}
// 外部連携の状況確認: 設定状況を読み直し、外部連携のテストできる行を上から順に認証確認する。
// 全テストでは直前の一覧再取得で読み直し済みのため、モデル一覧の結果を消さないよう再読込しない。
async function 外部連携確認({再読込=true}={}){
 if(!connected.value || integrationBusy.value || latestBusy.value || keyBusy.value || keyTesting.value)return;
 integrationBusy.value=true;const generation=再読込||!keyData.value?keyGeneration+1:keyGeneration;
 try{if(再読込||!keyData.value)await loadKeys();if(generation!==keyGeneration || !keyData.value)return;
  for(const item of keyData.value.項目.filter(item=>外部連携か(item) && item.テスト可能)){if(generation!==keyGeneration)return;await testKey(item.id);}}
 finally{integrationBusy.value=false;}
}
// 外部連携の書込: サーバーが直前に確認した結果を integration_info.json へ保存する（画面の値は送らない）。
async function 外部連携書込(){
 if(!connected.value || integrationWriteBusy.value || integrationBusy.value || keyBusy.value || keyTesting.value || !Object.keys(keyResults.value).some(id=>外部連携か({id})))return false;
 integrationWriteBusy.value=true;const generation=keyGeneration;
 try{await api('api/外部連携書込','POST');if(generation===keyGeneration)integrationWritten.value=true;return true;}
 catch(error){if(generation===keyGeneration)message.value=error.message;return false;}
 finally{integrationWriteBusy.value=false;}
}
// モデル情報の書込: サーバーが直前に取得した結果をプロバイダ別ファイルへ保存する（画面の値は送らない）。
async function モデル書込(){
 if(!connected.value || modelWriteBusy.value || latestBusy.value || keyBusy.value || keyTesting.value || !Object.keys(keyResults.value).length)return false;
 modelWriteBusy.value=true;const generation=keyGeneration;
 try{await api('api/モデル書込','POST');if(generation===keyGeneration)modelWritten.value=true;return true;}
 catch(error){if(generation===keyGeneration)message.value=error.message;return false;}
 finally{modelWriteBusy.value=false;}
}
function 設定を破棄(){resetPublic();keyGeneration++;keyData.value=null;keyResults.value={};keyBusy.value=false;keyTesting.value='';integrationWritten.value=false;}
function 終了(){設定を破棄();}
return { keyData,keyBusy,keyTesting,keyResults,latestBusy,modelWriteBusy,modelWritten,integrationBusy,integrationWriteBusy,integrationWritten,publicModels,publicBusy,loadKeys,testKey,一覧再取得,モデル書込,外部連携確認,外部連携書込,refreshPublic,resetPublic,設定を破棄,終了 };
}
