<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as THREE from 'three'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'
import { VRMLoaderPlugin, VRMUtils } from '@pixiv/three-vrm'
import { VRMAnimationLoaderPlugin, createVRMAnimationClip } from '@pixiv/three-vrm-animation'
import { DEFAULT_VRM_MODEL_URL, DEFAULT_VRMA_FILES } from '@/lib/config'

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
}>(), {
  transparentMode: false,
  subtitleText: '',
})

const mountRef = ref<HTMLDivElement | null>(null)
const loadError = ref('')
const currentMotion = ref('待機')
const loading = ref(true)
const dragging = ref(false)

const stageTone = computed(() => Math.max(props.micLevel, props.speakerLevel))

let renderer: THREE.WebGLRenderer | null = null
let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let clock: THREE.Clock | null = null
let frameHandle = 0
let currentVrm: any = null
let motionLoader: GLTFLoader | null = null
let modelLoader: GLTFLoader | null = null
let mixer: THREE.AnimationMixer | null = null
let modelSize: THREE.Vector3 | null = null
let destroyed = false
let currentMotionIndex = -1
let lipCurrent = 0
let manualRotationY = 0
let dragPointerId: number | null = null
let dragStartX = 0
let dragStartRotationY = 0

function fitCamera() {
  if (!camera || !modelSize) return

  const padding = 1.06
  const halfHeight = Math.max(0.1, modelSize.y * 0.5)
  const halfWidth = Math.max(0.1, modelSize.x * 0.5)
  const verticalFov = THREE.MathUtils.degToRad(camera.fov)
  const horizontalFov = 2 * Math.atan(Math.tan(verticalFov / 2) * camera.aspect)
  const distanceForHeight = halfHeight / Math.tan(verticalFov / 2)
  const distanceForWidth = halfWidth / Math.tan(horizontalFov / 2)
  const distance = Math.max(distanceForHeight, distanceForWidth) * padding * 0.54

  camera.position.set(0, modelSize.y * 0.74, -Math.max(1.1, distance))
  camera.lookAt(0, modelSize.y * 0.74, 0)
  camera.updateProjectionMatrix()
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

function playRandomMotion() {
  if (!motionLoader || !currentVrm || destroyed) return

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
      if (destroyed || !currentVrm) return

      const vrmAnimation = gltf.userData?.vrmAnimations?.[0]
      if (!vrmAnimation) return

      if (mixer) {
        mixer.stopAllAction()
        mixer.removeEventListener('finished', playRandomMotion)
      }

      mixer = new THREE.AnimationMixer(currentVrm.scene)
      const clip = createVRMAnimationClip(vrmAnimation, currentVrm)
      const action = mixer.clipAction(clip)
      action.setLoop(THREE.LoopOnce, 1)
      action.clampWhenFinished = true
      action.play()
      mixer.addEventListener('finished', playRandomMotion)
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
  camera = new THREE.PerspectiveCamera(28, 1, 0.1, 40)
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
      container.add(vrm.scene)
      fitCamera()
      playRandomMotion()
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

    if (currentVrm) {
      const blink = Math.sin(elapsed * 2.4) > 0.985 ? 1 : 0
      const lipTarget = Math.min(1, props.speakerLevel * 1.6 + props.micLevel * 1.1)
      lipCurrent += (lipTarget - lipCurrent) * 0.28

      currentVrm.expressionManager?.setValue('blink', blink)
      currentVrm.expressionManager?.setValue('aa', Math.min(1, lipCurrent * 2.3))
      currentVrm.scene.rotation.y = manualRotationY + Math.sin(elapsed * 0.28) * 0.08
      currentVrm.scene.position.y = Math.sin(elapsed * 0.9) * 0.01
      currentVrm.update(delta)
    }

    mixer?.update(delta)
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
  dragStartRotationY = manualRotationY
  mountRef.value.setPointerCapture(event.pointerId)
}

function handlePointerMove(event: PointerEvent) {
  if (!dragging.value || dragPointerId !== event.pointerId) return
  const deltaX = event.clientX - dragStartX
  manualRotationY = THREE.MathUtils.clamp(dragStartRotationY + deltaX * 0.0085, -1.2, 1.2)
}

function stopPointerDrag(event?: PointerEvent) {
  if (mountRef.value && dragPointerId !== null && event?.pointerId === dragPointerId) {
    mountRef.value.releasePointerCapture(dragPointerId)
  }
  dragging.value = false
  dragPointerId = null
}

watch(stageTone, (value) => {
  if (!currentVrm?.expressionManager) return
  currentVrm.expressionManager.setValue('aa', Math.min(1, value * 1.5))
})

onMounted(() => {
  initScene()
})

onBeforeUnmount(() => {
  destroyed = true
  window.cancelAnimationFrame(frameHandle)
  window.removeEventListener('resize', resizeStage)
  mixer?.removeEventListener('finished', playRandomMotion)
  mixer?.stopAllAction()
  renderer?.dispose()
  currentVrm = null
  if (renderer?.domElement.parentElement) {
    renderer.domElement.parentElement.removeChild(renderer.domElement)
  }
  renderer = null
  scene = null
  camera = null
  clock = null
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
    ></div>
    <div v-show="!transparentMode" class="glow glow-a" :style="{ opacity: 0.24 + stageTone * 0.45 }"></div>
    <div v-show="!transparentMode" class="glow glow-b" :style="{ opacity: 0.14 + stageTone * 0.34 }"></div>

    <div v-if="subtitleText" class="avatar-subtitle">
      {{ subtitleText }}
    </div>

    <div v-if="!transparentMode && loading" class="stage-status">
      <img src="/icons/loading.gif" alt="loading" />
      <span>VRM を読み込んでいます...</span>
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
}

.canvas-host:active {
  cursor: grabbing;
}

.glow {
  position: absolute;
  border-radius: 999px;
  filter: blur(54px);
  pointer-events: none;
}

.glow-a {
  width: 220px;
  height: 220px;
  top: 10%;
  left: 6%;
  background: rgba(255, 196, 76, 0.75);
}

.glow-b {
  width: 240px;
  height: 240px;
  right: 6%;
  bottom: 8%;
  background: rgba(97, 154, 255, 0.66);
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
  color: #f4f4ff;
  text-align: center;
  font-size: 1.425rem;
  line-height: 1.5;
  backdrop-filter: blur(12px);
  pointer-events: none;
  z-index: 6;
  white-space: pre-wrap;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.45);
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
