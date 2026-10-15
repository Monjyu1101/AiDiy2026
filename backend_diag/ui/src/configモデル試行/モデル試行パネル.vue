<script setup>
import { computed } from 'vue';
import { 再生可能な音声 } from './モデル試行音声.mjs';
import 状態バッジ from '../共通表示/状態バッジ.vue';
import './モデル試行.css';
const props=defineProps(['data','results','loading','running','selected','online','message','audioStates','visible']);
defineEmits(['refresh','start','cancel','select','audio-load','audio-error']);
const items=computed(()=>props.data?.項目||[]);
const row=computed(()=>items.value.find(item=>item.id===props.selected));
const result=computed(()=>props.results?.[props.selected]);
const audio=computed(()=>row.value?.id==='LIVE'?再生可能な音声(result.value):null);
const audioState=computed(()=>props.audioStates?.[audio.value?.id]);
const 状態=item=>props.results?.[item.id]?.状態 || (item.状態==='未実行'?'未実施':item.状態) || '未実施';
const 名前=item=>`${item.区分 || item.id}${item.役割 ? ` / ${item.役割}` : ''}`;
</script>
<template>
<section class="panel model-trial-panel" aria-label="configモデル試行">
 <div class="panel-heading"><h2>configモデル試行</h2><div class="panel-actions"><button :disabled="!online || loading || running" @click="$emit('refresh')">設定を再読込</button><button id="model-trial-start" :disabled="!online || loading || running || !items.length" @click="$emit('start')">順番に試行</button><button :disabled="!running" @click="$emit('cancel')">中止</button></div></div>
 <p class="panel-note">設定中のモデルで短い応答を確認します。試行は料金が発生する場合があります。同じ実効モデルの成功結果はサーバーで共有します。</p>
 <p v-if="!online" class="panel-note warning" role="status">Tools 接続時に利用できます。</p>
 <p v-else-if="message" class="panel-note" role="status" aria-live="polite">{{message}}</p>
 <main class="trial-layout"><aside aria-label="設定モデル一覧"><p v-if="loading">設定を読込中…</p><p v-else-if="!items.length">設定項目がありません。設定を再読込してください。</p>
  <button v-for="item in items" :key="item.id" class="trial-row" :class="{selected:selected===item.id}" :aria-pressed="selected===item.id" @click="$emit('select',item.id)"><span class="trial-row-title"><strong>{{名前(item)}}</strong><component :is="状態バッジ" :state="状態(item)"/></span><span class="trial-model">{{item.プロバイダ || '未設定'}} / {{item.モデル || '未設定'}}</span><span v-if="results?.[item.id]?.共有元" class="trial-share">共有元: {{results[item.id].共有元}}</span></button>
 </aside><article aria-live="polite"><template v-if="row"><span class="eyebrow">configモデル試行 / {{row.id}}</span><h2>{{名前(row)}}</h2><component :is="状態バッジ" class="status" :state="状態(row)"/><dl><dt>プロバイダ</dt><dd>{{row.プロバイダ || '未設定'}}</dd><dt>設定モデル</dt><dd>{{row.モデル || '未設定'}}</dd><dt>確認経路</dt><dd>{{row.id==='LIVE'?'Tools 内部 HTTP（Live）':'Tools MCP'}}</dd><template v-if="row.音声"><dt>音声</dt><dd>{{row.音声}}</dd></template><template v-if="row.継承元"><dt>設定の継承元</dt><dd>{{row.継承元}}</dd></template><dt>結果</dt><dd>{{result?.説明 || row.説明 || '未実施'}}</dd><template v-if="result?.実行モデル"><dt>実行モデル</dt><dd>{{result.実行モデル}}</dd></template><template v-if="result?.共有元"><dt>共有元</dt><dd>{{result.共有元}}（同じ実効モデルの成功結果）</dd></template><template v-if="result?.所要ms!=null"><dt>所要時間</dt><dd>{{result.所要ms}} ms</dd></template></dl><h3>応答</h3><pre class="trial-reply">{{String(result?.応答 || '応答はまだありません。').slice(0,4000)}}</pre><section v-if="audio" class="trial-audio" aria-label="Live 応答音声"><h3>応答音声（{{(audio.長さms/1000).toFixed(2)}} 秒）</h3><p>一時保存した音声です。再生ボタンで確認できます。</p><audio v-if="audioState?.url && visible!==false" :key="audio.id" :src="audioState.url" controls preload="none" aria-label="Live 応答音声の再生" @error="$emit('audio-error',audio.id)"></audio><button v-if="!audioState?.url" :disabled="!online || audioState?.読込中" @click="$emit('audio-load',result)">{{audioState?.読込中?'音声を読込中…':'音声を読み込む'}}</button><p v-if="audioState?.エラー" class="warning" role="status">{{audioState.エラー}}</p></section></template><div v-else class="welcome"><h2>設定モデルの試行</h2><p>一覧から選択して詳細を確認できます。「順番に試行」で開始します。</p></div></article></main>
 <details class="test-notes"><summary>試行について</summary><p>Chat・Code・Task・Team は MCP、Live は Tools 内部 HTTP を使います。診断サーバー経由で確認し、API キーは画面に送信しません。起動時や「全テスト」では試行しません。未設定・未対応は成功扱いにしません。設定変更や切断後は再読込して試行してください。</p><p>中止後も、サービス側ですでに開始した処理や料金は取り消せない場合があります。</p></details>
</section>
</template>
