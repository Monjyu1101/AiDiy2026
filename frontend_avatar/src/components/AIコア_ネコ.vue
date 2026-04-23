<!--
  -*- coding: utf-8 -*-

  -------------------------------------------------------------------------
  COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
  Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
  Commercial use requires prior written consent from all keyword holders.
  See LICENSE for full terms. Thank you for keeping the rules.
  https://github.com/monjyu1101/AiDiy2026
  -------------------------------------------------------------------------
-->

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'

type SpriteName =
  | 'idle' | 'alert' | 'scratchSelf'
  | 'scratchWallN' | 'scratchWallS' | 'scratchWallE' | 'scratchWallW'
  | 'tired' | 'sleeping'
  | 'N' | 'NE' | 'E' | 'SE' | 'S' | 'SW' | 'W' | 'NW'

type SpritePoint = readonly [number, number]

const props = defineProps<{ showBoundary?: boolean }>()

const stageRef = ref<HTMLDivElement | null>(null)
const nekoRef  = ref<HTMLDivElement | null>(null)
const isSleeping = ref(false)

// ネコの移動可能領域の余白（この外にマウスが入るとネコは境界で止まってカキかきする）
const CAT_MARGIN = 60
const CAT_MARGIN_BOTTOM = 90  // 左下チェックボックス分だけ広めに
const SLEEP_AFTER = 300  // 100ms × 300 = 30秒

const nekoSpeed = 10
const spriteSets: Record<SpriteName, readonly SpritePoint[]> = {
  idle:         [[-3, -3]],
  alert:        [[-7, -3]],
  scratchSelf:  [[-5, 0], [-6, 0], [-7, 0]],
  scratchWallN: [[0, 0], [0, -1]],
  scratchWallS: [[-7, -1], [-6, -2]],
  scratchWallE: [[-2, -2], [-2, -3]],
  scratchWallW: [[-4, 0], [-4, -1]],
  tired:        [[-3, -2]],
  sleeping:     [[-2, 0], [-2, -1]],
  N:  [[-1, -2], [-1, -3]],
  NE: [[0, -2], [0, -3]],
  E:  [[-3, 0], [-3, -1]],
  SE: [[-5, -1], [-5, -2]],
  S:  [[-6, -3], [-7, -2]],
  SW: [[-5, -3], [-6, -1]],
  W:  [[-4, -2], [-4, -3]],
  NW: [[-1, 0], [-1, -1]],
}

let animationId = 0
let lastFrameTimestamp = 0
let frameCount = 0
let idleTime = 0
let idleAnimation: SpriteName | null = null
let idleAnimationFrame = 0
let sleepFrames = 0
let nekoPosX = 32
let nekoPosY = 32
let mousePosX = 180
let mousePosY = 160
let noMouseFrames = 0  // マウス未操作フレーム数

const NO_MOUSE_IDLE = 150  // 15秒後にマウスをネコ頭上へ

const clamp = (v: number, lo: number, hi: number) => Math.min(Math.max(v, lo), hi)

const catMinX = (width: number)  => CAT_MARGIN
const catMaxX = (width: number)  => width  - CAT_MARGIN
const catMinY = (height: number) => CAT_MARGIN
const catMaxY = (height: number) => height - CAT_MARGIN_BOTTOM

const setSprite = (name: SpriteName, frame: number) => {
  const el = nekoRef.value
  if (!el) return
  const sp = spriteSets[name][frame % spriteSets[name].length]
  el.style.backgroundPosition = `${sp[0] * 32}px ${sp[1] * 32}px`
}

const applyPosition = () => {
  const el = nekoRef.value
  if (!el) return
  el.style.left = `${nekoPosX - 16}px`
  el.style.top  = `${nekoPosY - 16}px`
}

const resetIdleAnimation = () => {
  idleAnimation      = null
  idleAnimationFrame = 0
  sleepFrames        = 0
  isSleeping.value   = false
}

const wakeUpAndRun = (width: number, height: number) => {
  resetIdleAnimation()
  idleTime = 0
  noMouseFrames = 0
  const roll = Math.random()
  const midY = CAT_MARGIN + Math.random() * (height - CAT_MARGIN * 2)
  if (roll < 0.33) {
    // 左壁へ: マウスを移動領域の外（左）に置く → ネコは左境界で止まる → カキかき
    mousePosX = 0
    mousePosY = midY
  } else if (roll < 0.66) {
    // 右壁へ: マウスを移動領域の外（右）に置く → ネコは右境界で止まる → カキかき
    mousePosX = width
    mousePosY = midY
  } else {
    // 内部ランダム（移動領域内）
    mousePosX = CAT_MARGIN + Math.random() * (width  - CAT_MARGIN * 2)
    mousePosY = CAT_MARGIN + Math.random() * (height - CAT_MARGIN * 2)
  }
}

const idle = (width: number, height: number) => {
  idleTime += 1

  if (idleAnimation === null) {
    if (idleTime > SLEEP_AFTER) {
      idleAnimation = 'sleeping'
    } else if (idleTime > 5 && nekoPosX <= catMinX(width) + 2 && mousePosX < catMinX(width)) {
      idleAnimation = 'scratchWallW'
    } else if (idleTime > 5 && nekoPosX >= catMaxX(width) - 2 && mousePosX > catMaxX(width)) {
      idleAnimation = 'scratchWallE'
    } else if (idleTime > 5 && nekoPosY <= catMinY(height) + 2 && mousePosY < catMinY(height)) {
      idleAnimation = 'scratchWallN'
    } else if (idleTime > 5 && nekoPosY >= catMaxY(height) - 2 && mousePosY > catMaxY(height)) {
      idleAnimation = 'scratchWallS'
    } else if (idleTime > 10 && Math.floor(Math.random() * 200) === 0) {
      idleAnimation = 'scratchSelf'
    }
  }

  switch (idleAnimation) {
    case 'sleeping':
      if (idleAnimationFrame < 8) { setSprite('tired', 0); break }
      isSleeping.value = true
      sleepFrames += 1
      setSprite('sleeping', Math.floor(idleAnimationFrame / 4))
      if (idleAnimationFrame > 192) idleAnimationFrame = 8
      if (sleepFrames >= SLEEP_AFTER) { wakeUpAndRun(width, height); return }
      break
    case 'scratchWallN':
    case 'scratchWallS':
    case 'scratchWallE':
    case 'scratchWallW':
    case 'scratchSelf':
      setSprite(idleAnimation, idleAnimationFrame)
      if (idleAnimationFrame > 9) {
        resetIdleAnimation()
        idleTime = 0
        // スクラッチ完了後は無条件でマウスをネコ中心へ固定
        // noMouseFrames を閾値以上にすることで frame() が毎フレーム上書きし続ける
        mousePosX = nekoPosX
        mousePosY = nekoPosY
        noMouseFrames = NO_MOUSE_IDLE
      }
      break
    default:
      setSprite('idle', 0)
      return
  }
  idleAnimationFrame += 1
}

const frame = () => {
  const stageRect = stageRef.value?.getBoundingClientRect()
  if (!stageRect) return
  const width  = Math.max(64, stageRect.width)
  const height = Math.max(64, stageRect.height)

  // マウス未操作が15秒続いたらネコ頭上をマウス位置とみなす
  noMouseFrames += 1
  if (noMouseFrames >= NO_MOUSE_IDLE) {
    mousePosX = nekoPosX
    mousePosY = nekoPosY
  }

  frameCount += 1
  const diffX    = nekoPosX - mousePosX
  const diffY    = nekoPosY - mousePosY
  const distance = Math.sqrt(diffX ** 2 + diffY ** 2)

  // 境界で止まっている判定: ネコが領域端にいてマウスがその外にある
  const stuckLeft  = nekoPosX <= catMinX(width)  + 2 && mousePosX < catMinX(width)
  const stuckRight = nekoPosX >= catMaxX(width)  - 2 && mousePosX > catMaxX(width)
  const stuckTop   = nekoPosY <= catMinY(height) + 2 && mousePosY < catMinY(height)
  const stuckBot   = nekoPosY >= catMaxY(height) - 2 && mousePosY > catMaxY(height)
  const stuckAtWall = stuckLeft || stuckRight || stuckTop || stuckBot

  if (distance < nekoSpeed || distance < 48 || stuckAtWall) {
    idle(width, height)
    return
  }

  resetIdleAnimation()
  idleTime = 0

  let direction = ''
  direction += diffY / distance >  0.5 ? 'N' : ''
  direction += diffY / distance < -0.5 ? 'S' : ''
  direction += diffX / distance >  0.5 ? 'W' : ''
  direction += diffX / distance < -0.5 ? 'E' : ''
  setSprite((direction || 'idle') as SpriteName, frameCount)

  nekoPosX -= (diffX / distance) * nekoSpeed
  nekoPosY -= (diffY / distance) * nekoSpeed
  nekoPosX = clamp(nekoPosX, catMinX(width),  catMaxX(width))
  nekoPosY = clamp(nekoPosY, catMinY(height), catMaxY(height))
  applyPosition()
}

const onAnimationFrame = (timestamp: number) => {
  if (!stageRef.value || !nekoRef.value) return
  if (!lastFrameTimestamp) lastFrameTimestamp = timestamp
  if (timestamp - lastFrameTimestamp > 100) {
    lastFrameTimestamp = timestamp
    frame()
  }
  animationId = window.requestAnimationFrame(onAnimationFrame)
}

const handlePointerMove = (event: PointerEvent) => {
  const stageRect = stageRef.value?.getBoundingClientRect()
  if (!stageRect) return
  // マウスはステージ全体を追跡（移動領域外も OK）
  mousePosX = event.clientX - stageRect.left
  mousePosY = event.clientY - stageRect.top
  noMouseFrames = 0
}

const handleResize = () => {
  const stageRect = stageRef.value?.getBoundingClientRect()
  if (!stageRect) return
  const w = Math.max(64, stageRect.width)
  const h = Math.max(64, stageRect.height)
  nekoPosX = clamp(nekoPosX, catMinX(w), catMaxX(w))
  nekoPosY = clamp(nekoPosY, catMinY(h), catMaxY(h))
  mousePosX = clamp(mousePosX, 0, w)
  mousePosY = clamp(mousePosY, 0, h)
  applyPosition()
}

const resetToStage = () => {
  const stageRect = stageRef.value?.getBoundingClientRect()
  const width  = Math.max(64, stageRect?.width  ?? 640)
  const height = Math.max(64, stageRect?.height ?? 360)
  nekoPosX  = clamp(width  * 0.35, catMinX(width),  catMaxX(width))
  nekoPosY  = clamp(height * 0.55, catMinY(height), catMaxY(height))
  mousePosX = clamp(width  * 0.60, catMinX(width),  catMaxX(width))
  mousePosY = clamp(height * 0.40, catMinY(height), catMaxY(height))
  frameCount = 0
  idleTime   = 0
  resetIdleAnimation()
  applyPosition()
  setSprite('idle', 0)
}

onMounted(() => {
  resetToStage()
  const stageEl = stageRef.value
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  if (!stageEl || reducedMotion) return
  stageEl.addEventListener('pointermove', handlePointerMove)
  stageEl.addEventListener('pointerdown', handlePointerMove)
  window.addEventListener('resize', handleResize)
  animationId = window.requestAnimationFrame(onAnimationFrame)
})

onBeforeUnmount(() => {
  const stageEl = stageRef.value
  if (stageEl) {
    stageEl.removeEventListener('pointermove', handlePointerMove)
    stageEl.removeEventListener('pointerdown', handlePointerMove)
  }
  window.removeEventListener('resize', handleResize)
  if (animationId) window.cancelAnimationFrame(animationId)
})
</script>

<template>
  <div ref="stageRef" class="neko-stage">
    <div
      v-if="props.showBoundary"
      class="neko-boundary"
      :style="{
        left:   `${CAT_MARGIN}px`,
        top:    `${CAT_MARGIN}px`,
        right:  `${CAT_MARGIN}px`,
        bottom: `${CAT_MARGIN_BOTTOM}px`,
      }"
    ></div>
    <div ref="nekoRef" class="neko-sprite" aria-hidden="true"></div>
  </div>
</template>

<style scoped>
.neko-stage {
  position: absolute;
  inset: 0;
  z-index: 2;
  overflow: hidden;
  cursor: crosshair;
  background: transparent;
}

.neko-boundary {
  position: absolute;
  border: 1px dashed rgba(180, 200, 255, 0.35);
  border-radius: 4px;
  pointer-events: none;
  z-index: 0;
}

.neko-sprite {
  position: absolute;
  left: 16px;
  top: 16px;
  width: 32px;
  height: 32px;
  background-image: url('/oneko.gif');
  background-repeat: no-repeat;
  background-size: 256px 128px;
  image-rendering: pixelated;
  pointer-events: none;
  z-index: 1;
  transform: scale(2);
  transform-origin: center;
}
</style>
