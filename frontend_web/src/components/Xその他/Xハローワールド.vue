<!--
  -*- coding: utf-8 -*-

  -------------------------------------------------------------------------
  COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
  Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
  Commercial use requires prior written consent from all copyright holders.
  See LICENSE for full terms. Thank you for keeping the rules.
  https://github.com/monjyu1101/AiDiy2026
  -------------------------------------------------------------------------
-->

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const baseUrl = import.meta.env.BASE_URL || '/';
const frameSrc = `${baseUrl}Xハローワールド/index.html`;
const route = useRoute();
const router = useRouter();
const normalizeQueryValue = (value: string | string[] | null | undefined): string | null =>
  Array.isArray(value) ? value[0] ?? null : value ?? null;
const toHalfwidthUrl = (value: string): string => value.replace(/？/g, '?').replace(/＆/g, '&').replace(/＝/g, '=');
const 戻URL = computed(() => {
  const value = normalizeQueryValue(route.query.戻URL as string | string[] | undefined);
  return value ? String(value) : '';
});
const handleReturn = () => {
  if (!戻URL.value) return;
  router.push(toHalfwidthUrl(戻URL.value));
};
</script>

<template>
  <div class="page-container">
    <button v-if="戻URL" class="btn-return" @click="handleReturn">戻る</button>
    <iframe
      class="world-frame"
      :src="frameSrc"
      title="Xハローワールド"
      frameborder="0"
      allow="fullscreen"
      loading="lazy"
    ></iframe>
  </div>
</template>

<style scoped>
.page-container {
  position: relative;
  width: 100%;
  height: 100%;
  background: #071016;
}

.world-frame {
  width: 100%;
  height: 100%;
  border: 0;
  display: block;
}

.btn-return {
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 2;
  height: 30px;
  padding: 0 14px;
  border: 1px solid rgba(255, 255, 255, 0.40);
  background: rgba(5, 14, 20, 0.72);
  color: #e8faff;
  cursor: pointer;
  font-size: 12px;
  font-weight: 700;
  backdrop-filter: blur(8px);
}

.btn-return:hover {
  background: rgba(6, 36, 48, 0.86);
}
</style>
