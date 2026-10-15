import { ref } from 'vue';

// 2つの設定画面で取得・試験・公開キャッシュの世代を共有する。認証 API は App から受け取る。
export function キー設定状態を作成({ api, connected, message }) {
const keyData=ref(null),keyBusy=ref(false),keyTesting=ref(''),keyResults=ref({});
let keyGeneration=0, publicPoll=null, publicGeneration=0;
const publicModels=ref({状態:'未取得',件数:0,世代:-1}),publicBusy=ref(false);
function resetPublic(){publicGeneration++;clearTimeout(publicPoll);publicModels.value={状態:'未取得',件数:0,世代:-1};publicBusy.value=false;}
function updatePublic(data){if(data && Number(data.世代)>=Number(publicModels.value.世代))publicModels.value=data;}
async function pollPublic(){clearTimeout(publicPoll);if(!connected.value)return;const generation=publicGeneration;try{const data=await api('api/公開モデル');if(generation!==publicGeneration)return;updatePublic(data);}catch(error){if(generation===publicGeneration)message.value=error.message;return;}if(publicModels.value.状態==='取得中')publicPoll=setTimeout(pollPublic,1000);}
async function refreshPublic(){if(publicBusy.value || !connected.value)return;publicBusy.value=true;const generation=publicGeneration;try{const pending=api('api/公開モデル/再取得','POST');publicPoll=setTimeout(pollPublic,100);const data=await pending;if(generation===publicGeneration)updatePublic(data);}catch(error){if(generation===publicGeneration)message.value=error.message;}finally{if(generation===publicGeneration)publicBusy.value=false;}}
async function loadKeys(){if(!connected.value || keyBusy.value || keyTesting.value)return;keyBusy.value=true;const generation=++keyGeneration;keyData.value=null;keyResults.value={};try{const data=await api('api/キー設定');if(generation===keyGeneration){keyData.value=data;updatePublic(data.公開モデル);if(publicModels.value.状態==='取得中')publicPoll=setTimeout(pollPublic,1000);}}catch(error){if(generation===keyGeneration)message.value=error.message;}finally{if(generation===keyGeneration)keyBusy.value=false;}}
async function testKey(id){
 if(!connected.value || keyTesting.value || keyBusy.value)return;

 keyTesting.value=id;const generation=keyGeneration;const next={...keyResults.value};delete next[id];keyResults.value=next;
 try{const result=await api(`api/キーテスト/${encodeURIComponent(id)}`,'POST');if(generation===keyGeneration)keyResults.value={...keyResults.value,[id]:result};}catch(error){if(generation===keyGeneration)message.value=error.message;}finally{if(generation===keyGeneration)keyTesting.value='';}
}

function 設定を破棄(){resetPublic();keyGeneration++;keyData.value=null;keyResults.value={};keyBusy.value=false;keyTesting.value='';}
function 終了(){設定を破棄();}
return { keyData,keyBusy,keyTesting,keyResults,publicModels,publicBusy,loadKeys,testKey,refreshPublic,resetPublic,設定を破棄,終了 };
}
