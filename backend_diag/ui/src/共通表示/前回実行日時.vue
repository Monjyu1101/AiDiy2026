<script setup>
import { computed } from 'vue';
const props=defineProps(['value']);
const 表示=computed(()=>{
  const date=new Date(props.value);
  return props.value && Number.isFinite(date.getTime()) ? date.toLocaleString('ja-JP',{year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false}) : '未実行';
});
</script>
<template><span class="previous-run" aria-live="polite">[前回実行日時: <time v-if="value" :datetime="value">{{表示}}</time><template v-else>{{表示}}</template>]</span></template>
