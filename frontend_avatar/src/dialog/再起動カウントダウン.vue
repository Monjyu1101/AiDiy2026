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

<template>
  <div v-if="isVisible" class="reboot-overlay">
    <div class="reboot-dialog">
      <div class="reboot-title">
        <span class="reboot-icon">↻</span>
        <span>システム再起動</span>
      </div>
      <div class="reboot-message">
        システムが再起動します。
      </div>
      <div class="countdown-number">{{ countdown }}</div>
      <div class="reboot-subtext">秒後に画面が自動的にリロードされます。</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  show: boolean
  waitSeconds?: number
}>()

const isVisible = ref(false)
const countdown = ref(0)
let timer: number | ReturnType<typeof setInterval> | undefined

watch(
  () => props.show,
  (newVal) => {
    if (newVal) {
      startCountdown(props.waitSeconds || 15)
    } else {
      stopCountdown()
    }
  },
)

function startCountdown(seconds: number) {
  isVisible.value = true
  countdown.value = seconds

  if (timer) {
    clearInterval(timer)
  }

  timer = window.setInterval(() => {
    countdown.value -= 1
    if (countdown.value <= 0) {
      stopCountdown()
      reloadPage()
    }
  }, 1000)
}

function stopCountdown() {
  if (timer) {
    clearInterval(timer)
    timer = undefined
  }
  isVisible.value = false
}

function reloadPage() {
  if (window.parent && window.parent !== window) {
    window.parent.location.reload()
  } else {
    window.location.reload()
  }
}
</script>

<style scoped>
.reboot-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  backdrop-filter: blur(8px);
}

.reboot-dialog {
  background: linear-gradient(135deg, #1a202c, #2d3748);
  color: #edf2f7;
  padding: 40px 50px;
  border-radius: 12px;
  border: 2px solid #4299e1;
  box-shadow: 0 15px 45px rgba(0, 0, 0, 0.6), 0 0 30px rgba(66, 153, 225, 0.4);
  font-family: 'Segoe UI', 'Roboto', sans-serif;
  min-width: 380px;
  text-align: center;
}

.reboot-title {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 15px;
  color: #63b3ed;
  letter-spacing: 1px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.reboot-icon {
  display: inline-flex;
  animation: spin 2s linear infinite;
}

.reboot-message {
  font-size: 16px;
  margin-bottom: 20px;
  color: #cbd5e0;
  line-height: 1.5;
}

.countdown-number {
  font-size: 64px;
  font-weight: 800;
  color: #48bb78;
  margin: 10px 0;
  text-shadow: 0 0 15px rgba(72, 187, 120, 0.8);
  animation: pulse 1.5s infinite alternate;
}

.reboot-subtext {
  font-size: 14px;
  color: #a0aec0;
  margin-top: 15px;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes pulse {
  from { transform: scale(1); }
  to { transform: scale(1.05); }
}
</style>
