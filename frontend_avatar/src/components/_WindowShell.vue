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
import { computed, onBeforeUnmount, ref } from 'vue'

type ResizeDirection =
  | 'n'
  | 's'
  | 'e'
  | 'w'
  | 'ne'
  | 'nw'
  | 'se'
  | 'sw'

const props = withDefaults(defineProps<{
  title: string;
  theme?: 'purple' | 'light';
  closable?: boolean;
  resizable?: boolean;
  closeMode?: 'window' | 'event' | 'minimize';
  chromeVisible?: boolean;
}>(), {
  theme: 'light',
  closable: true,
  resizable: true,
  closeMode: 'window',
  chromeVisible: true,
})

const emit = defineEmits<{
  close: []
}>()

const actionButtonLabel = computed(() => (props.closeMode === 'minimize' ? '−' : '×'))
const actionButtonTitle = computed(() => (props.closeMode === 'minimize' ? '最小化' : '閉じる'))

const リサイズ中 = ref(false)

let 最小幅 = 0
let 最小高 = 0
let 現在方向: ResizeDirection | null = null
let 現在幅 = 0
let 現在高 = 0
let 現在X = 0
let 現在Y = 0
let 初期化済み = false

function closeWindow() {
  if (props.closeMode === 'event') {
    emit('close')
    return
  }
  if (props.closeMode === 'minimize') {
    void window.desktopApi?.minimizeCurrentWindow?.()
    return
  }
  void window.desktopApi?.closeCurrentWindow?.()
}

function 停止リサイズ() {
  リサイズ中.value = false
  現在方向 = null
  初期化済み = false
  window.removeEventListener('pointermove', リサイズ処理)
  window.removeEventListener('pointerup', 停止リサイズ)
}

function 開始リサイズ(event: PointerEvent, direction: ResizeDirection) {
  event.preventDefault()
  event.stopPropagation()

  現在方向 = direction
  初期化済み = false
  リサイズ中.value = true

  // リスナーを即時登録（イベントを取り逃がさないため）
  window.addEventListener('pointermove', リサイズ処理)
  window.addEventListener('pointerup', 停止リサイズ)

  // ウィンドウ情報を非同期取得
  void (async () => {
    const metrics = await window.desktopApi?.getWindowBounds?.()
    if (!metrics || !現在方向) return
    現在幅 = metrics.width
    現在高 = metrics.height
    現在X = metrics.x
    現在Y = metrics.y
    最小幅 = metrics.minWidth
    最小高 = metrics.minHeight
    初期化済み = true
  })()
}

function リサイズ処理(event: PointerEvent) {
  if (!現在方向 || !初期化済み) return

  // movementX/Y を累積（screenX座標系の不一致を回避）
  const dx = event.movementX
  const dy = event.movementY

  let nextX = 現在X
  let nextY = 現在Y
  let nextWidth = 現在幅
  let nextHeight = 現在高

  if (現在方向.includes('e')) {
    nextWidth = Math.max(最小幅, 現在幅 + dx)
  }

  if (現在方向.includes('s')) {
    nextHeight = Math.max(最小高, 現在高 + dy)
  }

  if (現在方向.includes('w')) {
    nextWidth = Math.max(最小幅, 現在幅 - dx)
    nextX = 現在X + (現在幅 - nextWidth)
  }

  if (現在方向.includes('n')) {
    nextHeight = Math.max(最小高, 現在高 - dy)
    nextY = 現在Y + (現在高 - nextHeight)
  }

  // 次回計算のために現在値を更新
  現在幅 = nextWidth
  現在高 = nextHeight
  現在X = nextX
  現在Y = nextY

  void window.desktopApi?.setWindowBounds?.({
    x: nextX,
    y: nextY,
    width: nextWidth,
    height: nextHeight,
  })
}

onBeforeUnmount(() => {
  停止リサイズ()
})
</script>

<template>
  <section
    class="window-shell"
    :class="[`theme-${theme}`, { resizing: リサイズ中, 'chrome-hidden': !chromeVisible }]"
  >
    <header class="window-titlebar">
      <div class="title-left">
        <slot name="title-left"></slot>
        <strong>{{ title }}</strong>
      </div>
      <div class="title-right">
        <slot name="title-right"></slot>
        <button
          v-if="closable"
          class="close-button"
          type="button"
          :title="actionButtonTitle"
          @click="closeWindow"
        >{{ actionButtonLabel }}</button>
      </div>
    </header>

    <div class="window-body">
      <slot></slot>
    </div>

    <template v-if="resizable">
      <button class="resize-handle edge north" type="button" aria-label="resize north" @pointerdown="開始リサイズ($event, 'n')"></button>
      <button class="resize-handle edge south" type="button" aria-label="resize south" @pointerdown="開始リサイズ($event, 's')"></button>
      <button class="resize-handle edge east" type="button" aria-label="resize east" @pointerdown="開始リサイズ($event, 'e')"></button>
      <button class="resize-handle edge west" type="button" aria-label="resize west" @pointerdown="開始リサイズ($event, 'w')"></button>
      <button class="resize-handle corner north-east" type="button" aria-label="resize north east" @pointerdown="開始リサイズ($event, 'ne')"></button>
      <button class="resize-handle corner north-west" type="button" aria-label="resize north west" @pointerdown="開始リサイズ($event, 'nw')"></button>
      <button class="resize-handle corner south-east" type="button" aria-label="resize south east" @pointerdown="開始リサイズ($event, 'se')"></button>
      <button class="resize-handle corner south-west" type="button" aria-label="resize south west" @pointerdown="開始リサイズ($event, 'sw')"></button>
    </template>
  </section>
</template>

<style scoped>
.window-shell {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  border: 1px solid rgba(153, 153, 153, 0.88);
  background: rgba(12, 12, 12, 0.72);
  box-shadow: 0 20px 42px rgba(0, 0, 0, 0.3);
  position: relative;
}

.window-shell.resizing {
  user-select: none;
}

.window-shell.chrome-hidden {
  border-color: transparent;
  background: transparent;
  box-shadow: none;
}

.window-titlebar {
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 0 8px;
  cursor: move;
  -webkit-app-region: drag;
}

.window-shell.chrome-hidden .window-titlebar {
  opacity: 0;
  pointer-events: none;
  border-bottom-color: transparent;
  box-shadow: none;
}

.title-left,
.title-right {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.title-left strong {
  font-size: 0.74rem;
  line-height: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.title-right {
  -webkit-app-region: no-drag;
}

.window-body {
  position: relative;
  height: calc(100% - 28px);
  user-select: text;
}

.close-button {
  width: 20px;
  height: 20px;
  border: none;
  background: rgba(0, 0, 0, 0.72);
  color: #fff;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  line-height: 1;
  padding: 0;
}

.resize-handle {
  position: absolute;
  border: none;
  background: transparent;
  padding: 0;
  margin: 0;
  opacity: 0;
  z-index: 20;
}

.window-shell.chrome-hidden .resize-handle {
  pointer-events: none;
}

.resize-handle:hover,
.window-shell.resizing .resize-handle {
  opacity: 1;
}

.edge.north,
.edge.south {
  left: 10px;
  right: 10px;
  height: 8px;
  cursor: ns-resize;
}

.edge.north {
  top: 0;
}

.edge.south {
  bottom: 0;
}

.edge.east,
.edge.west {
  top: 10px;
  bottom: 10px;
  width: 8px;
  cursor: ew-resize;
}

.edge.east {
  right: 0;
}

.edge.west {
  left: 0;
}

.corner {
  width: 14px;
  height: 14px;
}

.corner.north-east {
  top: 0;
  right: 0;
  cursor: nesw-resize;
}

.corner.north-west {
  top: 0;
  left: 0;
  cursor: nwse-resize;
}

.corner.south-east {
  right: 0;
  bottom: 0;
  cursor: nwse-resize;
}

.corner.south-west {
  left: 0;
  bottom: 0;
  cursor: nesw-resize;
}

.theme-purple {
  border-color: rgba(143, 124, 255, 0.58);
  background: rgba(6, 8, 14, 0.18);
}

.theme-purple .window-titlebar {
  border-bottom: 1px solid rgba(93, 68, 168, 0.95);
  background: linear-gradient(135deg, rgba(108, 78, 196, 0.94), rgba(143, 104, 221, 0.9));
  color: #fff;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.16),
    inset 0 -1px 0 rgba(44, 24, 101, 0.3);
}

.theme-purple .resize-handle:hover {
  background: rgba(162, 143, 255, 0.18);
}

.theme-light .window-titlebar {
  border-bottom: 1px solid rgba(120, 120, 120, 0.9);
  background: rgba(200, 200, 200, 0.92);
  color: #222;
}

.theme-light .resize-handle:hover {
  background: rgba(110, 110, 110, 0.14);
}
</style>
