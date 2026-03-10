<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { AI_WS_ENDPOINT } from '@/lib/config'
import { AIWebSocket } from '@/lib/websocket'

type コードチャンネル = '1' | '2' | '3' | '4'
type 行種別 =
  | 'input_text'
  | 'input_request'
  | 'output_text'
  | 'welcome_text'
  | 'input_file'
  | 'output_file'
  | 'cancel_run'
  | 'stream'

type 行データ = {
  id: string
  role: 行種別
  content: string
  fileName?: string
  thumbnail?: string | null
  isStream?: boolean
  isCollapsed?: boolean
}

const props = defineProps<{
  sessionId: string
  channel: コードチャンネル
  codeAi: string
  inputConnected: boolean
}>()

const emit = defineEmits<{
  submit: [text: string, channel: コードチャンネル]
  cancel: [channel: コードチャンネル]
  'send-file': [payload: { channel: コードチャンネル; fileName: string; base64: string }]
}>()

const 出力接続済み = ref(false)
const メッセージ一覧 = ref<行データ[]>([])
const 入力テキスト = ref('')
const 送信中 = ref(false)
const ストリーム受信中 = ref(false)
const ドラッグ中 = ref(false)
const チャット領域 = ref<HTMLElement | null>(null)
const テキストエリア = ref<HTMLTextAreaElement | null>(null)
const 入力欄最大到達 = ref(false)
const 入力欄固定中 = ref(false)
const 入力欄固定高さ = ref(60)
const 入力欄最小高さ = 60
const 入力欄最大高さ = ref(380)

let 出力WebSocket: AIWebSocket | null = null
let messageSeq = 0
let streamMessageId: string | null = null

const WebSocket接続中 = computed(() => props.inputConnected && 出力接続済み.value)
const 接続状態表示 = computed(() => (WebSocket接続中.value ? '接続中' : '切断'))

// ===================== ターミナルエフェクト =====================

type 演出状態 = {
  container: HTMLElement
  textSpan: HTMLElement
  cursorSpan: HTMLElement
  queue: string[]
  running: boolean
  ready: boolean
  finalizeOnEmpty: boolean
  blinkInterval: ReturnType<typeof setInterval>
}

const 演出状態Map = new Map<string, 演出状態>()
const 描画済みID = new Set<string>()
const ストリーム既知長 = new Map<string, number>()

function カーソル色取得(role: 行種別): string {
  switch (role) {
    case 'input_text': return '#ffffff'
    case 'input_request': return '#ffaa66'
    case 'output_text': return '#00ff00'
    case 'welcome_text': return '#00ff00'
    case 'cancel_run': return '#ff5555'
    case 'stream': return '#00ff00'
    default: return '#00ff00'
  }
}

function 速度設定(len: number) {
  return { interval: 10, batch: Math.floor(len / 50) + 1 }
}

function 演出初期化(id: string, container: HTMLElement, cursorColor: string) {
  container.innerHTML = ''
  const textSpan = document.createElement('span')
  textSpan.className = 'terminal-text'
  container.appendChild(textSpan)
  const cursorSpan = document.createElement('span')
  cursorSpan.className = 'terminal-cursor'
  cursorSpan.textContent = '\u0020'
  cursorSpan.style.display = 'inline-block'
  cursorSpan.style.width = '8px'
  cursorSpan.style.backgroundColor = cursorColor
  cursorSpan.style.color = '#000'
  container.appendChild(cursorSpan)

  let blinkVisible = true
  const blinkInterval = setInterval(() => {
    cursorSpan.style.backgroundColor = blinkVisible ? 'transparent' : cursorColor
    blinkVisible = !blinkVisible
  }, 300)

  const state: 演出状態 = { container, textSpan, cursorSpan, queue: [], running: false, ready: false, finalizeOnEmpty: false, blinkInterval }
  演出状態Map.set(id, state)
  最下部スクロール()
  window.setTimeout(() => { state.ready = true; 演出実行(id) }, 500)
}

function 演出キュー追加(id: string, text: string, finalize: boolean) {
  const state = 演出状態Map.get(id)
  if (!state) return
  if (text) state.queue.push(text)
  if (finalize) state.finalizeOnEmpty = true
  演出実行(id)
}

function 演出実行(id: string) {
  const state = 演出状態Map.get(id)
  if (!state || state.running || !state.ready) return
  if (state.queue.length === 0) {
    if (state.finalizeOnEmpty) {
      state.cursorSpan.remove()
      clearInterval(state.blinkInterval)
      演出状態Map.delete(id)
      最下部スクロール()
    }
    return
  }
  state.running = true
  const chunk = state.queue.shift() ?? ''
  const { interval, batch } = 速度設定(chunk.length)
  let index = 0
  const tick = () => {
    const end = Math.min(index + batch, chunk.length)
    if (end > index) { state.textSpan.textContent += chunk.slice(index, end); index = end; nextTick(最下部スクロール) }
    if (index >= chunk.length) { state.running = false; nextTick(最下部スクロール); 演出実行(id); return }
    window.setTimeout(tick, interval)
  }
  tick()
}

function メッセージ描画開始(msg: 行データ) {
  if (描画済みID.has(msg.id)) return
  描画済みID.add(msg.id)
  if (msg.role === 'input_file' || msg.role === 'output_file') return
  nextTick(() => {
    const el = document.getElementById(msg.id)
    if (!el) return
    const bubble = el.querySelector('.bubble-content') as HTMLElement | null
    if (!bubble) return
    演出初期化(msg.id, bubble, カーソル色取得(msg.role))
    演出キュー追加(msg.id, msg.content, !msg.isStream)
  })
}

function ストリーム追記チェック(msg: 行データ) {
  if (!msg.isStream) return
  const state = 演出状態Map.get(msg.id)
  if (!state) return
  const prev = ストリーム既知長.get(msg.id) ?? 0
  if (msg.content.length > prev) {
    演出キュー追加(msg.id, msg.content.slice(prev), false)
    ストリーム既知長.set(msg.id, msg.content.length)
  }
  if (msg.isCollapsed) {
    演出キュー追加(msg.id, '', true)
    ストリーム既知長.delete(msg.id)
  }
}

// ===================== メッセージ管理 =====================

function newId() {
  return `code-${props.channel}-${Date.now()}-${messageSeq++}`
}

function pushLine(role: 行種別, content: string, extra?: Partial<行データ>) {
  メッセージ一覧.value.push({ id: newId(), role, content, ...extra })
  最下部スクロール()
}

function payloadText(message: Record<string, unknown>) {
  const v = message.メッセージ内容
  if (typeof v === 'string') return v
  if (v == null) return ''
  return JSON.stringify(v, null, 2)
}

function handleOutputStream(message: Record<string, unknown>) {
  const content = payloadText(message).trim()
  if (!content) return
  if (content === '<<< 処理開始 >>>') {
    const id = newId()
    streamMessageId = id
    ストリーム受信中.value = true
    メッセージ一覧.value.push({ id, role: 'stream', content: `${content}\n`, isStream: true, isCollapsed: false })
    最下部スクロール()
    return
  }
  if (content === '<<< 処理終了 >>>') {
    const target = メッセージ一覧.value.find((m) => m.id === streamMessageId)
    if (target) { target.content += `${content}\n`; target.isCollapsed = true }
    streamMessageId = null
    ストリーム受信中.value = false
    送信中.value = false
    最下部スクロール()
    return
  }
  const target = メッセージ一覧.value.find((m) => m.id === streamMessageId)
  if (target) { target.content += `${content}\n` }
  最下部スクロール()
}

// ===================== WebSocket =====================

function bindSocket(socket: AIWebSocket) {
  socket.onStateChange((connected) => { 出力接続済み.value = connected })
  socket.on('welcome_info', (m) => { const t = payloadText(m).trim(); if (t) pushLine('welcome_text', t) })
  socket.on('welcome_text', (m) => { const t = payloadText(m).trim(); if (t) pushLine('welcome_text', t) })
  socket.on('input_text', (m) => { const t = payloadText(m).trim(); if (t) pushLine('input_text', t) })
  socket.on('input_request', (m) => { const t = payloadText(m).trim(); if (t) pushLine('input_request', t) })
  socket.on('output_text', (m) => { const t = payloadText(m).trim(); if (t) pushLine('output_text', t); 送信中.value = false })
  socket.on('output_stream', handleOutputStream)
  socket.on('cancel_run', (m) => { const t = payloadText(m).trim(); if (t) pushLine('cancel_run', t); 送信中.value = false; ストリーム受信中.value = false })
  socket.on('input_file', (m) => { pushLine('input_file', '', { fileName: String(m.ファイル名 || ''), thumbnail: (m.サムネイル画像 as string) ?? null }) })
  socket.on('output_file', (m) => { pushLine('output_file', '', { fileName: String(m.ファイル名 || ''), thumbnail: (m.サムネイル画像 as string) ?? null }) })
  socket.on('update_info', (m) => {
    const 内容 = m.メッセージ内容
    if (内容 && typeof 内容 === 'object' && Array.isArray((内容 as Record<string, unknown>).update_files)) {
      const files = (内容 as Record<string, unknown>).update_files as string[]
      if (files.length > 0) pushLine('welcome_text', `[更新] ${files.join(', ')}`)
    }
  })
}

async function connectOutputSocket() {
  if (!props.sessionId) return
  出力WebSocket?.disconnect()
  出力WebSocket = new AIWebSocket(AI_WS_ENDPOINT, props.sessionId, props.channel)
  bindSocket(出力WebSocket)
  try { await 出力WebSocket.connect() } catch (e) {
    pushLine('cancel_run', e instanceof Error ? e.message : '接続エラー')
  }
}

// ===================== 操作 =====================

function 送信() {
  const text = 入力テキスト.value.trim()
  if (!text || !WebSocket接続中.value) return
  emit('submit', text, props.channel)
  入力テキスト.value = ''
  入力欄状態リセット()
  送信中.value = true
}

function キャンセル() {
  if (!WebSocket接続中.value) return
  emit('cancel', props.channel)
}

async function fileToBase64(file: File) {
  const buffer = await file.arrayBuffer()
  let binary = ''
  const bytes = new Uint8Array(buffer)
  bytes.forEach((b) => { binary += String.fromCharCode(b) })
  return btoa(binary)
}

async function handleFiles(files: File[]) {
  for (const file of files) {
    const base64 = await fileToBase64(file)
    emit('send-file', { channel: props.channel, fileName: file.name, base64 })
  }
}

function handleDrop(e: DragEvent) {
  e.preventDefault(); ドラッグ中.value = false
  const files = Array.from(e.dataTransfer?.files || [])
  if (files.length) void handleFiles(files)
}

function handleDragOver(e: DragEvent) { e.preventDefault(); if (WebSocket接続中.value) ドラッグ中.value = true }
function handleDragLeave(e: DragEvent) { e.preventDefault(); if (e.currentTarget === e.target) ドラッグ中.value = false }

// ===================== クリック→貼り付け =====================

const 貼り付け対象: 行種別[] = ['input_text', 'output_text', 'input_request', 'cancel_run', 'welcome_text']

function メッセージクリック(msg: 行データ) {
  if (msg.isStream && msg.isCollapsed) { msg.isCollapsed = false; return }
  if (msg.role === 'input_file' || msg.role === 'output_file') {
    if (msg.fileName) {
      const sep = 入力テキスト.value && !入力テキスト.value.endsWith('\n') ? '\n' : ''
      入力テキスト.value = `${入力テキスト.value}${sep}"${msg.fileName}"\n`
    }
    return
  }
  if (!貼り付け対象.includes(msg.role)) return
  入力テキスト.value = `${msg.content.replace(/\s+$/u, '')}\n`
  nextTick(() => { テキストエリア.value?.focus(); テキストエリア自動調整() })
}

function 折りたたみ切替(msg: 行データ) {
  if (msg.isStream) msg.isCollapsed = !msg.isCollapsed
}

function メッセージカーソル(msg: 行データ): string {
  if (msg.isStream && msg.isCollapsed) return 'pointer'
  if (msg.role === 'input_file' || msg.role === 'output_file') return 'pointer'
  return 貼り付け対象.includes(msg.role) ? 'pointer' : 'default'
}

function メッセージCSSクラス(role: 行種別): string {
  switch (role) {
    case 'input_text': return 'input_text'
    case 'input_request': return 'input_request'
    case 'output_text': return 'output_text'
    case 'welcome_text': return 'welcome_text'
    case 'cancel_run': return 'cancel_run'
    case 'input_file': return 'input_file'
    case 'output_file': return 'output_file'
    case 'stream': return 'output_text'
  }
}

// ===================== 入力欄 =====================

function 入力欄状態リセット() {
  入力欄最大到達.value = false; 入力欄固定中.value = false; 入力欄固定高さ.value = 入力欄最小高さ
  if (テキストエリア.value) テキストエリア.value.style.height = `${入力欄最小高さ}px`
}

function テキストエリア自動調整() {
  if (!テキストエリア.value) return
  const container = テキストエリア.value.closest('.agent-container') as HTMLElement | null
  if (container) 入力欄最大高さ.value = Math.max(入力欄最小高さ, Math.floor(container.clientHeight * 0.78))
  if (入力テキスト.value.length === 0) { 入力欄状態リセット(); return }
  if (入力欄固定中.value) { 入力欄最大到達.value = true; テキストエリア.value.style.height = `${入力欄固定高さ.value}px`; return }
  テキストエリア.value.style.height = `${入力欄最小高さ}px`
  const next = Math.max(テキストエリア.value.scrollHeight, 入力欄最小高さ)
  if (next >= 入力欄最大高さ.value) {
    入力欄最大到達.value = true; 入力欄固定中.value = true; 入力欄固定高さ.value = 入力欄最大高さ.value
    テキストエリア.value.style.height = `${入力欄固定高さ.value}px`; return
  }
  入力欄最大到達.value = false
  テキストエリア.value.style.height = `${next}px`
}

function 最下部スクロール() {
  nextTick(() => { if (チャット領域.value) チャット領域.value.scrollTop = チャット領域.value.scrollHeight })
}

// ===================== Watchers =====================

watch(
  () => メッセージ一覧.value,
  (msgs) => {
    for (const msg of msgs) {
      if (!描画済みID.has(msg.id)) メッセージ描画開始(msg)
      else if (msg.isStream) ストリーム追記チェック(msg)
    }
    最下部スクロール()
  },
  { deep: true, immediate: true },
)

watch(入力テキスト, () => nextTick(テキストエリア自動調整))

watch(() => props.sessionId, () => { if (props.sessionId) void connectOutputSocket() })

onMounted(() => {
  if (props.sessionId) void connectOutputSocket()
  window.addEventListener('resize', テキストエリア自動調整)
  nextTick(テキストエリア自動調整)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', テキストエリア自動調整)
  出力WebSocket?.disconnect(); 出力WebSocket = null
  for (const state of 演出状態Map.values()) clearInterval(state.blinkInterval)
  演出状態Map.clear()
})

defineExpose({
  WebSocket接続中,
  接続状態表示,
  出力接続済み,
})
</script>

<template>
  <section class="agent-container">
    <div ref="チャット領域" class="terminal-area">
      <div
        v-for="msg in メッセージ一覧"
        :key="msg.id"
        :id="msg.id"
        :class="['message', メッセージCSSクラス(msg.role), msg.isStream ? 'stream-output' : '', msg.isCollapsed ? 'collapsed' : '']"
      >
        <div
          class="message-bubble"
          @click="メッセージクリック(msg)"
          :style="{ cursor: メッセージカーソル(msg) }"
        >
          <!-- 折りたたみ表示 -->
          <div v-if="msg.isStream && msg.isCollapsed" class="collapsed-wrapper">
            <span class="collapsed-indicator">...</span>
            <span class="collapsed-arrow">&#x25C0;</span>
          </div>

          <div v-show="!(msg.isStream && msg.isCollapsed)" class="bubble-content">
            <!-- ファイルメッセージ -->
            <template v-if="msg.role === 'input_file' || msg.role === 'output_file'">
              <div class="file-message">
                <div class="file-name">
                  <span v-if="msg.role === 'input_file'">ファイル入力: </span>
                  <span v-else>ファイル出力: </span>
                  {{ msg.fileName || 'ファイル' }}
                </div>
                <img v-if="msg.thumbnail" class="file-thumbnail" :src="`data:image/png;base64,${msg.thumbnail}`" alt="" />
              </div>
            </template>
            <!-- テキスト: ターミナルエフェクトがDOMを書き込む -->
          </div>

          <span
            v-if="msg.isStream && !msg.isCollapsed"
            class="expand-indicator"
            @click.stop="折りたたみ切替(msg)"
            title="折りたたむ"
          >&#x25BC;</span>
        </div>
      </div>

      <div v-if="メッセージ一覧.length === 0" class="empty-message">コードチャンネル {{ channel }}</div>
    </div>

    <div class="control-area">
      <div class="text-input-area" :class="{ 'drag-over': ドラッグ中 }" @dragover="handleDragOver" @dragleave="handleDragLeave" @drop="handleDrop">
        <div class="input-container">
          <span class="prompt-symbol" @click="入力テキスト = ''; 入力欄状態リセット()">&gt;</span>
          <textarea
            ref="テキストエリア"
            v-model="入力テキスト"
            :class="['input-field', { 'at-limit': 入力欄最大到達 }]"
            :style="{ maxHeight: `${入力欄最大高さ}px` }"
            placeholder="メッセージを入力..."
            maxlength="5000"
            :disabled="!WebSocket接続中"
            @keydown.enter.exact.prevent="送信"
            @input="テキストエリア自動調整"
          ></textarea>
        </div>

        <button
          class="agent-send-btn"
          :class="{ 'has-text': 入力テキスト.length > 0, 'ws-disabled': !WebSocket接続中 }"
          type="button"
          :disabled="!WebSocket接続中 || !入力テキスト.trim()"
          @click="送信"
        >
          <img src="/icons/sending.png" alt="送信" />
          <span class="send-code-label">CODE</span>
        </button>

        <button
          class="agent-cancel-btn"
          :class="{ 'is-active': ストリーム受信中 }"
          type="button"
          :disabled="!ストリーム受信中 || !WebSocket接続中"
          @click="キャンセル"
        >
          <img src="/icons/abort.png" alt="停止" />
        </button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.agent-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #101010;
}

.terminal-area {
  flex: 1;
  padding: 18px;
  overflow: auto;
  background: #000;
  font-family: "Courier New", monospace;
  font-size: 11px;
}

.terminal-area::-webkit-scrollbar { width: 8px; height: 8px; }
.terminal-area::-webkit-scrollbar-track { background: #1a1a1a; }
.terminal-area::-webkit-scrollbar-thumb { background: #666; border-radius: 2px; }

.message { margin-bottom: 1px; animation: slideIn 0.3s ease; }
@keyframes slideIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

.message-bubble {
  display: inline-block;
  max-width: 95%;
  padding: 2px 8px;
  border-radius: 2px;
  word-wrap: break-word;
  line-height: 1.2;
  font-family: "Courier New", monospace;
  font-size: 11px;
  white-space: pre-wrap;
}

.message.input_text .message-bubble { color: #fff; border-left: 4px solid rgba(255, 255, 255, 0.7); }
.message.input_request .message-bubble { color: #ffaa66; border-left: 4px solid rgba(255, 170, 102, 0.7); }
.message.input_request .message-bubble::before { content: "REQ > "; font-weight: bold; color: #ffaa66; }
.message.output_text .message-bubble,
.message.welcome_text .message-bubble { color: #00ff00; border-left: 4px solid rgba(0, 255, 0, 0.7); min-width: 200px; }
.message.cancel_run .message-bubble { color: #ff7777; border-left: 4px solid rgba(255, 90, 90, 0.7); }
.message.input_file .message-bubble { color: #fff; border-left: 4px solid rgba(255, 255, 255, 0.7); display: block; }
.message.output_file .message-bubble { color: #00ff00; border-left: 4px solid rgba(0, 255, 0, 0.7); display: block; }

.message.stream-output .message-bubble {
  background: rgba(0, 255, 0, 0.08);
  border-radius: 4px;
  padding: 8px 12px;
  position: relative;
}

.message.stream-output.collapsed .message-bubble { padding: 4px 8px; }

.collapsed-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  cursor: pointer;
}

.collapsed-indicator { color: #00cc00; font-weight: bold; font-size: 16px; }
.collapsed-arrow { color: #00cc00; font-size: 14px; }

.expand-indicator {
  position: absolute;
  top: 4px;
  right: 8px;
  color: #00cc00;
  font-size: 12px;
  cursor: pointer;
  user-select: none;
}

.expand-indicator:hover { color: #00ff00; }

:deep(.terminal-text) {
  display: inline;
  white-space: pre-wrap;
  font-family: "Courier New", monospace;
  line-height: 1.1;
}

:deep(.terminal-cursor) {
  display: inline !important;
  background-color: #00ff00 !important;
  color: #000 !important;
  padding: 0 2px !important;
  font-family: "Courier New", monospace !important;
  font-weight: bold !important;
}

.file-message { display: flex; flex-direction: column; gap: 6px; }
.file-name { font-family: "Courier New", monospace; font-size: 11px; }
.message.output_file .file-name { color: #00ff00; }

.file-thumbnail {
  max-width: 240px;
  max-height: 180px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 2px;
  object-fit: contain;
  background: #111;
}

.bubble-content { margin: 0; }

.empty-message { color: #7f8a99; }

/* 入力エリア */
.control-area {
  padding: 10px 20px 0;
  background: #101010;
  border-top: 1px solid #2c2c2c;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.text-input-area {
  min-width: 0;
  display: flex;
  gap: 10px;
  align-items: flex-end;
}

.text-input-area.drag-over {
  background: rgba(102, 126, 234, 0.2);
  border: 2px dashed #667eea;
  border-radius: 4px;
  padding: 8px;
}

.input-container {
  position: relative;
  flex: 1;
  margin-bottom: 0;
}

.prompt-symbol {
  position: absolute;
  left: 8px;
  top: 16px;
  color: #fff;
  font-family: "Courier New", monospace;
  font-weight: bold;
  font-size: 16px;
  cursor: pointer;
  user-select: none;
  z-index: 1;
}

.input-field {
  width: 100%;
  padding: 10px 16px 6px 30px;
  border: 2px solid rgba(255, 255, 255, 0.5);
  border-radius: 0;
  outline: none;
  font-size: 14px;
  background: rgba(0, 0, 0, 0.35);
  color: #e0e0e0;
  resize: none;
  min-height: 60px;
  max-height: 380px;
  overflow-y: auto;
  line-height: 1.4;
  height: 60px;
}

.input-field.at-limit { font-size: 8px; line-height: 1.1; }
.input-field:disabled { border-color: #808080; color: #666; background: rgba(128, 128, 128, 0.1); }
.input-field:focus { border-color: #fff; }
.input-field::placeholder { color: #888; }

.agent-send-btn {
  border: 2px solid #667eea;
  border-radius: 2px;
  cursor: pointer;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  box-shadow: none;
  padding: 0;
  width: 56px;
  height: 48px;
  margin-bottom: 20px;
  margin-left: 10px;
  background: rgba(255, 255, 255, 0.95);
  color: white;
}

.agent-send-btn img {
  width: 34px;
  height: 34px;
  object-fit: contain;
  pointer-events: none;
  filter: brightness(0);
}

.send-code-label {
  position: absolute;
  left: 50%;
  bottom: 3px;
  transform: translateX(-50%);
  pointer-events: none;
  font-size: 9px;
  font-weight: 700;
  line-height: 1;
  letter-spacing: 0.7px;
  color: #334155;
  text-shadow: 0 1px 1px rgba(255, 255, 255, 0.6);
}

.agent-send-btn:hover:not(:disabled) {
  background: rgba(240, 240, 240, 0.95);
  border-color: #5a6fd8;
}

.agent-send-btn.has-text {
  background: #667eea;
  border-color: #667eea;
}

.agent-send-btn.has-text img { filter: brightness(0) invert(1); }

.agent-send-btn.has-text .send-code-label {
  color: #ffffff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.4);
}

.agent-send-btn.has-text:hover:not(:disabled) {
  background: #5a6fd8;
  border-color: #5a6fd8;
}

.agent-send-btn:disabled:not(.ws-disabled) {
  background: rgba(255, 255, 255, 0.95);
  border-color: #667eea;
  cursor: not-allowed;
  opacity: 1;
}

.agent-send-btn:disabled:not(.ws-disabled) img { filter: brightness(0); }

.agent-send-btn.ws-disabled {
  background: #808080 !important;
  border-color: #808080 !important;
  box-shadow: none;
  cursor: not-allowed;
  opacity: 1;
}

.agent-send-btn.ws-disabled img { filter: brightness(0) invert(1) !important; }

.agent-send-btn.ws-disabled .send-code-label {
  color: #ffffff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.35);
}

.agent-cancel-btn {
  border: 2px solid #808080;
  border-radius: 2px;
  cursor: not-allowed;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  width: 56px;
  height: 48px;
  margin-bottom: 20px;
  margin-left: 4px;
  background: rgba(128, 128, 128, 0.3);
  transition: all 0.2s ease;
}

.agent-cancel-btn img {
  width: 44px;
  height: 44px;
  object-fit: contain;
  pointer-events: none;
  filter: brightness(0) invert(1) opacity(0.6);
}

.agent-cancel-btn.is-active {
  background: #ff4444;
  border-color: #ff4444;
  cursor: pointer;
}

.agent-cancel-btn.is-active img { filter: brightness(0) invert(1); }

.agent-cancel-btn.is-active:hover {
  background: #cc0000;
  border-color: #cc0000;
}

.agent-cancel-btn:disabled { opacity: 0.6; }

@media (max-width: 480px) {
  .text-input-area {
    flex-wrap: wrap;
  }

  .agent-send-btn,
  .agent-cancel-btn {
    margin-bottom: 8px;
  }
}
</style>
