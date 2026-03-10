<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import type { ChatMessage, ModelSettings } from '@/types'

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
const 接続状態表示 = computed(() => (WebSocket接続中.value ? '接続中' : '切断'))
const 送信可能 = computed(() => WebSocket接続中.value && 入力テキスト.value.trim().length > 0)
const モデル情報表示 = computed(() => {
  const 候補 = [
    props.modelSettings.CHAT_AI_NAME,
    props.modelSettings.LIVE_AI_NAME,
    props.modelSettings.CODE_AI1_NAME,
    props.modelSettings.CODE_AI2_NAME,
    props.modelSettings.CODE_AI3_NAME,
    props.modelSettings.CODE_AI4_NAME,
  ].filter(Boolean)
  return 候補.join(', ')
})

function メッセージ種別クラス(kind: ChatMessage['kind']) {
  switch (kind) {
    case 'user':
      return 'input_text'
    case 'assistant':
      return 'output_text'
    case 'recognition-user':
      return 'recognition_input'
    case 'recognition-assistant':
      return 'recognition_output'
    default:
      return 'welcome_text'
  }
}

function 入力欄高さ更新() {
  if (!テキストエリア.value) return
  const コンテナ = テキストエリア.value.closest('.chat-container') as HTMLElement | null
  if (!コンテナ) return

  const 候補高さ = Math.floor(コンテナ.clientHeight * 0.78)
  入力欄最大高さ.value = Math.max(入力欄最小高さ, 候補高さ)
  テキストエリア.value.style.height = `${入力欄最小高さ}px`

  if (入力テキスト.value.length === 0) {
    入力欄最大到達.value = false
    return
  }

  const 次の高さ = Math.max(テキストエリア.value.scrollHeight, 入力欄最小高さ)
  入力欄最大到達.value = 次の高さ >= 入力欄最大高さ.value
  テキストエリア.value.style.height = `${Math.min(次の高さ, 入力欄最大高さ.value)}px`
}

function 入力欄クリア() {
  入力テキスト.value = ''
  nextTick(() => {
    if (!テキストエリア.value) return
    テキストエリア.value.focus()
    入力欄高さ更新()
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

function ドラッグオーバー処理(event: DragEvent) {
  event.preventDefault()
  if (!WebSocket接続中.value) return
  ドラッグ中.value = true
}

function ドラッグ離脱処理(event: DragEvent) {
  event.preventDefault()
  if (event.currentTarget === event.target) {
    ドラッグ中.value = false
  }
}

function ドロップ処理(event: DragEvent) {
  event.preventDefault()
  ドラッグ中.value = false
  if (!WebSocket接続中.value) return
  const files = Array.from(event.dataTransfer?.files || [])
  if (files.length === 0) return
  emit('drop-files', files)
}

watch(
  () => props.messages.length,
  async () => {
    await nextTick()
    if (チャット領域.value) {
      チャット領域.value.scrollTop = チャット領域.value.scrollHeight
    }
  },
)

watch(
  () => 入力テキスト.value,
  async () => {
    await nextTick()
    入力欄高さ更新()
  },
)
</script>

<template>
  <section class="chat-container" data-interactive="true">
    <div class="header">
      <h1>
        AiDiy AI
        <span v-if="モデル情報表示" class="model-info">({{ モデル情報表示 }})</span>
      </h1>
      <div class="status">
        <span :class="['status-dot', WebSocket接続中 ? 'connecting' : 'disconnected']"></span>
        <span>{{ 接続状態表示 }}</span>
      </div>
    </div>

    <div ref="チャット領域" class="chat-area">
      <div v-if="welcomeInfo" class="welcome-message">
        {{ welcomeInfo }}
      </div>

      <div
        v-for="メッセージ項目 in messages"
        :key="メッセージ項目.id"
        :class="['message', メッセージ種別クラス(メッセージ項目.kind)]"
      >
        <div class="message-bubble">
          <div class="bubble-content">{{ メッセージ項目.text }}</div>
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
  font-size: 22px;
  font-weight: bold;
  margin: 0;
  line-height: 1.2;
}

.model-info {
  font-size: 14px;
  font-weight: normal;
  color: #666;
  margin-left: 8px;
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

.status-dot.disconnected {
  background: #888888;
}

.status-dot.connecting {
  background: #44ff44;
}

.chat-area {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  overflow-x: auto;
  background: #000000;
  position: relative;
}

.chat-area::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.chat-area::-webkit-scrollbar-track {
  background: #1a1a1a;
}

.chat-area::-webkit-scrollbar-thumb {
  background: #666666;
  border-radius: 2px;
}

.chat-area::-webkit-scrollbar-thumb:hover {
  background: #888888;
}

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
  text-align: left;
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

.message.input_text .message-bubble {
  color: #ffffff;
  border-left: 4px solid rgba(255, 255, 255, 0.7);
}

.message.output_text .message-bubble,
.message.welcome_text .message-bubble {
  color: #00ff00;
  border-left: 4px solid rgba(0, 255, 0, 0.7);
  min-width: 200px;
}

.message.recognition_input .message-bubble {
  color: #e5e7eb;
  border-left: 4px solid rgba(187, 187, 187, 0.7);
}

.message.recognition_output .message-bubble {
  color: #9ae6b4;
  border-left: 4px solid rgba(0, 153, 204, 0.7);
}

.bubble-content,
.empty-message p {
  margin: 0;
}

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

.input-field.at-limit {
  font-size: 8px;
  line-height: 1.1;
}

.input-field:disabled {
  border-color: #808080;
  color: #666;
  background: rgba(128, 128, 128, 0.1);
}

.input-field:focus {
  border-color: #ffffff;
}

.input-field::placeholder {
  color: #888;
}

.mode-panel {
  display: flex;
  flex-direction: row;
  gap: 8px;
  padding-bottom: 16px;
  justify-content: center;
  margin-top: -4px;
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

.chat-send-btn:hover:not(:disabled) {
  background: rgba(240, 240, 240, 0.95);
  border-color: #5a6fd8;
}

.chat-send-btn.has-text {
  background: #667eea;
  border-color: #667eea;
}

.chat-send-btn.has-text img {
  filter: brightness(0) invert(1);
}

.chat-send-btn.has-text:hover:not(:disabled) {
  background: #5a6fd8;
  border-color: #5a6fd8;
}

.chat-send-btn:disabled:not(.ws-disabled) {
  background: rgba(255, 255, 255, 0.95);
  border-color: #667eea;
  cursor: not-allowed;
  opacity: 1;
}

.chat-send-btn:disabled:not(.ws-disabled) img {
  filter: brightness(0);
}

.chat-send-btn.ws-disabled {
  background: #808080 !important;
  border-color: #808080 !important;
  cursor: not-allowed;
  opacity: 1;
}

.chat-send-btn.ws-disabled img {
  filter: brightness(0) invert(1) !important;
}

@media (max-width: 820px) {
  .header h1 {
    font-size: 16px;
  }

  .model-info {
    display: none;
  }

  .control-area {
    flex-direction: column;
    align-items: stretch;
    padding-bottom: 12px;
  }

  .mode-panel {
    padding-bottom: 0;
  }

  .chat-send-btn {
    width: 100%;
    margin-bottom: 0;
  }
}
</style>
