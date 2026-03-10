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
import type { AuthUser, ChatMessage, MessageKind, ModelSettings } from '@/types'

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
  chat: 'AiDiy AI',
  file: 'AiDiy File Manager',
  image: 'AiDiy Live Capture',
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
const fileRef = ref<{ 接続済み: boolean; 読込中: boolean; ファイルリスト要求: () => void } | null>(null)
const imageRef = ref<{ 接続状態: 'disconnected' | 'connecting' | 'sending'; 状態表示テキスト: string; WebSocket接続中: boolean } | null>(null)
const codeRef = ref<{ WebSocket接続中: boolean; 接続状態表示: string; 出力接続済み: boolean } | null>(null)
const subtitleText = ref('')
let subtitleTimer: ReturnType<typeof setTimeout> | null = null

function setSubtitle(text: string) {
  subtitleText.value = text
  if (subtitleTimer) clearTimeout(subtitleTimer)
  subtitleTimer = setTimeout(() => {
    subtitleText.value = ''
  }, 8000)
}

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
let detachWindowShownListener: (() => void) | null = null
let snapshotRetryTimer: ReturnType<typeof setInterval> | null = null

function requestSnapshot() {
  desktopChannel?.postMessage({ type: 'request-snapshot' })
}

function startSnapshotRetry() {
  if (snapshotRetryTimer) return
  snapshotRetryTimer = setInterval(() => {
    if (auxSnapshot.value?.sessionId) {
      stopSnapshotRetry()
      return
    }
    requestSnapshot()
  }, 1000)
}

function stopSnapshotRetry() {
  if (!snapshotRetryTimer) return
  clearInterval(snapshotRetryTimer)
  snapshotRetryTimer = null
}

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
    if (auxSnapshot.value?.sessionId) {
      stopSnapshotRetry()
    }
  }
}

async function detectWindowRole() {
  windowRole.value = (await window.desktopApi?.getWindowRole?.()) || resolveFallbackRole()
}

let streamMessageId: string | null = null

function newMessageId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function pushMessage(kind: MessageKind, text: string, extra?: Partial<ChatMessage>) {
  const normalized = String(text || '').trim()
  if (!normalized && !extra?.fileName) return

  messages.value.push({
    id: newMessageId(),
    kind,
    text: normalized,
    timestamp: new Date().toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' }),
    ...extra,
  })
}

function handleOutputStream(message: Record<string, any>) {
  const content = String(message.メッセージ内容 || '').trim()
  if (!content) return

  if (content === '<<< 処理開始 >>>') {
    const id = newMessageId()
    streamMessageId = id
    messages.value.push({
      id,
      kind: 'stream',
      text: `${content}\n`,
      timestamp: new Date().toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' }),
      isStream: true,
      isCollapsed: false,
    })
    return
  }

  if (content === '<<< 処理終了 >>>') {
    const target = messages.value.find((m) => m.id === streamMessageId)
    if (target) {
      target.text += `${content}\n`
      target.isCollapsed = true
    }
    streamMessageId = null
    return
  }

  const target = messages.value.find((m) => m.id === streamMessageId)
  if (target) {
    target.text += `${content}\n`
  }
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
  localStorage.removeItem('avatar_session_id')
  sessionId.value = ''
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

  const sessionHint = preferredSessionId || sessionId.value || ''

  try {
    // Web版と同様: REST APIでセッションを初期化してIDを取得
    let resolvedSessionId = sessionHint
    try {
      const initRes = await apiClient.post('/core/AIコア/初期化', { セッションID: sessionHint })
      if (initRes.data.status === 'OK' && initRes.data.data?.セッションID) {
        resolvedSessionId = initRes.data.data.セッションID
      }
    } catch {
      // REST失敗時はヒントをそのまま使用（WebSocket側で生成される）
    }

    const nextInputSocket = new AIWebSocket(AI_WS_ENDPOINT, resolvedSessionId, 'input')
    attachSocketState(nextInputSocket, inputConnected)
    nextInputSocket.on('init', handleInputInit)
    nextInputSocket.on('error', (message) => {
      coreError.value = String(message.メッセージ内容 || message.error || 'AIコア接続エラー')
    })
    nextInputSocket.on('welcome_info', (message) => {
      const text = String(message.メッセージ内容 || '').trim()
      if (text) welcomeInfo.value = text
    })
    nextInputSocket.on('welcome_text', (message) => {
      const text = String(message.メッセージ内容 || '')
      pushMessage('system', text)
      setSubtitle(text)
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
      const text = String(message.メッセージ内容 || '')
      pushMessage('system', text)
      setSubtitle(text)
    })
    nextChatSocket.on('input_text', (message) => {
      pushMessage('user', String(message.メッセージ内容 || ''))
    })
    nextChatSocket.on('input_request', (message) => {
      pushMessage('input-request', String(message.メッセージ内容 || ''))
    })
    nextChatSocket.on('input_file', (message) => {
      pushMessage('input-file', '', {
        fileName: message.ファイル名 ?? null,
        thumbnail: message.サムネイル画像 ?? null,
      })
    })
    nextChatSocket.on('output_text', (message) => {
      const text = String(message.メッセージ内容 || '')
      pushMessage('assistant', text)
      setSubtitle(text)
    })
    nextChatSocket.on('output_request', (message) => {
      pushMessage('output-request', String(message.メッセージ内容 || ''))
    })
    nextChatSocket.on('output_file', (message) => {
      pushMessage('output-file', '', {
        fileName: message.ファイル名 ?? null,
        thumbnail: message.サムネイル画像 ?? null,
      })
    })
    nextChatSocket.on('output_stream', handleOutputStream)
    nextChatSocket.on('recognition_input', (message) => {
      pushMessage('recognition-user', String(message.メッセージ内容 || ''))
    })
    nextChatSocket.on('recognition_output', (message) => {
      const text = String(message.メッセージ内容 || '')
      pushMessage('recognition-assistant', text)
      setSubtitle(text)
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
    broadcastSnapshot()
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
    localStorage.removeItem('avatar_session_id')
    sessionId.value = ''
    await fetchCurrentUser()
    windowRole.value = 'core'
    await window.desktopApi?.setWindowMode?.('core')
    await refreshPanelStates()
    await initializeCore('')
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
  await initializeCore(sessionId.value || '')
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
    送信モード: chatMode.value,
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

async function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const result = reader.result
      if (typeof result === 'string') {
        const i = result.indexOf(',')
        resolve(i >= 0 ? result.slice(i + 1) : result)
      } else {
        reject(new Error('unexpected result type'))
      }
    }
    reader.onerror = () => reject(reader.error)
    reader.readAsDataURL(file)
  })
}

async function handleChatFileDrop(files: File[]) {
  for (const file of files) {
    try {
      const base64 = await fileToBase64(file)
      sendInputPayloadFromWindow({
        チャンネル: '0',
        メッセージ識別: 'input_file',
        メッセージ内容: base64,
        ファイル名: file.name,
        サムネイル画像: null,
      })
    } catch (error) {
      coreError.value = `ファイル送信エラー: ${file.name}`
    }
  }
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

function handleImageTextSubmit(text: string) {
  if (!text.trim()) return
  sendInputPayloadFromWindow({
    チャンネル: 'input',
    メッセージ識別: 'input_text',
    メッセージ内容: text.trim(),
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
    requestSnapshot()
    startSnapshotRetry()
    detachWindowShownListener = window.desktopApi?.onWindowShown?.(() => {
      requestSnapshot()
      startSnapshotRetry()
    }) || null
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
    await initializeCore(sessionId.value || '')
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
  detachWindowShownListener?.()
  desktopChannel?.removeEventListener('message', handleDesktopChannelMessage)
  desktopChannel?.close()
  stopSnapshotRetry()
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
      :subtitle-text="subtitleText"
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
      theme="purple"
    >
      <template #title-right>
        <span :class="['chat-status-dot', displayInputConnected && displayChatConnected ? 'on' : '']"></span>
        <span class="chat-status-text">{{ displayInputConnected && displayChatConnected ? '接続中' : '切断' }}</span>
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
      theme="purple"
    >
      <template #title-right>
        <span :class="['file-status-dot', fileRef?.接続済み ? 'on' : '']"></span>
        <span class="file-status-text">{{ fileRef?.接続済み ? '接続中' : '切断' }}</span>
        <button class="file-reload-btn" type="button" :disabled="fileRef?.読込中" @click="fileRef?.ファイルリスト要求()">↺</button>
      </template>
      <component :is="AIファイル" ref="fileRef" :session-id="displaySessionId" :active="panelVisibility.file" />
    </component>

    <component
      :is="WindowShell"
      v-else-if="currentPanelKey === 'image'"
      :title="PANEL_TITLES.image"
      theme="purple"
    >
      <template #title-right>
        <span
          :class="[
            'image-status-dot',
            imageRef?.接続状態 === 'sending' ? 'sending' : imageRef?.WebSocket接続中 ? 'on' : '',
          ]"
        ></span>
        <span class="image-status-text">{{ imageRef?.状態表示テキスト || '切断' }}</span>
      </template>
      <component
        :is="AIイメージ"
        ref="imageRef"
        :session-id="displaySessionId"
        :input-connected="displayInputConnected"
        :active="panelVisibility.image"
        :auto-show-selection="panelVisibility.image"
        @submit-image="handleImageSubmit"
        @submit-text="handleImageTextSubmit"
      />
    </component>

    <component
      :is="WindowShell"
      v-else-if="currentPanelKey && currentCodeChannel"
      :title="PANEL_TITLES[currentPanelKey]"
      theme="purple"
    >
      <template #title-right>
        <span v-if="currentCodeModel" class="code-model-text">{{ currentCodeModel }}</span>
        <span :class="['code-status-dot', codeRef?.WebSocket接続中 ? 'on' : '']"></span>
        <span class="code-status-text">{{ codeRef?.接続状態表示 || '切断' }}</span>
      </template>
      <component
        :is="AIコード"
        ref="codeRef"
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

<style scoped>
.file-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #888;
  flex-shrink: 0;
}
.file-status-dot.on { background: #44ff44; }
.file-status-text { font-size: 10px; font-weight: bold; }
.file-reload-btn {
  background: #22c55e;
  border: 1px solid #16a34a;
  border-radius: 2px;
  font-size: 14px;
  color: #fff;
  cursor: pointer;
  width: 20px;
  height: 20px;
  line-height: 18px;
  text-align: center;
  padding: 0;
}
.file-reload-btn:hover:not(:disabled) { background: #34d399; }
.file-reload-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.chat-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #888;
  flex-shrink: 0;
}
.chat-status-dot.on { background: #44ff44; }
.chat-status-text { font-size: 10px; font-weight: bold; }
.image-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #888;
  flex-shrink: 0;
}
.image-status-dot.on { background: #44ff44; }
.image-status-dot.sending { background: #ff4444; }
.image-status-text { font-size: 10px; font-weight: bold; }
.code-model-text {
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 10px;
  color: rgba(255, 255, 255, 0.88);
}
.code-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #888;
  flex-shrink: 0;
}
.code-status-dot.on { background: #44ff44; }
.code-status-text { font-size: 10px; font-weight: bold; }
</style>
