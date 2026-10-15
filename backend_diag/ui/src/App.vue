<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue';
import インストールパネル from './インストール/インストールパネル.vue';
import { インストール状態を作成 } from './インストール/インストール状態.mjs';
import モデルキー設定パネル from './モデルキー設定/モデルキー設定パネル.vue';
import 外部連携設定パネル from './外部連携設定/外部連携設定パネル.vue';
import { キー設定状態を作成 } from './キー設定共通/キー設定状態.mjs';
import ステータスバー from './ウィンドウ/ステータスバー.vue';
import {Tools接続を作成} from './ウィンドウ/Tools接続.mjs';
const tab=ref('install'), key=ref(new URLSearchParams(location.hash.slice(1)).get('token') || ''), input=ref('');
if(location.hash) history.replaceState(null,'',location.pathname+location.search);
const connected=ref(false),connecting=ref(false);
const message=ref('ローカル環境の外部プログラムを確認します。');
const { 確認中, 項目, 結果, 調査, 一覧を反映, インストール確認 } = インストール状態を作成({ api, 接続済み: connected, 通知: message });
const { keyData,keyBusy,keyTesting,keyResults,publicModels,publicBusy,loadKeys,testKey,refreshPublic,resetPublic,設定を破棄,終了 } = キー設定状態を作成({ api, connected, message });
const toolsOnline=ref(false),toolsChecking=ref(false),toolsEnabled=ref(true);
const tools=Tools接続を作成({api,反映:state=>{toolsOnline.value=state.online;toolsChecking.value=state.checking;}});
watch(connected,value=>tools.接続(value));
watch(toolsEnabled,value=>tools.有効(value));
onUnmounted(()=>{終了();tools.終了();});
async function api(path,method='GET',signal) {
 const response=await fetch(new URL(path,location.href),{method,signal,headers:{Authorization:`Bearer ${key.value}`},cache:'no-store',credentials:'same-origin'});
 const data=await response.json();
 if(!response.ok){if(response.status===401){設定を破棄();key.value='';connected.value=false;}throw new Error(data.エラー || '通信に失敗しました。');}
 return data;
}
async function connect(){if(connecting.value)return;connecting.value=true;try{const data=await api('api/一覧');一覧を反映(data);resetPublic();connected.value=true;message.value=`インストール確認: ${項目.value.length} 件。ボタンで、このサーバーの実行環境を確認します。`;if(tab.value!=='install')await loadKeys();}catch(error){message.value=error.message;}finally{connecting.value=false;}}
function submit(){if(connecting.value)return;key.value=input.value.trim();input.value='';connect();}
async function changeTab(value){tab.value=value;if(value!=='install' && !keyData.value)await loadKeys();}
onMounted(()=>{if(key.value)connect();});
</script>
<template>
<ステータスバー :online="toolsOnline" :enabled="toolsEnabled" :checking="toolsChecking" :connected="connected"/>
<div class="component-toolbar"><span>環境診断</span><nav><button class="tools-toggle" role="switch" :aria-checked="toolsEnabled" @click="toolsEnabled=!toolsEnabled">tools接続確認 {{toolsEnabled?'ON':'OFF'}}</button><button :disabled="!connected || !toolsEnabled || toolsChecking" @click="tools.refresh">再確認</button><button id="run" :disabled="!connected || 確認中" @click="インストール確認" title="現在の対象はインストール確認のみ">{{確認中 ? '確認中…' : '全テスト'}}</button></nav></div>
<nav class="tabs" aria-label="診断の種類"><button :aria-pressed="tab==='install'" :class="{active:tab==='install'}" @click="changeTab('install')">インストール</button><button :aria-pressed="tab==='keys'" :class="{active:tab==='keys'}" @click="changeTab('keys')">モデルキー設定</button><button :aria-pressed="tab==='integrations'" :class="{active:tab==='integrations'}" @click="changeTab('integrations')">外部連携設定</button><span>全テストの対象: インストール確認のみ</span></nav>
<section v-if="!connected" id="login" class="login"><label for="token">起動したターミナルの認証 URL を開くか、認証キーを入力してください。</label><form @submit.prevent="submit"><input id="token" v-model="input" :disabled="connecting" type="password" autocomplete="off" placeholder="起動中のみ有効な認証キー"><button id="connect" :disabled="connecting">接続</button></form></section>
<p v-if="message" id="message" role="status" aria-live="polite">{{message}}</p>
<component :is="インストールパネル" v-show="tab==='install'" :項目="項目" :結果="結果" :確認中="確認中" :接続済み="connected" @確認="インストール確認"/>
<component :is="モデルキー設定パネル" v-show="tab==='keys'" :data="keyData" :results="keyResults" :loading="keyBusy" :testing="keyTesting" :connected="connected" :public-models="publicModels" :public-busy="publicBusy" @refresh="loadKeys" @refresh-public="refreshPublic" @test="testKey"/>
<component :is="外部連携設定パネル" v-show="tab==='integrations'" :data="keyData" :results="keyResults" :loading="keyBusy" :testing="keyTesting" :connected="connected" @refresh="loadKeys"/>
<footer><div class="diag-meta"><span>診断 {{connected?'接続済み':'未接続'}}</span><span>tools {{!toolsEnabled?'確認OFF':toolsOnline?'オンライン':'オフライン'}}</span></div><p id="coverage" v-if="調査.sourceTargetFiles">調査{{調査.complete ? '完了':'途中'}}: 対象ソース・設定 {{Number(調査.scannedSourceFiles || 0).toLocaleString()}} / {{Number(調査.sourceTargetFiles).toLocaleString()}} 件 · {{項目.length}} 項目 · {{String(調査.commit || '').slice(0,8)}}。通常の Markdown 本文・画像・音声・モデル等は除外。</p><p v-else>ソース調査情報は接続後に表示します。</p>対象はこの診断サーバーの実行環境です。存在確認は動作・認証・接続の保証ではありません。</footer>
</template>
