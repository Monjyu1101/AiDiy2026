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
    <h2 class="page-title">【 マスタ 】</h2>

    <div class="content">
      <p>マスタ管理機能へのアクセスリンクです。下記から選択してください。</p>

      <div class="master-menu-sections">
        <div class="menu-row">
          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">M車</span>
              M車両
            </div>
            <div class="menu-card-description">
              車両マスター管理・車両情報登録・車両設定
            </div>
            <router-link to="/Mマスタ/M車両/一覧?戻URL=/Mマスタ" class="menu-card-link">
              開く →
            </router-link>
          </div>

          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">M配</span>
              M配車区分
            </div>
            <div class="menu-card-description">
              配車区分マスター・配車カテゴリ管理・色設定
            </div>
            <router-link to="/Mマスタ/M配車区分/一覧?戻URL=/Mマスタ" class="menu-card-link">
              開く →
            </router-link>
          </div>
        </div>

        <div class="menu-hairline"></div>

        <div class="menu-row">
          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">M分</span>
              M商品分類
            </div>
            <div class="menu-card-description">
              商品分類マスター・牛飼料系から原材料他までの分類管理
            </div>
            <router-link to="/Mマスタ/M商品分類/一覧?戻URL=/Mマスタ" class="menu-card-link">
              開く →
            </router-link>
          </div>

          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">M商</span>
              M商品
            </div>
            <div class="menu-card-description">
              商品マスター管理・商品情報登録・在庫設定
            </div>
            <router-link to="/Mマスタ/M商品/一覧?戻URL=/Mマスタ" class="menu-card-link">
              開く →
            </router-link>
          </div>

          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">M構</span>
              M商品構成
            </div>
            <div class="menu-card-description">
              生産ロット単位の構成商品マスター・構成比率と構成数量の管理
            </div>
            <router-link to="/Mマスタ/M商品構成/一覧?戻URL=/Mマスタ" class="menu-card-link">
              開く →
            </router-link>
          </div>
        </div>

        <div class="menu-hairline"></div>

        <div class="menu-row">

          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">M生</span>
              M生産区分
            </div>
            <div class="menu-card-description">
              生産区分マスター・牛飼料からその他までの区分管理・色設定
            </div>
            <router-link to="/Mマスタ/M生産区分/一覧?戻URL=/Mマスタ" class="menu-card-link">
              開く →
            </router-link>
          </div>

          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">M工</span>
              M生産工程
            </div>
            <div class="menu-card-description">
              生産工程マスター管理・ライン１からライン７までの生産工程登録
            </div>
            <router-link to="/Mマスタ/M生産工程/一覧?戻URL=/Mマスタ" class="menu-card-link">
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
.master-menu-sections {
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

  .menu-hairline {
    width: 100%;
  }
}
</style>

