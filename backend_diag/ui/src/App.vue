<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import InstallPanel from './InstallPanel.vue';
import KeyPanel from './KeyPanel.vue';
const tab=ref('install'), key=ref(new URLSearchParams(location.hash.slice(1)).get('token') || ''), input=ref('');
if(location.hash) history.replaceState(null,'',location.pathname+location.search);
const connected=ref(false),connecting=ref(false),busy=ref(false),entries=ref([]),results=ref([]),coverage=ref({}),keyData=ref(null),keyBusy=ref(false),keyTesting=ref(''),keyResults=ref({});
let keyGeneration=0, publicPoll=null, publicGeneration=0;
const publicModels=ref({状態:'未取得',件数:0,世代:-1}),publicBusy=ref(false);
function resetPublic(){publicGeneration++;clearTimeout(publicPoll);publicModels.value={状態:'未取得',件数:0,世代:-1};publicBusy.value=false;}
function updatePublic(data){if(data && Number(data.世代)>=Number(publicModels.value.世代))publicModels.value=data;}
async function pollPublic(){clearTimeout(publicPoll);if(!connected.value)return;const generation=publicGeneration;try{const data=await api('api/公開モデル');if(generation!==publicGeneration)return;updatePublic(data);}catch(error){if(generation===publicGeneration)message.value=error.message;return;}if(publicModels.value.状態==='取得中')publicPoll=setTimeout(pollPublic,1000);}
async function refreshPublic(){if(publicBusy.value || !connected.value)return;publicBusy.value=true;const generation=publicGeneration;try{const pending=api('api/公開モデル/再取得','POST');publicPoll=setTimeout(pollPublic,100);const data=await pending;if(generation===publicGeneration)updatePublic(data);}catch(error){if(generation===publicGeneration)message.value=error.message;}finally{if(generation===publicGeneration)publicBusy.value=false;}}
onUnmounted(()=>clearTimeout(publicPoll));
const message=ref('ローカル環境の外部プログラムを確認します。');
const counts=computed(()=>['未確認','未検出','OK','NG','ERR'].map(状態=>({状態,数:entries.value.filter(e=>(results.value.find(r=>r.id===e.id)?.状態 || '未確認')===状態).length})).filter(r=>r.数));
async function api(path,method='GET') {
 const response=await fetch(new URL(path,location.href),{method,headers:{Authorization:`Bearer ${key.value}`},cache:'no-store',credentials:'same-origin'});
 const data=await response.json();
 if(!response.ok){if(response.status===401){resetPublic();keyGeneration++;key.value='';connected.value=false;keyData.value=null;keyResults.value={};}throw new Error(data.エラー || '通信に失敗しました。');}
 return data;
}
async function connect(){if(connecting.value)return;connecting.value=true;try{const data=await api('api/一覧');entries.value=data.項目;results.value=data.結果;coverage.value=data.調査 || {};resetPublic();connected.value=true;message.value=`インストール確認: ${entries.value.length} 件。ボタンで、このサーバーの実行環境を確認します。`;if(tab.value==='keys')await loadKeys();}catch(error){message.value=error.message;}finally{connecting.value=false;}}
function submit(){if(connecting.value)return;key.value=input.value.trim();input.value='';connect();}
async function runInstall(){if(busy.value || !connected.value)return;busy.value=true;message.value='インストール確認中です。プログラムごとに最大 5 秒、4 件ずつ確認しています…';try{results.value=(await api('api/診断','POST')).結果;message.value='インストール確認完了。未検出は全体の起動失敗を意味しません。';}catch(error){message.value=error.message;}finally{busy.value=false;}}
async function loadKeys(){if(!connected.value || keyBusy.value || keyTesting.value)return;keyBusy.value=true;const generation=++keyGeneration;keyData.value=null;keyResults.value={};try{const data=await api('api/キー設定');if(generation===keyGeneration){keyData.value=data;updatePublic(data.公開モデル);if(publicModels.value.状態==='取得中')publicPoll=setTimeout(pollPublic,1000);}}catch(error){message.value=error.message;}finally{keyBusy.value=false;}}
async function changeTab(value){tab.value=value;if(value==='keys' && !keyData.value)await loadKeys();}
async function testKey(id){
 if(!connected.value || keyTesting.value || keyBusy.value)return;

 keyTesting.value=id;const generation=keyGeneration;const next={...keyResults.value};delete next[id];keyResults.value=next;
 try{const result=await api(`api/キーテスト/${encodeURIComponent(id)}`,'POST');if(generation===keyGeneration)keyResults.value={...keyResults.value,[id]:result};}catch(error){message.value=error.message;}finally{keyTesting.value='';}
}
onMounted(()=>{if(key.value)connect();});
</script>
<template>
<header><div><span class="eyebrow">AIDIY • ENVIRONMENT</span><h1>環境診断</h1></div><button id="run" :disabled="!connected || busy" @click="runInstall" title="現在の対象はインストール確認のみ">{{busy ? '確認中…' : '全テスト'}}</button></header>
<nav class="tabs" aria-label="診断の種類"><button :aria-pressed="tab==='install'" :class="{active:tab==='install'}" @click="changeTab('install')">インストール</button><button :aria-pressed="tab==='keys'" :class="{active:tab==='keys'}" @click="changeTab('keys')">キー設定状況</button><span>全テストの対象: インストール確認のみ</span></nav>
<section v-if="!connected" id="login" class="login"><label for="token">起動したターミナルの認証 URL を開くか、認証キーを入力してください。</label><form @submit.prevent="submit"><input id="token" v-model="input" :disabled="connecting" type="password" autocomplete="off" placeholder="起動中のみ有効な認証キー"><button id="connect" :disabled="connecting">接続</button></form></section>
<p id="message" role="status" aria-live="polite">{{message}}</p>
<InstallPanel v-show="tab==='install'" :entries="entries" :results="results" :busy="busy" :connected="connected" :counts="counts" @run="runInstall"/>
<KeyPanel v-show="tab==='keys'" :data="keyData" :results="keyResults" :loading="keyBusy" :testing="keyTesting" :connected="connected" :public-models="publicModels" :public-busy="publicBusy" @refresh="loadKeys" @refresh-public="refreshPublic" @test="testKey"/>
<footer><p id="coverage" v-if="coverage.sourceTargetFiles">調査{{coverage.complete ? '完了':'途中'}}: 対象ソース・設定 {{Number(coverage.scannedSourceFiles || 0).toLocaleString()}} / {{Number(coverage.sourceTargetFiles).toLocaleString()}} 件 · {{entries.length}} 項目 · {{String(coverage.commit || '').slice(0,8)}}。通常の Markdown 本文・画像・音声・モデル等は除外。</p><p v-else>ソース調査情報は接続後に表示します。</p>対象はこの診断サーバーの実行環境です。存在確認は動作・認証・接続の保証ではありません。</footer>
</template>
