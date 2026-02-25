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
import { computed, ref, watch } from 'vue';
import { シキHTML生成 } from '@/utils/shiki';

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

const ハイライトHTML = ref('');
let ハイライト要求連番 = 0;

const テキストハイライト更新 = async () => {
  if (!props.show || !テキスト表示.value || !テキスト内容.value) {
    ハイライトHTML.value = '';
    return;
  }

  const 現在連番 = ++ハイライト要求連番;
  try {
    const html = await シキHTML生成(テキスト内容.value, props.ファイル名);
    if (現在連番 !== ハイライト要求連番) return;
    ハイライトHTML.value = html;
  } catch {
    if (現在連番 !== ハイライト要求連番) return;
    ハイライトHTML.value = '';
  }
};

watch(
  [() => props.show, () => props.ファイル名, () => props.base64_data, テキスト表示],
  () => {
    void テキストハイライト更新();
  },
  { immediate: true }
);

const handleClose = () => {
  emit('close');
};

const handleDownload = () => {
  if (!props.base64_data) return;
  const ベース名 = props.ファイル名.replace(/\\/g, '/').split('/').pop() ?? props.ファイル名;
  const a = document.createElement('a');
  a.href = `data:application/octet-stream;base64,${props.base64_data}`;
  a.download = ベース名;
  a.click();
};
</script>

<template>
  <div v-if="show" class="file-content-overlay" @click.self="handleClose">
    <div class="file-content-dialog">
      <div class="file-name">{{ ファイル名 }}</div>

      <div class="file-content-body">
        <img v-if="画像表示 && 画像DataUrl" class="preview-image" :src="画像DataUrl" alt="image preview" />
        <div v-else-if="テキスト表示 && ハイライトHTML" class="preview-text preview-highlight" v-html="ハイライトHTML"></div>
        <pre v-else-if="テキスト表示" class="preview-text">{{ テキスト内容 }}</pre>
        <div v-else class="unsupported-message">この拡張子はプレビュー対象外です。</div>
      </div>

      <div class="file-content-footer">
        <button type="button" class="btn-download" @click="handleDownload" :disabled="!base64_data">ダウンロード</button>
        <button type="button" class="btn-close" @click="handleClose">閉じる</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
@keyframes fadeIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}

.file-content-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10001;
  animation: fadeIn 0.3s ease;
}

.file-content-dialog {
  max-width: 90%;
  max-height: 90%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.file-content-header {
  display: none;
}

.file-name {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  word-break: break-all;
  color: #ffffff;
  text-align: center;
}

.file-content-body {
  overflow: auto;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-image {
  display: block;
  max-width: 100%;
  max-height: calc(90vh - 120px);
  object-fit: contain;
  border-radius: 4px;
  box-shadow: 0 4px 20px rgba(255, 255, 255, 0.3);
}

.preview-text {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  color: #e5e7eb;
  background: rgba(0, 0, 0, 0.4);
  padding: 12px;
  border-radius: 4px;
  max-height: calc(90vh - 140px);
  overflow: auto;
}

.preview-highlight {
  padding: 0;
  background: transparent;
}

.preview-highlight :deep(pre.shiki-pre) {
  margin: 0;
  padding: 12px;
  background: transparent !important;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.5;
  max-height: calc(90vh - 140px);
  overflow: auto;
}

.preview-highlight :deep(pre.shiki-pre code) {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-word;
}

.unsupported-message {
  color: #9ca3af;
  font-size: 13px;
}

.file-content-footer {
  display: flex;
  justify-content: center;
  gap: 15px;
  flex-shrink: 0;
}

.btn-download,
.btn-close {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.btn-download {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
}

.btn-download:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.5);
}

.btn-download:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-close {
  background: #808080;
  color: white;
}

.btn-close:hover {
  background: #666666;
  transform: scale(1.05);
}
</style>
