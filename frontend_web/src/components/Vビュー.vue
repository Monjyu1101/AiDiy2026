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

<template>
  <div class="menu-view">
    <h2 class="page-title">【 ビュー 】</h2>

    <div class="content">
      <p>ビュー機能へのアクセスリンクです。下記から選択してください。</p>

      <div class="menu-grid">
        <!-- V商品推移表カード -->
        <div class="menu-card menu-card-fixed">
          <div class="menu-card-title">
            <span class="icon">V推</span>
            V商品推移表
          </div>
          <div class="menu-card-description">
            商品推移グラフ表示・在庫推移分析・トレンド確認
          </div>
          <router-link to="/Vビュー/V商品推移表?戻URL=/Vビュー" class="menu-card-link">
            開く
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped src="../assets/menu-common.css"></style>
<style scoped>
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
  .menu-card-fixed {
    width: 100%;
    min-width: 0;
    height: auto;
    min-height: 158px;
  }
}
</style>

