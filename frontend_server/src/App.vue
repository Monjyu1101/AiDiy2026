<!--
  -*- coding: utf-8 -*-

  ------------------------------------------------
  COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
  This software is licensed under the MIT License.
  https://github.com/monjyu1101
  Thank you for keeping the rules.
  ------------------------------------------------
-->

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import Layout from './components/_Layout.vue';
import qAlertDialog from './components/_share/qAlertDialog.vue';
import qConfirmDialog from './components/_share/qConfirmDialog.vue';
import qColorPickerDialog from './components/_share/qColorPickerDialog.vue';
import { setAlertInstance, setConfirmInstance, setColorPickerInstance } from './utils/qAlert';

const route = useRoute();
const alertRef = ref(null);
const confirmRef = ref(null);
const colorPickerRef = ref(null);

// ログイン画面以外はレイアウトを適用
const isLogin = computed(() => route.path === '/ログイン');

onMounted(() => {
  if (alertRef.value) {
    setAlertInstance(alertRef.value);
  }
  if (confirmRef.value) {
    setConfirmInstance(confirmRef.value);
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
  <qConfirmDialog ref="confirmRef" />
  <qColorPickerDialog ref="colorPickerRef" />
</template>

