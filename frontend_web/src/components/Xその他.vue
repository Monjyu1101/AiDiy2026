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
import { onMounted, onBeforeUnmount } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const AUTO_JUMP_MS = 60000;
const AUTO_JUMP_PATH = '/Xその他/X自己紹介/表示';
const cancelEvents = ['mousedown', 'keydown', 'touchstart', 'wheel', 'scroll'];
const cancelOptions = { passive: true };
let timerId: ReturnType<typeof setTimeout> | null = null;
let armTimerId: ReturnType<typeof setTimeout> | null = null;
let isCancelled = false;
let isArmed = false;

const removeCancelListeners = () => {
  if (!isArmed) return;
  cancelEvents.forEach((eventName) => {
    document.removeEventListener(eventName as keyof DocumentEventMap, cancelAutoJump as any);
  });
};

const cancelAutoJump = () => {
  if (!isArmed) return;
  if (isCancelled) return;
  isCancelled = true;
  if (timerId) {
    clearTimeout(timerId);
    timerId = null;
  }
  removeCancelListeners();
};

const armAutoJump = () => {
  isArmed = true;
  cancelEvents.forEach((eventName) => {
    document.addEventListener(eventName as keyof DocumentEventMap, cancelAutoJump as any);
  });
};

const startAutoJump = () => {
  timerId = setTimeout(() => {
    router.push(AUTO_JUMP_PATH);
  }, AUTO_JUMP_MS);
};

onMounted(() => {
  startAutoJump();
  armTimerId = setTimeout(armAutoJump, 500);
});

onBeforeUnmount(() => {
  if (timerId) {
    clearTimeout(timerId);
    timerId = null;
  }
  if (armTimerId) {
    clearTimeout(armTimerId);
    armTimerId = null;
  }
  removeCancelListeners();
});
</script>

<template>
  <div class="menu-view">
    <h2 class="page-title">【 その他 】</h2>

    <div class="content">
      <p>テスト機能・ゲームへのアクセスリンクです。下記から選択してください。</p>

      <div class="menu-grid">
        <!-- Xインベーダーカード -->
        <div class="menu-card">
          <div class="menu-card-title">
            <span class="icon">X侵</span>
            Xインベーダー
          </div>
          <div class="menu-card-description">
            クラシックインベーダーゲーム・レトロゲーム体験
          </div>
          <router-link to="/Xその他/Xインベーダー/ゲーム" class="menu-card-link">
            開く →
          </router-link>
        </div>

        <!-- Xテトリスカード -->
        <div class="menu-card">
          <div class="menu-card-title">
            <span class="icon">Xテ</span>
            Xテトリス
          </div>
          <div class="menu-card-description">
            テトリスゲーム・パズルゲーム体験
          </div>
          <router-link to="/Xその他/Xテトリス/ゲーム" class="menu-card-link">
            開く →
          </router-link>
        </div>

        <!-- Xリバーシカード -->
        <div class="menu-card">
          <div class="menu-card-title">
            <span class="icon">Xリ</span>
            Xリバーシ
          </div>
          <div class="menu-card-description">
            リバーシ（オセロ）ゲーム・対戦ゲーム体験
          </div>
          <router-link to="/Xその他/Xリバーシ/ゲーム" class="menu-card-link">
            開く →
          </router-link>
        </div>

        <!-- X自己紹介カード -->
        <div class="menu-card">
          <div class="menu-card-title">
            <span class="icon">X自</span>
            X自己紹介
          </div>
          <div class="menu-card-description">
            システム自己紹介・プロフィール表示
          </div>
          <router-link to="/Xその他/X自己紹介/表示" class="menu-card-link">
            開く →
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped src="../assets/menu-common.css"></style>
<style scoped>
/* 追加のスタイルがあればここに記述 */
</style>

