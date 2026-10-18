<script setup>
import {computed} from 'vue';
import './起動ミニ.css';
const props=defineProps({state:Object,online:Boolean});
defineEmits(['restore','select']);
const 稼働数=computed(()=>props.state.項目.value.filter(item=>item.状態==='稼働中').length);
function tone(state){return state==='稼働中'?'running':state==='エラー'?'error':['起動中','再起動中','確認中','再起動待ち','停止中'].includes(state)?'busy':'idle';}
</script>
<template>
<section class="panel start-mini" aria-label="起動ミニ表示">
 <div class="mini-heading"><div><h2>起動状況</h2><span role="status">{{online?`${稼働数} / ${state.項目.value.length} 稼働中`:'診断 未接続'}}</span></div><button @click="$emit('restore')" class="mini-restore">通常表示</button></div>
 <div class="mini-services">
  <button v-for="item in state.項目.value" :key="item.id" class="mini-service" :data-tone="online?tone(item.状態):'idle'" :aria-label="item.名前+' '+(online?item.状態:'未接続')+'。コンソールを表示'" @click="$emit('select',item.id)"><span class="mini-indicator" aria-hidden="true"></span><span class="mini-name">{{item.名前}}</span><span class="mini-state">{{online?item.状態:'未接続'}}</span></button>
 </div>
 <p class="mini-help">機能をクリックするとコンソールに戻ります。</p>
</section>
</template>
