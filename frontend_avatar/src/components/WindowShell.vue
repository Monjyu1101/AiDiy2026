<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'

type ResizeDirection =
  | 'n'
  | 's'
  | 'e'
  | 'w'
  | 'ne'
  | 'nw'
  | 'se'
  | 'sw'

withDefaults(defineProps<{
  title: string;
  theme?: 'purple' | 'light';
  closable?: boolean;
  resizable?: boolean;
}>(), {
  theme: 'light',
  closable: true,
  resizable: true,
})

const リサイズ中 = ref(false)

let 開始X = 0
let 開始Y = 0
let 開始幅 = 0
let 開始高 = 0
let 開始左 = 0
let 開始上 = 0
let 最小幅 = 0
let 最小高 = 0
let 現在方向: ResizeDirection | null = null

function closeWindow() {
  void window.desktopApi?.closeCurrentWindow?.()
}

function 停止リサイズ() {
  リサイズ中.value = false
  現在方向 = null
  window.removeEventListener('pointermove', リサイズ処理)
  window.removeEventListener('pointerup', 停止リサイズ)
}

async function 開始リサイズ(event: PointerEvent, direction: ResizeDirection) {
  event.preventDefault()
  event.stopPropagation()

  const metrics = await window.desktopApi?.getWindowBounds?.()
  if (!metrics) return

  開始X = event.screenX
  開始Y = event.screenY
  開始左 = metrics.x
  開始上 = metrics.y
  開始幅 = metrics.width
  開始高 = metrics.height
  最小幅 = metrics.minWidth
  最小高 = metrics.minHeight
  現在方向 = direction
  リサイズ中.value = true

  window.addEventListener('pointermove', リサイズ処理)
  window.addEventListener('pointerup', 停止リサイズ)
}

function リサイズ処理(event: PointerEvent) {
  if (!現在方向) return

  const deltaX = event.screenX - 開始X
  const deltaY = event.screenY - 開始Y

  let nextX = 開始左
  let nextY = 開始上
  let nextWidth = 開始幅
  let nextHeight = 開始高

  if (現在方向.includes('e')) {
    nextWidth = Math.max(最小幅, 開始幅 + deltaX)
  }

  if (現在方向.includes('s')) {
    nextHeight = Math.max(最小高, 開始高 + deltaY)
  }

  if (現在方向.includes('w')) {
    const rawWidth = 開始幅 - deltaX
    nextWidth = Math.max(最小幅, rawWidth)
    nextX = 開始左 + (開始幅 - nextWidth)
  }

  if (現在方向.includes('n')) {
    const rawHeight = 開始高 - deltaY
    nextHeight = Math.max(最小高, rawHeight)
    nextY = 開始上 + (開始高 - nextHeight)
  }

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
  <section class="window-shell" :class="[`theme-${theme}`, { resizing: リサイズ中 }]">
    <header class="window-titlebar">
      <div class="title-left">
        <slot name="title-left"></slot>
        <strong>{{ title }}</strong>
      </div>
      <div class="title-right">
        <slot name="title-right"></slot>
        <button v-if="closable" class="close-button" type="button" @click="closeWindow">×</button>
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
