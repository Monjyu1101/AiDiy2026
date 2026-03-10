<!--
  -*- coding: utf-8 -*-

  -------------------------------------------------------------------------
  COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
  Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
  Commercial use requires prior written consent from all copyright holders.
  See LICENSE for full terms. Thank you for keeping the rules.
  https://github.com/monjyu1101
  -------------------------------------------------------------------------
-->

<script setup lang="ts">
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import { qConfirm } from '../utils/qAlert';

const router = useRouter();
const authStore = useAuthStore();

onMounted(async () => {
  const confirmed = await qConfirm('ログアウトしますか？');

  if (confirmed) {
    authStore.logout();
  } else {
    // キャンセルした場合は元の画面に戻る
    router.back();
  }
});
</script>

<template>
  <div class="logout-container">
    <div class="logout-message">ログアウト処理中...</div>
  </div>
</template>

<style scoped>
.logout-container {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background: linear-gradient(135deg, #faf7f2 0%, #f5f1e8 50%, #f0ebe0 100%);
}

.logout-message {
  font-size: 18px;
  color: #333;
  text-align: center;
}
</style>

