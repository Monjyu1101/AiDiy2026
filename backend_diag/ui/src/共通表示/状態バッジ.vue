<script setup>
import { computed } from 'vue';
const props = defineProps({
  state: { type: String, default: '未確認' },
  label: { type: String, default: '' },
});
const tone = computed(() => ({ OK: 'success', 取得済: 'success', 未検出: 'warning', 注意: 'warning', NG: 'danger', ERR: 'danger', 失敗: 'danger', 取得中: 'pending', 確認中: 'pending', キャッシュ利用: 'cache', PASS: 'cache' })[props.state] || 'neutral');
const text = computed(() => props.label || props.state);
</script>

<template>
  <span class="badge" :data-state="state" :data-tone="tone" :aria-label="text">
    <span v-if="state==='確認中' || state==='取得中'" class="badge-spinner" aria-hidden="true"></span>
    <span class="badge-label">{{text}}</span>
  </span>
</template>
