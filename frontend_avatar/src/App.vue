<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import AIチャット from '@/components/AIチャット.vue'
import AIコア from '@/components/AIコア.vue'
import AIコード from '@/components/AIコード.vue'
import AIファイル from '@/components/AIファイル.vue'
import AIイメージ from '@/components/AIイメージ.vue'
import ログイン from '@/components/ログイン.vue'
import WindowShell from '@/components/WindowShell.vue'
import apiClient from '@/_share/api'
import { AI_WS_ENDPOINT, defaultModelSettings } from '@/_share/config'
import { AIWebSocket } from '@/_share/websocket'
import type { AuthUser, ChatMessage, MessageKind, ModelSettings } from '@/types'

type PanelKey = 'chat' | 'file' | 'image' | 'code1' | 'code2' | 'code3' | 'code4'
type WindowRole = 'login' | 'core' | PanelKey
type チャットモード = 'Chat' | 'Live' | 'Code1' | 'Code2' | 'Code3' | 'Code4'
type SharedSnapshot = {
  認証済み: boolean
  利用者ラベル: string
  セッションID: string
  入力ウェルカム情報: string
  メッセージ一覧: ChatMessage[]
  チャットモード: チャットモード
  モデル設定: ModelSettings
  入力接続済み: boolean
  チャット接続済み: boolean
  パネル表示状態: Record<PanelKey, boolean>
  コア処理中: boolean
  コアエラー: string
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

function パネル表示状態生成(): Record<PanelKey, boolean> {
  return {
    chat: true,
    file: true,
    image: true,
    code1: true,
    code2: true,
    code3: true,
    code4: true,
  }
}

function フォールバックロール解決(): WindowRole {
  const role = new URLSearchParams(window.location.search).get('role')
  if (role === 'core' || role === 'login' || PANEL_KEYS.includes(role as PanelKey)) {
    return role as WindowRole
  }
  return 'login'
}

function 保存利用者読込(): AuthUser | null {
  const raw = localStorage.getItem('user')
  if (!raw) {
    return null
  }

  try {
    return JSON.parse(raw) as AuthUser
  } catch {
    localStorage.removeItem('user')
    return null
  }
}

const ウィンドウロール = ref<WindowRole>(フォールバックロール解決())
const 認証トークン = ref(localStorage.getItem('token') || '')
const 利用者 = ref<AuthUser | null>(保存利用者読込())
const 認証読込中 = ref(true)
const 認証処理中 = ref(false)
const 認証エラー = ref('')
const コア処理中 = ref(false)
const コアエラー = ref('')
const セッションID = ref(localStorage.getItem('avatar_session_id') || '')
const 入力ウェルカム情報 = ref('')
const メッセージ一覧 = ref<ChatMessage[]>([])
const チャットモード = ref<チャットモード>('Live')
const モデル設定 = ref<ModelSettings>(defaultModelSettings())
const 補助スナップショット = ref<SharedSnapshot | null>(null)

const 入力接続済み = ref(false)
const チャット接続済み = ref(false)
const 初期マイク有効 = ref(false)
const 初期スピーカー有効 = ref(true)
const 音声状態シード = ref(0)
const パネル表示状態 = ref(パネル表示状態生成())

const coreSocket = shallowRef<AIWebSocket | null>(null)
const inputSocket = shallowRef<AIWebSocket | null>(null)
const chatSocket = shallowRef<AIWebSocket | null>(null)
const ファイルRef = ref<{ 接続済み: boolean; 読込中: boolean; ファイルリスト要求: () => void } | null>(null)
const イメージRef = ref<{ 接続状態: 'disconnected' | 'connecting' | 'sending'; 状態表示テキスト: string; WebSocket接続中: boolean } | null>(null)
const チャットRef = ref<{ WebSocket接続中: boolean; チャット接続済み: boolean } | null>(null)
const コードRef = ref<{ WebSocket接続中: boolean; 接続状態表示: string; 出力接続済み: boolean } | null>(null)
const 自動選択表示 = ref(true)
const 認証エラーメッセージKey = 'avatar_auth_error'
const コアViewRef = ref<{ addSubtitle: (text: string) => void } | null>(null)

const versions = window.desktopApi?.versions

const 認証済み = computed(() => Boolean(認証トークン.value && 利用者.value))
const コアウィンドウ = computed(() => ウィンドウロール.value === 'core')
const ログインウィンドウ = computed(() => ウィンドウロール.value === 'login')
const 現在パネルキー = computed<PanelKey | null>(() => {
  return PANEL_KEYS.includes(ウィンドウロール.value as PanelKey) ? (ウィンドウロール.value as PanelKey) : null
})
const 利用者ラベル = computed(() => 利用者.value?.利用者名 || 利用者.value?.利用者ID || '未ログイン')

const 表示メッセージ一覧 = computed(() => (コアウィンドウ.value ? メッセージ一覧.value : 補助スナップショット.value?.メッセージ一覧 || []))
const 表示ウェルカム情報 = computed(() =>
  コアウィンドウ.value ? 入力ウェルカム情報.value : 補助スナップショット.value?.入力ウェルカム情報 || '',
)
const 表示セッションID = computed(() =>
  コアウィンドウ.value ? セッションID.value : 補助スナップショット.value?.セッションID || '',
)
const 表示チャットモード = computed(() =>
  コアウィンドウ.value ? チャットモード.value : 補助スナップショット.value?.チャットモード || 'Live',
)
const 表示入力接続済み = computed(() =>
  コアウィンドウ.value ? 入力接続済み.value : Boolean(補助スナップショット.value?.入力接続済み),
)
const 表示チャット接続済み = computed(() =>
  コアウィンドウ.value ? チャット接続済み.value : Boolean(補助スナップショット.value?.チャット接続済み),
)
const 表示チャットモデル = computed(() =>
  コアウィンドウ.value
    ? モデル設定.value.CHAT_AI_NAME || 'chat'
    : 補助スナップショット.value?.モデル設定.CHAT_AI_NAME || 'chat',
)
const 表示モデル設定 = computed(() =>
  コアウィンドウ.value ? モデル設定.value : 補助スナップショット.value?.モデル設定 || defaultModelSettings(),
)
const 現在コードチャンネル = computed<'1' | '2' | '3' | '4' | ''>(() => {
  switch (現在パネルキー.value) {
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
const 現在コードモデル = computed(() => {
  switch (現在パネルキー.value) {
    case 'code1':
      return 表示モデル設定.value.CODE_AI1_NAME
    case 'code2':
      return 表示モデル設定.value.CODE_AI2_NAME
    case 'code3':
      return 表示モデル設定.value.CODE_AI3_NAME
    case 'code4':
      return 表示モデル設定.value.CODE_AI4_NAME
    default:
      return ''
  }
})

const 認証期限切れ処理 = () => {
  認証クリア('認証の有効期限が切れました。再ログインしてください。')
}

let デスクトップチャンネル: BroadcastChannel | null = null
let パネル状態リスナー解除: (() => void) | null = null
let ウィンドウ表示リスナー解除: (() => void) | null = null
let スナップショット再試行タイマー: ReturnType<typeof setInterval> | null = null

function ストレージ認証同期(options: { syncError?: boolean } = {}) {
  認証トークン.value = localStorage.getItem('token') || ''
  利用者.value = 認証トークン.value ? 保存利用者読込() : null

  if (options.syncError) {
    認証エラー.value = localStorage.getItem(認証エラーメッセージKey) || ''
    if (認証エラー.value) {
      localStorage.removeItem(認証エラーメッセージKey)
    }
  }
}

function ストレージ変更処理(event: StorageEvent) {
  if (
    event.key
    && event.key !== 'token'
    && event.key !== 'user'
    && event.key !== 認証エラーメッセージKey
    && event.key !== 'avatar_session_id'
  ) {
    return
  }

  ストレージ認証同期({ syncError: event.key === 認証エラーメッセージKey || !event.key })
}

function スナップショット要求() {
  デスクトップチャンネル?.postMessage({ type: 'request-snapshot' })
}

function スナップショット再試行開始() {
  if (スナップショット再試行タイマー) return
  スナップショット再試行タイマー = setInterval(() => {
    if (補助スナップショット.value?.セッションID) {
      スナップショット再試行停止()
      return
    }
    スナップショット要求()
  }, 1000)
}

function スナップショット再試行停止() {
  if (!スナップショット再試行タイマー) return
  clearInterval(スナップショット再試行タイマー)
  スナップショット再試行タイマー = null
}

function パネル状態更新(states?: Record<PanelKey, boolean>) {
  パネル表示状態.value = {
    ...パネル表示状態生成(),
    ...(states || {}),
  }
}

async function パネル状態再読込() {
  const states = await window.desktopApi?.getPanelStates?.()
  if (states) {
    パネル状態更新(states)
  }
}

function スナップショット構築(): SharedSnapshot {
  return {
    認証済み: 認証済み.value,
    利用者ラベル: 利用者ラベル.value,
    セッションID: セッションID.value,
    入力ウェルカム情報: 入力ウェルカム情報.value,
    メッセージ一覧: [...メッセージ一覧.value],
    チャットモード: チャットモード.value,
    モデル設定: { ...モデル設定.value },
    入力接続済み: 入力接続済み.value,
    チャット接続済み: チャット接続済み.value,
    パネル表示状態: { ...パネル表示状態.value },
    コア処理中: コア処理中.value,
    コアエラー: コアエラー.value,
  }
}

function スナップショット送信() {
  if (!デスクトップチャンネル || !コアウィンドウ.value) return
  デスクトップチャンネル.postMessage({ type: 'snapshot', snapshot: スナップショット構築() })
}

function デスクトップチャンネルメッセージ処理(event: MessageEvent) {
  const payload = event.data
  if (!payload || typeof payload !== 'object') return

  if (コアウィンドウ.value) {
    if (payload.type === 'request-snapshot') {
      スナップショット送信()
      return
    }

    if (payload.type === 'send-message' && typeof payload.text === 'string') {
      メッセージ送信(payload.text)
      return
    }

    if (payload.type === 'send-input-payload' && payload.message) {
      入力ペイロード送信(payload.message as Record<string, unknown>)
      return
    }

    if (payload.type === 'set-chat-mode' && チャットモード一覧.includes(payload.mode as チャットモード)) {
      チャットモード.value = payload.mode
      return
    }

    if (payload.type === 'chat-state' && typeof payload.connected === 'boolean') {
      チャット接続済み.value = payload.connected
      return
    }

    return
  }

  if (payload.type === 'snapshot') {
    補助スナップショット.value = payload.snapshot as SharedSnapshot
    if (補助スナップショット.value?.セッションID) {
      スナップショット再試行停止()
    }
  }
}

async function ウィンドウロール検出() {
  ウィンドウロール.value = (await window.desktopApi?.getWindowRole?.()) || フォールバックロール解決()
}

let ストリームメッセージID: string | null = null

function 新規メッセージID(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function メッセージ追加(kind: MessageKind, text: string, extra?: Partial<ChatMessage>) {
  const normalized = String(text || '').trim()
  if (!normalized && !extra?.fileName) return

  メッセージ一覧.value.push({
    id: 新規メッセージID(),
    kind,
    text: normalized,
    timestamp: new Date().toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' }),
    ...extra,
  })
}

function 出力ストリーム処理(message: Record<string, any>) {
  const content = String(message.メッセージ内容 || '').trim()
  if (!content) return

  if (content === '<<< 処理開始 >>>') {
    const id = 新規メッセージID()
    ストリームメッセージID = id
    メッセージ一覧.value.push({
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
    const target = メッセージ一覧.value.find((m) => m.id === ストリームメッセージID)
    if (target) {
      target.text += `${content}\n`
      target.isCollapsed = true
    }
    ストリームメッセージID = null
    return
  }

  const target = メッセージ一覧.value.find((m) => m.id === ストリームメッセージID)
  if (target) {
    target.text += `${content}\n`
  }
}

function コア状態リセット() {
  入力接続済み.value = false
  チャット接続済み.value = false
  入力ウェルカム情報.value = ''
  メッセージ一覧.value = []
  初期マイク有効.value = false
  初期スピーカー有効.value = true
  コアエラー.value = ''
  モデル設定.value = defaultModelSettings()
  チャットモード.value = 'Live'
}

function コア切断() {
  coreSocket.value?.disconnect()
  inputSocket.value?.disconnect()
  chatSocket.value?.disconnect()
  inputSocket.value = null
  chatSocket.value = null
  コア状態リセット()
}

function 認証クリア(message = '') {
  認証トークン.value = ''
  利用者.value = null
  認証処理中.value = false
  認証エラー.value = message
  補助スナップショット.value = null
  パネル状態更新()
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  localStorage.removeItem('avatar_session_id')
  if (message) {
    localStorage.setItem(認証エラーメッセージKey, message)
  } else {
    localStorage.removeItem(認証エラーメッセージKey)
  }
  セッションID.value = ''
  コア切断()
  ウィンドウロール.value = 'login'
  void window.desktopApi?.openLoginWindow?.()
}

function ソケット状態バインド(client: AIWebSocket, target: typeof 入力接続済み) {
  client.onStateChange((connected) => {
    target.value = connected
  })
}

function 初期化処理(message: Record<string, any>) {
  const payload = message.メッセージ内容 ?? {}
  const buttons = payload.ボタン ?? {}
  const settings = payload.モデル設定 ?? {}

  モデル設定.value = {
    CHAT_AI_NAME: settings.CHAT_AI_NAME || '',
    LIVE_AI_NAME: settings.LIVE_AI_NAME || '',
    CODE_AI1_NAME: settings.CODE_AI1_NAME || '',
    CODE_AI2_NAME: settings.CODE_AI2_NAME || '',
    CODE_AI3_NAME: settings.CODE_AI3_NAME || '',
    CODE_AI4_NAME: settings.CODE_AI4_NAME || '',
  }

  初期スピーカー有効.value = buttons.スピーカー ?? true
  初期マイク有効.value = buttons.マイク ?? false
  音声状態シード.value += 1
  switch (String(buttons.チャットモード || 'live').toLowerCase()) {
    case 'chat':
      チャットモード.value = 'Chat'
      break
    case 'code1':
      チャットモード.value = 'Code1'
      break
    case 'code2':
      チャットモード.value = 'Code2'
      break
    case 'code3':
      チャットモード.value = 'Code3'
      break
    case 'code4':
      チャットモード.value = 'Code4'
      break
    default:
      チャットモード.value = 'Live'
      break
  }
}

async function コア初期化(preferredSessionId = '') {
  if (!利用者.value) return

  コア切断()
  コア処理中.value = true
  コアエラー.value = ''

  const sessionHint = preferredSessionId || セッションID.value || ''

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

    // coreチャンネルを先に接続（init・制御メッセージ・welcome を一括受信）
    const nextCoreSocket = new AIWebSocket(AI_WS_ENDPOINT, resolvedSessionId, 'core')
    ソケット状態バインド(nextCoreSocket, 入力接続済み)
    nextCoreSocket.on('init', 初期化処理)
    nextCoreSocket.on('error', (message) => {
      コアエラー.value = String(message.メッセージ内容 || message.error || 'AIコア接続エラー')
    })
    nextCoreSocket.on('welcome_info', (message) => {
      const text = String(message.メッセージ内容 || '').trim()
      if (text) 入力ウェルカム情報.value = text
    })
    nextCoreSocket.on('welcome_text', (message) => {
      const text = String(message.メッセージ内容 || '')
      メッセージ追加('system', text)
    })
    nextCoreSocket.on('output_text', (message) => {
      const text = String(message.メッセージ内容 || '')
      if (text) コアViewRef.value?.addSubtitle(text)
    })
    nextCoreSocket.on('recognition_output', (message) => {
      const text = String(message.メッセージ内容 || '')
      if (text) コアViewRef.value?.addSubtitle(text)
    })

    const nextSessionId = await nextCoreSocket.connect()
    セッションID.value = nextSessionId
    localStorage.setItem('avatar_session_id', nextSessionId)
    coreSocket.value = nextCoreSocket

    // inputチャンネルを接続（送信専用・ハンドラなし）
    const nextInputSocket = new AIWebSocket(AI_WS_ENDPOINT, nextSessionId, 'input')
    nextInputSocket.connect().catch((e) => console.error('[Avatar] inputチャンネル接続エラー:', e))
    inputSocket.value = nextInputSocket

    操作状態同期()
    スナップショット送信()
  } catch (error) {
    コアエラー.value = error instanceof Error ? error.message : 'AIコアへ接続できませんでした。'
    コア切断()
  } finally {
    コア処理中.value = false
  }
}

function 操作状態同期() {
  if (!inputSocket.value?.isConnected()) return

  inputSocket.value.send({
    セッションID: セッションID.value,
    チャンネル: 'input',
    メッセージ識別: 'operations',
    メッセージ内容: {
      ボタン: {
        ファイル: パネル表示状態.value.file,
        チャット: パネル表示状態.value.chat,
        エージェント1: パネル表示状態.value.code1,
        イメージ: パネル表示状態.value.image,
        エージェント2: パネル表示状態.value.code2,
        エージェント3: パネル表示状態.value.code3,
        エージェント4: パネル表示状態.value.code4,
        チャットモード: チャットモード.value.toLowerCase(),
      },
    },
  })
}

async function 現在利用者取得() {
  if (!認証トークン.value) return

  const response = await apiClient.post('/core/auth/現在利用者')
  if (response.data.status !== 'OK') {
    throw new Error(response.data.message || '利用者情報を取得できませんでした。')
  }

  利用者.value = response.data.data
  localStorage.setItem('user', JSON.stringify(利用者.value))
}

async function ログイン送信(payload: { 利用者ID: string; パスワード: string }) {
  認証処理中.value = true
  認証エラー.value = ''

  try {
    const response = await apiClient.post('/core/auth/ログイン', payload)
    if (response.data.status !== 'OK') {
      認証エラー.value = response.data.message || 'ログインに失敗しました。'
      return
    }

    認証トークン.value = response.data.data.access_token
    localStorage.setItem('token', 認証トークン.value)
    localStorage.setItem('avatar_last_user', payload.利用者ID)
    localStorage.removeItem('user')
    localStorage.removeItem(認証エラーメッセージKey)
    localStorage.removeItem('avatar_session_id')
    セッションID.value = ''
    await window.desktopApi?.openCoreWindow?.()
  } catch (error) {
    認証エラー.value = error instanceof Error ? error.message : 'ログインエラーが発生しました。'
  } finally {
    認証処理中.value = false
  }
}

async function パネル切替(panel: PanelKey) {
  const nextStates = {
    ...パネル表示状態.value,
    [panel]: !パネル表示状態.value[panel],
  }
  パネル状態更新(nextStates)
  操作状態同期()
  スナップショット送信()

  try {
    const states = await window.desktopApi?.togglePanel?.(panel)
    if (states) {
      パネル状態更新(states)
      操作状態同期()
      スナップショット送信()
    }
  } catch {
    パネル状態更新({
      ...nextStates,
      [panel]: !nextStates[panel],
    })
    操作状態同期()
    スナップショット送信()
  }
}

async function イメージ選択キャンセル() {
  自動選択表示.value = false
  if (現在パネルキー.value === 'image') {
    const states = await window.desktopApi?.togglePanel?.('image')
    if (states) {
      パネル状態更新(states)
    }
  }
}

function イメージ選択完了() {
  自動選択表示.value = false
}

async function 再接続() {
  await コア初期化(セッションID.value || '')
}

function チャット状態中継(connected: boolean) {
  if (コアウィンドウ.value) {
    チャット接続済み.value = connected
    return
  }
  デスクトップチャンネル?.postMessage({ type: 'chat-state', connected })
}

function 入力ペイロード送信(message: Record<string, unknown>) {
  if (!inputSocket.value?.isConnected()) {
    コアエラー.value = 'AIコアに未接続です。再接続してください。'
    return
  }

  inputSocket.value.send({
    セッションID: セッションID.value,
    ...message,
  })
}

function メッセージ送信(text: string) {
  入力ペイロード送信({
    チャンネル: '0',
    送信モード: チャットモード.value,
    メッセージ識別: 'input_text',
    メッセージ内容: text,
  })
}

function ウィンドウからメッセージ送信(text: string) {
  if (コアウィンドウ.value) {
    メッセージ送信(text)
    return
  }

  デスクトップチャンネル?.postMessage({ type: 'send-message', text })
}

function ウィンドウから入力ペイロード送信(message: Record<string, unknown>) {
  if (コアウィンドウ.value) {
    入力ペイロード送信(message)
    return
  }

  デスクトップチャンネル?.postMessage({ type: 'send-input-payload', message })
}

async function ファイルをBase64変換(file: File): Promise<string> {
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

async function チャットファイルドロップ処理(files: File[]) {
  for (const file of files) {
    try {
      const base64 = await ファイルをBase64変換(file)
      ウィンドウから入力ペイロード送信({
        チャンネル: '0',
        メッセージ識別: 'input_file',
        メッセージ内容: base64,
        ファイル名: file.name,
        サムネイル画像: null,
      })
    } catch (error) {
      コアエラー.value = `ファイル送信エラー: ${file.name}`
    }
  }
}

function コード送信処理(text: string, channel: '1' | '2' | '3' | '4') {
  ウィンドウから入力ペイロード送信({
    チャンネル: channel,
    メッセージ識別: 'input_text',
    メッセージ内容: text,
  })
}

function コードキャンセル処理(channel: '1' | '2' | '3' | '4') {
  ウィンドウから入力ペイロード送信({
    チャンネル: channel,
    メッセージ識別: 'cancel_run',
    メッセージ内容: '強制停止！',
  })
}

function コードファイル送信処理(payload: { channel: '1' | '2' | '3' | '4'; fileName: string; base64: string }) {
  ウィンドウから入力ペイロード送信({
    チャンネル: payload.channel,
    メッセージ識別: 'input_file',
    メッセージ内容: payload.base64,
    ファイル名: payload.fileName,
    サムネイル画像: null,
  })
}

function イメージ送信処理(payload: { text: string; mimeType: string; base64: string }) {
  const text = payload.text.trim()
  if (text) {
    ウィンドウから入力ペイロード送信({
      チャンネル: 'input',
      メッセージ識別: 'input_text',
      メッセージ内容: text,
    })
  }

  ウィンドウから入力ペイロード送信({
    チャンネル: 'input',
    出力先チャンネル: '0',
    メッセージ識別: 'input_image',
    メッセージ内容: payload.mimeType,
    ファイル名: payload.base64,
  })
}

function イメージテキスト送信処理(text: string) {
  if (!text.trim()) return
  ウィンドウから入力ペイロード送信({
    チャンネル: 'input',
    メッセージ識別: 'input_text',
    メッセージ内容: text.trim(),
  })
}

function チャットモード更新(nextMode: チャットモード) {
  if (コアウィンドウ.value) {
    チャットモード.value = nextMode
    return
  }

  if (補助スナップショット.value) {
    補助スナップショット.value = {
      ...補助スナップショット.value,
      チャットモード: nextMode,
    }
  }
  デスクトップチャンネル?.postMessage({ type: 'set-chat-mode', mode: nextMode })
}

watch(チャットモード, () => {
  if (!コアウィンドウ.value) return
  操作状態同期()
})

watch(パネル表示状態, () => {
  if (!コアウィンドウ.value) return
  操作状態同期()
}, { deep: true })

watch(
  () => ({
    role: ウィンドウロール.value,
    認証済み: 認証済み.value,
    セッションID: セッションID.value,
    入力ウェルカム情報: 入力ウェルカム情報.value,
    メッセージ一覧: メッセージ一覧.value,
    チャットモード: チャットモード.value,
    モデル設定: モデル設定.value,
    入力接続済み: 入力接続済み.value,
    チャット接続済み: チャット接続済み.value,
    パネル表示状態: パネル表示状態.value,
    コア処理中: コア処理中.value,
    コアエラー: コアエラー.value,
    利用者ラベル: 利用者ラベル.value,
  }),
  () => {
    スナップショット送信()
  },
  { deep: true },
)

onMounted(async () => {
  window.addEventListener('auth-expired', 認証期限切れ処理)
  window.addEventListener('storage', ストレージ変更処理)

  デスクトップチャンネル = new BroadcastChannel('avatar-desktop-sync')
  デスクトップチャンネル.addEventListener('message', デスクトップチャンネルメッセージ処理)

  await ウィンドウロール検出()

  パネル状態リスナー解除 = window.desktopApi?.onPanelStatesChanged?.((states) => {
    パネル状態更新(states)
  }) || null

  ウィンドウ表示リスナー解除 = window.desktopApi?.onWindowShown?.(() => {
    ストレージ認証同期({ syncError: ログインウィンドウ.value })
    if (現在パネルキー.value) {
      スナップショット要求()
      スナップショット再試行開始()
    }
  }) || null

  if (現在パネルキー.value) {
    認証読込中.value = false
    スナップショット要求()
    スナップショット再試行開始()
    return
  }

  await パネル状態再読込()
  ストレージ認証同期({ syncError: true })

  if (!認証トークン.value) {
    認証読込中.value = false
    return
  }

  try {
    await 現在利用者取得()

    if (ログインウィンドウ.value) {
      await window.desktopApi?.openCoreWindow?.()
      return
    }

    await コア初期化(セッションID.value || '')
  } catch {
    認証クリア()
  } finally {
    認証読込中.value = false
    await パネル状態再読込()
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('auth-expired', 認証期限切れ処理)
  window.removeEventListener('storage', ストレージ変更処理)
  パネル状態リスナー解除?.()
  ウィンドウ表示リスナー解除?.()
  デスクトップチャンネル?.removeEventListener('message', デスクトップチャンネルメッセージ処理)
  デスクトップチャンネル?.close()
  スナップショット再試行停止()
  コア切断()
})
</script>

<template>
  <main class="app-root">
    <component
      :is="ログイン"
      v-if="ログインウィンドウ && (!認証済み || 認証処理中) && !認証読込中"
      :loading="認証処理中"
      :error-message="認証エラー"
      :versions="versions"
      @submit="ログイン送信"
    />

    <component
      :is="AIコア"
      v-else-if="コアウィンドウ && 認証済み"
      ref="コアViewRef"
      :session-id="セッションID"
      :user-label="利用者ラベル"
      :live-model="モデル設定.LIVE_AI_NAME"
      :welcome-info="入力ウェルカム情報"
      :input-connected="入力接続済み"
      :input-socket="inputSocket"
      :initial-mic-enabled="初期マイク有効"
      :initial-speaker-enabled="初期スピーカー有効"
      :audio-state-seed="音声状態シード"
      :panel-visibility="パネル表示状態"
      :core-busy="コア処理中"
      :core-error="コアエラー"
      @toggle-panel="パネル切替"
      @reconnect="再接続"
      @logout="認証クリア()"
    />

    <component
      :is="WindowShell"
      v-else-if="現在パネルキー === 'chat'"
      :title="PANEL_TITLES.chat"
      theme="purple"
    >
      <template #title-right>
        <span :class="['chat-status-dot', チャットRef?.WebSocket接続中 ? 'on' : '']"></span>
        <span class="chat-status-text">{{ チャットRef?.WebSocket接続中 ? '接続中' : '切断' }}</span>
      </template>

      <component
        :is="AIチャット"
        ref="チャットRef"
        :messages="表示メッセージ一覧"
        :welcome-info="表示ウェルカム情報"
        :session-id="表示セッションID"
        :active="パネル表示状態.chat"
        :mode="表示チャットモード"
        :input-connected="表示入力接続済み"
        :chat-connected="表示チャット接続済み"
        :model-settings="表示モデル設定"
        @send-input-payload="ウィンドウから入力ペイロード送信"
        @update:mode="チャットモード更新"
        @chat-state="チャット状態中継"
      />
    </component>

    <component
      :is="WindowShell"
      v-else-if="現在パネルキー === 'file'"
      :title="PANEL_TITLES.file"
      theme="purple"
    >
      <template #title-right>
        <span :class="['file-status-dot', ファイルRef?.接続済み ? 'on' : '']"></span>
        <span class="file-status-text">{{ ファイルRef?.接続済み ? '接続中' : '切断' }}</span>
        <button class="file-reload-btn" type="button" :disabled="ファイルRef?.読込中" @click="ファイルRef?.ファイルリスト要求()">↺</button>
      </template>
      <component
        :is="AIファイル"
        ref="ファイルRef"
        :session-id="表示セッションID"
        :active="パネル表示状態.file"
        @send-input-payload="ウィンドウから入力ペイロード送信"
      />
    </component>

    <component
      :is="WindowShell"
      v-else-if="現在パネルキー === 'image'"
      :title="PANEL_TITLES.image"
      theme="purple"
    >
      <template #title-right>
        <span
          :class="[
            'image-status-dot',
            イメージRef?.接続状態 === 'sending' ? 'sending' : イメージRef?.WebSocket接続中 ? 'on' : '',
          ]"
        ></span>
        <span class="image-status-text">{{ イメージRef?.状態表示テキスト || '切断' }}</span>
      </template>
      <component
        :is="AIイメージ"
        ref="イメージRef"
        :session-id="表示セッションID"
        :input-connected="表示入力接続済み"
        :active="パネル表示状態.image"
        :auto-show-selection="自動選択表示"
        @submit-image="イメージ送信処理"
        @submit-text="イメージテキスト送信処理"
        @selection-cancel="イメージ選択キャンセル"
        @selection-complete="イメージ選択完了"
      />
    </component>

    <component
      :is="WindowShell"
      v-else-if="現在パネルキー && 現在コードチャンネル"
      :title="PANEL_TITLES[現在パネルキー]"
      theme="purple"
    >
      <template #title-right>
        <span v-if="現在コードモデル" class="code-model-text">{{ 現在コードモデル }}</span>
        <span :class="['code-status-dot', コードRef?.WebSocket接続中 ? 'on' : '']"></span>
        <span class="code-status-text">{{ コードRef?.接続状態表示 || '切断' }}</span>
      </template>
      <component
        :is="AIコード"
        ref="コードRef"
        :session-id="表示セッションID"
        :channel="現在コードチャンネル"
        :active="現在パネルキー ? パネル表示状態[現在パネルキー] : false"
        :code-ai="現在コードモデル"
        :input-connected="表示入力接続済み"
        @submit="コード送信処理"
        @cancel="コードキャンセル処理"
        @send-file="コードファイル送信処理"
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
