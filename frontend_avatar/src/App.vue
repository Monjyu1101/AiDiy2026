<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import AIチャット from '@/components/AIチャット.vue'
import AIコア from '@/components/AIコア.vue'
import AIコード from '@/components/AIコード.vue'
import AIファイル from '@/components/AIファイル.vue'
import AIイメージ from '@/components/AIイメージ.vue'
import ログイン from '@/components/ログイン.vue'
import WindowShell from '@/components/WindowShell.vue'
import apiClient from '@/lib/api'
import { AudioController } from '@/lib/audio-controller'
import { AI_WS_ENDPOINT, defaultModelSettings } from '@/lib/config'
import { AIWebSocket } from '@/lib/websocket'
import type { AuthUser, ChatMessage, ModelSettings } from '@/types'

type PanelKey = 'chat' | 'file' | 'image' | 'code1' | 'code2' | 'code3' | 'code4'
type WindowRole = 'login' | 'core' | PanelKey
type チャットモード = 'Chat' | 'Live' | 'Code1' | 'Code2' | 'Code3' | 'Code4'
type SharedSnapshot = {
  isAuthenticated: boolean
  userLabel: string
  sessionId: string
  welcomeInfo: string
  messages: ChatMessage[]
  chatMode: チャットモード
  modelSettings: ModelSettings
  inputConnected: boolean
  chatConnected: boolean
  audioConnected: boolean
  micEnabled: boolean
  speakerEnabled: boolean
  micLevel: number
  speakerLevel: number
  panelVisibility: Record<PanelKey, boolean>
  coreBusy: boolean
  coreError: string
}

const PANEL_KEYS: PanelKey[] = ['chat', 'file', 'image', 'code1', 'code2', 'code3', 'code4']
const PANEL_TITLES: Record<PanelKey, string> = {
  chat: 'AiDiy AI Chat',
  file: 'AiDiy AI File',
  image: 'AiDiy AI Image',
  code1: 'AiDiy AI Code 1',
  code2: 'AiDiy AI Code 2',
  code3: 'AiDiy AI Code 3',
  code4: 'AiDiy AI Code 4',
}
const チャットモード一覧: チャットモード[] = ['Chat', 'Live', 'Code1', 'Code2', 'Code3', 'Code4']

function createPanelVisibility(): Record<PanelKey, boolean> {
  return {
    chat: false,
    file: false,
    image: false,
    code1: false,
    code2: false,
    code3: false,
    code4: false,
  }
}

function resolveFallbackRole(): WindowRole {
  const role = new URLSearchParams(window.location.search).get('role')
  if (role === 'core' || role === 'login' || PANEL_KEYS.includes(role as PanelKey)) {
    return role as WindowRole
  }
  return 'login'
}

const windowRole = ref<WindowRole>(resolveFallbackRole())
const token = ref(localStorage.getItem('token') || '')
const user = ref<AuthUser | null>(JSON.parse(localStorage.getItem('user') || 'null'))
const loadingAuth = ref(true)
const authBusy = ref(false)
const authError = ref('')
const coreBusy = ref(false)
const coreError = ref('')
const sessionId = ref(localStorage.getItem('avatar_session_id') || '')
const welcomeInfo = ref('')
const messages = ref<ChatMessage[]>([])
const chatMode = ref<チャットモード>('Live')
const modelSettings = ref<ModelSettings>(defaultModelSettings())
const auxSnapshot = ref<SharedSnapshot | null>(null)

const inputConnected = ref(false)
const chatConnected = ref(false)
const audioConnected = ref(false)
const micEnabled = ref(false)
const speakerEnabled = ref(true)
const micLevel = ref(0)
const speakerLevel = ref(0)
const panelVisibility = ref(createPanelVisibility())

const inputSocket = shallowRef<AIWebSocket | null>(null)
const chatSocket = shallowRef<AIWebSocket | null>(null)
const audioSocket = shallowRef<AIWebSocket | null>(null)
const audioController = shallowRef<AudioController | null>(null)

const versions = window.desktopApi?.versions

const isAuthenticated = computed(() => Boolean(token.value && user.value))
const isCoreWindow = computed(() => windowRole.value === 'core')
const isLoginWindow = computed(() => windowRole.value === 'login')
const currentPanelKey = computed<PanelKey | null>(() => {
  return PANEL_KEYS.includes(windowRole.value as PanelKey) ? (windowRole.value as PanelKey) : null
})
const userLabel = computed(() => user.value?.利用者名 || user.value?.利用者ID || '未ログイン')
const connectionReady = computed(() => inputConnected.value && chatConnected.value)
const transportState = computed(() => {
  if (connectionReady.value && audioConnected.value) return '接続中'
  if (coreBusy.value) return '接続中...'
  if (inputConnected.value || chatConnected.value || audioConnected.value) return '部分接続'
  return '切断'
})

const displayMessages = computed(() => (isCoreWindow.value ? messages.value : auxSnapshot.value?.messages || []))
const displayWelcomeInfo = computed(() =>
  isCoreWindow.value ? welcomeInfo.value : auxSnapshot.value?.welcomeInfo || '',
)
const displaySessionId = computed(() =>
  isCoreWindow.value ? sessionId.value : auxSnapshot.value?.sessionId || '',
)
const displayChatMode = computed(() =>
  isCoreWindow.value ? chatMode.value : auxSnapshot.value?.chatMode || 'Live',
)
const displayInputConnected = computed(() =>
  isCoreWindow.value ? inputConnected.value : Boolean(auxSnapshot.value?.inputConnected),
)
const displayChatConnected = computed(() =>
  isCoreWindow.value ? chatConnected.value : Boolean(auxSnapshot.value?.chatConnected),
)
const displayChatModel = computed(() =>
  isCoreWindow.value
    ? modelSettings.value.CHAT_AI_NAME || 'chat'
    : auxSnapshot.value?.modelSettings.CHAT_AI_NAME || 'chat',
)
const displayModelSettings = computed(() =>
  isCoreWindow.value ? modelSettings.value : auxSnapshot.value?.modelSettings || defaultModelSettings(),
)
const currentCodeChannel = computed<'1' | '2' | '3' | '4' | ''>(() => {
  switch (currentPanelKey.value) {
    case 'code1':
      return '1'
    case 'code2':
      return '2'
    case 'code3':
      return '3'
    case 'code4':
      return '4'
    default:
      return ''
  }
})
const currentCodeModel = computed(() => {
  switch (currentPanelKey.value) {
    case 'code1':
      return displayModelSettings.value.CODE_AI1_NAME
    case 'code2':
      return displayModelSettings.value.CODE_AI2_NAME
    case 'code3':
      return displayModelSettings.value.CODE_AI3_NAME
    case 'code4':
      return displayModelSettings.value.CODE_AI4_NAME
    default:
      return ''
  }
})

const authExpiredHandler = () => {
  clearAuth('認証の有効期限が切れました。再ログインしてください。')
}

let desktopChannel: BroadcastChannel | null = null
let detachPanelStatesListener: (() => void) | null = null

function updatePanelStates(states?: Record<PanelKey, boolean>) {
  panelVisibility.value = {
    ...createPanelVisibility(),
    ...(states || {}),
  }
}

async function refreshPanelStates() {
  const states = await window.desktopApi?.getPanelStates?.()
  if (states) {
    updatePanelStates(states)
  }
}

function buildSnapshot(): SharedSnapshot {
  return {
    isAuthenticated: isAuthenticated.value,
    userLabel: userLabel.value,
    sessionId: sessionId.value,
    welcomeInfo: welcomeInfo.value,
    messages: [...messages.value],
    chatMode: chatMode.value,
    modelSettings: { ...modelSettings.value },
    inputConnected: inputConnected.value,
    chatConnected: chatConnected.value,
    audioConnected: audioConnected.value,
    micEnabled: micEnabled.value,
    speakerEnabled: speakerEnabled.value,
    micLevel: micLevel.value,
    speakerLevel: speakerLevel.value,
    panelVisibility: { ...panelVisibility.value },
    coreBusy: coreBusy.value,
    coreError: coreError.value,
  }
}

function broadcastSnapshot() {
  if (!desktopChannel || !isCoreWindow.value) return
  desktopChannel.postMessage({ type: 'snapshot', snapshot: buildSnapshot() })
}

function handleDesktopChannelMessage(event: MessageEvent) {
  const payload = event.data
  if (!payload || typeof payload !== 'object') return

  if (isCoreWindow.value) {
    if (payload.type === 'request-snapshot') {
      broadcastSnapshot()
      return
    }

    if (payload.type === 'send-message' && typeof payload.text === 'string') {
      sendMessage(payload.text)
      return
    }

    if (payload.type === 'send-input-payload' && payload.message) {
      sendInputPayload(payload.message as Record<string, unknown>)
      return
    }

    if (payload.type === 'set-chat-mode' && チャットモード一覧.includes(payload.mode as チャットモード)) {
      chatMode.value = payload.mode
    }
    return
  }

  if (payload.type === 'snapshot') {
    auxSnapshot.value = payload.snapshot as SharedSnapshot
  }
}

async function detectWindowRole() {
  windowRole.value = (await window.desktopApi?.getWindowRole?.()) || resolveFallbackRole()
}

function pushMessage(kind: ChatMessage['kind'], text: string) {
  const normalized = String(text || '').trim()
  if (!normalized) return

  messages.value.push({
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    kind,
    text: normalized,
    timestamp: new Date().toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' }),
  })
}

function resetCoreState() {
  inputConnected.value = false
  chatConnected.value = false
  audioConnected.value = false
  welcomeInfo.value = ''
  messages.value = []
  micEnabled.value = false
  speakerEnabled.value = true
  micLevel.value = 0
  speakerLevel.value = 0
  coreError.value = ''
  modelSettings.value = defaultModelSettings()
  chatMode.value = 'Live'
}

function disconnectCore() {
  audioController.value?.cleanup()
  inputSocket.value?.disconnect()
  chatSocket.value?.disconnect()
  audioSocket.value?.disconnect()
  inputSocket.value = null
  chatSocket.value = null
  audioSocket.value = null
  resetCoreState()
}

function clearAuth(message = '') {
  token.value = ''
  user.value = null
  authBusy.value = false
  authError.value = message
  auxSnapshot.value = null
  updatePanelStates()
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  disconnectCore()
  windowRole.value = 'login'
  void window.desktopApi?.setWindowMode?.('login')
}

function attachSocketState(client: AIWebSocket, target: typeof inputConnected) {
  client.onStateChange((connected) => {
    target.value = connected
  })
}

function handleInputInit(message: Record<string, any>) {
  const payload = message.メッセージ内容 ?? {}
  const buttons = payload.ボタン ?? {}
  const settings = payload.モデル設定 ?? {}

  modelSettings.value = {
    CHAT_AI_NAME: settings.CHAT_AI_NAME || '',
    LIVE_AI_NAME: settings.LIVE_AI_NAME || '',
    CODE_AI1_NAME: settings.CODE_AI1_NAME || '',
    CODE_AI2_NAME: settings.CODE_AI2_NAME || '',
    CODE_AI3_NAME: settings.CODE_AI3_NAME || '',
    CODE_AI4_NAME: settings.CODE_AI4_NAME || '',
  }

  speakerEnabled.value = buttons.スピーカー ?? true
  micEnabled.value = buttons.マイク ?? false
  switch (String(buttons.チャットモード || 'live').toLowerCase()) {
    case 'chat':
      chatMode.value = 'Chat'
      break
    case 'code1':
      chatMode.value = 'Code1'
      break
    case 'code2':
      chatMode.value = 'Code2'
      break
    case 'code3':
      chatMode.value = 'Code3'
      break
    case 'code4':
      chatMode.value = 'Code4'
      break
    default:
      chatMode.value = 'Live'
      break
  }

  audioController.value?.setLiveModelName(modelSettings.value.LIVE_AI_NAME)
  audioController.value?.setSpeakerEnabled(speakerEnabled.value)
}

async function initializeCore(preferredSessionId = '') {
  if (!user.value) return

  disconnectCore()
  coreBusy.value = true
  coreError.value = ''

  const sessionHint = preferredSessionId || sessionId.value || user.value.利用者ID

  try {
    const nextInputSocket = new AIWebSocket(AI_WS_ENDPOINT, sessionHint, 'input')
    attachSocketState(nextInputSocket, inputConnected)
    nextInputSocket.on('init', handleInputInit)
    nextInputSocket.on('error', (message) => {
      coreError.value = String(message.メッセージ内容 || message.error || 'AIコア接続エラー')
    })

    const nextSessionId = await nextInputSocket.connect()
    sessionId.value = nextSessionId
    localStorage.setItem('avatar_session_id', nextSessionId)
    inputSocket.value = nextInputSocket

    const nextChatSocket = new AIWebSocket(AI_WS_ENDPOINT, nextSessionId, '0')
    attachSocketState(nextChatSocket, chatConnected)
    nextChatSocket.on('welcome_info', (message) => {
      welcomeInfo.value = String(message.メッセージ内容 || '').trim()
    })
    nextChatSocket.on('welcome_text', (message) => {
      pushMessage('system', String(message.メッセージ内容 || ''))
    })
    nextChatSocket.on('input_text', (message) => {
      pushMessage('user', String(message.メッセージ内容 || ''))
    })
    nextChatSocket.on('output_text', (message) => {
      pushMessage('assistant', String(message.メッセージ内容 || ''))
    })
    nextChatSocket.on('recognition_input', (message) => {
      pushMessage('recognition-user', String(message.メッセージ内容 || ''))
    })
    nextChatSocket.on('recognition_output', (message) => {
      pushMessage('recognition-assistant', String(message.メッセージ内容 || ''))
    })
    await nextChatSocket.connect()
    chatSocket.value = nextChatSocket

    const nextAudioSocket = new AIWebSocket(AI_WS_ENDPOINT, nextSessionId, 'audio')
    attachSocketState(nextAudioSocket, audioConnected)
    nextAudioSocket.on('output_audio', (message) => {
      audioController.value?.handleAudioMessage(message)
    })
    nextAudioSocket.on('cancel_audio', () => {
      audioController.value?.cancelOutput(false)
    })
    await nextAudioSocket.connect()
    audioSocket.value = nextAudioSocket

    audioController.value?.setAudioSocket(nextAudioSocket)
    audioController.value?.setSessionId(nextSessionId)
    audioController.value?.setLiveModelName(modelSettings.value.LIVE_AI_NAME)
    audioController.value?.setSpeakerEnabled(speakerEnabled.value)

    if (micEnabled.value) {
      const result = await audioController.value?.startMicrophone()
      if (!result?.success) {
        micEnabled.value = false
        coreError.value = result?.error || 'マイクを開始できませんでした。'
      }
    }

    syncOperationState()
  } catch (error) {
    coreError.value = error instanceof Error ? error.message : 'AIコアへ接続できませんでした。'
    disconnectCore()
  } finally {
    coreBusy.value = false
  }
}

function syncOperationState() {
  if (!inputSocket.value?.isConnected()) return

  inputSocket.value.send({
    セッションID: sessionId.value,
    チャンネル: 'input',
    メッセージ識別: 'operations',
    メッセージ内容: {
      ボタン: {
        マイク: micEnabled.value,
        スピーカー: speakerEnabled.value,
        チャット: true,
        チャットモード: chatMode.value.toLowerCase(),
      },
    },
  })
}

async function fetchCurrentUser() {
  if (!token.value) return

  const response = await apiClient.post('/core/auth/現在利用者')
  if (response.data.status !== 'OK') {
    throw new Error(response.data.message || '利用者情報を取得できませんでした。')
  }

  user.value = response.data.data
  localStorage.setItem('user', JSON.stringify(user.value))
}

async function submitLogin(payload: { 利用者ID: string; パスワード: string }) {
  authBusy.value = true
  authError.value = ''

  try {
    const response = await apiClient.post('/core/auth/ログイン', payload)
    if (response.data.status !== 'OK') {
      authError.value = response.data.message || 'ログインに失敗しました。'
      return
    }

    token.value = response.data.data.access_token
    localStorage.setItem('token', token.value)
    localStorage.setItem('avatar_last_user', payload.利用者ID)
    await fetchCurrentUser()
    windowRole.value = 'core'
    await window.desktopApi?.setWindowMode?.('core')
    await refreshPanelStates()
    await initializeCore(payload.利用者ID)
  } catch (error) {
    authError.value = error instanceof Error ? error.message : 'ログインエラーが発生しました。'
  } finally {
    authBusy.value = false
  }
}

async function toggleMicrophone() {
  if (!audioController.value) return

  coreError.value = ''
  await audioController.value.unlockAudio()
  if (!micEnabled.value) {
    const result = await audioController.value.startMicrophone()
    if (!result.success) {
      coreError.value = result.error || 'マイクを開始できませんでした。'
      return
    }
    micEnabled.value = true
  } else {
    audioController.value.stopMicrophone()
    micEnabled.value = false
  }

  syncOperationState()
}

function toggleSpeaker() {
  if (!audioController.value) return

  void audioController.value.unlockAudio()
  speakerEnabled.value = !speakerEnabled.value
  audioController.value.setSpeakerEnabled(speakerEnabled.value)
  syncOperationState()
}

async function togglePanel(panel: PanelKey) {
  const states = await window.desktopApi?.togglePanel?.(panel)
  if (states) {
    updatePanelStates(states)
  }
}

async function reconnect() {
  await initializeCore(sessionId.value || user.value?.利用者ID || '')
}

function sendInputPayload(message: Record<string, unknown>) {
  if (!inputSocket.value?.isConnected()) {
    coreError.value = 'AIコアに未接続です。再接続してください。'
    return
  }

  inputSocket.value.send({
    セッションID: sessionId.value,
    ...message,
  })
}

function sendMessage(text: string) {
  void audioController.value?.unlockAudio()

  sendInputPayload({
    チャンネル: '0',
    送信モード: chatMode.value.toLowerCase(),
    メッセージ識別: 'input_text',
    メッセージ内容: text,
  })
}

function sendMessageFromWindow(text: string) {
  if (isCoreWindow.value) {
    sendMessage(text)
    return
  }

  desktopChannel?.postMessage({ type: 'send-message', text })
}

function sendInputPayloadFromWindow(message: Record<string, unknown>) {
  if (isCoreWindow.value) {
    sendInputPayload(message)
    return
  }

  desktopChannel?.postMessage({ type: 'send-input-payload', message })
}

function handleChatFileDrop(files: File[]) {
  const firstFile = files[0]
  if (!firstFile) return
  coreError.value = `ファイル送信は AIチャット 未実装です: ${firstFile.name}`
}

function handleCodeSubmit(text: string, channel: '1' | '2' | '3' | '4') {
  sendInputPayloadFromWindow({
    チャンネル: channel,
    メッセージ識別: 'input_text',
    メッセージ内容: text,
  })
}

function handleCodeCancel(channel: '1' | '2' | '3' | '4') {
  sendInputPayloadFromWindow({
    チャンネル: channel,
    メッセージ識別: 'cancel_run',
    メッセージ内容: '強制停止！',
  })
}

function handleCodeFileSend(payload: { channel: '1' | '2' | '3' | '4'; fileName: string; base64: string }) {
  sendInputPayloadFromWindow({
    チャンネル: payload.channel,
    メッセージ識別: 'input_file',
    メッセージ内容: payload.base64,
    ファイル名: payload.fileName,
    サムネイル画像: null,
  })
}

function handleImageSubmit(payload: { text: string; mimeType: string; base64: string }) {
  const text = payload.text.trim()
  if (text) {
    sendInputPayloadFromWindow({
      チャンネル: 'input',
      メッセージ識別: 'input_text',
      メッセージ内容: text,
    })
  }

  sendInputPayloadFromWindow({
    チャンネル: 'input',
    出力先チャンネル: '0',
    メッセージ識別: 'input_image',
    メッセージ内容: payload.mimeType,
    ファイル名: payload.base64,
  })
}

function updateChatMode(nextMode: チャットモード) {
  if (isCoreWindow.value) {
    chatMode.value = nextMode
    return
  }

  if (auxSnapshot.value) {
    auxSnapshot.value = {
      ...auxSnapshot.value,
      chatMode: nextMode,
    }
  }
  desktopChannel?.postMessage({ type: 'set-chat-mode', mode: nextMode })
}

watch(chatMode, () => {
  if (!isCoreWindow.value) return
  syncOperationState()
})

watch(speakerEnabled, (enabled) => {
  audioController.value?.setSpeakerEnabled(enabled)
})

watch(
  () => ({
    role: windowRole.value,
    isAuthenticated: isAuthenticated.value,
    sessionId: sessionId.value,
    welcomeInfo: welcomeInfo.value,
    messages: messages.value,
    chatMode: chatMode.value,
    modelSettings: modelSettings.value,
    inputConnected: inputConnected.value,
    chatConnected: chatConnected.value,
    audioConnected: audioConnected.value,
    micEnabled: micEnabled.value,
    speakerEnabled: speakerEnabled.value,
    micLevel: micLevel.value,
    speakerLevel: speakerLevel.value,
    panelVisibility: panelVisibility.value,
    coreBusy: coreBusy.value,
    coreError: coreError.value,
    userLabel: userLabel.value,
  }),
  () => {
    broadcastSnapshot()
  },
  { deep: true },
)

onMounted(async () => {
  window.addEventListener('auth-expired', authExpiredHandler)

  desktopChannel = new BroadcastChannel('avatar-desktop-sync')
  desktopChannel.addEventListener('message', handleDesktopChannelMessage)

  await detectWindowRole()

  detachPanelStatesListener = window.desktopApi?.onPanelStatesChanged?.((states) => {
    updatePanelStates(states)
  }) || null

  if (currentPanelKey.value) {
    loadingAuth.value = false
    desktopChannel.postMessage({ type: 'request-snapshot' })
    return
  }

  audioController.value = new AudioController({
    onInputLevel: (value) => {
      micLevel.value = value
    },
    onOutputLevel: (value) => {
      speakerLevel.value = value
    },
    getSocket: () => audioSocket.value,
    getSessionId: () => sessionId.value,
  })

  await refreshPanelStates()

  if (!token.value) {
    loadingAuth.value = false
    await window.desktopApi?.setWindowMode?.('login')
    return
  }

  try {
    await fetchCurrentUser()
    windowRole.value = 'core'
    await window.desktopApi?.setWindowMode?.('core')
    await initializeCore(sessionId.value || user.value?.利用者ID || '')
  } catch {
    clearAuth()
  } finally {
    loadingAuth.value = false
    await refreshPanelStates()
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('auth-expired', authExpiredHandler)
  detachPanelStatesListener?.()
  desktopChannel?.removeEventListener('message', handleDesktopChannelMessage)
  desktopChannel?.close()
  disconnectCore()
})
</script>

<template>
  <main class="app-root">
    <component
      :is="ログイン"
      v-if="isLoginWindow && !isAuthenticated && !loadingAuth"
      :loading="authBusy"
      :error-message="authError"
      :versions="versions"
      @submit="submitLogin"
    />

    <component
      :is="AIコア"
      v-else-if="isCoreWindow && isAuthenticated"
      :session-id="sessionId"
      :user-label="userLabel"
      :live-model="modelSettings.LIVE_AI_NAME"
      :connection-ready="connectionReady"
      :transport-state="transportState"
      :input-connected="inputConnected"
      :chat-connected="chatConnected"
      :audio-connected="audioConnected"
      :mic-enabled="micEnabled"
      :speaker-enabled="speakerEnabled"
      :mic-level="micLevel"
      :speaker-level="speakerLevel"
      :panel-visibility="panelVisibility"
      :core-busy="coreBusy"
      :core-error="coreError"
      @toggle-microphone="toggleMicrophone"
      @toggle-speaker="toggleSpeaker"
      @toggle-panel="togglePanel"
      @reconnect="reconnect"
      @logout="clearAuth()"
    />

    <component
      :is="WindowShell"
      v-else-if="currentPanelKey === 'chat'"
      :title="PANEL_TITLES.chat"
      theme="light"
    >
      <template #title-right>
        <span class="panel-state">{{ displayChatModel }}</span>
        <span class="panel-state">{{ displayChatMode }}</span>
      </template>

      <component
        :is="AIチャット"
        :messages="displayMessages"
        :welcome-info="displayWelcomeInfo"
        :session-id="displaySessionId"
        :mode="displayChatMode"
        :input-connected="displayInputConnected"
        :chat-connected="displayChatConnected"
        :model-settings="displayModelSettings"
        @submit="sendMessageFromWindow"
        @update:mode="updateChatMode"
        @drop-files="handleChatFileDrop"
      />
    </component>

    <component
      :is="WindowShell"
      v-else-if="currentPanelKey === 'file'"
      :title="PANEL_TITLES.file"
      theme="light"
    >
      <component :is="AIファイル" :session-id="displaySessionId" />
    </component>

    <component
      :is="WindowShell"
      v-else-if="currentPanelKey === 'image'"
      :title="PANEL_TITLES.image"
      theme="light"
    >
      <component
        :is="AIイメージ"
        :session-id="displaySessionId"
        :input-connected="displayInputConnected"
        @submit-image="handleImageSubmit"
      />
    </component>

    <component
      :is="WindowShell"
      v-else-if="currentPanelKey && currentCodeChannel"
      :title="PANEL_TITLES[currentPanelKey]"
      theme="light"
    >
      <component
        :is="AIコード"
        :session-id="displaySessionId"
        :channel="currentCodeChannel"
        :code-ai="currentCodeModel"
        :input-connected="displayInputConnected"
        @submit="handleCodeSubmit"
        @cancel="handleCodeCancel"
        @send-file="handleCodeFileSend"
      />
    </component>

    <section v-else class="loading-state">
      <img class="loading-logo" src="/icons/loading.gif" alt="loading" />
      <p>認証状態を確認しています...</p>
    </section>
  </main>
</template>
