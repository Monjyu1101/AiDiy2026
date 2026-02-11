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
import { ref, onMounted } from 'vue';
import TopBar from './_TopBar.vue';
import TopMenu from './_TopMenu.vue';

// メニュー状態: 1=全表示, 2=メニュー非表示, 3=最小化
const menuState = ref(1);

const toggleMenu = () => {
  // 3段階でトグル: 1 → 2 → 3 → 1
  menuState.value = menuState.value >= 3 ? 1 : menuState.value + 1;

  // 状態をlocalStorageに保存
  localStorage.setItem('menu_state', menuState.value.toString());

  console.log('Menu state:', menuState.value);
};

// 保存された状態を復元
onMounted(() => {
  const saved = localStorage.getItem('menu_state');
  if (saved !== null) {
    const state = parseInt(saved, 10);
    if (!isNaN(state) && state >= 1 && state <= 3) {
      menuState.value = state;
    }
  }
});
</script>

<template>
  <div class="app-layout">
    <TopBar @toggle-menu="toggleMenu" :menuState="menuState" />
    <TopMenu :isOpen="menuState === 1" />
    <main class="content" :class="{ 'full-height': menuState >= 2 }">
      <slot></slot>
    </main>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f0f0f0;
}

.content {
  flex: 1;
  padding: 0;
  overflow-y: auto;
  transition: all 0.3s ease;
}

.content.full-height {
  /* メニュー非表示時にコンテンツを広げる */
  flex: 1;
}
</style>

