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
import { ref } from 'vue';

const isVisible = ref(false);
const message = ref('');
const dialogMode = ref<'alert' | 'confirm'>('alert');
const resolveAlertPromise = ref<(() => void) | null>(null);
const resolveConfirmPromise = ref<((value: boolean) => void) | null>(null);

const show = (msg: string): Promise<void> => {
  dialogMode.value = 'alert';
  message.value = msg;
  isVisible.value = true;
  resolveConfirmPromise.value = null;

  return new Promise((resolve) => {
    resolveAlertPromise.value = resolve;
  });
};

const showConfirm = (msg: string): Promise<boolean> => {
  dialogMode.value = 'confirm';
  message.value = msg;
  isVisible.value = true;
  resolveAlertPromise.value = null;

  return new Promise((resolve) => {
    resolveConfirmPromise.value = resolve;
  });
};

const handleOk = () => {
  isVisible.value = false;
  if (dialogMode.value === 'confirm') {
    if (resolveConfirmPromise.value) {
      resolveConfirmPromise.value(true);
      resolveConfirmPromise.value = null;
    }
    return;
  }
  if (resolveAlertPromise.value) {
    resolveAlertPromise.value();
    resolveAlertPromise.value = null;
  }
};

const handleCancel = () => {
  isVisible.value = false;
  if (resolveConfirmPromise.value) {
    resolveConfirmPromise.value(false);
    resolveConfirmPromise.value = null;
  }
};

const handleOverlayClick = () => {
  if (dialogMode.value === 'confirm') {
    handleCancel();
    return;
  }
  handleOk();
};

defineExpose({ show, showConfirm });
</script>

<template>
  <teleport to="body">
    <div v-if="isVisible" class="dialog-overlay" @click.self="handleOverlayClick">
      <div class="dialog-container">
        <div class="dialog-content">
          <div class="dialog-message">{{ message }}</div>
          <div class="dialog-buttons">
            <button
              v-if="dialogMode === 'confirm'"
              class="dialog-btn dialog-btn-cancel"
              @click="handleCancel"
            >
              キャンセル
            </button>
            <button class="dialog-btn dialog-btn-ok" @click="handleOk">
              OK
            </button>
          </div>
        </div>
      </div>
    </div>
  </teleport>
</template>

<style scoped>
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
}

.dialog-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  min-width: 320px;
  max-width: 500px;
  margin: 20px;
}

.dialog-content {
  padding: 24px;
}

.dialog-message {
  font-size: 14px;
  line-height: 1.6;
  color: #333;
  margin-bottom: 24px;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.dialog-buttons {
  display: flex;
  justify-content: center;
  gap: 10px;
}

.dialog-btn {
  padding: 8px 24px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background-color 0.2s;
  min-width: 80px;
}

.dialog-btn-ok {
  background-color: #007bff;
  color: white;
}

.dialog-btn-ok:hover {
  background-color: #0056b3;
}

.dialog-btn-cancel {
  background-color: #6c757d;
  color: white;
}

.dialog-btn-cancel:hover {
  background-color: #545b62;
}
</style>

