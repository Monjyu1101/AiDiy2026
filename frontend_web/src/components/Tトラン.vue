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
import { RouterLink } from 'vue-router';
</script>

<template>
  <div class="menu-view">
    <h2 class="page-title">【 トラン 】</h2>

    <div class="content">
      <p>トランザクション管理機能へのアクセスリンクです。下記から選択してください。</p>

      <div class="transaction-menu-sections">
        <div class="menu-row">
          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">T配</span>
              T配車
            </div>
            <div class="menu-card-description">
              配車データ管理・配車情報登録・スケジュール管理
            </div>
            <RouterLink to="/Tトラン/T配車/一覧?戻URL=/Tトラン" class="menu-card-link">
              一覧を開く
            </RouterLink>
          </div>
        </div>

        <div class="menu-hairline"></div>

        <div class="menu-row">
          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">T入</span>
              T商品入庫
            </div>
            <div class="menu-card-description">
              商品入庫データ管理・入庫情報登録
            </div>
            <RouterLink to="/Tトラン/T商品入庫/一覧?戻URL=/Tトラン" class="menu-card-link">
              一覧を開く
            </RouterLink>
          </div>

          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">T出</span>
              T商品出庫
            </div>
            <div class="menu-card-description">
              商品出庫データ管理・出庫情報登録
            </div>
            <RouterLink to="/Tトラン/T商品出庫/一覧?戻URL=/Tトラン" class="menu-card-link">
              一覧を開く
            </RouterLink>
          </div>

          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">T棚</span>
              T商品棚卸
            </div>
            <div class="menu-card-description">
              商品棚卸データ管理・棚卸情報登録
            </div>
            <RouterLink to="/Tトラン/T商品棚卸/一覧?戻URL=/Tトラン" class="menu-card-link">
              一覧を開く
            </RouterLink>
          </div>
        </div>

        <div class="menu-hairline"></div>

        <div class="menu-row">
          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">T生</span>
              T生産
            </div>
            <div class="menu-card-description">
              生産データ管理・生産情報登録・スケジュール管理
            </div>
            <RouterLink to="/Tトラン/T生産/一覧?戻URL=/Tトラン" class="menu-card-link">
              一覧を開く
            </RouterLink>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped src="../assets/menu-common.css"></style>
<style scoped>
.transaction-menu-sections {
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

