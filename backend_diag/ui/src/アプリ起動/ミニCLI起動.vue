<script setup>
import {computed,watch} from 'vue';
const props=defineProps({state:Object,appState:Object,online:Boolean});
watch(()=>props.online,value=>{if(value)void props.state.読込();else props.state.切断();},{immediate:true});
const 外部CLI=computed(()=>props.state.項目.value.filter(item=>item.id!=='aidiy_hermes'));
</script>
<template>
<section v-if="外部CLI.length" class="mini-cli-launch" aria-label="CLI起動">
 <div class="mini-cli-buttons">
  <button v-for="item in 外部CLI" :key="item.id" class="mini-cli-button" :data-cli="item.id" :aria-label="item.名前+' をTermで起動（'+item.モード+'）'" :title="item.名前+' / '+item.モード+' / モデル指定なし / 複数起動可'+(appState.フォルダ.value?' — '+appState.フォルダ.value:' — プロジェクト選択してね')" :disabled="!online||!appState.フォルダ.value||!!appState.処理中.value&&!appState.処理中.value.startsWith('cli:')||appState.選択中.value" @click="state.起動(item.id,{確認省略:true})"><span class="mini-icon-frame"><img :src="'CLI_'+item.id+'.svg'" alt="" width="40" height="40"></span></button>
 </div>
</section>
</template>
