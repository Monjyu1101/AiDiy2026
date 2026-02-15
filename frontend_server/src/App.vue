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
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import Layout from './components/_Layout.vue';
import qAlertDialog from './components/_share/qAlertDialog.vue';
import qColorPickerDialog from './components/_share/qColorPickerDialog.vue';
import { setAlertInstance, setConfirmInstance, setColorPickerInstance } from './utils/qAlert';

const route = useRoute();
type AlertDialogInstance = {
  show: (message: string) => Promise<void>;
  showConfirm: (message: string) => Promise<boolean>;
};

const alertRef = ref<AlertDialogInstance | null>(null);
const colorPickerRef = ref(null);

// ログイン画面以外はレイアウトを適用
const isLogin = computed(() => route.path === '/ログイン');

onMounted(() => {
  if (alertRef.value) {
    setAlertInstance(alertRef.value);
    setConfirmInstance({ show: alertRef.value.showConfirm });
  }
  if (colorPickerRef.value) {
    setColorPickerInstance(colorPickerRef.value);
  }
});
</script>

<template>
  <div v-if="isLogin">
    <RouterView />
  </div>
  <Layout v-else>
    <RouterView />
  </Layout>
  <qAlertDialog ref="alertRef" />
  <qColorPickerDialog ref="colorPickerRef" />
</template>

