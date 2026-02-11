<!--
  -*- coding: utf-8 -*-

  ------------------------------------------------
  COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
  This software is licensed under the MIT License.
  https://github.com/monjyu1101
  Thank you for keeping the rules.
  ------------------------------------------------
-->

<script setup lang="ts">
import { ref } from 'vue';
import { useRoute } from 'vue-router';
import apiClient from '@/api/client';
import { qConfirm } from '@/utils/qAlert';
import RebootDialog from './再起動カウントダウン.vue';

const route = useRoute();

const props = defineProps<{
  show: boolean;
  files: string[];
  isAiDiyMode: boolean;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
}>();

const loading = ref(false);
const showRebootDialog = ref(false);
const rebootWaitSeconds = ref(15);

const handleClose = () => {
  emit('close');
};

const handleAppReboot = async () => {
  const confirmed = await qConfirm('アプリケーションを再起動します。よろしいですか？');
  if (!confirmed) return;

  loading.value = true;

  try {
    const セッションID = route.query.セッションID as string;
    if (!セッションID) {
      alert('セッションIDが見つかりません。画面をリロードしてください。');
      loading.value = false;
      return;
    }

    const response = await apiClient.post('/core/AIコア/モデル情報/設定', {
      セッションID,
      モデル設定: {},
      再起動要求: { reboot_core: false, reboot_apps: true }
    });

    if (response?.data?.status === 'OK') {
      rebootWaitSeconds.value = 15;
      showRebootDialog.value = true;
    } else {
      alert(response?.data?.message || 'アプリ再起動に失敗しました');
    }
  } catch (error: any) {
    alert(`アプリ再起動エラー: ${error?.response?.data?.message || error?.message || error}`);
  } finally {
    loading.value = false;
  }
};

const handleResetReboot = async () => {
  const confirmed = await qConfirm('現在のAI設定をすべてリセットし、システムを再起動します。よろしいですか？');
  if (!confirmed) return;

  loading.value = true;

  try {
    const セッションID = route.query.セッションID as string;
    if (!セッションID) {
      alert('セッションIDが見つかりません。画面をリロードしてください。');
      loading.value = false;
      return;
    }

    const response = await apiClient.post('/core/AIコア/モデル情報/設定', {
      セッションID,
      モデル設定: {},
      再起動要求: { reboot_core: true, reboot_apps: true }
    });

    if (response?.data?.status === 'OK') {
      rebootWaitSeconds.value = 45;
      showRebootDialog.value = true;
    } else {
      alert(response?.data?.message || 'リセット再起動に失敗しました');
    }
  } catch (error: any) {
    alert(`リセット再起動エラー: ${error?.response?.data?.message || error?.message || error}`);
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div v-if="show" class="update-files-dialog-overlay" @click.self="handleClose">
    <div class="update-files-dialog">
      <!-- タイトル -->
      <div class="update-files-dialog-title">🔄 CodeAI がファイルを更新しました</div>

      <!-- ファイル数表示 -->
      <div class="update-files-count">更新ファイル数: {{ files.length }}件</div>

      <!-- ファイルリスト -->
      <div class="update-files-list-container">
        <div class="update-files-list">
          <div v-for="(file, index) in files" :key="index" class="update-file-item">
            {{ index + 1 }}. {{ file }}
          </div>
        </div>
      </div>

      <!-- 確認メッセージ -->
      <div class="update-files-confirm-message">システムを再起動しますか？</div>

      <!-- ボタン -->
      <div class="update-files-dialog-actions">
        <button type="button" class="cancel-button" @click="handleClose">キャンセル</button>
        <button
          v-if="isAiDiyMode"
          type="button"
          class="app-reboot-button"
          :disabled="loading"
          @click="handleAppReboot"
        >
          アプリ再起動
        </button>
        <button
          v-if="isAiDiyMode"
          type="button"
          class="reset-reboot-button"
          :disabled="loading"
          @click="handleResetReboot"
        >
          リセット再起動
        </button>
      </div>
    </div>
  </div>

  <RebootDialog :show="showRebootDialog" :wait-seconds="rebootWaitSeconds" />
</template>

<style scoped>
/* オーバーレイ */
.update-files-dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  backdrop-filter: blur(4px);
}

/* ダイアログ本体 */
.update-files-dialog {
  background: linear-gradient(135deg, rgba(40, 10, 25, 0.95), rgba(50, 15, 35, 0.95));
  color: #ffe0f0;
  padding: 28px 32px;
  border-radius: 12px;
  border: 2px solid #ff69b4;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5), 0 0 30px rgba(255, 105, 180, 0.4);
  font-family: 'Courier New', monospace;
  min-width: 420px;
  max-width: 600px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

/* タイトル */
.update-files-dialog-title {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 8px;
  color: #ffb6d9;
  text-align: center;
  text-shadow: 0 0 10px rgba(255, 105, 180, 0.6);
}

/* ファイル数表示 */
.update-files-count {
  font-size: 14px;
  margin-bottom: 16px;
  color: #ffc0e0;
  text-align: center;
}

/* ファイルリストコンテナ */
.update-files-list-container {
  margin-bottom: 20px;
}

.update-files-list {
  background: rgba(20, 5, 15, 0.6);
  border: 1px solid rgba(255, 105, 180, 0.3);
  border-radius: 6px;
  padding: 12px;
  max-height: 300px;
  overflow-y: auto;
  font-size: 13px;
  line-height: 1.6;
}

/* カスタムスクロールバー */
.update-files-list::-webkit-scrollbar {
  width: 8px;
}

.update-files-list::-webkit-scrollbar-track {
  background: rgba(20, 5, 15, 0.4);
  border-radius: 4px;
}

.update-files-list::-webkit-scrollbar-thumb {
  background: rgba(255, 105, 180, 0.5);
  border-radius: 4px;
}

.update-files-list::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 105, 180, 0.7);
}

/* ファイルアイテム */
.update-file-item {
  padding: 6px 8px;
  margin-bottom: 4px;
  background: rgba(255, 105, 180, 0.1);
  border-left: 3px solid #ff69b4;
  border-radius: 3px;
  color: #ffd0e8;
  word-break: break-all;
}

/* 確認メッセージ */
.update-files-confirm-message {
  font-size: 15px;
  margin-bottom: 20px;
  color: #ffb6d9;
  text-align: center;
  font-weight: bold;
}

/* ボタンコンテナ */
.update-files-dialog-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.update-files-dialog-actions button {
  padding: 10px 24px;
  border-radius: 6px;
  cursor: pointer;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  transition: all 0.2s;
  border: 1px solid;
}

.update-files-dialog-actions button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* キャンセルボタン */
.cancel-button {
  background: rgba(100, 100, 100, 0.3);
  color: #e0e0e0;
  border-color: rgba(200, 200, 200, 0.3);
}

.cancel-button:hover:not(:disabled) {
  background: rgba(150, 150, 150, 0.4);
  border-color: rgba(200, 200, 200, 0.5);
}

/* アプリ再起動ボタン（青系） */
.app-reboot-button {
  background: linear-gradient(135deg, #4169e1, #1e90ff);
  color: #ffffff;
  border-color: #1e90ff;
  font-weight: bold;
  box-shadow: 0 4px 12px rgba(30, 144, 255, 0.4);
}

.app-reboot-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #1e90ff, #00bfff);
  box-shadow: 0 6px 16px rgba(30, 144, 255, 0.6);
  transform: translateY(-1px);
}

.app-reboot-button:active:not(:disabled) {
  transform: translateY(0);
}

/* リセット再起動ボタン（赤系） */
.reset-reboot-button {
  background: linear-gradient(135deg, #ff1493, #ff69b4);
  color: #ffffff;
  border-color: #ff69b4;
  font-weight: bold;
  box-shadow: 0 4px 12px rgba(255, 20, 147, 0.4);
}

.reset-reboot-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #ff0080, #ff1493);
  box-shadow: 0 6px 16px rgba(255, 20, 147, 0.6);
  transform: translateY(-1px);
}

.reset-reboot-button:active:not(:disabled) {
  transform: translateY(0);
}
</style>
