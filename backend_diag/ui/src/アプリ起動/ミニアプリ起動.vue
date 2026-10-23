<script setup>
import {起動モーション} from './起動モーション.mjs';
import './起動モーション.css';
import {computed,watch,ref,onBeforeUnmount} from 'vue';
import {アプリアイコン} from './アプリアイコン.mjs';
const props=defineProps({state:Object,cliState:Object,online:Boolean});
defineEmits(['open-apps']);
const Hermes=computed(()=>props.cliState?.項目.value.find(item=>item.id==='aidiy_hermes'));
watch(()=>props.online,value=>{if(value)void props.state.読込();},{immediate:true});
// 未選択の案内は英語で右端から左端へ流す（通常画面の入力欄とボタンのtitleは日本語のまま）
const 未選択案内='SELECT YOUR PROJECT  ▸▸  READY FOR LAUNCH';
// 文字を格子1マス（1.6px）ずつ送るため、流す距離をマス数で渡す。固定の格子の下を文字が移って見える。
const マーキー=ref(null);let 監視;
watch(マーキー,el=>{監視?.disconnect();if(!el)return;const 設定=()=>el.style.setProperty('--marquee-cells',String(Math.max(1,Math.round(el.offsetWidth/1.6))));設定();監視=new ResizeObserver(設定);監視.observe(el);});
onBeforeUnmount(()=>監視?.disconnect());
</script>
<template>
<div class="mini-app-launch" aria-label="アプリ起動">
 <div class="mini-app-buttons">
  <button v-for="item in state.項目.value" :key="item.id" class="mini-app-button" :data-app="item.id" :aria-label="item.名前+' を起動'" :title="item.名前+' を起動'+(state.フォルダ.value?' — '+state.フォルダ.value:' — プロジェクト選択してね')" :disabled="!online||!state.フォルダ.value||!!state.処理中.value||state.選択中.value" @click="state.起動(item.id,{開始時:起動モーション($event)})"><span class="mini-icon-frame"><span class="launch-frame launch-frame-40" aria-hidden="true"><img :src="アプリアイコン[item.id]" alt="" width="40" height="40"><svg class="launch-trace" viewBox="0 0 100 100" focusable="false"><rect class="launch-trace-light" x="2" y="2" width="96" height="96" rx="5" pathLength="100" /></svg></span></span></button>
  <button v-if="Hermes" class="mini-app-button mini-hermes-button" data-cli="aidiy_hermes" :aria-label="Hermes.名前+' をTermで起動（'+Hermes.モード+'）'" :title="Hermes.名前+' / '+Hermes.モード+' / モデル指定なし / 複数起動可'+(state.フォルダ.value?' — '+state.フォルダ.value:' — プロジェクト選択してね')" :disabled="!online||!state.フォルダ.value||!!state.処理中.value&&!state.処理中.value.startsWith('cli:')||state.選択中.value" @click="cliState.起動('aidiy_hermes',{確認省略:true,開始時:起動モーション($event)})"><span class="mini-icon-frame"><span class="launch-frame launch-frame-40" aria-hidden="true"><img src="CLI_aidiy_hermes.svg" alt="" width="40" height="40"><svg class="launch-trace" viewBox="0 0 100 100" focusable="false"><rect class="launch-trace-light" x="2" y="2" width="96" height="96" rx="5" pathLength="100" /></svg></span></span></button>
 </div>
 <button v-if="!state.フォルダ.value" type="button" class="mini-app-message required mini-project-link" title="プロジェクト選択してね" aria-label="アプリ起動パネルでプロジェクトを選択" @click="$emit('open-apps')"><span ref="マーキー" class="mini-app-marquee">{{未選択案内}}</span></button>
 <p v-else class="mini-app-message" :title="state.フォルダ.value">{{state.フォルダ.value}}</p>
</div>
</template>
