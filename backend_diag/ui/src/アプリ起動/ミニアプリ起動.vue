<script setup>
import {computed,ref,watch} from 'vue';
import {アプリアイコン} from './アプリアイコン.mjs';
const props=defineProps({state:Object,cliState:Object,online:Boolean});
const 最後の対象=ref('');
const Hermes=computed(()=>props.cliState?.項目.value.find(item=>item.id==='aidiy_hermes'));
watch(()=>props.online,value=>{if(value)void props.state.読込();},{immediate:true});
const 結果=computed(()=>props.state.結果.value[最後の対象.value]);
// 未選択の案内は英語で右端から左端へ流す（通常画面の入力欄とボタンのtitleは日本語のまま）
const 未選択案内='SELECT YOUR PROJECT  ▸▸  READY FOR LAUNCH';
const 通知=computed(()=>!props.state.フォルダ.value?未選択案内:props.state.処理中.value?'起動確認中…':結果.value?.通知||props.state.フォルダ.value);
function 起動(id){最後の対象.value=id;void props.state.起動(id);}
</script>
<template>
<div class="mini-app-launch" aria-label="アプリ起動">
 <div class="mini-app-buttons">
  <button v-for="item in state.項目.value" :key="item.id" class="mini-app-button" :data-app="item.id" :aria-label="item.名前+' を起動'" :title="item.名前+' を起動'+(state.フォルダ.value?' — '+state.フォルダ.value:' — プロジェクト選択してね')" :disabled="!online||!state.フォルダ.value||!!state.処理中.value||state.選択中.value" @click="起動(item.id)"><span class="mini-icon-frame"><img :src="アプリアイコン[item.id]" alt="" width="36" height="36"></span><span class="mini-icon-caption">{{item.名前}}</span></button>
  <button v-if="Hermes" class="mini-app-button mini-hermes-button" data-cli="aidiy_hermes" :aria-label="Hermes.名前+' をTermで起動（'+Hermes.モード+'）'" :title="Hermes.名前+' / '+Hermes.モード+' / モデル指定なし'+(state.フォルダ.value?' — '+state.フォルダ.value:' — プロジェクト選択してね')" :disabled="!online||!state.フォルダ.value||!!state.処理中.value||state.選択中.value" @click="cliState.起動('aidiy_hermes')"><span class="mini-icon-frame"><img src="CLI_aidiy_hermes.png" alt="" width="36" height="36"></span><span class="mini-icon-caption">Hermes</span></button>
 </div>
 <p class="mini-app-message" :class="{required:!state.フォルダ.value,error:!!state.フォルダ.value&&結果?.種別==='error'}" role="status" :title="state.フォルダ.value?通知:'プロジェクト選択してね'"><span v-if="!state.フォルダ.value" class="mini-app-marquee">{{通知}}</span><template v-else>{{通知}}</template></p>
</div>
</template>
