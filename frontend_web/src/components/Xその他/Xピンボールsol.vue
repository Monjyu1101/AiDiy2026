<!--
  -*- coding: utf-8 -*-
  COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
  Licensed under "AiDiy 公開利用ライセンス v1.1".
-->
<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const baseUrl = import.meta.env.BASE_URL || '/'
const frameSrc = `${baseUrl}Xピンボールsol/index.html`
const route = useRoute()
const router = useRouter()
const 戻URL = computed(() => {
  const value = Array.isArray(route.query.戻URL) ? route.query.戻URL[0] : route.query.戻URL
  return value ? String(value) : ''
})
const 戻る = () => {
  if (戻URL.value) router.push(戻URL.value.replace(/？/g, '?').replace(/＆/g, '&').replace(/＝/g, '='))
}
</script>

<template>
  <div class="page-container">
    <h2 class="page-title">
      <span>【 Xピンボールsol 】</span>
      <button v-if="戻URL" @click="戻る">戻る</button>
    </h2>
    <div class="iframe-wrapper">
      <iframe class="game-frame" :src="frameSrc" title="Xピンボールsol" allow="autoplay; fullscreen"></iframe>
    </div>
  </div>
</template>

<style scoped>
.page-container { width: 100%; height: 100%; min-height: 620px; display: flex; flex-direction: column; background: #04020b; }
.page-title { height: 35px; min-height: 35px; margin: 0 0 5px; padding: 8px 20px 8px 40px; display: flex; align-items: center; color: #ffe3a4; font-size: 14px; background: linear-gradient(90deg, #160817, #351122, #10152c); box-shadow: 0 2px 12px rgba(255, 77, 24, .25); }
.page-title span { flex: 1; }
.page-title button { border: 1px solid #ff7538; background: #2b101d; color: #fff0d2; cursor: pointer; padding: 3px 12px; }
.page-title button:hover { background: #5a1821; box-shadow: 0 0 10px #ff5d2e; }
.iframe-wrapper { width: 100%; flex: 1; min-height: 585px; }
.game-frame { display: block; width: 100%; height: 100%; border: 0; }
</style>
