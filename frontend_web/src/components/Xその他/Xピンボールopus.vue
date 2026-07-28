<!--
  -*- coding: utf-8 -*-
  COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
  Licensed under "AiDiy 公開利用ライセンス v1.1".
-->
<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const baseUrl = import.meta.env.BASE_URL || '/'
const frameSrc = `${baseUrl}Xピンボールopus/index.html`
const route = useRoute()
const router = useRouter()
const URLメニュー = computed(() => {
  const value = Array.isArray(route.query.URLメニュー) ? route.query.URLメニュー[0] : route.query.URLメニュー
  return value ? String(value) : ''
})
const URL戻り先 = computed(() => {
  const value = Array.isArray(route.query.URL戻り先) ? route.query.URL戻り先[0] : route.query.URL戻り先
  return value ? String(value) : ''
})
const toHalfwidthUrl = (value: string) => value.replace(/／/g, '/').replace(/？/g, '?').replace(/＆/g, '&').replace(/＝/g, '=')
const メニュー = () => {
  if (URLメニュー.value) router.push(toHalfwidthUrl(URLメニュー.value))
}
const 戻る = () => {
  if (URL戻り先.value) router.push(toHalfwidthUrl(URL戻り先.value))
}
</script>

<template>
  <div class="page-container">
    <h2 class="page-title">
      <span>【 Xピンボールopus 】</span>
      <div class="header-actions">
        <button v-if="URLメニュー" @click="メニュー">メニュー</button>
        <button v-if="URL戻り先 && URL戻り先 !== URLメニュー" @click="戻る">戻る</button>
      </div>
    </h2>
    <div class="iframe-wrapper">
      <iframe class="game-frame" :src="frameSrc" title="Xピンボールopus" allow="autoplay; fullscreen"></iframe>
    </div>
  </div>
</template>

<style scoped>
.page-container { width: 100%; height: 100%; min-height: min(620px, 100dvh); display: flex; flex-direction: column; background: #120c07; }
.page-title { height: 35px; min-height: 35px; margin: 0 0 5px; padding: 8px 20px 8px 40px; display: flex; align-items: center; color: #ffe6ba; font-size: 14px; background: linear-gradient(90deg, #160e08, #4b2b13, #112c35); box-shadow: 0 2px 12px rgba(201, 136, 74, .3); }
.page-title span { flex: 1; }
.header-actions { display: flex; align-items: center; gap: 8px; }
.page-title button { border: 1px solid #d99a57; background: #29180c; color: #fff0d2; cursor: pointer; padding: 3px 12px; }
.page-title button:hover { background: #573117; box-shadow: 0 0 10px #e0a35c; }
.iframe-wrapper { width: 100%; flex: 1; min-height: min(585px, calc(100dvh - 40px)); }
.game-frame { display: block; width: 100%; height: 100%; border: 0; }

@media (max-height: 520px) {
  .page-container { min-height: 360px; }
  .iframe-wrapper { min-height: 320px; }
}
</style>
