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
import { RouterLink } from 'vue-router';
</script>

<template>
  <div class="menu-view">
    <h2 class="page-title">【 スケジュール 】</h2>

    <div class="content">
      <p>スケジュール管理機能へのアクセスリンクです。下記から選択してください。</p>

      <div class="schedule-menu-sections">
        <div class="menu-row">
          <!-- S配車_週表示カード -->
          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">S週</span>
              S配車_週表示
            </div>
            <div class="menu-card-description">
              配車スケジュール週表示・週単位の配車管理・スケジュール調整
            </div>
            <RouterLink class="menu-card-link" to="/Sスケジュール/S配車_週表示?戻URL=/Sスケジュール">
              画面を開く
            </RouterLink>
          </div>

          <!-- S配車_日表示カード -->
          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">S日</span>
              S配車_日表示
            </div>
            <div class="menu-card-description">
              配車スケジュール日表示・日単位の配車管理・詳細スケジュール
            </div>
            <RouterLink class="menu-card-link" to="/Sスケジュール/S配車_日表示?戻URL=/Sスケジュール">
              画面を開く
            </RouterLink>
          </div>
        </div>

        <div class="menu-hairline"></div>

        <div class="menu-row">
          <!-- S生産_週表示カード -->
          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">S生週</span>
              S生産_週表示
            </div>
            <div class="menu-card-description">
              生産スケジュール週表示・週単位の生産管理・スケジュール調整
            </div>
            <RouterLink class="menu-card-link" to="/Sスケジュール/S生産_週表示?戻URL=/Sスケジュール">
              画面を開く
            </RouterLink>
          </div>

          <!-- S生産_日表示カード -->
          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">S生日</span>
              S生産_日表示
            </div>
            <div class="menu-card-description">
              生産スケジュール日表示・日単位の生産管理・詳細スケジュール
            </div>
            <RouterLink class="menu-card-link" to="/Sスケジュール/S生産_日表示?戻URL=/Sスケジュール">
              画面を開く
            </RouterLink>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped src="../assets/menu-common.css"></style>
<style scoped>
.schedule-menu-sections {
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

.menu-hairline {
  width: 100%;
  height: 1px;
  background: linear-gradient(90deg, rgba(90, 74, 58, 0.12) 0%, rgba(90, 74, 58, 0.45) 50%, rgba(90, 74, 58, 0.12) 100%);
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

