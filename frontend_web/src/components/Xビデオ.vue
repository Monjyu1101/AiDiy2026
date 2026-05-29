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
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const baseUrl = import.meta.env.BASE_URL || '/';
const allUrl      = `${baseUrl}Xビデオ/AiDiy紹介__all_ja/index.html`;
const backendUrl  = `${baseUrl}Xビデオ/AiDiy紹介_backend_ja/index.html`;
const frontendUrl = `${baseUrl}Xビデオ/AiDiy紹介_frontend_ja/index.html`;
const aiコアUrl   = `${baseUrl}Xビデオ/AiDiy紹介_AIコア_ja/index.html`;
const toolsUrl    = `${baseUrl}Xビデオ/AiDiy紹介_tools_ja/index.html`;
const hermesUrl   = `${baseUrl}Xビデオ/AiDiy紹介_hermes_ja/index.html`;
const avatarUrl   = `${baseUrl}Xビデオ/AiDiy紹介_avatar_ja/index.html`;
const 配車管理Url  = `${baseUrl}Xビデオ/AiDiy実装_配車管理_ja/index.html`;
const 生産管理Url  = `${baseUrl}Xビデオ/AiDiy実装_生産管理_ja/index.html`;
const 在庫管理Url  = `${baseUrl}Xビデオ/AiDiy実装_在庫管理_ja/index.html`;
const webAiDiyUrl = `${baseUrl}Xビデオ/AiDiy実装_web_ja/index.html`;
const avatarAiDiyUrl = `${baseUrl}Xビデオ/AiDiy実装_avatar_ja/index.html`;
const ビデオページ生成解説Url = `${baseUrl}Xビデオ/解説_ビデオページ生成_ja/index.html`;
const ニュースUrl       = `${baseUrl}Xビデオ/ニュース_20260521_anthropic2026前半_ja/index.html`;
const ニュースGoogleUrl  = `${baseUrl}Xビデオ/ニュース_20260521_google2026前半_ja/index.html`;
const ニュースOpenAIUrl  = `${baseUrl}Xビデオ/ニュース_20260521_openai2026前半_ja/index.html`;

const route = useRoute();
const router = useRouter();
const normalizeQueryValue = (value: string | string[] | null | undefined): string | null =>
  Array.isArray(value) ? value[0] ?? null : value ?? null;
const toHalfwidthUrl = (value: string): string => value.replace(/？/g, '?').replace(/＆/g, '&').replace(/＝/g, '=');
const 戻URL = computed(() => {
  const value = normalizeQueryValue(route.query.戻URL as string | string[] | undefined);
  return value ? String(value) : '';
});
const handleReturn = () => {
  if (!戻URL.value) return;
  router.push(toHalfwidthUrl(戻URL.value));
};
</script>

<template>
  <div class="menu-view">
    <h2 class="page-title">
      <span class="title-text">【 Xビデオ 】</span>
      <button v-if="戻URL" class="btn-return" @click="handleReturn">戻る</button>
    </h2>

    <div class="content">
      <p>AiDiy 紹介ビデオ・プレゼンテーションへのアクセスリンクです。下記から選択してください。</p>

      <div class="video-menu-sections">
        <div class="section-label">紹介</div>

        <div class="menu-row">
          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">X全</span>
              AiDiy紹介 (all)
            </div>
            <div class="menu-card-description">
              全シーンを通しで再生する総合プレゼン
            </div>
            <a :href="allUrl" target="_blank" rel="noopener noreferrer" class="menu-card-link">
              別タブで開く →
            </a>
          </div>

          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">X後</span>
              AiDiy紹介 (backend)
            </div>
            <div class="menu-card-description">
              バックエンド構成にフォーカスした紹介ビデオ
            </div>
            <a :href="backendUrl" target="_blank" rel="noopener noreferrer" class="menu-card-link">
              別タブで開く →
            </a>
          </div>

          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">X前</span>
              AiDiy紹介 (frontend)
            </div>
            <div class="menu-card-description">
              フロントエンド構成にフォーカスした紹介ビデオ
            </div>
            <a :href="frontendUrl" target="_blank" rel="noopener noreferrer" class="menu-card-link">
              別タブで開く →
            </a>
          </div>

          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">XAI</span>
              AiDiy紹介 (AIコア)
            </div>
            <div class="menu-card-description">
              AIコア機能にフォーカスした紹介ビデオ
            </div>
            <a :href="aiコアUrl" target="_blank" rel="noopener noreferrer" class="menu-card-link">
              別タブで開く →
            </a>
          </div>

          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">XMC</span>
              AiDiy紹介 (tools)
            </div>
            <div class="menu-card-description">
              MCP ツール群にフォーカスした紹介ビデオ
            </div>
            <a :href="toolsUrl" target="_blank" rel="noopener noreferrer" class="menu-card-link">
              別タブで開く →
            </a>
          </div>

          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">Xヘ</span>
              AiDiy紹介 (hermes)
            </div>
            <div class="menu-card-description">
              Hermes CLI 機能にフォーカスした紹介ビデオ
            </div>
            <a :href="hermesUrl" target="_blank" rel="noopener noreferrer" class="menu-card-link">
              別タブで開く →
            </a>
          </div>

          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">Xア</span>
              AiDiy紹介 (avatar)
            </div>
            <div class="menu-card-description">
              Avatar 機能にフォーカスした紹介ビデオ
            </div>
            <a :href="avatarUrl" target="_blank" rel="noopener noreferrer" class="menu-card-link">
              別タブで開く →
            </a>
          </div>
        </div>

        <div class="section-label">実装</div>

        <div class="menu-row">
          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">XWb</span>
              AiDiy実装 (web)
            </div>
            <div class="menu-card-description">
              Vue 3 + TypeScript Web UI・qTubler・AI コアの紹介ビデオ
            </div>
            <a :href="webAiDiyUrl" target="_blank" rel="noopener noreferrer" class="menu-card-link">
              別タブで開く →
            </a>
          </div>

          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">XAv</span>
              AiDiy実装 (avatar)
            </div>
            <div class="menu-card-description">
              Electron/Web デュアルモード VRM アバター + AI コアの紹介ビデオ
            </div>
            <a :href="avatarAiDiyUrl" target="_blank" rel="noopener noreferrer" class="menu-card-link">
              別タブで開く →
            </a>
          </div>
        </div>

        <div class="section-label">実装例</div>

        <div class="menu-row">
          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">X配</span>
              実装例 (配車管理)
            </div>
            <div class="menu-card-description">
              配車区分・車両マスタと配車指示・スケジュール管理の紹介ビデオ
            </div>
            <a :href="配車管理Url" target="_blank" rel="noopener noreferrer" class="menu-card-link">
              別タブで開く →
            </a>
          </div>

          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">X生</span>
              実装例 (生産管理)
            </div>
            <div class="menu-card-description">
              商品構成マスタ・生産指示・スケジュール管理の紹介ビデオ
            </div>
            <a :href="生産管理Url" target="_blank" rel="noopener noreferrer" class="menu-card-link">
              別タブで開く →
            </a>
          </div>

          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">X在</span>
              実装例 (在庫管理)
            </div>
            <div class="menu-card-description">
              入庫・出庫・棚卸トランザクションと商品推移表の紹介ビデオ
            </div>
            <a :href="在庫管理Url" target="_blank" rel="noopener noreferrer" class="menu-card-link">
              別タブで開く →
            </a>
          </div>
        </div>

        <div class="section-label">活用事例</div>

        <div class="menu-row">
          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">XVG</span>
              活用事例 (ビデオページ生成解説)
            </div>
            <div class="menu-card-description">
              MCP と CodeAgents でビデオページを作る流れを日本語で解説
            </div>
            <a :href="ビデオページ生成解説Url" target="_blank" rel="noopener noreferrer" class="menu-card-link">
              別タブで開く →
            </a>
          </div>
        </div>

        <div class="section-label">ニュース</div>

        <div class="menu-row">
          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">Xニュ</span>
              ニュース (Anthropic)
            </div>
            <div class="menu-card-description">
              Anthropic 2026年ニュース解説ビデオ
            </div>
            <a :href="ニュースUrl" target="_blank" rel="noopener noreferrer" class="menu-card-link">
              別タブで開く →
            </a>
          </div>

          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">XGo</span>
              ニュース (Google)
            </div>
            <div class="menu-card-description">
              Google 2026年ニュース解説ビデオ
            </div>
            <a :href="ニュースGoogleUrl" target="_blank" rel="noopener noreferrer" class="menu-card-link">
              別タブで開く →
            </a>
          </div>

          <div class="menu-card menu-card-fixed">
            <div class="menu-card-title">
              <span class="icon">XOA</span>
              ニュース (OpenAI)
            </div>
            <div class="menu-card-description">
              OpenAI 2026年ニュース解説ビデオ
            </div>
            <a :href="ニュースOpenAIUrl" target="_blank" rel="noopener noreferrer" class="menu-card-link">
              別タブで開く →
            </a>
          </div>

        </div>
      </div>
    </div>
  </div>
</template>

<style scoped src="../assets/menu-common.css"></style>
<style scoped>
.page-title {
  display: flex;
  align-items: center;
}

.title-text {
  flex: 1;
}

.btn-return {
  margin-left: auto;
  height: 24px;
  padding: 0 12px;
  border: none;
  border-radius: 0;
  cursor: pointer;
  font-size: 12px;
  background-color: #dc3545;
  color: #fff;
}

.btn-return:hover {
  background-color: #c82333;
}

.video-menu-sections {
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

.section-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  color: #888;
  text-transform: uppercase;
  border-bottom: 1px solid #333;
  padding-bottom: 4px;
  margin-top: 4px;
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
