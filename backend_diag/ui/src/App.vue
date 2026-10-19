<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue';
import 導入状況パネル from './導入状況/導入状況パネル.vue';
import { 導入状況状態を作成 } from './導入状況/導入状況状態.mjs';
import モデル一覧パネル from './モデル一覧/モデル一覧パネル.vue';
import 外部連携パネル from './外部連携/外部連携パネル.vue';
import { キー設定状態を作成 } from './キー設定共通/キー設定状態.mjs';
import 設定モデルパネル from './設定モデル/設定モデルパネル.vue';
import { 設定モデル状態を作成 } from './設定モデル/設定モデル状態.mjs';
import AIモデルパネル from './AIモデル/AIモデルパネル.vue';
import {AIモデル状態を作成} from './AIモデル/AIモデル状態.mjs';
import ステータスバー from './ウィンドウ/ステータスバー.vue';
import {Tools接続を作成} from './ウィンドウ/Tools接続.mjs';
import アプリ起動パネル from './アプリ起動/アプリ起動パネル.vue';
import {アプリ状態を作成} from './アプリ起動/アプリ状態.mjs';
import 起動パネル from './起動/起動パネル.vue';
import {起動状態を作成} from './起動/起動状態.mjs';
import 起動ミニパネル from './起動/起動ミニパネル.vue';
import {起動ミニ表示を作成} from './ウィンドウ/起動ミニ表示.mjs';
const tab=ref('start'), key=ref(new URLSearchParams(location.hash.slice(1)).get('token') || ''), input=ref('');
if(location.hash) history.replaceState(null,'',location.pathname+location.search);
const connected=ref(false),connecting=ref(false);
const message=ref('ローカル環境の外部プログラムを確認します。');
const { 前回実行日時, 確認中, 確認済み, 書込中, 書込済み, 表示中, 項目, 結果, 調査, 一覧を反映, 状況確認, 書込, 全テスト } = 導入状況状態を作成({ api, 接続済み: connected, 通知: message });
const { modelLastRun,integrationLastRun,keyData,keyBusy,keyTesting,keyResults,latestBusy,modelWriteBusy,modelWritten,integrationBusy,integrationWriteBusy,integrationWritten,publicModels,publicBusy,loadKeys,testKey,一覧再取得,モデル書込,外部連携確認,外部連携書込,refreshPublic,resetPublic,設定を破棄,終了 } = キー設定状態を作成({ api, connected, message });
const toolsOnline=ref(false),toolsChecking=ref(false);
const tools=Tools接続を作成({api,反映:state=>{toolsOnline.value=state.online;toolsChecking.value=state.checking;}});
const 起動=起動状態を作成({api});
const アプリ=アプリ状態を作成({api});
const ミニ=起動ミニ表示を作成({利用可能:()=>['start','apps'].includes(tab.value)&&connected.value,初期表示:globalThis.window?.aidiyWindow?.initialMini===true&&globalThis.performance?.getEntriesByType('navigation')[0]?.type!=='reload'});
const {表示中:ミニ表示}=ミニ;
watch([tab,connected,ミニ表示],([value,online,mini])=>{起動.表示((value==='start'||value==='apps'&&mini)&&online,!mini);if(!['start','apps'].includes(value)||!online)void ミニ.変更(false);});
watch(ミニ.エラー,error=>{if(error)message.value=error;});
function コンソールへ戻る(id){起動.選択.value=id;tab.value='start';void ミニ.変更(false);}
const 手動=AIモデル状態を作成({api,接続可能:()=>connected.value&&toolsOnline.value});
watch(tab,(value,old)=>{if(old==='manual')手動.表示を離れる();if(old==='trials')試行.表示を離れる();},{flush:'sync'});
const 試行=設定モデル状態を作成({api,接続可能:()=>connected.value&&toolsOnline.value});
const {設定:試行設定,結果:試行結果,読込中:試行読込中,実行中:試行実行中,選択:試行選択,通知:試行通知,音声状態:試行音声}=試行;
watch(connected,value=>tools.接続(value));
watch(()=>connected.value&&toolsOnline.value,value=>{if(!value){試行.切断();手動.中止();}else if(tab.value==='trials')void 試行.読込();else if(tab.value==='manual')void 手動.読込();},{flush:'sync'});
onUnmounted(()=>{手動.終了();試行.終了();終了();tools.終了();起動.終了();void ミニ.変更(false);});
async function api(path,method='GET',signal,format='json',body) {
 const response=await fetch(new URL(path,location.href),{method,signal,headers:{Authorization:`Bearer ${key.value}`,...(body!==undefined?{'Content-Type':'application/json'}:{})},...(body!==undefined?{body:JSON.stringify(body)}:{}),cache:'no-store',credentials:'same-origin'});
 if(response.ok && format==='blob')return response.blob();
 const data=await response.json();
 if(!response.ok){if(response.status===401){設定を破棄();key.value='';connected.value=false;}throw new Error(data.エラー || '通信に失敗しました。');}
 return data;
}
async function connect(){if(connecting.value)return;connecting.value=true;try{const data=await api('api/一覧');一覧を反映(data);resetPublic();connected.value=true;message.value='';if(tab.value==='keys'||tab.value==='integrations')await loadKeys();}catch(error){message.value=error.message;void ミニ.変更(false);}finally{connecting.value=false;}}
function submit(){if(connecting.value)return;key.value=input.value.trim();input.value='';connect();}
// 全テスト: 状況確認→書込、続けて一覧再取得→モデル情報の書込。
// 実行中の処理に合わせて、導入状況→モデル一覧→外部連携の順に表示タブを切り替え、終わったら導入状況タブへ戻す。
async function 全診断(){tab.value='install';if(!await 全テスト())return;tab.value='keys';await 一覧再取得();await モデル書込();tab.value='integrations';await 外部連携確認({再読込:false});await 外部連携書込();tab.value='install';}
async function changeTab(value){if(['trials','manual'].includes(value)&&(!connected.value||!toolsOnline.value))return;tab.value=value;if(value==='start'||value==='apps')return;if(value==='manual'){if(!手動.一覧.value)await 手動.読込();return;}if(value==='trials'){if(!試行設定.value)await 試行.読込();}else if(value!=='install' && !keyData.value)await loadKeys();}
onMounted(()=>{if(key.value)connect();});
</script>
<template>
<component :is="ステータスバー" :online="toolsOnline" :enabled="true" :checking="toolsChecking" :connected="connected" :compact="ミニ表示" @restore="ミニ.変更(false)"/>
<nav class="tabs" v-show="!ミニ表示" aria-label="診断の種類"><button :aria-pressed="tab==='install'" :class="{active:tab==='install'}" @click="changeTab('install')">導入状況</button><button :aria-pressed="tab==='keys'" :class="{active:tab==='keys'}" @click="changeTab('keys')">モデル一覧</button><button :aria-pressed="tab==='integrations'" :class="{active:tab==='integrations'}" @click="changeTab('integrations')">外部連携</button><button :aria-pressed="tab==='trials'" :class="{active:tab==='trials'}" :disabled="!connected || !toolsOnline" title="Tools 接続時に利用できます" @click="changeTab('trials')">設定モデル</button><button :aria-pressed="tab==='manual'" :class="{active:tab==='manual'}" :disabled="!connected || !toolsOnline" @click="changeTab('manual')">AIモデル</button><button :aria-pressed="tab==='start'" :class="{active:tab==='start'}" @click="changeTab('start')">システム起動</button><button :aria-pressed="tab==='apps'" :class="{active:tab==='apps'}" @click="changeTab('apps')">アプリ起動</button><button id="run" class="run-all" v-show="tab!=='apps'" :disabled="tab==='start'?(!connected||起動.読込中.value||起動.保存中.value||起動.処理中.value||起動.起動中.value):!connected || 確認中 || 書込中 || latestBusy || modelWriteBusy || integrationBusy || integrationWriteBusy || (tab==='manual' && (!toolsOnline || 手動.実行中.value || 手動.読込中.value || !手動.一覧.value))" @click="tab==='start'?起動.再起動():tab==='manual'?手動.開始(true):全診断()" :title="tab==='start'?'選択した機能を_start.pyの順に再起動します':tab==='manual'?'Chat→Live→Decision→Codeを順に試行します':'導入状況・モデル一覧・外部連携を順に確認し、結果を書き込みます'">{{tab==='start'?(起動.起動中.value?'起動中…':'設定起動'):tab==='manual'?(手動.実行中.value?'実行中…':'一括試行'):確認中 || integrationBusy ? '確認中…' : 書込中 || modelWriteBusy || integrationWriteBusy ? '書込中…' : latestBusy ? '取得中…' : '全テスト'}}</button></nav>
<section v-if="!connected&&!ミニ表示" id="login" class="login"><label for="token">起動したターミナルの認証 URL を開くか、認証キーを入力してください。</label><form @submit.prevent="submit"><input id="token" v-model="input" :disabled="connecting" type="password" autocomplete="off" placeholder="起動中のみ有効な認証キー"><button id="connect" :disabled="connecting">接続</button></form></section>
<p v-if="message" id="message" role="status" aria-live="polite" v-show="!ミニ表示">{{message}}</p>
<component :is="導入状況パネル" :last-run="前回実行日時" v-show="tab==='install'" :項目="項目" :結果="結果" :確認中="確認中" :接続済み="connected" :確認済み="確認済み" :書込中="書込中" :書込済み="書込済み" :表示中="表示中" @確認="状況確認" @書込="書込"/>
<component :is="モデル一覧パネル" :last-run="modelLastRun" v-show="tab==='keys'" :data="keyData" :results="keyResults" :loading="keyBusy" :testing="keyTesting" :connected="connected" :public-models="publicModels" :public-busy="publicBusy" :latest-busy="latestBusy" :write-busy="modelWriteBusy" :written="modelWritten" @latest="一覧再取得" @write="モデル書込" @refresh-public="refreshPublic" @test="testKey"/>
<component :is="外部連携パネル" :last-run="integrationLastRun" v-show="tab==='integrations'" :data="keyData" :results="keyResults" :loading="keyBusy" :testing="keyTesting" :connected="connected" :busy="integrationBusy" :write-busy="integrationWriteBusy" :written="integrationWritten" @check="外部連携確認" @write="外部連携書込" @test="testKey"/>
<component :is="設定モデルパネル" v-show="tab==='trials'" :data="試行設定" :results="試行結果" :loading="試行読込中" :running="試行実行中" :selected="試行選択" :online="connected && toolsOnline" :message="試行通知" :audio-states="試行音声" :visible="tab==='trials'" @audio-load="試行.音声読込" @audio-error="試行.音声再生失敗" @refresh="試行.読込" @start="試行.開始()" @test="試行.個別開始($event)" @cancel="試行.中止()" @select="試行選択=$event"/>
<component :is="AIモデルパネル" v-show="tab==='manual'" :state="手動" :online="connected && toolsOnline" :visible="tab==='manual'"/>
<component :is="アプリ起動パネル" :state="アプリ" :online="connected" :visible="tab==='apps'&&!ミニ表示" @mini="ミニ.変更(true)"/>
<component :is="起動パネル" :state="起動" :online="connected" :visible="tab==='start'&&!ミニ表示" @mini="ミニ.変更(true)"/>
<component v-if="ミニ表示&&['start','apps'].includes(tab)" :is="起動ミニパネル" :app-state="アプリ" :app-online="connected" :state="起動" :online="connected&&!起動.更新失敗.value" @select="コンソールへ戻る"/>
<footer v-show="!ミニ表示"><div class="diag-meta"><span>診断 {{connected?'接続済み':'未接続'}}</span><span>tools {{toolsOnline?'オンライン':'オフライン'}}</span></div><p id="coverage" v-if="調査.sourceTargetFiles">調査{{調査.complete ? '完了':'途中'}}: 対象ソース・設定 {{Number(調査.scannedSourceFiles || 0).toLocaleString()}} / {{Number(調査.sourceTargetFiles).toLocaleString()}} 件 · {{項目.length}} 項目 · {{String(調査.commit || '').slice(0,8)}}。通常の Markdown 本文・画像・音声・モデル等は除外。</p><p v-else>ソース調査情報は接続後に表示します。</p>対象はこの診断サーバーの実行環境です。存在確認は動作・認証・接続の保証ではありません。</footer>
</template>
