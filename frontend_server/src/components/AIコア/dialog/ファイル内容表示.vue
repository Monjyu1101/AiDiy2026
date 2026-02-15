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

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  show: boolean;
  ファイル名: string;
  base64_data: string;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
}>();

const 画像MIME辞書: Record<string, string> = {
  png: 'image/png',
  jpg: 'image/jpeg',
  jpeg: 'image/jpeg',
  gif: 'image/gif',
  webp: 'image/webp',
  bmp: 'image/bmp',
  svg: 'image/svg+xml'
};

const テキスト拡張子セット = new Set([
  'py', 'vue', 'ts', 'tsx', 'js', 'jsx', 'json', 'md', 'txt',
  'html', 'css', 'scss', 'sass', 'less', 'yml', 'yaml', 'toml',
  'ini', 'env', 'sql', 'csv', 'log', 'xml', 'sh', 'ps1', 'bat'
]);

const 拡張子 = computed(() => {
  const クエリ除去 = (props.ファイル名 || '').split(/[?#]/u, 1)[0] || '';
  const 最後のスラッシュ位置 = Math.max(クエリ除去.lastIndexOf('/'), クエリ除去.lastIndexOf('\\'));
  const ベース名 = 最後のスラッシュ位置 >= 0 ? クエリ除去.slice(最後のスラッシュ位置 + 1) : クエリ除去;
  const ドット位置 = ベース名.lastIndexOf('.');
  if (ドット位置 < 0) return '';
  return ベース名.slice(ドット位置 + 1).toLowerCase();
});

const 画像表示 = computed(() => !!画像MIME辞書[拡張子.value]);
const テキスト表示 = computed(() => テキスト拡張子セット.has(拡張子.value));

const 画像DataUrl = computed(() => {
  if (!画像表示.value || !props.base64_data) return '';
  return `data:${画像MIME辞書[拡張子.value]};base64,${props.base64_data}`;
});

const テキスト内容 = computed(() => {
  if (!テキスト表示.value || !props.base64_data) return '';
  try {
    const binary = window.atob(props.base64_data);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return new TextDecoder('utf-8').decode(bytes);
  } catch (error) {
    return `テキストデコードに失敗しました: ${error}`;
  }
});

const handleClose = () => {
  emit('close');
};
</script>

<template>
  <div v-if="show" class="file-content-overlay" @click.self="handleClose">
    <div class="file-content-dialog">
      <div class="file-content-header">
        <div class="file-content-title">ファイル内容表示</div>
        <button type="button" class="close-button" @click="handleClose">×</button>
      </div>

      <div class="file-name">{{ ファイル名 }}</div>

      <div class="file-content-body">
        <img v-if="画像表示 && 画像DataUrl" class="preview-image" :src="画像DataUrl" alt="image preview" />
        <pre v-else-if="テキスト表示" class="preview-text">{{ テキスト内容 }}</pre>
        <div v-else class="unsupported-message">この拡張子はプレビュー対象外です。</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.file-content-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10001;
}

.file-content-dialog {
  width: min(1000px, 92vw);
  max-height: 88vh;
  background: #0f1115;
  color: #e5e7eb;
  border: 1px solid #30363d;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.file-content-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-bottom: 1px solid #30363d;
}

.file-content-title {
  font-size: 14px;
  font-weight: 700;
}

.close-button {
  width: 28px;
  height: 28px;
  border: 1px solid #444c56;
  background: #161b22;
  color: #e5e7eb;
  border-radius: 4px;
  cursor: pointer;
}

.close-button:hover {
  background: #1f2630;
}

.file-name {
  padding: 10px 14px;
  border-bottom: 1px solid #30363d;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  word-break: break-all;
}

.file-content-body {
  padding: 12px 14px;
  overflow: auto;
  min-height: 200px;
}

.preview-image {
  display: block;
  max-width: 100%;
  max-height: 72vh;
  margin: 0 auto;
  border: 1px solid #30363d;
}

.preview-text {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.unsupported-message {
  color: #9ca3af;
  font-size: 13px;
}
</style>
