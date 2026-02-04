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
    <h2 class="page-title">【 管理 】</h2>

    <div class="content">
      <p>管理機能へのアクセスリンクです。下記から選択してください。</p>

      <div class="menu-grid">
        <!-- AIコアカード -->
        <div class="menu-card">
          <div class="menu-card-title">
            <span class="icon">AI</span>
            AIコア
          </div>
          <div class="menu-card-description">
            AI対話機能・音声認識・画像生成・コードエージェント
          </div>
          <a href="/AIコア" target="_blank" class="menu-card-link">
            開く →
          </a>
        </div>

        <!-- C権限カード -->
        <div class="menu-card">
          <div class="menu-card-title">
            <span class="icon">C権</span>
            C権限
          </div>
          <div class="menu-card-description">
            権限管理・ユーザー権限設定・アクセス制御
          </div>
          <router-link to="/C管理/C権限/一覧" class="menu-card-link">
            開く →
          </router-link>
        </div>

        <!-- C利用者カード -->
        <div class="menu-card">
          <div class="menu-card-title">
            <span class="icon">C利</span>
            C利用者
          </div>
          <div class="menu-card-description">
            利用者管理・ユーザー情報管理・アカウント設定
          </div>
          <router-link to="/C管理/C利用者/一覧" class="menu-card-link">
            開く →
          </router-link>
        </div>

        <!-- C採番カード -->
        <div class="menu-card">
          <div class="menu-card-title">
            <span class="icon">C採</span>
            C採番
          </div>
          <div class="menu-card-description">
            採番管理・ID自動生成機能・シーケンス管理
          </div>
          <router-link to="/C管理/C採番/一覧" class="menu-card-link">
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


