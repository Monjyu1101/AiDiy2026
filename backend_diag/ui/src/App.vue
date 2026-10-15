<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue';
import インストールパネル from './インストール/インストールパネル.vue';
import { インストール状態を作成 } from './インストール/インストール状態.mjs';
import モデルキー設定パネル from './モデルキー設定/モデルキー設定パネル.vue';
import 外部連携設定パネル from './外部連携設定/外部連携設定パネル.vue';
import { キー設定状態を作成 } from './キー設定共通/キー設定状態.mjs';
import モデル試行パネル from './configモデル試行/モデル試行パネル.vue';
import { モデル試行状態を作成 } from './configモデル試行/モデル試行状態.mjs';
import ステータスバー from './ウィンドウ/ステータスバー.vue';
import {Tools接続を作成} from './ウィンドウ/Tools接続.mjs';
const tab=ref('install'), key=ref(new URLSearchParams(location.hash.slice(1)).get('token') || ''), input=ref('');
if(location.hash) history.replaceState(null,'',location.pathname+location.search);
const connected=ref(false),connecting=ref(false);
const message=ref('ローカル環境の外部プログラムを確認します。');
const { 確認中, 確認済み, 書込中, 書込済み, 表示中, 項目, 結果, 調査, 一覧を反映, インストール確認, 書込, 全テスト } = インストール状態を作成({ api, 接続済み: connected, 通知: message });
const { keyData,keyBusy,keyTesting,keyResults,latestBusy,modelWriteBusy,modelWritten,publicModels,publicBusy,loadKeys,testKey,最新モデル取得,モデル書込,refreshPublic,resetPublic,設定を破棄,終了 } = キー設定状態を作成({ api, connected, message });
const toolsOnline=ref(false),toolsChecking=ref(false);
const tools=Tools接続を作成({api,反映:state=>{toolsOnline.value=state.online;toolsChecking.value=state.checking;}});
const 試行=モデル試行状態を作成({api,接続可能:()=>connected.value&&toolsOnline.value});
const {設定:試行設定,結果:試行結果,読込中:試行読込中,実行中:試行実行中,選択:試行選択,通知:試行通知,音声状態:試行音声}=試行;
watch(connected,value=>tools.接続(value));
watch(()=>connected.value&&toolsOnline.value,value=>{if(!value)試行.切断();else if(tab.value==='trials')void 試行.読込();},{flush:'sync'});
onUnmounted(()=>{試行.終了();終了();tools.終了();});
async function api(path,method='GET',signal,format='json') {
 const response=await fetch(new URL(path,location.href),{method,signal,headers:{Authorization:`Bearer ${key.value}`},cache:'no-store',credentials:'same-origin'});
 if(response.ok && format==='blob')return response.blob();
 const data=await response.json();
 if(!response.ok){if(response.status===401){設定を破棄();key.value='';connected.value=false;}throw new Error(data.エラー || '通信に失敗しました。');}
 return data;
}
async function connect(){if(connecting.value)return;connecting.value=true;try{const data=await api('api/一覧');一覧を反映(data);resetPublic();connected.value=true;message.value='';if(tab.value==='keys'||tab.value==='integrations')await loadKeys();}catch(error){message.value=error.message;}finally{connecting.value=false;}}
function submit(){if(connecting.value)return;key.value=input.value.trim();input.value='';connect();}
// 全テスト: インストール確認→書込、続けて最新モデル取得→モデル情報の書込。
async function 全診断(){if(!await 全テスト())return;await 最新モデル取得();await モデル書込();}
async function changeTab(value){if(value==='trials'&&(!connected.value||!toolsOnline.value))return;tab.value=value;if(value==='trials'){if(!試行設定.value)await 試行.読込();}else if(value!=='install' && !keyData.value)await loadKeys();}
onMounted(()=>{if(key.value)connect();});
</script>
<template>
<component :is="ステータスバー" :online="toolsOnline" :enabled="true" :checking="toolsChecking" :connected="connected"/>
<nav class="tabs" aria-label="診断の種類"><button :aria-pressed="tab==='install'" :class="{active:tab==='install'}" @click="changeTab('install')">インストール</button><button :aria-pressed="tab==='keys'" :class="{active:tab==='keys'}" @click="changeTab('keys')">モデルキー設定</button><button :aria-pressed="tab==='integrations'" :class="{active:tab==='integrations'}" @click="changeTab('integrations')">外部連携設定</button><button :aria-pressed="tab==='trials'" :class="{active:tab==='trials'}" :disabled="!connected || !toolsOnline" title="Tools 接続時に利用できます" @click="changeTab('trials')">configモデル試行</button><button id="run" class="run-all" :disabled="!connected || 確認中 || 書込中 || latestBusy || modelWriteBusy" @click="全診断" title="インストール確認と最新モデル取得を実行し、結果を書き込みます">{{確認中 ? '確認中…' : 書込中 || modelWriteBusy ? '書込中…' : latestBusy ? '取得中…' : '全テスト'}}</button></nav>
<section v-if="!connected" id="login" class="login"><label for="token">起動したターミナルの認証 URL を開くか、認証キーを入力してください。</label><form @submit.prevent="submit"><input id="token" v-model="input" :disabled="connecting" type="password" autocomplete="off" placeholder="起動中のみ有効な認証キー"><button id="connect" :disabled="connecting">接続</button></form></section>
<p v-if="message" id="message" role="status" aria-live="polite">{{message}}</p>
<component :is="インストールパネル" v-show="tab==='install'" :項目="項目" :結果="結果" :確認中="確認中" :接続済み="connected" :確認済み="確認済み" :書込中="書込中" :書込済み="書込済み" :表示中="表示中" @確認="インストール確認" @書込="書込"/>
<component :is="モデルキー設定パネル" v-show="tab==='keys'" :data="keyData" :results="keyResults" :loading="keyBusy" :testing="keyTesting" :connected="connected" :public-models="publicModels" :public-busy="publicBusy" :latest-busy="latestBusy" :write-busy="modelWriteBusy" :written="modelWritten" @latest="最新モデル取得" @write="モデル書込" @refresh-public="refreshPublic" @test="testKey"/>
<component :is="外部連携設定パネル" v-show="tab==='integrations'" :data="keyData" :results="keyResults" :loading="keyBusy" :testing="keyTesting" :connected="connected" @refresh="loadKeys"/>
<component :is="モデル試行パネル" v-show="tab==='trials'" :data="試行設定" :results="試行結果" :loading="試行読込中" :running="試行実行中" :selected="試行選択" :online="connected && toolsOnline" :message="試行通知" :audio-states="試行音声" :visible="tab==='trials'" @audio-load="試行.音声読込" @audio-error="試行.音声再生失敗" @refresh="試行.読込" @start="試行.開始" @cancel="試行.中止()" @select="試行選択=$event"/>
<footer><div class="diag-meta"><span>診断 {{connected?'接続済み':'未接続'}}</span><span>tools {{toolsOnline?'オンライン':'オフライン'}}</span></div><p id="coverage" v-if="調査.sourceTargetFiles">調査{{調査.complete ? '完了':'途中'}}: 対象ソース・設定 {{Number(調査.scannedSourceFiles || 0).toLocaleString()}} / {{Number(調査.sourceTargetFiles).toLocaleString()}} 件 · {{項目.length}} 項目 · {{String(調査.commit || '').slice(0,8)}}。通常の Markdown 本文・画像・音声・モデル等は除外。</p><p v-else>ソース調査情報は接続後に表示します。</p>対象はこの診断サーバーの実行環境です。存在確認は動作・認証・接続の保証ではありません。</footer>
</template>
