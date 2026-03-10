<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { AI_WS_ENDPOINT } from '@/lib/config'
import { AIWebSocket } from '@/lib/websocket'

type コードチャンネル = '1' | '2' | '3' | '4'
type 行種別 = 'input_text' | 'output_text' | 'welcome_text' | 'input_file' | 'output_file' | 'cancel_run'
type 行データ = {
  id: string
  role: 行種別
  content: string
  fileName?: string
}

const props = defineProps<{
  sessionId: string;
  channel: コードチャンネル;
  codeAi: string;
  inputConnected: boolean;
}>()

const emit = defineEmits<{
  submit: [text: string, channel: コードチャンネル];
  cancel: [channel: コードチャンネル];
  'send-file': [payload: { channel: コードチャンネル; fileName: string; base64: string }];
}>()

const 出力接続済み = ref(false)
const メッセージ一覧 = ref<行データ[]>([])
const 入力テキスト = ref('')
const 送信中 = ref(false)
const ストリーム受信中 = ref(false)
const ドラッグ中 = ref(false)
const チャット領域 = ref<HTMLElement | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const 入力欄最大到達 = ref(false)
const テキストエリア = ref<HTMLTextAreaElement | null>(null)

let 出力WebSocket: AIWebSocket | null = null
let messageSeq = 0

const WebSocket接続中 = computed(() => props.inputConnected && 出力接続済み.value)
const 接続状態表示 = computed(() => (WebSocket接続中.value ? '接続中' : '切断'))

function pushLine(role: 行種別, content: string, fileName = '') {
  メッセージ一覧.value.push({
    id: `code-${props.channel}-${Date.now()}-${messageSeq++}`,
    role,
    content,
    fileName,
  })
  requestAnimationFrame(() => {
    if (チャット領域.value) {
      チャット領域.value.scrollTop = チャット領域.value.scrollHeight
    }
  })
}

function payloadText(message: Record<string, unknown>) {
  const value = message.メッセージ内容
  if (typeof value === 'string') return value
  if (value == null) return ''
  return JSON.stringify(value, null, 2)
}

function bindSocket(socket: AIWebSocket) {
  socket.onStateChange((connected) => {
    出力接続済み.value = connected
  })
  socket.on('welcome_info', (message) => {
    const text = payloadText(message).trim()
    if (text) pushLine('welcome_text', text)
  })
  socket.on('welcome_text', (message) => {
    const text = payloadText(message).trim()
    if (text) pushLine('welcome_text', text)
  })
  socket.on('input_text', (message) => {
    const text = payloadText(message).trim()
    if (text) pushLine('input_text', `> ${text}`)
  })
  socket.on('output_text', (message) => {
    const text = payloadText(message).trim()
    if (text) pushLine('output_text', text)
    送信中.value = false
  })
  socket.on('output_stream', (message) => {
    const text = payloadText(message).trim()
    if (text) pushLine('output_text', text)
    ストリーム受信中.value = !text.includes('<<< 処理終了 >>>')
  })
  socket.on('cancel_run', (message) => {
    const text = payloadText(message).trim()
    if (text) pushLine('cancel_run', text)
    送信中.value = false
    ストリーム受信中.value = false
  })
  socket.on('input_file', (message) => {
    pushLine('input_file', 'ファイル入力', String(message.ファイル名 || ''))
  })
  socket.on('output_file', (message) => {
    pushLine('output_file', 'ファイル出力', String(message.ファイル名 || ''))
  })
}

async function connectOutputSocket() {
  if (!props.sessionId) return
  出力WebSocket?.disconnect()
  出力WebSocket = new AIWebSocket(AI_WS_ENDPOINT, props.sessionId, props.channel)
  bindSocket(出力WebSocket)
  try {
    await 出力WebSocket.connect()
  } catch (error) {
    pushLine('cancel_run', error instanceof Error ? error.message : '接続エラー')
  }
}

async function fileToBase64(file: File) {
  const buffer = await file.arrayBuffer()
  let binary = ''
  const bytes = new Uint8Array(buffer)
  bytes.forEach((byte) => {
    binary += String.fromCharCode(byte)
  })
  return btoa(binary)
}

function 送信() {
  const text = 入力テキスト.value.trim()
  if (!text || !WebSocket接続中.value) return
  emit('submit', text, props.channel)
  pushLine('input_text', `> ${text}`)
  入力テキスト.value = ''
  送信中.value = true
}

function キャンセル() {
  if (!WebSocket接続中.value) return
  emit('cancel', props.channel)
}

async function handleFiles(files: File[]) {
  for (const file of files) {
    const base64 = await fileToBase64(file)
    emit('send-file', { channel: props.channel, fileName: file.name, base64 })
    pushLine('input_file', 'ファイル入力', file.name)
  }
}

function handleDrop(event: DragEvent) {
  event.preventDefault()
  ドラッグ中.value = false
  const files = Array.from(event.dataTransfer?.files || [])
  if (files.length === 0) return
  void handleFiles(files)
}

function handleDragOver(event: DragEvent) {
  event.preventDefault()
  ドラッグ中.value = true
}

function handleDragLeave(event: DragEvent) {
  event.preventDefault()
  if (event.currentTarget === event.target) {
    ドラッグ中.value = false
  }
}

function openFilePicker() {
  fileInput.value?.click()
}

function onFileChange(event: Event) {
  const files = Array.from((event.target as HTMLInputElement).files || [])
  if (files.length === 0) return
  void handleFiles(files)
  ;(event.target as HTMLInputElement).value = ''
}

function adjustTextarea() {
  if (!テキストエリア.value) return
  テキストエリア.value.style.height = '60px'
  const nextHeight = Math.min(220, Math.max(60, テキストエリア.value.scrollHeight))
  入力欄最大到達.value = nextHeight >= 220
  テキストエリア.value.style.height = `${nextHeight}px`
}

watch(() => props.sessionId, () => {
  if (props.sessionId) {
    void connectOutputSocket()
  }
})

watch(() => 入力テキスト.value, () => {
  requestAnimationFrame(adjustTextarea)
})

onMounted(() => {
  if (props.sessionId) {
    void connectOutputSocket()
  }
})

onBeforeUnmount(() => {
  出力WebSocket?.disconnect()
  出力WebSocket = null
})
</script>

<template>
  <section class="agent-container" @dragover="handleDragOver" @dragleave="handleDragLeave" @drop="handleDrop">
    <div class="header">
      <h1>AiDiy Code {{ channel }}<span v-if="codeAi" class="model-info">({{ codeAi }})</span></h1>
      <div class="status">
        <span :class="['status-dot', WebSocket接続中 ? 'connecting' : 'disconnected']"></span>
        <span>{{ 接続状態表示 }}</span>
      </div>
    </div>

    <div ref="チャット領域" class="terminal-area" :class="{ dragging: ドラッグ中 }">
      <div v-for="line in メッセージ一覧" :key="line.id" :class="['terminal-line', line.role]">
        <div v-if="line.role === 'input_file' || line.role === 'output_file'" class="file-message">
          <span>{{ line.role === 'input_file' ? 'ファイル入力: ' : 'ファイル出力: ' }}</span>{{ line.fileName }}
        </div>
        <div v-else class="line-content">{{ line.content }}</div>
      </div>
      <div v-if="メッセージ一覧.length === 0" class="empty-message">コードチャンネル {{ channel }}</div>
    </div>

    <div class="control-area">
      <div class="text-input-area">
        <div class="input-container">
          <span class="prompt-symbol" @click="入力テキスト = ''">&gt;</span>
          <textarea
            ref="テキストエリア"
            v-model="入力テキスト"
            :class="['input-field', { 'at-limit': 入力欄最大到達 }]"
            placeholder="コード指示を入力..."
            :disabled="!WebSocket接続中"
            @keydown.enter.exact.prevent="送信"
          ></textarea>
        </div>
      </div>

      <div class="button-stack">
        <button class="sub-button" type="button" :disabled="!WebSocket接続中" @click="openFilePicker">FILE</button>
        <button class="sub-button danger" type="button" :disabled="!ストリーム受信中" @click="キャンセル">STOP</button>
      </div>

      <button
        class="send-button"
        :class="{ 'has-text': 入力テキスト.length > 0, 'ws-disabled': !WebSocket接続中 }"
        type="button"
        :disabled="!WebSocket接続中 || !入力テキスト.trim()"
        @click="送信"
      >
        <img src="/icons/sending.png" alt="送信" />
        <span>CODE</span>
      </button>
    </div>

    <input ref="fileInput" type="file" hidden @change="onFileChange" />
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

.header {
  background: #c8c8c8;
  color: #333;
  padding: 5px 20px;
  text-align: center;
  position: relative;
  min-height: 35px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.header h1 {
  margin: 0;
  font-size: 22px;
  line-height: 1.2;
}

.model-info {
  margin-left: 8px;
  font-size: 14px;
  color: #666;
  font-weight: normal;
}

.status {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: bold;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.status-dot.disconnected { background: #888; }
.status-dot.connecting { background: #44ff44; }

.terminal-area {
  flex: 1;
  padding: 18px;
  overflow: auto;
  background: #000;
  font-family: "Courier New", monospace;
  font-size: 11px;
}

.terminal-area.dragging {
  outline: 2px dashed #667eea;
  outline-offset: -8px;
}

.terminal-line {
  margin-bottom: 2px;
}

.line-content,
.file-message {
  display: inline-block;
  max-width: 95%;
  padding: 2px 8px;
  border-left: 4px solid rgba(255, 255, 255, 0.3);
  white-space: pre-wrap;
}

.terminal-line.input_text .line-content { color: #fff; border-left-color: rgba(255, 255, 255, 0.7); }
.terminal-line.output_text .line-content,
.terminal-line.welcome_text .line-content { color: #00ff00; border-left-color: rgba(0, 255, 0, 0.7); }
.terminal-line.cancel_run .line-content { color: #ff7777; border-left-color: rgba(255, 90, 90, 0.7); }
.terminal-line.input_file .file-message { color: #fff; border-left-color: rgba(255, 255, 255, 0.7); }
.terminal-line.output_file .file-message { color: #00ff00; border-left-color: rgba(0, 255, 0, 0.7); }

.empty-message {
  color: #7f8a99;
}

.control-area {
  padding: 10px 20px 12px;
  background: #101010;
  border-top: 1px solid #2c2c2c;
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 10px;
  align-items: end;
}

.input-container {
  position: relative;
}

.prompt-symbol {
  position: absolute;
  left: 8px;
  top: 16px;
  color: #ffffff;
  font-weight: bold;
  font-size: 16px;
  cursor: pointer;
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
  max-height: 220px;
  overflow-y: auto;
  line-height: 1.4;
  height: 60px;
}

.input-field.at-limit {
  font-size: 10px;
}

.button-stack {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sub-button,
.send-button {
  border: 2px solid #667eea;
  background: rgba(255, 255, 255, 0.95);
  color: #000;
  cursor: pointer;
}

.sub-button {
  width: 64px;
  height: 32px;
  font-family: "Courier New", monospace;
  font-size: 12px;
  font-weight: bold;
}

.sub-button.danger {
  border-color: #cc4444;
}

.send-button {
  width: 72px;
  height: 56px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  font-family: "Courier New", monospace;
  font-size: 11px;
  font-weight: bold;
}

.send-button img {
  width: 22px;
  height: 22px;
  filter: brightness(0);
}

.send-button.has-text {
  background: #667eea;
  color: #fff;
}

.send-button.has-text img,
.send-button.ws-disabled img {
  filter: brightness(0) invert(1);
}

.send-button.ws-disabled,
.sub-button:disabled,
.send-button:disabled {
  background: #808080;
  border-color: #808080;
  color: #fff;
  cursor: not-allowed;
}

@media (max-width: 820px) {
  .control-area {
    grid-template-columns: 1fr;
  }

  .button-stack {
    flex-direction: row;
  }

  .send-button,
  .sub-button {
    width: 100%;
  }
}
</style>
