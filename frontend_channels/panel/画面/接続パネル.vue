<!--

 * -*- coding: utf-8 -*-
 *
 * -------------------------------------------------------------------------
 * COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
 * Licensed under "AiDiy 公開利用ライセンス v1.1".
 * Commercial use requires prior written consent from all copyright holders.
 * See LICENSE for full terms. Thank you for keeping the rules.
 * https://github.com/monjyu1101/AiDiy2026
 * -------------------------------------------------------------------------


-->
<script setup>
import { onMounted, onBeforeUnmount, ref } from 'vue';
import { パネル状態作成 } from '../接続/パネル状態.js';
import 機能切替 from './機能切替.vue';
const 画面 = パネル状態作成(window.discordPanel);
const canvas = ref(), 本文 = ref(), 詳細 = ref();
onMounted(() => 画面.開始(canvas.value, 本文.value, 詳細.value));
onBeforeUnmount(() => 画面.終了());
</script>
<template>
  <canvas id="audio-cloud" ref="canvas" aria-hidden="true"></canvas>
  <header><div id="status" role="status" aria-live="polite"><i id="dot" :data-phase="画面.接続状態.phase"></i><span id="status-text">{{ 画面.状態名 }}</span></div><div class="brand"><strong>AiDiy Discord</strong></div><div class="window-actions"><button id="minimize" title="最小化" aria-label="最小化" @click="画面.ウィンドウ操作('minimize')">−</button><button id="close" title="閉じる" aria-label="閉じる" @click="画面.ウィンドウ操作('close')">×</button></div></header>
  <div id="activity-bar" aria-hidden="true"></div>
  <div class="conversation-toolbar"><div class="conversation-context"><span class="project-label">プロジェクト:</span><span id="project-folder" :title="画面.フォルダ.path">{{ 画面.フォルダ.name }}</span></div><button id="toggle" :class="{ awaiting: 画面.編集可能 }" :disabled="画面.接続操作不可" @click="画面.接続切替">{{ 画面.接続ボタン }}</button></div>
  <div id="features" role="group" aria-label="有効な機能"><span v-for="機能 in ['live', 'code']" :id="`feature-${機能}`" :key="機能" class="feature-chip" :class="{ off: !画面.機能[機能] }"><i aria-hidden="true"></i><em>{{ 機能.toUpperCase() }}</em><b>{{ 画面.機能[機能] ? 'ON' : 'OFF' }}</b></span></div>
  <main>
    <div id="settings">
      <div class="section-label">音声会話 <component :is="機能切替" id="live-toggle" :有効="画面.機能.live" :無効="!画面.編集可能 || 画面.保存中 || 画面.操作中" 説明="音声会話（Live）を使う" @切替="画面.ライブ切替" /></div>
      <div class="row"><label for="provider">AI</label><select id="provider" v-model="画面.ライブAI" :disabled="画面.ライブ編集不可" @change="画面.ライブAI変更"><option v-for="(名前, id) in 画面.AI候補" :key="id" :value="id">{{ 名前 }}</option></select><label class="voice-label" for="voice">音声</label><select id="voice" v-model="画面.音声" :disabled="画面.ライブ編集不可" @change="画面.保存"><option v-if="!画面.音声" value="" disabled>候補から選択してください</option><option v-for="(名前, id) in 画面.音声候補" :key="id" :value="id">{{ 名前 }}</option></select></div>
      <div class="row"><label for="model">モデル</label><select id="model" v-model="画面.ライブモデル" :disabled="画面.ライブ編集不可" @change="画面.保存"><option v-if="!画面.ライブモデル" value="" disabled>候補から選択してください</option><option v-for="(名前, id) in 画面.モデル候補" :key="id" :value="id">{{ 名前 }}</option></select></div>
      <div class="section-label code-section">コード <component :is="機能切替" id="code-toggle" :有効="true" :無効="true" 説明="コードは常に ON です" /></div>
      <div class="row"><label for="code-provider">コード AI</label><select id="code-provider" v-model="画面.コードAI" :disabled="画面.コード編集不可" @change="画面.コードAI変更"><option v-for="(名前, id) in 画面.コードAI候補" :key="id" :value="id">{{ 名前 }}</option></select></div>
      <div class="row code-last"><label for="code-model">モデル</label><input id="code-model" v-model="画面.コードモデル" list="code-models" maxlength="300" spellcheck="false" autocomplete="off" placeholder="未指定時はコード AI の既定モデル" :disabled="画面.コード編集不可" @change="画面.保存"><datalist id="code-models"><option v-for="item in 画面.コードモデル候補" :key="item.id" :value="item.id">{{ item.label }}</option></datalist></div>
      <textarea id="error-detail" ref="詳細" readonly :hidden="!画面.接続状態.details" :value="画面.接続状態.details || ''" aria-label="接続エラーの詳細（選択してコピーできます）"></textarea>
      <p class="hint">専用チャンネルに投稿、またはボイスチャンネルに参加。</p>
      <p id="note" class="note" :class="{ error: 画面.案内エラー }" role="status">{{ 画面.案内 }}</p>
    </div>
    <section id="stage" aria-label="最後のやり取り">
      <div class="welcome-mark" aria-hidden="true"><img src="../../frontend_ide/host/media/AiDiy.png" alt=""></div>
      <div id="stage-log" aria-live="polite"><div id="stage-idle" class="stage-entry" :hidden="画面.発言表示"><span class="stage-who">接続先</span><span class="stage-text">専用チャンネルに投稿、またはボイスチャンネルに参加。</span></div><div id="stage-message" class="stage-entry" :hidden="!画面.発言表示" :class="{ fading: 画面.発言消去中 }" :data-role="画面.発言役割"><span id="stage-who" class="stage-who">{{ 画面.発言者 }}</span><span id="stage-text" ref="本文" class="stage-text"><span>{{ 画面.発言本文 }}</span><span v-if="画面.文字表示中" class="terminal-cursor"></span></span></div></div>
    </section>
  </main>
  <button id="monitor" role="switch" :aria-checked="画面.モニター" :disabled="画面.モニター切替中" title="接続中の音声（入力・AI の声）をこのPCで聞く" @click="画面.モニター切替"><span class="monitor-label">モニター</span><span class="switch-track" aria-hidden="true"><span class="switch-knob"></span></span><span id="monitor-state">{{ 画面.モニター ? 'ON' : 'OFF' }}</span></button>
</template>
