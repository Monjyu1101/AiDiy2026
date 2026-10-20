<!--
  COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
  Licensed under "AiDiy 公開利用ライセンス v1.1". See LICENSE.
-->
<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

withDefaults(defineProps<{ closable?: boolean }>(), { closable: true })
const emit = defineEmits<{ close: [] }>()
const ピン状態 = ref<AvatarWindowPinState>({ pinned: false, locked: false })
const ピン読込済み = ref(false)
const ピン変更中 = ref(false)
const ピン説明 = computed(() => ピン状態.value.locked
  ? 'VRモード中は最前面のピン止めを解除できません'
  : ピン状態.value.pinned ? '最前面のピン止めを解除' : '最前面にピン止め')
let 購読解除: (() => void) | undefined
let 更新番号 = 0
let 破棄済み = false

function 最小化() {
  void window.desktopApi?.minimizeCurrentWindow?.()
}

function 最大化切替() {
  void window.desktopApi?.toggleMaximizeCurrentWindow?.()
}

function ピン状態反映(state: AvatarWindowPinState | null | undefined) {
  if (!state || 破棄済み) return
  更新番号 += 1
  ピン状態.value = state
  ピン読込済み.value = true
}

async function ピン切替() {
  if (!ピン読込済み.value || ピン状態.value.locked || ピン変更中.value) return
  ピン変更中.value = true
  const 変更番号 = 更新番号
  try {
    const state = await window.desktopApi?.toggleWindowPin?.()
    if (変更番号 === 更新番号) ピン状態反映(state)
  } catch (error) {
    console.error('[window-pin] toggle failed:', error)
  } finally {
    ピン変更中.value = false
  }
}

onMounted(async () => {
  購読解除 = window.desktopApi?.onWindowPinChanged?.(ピン状態反映)
  const 読込番号 = 更新番号
  try {
    const state = await window.desktopApi?.getWindowPinState?.()
    // 読込中にmainから通知が届いた場合は、古い取得結果で上書きしない。
    if (読込番号 === 更新番号) ピン状態反映(state)
  } catch (error) {
    console.error('[window-pin] read failed:', error)
  }
})

onBeforeUnmount(() => {
  破棄済み = true
  購読解除?.()
})
</script>

<template>
  <div class="window-controls" data-aidiy-no-window-move @pointerdown.stop>
    <button
      class="window-control" type="button" title="最小化" aria-label="最小化"
      @click="最小化"
    >−</button>
    <button
      class="window-control" type="button" title="最大化 / 元に戻す" aria-label="最大化 / 元に戻す"
      @click="最大化切替"
    >□</button>
    <button
      class="window-control pin-button" :class="{ pinned: ピン状態.pinned }"
      type="button" :title="ピン説明" :aria-label="ピン説明" :aria-pressed="ピン状態.pinned"
      :disabled="!ピン読込済み || ピン状態.locked || ピン変更中" @click="ピン切替"
    >📌</button>
    <button
      v-if="closable" class="window-control close-button" type="button" title="閉じる" aria-label="閉じる"
      @click="emit('close')"
    >×</button>
  </div>
</template>

<style scoped>
.window-controls {
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;
  gap: 2px;
  -webkit-app-region: no-drag;
}

.window-control {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  padding: 0;
  border: none;
  border-radius: 2px;
  background: rgba(0, 0, 0, 0.72);
  color: #fff;
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
  -webkit-app-region: no-drag;
}

.window-control:hover:not(:disabled) {
  background: rgba(0, 0, 0, 0.9);
}

.window-control:focus-visible {
  outline: 2px solid #c4b5fd;
  outline-offset: 1px;
}

.pin-button {
  font-size: 12px;
  filter: grayscale(1);
  opacity: 0.56;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.85);
}

.pin-button.pinned {
  background: #6d4eaf;
  filter: none;
  opacity: 1;
  box-shadow: inset 0 0 0 1px rgba(222, 206, 255, 0.65);
}

.window-control:disabled {
  cursor: default;
}

.close-button:hover {
  background: #b33b48;
}
</style>
