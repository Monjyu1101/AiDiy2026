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
const allEnUrl    = `${baseUrl}Xビデオ/AiDiy紹介__all_en/index.html`;
const 紹介ビデオ生成Url = `${baseUrl}Xビデオ/AiDiy紹介_ビデオ生成_ja/index.html`;
const 解説ビデオ生成Url = `${baseUrl}Xビデオ/AiDiy解説_ビデオ生成_ja/index.html`;
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
const 解説AllUrl          = `${baseUrl}Xビデオ/AiDiy解説__all_ja/index.html`;
const 解説AllEnUrl        = `${baseUrl}Xビデオ/AiDiy解説__all_en/index.html`;
const 解説toolsUrl        = `${baseUrl}Xビデオ/AiDiy解説_tools_ja/index.html`;
const ビデオページ生成解説Url = `${baseUrl}Xビデオ/AiDiy解説_ビデオページ生成_ja/index.html`;
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
        <div class="section-label">AiDiy紹介</div>

        <div class="menu-row">
          <a class="menu-card menu-card-fixed" :href="allUrl" target="_blank" rel="noopener noreferrer">
            <div class="menu-card-title">
              <span class="icon">X全</span>
              AiDiy紹介 (all)
            </div>
            <div class="menu-card-description">
              backend・frontend・AIコア・tools・hermes・avatar の全テーマを通しで再生する総合プレゼンビデオ
            </div>
          </a>

          <a class="menu-card menu-card-fixed" :href="allEnUrl" target="_blank" rel="noopener noreferrer">
            <div class="menu-card-title">
              <span class="icon">X全</span>
              AiDiy紹介 (all EN)
            </div>
            <div class="menu-card-description">
              English version — full AiDiy introduction covering all themes in one presentation
            </div>
          </a>

          <a class="menu-card menu-card-fixed" :href="backendUrl" target="_blank" rel="noopener noreferrer">
            <div class="menu-card-title">
              <span class="icon">X後</span>
              AiDiy紹介 (backend)
            </div>
            <div class="menu-card-description">
              FastAPI + SQLAlchemy の 2 サーバー構成・4 層アーキテクチャ・日本語 API 設計を紹介
            </div>
          </a>

          <a class="menu-card menu-card-fixed" :href="frontendUrl" target="_blank" rel="noopener noreferrer">
            <div class="menu-card-title">
              <span class="icon">X前</span>
              AiDiy紹介 (frontend)
            </div>
            <div class="menu-card-description">
              Vue 3 + Vite + TypeScript・qTubler グリッド・Pinia / Vue Router の構成を紹介
            </div>
          </a>

          <a class="menu-card menu-card-fixed" :href="aiコアUrl" target="_blank" rel="noopener noreferrer">
            <div class="menu-card-title">
              <span class="icon">XAI</span>
              AiDiy紹介 (AIコア)
            </div>
            <div class="menu-card-description">
              マルチ AI 対話・WebSocket ストリーミング・Code AI エージェント連携を紹介
            </div>
          </a>

          <a class="menu-card menu-card-fixed" :href="toolsUrl" target="_blank" rel="noopener noreferrer">
            <div class="menu-card-title">
              <span class="icon">XMC</span>
              AiDiy紹介 (tools)
            </div>
            <div class="menu-card-description">
              14 の MCP サーバー・3 トランスポート対応の AiDiy TOOL HUB 全体像を紹介
            </div>
          </a>

          <a class="menu-card menu-card-fixed" :href="hermesUrl" target="_blank" rel="noopener noreferrer">
            <div class="menu-card-title">
              <span class="icon">Xヘ</span>
              AiDiy紹介 (hermes)
            </div>
            <div class="menu-card-description">
              コード支援 CLI aidiy_hermes の設計・複数 AI 切り替え・session 管理を紹介
            </div>
          </a>

          <a class="menu-card menu-card-fixed" :href="avatarUrl" target="_blank" rel="noopener noreferrer">
            <div class="menu-card-title">
              <span class="icon">Xア</span>
              AiDiy紹介 (avatar)
            </div>
            <div class="menu-card-description">
              Electron/Web デュアルモード・VRM アバター・Three.js + AI 音声連携を紹介
            </div>
          </a>

          <a class="menu-card menu-card-fixed" :href="紹介ビデオ生成Url" target="_blank" rel="noopener noreferrer">
            <div class="menu-card-title">
              <span class="icon">XVi</span>
              AiDiy紹介 (ビデオ生成)
            </div>
            <div class="menu-card-description">
              AiDiy のビデオ生成機能を一人アバターで紹介・9 ステップ全自動化を解説
            </div>
          </a>
        </div>

        <div class="section-label">AiDiy実装・解説</div>

        <div class="menu-row">
          <a class="menu-card menu-card-fixed" :href="解説AllUrl" target="_blank" rel="noopener noreferrer">
            <div class="menu-card-title">
              <span class="icon">X全</span>
              AiDiy解説 (all)
            </div>
            <div class="menu-card-description">
              AiDiy の全体構成・日本語ファースト設計・AI コア・MCP・ビデオページ生成までを二人掛け合いで解説
            </div>
          </a>

          <a class="menu-card menu-card-fixed" :href="解説AllEnUrl" target="_blank" rel="noopener noreferrer">
            <div class="menu-card-title">
              <span class="icon">X全</span>
              AiDiy解説 (all EN)
            </div>
            <div class="menu-card-description">
              English version — full AiDiy commentary covering architecture, AI core, MCP, and video generation
            </div>
          </a>

          <a class="menu-card menu-card-fixed" :href="webAiDiyUrl" target="_blank" rel="noopener noreferrer">
            <div class="menu-card-title">
              <span class="icon">XWb</span>
              AiDiy実装 (web)
            </div>
            <div class="menu-card-description">
              Vue 3 + TypeScript・qTubler グリッド・Axios/WebSocket・AI コア画面の実装を詳しく紹介
            </div>
          </a>

          <a class="menu-card menu-card-fixed" :href="avatarAiDiyUrl" target="_blank" rel="noopener noreferrer">
            <div class="menu-card-title">
              <span class="icon">XAv</span>
              AiDiy実装 (avatar)
            </div>
            <div class="menu-card-description">
              Electron IPC・Three.js VRM・音声同期・AI 対話の実装フローを詳しく紹介
            </div>
          </a>

          <a class="menu-card menu-card-fixed" :href="解説toolsUrl" target="_blank" rel="noopener noreferrer">
            <div class="menu-card-title">
              <span class="icon">XMC</span>
              AiDiy解説 (tools)
            </div>
            <div class="menu-card-description">
              14 の MCP サーバー・SSE/HTTP/stdio の 3 トランスポート・HTTP API 直接利用を二人掛け合いで解説
            </div>
          </a>

          <a class="menu-card menu-card-fixed" :href="ビデオページ生成解説Url" target="_blank" rel="noopener noreferrer">
            <div class="menu-card-title">
              <span class="icon">XVG</span>
              AiDiy解説 (ビデオページ生成)
            </div>
            <div class="menu-card-description">
              シナリオ作成・画像生成・音声合成・HTML 組み立てを MCP と CodeAgents で全自動化する流れを解説
            </div>
          </a>

          <a class="menu-card menu-card-fixed" :href="解説ビデオ生成Url" target="_blank" rel="noopener noreferrer">
            <div class="menu-card-title">
              <span class="icon">XVd</span>
              AiDiy解説 (ビデオ生成)
            </div>
            <div class="menu-card-description">
              AiDiy のビデオ生成機能を二人掛け合いで解説・utils モジュール設計・step ごとの仕組みを紹介
            </div>
          </a>
        </div>

        <div class="section-label">AiDiy実装例</div>

        <div class="menu-row">
          <a class="menu-card menu-card-fixed" :href="配車管理Url" target="_blank" rel="noopener noreferrer">
            <div class="menu-card-title">
              <span class="icon">X配</span>
              実装例 (配車管理)
            </div>
            <div class="menu-card-description">
              配車区分・車両マスタ（M系）と配車指示・スケジュール（T系）の実装例
            </div>
          </a>

          <a class="menu-card menu-card-fixed" :href="生産管理Url" target="_blank" rel="noopener noreferrer">
            <div class="menu-card-title">
              <span class="icon">X生</span>
              実装例 (生産管理)
            </div>
            <div class="menu-card-description">
              商品構成マスタ（M系）と生産指示・スケジュール（T系）の実装例
            </div>
          </a>

          <a class="menu-card menu-card-fixed" :href="在庫管理Url" target="_blank" rel="noopener noreferrer">
            <div class="menu-card-title">
              <span class="icon">X在</span>
              実装例 (在庫管理)
            </div>
            <div class="menu-card-description">
              入庫・出庫・棚卸（T系）と商品推移表（V系 生 SQL）の実装例
            </div>
          </a>

        </div>

        <div class="section-label">時事ニュース・解説</div>

        <div class="menu-row">
          <a class="menu-card menu-card-fixed" :href="ニュースUrl" target="_blank" rel="noopener noreferrer">
            <div class="menu-card-title">
              <span class="icon">Xニュ</span>
              ニュース (Anthropic)
            </div>
            <div class="menu-card-description">
              Claude 4 / Claude Code / MCP 標準化など Anthropic 2026年前半のトピックを二人掛け合いで解説
            </div>
          </a>

          <a class="menu-card menu-card-fixed" :href="ニュースGoogleUrl" target="_blank" rel="noopener noreferrer">
            <div class="menu-card-title">
              <span class="icon">XGo</span>
              ニュース (Google)
            </div>
            <div class="menu-card-description">
              Gemini 2.5 / Google I/O など Google 2026年前半のトピックを二人掛け合いで解説
            </div>
          </a>

          <a class="menu-card menu-card-fixed" :href="ニュースOpenAIUrl" target="_blank" rel="noopener noreferrer">
            <div class="menu-card-title">
              <span class="icon">XOA</span>
              ニュース (OpenAI)
            </div>
            <div class="menu-card-description">
              GPT-5 / o3 / Codex など OpenAI 2026年前半のトピックを二人掛け合いで解説
            </div>
          </a>

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

.section-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  color: #888;
  text-transform: none;
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
