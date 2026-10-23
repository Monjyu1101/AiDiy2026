<script setup>
import {起動モーション} from './起動モーション.mjs';
import './起動モーション.css';
import {computed,watch} from 'vue';
const props=defineProps({state:Object,appState:Object,online:Boolean});
watch(()=>props.online,value=>{if(value)void props.state.読込();else props.state.切断();},{immediate:true});
const 外部CLI=computed(()=>props.state.項目.value.filter(item=>item.id!=='aidiy_hermes'));
</script>
<template>
<section v-if="外部CLI.length" class="mini-cli-launch" aria-label="外部アプリ・CLI起動">
 <div class="mini-cli-buttons">
  <button v-for="item in 外部CLI" :key="item.id" class="mini-cli-button" :data-cli="item.id" :aria-label="item.種類==='editor'?item.名前+' でフォルダを開く':item.名前+' をTermで起動（'+item.モード+'）'" :title="item.名前+' / '+item.モード+(item.種類==='editor'?'':' / モデル指定なし')+' / 複数起動可'+(appState.フォルダ.value?' — '+appState.フォルダ.value:' — プロジェクト選択してね')" :disabled="!online||!appState.フォルダ.value||!!appState.処理中.value&&!appState.処理中.value.startsWith('cli:')||appState.選択中.value" @click="state.起動(item.id,{確認省略:true,開始時:起動モーション($event)})"><span class="mini-icon-frame"><span class="launch-frame launch-frame-40" aria-hidden="true"><img :src="'CLI_'+item.id+'.svg'" alt="" width="40" height="40"><svg class="launch-trace" viewBox="0 0 100 100" focusable="false"><rect class="launch-trace-light" x="2" y="2" width="96" height="96" rx="5" pathLength="100" /></svg></span></span></button>
 </div>
</section>
</template>
