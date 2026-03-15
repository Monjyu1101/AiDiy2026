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
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as THREE from 'three'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'
import { VRMLoaderPlugin, VRMUtils } from '@pixiv/three-vrm'
import { VRMAnimationLoaderPlugin, createVRMAnimationClip } from '@pixiv/three-vrm-animation'
import { DEFAULT_VRM_MODEL_URL, DEFAULT_VRMA_FILES } from '@/api/config'
import {
  自立身体制御初期化,
  自立身体制御リセット,
  自立身体制御適用,
  type 自立身体制御設定,
} from '@/components/AIコア_自立身体制御'
import {
  カメラ距離倍率適用,
  自動カメラワーク初期化,
  自動カメラワーク適用,
  手動カメラ周回適用,
  type 自動カメラワーク設定,
} from '@/components/AIコア_自動カメラワーク'

const props = withDefaults(defineProps<{
  sessionId: string;
  userName: string;
  liveModel: string;
  inputConnected: boolean;
  audioConnected: boolean;
  micEnabled: boolean;
  speakerEnabled: boolean;
  micLevel: number;
  speakerLevel: number;
  uiVisible: boolean;
  transparentMode?: boolean;
  subtitleText?: string;
  bodyAutonomousEnabled?: boolean;
  cameraAutoEnabled?: boolean;
}>(), {
  transparentMode: false,
  subtitleText: '',
  bodyAutonomousEnabled: false,
  cameraAutoEnabled: true,
})

const mountRef = ref<HTMLDivElement | null>(null)
const loadError = ref('')
const currentMotion = ref('待機')
const loading = ref(true)
const dragging = ref(false)


let renderer: THREE.WebGLRenderer | null = null
let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let clock: THREE.Clock | null = null
let frameHandle = 0
let currentVrm: any = null
let motionLoader: GLTFLoader | null = null
let modelLoader: GLTFLoader | null = null
let mixer: THREE.AnimationMixer | null = null
let currentAction: THREE.AnimationAction | null = null
let modelSize: THREE.Vector3 | null = null
let destroyed = false
let currentMotionIndex = -1
let lipCurrent = 0
const _lookAtPos = new THREE.Vector3()
let manualCameraAngle = 0
let manualCameraHeight = 0
let dragPointerId: number | null = null
let dragStartX = 0
let dragStartY = 0
let dragStartCameraAngle = 0
let dragStartCameraHeight = 0
let cameraBaseY = 0
let cameraBaseZ = -1.1
let cameraDistanceScale = 1
let autoBodySettings: 自立身体制御設定 | null = null
let autoCameraSettings: 自動カメラワーク設定 | null = null

const モーション補間秒数 = 0.3
const 視線補間速度 = 10
const カメラ目線オフセット = 0.18
const 視線補助最大ヨー角 = 48
const 視線補助最大ピッチ角 = 26

type 視線補助骨設定 = {
  node: THREE.Object3D
  初期姿勢: THREE.Quaternion
  ヨー倍率: number
  ピッチ倍率: number
}

type 視線補助設定 = {
  首: 視線補助骨設定 | null
  頭: 視線補助骨設定 | null
}

const _cameraPos = new THREE.Vector3()
const _cameraForward = new THREE.Vector3()
const _gazeEuler = new THREE.Euler(0, 0, 0, 'YXZ')
const _gazeQuat = new THREE.Quaternion()
const _baseQuat = new THREE.Quaternion()
let lookAtTarget: THREE.Object3D | null = null
let gazeAssistSettings: 視線補助設定 | null = null

function 視線補助骨作成(
  node: THREE.Object3D | null | undefined,
  ヨー倍率: number,
  ピッチ倍率: number,
): 視線補助骨設定 | null {
  if (!node) return null
  return {
    node,
    初期姿勢: node.quaternion.clone(),
    ヨー倍率,
    ピッチ倍率,
  }
}

function 視線補助初期化(vrm: any): 視線補助設定 | null {
  const humanoid = vrm?.humanoid
  if (!humanoid) return null

  const 首 = 視線補助骨作成(humanoid.getNormalizedBoneNode?.('neck') ?? null, 0.48, 0.3)
  const 頭 = 視線補助骨作成(humanoid.getNormalizedBoneNode?.('head') ?? null, 0.68, 0.4)
  if (!首 && !頭) return null

  return { 首, 頭 }
}

function 視線補助骨リセット(骨: 視線補助骨設定 | null) {
  if (!骨) return
  骨.node.quaternion.copy(骨.初期姿勢)
}

function 視線補助リセット(設定: 視線補助設定 | null) {
  if (!設定) return
  視線補助骨リセット(設定.首)
  視線補助骨リセット(設定.頭)
}

function 視線補助骨適用(骨: 視線補助骨設定 | null, yaw: number, pitch: number, blend: number) {
  if (!骨) return

  _gazeEuler.set(
    THREE.MathUtils.degToRad(pitch * 骨.ピッチ倍率),
    THREE.MathUtils.degToRad(yaw * 骨.ヨー倍率),
    0,
    'YXZ',
  )
  _gazeQuat.setFromEuler(_gazeEuler)
  骨.node.quaternion.slerp(_baseQuat.copy(骨.初期姿勢).multiply(_gazeQuat), blend)
}

function 目線ターゲット更新() {
  if (!camera || !lookAtTarget) return

  camera.getWorldPosition(_cameraPos)
  camera.getWorldDirection(_cameraForward)
  lookAtTarget.position.copy(_cameraPos).addScaledVector(_cameraForward, -カメラ目線オフセット)
  lookAtTarget.updateMatrixWorld()
  _lookAtPos.copy(lookAtTarget.position)
}

function 視線補助適用(delta: number) {
  if (!gazeAssistSettings || !currentVrm?.lookAt) return

  const yaw = THREE.MathUtils.clamp(currentVrm.lookAt.yaw ?? 0, -視線補助最大ヨー角, 視線補助最大ヨー角)
  const pitch = THREE.MathUtils.clamp(currentVrm.lookAt.pitch ?? 0, -視線補助最大ピッチ角, 視線補助最大ピッチ角)
  const blend = 1 - Math.exp(-delta * 視線補間速度)

  視線補助骨適用(gazeAssistSettings.首, yaw, pitch, blend)
  視線補助骨適用(gazeAssistSettings.頭, yaw, pitch, blend)
}

function 目線制御状態同期(enabled: boolean) {
  if (!currentVrm?.lookAt) return

  currentVrm.lookAt.autoUpdate = enabled
  currentVrm.lookAt.target = enabled ? lookAtTarget : null

  if (!enabled) {
    currentVrm.lookAt.reset()
    視線補助リセット(gazeAssistSettings)
  }
}

function 現在カメラ状態取得(設定: 自動カメラワーク設定, autoEnabled: boolean, elapsed: number) {
  const angle = 設定.初期角度 + manualCameraAngle + (autoEnabled ? elapsed * 設定.角速度 : 0)
  const displayedHeightOffset = manualCameraHeight + (autoEnabled ? Math.sin(angle * 0.5) * 設定.高さ振幅 : 0)
  return { angle, displayedHeightOffset }
}

function カメラ状態復元(
  設定: 自動カメラワーク設定,
  angle: number,
  displayedHeightOffset: number,
  autoEnabled: boolean,
  elapsed: number,
) {
  設定.初期角度 = angle - manualCameraAngle - (autoEnabled ? elapsed * 設定.角速度 : 0)
  manualCameraHeight = displayedHeightOffset - (autoEnabled ? Math.sin(angle * 0.5) * 設定.高さ振幅 : 0)
}

function カメラ位置反映(autoEnabled: boolean, elapsed = clock?.elapsedTime ?? 0) {
  if (!camera || !autoCameraSettings) return
  if (autoEnabled) {
    自動カメラワーク適用(camera, elapsed, autoCameraSettings, manualCameraAngle, manualCameraHeight)
  } else {
    手動カメラ周回適用(camera, autoCameraSettings, manualCameraAngle, manualCameraHeight)
  }
}

function fitCamera() {
  if (!camera || !modelSize) return

  const elapsed = clock?.elapsedTime ?? 0
  const previousSettings = autoCameraSettings
  const previousState = previousSettings
    ? 現在カメラ状態取得(previousSettings, props.cameraAutoEnabled, elapsed)
    : null

  const padding = 1.06
  const halfHeight = Math.max(0.1, modelSize.y * 0.5)
  const halfWidth = Math.max(0.1, modelSize.x * 0.5)
  const verticalFov = THREE.MathUtils.degToRad(camera.fov)
  const horizontalFov = 2 * Math.atan(Math.tan(verticalFov / 2) * camera.aspect)
  const distanceForHeight = halfHeight / Math.tan(verticalFov / 2)
  const distanceForWidth = halfWidth / Math.tan(horizontalFov / 2)
  const distance = Math.max(distanceForHeight, distanceForWidth) * padding * 0.54

  cameraBaseY = modelSize.y * 0.74
  cameraBaseZ = -Math.max(1.1, distance)
  autoBodySettings = currentVrm ? 自立身体制御初期化(currentVrm, modelSize) : null
  autoCameraSettings = 自動カメラワーク初期化(cameraBaseY, cameraBaseZ, modelSize)
  カメラ距離倍率適用(autoCameraSettings, cameraDistanceScale)
  if (previousState) {
    カメラ状態復元(autoCameraSettings, previousState.angle, previousState.displayedHeightOffset, props.cameraAutoEnabled, elapsed)
  }
  カメラ位置反映(props.cameraAutoEnabled, elapsed)
}

function resizeStage() {
  if (!renderer || !camera || !mountRef.value) return

  const width = mountRef.value.clientWidth || 1
  const height = mountRef.value.clientHeight || 1
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setSize(width, height)
  camera.aspect = width / height
  fitCamera()
}

function モーション終了時処理(event: THREE.Event & { action?: THREE.AnimationAction }) {
  if (!event.action || event.action !== currentAction) return
  playRandomMotion()
}

function playRandomMotion() {
  if (!motionLoader || !currentVrm || destroyed) return
  if (!mixer) {
    mixer = new THREE.AnimationMixer(currentVrm.scene)
    mixer.addEventListener('finished', モーション終了時処理)
  }

  let nextIndex = 0
  if (DEFAULT_VRMA_FILES.length > 1) {
    do {
      nextIndex = Math.floor(Math.random() * DEFAULT_VRMA_FILES.length)
    } while (nextIndex === currentMotionIndex)
  }
  currentMotionIndex = nextIndex
  const nextMotion = DEFAULT_VRMA_FILES[nextIndex] || DEFAULT_VRMA_FILES[0] || ''
  if (!nextMotion) return
  currentMotion.value = nextMotion.split('/').pop() || 'motion'

  motionLoader.load(
    nextMotion,
    (gltf: any) => {
      if (destroyed || !currentVrm || !mixer) return

      const vrmAnimation = gltf.userData?.vrmAnimations?.[0]
      if (!vrmAnimation) return

      const clip = createVRMAnimationClip(vrmAnimation, currentVrm)
      const action = mixer.clipAction(clip)
      const previousAction = currentAction

      action.reset()
      action.setLoop(THREE.LoopOnce, 1)
      action.clampWhenFinished = true
      action.enabled = true
      action.setEffectiveTimeScale(1)
      action.setEffectiveWeight(1)
      action.play()

      if (previousAction && previousAction !== action) {
        action.crossFadeFrom(previousAction, モーション補間秒数, false)
      }

      currentAction = action
    },
    undefined,
    () => {
      currentMotion.value = 'motion error'
    },
  )
}

function initScene() {
  if (!mountRef.value) return

  loading.value = true
  loadError.value = ''

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  renderer.outputColorSpace = THREE.SRGBColorSpace
  renderer.setClearColor(0x000000, 0)
  mountRef.value.appendChild(renderer.domElement)

  scene = new THREE.Scene()
  lookAtTarget = new THREE.Object3D()
  lookAtTarget.visible = false
  scene.add(lookAtTarget)
  camera = new THREE.PerspectiveCamera(28, 1, 0.01, 40)
  clock = new THREE.Clock()

  const ambient = new THREE.AmbientLight(0xffffff, 1.25)
  const keyLight = new THREE.DirectionalLight(0xfff5e6, Math.PI * 0.74)
  keyLight.position.set(1.2, 1.5, 1.1)
  const rimLight = new THREE.DirectionalLight(0xdde8ff, 1.05)
  rimLight.position.set(-1.3, 0.7, 1.3)

  const container = new THREE.Group()
  container.rotation.y = Math.PI

  scene.add(ambient, keyLight, rimLight, container)

  modelLoader = new GLTFLoader()
  modelLoader.register((parser: any) => new VRMLoaderPlugin(parser))

  motionLoader = new GLTFLoader()
  motionLoader.register((parser: any) => new VRMAnimationLoaderPlugin(parser))

  modelLoader.load(
    DEFAULT_VRM_MODEL_URL,
    (gltf: any) => {
      if (destroyed || !scene) return

      const vrm = gltf.userData?.vrm
      if (!vrm) {
        loadError.value = 'VRM を読み込めませんでした。'
        loading.value = false
        return
      }

      VRMUtils.removeUnnecessaryVertices(gltf.scene)
      VRMUtils.removeUnnecessaryJoints(gltf.scene)
      vrm.scene.traverse((object: THREE.Object3D) => {
        object.frustumCulled = false
      })

      const box = new THREE.Box3().setFromObject(vrm.scene)
      const center = box.getCenter(new THREE.Vector3())
      const size = box.getSize(new THREE.Vector3())

      vrm.scene.position.x -= center.x
      vrm.scene.position.y -= box.min.y
      vrm.scene.position.z -= center.z

      modelSize = size.clone()
      currentVrm = vrm
      gazeAssistSettings = 視線補助初期化(vrm)
      目線制御状態同期(props.bodyAutonomousEnabled)
      container.add(vrm.scene)
      fitCamera()
      if (props.bodyAutonomousEnabled) {
        autoBodySettings = currentVrm ? 自立身体制御初期化(currentVrm, modelSize) : autoBodySettings
        currentMotion.value = '自立'
      } else {
        playRandomMotion()
      }
      loading.value = false
    },
    undefined,
    (error: unknown) => {
      loadError.value = error instanceof Error ? error.message : 'VRM の読み込みに失敗しました。'
      loading.value = false
    },
  )

  const animate = () => {
    if (!renderer || !scene || !camera || !clock || destroyed) return

    const delta = clock.getDelta()
    const elapsed = clock.elapsedTime

    if (!props.bodyAutonomousEnabled) {
      mixer?.update(delta)
    }

    if (currentVrm) {
      const blink = Math.sin(elapsed * 2.4) > 0.985 ? 1 : 0
      const bodyState = props.bodyAutonomousEnabled && autoBodySettings
        ? 自立身体制御適用(elapsed, autoBodySettings)
        : { rotationY: 0, positionY: 0 }

      currentVrm.expressionManager?.setValue('blink', blink)
      currentVrm.expressionManager?.setValue('aa', Math.min(1, props.speakerLevel))
      currentVrm.scene.rotation.y = bodyState.rotationY
      currentVrm.scene.position.y = bodyState.positionY
      カメラ位置反映(props.cameraAutoEnabled, elapsed)
      if (props.bodyAutonomousEnabled && currentVrm.lookAt) {
        目線ターゲット更新()
        currentVrm.lookAt.lookAt(_lookAtPos)
        視線補助適用(delta)
      }
      currentVrm.update(delta)
    }

    renderer.render(scene, camera)
    frameHandle = window.requestAnimationFrame(animate)
  }

  resizeStage()
  window.addEventListener('resize', resizeStage)
  animate()
}

function handlePointerDown(event: PointerEvent) {
  if (!mountRef.value) return
  dragging.value = true
  dragPointerId = event.pointerId
  dragStartX = event.clientX
  dragStartY = event.clientY
  dragStartCameraAngle = manualCameraAngle
  dragStartCameraHeight = manualCameraHeight
  mountRef.value.setPointerCapture(event.pointerId)
}

function handlePointerMove(event: PointerEvent) {
  if (!dragging.value || dragPointerId !== event.pointerId) return
  const deltaX = event.clientX - dragStartX
  const deltaY = event.clientY - dragStartY
  manualCameraAngle = dragStartCameraAngle + deltaX * 0.0085
  manualCameraHeight = THREE.MathUtils.clamp(dragStartCameraHeight + deltaY * 0.006, -1.2, 1.2)
}

function stopPointerDrag(event?: PointerEvent) {
  if (mountRef.value && dragPointerId !== null && event?.pointerId === dragPointerId) {
    mountRef.value.releasePointerCapture(dragPointerId)
  }
  dragging.value = false
  dragPointerId = null
}

function handleWheel(event: WheelEvent) {
  if (!event.ctrlKey || !camera || !autoCameraSettings) return
  event.preventDefault()

  const nextScale = THREE.MathUtils.clamp(
    cameraDistanceScale * (event.deltaY > 0 ? 1.08 : 0.92),
    0.08,
    3.2,
  )
  cameraDistanceScale = nextScale
  カメラ距離倍率適用(autoCameraSettings, cameraDistanceScale)

  カメラ位置反映(props.cameraAutoEnabled)
}

watch(() => props.bodyAutonomousEnabled, (enabled) => {
  if (!currentVrm) return

  目線制御状態同期(enabled)

  if (enabled) {
    if (mixer) {
      mixer.timeScale = 0
    }
    autoBodySettings = modelSize ? 自立身体制御初期化(currentVrm, modelSize) : autoBodySettings
    currentMotion.value = '自立'
    return
  }

  if (mixer) {
    mixer.timeScale = 1
  }
  if (autoBodySettings) {
    自立身体制御リセット(autoBodySettings)
  }
  if (!currentAction) {
    playRandomMotion()
  }
}, { immediate: false })

watch(() => props.cameraAutoEnabled, (enabled, previousEnabled) => {
  if (!autoCameraSettings) return
  const oldEnabled = previousEnabled ?? enabled
  const elapsed = clock?.elapsedTime ?? 0
  const previousState = 現在カメラ状態取得(autoCameraSettings, oldEnabled, elapsed)
  カメラ状態復元(autoCameraSettings, previousState.angle, previousState.displayedHeightOffset, enabled, elapsed)
  カメラ位置反映(enabled, elapsed)
})

onMounted(() => {
  initScene()
})

onBeforeUnmount(() => {
  destroyed = true
  window.cancelAnimationFrame(frameHandle)
  window.removeEventListener('resize', resizeStage)
  mixer?.removeEventListener('finished', モーション終了時処理)
  mixer?.stopAllAction()
  currentAction = null
  視線補助リセット(gazeAssistSettings)
  renderer?.dispose()
  if (currentVrm?.lookAt) {
    currentVrm.lookAt.target = null
  }
  currentVrm = null
  if (renderer?.domElement.parentElement) {
    renderer.domElement.parentElement.removeChild(renderer.domElement)
  }
  renderer = null
  scene = null
  camera = null
  clock = null
  autoBodySettings = null
  autoCameraSettings = null
  gazeAssistSettings = null
  lookAtTarget = null
})
</script>

<template>
  <section class="avatar-stage-shell" :class="{ transparent: transparentMode }">
    <div
      ref="mountRef"
      class="canvas-host"
      data-interactive="true"
      @pointerdown="handlePointerDown"
      @pointermove="handlePointerMove"
      @pointerup="stopPointerDrag"
      @pointercancel="stopPointerDrag"
      @pointerleave="stopPointerDrag"
      @wheel="handleWheel"
    ></div>
    <div class="glow glow-a" :style="{ opacity: micLevel * 0.7 }"></div>
    <div class="glow glow-b" :style="{ opacity: speakerLevel * 0.7 }"></div>

    <div v-if="subtitleText" class="avatar-subtitle">
      {{ subtitleText }}
    </div>

    <div v-if="!transparentMode && loading" class="stage-loading">
      <img src="/icons/loading.gif" alt="loading" />
    </div>

    <div v-else-if="!transparentMode && loadError" class="stage-status error">
      <img src="/icons/abort.png" alt="error" />
      <span>{{ loadError }}</span>
    </div>

  </section>
</template>

<style scoped>
.avatar-stage-shell {
  position: absolute;
  inset: 0;
  overflow: hidden;
  background:
    radial-gradient(circle at 50% 18%, rgba(255, 198, 86, 0.14), transparent 28%),
    radial-gradient(circle at 78% 78%, rgba(107, 149, 255, 0.12), transparent 24%),
    linear-gradient(180deg, rgba(7, 9, 15, 0.18), rgba(7, 9, 15, 0.04));
}

.avatar-stage-shell.transparent {
  background: transparent;
}

.canvas-host {
  position: absolute;
  inset: 0;
  cursor: grab;
  touch-action: none;
  z-index: 1;
}

.canvas-host:active {
  cursor: grabbing;
}

.glow {
  position: absolute;
  border-radius: 999px;
  filter: blur(54px);
  pointer-events: none;
  z-index: 0;
}

.glow-a {
  width: 220px;
  height: 220px;
  top: 10%;
  left: 6%;
  background: rgba(220, 50, 50, 0.75);
}

.glow-b {
  width: 240px;
  height: 240px;
  top: 10%;
  right: 6%;
  background: rgba(0, 210, 220, 0.75);
}

.avatar-subtitle {
  position: absolute;
  left: 50%;
  bottom: 62px;
  transform: translateX(-50%);
  width: min(520px, calc(100% - 32px));
  padding: 10px 14px;
  border: 1px solid rgba(153, 141, 214, 0.34);
  background: rgba(3, 5, 10, 0.52);
  color: #00ff00;
  text-align: center;
  font-size: 1.425rem;
  line-height: 1.5;
  backdrop-filter: blur(12px);
  pointer-events: none;
  z-index: 6;
  white-space: pre-wrap;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.45);
}

.stage-loading {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.stage-loading img {
  width: 96px;
  height: 96px;
  object-fit: contain;
  opacity: 0.92;
}

.stage-status {
  position: absolute;
  left: 18px;
  bottom: 18px;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid rgba(153, 141, 214, 0.38);
  background: rgba(3, 5, 10, 0.42);
  color: #f4f4ff;
  backdrop-filter: blur(12px);
  font-size: 0.8rem;
}

.stage-status img {
  width: 18px;
  height: 18px;
}

.stage-status.error {
  color: #ffd3d3;
  border-color: rgba(255, 131, 131, 0.26);
}

@media (max-width: 720px) {
  .avatar-subtitle {
    bottom: 56px;
    width: calc(100% - 24px);
    font-size: 1.32rem;
  }

  .stage-status {
    left: 12px;
    right: 12px;
    bottom: 12px;
  }
}
</style>
