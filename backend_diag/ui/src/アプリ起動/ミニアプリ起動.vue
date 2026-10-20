<script setup>
import {computed,ref,watch} from 'vue';
import {アプリアイコン} from './アプリアイコン.mjs';
const props=defineProps({state:Object,cliState:Object,online:Boolean});
defineEmits(['open-apps']);
const 最後の対象=ref('');
const Hermes=computed(()=>props.cliState?.項目.value.find(item=>item.id==='aidiy_hermes'));
watch(()=>props.online,value=>{if(value)void props.state.読込();},{immediate:true});
const 結果=computed(()=>props.state.結果.value[最後の対象.value]);
// 未選択の案内は英語で右端から左端へ流す（通常画面の入力欄とボタンのtitleは日本語のまま）
const 未選択案内='SELECT YOUR PROJECT  ▸▸  READY FOR LAUNCH';
const 通知=computed(()=>!props.state.フォルダ.value?未選択案内:props.state.処理中.value?'起動中…':結果.value?.種別==='error'?結果.value.通知:props.state.フォルダ.value);
function 起動(id){最後の対象.value=id;void props.state.起動(id);}
</script>
<template>
<div class="mini-app-launch" aria-label="アプリ起動">
 <div class="mini-app-buttons">
  <button v-for="item in state.項目.value" :key="item.id" class="mini-app-button" :data-app="item.id" :aria-label="item.名前+' を起動'" :title="item.名前+' を起動'+(state.フォルダ.value?' — '+state.フォルダ.value:' — プロジェクト選択してね')" :disabled="!online||!state.フォルダ.value||!!state.処理中.value||state.選択中.value" @click="起動(item.id)"><span class="mini-icon-frame"><img :src="アプリアイコン[item.id]" alt="" width="40" height="40"></span></button>
  <button v-if="Hermes" class="mini-app-button mini-hermes-button" data-cli="aidiy_hermes" :aria-label="Hermes.名前+' をTermで起動（'+Hermes.モード+'）'" :title="Hermes.名前+' / '+Hermes.モード+' / モデル指定なし / 複数起動可'+(state.フォルダ.value?' — '+state.フォルダ.value:' — プロジェクト選択してね')" :disabled="!online||!state.フォルダ.value||!!state.処理中.value&&!state.処理中.value.startsWith('cli:')||state.選択中.value" @click="cliState.起動('aidiy_hermes',{確認省略:true})"><span class="mini-icon-frame"><img src="CLI_aidiy_hermes.svg" alt="" width="40" height="40"></span></button>
 </div>
 <button v-if="!state.フォルダ.value" type="button" class="mini-app-message required mini-project-link" title="プロジェクト選択してね" aria-label="アプリ起動パネルでプロジェクトを選択" @click="$emit('open-apps')"><span class="mini-app-marquee">{{通知}}</span></button>
 <p v-else class="mini-app-message" :class="{error:結果?.種別==='error'}" role="status" :title="通知">{{通知}}</p>
</div>
</template>
