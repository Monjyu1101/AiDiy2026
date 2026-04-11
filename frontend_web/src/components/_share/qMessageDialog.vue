<!--
  -*- coding: utf-8 -*-

  -------------------------------------------------------------------------
  COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
  Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
  Commercial use requires prior written consent from all copyright holders.
  See LICENSE for full terms. Thank you for keeping the rules.
  https://github.com/monjyu1101/AiDiy2026
  -------------------------------------------------------------------------
-->

<script setup lang="ts">
import { ref, onBeforeUnmount } from 'vue';

const DEFAULT_DURATION_MS = 3000;

const isVisible = ref(false);
const message = ref('');
const messageType = ref('success');
let hideTimer: ReturnType<typeof setTimeout> | null = null;
let resolvePromise: (() => void) | null = null;

const clearTimer = () => {
  if (!hideTimer) return;
  clearTimeout(hideTimer);
  hideTimer = null;
};

const finish = () => {
  clearTimer();
  isVisible.value = false;
  if (resolvePromise) {
    resolvePromise();
    resolvePromise = null;
  }
};

const show = (
  nextMessage: string,
  nextType = 'success',
  durationMs = DEFAULT_DURATION_MS
): Promise<void> => {
  clearTimer();
  if (resolvePromise) {
    resolvePromise();
    resolvePromise = null;
  }

  message.value = nextMessage;
  messageType.value = nextType;
  isVisible.value = true;

  return new Promise((resolve) => {
    resolvePromise = resolve;
    const delay = typeof durationMs === 'number' ? durationMs : DEFAULT_DURATION_MS;
    if (delay > 0) {
      hideTimer = setTimeout(() => {
        finish();
      }, delay);
    }
  });
};

onBeforeUnmount(() => {
  clearTimer();
  if (resolvePromise) {
    resolvePromise();
    resolvePromise = null;
  }
});

defineExpose({ show });
</script>

<template>
  <teleport to="body">
    <transition name="message-fade">
      <div
        v-if="isVisible"
        class="message-toast"
        :class="`message-${messageType}`"
        @click="finish"
      >
        {{ message }}
      </div>
    </transition>
  </teleport>
</template>

<style scoped>
.message-toast {
  position: fixed;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10001;
  min-width: 260px;
  max-width: min(720px, calc(100vw - 32px));
  padding: 12px 18px;
  border: 1px solid #cbd5e1;
  background: #fff;
  color: #1f2937;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.2);
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  cursor: pointer;
}

.message-success {
  border-color: #b7dfc2;
  background: #eaf8ef;
  color: #166534;
}

.message-error {
  border-color: #efb0b7;
  background: #fdecee;
  color: #991b1b;
}

.message-info {
  border-color: #b9d4f7;
  background: #eef5ff;
  color: #1d4ed8;
}

.message-fade-enter-active,
.message-fade-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.message-fade-enter-from,
.message-fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-6px);
}
</style>
