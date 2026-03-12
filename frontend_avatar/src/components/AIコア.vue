<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import アバター from '@/components/アバター.vue'
import WindowShell from '@/components/WindowShell.vue'
import { AudioController } from '@/lib/audio-controller'
import { AI_WS_ENDPOINT } from '@/lib/config'
import { AIWebSocket } from '@/lib/websocket'

type PanelKey = 'chat' | 'file' | 'image' | 'code1' | 'code2' | 'code3' | 'code4'

const props = defineProps<{
  sessionId: string;
  userLabel: string;
  liveModel: string;
  welcomeInfo: string;
  inputConnected: boolean;
  inputSocket: AIWebSocket | null;
  initialMicEnabled: boolean;
  initialSpeakerEnabled: boolean;
  audioStateSeed: number;
  panelVisibility: Record<PanelKey, boolean>;
  coreBusy: boolean;
  coreError: string;
}>()

// --- 字幕キュー（最小5秒・最大30秒表示） ---

const subtitleDisplay = ref('')
const subtitleQueue: string[] = []
let subtitleMinTimer: ReturnType<typeof setTimeout> | null = null
let subtitleMaxTimer: ReturnType<typeof setTimeout> | null = null

function clearSubtitleTimers() {
  if (subtitleMinTimer) { clearTimeout(subtitleMinTimer); subtitleMinTimer = null }
  if (subtitleMaxTimer) { clearTimeout(subtitleMaxTimer); subtitleMaxTimer = null }
}

function advanceSubtitle() {
  clearSubtitleTimers()
  if (subtitleQueue.length > 0) {
    subtitleDisplay.value = subtitleQueue.shift()!
    subtitleMinTimer = setTimeout(() => {
      subtitleMinTimer = null
      if (subtitleQueue.length > 0) {
        advanceSubtitle()
      } else {
        subtitleMaxTimer = setTimeout(() => {
          subtitleDisplay.value = ''
          subtitleMaxTimer = null
        }, 25000)
      }
    }, 5000)
  } else {
    subtitleDisplay.value = ''
  }
}

function addSubtitle(text: string) {
  if (!text.trim()) return
  subtitleQueue.push(text)
  if (!subtitleDisplay.value) {
    advanceSubtitle()
    return
  }
  if (!subtitleMinTimer && subtitleMaxTimer) {
    advanceSubtitle()
  }
}

const emit = defineEmits<{
  togglePanel: [panel: PanelKey];
  reconnect: [];
  logout: [];
}>()

const UI自動非表示秒数 = 15000
const ビジュアライザーバー数 = 32
const uiVisible = ref(true)
const 音声接続済み = ref(false)
const マイク有効 = ref(false)
const スピーカー有効 = ref(true)
const マイクレベル = ref(0)
const スピーカーレベル = ref(0)
const 音声エラー = ref('')
const 入力スペクトラム = ref<number[]>(初期スペクトラム())
const 出力スペクトラム = ref<number[]>(初期スペクトラム())
const audioSocket = shallowRef<AIWebSocket | null>(null)

let uiHideTimer: ReturnType<typeof setTimeout> | null = null
let 音声接続世代 = 0

const 音声処理機 = shallowRef(new AudioController({
  onInputLevel: (value) => {
    マイクレベル.value = value
  },
  onOutputLevel: (value) => {
    スピーカーレベル.value = value
  },
  onInputSpectrum: (values) => {
    入力スペクトラム.value = values
  },
  onOutputSpectrum: (values) => {
    出力スペクトラム.value = values
  },
  getSocket: () => audioSocket.value,
  getSessionId: () => props.sessionId,
}))

const transportState = computed(() => {
  if (props.inputConnected && 音声接続済み.value) return '接続中'
  if (props.coreBusy) return '接続中...'
  if (props.inputConnected || 音声接続済み.value) return '部分接続'
  return '切断'
})

const statusDotClass = computed(() => ({
  on: transportState.value === '接続中',
  partial: transportState.value === '部分接続' || transportState.value === '接続中...',
}))

const visualizerVisible = computed(() => {
  return uiVisible.value && (マイク有効.value || スピーカー有効.value || マイクレベル.value > 0.03 || スピーカーレベル.value > 0.03)
})

const panelToastText = computed(() => {
  if (props.coreError) return props.coreError
  if (音声エラー.value) return 音声エラー.value
  if (props.coreBusy) return 'AIコアへ接続しています...'
  return ''
})

const panelToastIsError = computed(() => Boolean(props.coreError || 音声エラー.value))

function 初期スペクトラム() {
  return Array.from({ length: ビジュアライザーバー数 }, () => 0.05)
}

function ビジュアライザー初期化() {
  入力スペクトラム.value = 初期スペクトラム()
  出力スペクトラム.value = 初期スペクトラム()
}

function clearUiHideTimer() {
  if (!uiHideTimer) return
  clearTimeout(uiHideTimer)
  uiHideTimer = null
}

function scheduleUiHide() {
  clearUiHideTimer()
  uiHideTimer = setTimeout(() => {
    uiVisible.value = false
  }, UI自動非表示秒数)
}

function handleMouseEnter() {
  clearUiHideTimer()
  uiVisible.value = true
}

function handleMouseLeave() {
  scheduleUiHide()
}

function パネル切替要求(panel: PanelKey) {
  emit('togglePanel', panel)
}

function 音声操作状態同期() {
  if (!props.inputSocket?.isConnected()) return

  props.inputSocket.send({
    セッションID: props.sessionId,
    チャンネル: 'input',
    メッセージ識別: 'operations',
    メッセージ内容: {
      ボタン: {
        マイク: マイク有効.value,
        スピーカー: スピーカー有効.value,
      },
    },
  })
}

function 音声切断(incrementGeneration = true) {
  if (incrementGeneration) {
    音声接続世代 += 1
  }

  audioSocket.value?.disconnect()
  audioSocket.value = null
  音声接続済み.value = false
  音声処理機.value.setAudioSocket(null)
  音声処理機.value.cleanup()
  マイクレベル.value = 0
  スピーカーレベル.value = 0
  ビジュアライザー初期化()
}

async function マイク開始反映() {
  const result = await 音声処理機.value.startMicrophone()
  if (!result.success) {
    マイク有効.value = false
    音声エラー.value = result.error || 'マイクを開始できませんでした。'
  }
}

function 音声シード反映() {
  マイク有効.value = props.initialMicEnabled
  スピーカー有効.value = props.initialSpeakerEnabled
  音声処理機.value.setSessionId(props.sessionId)
  音声処理機.value.setLiveModelName(props.liveModel)
  音声処理機.value.setSpeakerEnabled(スピーカー有効.value)
  if (!マイク有効.value) {
    音声処理機.value.stopMicrophone()
  } else if (音声接続済み.value) {
    void マイク開始反映()
  }
}

async function 音声接続開始() {
  if (!props.inputConnected || !props.sessionId) {
    音声切断()
    return
  }

  const currentGeneration = ++音声接続世代
  音声切断(false)
  音声エラー.value = ''

  const nextSocket = new AIWebSocket(AI_WS_ENDPOINT, props.sessionId, 'audio')
  nextSocket.onStateChange((connected) => {
    if (currentGeneration !== 音声接続世代) return
    音声接続済み.value = connected
  })
  nextSocket.on('output_audio', (message) => {
    if (currentGeneration !== 音声接続世代) return
    音声処理機.value.handleAudioMessage(message)
  })
  nextSocket.on('cancel_audio', () => {
    if (currentGeneration !== 音声接続世代) return
    音声処理機.value.cancelOutput({ resetLevel: false })
  })

  try {
    const connectedSessionId = await nextSocket.connect()
    if (currentGeneration !== 音声接続世代) {
      nextSocket.disconnect()
      return
    }

    audioSocket.value = nextSocket
    音声処理機.value.setAudioSocket(nextSocket)
    音声処理機.value.setSessionId(connectedSessionId)
    音声処理機.value.setLiveModelName(props.liveModel)
    音声処理機.value.setSpeakerEnabled(スピーカー有効.value)
    音声エラー.value = ''

    if (マイク有効.value) {
      await マイク開始反映()
    }
  } catch (error) {
    if (currentGeneration !== 音声接続世代) return
    音声エラー.value = error instanceof Error ? error.message : '音声チャンネルへ接続できませんでした。'
    音声切断(false)
  }
}

async function マイク切替() {
  if (!props.inputConnected || !音声接続済み.value) {
    音声エラー.value = '音声チャンネル接続後にマイクを操作してください。'
    return
  }

  音声エラー.value = ''
  await 音声処理機.value.unlockAudio()

  if (!マイク有効.value) {
    マイク有効.value = true
    await マイク開始反映()
    if (!マイク有効.value) {
      return
    }
  } else {
    音声処理機.value.stopMicrophone()
    マイク有効.value = false
  }

  音声操作状態同期()
}

async function スピーカー切替() {
  if (!props.inputConnected || !音声接続済み.value) {
    音声エラー.value = '音声チャンネル接続後にスピーカーを操作してください。'
    return
  }

  音声エラー.value = ''
  await 音声処理機.value.unlockAudio()
  スピーカー有効.value = !スピーカー有効.value
  音声処理機.value.setSpeakerEnabled(スピーカー有効.value)
  音声操作状態同期()
}

watch(() => props.audioStateSeed, () => {
  音声シード反映()
}, { immediate: true })

watch(() => props.liveModel, (model) => {
  音声処理機.value.setLiveModelName(model)
})

watch(
  () => [props.sessionId, props.inputConnected] as const,
  ([sessionId, inputConnected], previous) => {
    const [prevSessionId, prevInputConnected] = previous ?? ['', false]
    if (!inputConnected || !sessionId) {
      音声切断()
      return
    }

    if (!prevInputConnected || sessionId !== prevSessionId || !audioSocket.value?.isConnected()) {
      void 音声接続開始()
    }
  },
  { immediate: true },
)

onMounted(() => {
  scheduleUiHide()
})

onBeforeUnmount(() => {
  clearUiHideTimer()
  clearSubtitleTimers()
  音声切断()
})

defineExpose({ addSubtitle })
</script>

<template>
  <component
    :is="WindowShell"
    title="AiDiy Desktop Avatar"
    theme="purple"
    close-mode="event"
    :chrome-visible="uiVisible"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
    @close="emit('logout')"
  >
    <template v-if="uiVisible" #title-right>
      <span class="core-status-dot" :class="statusDotClass"></span>
      <span class="core-status-text">{{ transportState }}</span>
    </template>

    <div class="core-panel-body">
      <div v-show="visualizerVisible" class="audio-visualizer-overlay">
        <div class="audio-bars">
          <div v-for="(_, index) in 入力スペクトラム" :key="index" class="audio-bar-container">
            <i class="audio-bar output-audio" :style="{ height: `${Math.round((出力スペクトラム[index] || 0.05) * 100)}%` }"></i>
            <i class="audio-bar input-audio" :style="{ height: `${Math.round((入力スペクトラム[index] || 0.05) * 100)}%` }"></i>
          </div>
        </div>
      </div>

      <div v-if="uiVisible && welcomeInfo" class="welcome-info-overlay">
        {{ welcomeInfo }}
      </div>

      <component
        :is="アバター"
        :session-id="sessionId"
        :user-name="userLabel"
        :live-model="liveModel"
        :input-connected="inputConnected"
        :audio-connected="音声接続済み"
        :mic-enabled="マイク有効"
        :speaker-enabled="スピーカー有効"
        :mic-level="マイクレベル"
        :speaker-level="スピーカーレベル"
        :ui-visible="uiVisible"
        :transparent-mode="!uiVisible"
        :subtitle-text="subtitleDisplay"
      />

      <aside v-show="uiVisible" class="panel-icons">
        <button
          class="tool-button microphone-button"
          :class="{ active: マイク有効 }"
          :disabled="!inputConnected || !音声接続済み"
          type="button"
          title="マイク"
          @click="マイク切替"
        >
          <img src="/icons/microphone.png" alt="マイク" />
        </button>
        <button
          class="tool-button speaker-button"
          :class="{ inactive: !スピーカー有効, active: スピーカー有効 }"
          :disabled="!inputConnected || !音声接続済み"
          type="button"
          title="スピーカー"
          @click="スピーカー切替"
        >
          <img src="/icons/speaker.png" alt="スピーカー" />
        </button>
        <button
          class="tool-button file-button"
          :class="{ inactive: !panelVisibility.file, active: panelVisibility.file }"
          type="button"
          title="AIファイル"
          @click="パネル切替要求('file')"
        >
          <img src="/icons/folder_transparent.png" alt="ファイル" />
        </button>
        <button
          class="tool-button chat-button"
          :class="{ inactive: !panelVisibility.chat, active: panelVisibility.chat }"
          type="button"
          title="AIチャット"
          @click="パネル切替要求('chat')"
        >
          0
        </button>
        <button
          class="tool-button agent-button"
          :class="{ inactive: !panelVisibility.code1, active: panelVisibility.code1 }"
          type="button"
          title="AIコード1"
          @click="パネル切替要求('code1')"
        >
          1
        </button>
        <button
          class="tool-button camera-button"
          :class="{ inactive: !panelVisibility.image, active: panelVisibility.image }"
          type="button"
          title="AIイメージ"
          @click="パネル切替要求('image')"
        >
          <img src="/icons/camera.png" alt="イメージ" />
        </button>
        <button
          class="tool-button agent-button"
          :class="{ inactive: !panelVisibility.code2, active: panelVisibility.code2 }"
          type="button"
          title="AIコード2"
          @click="パネル切替要求('code2')"
        >
          2
        </button>
        <button
          class="tool-button agent-button"
          :class="{ inactive: !panelVisibility.code3, active: panelVisibility.code3 }"
          type="button"
          title="AIコード3"
          @click="パネル切替要求('code3')"
        >
          3
        </button>
        <button
          class="tool-button agent-button"
          :class="{ inactive: !panelVisibility.code4, active: panelVisibility.code4 }"
          type="button"
          title="AIコード4"
          @click="パネル切替要求('code4')"
        >
          4
        </button>
        <button class="tool-button sync-button" type="button" title="再接続" @click="emit('reconnect')">S</button>
      </aside>

      <div v-if="uiVisible && panelToastText" class="panel-toast" :class="{ error: panelToastIsError }">
        {{ panelToastText }}
      </div>
    </div>
  </component>
</template>

<style scoped>
.core-panel-body {
  position: relative;
  width: 100%;
  height: 100%;
}

.core-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.45);
  flex-shrink: 0;
}

.core-status-dot.on {
  background: #44ff44;
}

.core-status-dot.partial {
  background: #facc15;
}

.core-status-text {
  font-size: 10px;
  font-weight: bold;
}

.audio-visualizer-overlay {
  position: absolute;
  left: 50%;
  bottom: 18px;
  transform: translateX(-50%);
  width: min(220px, 42vw);
  height: 34px;
  background: rgba(3, 5, 10, 0.26);
  border: 1px solid rgba(153, 141, 214, 0.32);
  border-radius: 0;
  overflow: hidden;
  z-index: 8;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  pointer-events: none;
  padding: 8px;
  backdrop-filter: blur(12px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.audio-bars {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  height: 100%;
  width: 100%;
  gap: 1px;
}

.audio-bar-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  justify-content: flex-end;
  height: 100%;
  gap: 0;
  min-width: 1px;
}

.audio-bar {
  width: 100%;
  min-height: 2px;
  transition: height 0.05s ease-out;
}

.audio-bar.input-audio {
  background: #ff4444;
  order: 2;
}

.audio-bar.output-audio {
  background: #44ff44;
  order: 1;
}

.welcome-info-overlay {
  position: absolute;
  top: 8px;
  left: 10px;
  max-width: min(360px, calc(100% - 84px));
  padding: 4px 6px;
  color: rgba(196, 200, 208, 0.78);
  font-size: 0.78rem;
  line-height: 1.5;
  white-space: pre-wrap;
  pointer-events: none;
  z-index: 8;
}

.panel-icons {
  position: absolute;
  top: 20px;
  right: 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 9;
}

.tool-button {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 2px solid transparent;
  background: rgba(255, 255, 255, 0.95);
  color: #ffffff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(128, 128, 128, 0.3);
}

.tool-button img {
  width: 21px;
  height: 21px;
  display: block;
  object-fit: contain;
  pointer-events: none;
  filter: brightness(0);
}

.tool-button:hover:not(:disabled) {
  transform: scale(1.05);
}

.tool-button.microphone-button {
  border-color: #ff4444;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 2px 8px rgba(255, 68, 68, 0.3);
}

.tool-button.microphone-button:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(255, 68, 68, 0.4);
}

.tool-button.microphone-button.active {
  background: #ff4444;
  border-color: #ff4444;
  animation: pulse 2.5s infinite;
  box-shadow: 0 2px 8px rgba(255, 68, 68, 0.5);
}

.tool-button.microphone-button.active img {
  filter: brightness(0) invert(1);
}

.tool-button.speaker-button.inactive {
  border-color: #00bfff;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 2px 8px rgba(68, 255, 68, 0.3);
}

.tool-button.speaker-button.inactive:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(0, 191, 255, 0.4);
}

.tool-button.speaker-button {
  background: #00bfff;
  border-color: #00bfff;
  box-shadow: 0 2px 8px rgba(68, 255, 68, 0.3);
}

.tool-button.speaker-button:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(0, 191, 255, 0.4);
}

.tool-button.speaker-button.active {
  animation: pulse 2.5s infinite;
}

.tool-button.speaker-button.active img {
  filter: brightness(0) invert(1);
}

.tool-button.chat-button,
.tool-button.agent-button,
.tool-button.camera-button {
  border-radius: 0;
  width: 28px;
  height: 28px;
  margin-left: 2px;
  font-family: Consolas, 'Courier New', monospace;
  font-size: 17px;
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tool-button.file-button {
  border-radius: 2px;
}

.tool-button.file-button.inactive,
.tool-button.chat-button.inactive,
.tool-button.agent-button.inactive,
.tool-button.camera-button.inactive {
  border-color: #2e7d32;
  background: #888888;
  box-shadow: 0 2px 8px rgba(68, 255, 68, 0.3);
  color: #000000;
}

.tool-button.file-button.inactive img,
.tool-button.camera-button.inactive img {
  mix-blend-mode: multiply;
}

.tool-button.file-button.active,
.tool-button.chat-button.active,
.tool-button.agent-button.active,
.tool-button.camera-button.active {
  background: #000000;
  border-color: #44ff44;
  animation: pulse 2.5s infinite;
  box-shadow: 0 2px 8px rgba(68, 255, 68, 0.5);
}

.tool-button.file-button.active img,
.tool-button.camera-button.active img {
  filter: brightness(0) invert(1);
}

.tool-button.chat-button.active,
.tool-button.agent-button.active {
  color: #00ff00;
}

.tool-button.chat-button.inactive,
.tool-button.agent-button.inactive {
  color: #000000;
}

.tool-button.file-button:hover:not(:disabled),
.tool-button.chat-button:hover:not(:disabled),
.tool-button.agent-button:hover:not(:disabled),
.tool-button.camera-button:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(68, 255, 68, 0.4);
}

.tool-button.sync-button {
  background: #ffffff;
  border: 2px solid #ffffff;
  color: #000000;
  box-shadow: 0 2px 8px rgba(255, 255, 255, 0.3);
  font-family: Consolas, 'Courier New', monospace;
  font-size: 15px;
  font-weight: 700;
}

.tool-button.sync-button:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(255, 255, 255, 0.5);
}

.tool-button:disabled {
  background: #808080 !important;
  border-color: #808080 !important;
  cursor: not-allowed !important;
  box-shadow: 0 2px 8px rgba(128, 128, 128, 0.3) !important;
  animation: none !important;
}

.tool-button:disabled img {
  filter: brightness(0) invert(1) !important;
  mix-blend-mode: normal !important;
}

.tool-button:disabled:hover {
  transform: none !important;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
  }
}

.panel-toast {
  position: absolute;
  bottom: 12px;
  left: 50%;
  transform: translateX(-50%);
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.9);
  background: rgba(30, 30, 60, 0.85);
  border: 1px solid rgba(100, 100, 200, 0.4);
  backdrop-filter: blur(8px);
  white-space: nowrap;
  z-index: 10;
  pointer-events: none;
}

.panel-toast.error {
  color: #ff9999;
  background: rgba(60, 20, 20, 0.9);
  border-color: rgba(200, 60, 60, 0.6);
}

@media (max-width: 720px) {
  .audio-visualizer-overlay {
    bottom: 12px;
    width: min(220px, 52vw);
  }

  .welcome-info-overlay {
    top: 6px;
    left: 8px;
    max-width: calc(100% - 76px);
    font-size: 0.72rem;
  }

  .panel-icons {
    top: 20px;
    right: 10px;
    gap: 8px;
  }

  .tool-button {
    width: 30px;
    height: 30px;
  }

  .tool-button img {
    width: 19px;
    height: 19px;
  }

  .tool-button.chat-button,
  .tool-button.agent-button,
  .tool-button.camera-button {
    width: 26px;
    height: 26px;
    font-size: 15px;
  }
}
</style>
