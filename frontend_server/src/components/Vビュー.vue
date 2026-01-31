<!--
  -*- coding: utf-8 -*-

  ------------------------------------------------
  COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
  This software is licensed under the MIT License.
  https://github.com/monjyu1101
  Thank you for keeping the rules.
  ------------------------------------------------
-->

<template>
  <div class="menu-view">
    <h2 class="page-title">【 ビュー 】</h2>

    <div class="content">
      <p>ビュー機能へのアクセスリンクです。下記から選択してください。</p>

      <div class="menu-grid">
        <!-- V商品推移表カード -->
        <div class="menu-card">
          <div class="menu-card-title">
            <span class="icon">V推</span>
            V商品推移表
          </div>
          <div class="menu-card-description">
            商品推移グラフ表示・在庫推移分析・トレンド確認
          </div>
          <router-link to="/Vビュー/V商品推移表" class="menu-card-link">
            開く
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

