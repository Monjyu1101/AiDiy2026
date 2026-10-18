<script setup>
import {ref,watch,nextTick} from 'vue';
import './起動.css';
const props=defineProps({state:Object,online:Boolean,visible:Boolean});
defineEmits(['mini']);
const consoleView=ref(),targetTabs=ref();
watch([()=>props.state.コンソール.value,()=>props.visible,()=>props.state.選択.value],async()=>{await nextTick();if(props.visible&&consoleView.value)consoleView.value.scrollTop=consoleView.value.scrollHeight;});
watch(()=>props.state.選択.value,async()=>{await nextTick();if(props.visible)targetTabs.value?.querySelector('.active')?.scrollIntoView({block:'nearest',inline:'nearest'});});
function tone(state){return state==='稼働中'?'running':state==='エラー'?'error':['起動中','再起動中','確認中','再起動待ち','停止中'].includes(state)?'busy':'idle';}
</script>
<template>
<section class="panel start-panel" v-show="visible" aria-label="起動管理">
 <div class="panel-heading"><div><h2>起動</h2><p>機能ごとに設定を保存し、右上の「設定起動」で順番に再起動します。</p></div><div class="start-view-actions"><span class="start-save" role="status">{{state.保存表示.value}}</span><button class="start-mini-switch" :disabled="!online||!state.項目.value.length" @click="$emit('mini')">ミニ表示</button></div></div>
 <nav ref="targetTabs" class="start-targets" aria-label="起動する機能">
  <button v-for="item in state.項目.value" :key="item.id" :class="{active:state.選択.value===item.id}" :aria-pressed="state.選択.value===item.id" @click="state.選択.value=item.id"><span class="start-dot" :data-tone="tone(item.状態)"></span>{{item.名前}}<span v-if="item.設定.起動対象" class="start-enabled" title="設定起動の対象">✓</span></button>
 </nav>
 <div v-if="state.読込中.value" class="start-empty">起動設定を読み込んでいます…</div>
 <div v-else-if="!state.選択対象.value" class="start-empty">診断に接続すると、起動する機能を設定できます。</div>
 <template v-else>
  <div class="start-settings">
   <label v-for="(value,key) in state.選択対象.value.設定" :key="key"><input type="checkbox" :checked="value" :disabled="!online||state.保存中.value" @change="state.設定変更(state.選択.value,key,$event.target.checked)">{{key==='ブラウザ表示'?'ブラウザで開く':key}}</label>
   <span class="start-path">{{state.選択対象.value.フォルダ}}/_start.py</span>
  </div>
  <p v-if="state.選択.value==='web'" class="start-help">「ブラウザで開く」がオンの場合、HTTP 応答が20秒間安定してから chrome_devtools で開きます。Tools / MCP の起動が必要です。</p>
  <div class="start-console-heading"><strong>{{state.選択対象.value.名前}} コンソール</strong><span class="start-status" :data-tone="tone(state.選択対象.value.状態)">{{state.選択対象.value.状態}}</span><div class="start-console-actions"><button :disabled="!online||state.保存中.value||state.処理中.value||state.起動中.value" @click="state.再起動(state.選択.value)">再起動</button><button :disabled="!online||state.処理中.value" @click="state.停止()">停止（Ctrl+C）</button></div></div>
  <pre ref="consoleView" class="start-console" tabindex="0" role="log" :aria-label="state.選択対象.value.名前+' のログ。文字を選択してコピーできます'">{{state.コンソール.value}}</pre>
  <p class="start-help">ログを選択して Ctrl+C（Mac は ⌘C）でコピー。停止ボタンから Ctrl+C を送信します。設定変更は自動保存されます。</p>
 </template>
 <p v-if="state.通知.value" class="start-message" role="status">{{state.通知.value}}</p>
</section>
</template>
