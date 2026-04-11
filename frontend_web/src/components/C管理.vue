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
    <h2 class="page-title">【 管理 】</h2>

    <div class="content">
      <p>管理機能へのアクセスリンクです。下記から選択してください。</p>

      <div class="manage-menu-sections">
        <div class="menu-row">
          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">AI</span>
              AiDiy
            </div>
            <div class="menu-card-description">
              AI対話機能・音声認識・画像生成・コードエージェント
            </div>
            <a href="/AiDiy" target="_blank" class="menu-card-link">
              開く →
            </a>
          </div>
        </div>

        <div class="menu-hairline"></div>

        <div class="menu-row">
          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">C権</span>
              C権限
            </div>
            <div class="menu-card-description">
              権限管理・ユーザー権限設定・アクセス制御
            </div>
            <router-link to="/C管理/C権限/一覧?戻URL=/C管理" class="menu-card-link">
              開く →
            </router-link>
          </div>

          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">C利</span>
              C利用者
            </div>
            <div class="menu-card-description">
              利用者管理・ユーザー情報管理・アカウント設定
            </div>
            <router-link to="/C管理/C利用者/一覧?戻URL=/C管理" class="menu-card-link">
              開く →
            </router-link>
          </div>

          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">C採</span>
              C採番
            </div>
            <div class="menu-card-description">
              採番管理・ID自動生成機能・シーケンス管理
            </div>
            <router-link to="/C管理/C採番/一覧?戻URL=/C管理" class="menu-card-link">
              開く →
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped src="../assets/menu-common.css"></style>
<style scoped>
.manage-menu-sections {
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


