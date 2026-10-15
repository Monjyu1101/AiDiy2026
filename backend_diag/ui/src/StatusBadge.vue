<script setup>
import { computed } from 'vue';
const props = defineProps({
  state: { type: String, default: '未確認' },
  label: { type: String, default: '' },
});
const tone = computed(() => ({ OK: 'success', 取得済: 'success', 未検出: 'warning', 注意: 'warning', NG: 'danger', ERR: 'danger', 失敗: 'danger', 取得中: 'pending' })[props.state] || 'neutral');
const text = computed(() => props.label || props.state);
</script>

<template>
  <span class="badge" :data-state="state" :data-tone="tone" :aria-label="text">
    <svg class="badge-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
      <template v-if="tone === 'success'"><circle cx="8" cy="8" r="6"/><path d="m5 8 2 2 4-4"/></template>
      <template v-else-if="tone === 'danger'"><circle cx="8" cy="8" r="6"/><path d="m6 6 4 4m0-4-4 4"/></template>
      <template v-else-if="tone === 'warning'"><path d="M7.1 2.8a1 1 0 0 1 1.8 0l5 9.2a1 1 0 0 1-.9 1.5H3a1 1 0 0 1-.9-1.5Z"/><path d="M8 6v3m0 2h.01"/></template>
      <template v-else-if="tone === 'pending'"><circle cx="8" cy="8" r="6"/><path d="M8 4.5V8l2 1.5"/></template>
      <circle v-else class="badge-neutral-dot" cx="8" cy="8" r="3.5"/>
    </svg>
    <span class="badge-label">{{text}}</span>
  </span>
</template>
