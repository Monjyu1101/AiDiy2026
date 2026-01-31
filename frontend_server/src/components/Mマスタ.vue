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
    <h2 class="page-title">【 マスタ 】</h2>

    <div class="content">
      <p>マスタ管理機能へのアクセスリンクです。下記から選択してください。</p>

      <div class="menu-grid">
        <!-- M車両カード -->
        <div class="menu-card">
          <div class="menu-card-title">
            <span class="icon">M車</span>
            M車両
          </div>
          <div class="menu-card-description">
            車両マスター管理・車両情報登録・車両設定
          </div>
          <router-link to="/Mマスタ/M車両/一覧" class="menu-card-link">
            開く →
          </router-link>
        </div>

        <!-- M配車区分カード -->
        <div class="menu-card">
          <div class="menu-card-title">
            <span class="icon">M配</span>
            M配車区分
          </div>
          <div class="menu-card-description">
            配車区分マスター・配車カテゴリ管理・色設定
          </div>
          <router-link to="/Mマスタ/M配車区分/一覧" class="menu-card-link">
            開く →
          </router-link>
        </div>

        <!-- M商品カード -->
        <div class="menu-card">
          <div class="menu-card-title">
            <span class="icon">M商</span>
            M商品
          </div>
          <div class="menu-card-description">
            商品マスター管理・商品情報登録・在庫設定
          </div>
          <router-link to="/Mマスタ/M商品/一覧" class="menu-card-link">
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

