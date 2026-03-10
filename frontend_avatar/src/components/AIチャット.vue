<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { ChatMessage, MessageKind, ModelSettings } from '@/types'

type チャットモード = 'Chat' | 'Live' | 'Code1' | 'Code2' | 'Code3' | 'Code4'

const props = defineProps<{
  messages: ChatMessage[];
  welcomeInfo: string;
  sessionId: string;
  mode: チャットモード;
  inputConnected: boolean;
  chatConnected: boolean;
  modelSettings: ModelSettings;
}>()

const emit = defineEmits<{
  submit: [text: string];
  'update:mode': [mode: チャットモード];
  'drop-files': [files: File[]];
}>()

const 入力テキスト = ref('')
const チャット領域 = ref<HTMLElement | null>(null)
const テキストエリア = ref<HTMLTextAreaElement | null>(null)
const ドラッグ中 = ref(false)
const 入力欄最大到達 = ref(false)
const 入力欄固定中 = ref(false)
const 入力欄固定高さ = ref(60)

const 入力欄最小高さ = 60
const 入力欄最大高さ = ref(380)
const モード一覧: Array<{ value: チャットモード; label: string }> = [
  { value: 'Chat', label: 'Chat' },
  { value: 'Live', label: 'Live' },
  { value: 'Code1', label: 'Code1' },
  { value: 'Code2', label: 'Code2' },
  { value: 'Code3', label: 'Code3' },
  { value: 'Code4', label: 'Code4' },
]

const WebSocket接続中 = computed(() => props.inputConnected && props.chatConnected)
const 送信可能 = computed(() => WebSocket接続中.value && 入力テキスト.value.trim().length > 0)

// --- ターミナルエフェクト ---

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

function カーソル色取得(kind: MessageKind): string {
  switch (kind) {
    case 'user': return '#ffffff'
    case 'input-request': return '#ffaa66'
    case 'assistant': return '#00ff00'
    case 'output-request': return '#00ffff'
    case 'system': return '#00ff00'
    case 'recognition-user': return '#e5e7eb'
    case 'recognition-assistant': return '#9ae6b4'
    case 'stream': return '#00ff00'
    default: return '#00ff00'
  }
}

function 速度設定(文字数: number) {
  const batch = Math.floor(文字数 / 50) + 1
  return { interval: 10, batch }
}

function 演出初期化(messageId: string, container: HTMLElement, cursorColor: string) {
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
  cursorSpan.style.color = '#000000'
  container.appendChild(cursorSpan)

  let blinkVisible = true
  const blinkInterval = setInterval(() => {
    cursorSpan.style.backgroundColor = blinkVisible ? 'transparent' : cursorColor
    blinkVisible = !blinkVisible
  }, 300)

  const state: 演出状態 = {
    container,
    textSpan,
    cursorSpan,
    queue: [],
    running: false,
    ready: false,
    finalizeOnEmpty: false,
    blinkInterval,
  }
  演出状態Map.set(messageId, state)

  最下部スクロール()

  window.setTimeout(() => {
    state.ready = true
    演出実行(messageId)
  }, 500)
}

function 演出キュー追加(messageId: string, text: string, finalize: boolean) {
  const state = 演出状態Map.get(messageId)
  if (!state) return
  if (text) state.queue.push(text)
  if (finalize) state.finalizeOnEmpty = true
  演出実行(messageId)
}

function 演出実行(messageId: string) {
  const state = 演出状態Map.get(messageId)
  if (!state || state.running || !state.ready) return

  if (state.queue.length === 0) {
    if (state.finalizeOnEmpty) {
      state.cursorSpan.remove()
      clearInterval(state.blinkInterval)
      演出状態Map.delete(messageId)
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
    if (end > index) {
      state.textSpan.textContent += chunk.slice(index, end)
      index = end
      nextTick(() => 最下部スクロール())
    }
    if (index >= chunk.length) {
      state.running = false
      nextTick(() => 最下部スクロール())
      演出実行(messageId)
      return
    }
    window.setTimeout(tick, interval)
  }

  tick()
}

function メッセージ描画開始(msg: ChatMessage) {
  if (描画済みID.has(msg.id)) return
  描画済みID.add(msg.id)

  if (msg.kind === 'input-file' || msg.kind === 'output-file') return

  nextTick(() => {
    const el = document.getElementById(msg.id)
    if (!el) return
    const bubble = el.querySelector('.bubble-content') as HTMLElement | null
    if (!bubble) return

    const color = カーソル色取得(msg.kind)
    演出初期化(msg.id, bubble, color)
    演出キュー追加(msg.id, msg.text, !msg.isStream)
  })
}

// ストリーム追記を検出（メッセージIDごとに前回テキスト長を記録）
const ストリーム既知長 = new Map<string, number>()

function ストリーム追記チェック(msg: ChatMessage) {
  if (!msg.isStream) return
  const state = 演出状態Map.get(msg.id)
  if (!state) return

  const prev = ストリーム既知長.get(msg.id) ?? 0
  if (msg.text.length > prev) {
    const newText = msg.text.slice(prev)
    演出キュー追加(msg.id, newText, false)
    ストリーム既知長.set(msg.id, msg.text.length)
  }

  if (msg.isCollapsed) {
    演出キュー追加(msg.id, '', true)
    ストリーム既知長.delete(msg.id)
  }
}

// --- メッセージ種別CSS ---

function メッセージCSSクラス(kind: MessageKind): string {
  switch (kind) {
    case 'user': return 'input_text'
    case 'assistant': return 'output_text'
    case 'system': return 'welcome_text'
    case 'recognition-user': return 'recognition_input'
    case 'recognition-assistant': return 'recognition_output'
    case 'input-request': return 'input_request'
    case 'output-request': return 'output_request'
    case 'input-file': return 'input_file'
    case 'output-file': return 'output_file'
    case 'stream': return 'output_text'
    default: return 'welcome_text'
  }
}

// --- クリック→貼り付け ---

const 貼り付け対象: MessageKind[] = [
  'user', 'assistant', 'input-request', 'output-request',
  'input-file', 'output-file', 'recognition-user', 'recognition-assistant',
]

function 折りたたみ切替(msg: ChatMessage) {
  if (msg.isStream) {
    msg.isCollapsed = !msg.isCollapsed
  }
}

function メッセージクリック(msg: ChatMessage) {
  if (msg.isStream) {
    if (msg.isCollapsed) 折りたたみ切替(msg)
    return
  }

  if (!貼り付け対象.includes(msg.kind)) return

  let pasteText = ''
  if (msg.kind === 'input-file' || msg.kind === 'output-file') {
    pasteText = msg.fileName ? `"${msg.fileName}"` : ''
  } else {
    pasteText = msg.text.replace(/\s+$/u, '')
  }
  if (!pasteText) return

  const isFile = msg.kind === 'input-file' || msg.kind === 'output-file'
  if (isFile) {
    const sep = 入力テキスト.value && !入力テキスト.value.endsWith('\n') ? '\n' : ''
    入力テキスト.value = `${入力テキスト.value}${sep}${pasteText}\n`
  } else {
    入力テキスト.value = `${pasteText}\n`
  }

  nextTick(() => {
    if (!テキストエリア.value) return
    テキストエリア.value.focus()
    テキストエリア自動調整()
    const len = テキストエリア.value.value.length
    テキストエリア.value.setSelectionRange(len, len)
  })
}

function メッセージカーソル(msg: ChatMessage): string {
  if (msg.isStream && msg.isCollapsed) return 'pointer'
  return 貼り付け対象.includes(msg.kind) ? 'pointer' : 'default'
}

// --- 入力欄 ---

function テキストエリア自動調整() {
  if (!テキストエリア.value) return

  const コンテナ = テキストエリア.value.closest('.chat-container') as HTMLElement | null
  if (コンテナ) {
    const 候補高さ = Math.floor(コンテナ.clientHeight * 0.78)
    入力欄最大高さ.value = Math.max(入力欄最小高さ, 候補高さ)
  }

  if (入力テキスト.value.length === 0) {
    入力欄状態リセット()
    return
  }

  if (入力欄固定中.value) {
    入力欄最大到達.value = true
    テキストエリア.value.style.height = `${入力欄固定高さ.value}px`
    return
  }

  テキストエリア.value.style.height = `${入力欄最小高さ}px`
  const scrollH = テキストエリア.value.scrollHeight
  const next = Math.max(scrollH, 入力欄最小高さ)
  const atLimit = next >= 入力欄最大高さ.value
  入力欄最大到達.value = atLimit
  if (atLimit) {
    入力欄固定中.value = true
    入力欄固定高さ.value = 入力欄最大高さ.value
    テキストエリア.value.style.height = `${入力欄固定高さ.value}px`
    return
  }
  テキストエリア.value.style.height = `${next}px`
}

function 入力欄状態リセット() {
  入力欄最大到達.value = false
  入力欄固定中.value = false
  入力欄固定高さ.value = 入力欄最小高さ
  if (テキストエリア.value) {
    テキストエリア.value.style.height = `${入力欄最小高さ}px`
  }
}

function 入力欄クリア() {
  入力テキスト.value = ''
  入力欄状態リセット()
  nextTick(() => {
    テキストエリア.value?.focus()
    テキストエリア自動調整()
  })
}

function submit() {
  const text = 入力テキスト.value.trim()
  if (!text || !WebSocket接続中.value) return
  emit('submit', text)
  入力欄クリア()
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    submit()
  }
}

// --- D&D ---

function ドラッグオーバー処理(event: DragEvent) {
  event.preventDefault()
  if (!WebSocket接続中.value) return
  ドラッグ中.value = true
}

function ドラッグ離脱処理(event: DragEvent) {
  event.preventDefault()
  if (event.currentTarget === event.target) ドラッグ中.value = false
}

function ドロップ処理(event: DragEvent) {
  event.preventDefault()
  ドラッグ中.value = false
  if (!WebSocket接続中.value) return
  const files = Array.from(event.dataTransfer?.files || [])
  if (files.length === 0) return
  emit('drop-files', files)
}

// --- スクロール ---

function 最下部スクロール() {
  nextTick(() => {
    if (チャット領域.value) {
      チャット領域.value.scrollTop = チャット領域.value.scrollHeight
    }
  })
}

// --- メッセージ監視 ---

watch(
  () => props.messages,
  (msgs) => {
    for (const msg of msgs) {
      if (!描画済みID.has(msg.id)) {
        メッセージ描画開始(msg)
      } else if (msg.isStream) {
        ストリーム追記チェック(msg)
      }
    }
    最下部スクロール()
  },
  { deep: true, immediate: true },
)

watch(入力テキスト, () => nextTick(テキストエリア自動調整))

onMounted(() => {
  window.addEventListener('resize', テキストエリア自動調整)
  nextTick(テキストエリア自動調整)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', テキストエリア自動調整)
  for (const state of 演出状態Map.values()) {
    clearInterval(state.blinkInterval)
  }
  演出状態Map.clear()
})
</script>

<template>
  <section class="chat-container" data-interactive="true">
    <div ref="チャット領域" class="chat-area">
      <div v-if="welcomeInfo" class="welcome-message">
        {{ welcomeInfo }}
      </div>

      <div
        v-for="msg in messages"
        :key="msg.id"
        :id="msg.id"
        :class="[
          'message',
          メッセージCSSクラス(msg.kind),
          msg.kind === 'input-file' || msg.kind === 'output-file' ? 'is-file' : '',
          msg.isStream ? 'stream-output' : '',
          msg.isCollapsed ? 'collapsed' : '',
        ]"
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
            <template v-if="msg.kind === 'input-file' || msg.kind === 'output-file'">
              <div class="file-message">
                <div class="file-name">
                  <span v-if="msg.kind === 'input-file'">ファイル入力: </span>
                  <span v-if="msg.kind === 'output-file'">ファイル出力: </span>
                  {{ msg.fileName || 'ファイル受信' }}
                </div>
                <img
                  v-if="msg.thumbnail"
                  class="file-thumbnail"
                  :src="`data:image/png;base64,${msg.thumbnail}`"
                  alt="thumbnail"
                />
              </div>
            </template>
            <!-- テキストメッセージ: ターミナルエフェクトが直接DOMを書き込む -->
          </div>

          <span
            v-if="msg.isStream && !msg.isCollapsed"
            class="expand-indicator"
            @click.stop="折りたたみ切替(msg)"
            title="折りたたむ"
          >&#x25BC;</span>
        </div>
      </div>

      <div v-if="messages.length === 0" class="empty-message">
        <p>セッション: {{ sessionId || '未接続' }}</p>
      </div>
    </div>

    <div class="control-area">
      <div
        class="text-input-area"
        :class="{ 'drag-over': ドラッグ中 }"
        @dragover="ドラッグオーバー処理"
        @dragleave="ドラッグ離脱処理"
        @drop="ドロップ処理"
      >
        <div class="input-container">
          <span class="prompt-symbol" @click="入力欄クリア">&gt;</span>
          <textarea
            ref="テキストエリア"
            v-model="入力テキスト"
            :class="['input-field', { 'at-limit': 入力欄最大到達 }]"
            :style="{ maxHeight: `${入力欄最大高さ}px` }"
            placeholder="メッセージを入力..."
            maxlength="5000"
            :disabled="!WebSocket接続中"
            @keydown="handleKeydown"
            @input="テキストエリア自動調整"
          ></textarea>
        </div>
      </div>

      <div class="mode-panel">
        <div class="mode-selector">
          <label v-for="option in モード一覧.slice(0, 3)" :key="option.value" class="mode-option">
            <input
              type="radio"
              :checked="mode === option.value"
              name="avatar-chat-mode"
              @change="emit('update:mode', option.value)"
            />
            <span>{{ option.label }}</span>
          </label>
        </div>
        <div class="code-selector">
          <label v-for="option in モード一覧.slice(3)" :key="option.value" class="mode-option">
            <input
              type="radio"
              :checked="mode === option.value"
              name="avatar-chat-mode"
              @change="emit('update:mode', option.value)"
            />
            <span>{{ option.label }}</span>
          </label>
        </div>
      </div>

      <button
        class="chat-send-btn"
        :class="{
          'ws-disabled': !WebSocket接続中,
          'has-text': 入力テキスト.length > 0,
        }"
        type="button"
        :disabled="!送信可能"
        title="送信"
        @click="submit"
      >
        <img src="/icons/sending.png" alt="送信" />
      </button>
    </div>
  </section>
</template>

<style scoped>
.chat-container {
  background: #ffffff;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  width: 100%;
  height: 100%;
}

.chat-area {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  overflow-x: auto;
  background: #000000;
  position: relative;
}

.chat-area::-webkit-scrollbar { width: 8px; height: 8px; }
.chat-area::-webkit-scrollbar-track { background: #1a1a1a; }
.chat-area::-webkit-scrollbar-thumb { background: #666666; border-radius: 2px; }
.chat-area::-webkit-scrollbar-thumb:hover { background: #888888; }

.welcome-message {
  background: rgba(102, 126, 234, 0.08);
  color: #b8c5f2;
  padding: 12px 16px;
  border-radius: 2px;
  margin: 8px auto;
  border: 1px solid rgba(102, 126, 234, 0.3);
  border-left: 4px solid rgba(102, 126, 234, 0.6);
  text-align: center;
  max-width: 85%;
  font-family: "Courier New", monospace;
  font-size: 11px;
  white-space: pre-line;
}

.message {
  margin-bottom: 1px;
  animation: slideIn 0.3s ease;
  text-align: left;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

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

.message.input_text .message-bubble { color: #ffffff; border-left: 4px solid rgba(255, 255, 255, 0.7); }
.message.input_file .message-bubble { color: #ffffff; border-left: 4px solid rgba(255, 255, 255, 0.7); }
.message.input_request .message-bubble { color: #ffaa66; border-left: 4px solid rgba(255, 170, 102, 0.7); }
.message.input_request .message-bubble::before { content: "REQ > "; font-weight: bold; color: #ffaa66; }
.message.recognition_input .message-bubble { color: #e5e7eb; border-left: 4px solid rgba(187, 187, 187, 0.7); }
.message.output_text .message-bubble,
.message.welcome_text .message-bubble { color: #00ff00; border-left: 4px solid rgba(0, 255, 0, 0.7); min-width: 200px; }
.message.output_request .message-bubble { color: #00ffff; border-left: 4px solid rgba(0, 255, 255, 0.7); min-width: 200px; }
.message.output_file .message-bubble { color: #00ff00; border-left: 4px solid rgba(0, 255, 0, 0.7); }
.message.recognition_output .message-bubble { color: #9ae6b4; border-left: 4px solid rgba(0, 153, 204, 0.7); }

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
  color: #000000 !important;
  padding: 0 2px !important;
  font-family: "Courier New", monospace !important;
  font-weight: bold !important;
}

.file-message {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.message.is-file .message-bubble { display: block; }
.message.output_file.is-file .message-bubble { min-width: 0; }

.file-name {
  font-family: "Courier New", monospace;
  font-size: 11px;
  color: #ffffff;
}

.message.output_file .file-name { color: #00ff00; }

.file-thumbnail {
  max-width: 240px;
  max-height: 180px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 2px;
  object-fit: contain;
  background: #111;
}

.bubble-content,
.empty-message p { margin: 0; }

.empty-message {
  margin-top: auto;
  color: #8f9aa9;
  font-family: "Courier New", monospace;
  font-size: 12px;
}

.control-area {
  padding: 10px 20px 0 20px;
  background: #101010;
  border-top: 1px solid #2c2c2c;
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
  gap: 10px;
  align-items: flex-end;
}

.text-input-area {
  display: flex;
  gap: 10px;
  align-items: flex-end;
  flex: 1;
}

.text-input-area.drag-over {
  background-color: rgba(102, 126, 234, 0.2);
  border: 2px dashed #667eea;
  border-radius: 4px;
  padding: 6px;
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
  color: #ffffff;
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
.input-field:focus { border-color: #ffffff; }
.input-field::placeholder { color: #888; }

.mode-panel {
  display: flex;
  flex-direction: row;
  gap: 8px;
  padding-bottom: 16px;
  justify-content: center;
  margin-top: -4px;
  flex-shrink: 0;
}

.mode-selector,
.code-selector {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.mode-option {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #e0e0e0;
  font-size: 12px;
  cursor: pointer;
  user-select: none;
  line-height: 1.1;
  padding: 0;
}

.mode-option input[type="radio"] {
  width: 13px;
  height: 13px;
  cursor: pointer;
  accent-color: #667eea;
  margin: 0;
  position: relative;
  top: -8px;
}

.mode-option span {
  font-family: "Courier New", monospace;
  position: relative;
  top: -4px;
}

.chat-send-btn {
  border: 2px solid #667eea;
  border-radius: 2px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  padding: 0;
  width: 56px;
  height: 48px;
  margin-bottom: 20px;
  background: rgba(255, 255, 255, 0.95);
  flex-shrink: 0;
}

.chat-send-btn img {
  width: 34px;
  height: 34px;
  object-fit: contain;
  pointer-events: none;
  filter: brightness(0);
}

.chat-send-btn:hover:not(:disabled) { background: rgba(240, 240, 240, 0.95); border-color: #5a6fd8; }
.chat-send-btn.has-text { background: #667eea; border-color: #667eea; }
.chat-send-btn.has-text img { filter: brightness(0) invert(1); }
.chat-send-btn.has-text:hover:not(:disabled) { background: #5a6fd8; border-color: #5a6fd8; }
.chat-send-btn:disabled:not(.ws-disabled) { background: rgba(255, 255, 255, 0.95); border-color: #667eea; cursor: not-allowed; opacity: 1; }
.chat-send-btn:disabled:not(.ws-disabled) img { filter: brightness(0); }
.chat-send-btn.ws-disabled { background: #808080 !important; border-color: #808080 !important; cursor: not-allowed; opacity: 1; }
.chat-send-btn.ws-disabled img { filter: brightness(0) invert(1) !important; }

@media (max-width: 480px) {
  .control-area { flex-direction: column; align-items: stretch; padding-bottom: 12px; }
  .mode-panel { padding-bottom: 0; }
  .chat-send-btn { width: 100%; margin-bottom: 0; }
}
</style>
