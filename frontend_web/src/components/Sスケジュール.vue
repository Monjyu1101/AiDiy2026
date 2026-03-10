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
    <h2 class="page-title">【 スケジュール 】</h2>

    <div class="content">
      <p>スケジュール管理機能へのアクセスリンクです。下記から選択してください。</p>

      <div class="menu-grid">
        <!-- S配車_週表示カード -->
        <div class="menu-card">
          <div class="menu-card-title">
            <span class="icon">S週</span>
            S配車_週表示
          </div>
          <div class="menu-card-description">
            配車スケジュール週表示・週単位の配車管理・スケジュール調整
          </div>
          <router-link class="menu-card-link" to="/Sスケジュール/S配車_週表示">
            画面を開く
          </router-link>
        </div>

        <!-- S配車_日表示カード -->
        <div class="menu-card">
          <div class="menu-card-title">
            <span class="icon">S日</span>
            S配車_日表示
          </div>
          <div class="menu-card-description">
            配車スケジュール日表示・日単位の配車管理・詳細スケジュール
          </div>
          <router-link class="menu-card-link" to="/Sスケジュール/S配車_日表示">
            画面を開く
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

