<script setup>
import {computed,watch} from 'vue';
const props=defineProps({state:Object,appState:Object,online:Boolean});
watch(()=>props.online,value=>{if(value)void props.state.読込();else props.state.切断();},{immediate:true});
const 外部CLI=computed(()=>props.state.項目.value.filter(item=>item.id!=='aidiy_hermes'));
const caption=item=>({claude:'Claude',codex:'Codex',copilot:'Copilot',agy:'Agy',grok:'Grok',opencode:'OpenCode',aidiy_hermes:'Hermes'})[item.id]||item.名前;
</script>
<template>
<section class="mini-cli-launch" aria-label="CLI起動">
 <div class="mini-cli-heading"><span>外部CLI · 自動承認</span><button :disabled="!online||state.読込中.value||!!state.処理中.value" @click="state.読込()" title="利用可能なCLIを再確認" aria-label="利用可能なCLIを再確認">↻</button></div>
 <div v-if="外部CLI.length" class="mini-cli-buttons">
  <button v-for="item in 外部CLI" :key="item.id" class="mini-cli-button" :data-cli="item.id" :aria-label="item.名前+' をTermで起動（'+item.モード+'）'" :title="item.名前+' / '+item.モード+' / モデル指定なし'+(appState.フォルダ.value?' — '+appState.フォルダ.value:' — プロジェクト選択してね')" :disabled="!online||!appState.フォルダ.value||!!appState.処理中.value||appState.選択中.value" @click="state.起動(item.id)"><span class="mini-icon-frame"><img :src="'CLI_'+item.id+'.png'" alt="" width="36" height="36"></span><span class="mini-icon-caption">{{caption(item)}}</span></button>
 </div>
 <p v-else class="mini-cli-empty">{{state.読込中.value?'CLIを確認中…':'利用可能な外部CLIなし'}}</p>
 <p v-if="state.通知.value||state.処理中.value" class="mini-cli-message" :class="{error:state.失敗.value}" :title="state.通知.value" role="status">{{state.処理中.value?'Term を起動確認中…':state.通知.value}}</p>
</section>
</template>
