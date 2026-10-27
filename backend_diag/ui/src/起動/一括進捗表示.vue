<script setup>
import {computed} from 'vue';
import './一括進捗表示.css';
const props=defineProps({state:Object,compact:Boolean});
const 進捗=computed(()=>props.state.進捗表示.value);
const 見出し=computed(()=>{
 const label=進捗.value?.種別==='stop'?'強制停止':'一括起動';
 return label+(進捗.value?.状態==='running'?'中…':進捗.value?.状態==='error'?'を確認してください':'完了');
});
</script>
<template>
<section v-if="進捗" class="batch-progress" :class="{compact}" :data-state="進捗.状態" role="region" aria-label="システム起動の進行状況">
 <div class="batch-progress-message" role="status" aria-live="polite" aria-atomic="true">
  <strong><span v-if="進捗.状態==='running'" class="batch-progress-spinner" aria-hidden="true"></span>{{見出し}}</strong>
  <span>{{進捗.通知}}</span>
  <small v-if="state.更新失敗.value">状態を再確認しています。処理の停止は確認されていません。</small>
 </div>
 <small v-if="!compact" class="batch-progress-hint">タブを切り替えても処理は続きます。</small>
 <button v-if="進捗.状態!=='running'" type="button" aria-label="進行状況を閉じる" @click="state.進捗を閉じる()">閉じる</button>
</section>
</template>
