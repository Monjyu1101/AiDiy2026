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

const isVisible = ref(false);
const message = ref('');
const resolvePromise = ref<((value: void) => void) | null>(null);

const show = (msg: string): Promise<void> => {
  message.value = msg;
  isVisible.value = true;

  return new Promise((resolve) => {
    resolvePromise.value = resolve;
  });
};

const handleOk = () => {
  isVisible.value = false;
  if (resolvePromise.value) {
    resolvePromise.value();
    resolvePromise.value = null;
  }
};

defineExpose({ show });
</script>

<template>
  <teleport to="body">
    <div v-if="isVisible" class="dialog-overlay" @click.self="handleOk">
      <div class="dialog-container">
        <div class="dialog-content">
          <div class="dialog-message">{{ message }}</div>
          <div class="dialog-buttons">
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
</style>

