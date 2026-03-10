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

      <div class="menu-grid">
        <!-- T配車カード -->
        <div class="menu-card">
          <div class="menu-card-title">
            <span class="icon">T配</span>
            T配車
          </div>
          <div class="menu-card-description">
            配車データ管理・配車情報登録・スケジュール管理
          </div>
          <RouterLink to="/Tトラン/T配車/一覧" class="menu-card-link">
            一覧を開く
          </RouterLink>
        </div>

        <!-- T商品入庫カード -->
        <div class="menu-card">
          <div class="menu-card-title">
            <span class="icon">T入</span>
            T商品入庫
          </div>
          <div class="menu-card-description">
            商品入庫データ管理・入庫情報登録
          </div>
          <RouterLink to="/Tトラン/T商品入庫/一覧" class="menu-card-link">
            一覧を開く
          </RouterLink>
        </div>

        <!-- T商品出庫カード -->
        <div class="menu-card">
          <div class="menu-card-title">
            <span class="icon">T出</span>
            T商品出庫
          </div>
          <div class="menu-card-description">
            商品出庫データ管理・出庫情報登録
          </div>
          <RouterLink to="/Tトラン/T商品出庫/一覧" class="menu-card-link">
            一覧を開く
          </RouterLink>
        </div>

        <!-- T商品棚卸カード -->
        <div class="menu-card">
          <div class="menu-card-title">
            <span class="icon">T棚</span>
            T商品棚卸
          </div>
          <div class="menu-card-description">
            商品棚卸データ管理・棚卸情報登録
          </div>
          <RouterLink to="/Tトラン/T商品棚卸/一覧" class="menu-card-link">
            一覧を開く
          </RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped src="../assets/menu-common.css"></style>
<style scoped>
/* 追加のスタイルがあればここに記述 */
</style>

