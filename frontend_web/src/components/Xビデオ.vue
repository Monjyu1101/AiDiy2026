<!--
  -*- coding: utf-8 -*-

  -------------------------------------------------------------------------
  COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
  Licensed under "AiDiy 公開利用ライセンス v1.1".
  Commercial use requires prior written consent from all copyright holders.
  See LICENSE for full terms. Thank you for keeping the rules.
  https://github.com/monjyu1101/AiDiy2026
  -------------------------------------------------------------------------
-->

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const baseUrl = import.meta.env.BASE_URL || '/';
const allUrl = `${baseUrl}Xビデオ/AiDiy紹介__all/index.html`;
const avatarUrl = `${baseUrl}Xビデオ/AiDiy紹介_avatar/index.html`;
const hermesUrl = `${baseUrl}Xビデオ/AiDiy紹介_hermes/index.html`;

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
  <div class="menu-view">
    <h2 class="page-title">
      <span class="title-text">【 Xビデオ 】</span>
      <button v-if="戻URL" class="btn-return" @click="handleReturn">戻る</button>
    </h2>

    <div class="content">
      <p>AiDiy 紹介ビデオ・プレゼンテーションへのアクセスリンクです。下記から選択してください。</p>

      <div class="video-menu-sections">
        <div class="menu-row">
          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">X全</span>
              AiDiy紹介 (all)
            </div>
            <div class="menu-card-description">
              全シーンを通しで再生する総合プレゼン
            </div>
            <a :href="allUrl" target="_blank" rel="noopener noreferrer" class="menu-card-link">
              別タブで開く →
            </a>
          </div>

          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">Xア</span>
              AiDiy紹介 (avatar)
            </div>
            <div class="menu-card-description">
              Avatar 機能にフォーカスした紹介ビデオ
            </div>
            <a :href="avatarUrl" target="_blank" rel="noopener noreferrer" class="menu-card-link">
              別タブで開く →
            </a>
          </div>

          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">Xヘ</span>
              AiDiy紹介 (hermes)
            </div>
            <div class="menu-card-description">
              Hermes CLI 機能にフォーカスした紹介ビデオ
            </div>
            <a :href="hermesUrl" target="_blank" rel="noopener noreferrer" class="menu-card-link">
              別タブで開く →
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped src="../assets/menu-common.css"></style>
<style scoped>
.page-title {
  display: flex;
  align-items: center;
}

.title-text {
  flex: 1;
}

.btn-return {
  margin-left: auto;
  height: 24px;
  padding: 0 12px;
  border: none;
  border-radius: 0;
  cursor: pointer;
  font-size: 12px;
  background-color: #dc3545;
  color: #fff;
}

.btn-return:hover {
  background-color: #c82333;
}

.video-menu-sections {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-top: 20px;
}

.menu-row {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
}

.menu-card-fixed {
  width: 320px;
  min-width: 320px;
  height: 158px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.menu-card-fixed .menu-card-description {
  flex: 1;
}

@media (max-width: 768px) {
  .menu-row {
    flex-direction: column;
  }

  .menu-card-fixed {
    width: 100%;
    min-width: 0;
    height: auto;
    min-height: 158px;
  }
}
</style>
