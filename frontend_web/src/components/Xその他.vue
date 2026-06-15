<!--
  -*- coding: utf-8 -*-

  -------------------------------------------------------------------------
  COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
  Licensed under "AiDiy 公開利用ライセンス v1.1".
  Commercial use requires prior written consent from all copyright holders.
  See LICENSE for full terms. Thank you for keeping the rules.
  https://github.com/monjyu1101/AiDiy2026
  -------------------------------------------------------------------------
-->

<script setup lang="ts">
import { onMounted, onBeforeUnmount } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const baseUrl = import.meta.env.BASE_URL || '/';
const worldSceneryUrl = `${baseUrl}X世界の絶景/index.html`;
const solarSystemUrl = `${baseUrl}X太陽系/index.html`;
const bgmUrl = `${baseUrl}X動画再生BGM/index.html`;
const AUTO_JUMP_MS = 60000;
const AUTO_JUMP_PATH = '/Xその他/X自己紹介/表示';
const cancelEvents = ['mousedown', 'keydown', 'touchstart', 'wheel', 'scroll'];
const cancelOptions = { passive: true };
let timerId: ReturnType<typeof setTimeout> | null = null;
let armTimerId: ReturnType<typeof setTimeout> | null = null;
let isCancelled = false;
let isArmed = false;

const removeCancelListeners = () => {
  if (!isArmed) return;
  cancelEvents.forEach((eventName) => {
    document.removeEventListener(eventName as keyof DocumentEventMap, cancelAutoJump as any);
  });
};

const cancelAutoJump = () => {
  if (!isArmed) return;
  if (isCancelled) return;
  isCancelled = true;
  if (timerId) {
    clearTimeout(timerId);
    timerId = null;
  }
  removeCancelListeners();
};

const armAutoJump = () => {
  isArmed = true;
  cancelEvents.forEach((eventName) => {
    document.addEventListener(eventName as keyof DocumentEventMap, cancelAutoJump as any);
  });
};

const startAutoJump = () => {
  timerId = setTimeout(() => {
    router.push(AUTO_JUMP_PATH);
  }, AUTO_JUMP_MS);
};

onMounted(() => {
  startAutoJump();
  armTimerId = setTimeout(armAutoJump, 500);
});

onBeforeUnmount(() => {
  if (timerId) {
    clearTimeout(timerId);
    timerId = null;
  }
  if (armTimerId) {
    clearTimeout(armTimerId);
    armTimerId = null;
  }
  removeCancelListeners();
});
</script>

<template>
  <div class="menu-view">
    <h2 class="page-title">【 その他 】</h2>

    <div class="content">
      <p>テスト機能・ゲームへのアクセスリンクです。下記から選択してください。</p>

      <div class="other-menu-sections">
        <div class="menu-row">
          <router-link class="menu-card menu-card-fixed" to="/Xその他/X自己紹介/表示?戻URL=/Xその他">
            <div class="menu-card-title">
              <span class="icon">X自</span>
              X自己紹介
            </div>
            <div class="menu-card-description">
              AiDiy のバージョン・システム構成・ライセンス情報のプロフィール表示
            </div>
          </router-link>

          <router-link class="menu-card menu-card-fixed" to="/Xビデオ?戻URL=/Xその他">
            <div class="menu-card-title">
              <span class="icon">Xビ</span>
              Xビデオ
            </div>
            <div class="menu-card-description">
              AiDiy の機能紹介・実装解説・時事ニュース解説ビデオの一覧
            </div>
          </router-link>
        </div>

        <div class="menu-row">
          <a class="menu-card menu-card-fixed" :href="worldSceneryUrl" target="_blank" rel="noopener noreferrer">
            <div class="menu-card-title">
              <span class="icon">X世</span>
              X世界の絶景
            </div>
            <div class="menu-card-description">
              世界各地の絶景スポットをランダムに巡回する全画面スライドショー
            </div>
          </a>

          <a class="menu-card menu-card-fixed" :href="bgmUrl" target="_blank" rel="noopener noreferrer">
            <div class="menu-card-title">
              <span class="icon">X音</span>
              X動画再生BGM
            </div>
            <div class="menu-card-description">
              2つのビデオソースをクロスフェードで交互再生するBGMプレイヤー
            </div>
          </a>

          <a class="menu-card menu-card-fixed" :href="solarSystemUrl" target="_blank" rel="noopener noreferrer">
            <div class="menu-card-title">
              <span class="icon">X太</span>
              X太陽系
            </div>
            <div class="menu-card-description">
              年月日スライダーで任意の日時の惑星配置を3Dシミュレーション
            </div>
          </a>
        </div>

        <div class="menu-hairline"></div>

        <div class="menu-row">
          <router-link class="menu-card menu-card-fixed" to="/Xその他/Xインベーダー/ゲーム?戻URL=/Xその他">
            <div class="menu-card-title">
              <span class="icon">X侵</span>
              Xインベーダー
            </div>
            <div class="menu-card-description">
              スペースインベーダー風レトロシューティングゲーム
            </div>
          </router-link>

          <router-link class="menu-card menu-card-fixed" to="/Xその他/Xテトリス/ゲーム?戻URL=/Xその他">
            <div class="menu-card-title">
              <span class="icon">Xテ</span>
              Xテトリス
            </div>
            <div class="menu-card-description">
              キーボード・タッチ操作対応のテトリスパズルゲーム
            </div>
          </router-link>

          <router-link class="menu-card menu-card-fixed" to="/Xその他/Xリバーシ/ゲーム?戻URL=/Xその他">
            <div class="menu-card-title">
              <span class="icon">Xリ</span>
              Xリバーシ
            </div>
            <div class="menu-card-description">
              CPU対戦・二人対戦モード対応のリバーシ（オセロ）ゲーム
            </div>
          </router-link>

          <router-link class="menu-card menu-card-fixed" to="/Xその他/X立体リバーシ/ゲーム?戻URL=/Xその他">
            <div class="menu-card-title">
              <span class="icon">X立</span>
              X立体リバーシ
            </div>
            <div class="menu-card-description">
              立方体6面を使った3D空間でのリバーシ・CPU対戦モード搭載
            </div>
          </router-link>

        </div>
      </div>
    </div>
  </div>
</template>

<style scoped src="../assets/menu-common.css"></style>
<style scoped>
.other-menu-sections {
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
