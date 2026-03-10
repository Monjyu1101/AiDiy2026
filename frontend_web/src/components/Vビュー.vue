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

