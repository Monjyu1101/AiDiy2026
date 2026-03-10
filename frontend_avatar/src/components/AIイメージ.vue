<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'

const props = defineProps<{
  sessionId: string;
  inputConnected: boolean;
}>()

const emit = defineEmits<{
  'submit-image': [payload: { text: string; mimeType: string; base64: string }];
}>()

const 選択画像URL = ref('')
const 選択画像Base64 = ref('')
const 選択画像MIME = ref('image/png')
const 入力テキスト = ref('')
const ファイル入力 = ref<HTMLInputElement | null>(null)
const 動画要素 = ref<HTMLVideoElement | null>(null)
const カメラ起動中 = ref(false)
const 送信中 = ref(false)
let stream: MediaStream | null = null

const 接続状態 = computed(() => (props.inputConnected ? 'connecting' : 'disconnected'))
const 状態表示テキスト = computed(() => (props.inputConnected ? '接続中' : '切断'))
const 送信可能 = computed(() => props.inputConnected && Boolean(選択画像Base64.value))

async function openPicker() {
  ファイル入力.value?.click()
}

async function onFileChange(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  await loadFile(file)
  ;(event.target as HTMLInputElement).value = ''
}

async function loadFile(file: File) {
  const dataUrl = await fileToDataUrl(file)
  選択画像URL.value = dataUrl
  選択画像Base64.value = dataUrl.split(',')[1] || ''
  選択画像MIME.value = file.type || 'image/png'
}

function fileToDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(reader.error)
    reader.readAsDataURL(file)
  })
}

async function startCamera() {
  if (stream) return
  stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false })
  カメラ起動中.value = true
  if (動画要素.value) {
    動画要素.value.srcObject = stream
    await 動画要素.value.play()
  }
}

function stopCamera() {
  stream?.getTracks().forEach((track) => track.stop())
  stream = null
  カメラ起動中.value = false
  if (動画要素.value) {
    動画要素.value.pause()
    動画要素.value.srcObject = null
  }
}

function captureFrame() {
  if (!動画要素.value) return
  const video = 動画要素.value
  const canvas = document.createElement('canvas')
  canvas.width = video.videoWidth || 1280
  canvas.height = video.videoHeight || 720
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
  const dataUrl = canvas.toDataURL('image/jpeg', 0.86)
  選択画像URL.value = dataUrl
  選択画像Base64.value = dataUrl.split(',')[1] || ''
  選択画像MIME.value = 'image/jpeg'
}

function submitImage() {
  if (!送信可能.value) return
  送信中.value = true
  emit('submit-image', {
    text: 入力テキスト.value,
    mimeType: 選択画像MIME.value,
    base64: 選択画像Base64.value,
  })
  window.setTimeout(() => {
    送信中.value = false
  }, 400)
}

onBeforeUnmount(() => {
  stopCamera()
})
</script>

<template>
  <section class="image-container">
    <div class="image-header">
      <h1>Live Capture</h1>
      <div class="image-status">
        <div :class="['image-status-dot', 接続状態, { sending: 送信中 }]"></div>
        <span>{{ 状態表示テキスト }}</span>
      </div>
    </div>

    <div class="image-area" :class="{ monitoring: inputConnected }">
      <div class="image-preview" :class="{ disabled: !inputConnected }" @click="openPicker">
        <video v-if="カメラ起動中 && !選択画像URL" ref="動画要素" class="preview-image" muted playsinline></video>
        <img v-else-if="選択画像URL" :src="選択画像URL" alt="プレビュー" class="preview-image" />
        <div v-else class="preview-placeholder">クリックして画像選択 / CAMで取得</div>
      </div>

      <div class="toolbar">
        <button class="tool-button" type="button" :disabled="!inputConnected" @click="openPicker">SELECT</button>
        <button class="tool-button" type="button" :disabled="!inputConnected || カメラ起動中" @click="startCamera">CAM</button>
        <button class="tool-button" type="button" :disabled="!カメラ起動中" @click="captureFrame">CAPTURE</button>
        <button class="tool-button" type="button" :disabled="!カメラ起動中" @click="stopCamera">STOP</button>
      </div>
    </div>

    <div class="control-area">
      <div class="text-input-area">
        <div class="input-container">
          <span class="prompt-symbol">&gt;</span>
          <textarea
            v-model="入力テキスト"
            class="input-field"
            placeholder="画像について AI に渡す指示..."
            :disabled="!inputConnected"
          ></textarea>
        </div>
      </div>

      <button
        class="image-send-btn"
        :class="{ 'has-text': 選択画像Base64 || 入力テキスト, 'ws-disabled': !inputConnected }"
        type="button"
        :disabled="!送信可能"
        @click="submitImage"
      >
        <img src="/icons/sending.png" alt="送信" />
        <span class="send-live-label">LIVE</span>
      </button>
    </div>

    <input ref="ファイル入力" type="file" accept="image/*" hidden @change="onFileChange" />
  </section>
</template>

<style scoped>
.image-container {
  background: #101010;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
}

.image-header {
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

.image-header h1 {
  font-size: 22px;
  margin: 0;
}

.image-status {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: bold;
}

.image-status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.image-status-dot.disconnected { background: #888888; }
.image-status-dot.connecting { background: #44ff44; }
.image-status-dot.sending { background: #ff4444; }

.image-area {
  flex: 1;
  display: grid;
  grid-template-rows: 1fr auto;
  gap: 12px;
  padding: 16px;
  background: #000;
}

.image-area.monitoring {
  box-shadow: inset 0 0 0 1px rgba(68, 255, 68, 0.22);
}

.image-preview {
  width: 100%;
  min-height: 260px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: #111;
  display: grid;
  place-items: center;
  cursor: pointer;
  overflow: hidden;
}

.image-preview.disabled {
  cursor: not-allowed;
}

.preview-placeholder {
  color: #9aa3b2;
  font-family: "Courier New", monospace;
  font-size: 13px;
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.toolbar {
  display: flex;
  gap: 8px;
}

.tool-button {
  height: 32px;
  min-width: 84px;
  border: 2px solid #667eea;
  background: rgba(255, 255, 255, 0.95);
  color: #000;
  cursor: pointer;
  font-family: "Courier New", monospace;
  font-size: 12px;
  font-weight: bold;
}

.tool-button:disabled {
  background: #808080;
  border-color: #808080;
  color: #fff;
  cursor: not-allowed;
}

.control-area {
  padding: 10px 20px 12px 20px;
  background: #101010;
  border-top: 1px solid #2c2c2c;
  display: grid;
  grid-template-columns: 1fr 72px;
  gap: 10px;
  align-items: end;
}

.input-container {
  position: relative;
}

.prompt-symbol {
  position: absolute;
  left: 8px;
  top: 12px;
  color: #ffffff;
  font-family: "Courier New", monospace;
  font-weight: bold;
}

.input-field {
  width: 100%;
  min-height: 64px;
  resize: vertical;
  padding: 10px 16px 10px 30px;
  border: 2px solid rgba(255, 255, 255, 0.5);
  background: rgba(0, 0, 0, 0.35);
  color: #e0e0e0;
}

.image-send-btn {
  border: 2px solid #667eea;
  border-radius: 2px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  padding: 0;
  width: 72px;
  height: 64px;
  background: rgba(255, 255, 255, 0.95);
}

.image-send-btn img {
  width: 26px;
  height: 26px;
  filter: brightness(0);
}

.image-send-btn.has-text {
  background: #667eea;
}

.image-send-btn.has-text img,
.image-send-btn.has-text .send-live-label,
.image-send-btn.ws-disabled img,
.image-send-btn.ws-disabled .send-live-label {
  filter: brightness(0) invert(1);
  color: #fff;
}

.image-send-btn:disabled,
.image-send-btn.ws-disabled {
  background: #808080;
  border-color: #808080;
  cursor: not-allowed;
}

.send-live-label {
  font-family: "Courier New", monospace;
  font-size: 11px;
  font-weight: bold;
}

@media (max-width: 820px) {
  .control-area {
    grid-template-columns: 1fr;
  }

  .image-send-btn {
    width: 100%;
  }

  .toolbar {
    flex-wrap: wrap;
  }
}
</style>
