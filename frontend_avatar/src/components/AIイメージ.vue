<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps<{
  sessionId: string
  inputConnected: boolean
  active?: boolean
  autoShowSelection?: boolean
}>()

const emit = defineEmits<{
  'submit-image': [payload: { text: string; mimeType: string; base64: string }]
  'submit-text': [text: string]
  'selection-cancel': []
  'selection-complete': []
}>()

// --- 画像ソース状態 ---
const 画像プレビュー = ref<string | null>(null)
const ファイル入力 = ref<HTMLInputElement | null>(null)
const 動画要素 = ref<HTMLVideoElement | null>(null)
const 描画キャンバス = ref<HTMLCanvasElement | null>(null)
const 小型キャンバス = ref<HTMLCanvasElement | null>(null)
const メディアストリーム = ref<MediaStream | null>(null)
const キャプチャタイマー = ref<number | null>(null)
const 選択画像 = ref<HTMLImageElement | null>(null)
const ファイル画像モード = ref(false)
const ファイル画像タイマー = ref<number | null>(null)
const ファイル選択中 = ref(false)
const ファイルダイアログ待機中 = ref(false)
const ファイルダイアログ変更済み = ref(false)
const ファイルダイアログ確認タイマー = ref<number | null>(null)

// --- 送信状態 ---
const 接続状態 = ref<'disconnected' | 'connecting' | 'sending'>('disconnected')
const 送信中 = ref(false)
const フラッシュ中 = ref(false)
const エラーメッセージ = ref('')
let フラッシュタイマーID: number | null = null

// --- 変化検出 ---
const 最終変化時刻 = ref(0)
const 最終送信時刻 = ref(0)
const 前回小画像 = ref<ImageData | null>(null)
const 安定後送信済み = ref(false)

// --- テキスト入力 ---
const 入力テキスト = ref('')
const テキストエリア = ref<HTMLTextAreaElement | null>(null)
const ドラッグ中 = ref(false)
const 入力欄最大到達 = ref(false)
const 入力欄最小高さ = 60
const 入力欄最大高さ = ref(380)
const 入力欄固定中 = ref(false)
const 入力欄固定高さ = ref(入力欄最小高さ)

// --- UI ---
const 選択ポップアップ表示 = ref(false)
// --- 自動送信設定 ---
const CAPTURE_INTERVAL_MS = 550
const 自動送信変化率パーセント = ref(3)
const 自動送信待機秒 = ref(2)
const 自動送信強制秒 = ref(60)

const WebSocket接続中 = computed(() => Boolean(props.sessionId))
const 状態表示テキスト = computed(() => {
  const map: Record<string, string> = { disconnected: '切断', connecting: '接続中', sending: '送信中' }
  return map[接続状態.value] ?? '切断'
})

// ===================== テキスト入力 =====================

function 入力欄状態リセット() {
  入力欄最大到達.value = false
  入力欄固定中.value = false
  入力欄固定高さ.value = 入力欄最小高さ
  if (テキストエリア.value) テキストエリア.value.style.height = `${入力欄最小高さ}px`
}

function 入力欄クリア() {
  入力テキスト.value = ''
  入力欄状態リセット()
  nextTick(() => {
    テキストエリア.value?.focus()
    テキストエリア自動調整()
  })
}

function テキストエリア自動調整() {
  if (!テキストエリア.value) return
  const コンテナ = テキストエリア.value.closest('.image-container') as HTMLElement | null
  if (コンテナ) {
    入力欄最大高さ.value = Math.max(入力欄最小高さ, Math.floor(コンテナ.clientHeight * 0.30))
  }
  if (入力テキスト.value.length === 0) { 入力欄状態リセット(); return }
  if (入力欄固定中.value) {
    入力欄最大到達.value = true
    テキストエリア.value.style.height = `${入力欄固定高さ.value}px`
    return
  }
  テキストエリア.value.style.height = `${入力欄最小高さ}px`
  const scrollH = テキストエリア.value.scrollHeight
  const next = Math.max(scrollH, 入力欄最小高さ)
  if (next >= 入力欄最大高さ.value) {
    入力欄最大到達.value = true
    入力欄固定中.value = true
    入力欄固定高さ.value = 入力欄最大高さ.value
    テキストエリア.value.style.height = `${入力欄固定高さ.value}px`
    return
  }
  入力欄最大到達.value = false
  テキストエリア.value.style.height = `${next}px`
}

function テキスト送信() {
  if (!入力テキスト.value.trim() || !WebSocket接続中.value) return
  emit('submit-text', 入力テキスト.value.trim())
}

function 送信ボタン処理() {
  テキスト送信()
  入力欄クリア()
}

// ===================== D&D =====================

function ドラッグオーバー処理(e: DragEvent) {
  e.preventDefault()
  if (!WebSocket接続中.value) return
  ドラッグ中.value = true
}

function ドラッグ離脱処理(e: DragEvent) {
  e.preventDefault()
  if (e.currentTarget === e.target) ドラッグ中.value = false
}

function ドロップ処理(e: DragEvent) {
  e.preventDefault()
  ドラッグ中.value = false
  if (!WebSocket接続中.value) return
  const files = e.dataTransfer?.files
  if (!files || files.length === 0) return
  for (const f of Array.from(files)) {
    if (!f.type.startsWith('image/')) continue
    const reader = new FileReader()
    reader.onload = (ev) => {
      const dataUrl = ev.target?.result as string
      const img = new Image()
      img.onload = () => ファイル画像キャプチャ開始(img)
      img.src = dataUrl
    }
    reader.readAsDataURL(f)
  }
}

// ===================== リソース選択 =====================

function 選択表示() {
  if (!WebSocket接続中.value) return
  エラーメッセージ.value = ''
  選択ポップアップ表示.value = true
}

function 選択取消() {
  選択ポップアップ表示.value = false
  キャプチャ停止()
  emit('selection-cancel')
}

function 選択処理(option: 'file' | 'camera' | 'desktop') {
  if (!WebSocket接続中.value) return
  選択ポップアップ表示.value = false
  switch (option) {
    case 'file':
      ファイル選択()
      break
    case 'camera':
      void カメラキャプチャ()
      break
    case 'desktop':
      void 画面共有キャプチャ()
      break
  }
}

function ファイル選択() {
  if (!WebSocket接続中.value) return
  if (ファイル入力.value) ファイル入力.value.value = ''
  ファイル選択中.value = true
  ファイルダイアログ待機中.value = true
  ファイルダイアログ変更済み.value = false

  const フォーカス処理 = () => {
    if (!ファイルダイアログ待機中.value) return
    if (ファイルダイアログ確認タイマー.value) {
      window.clearInterval(ファイルダイアログ確認タイマー.value)
      ファイルダイアログ確認タイマー.value = null
    }
    const 開始時刻 = Date.now()
    ファイルダイアログ確認タイマー.value = window.setInterval(() => {
      if (!ファイルダイアログ待機中.value) {
        if (ファイルダイアログ確認タイマー.value) {
          window.clearInterval(ファイルダイアログ確認タイマー.value)
          ファイルダイアログ確認タイマー.value = null
        }
        return
      }
      if (ファイルダイアログ変更済み.value) {
        ファイルダイアログ待機中.value = false
        ファイル選択中.value = false
        if (ファイルダイアログ確認タイマー.value) {
          window.clearInterval(ファイルダイアログ確認タイマー.value)
          ファイルダイアログ確認タイマー.value = null
        }
        return
      }
      const ファイル有無 = !!(ファイル入力.value && ファイル入力.value.files && ファイル入力.value.files.length > 0)
      if (ファイル有無) {
        ファイルダイアログ待機中.value = false
        ファイル選択中.value = false
        if (ファイルダイアログ確認タイマー.value) {
          window.clearInterval(ファイルダイアログ確認タイマー.value)
          ファイルダイアログ確認タイマー.value = null
        }
        return
      }
      if (Date.now() - 開始時刻 >= 2000) {
        ファイルダイアログ待機中.value = false
        ファイル選択中.value = false
        if (ファイルダイアログ確認タイマー.value) {
          window.clearInterval(ファイルダイアログ確認タイマー.value)
          ファイルダイアログ確認タイマー.value = null
        }
        emit('selection-cancel')
      }
    }, 100)
  }

  window.addEventListener('focus', フォーカス処理, { once: true })
  ファイル入力.value?.click()
}

function ファイル変更処理(e: Event) {
  ファイルダイアログ変更済み.value = true
  ファイルダイアログ待機中.value = false
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file || !file.type.startsWith('image/')) {
    ファイル選択中.value = false
    emit('selection-cancel')
    return
  }
  const reader = new FileReader()
  reader.onload = (ev) => {
    const dataUrl = ev.target?.result as string
    const img = new Image()
    img.onload = () => {
      ファイル画像キャプチャ開始(img)
      emit('selection-complete')
    }
    img.src = dataUrl
  }
  reader.readAsDataURL(file)
  ファイル選択中.value = false
}

// ===================== キャプチャ =====================

async function カメラキャプチャ() {
  try {
    if (!WebSocket接続中.value) return
    const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false })
    await キャプチャ開始(stream)
    emit('selection-complete')
  } catch (error) {
    console.error('[AIイメージ] カメラ取得エラー:', error)
    キャプチャ停止()
    emit('selection-cancel')
  }
}

async function 画面共有キャプチャ() {
  try {
    if (!WebSocket接続中.value) return
    const stream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: false })
    await キャプチャ開始(stream)
    emit('selection-complete')
  } catch (error) {
    console.error('[AIイメージ] 画面共有取得エラー:', error)
    キャプチャ停止()
    emit('selection-cancel')
  }
}

async function キャプチャ開始(映像ストリーム: MediaStream) {
  キャプチャ停止()
  メディアストリーム.value = 映像ストリーム
  接続状態.value = 'connecting'
  最終変化時刻.value = Date.now()
  最終送信時刻.value = Date.now()
  安定後送信済み.value = false

  if (動画要素.value) {
    動画要素.value.srcObject = 映像ストリーム
    try { await 動画要素.value.play() } catch { /* ignore */ }
  }

  キャプチャタイマー.value = window.setInterval(フレーム取得, CAPTURE_INTERVAL_MS)
}

function ファイル画像キャプチャ開始(img: HTMLImageElement) {
  キャプチャ停止()
  選択画像.value = img
  ファイル画像モード.value = true
  接続状態.value = 'connecting'
  最終送信時刻.value = Date.now()
  ファイル画像フレーム取得()
  ファイル画像強制送信タイマー再設定()
}

function ファイル画像フレーム取得() {
  if (!選択画像.value || !描画キャンバス.value) return
  const img = 選択画像.value
  const w = img.naturalWidth || img.width
  const h = img.naturalHeight || img.height
  描画キャンバス.value.width = w
  描画キャンバス.value.height = h
  const ctx = 描画キャンバス.value.getContext('2d')
  if (!ctx) return
  ctx.drawImage(img, 0, 0, w, h)
  const dataUrl = 描画キャンバス.value.toDataURL('image/jpeg', 0.8)
  画像プレビュー.value = dataUrl
  画像送信(dataUrl)
}

function ファイル画像タイマー停止() {
  if (ファイル画像タイマー.value) {
    window.clearInterval(ファイル画像タイマー.value)
    ファイル画像タイマー.value = null
  }
}

function ファイル画像モード解除() {
  ファイル画像タイマー停止()
  選択画像.value = null
  ファイル画像モード.value = false
}

function ファイル画像強制送信タイマー再設定() {
  ファイル画像タイマー停止()
  if (!ファイル画像モード.value || !選択画像.value) return
  if (自動送信強制秒.value <= 0) return
  ファイル画像タイマー.value = window.setInterval(ファイル画像フレーム取得, 自動送信強制秒.value * 1000)
}

function キャプチャ停止(状態を切断へ戻す = true) {
  if (キャプチャタイマー.value) {
    window.clearInterval(キャプチャタイマー.value)
    キャプチャタイマー.value = null
  }
  if (メディアストリーム.value) {
    for (const t of メディアストリーム.value.getTracks()) t.stop()
    メディアストリーム.value = null
  }
  if (動画要素.value) 動画要素.value.srcObject = null
  前回小画像.value = null
  ファイル画像モード解除()
  接続状態.value = 状態を切断へ戻す ? 'disconnected' : (WebSocket接続中.value ? 'connecting' : 'disconnected')
}

// ===================== 変化検出 + 自動送信 =====================

function 差分計算(a: ImageData, b: ImageData): number {
  const len = a.data.length
  if (len !== b.data.length) return 100
  let sum = 0
  for (let i = 0; i < len; i += 4) {
    const dr = a.data[i]! - b.data[i]!
    const dg = a.data[i + 1]! - b.data[i + 1]!
    const db = a.data[i + 2]! - b.data[i + 2]!
    sum += (dr * dr + dg * dg + db * db) / 3
  }
  return (Math.sqrt(sum / (len / 4)) / 255) * 100
}

function フレーム取得() {
  if (!動画要素.value || !描画キャンバス.value || !小型キャンバス.value) return
  if (動画要素.value.readyState < 2) return

  const w = 動画要素.value.videoWidth || 640
  const h = 動画要素.value.videoHeight || 360
  描画キャンバス.value.width = w
  描画キャンバス.value.height = h
  const ctx = 描画キャンバス.value.getContext('2d')
  if (!ctx) return
  ctx.drawImage(動画要素.value, 0, 0, w, h)

  const sw = 64, sh = 36
  小型キャンバス.value.width = sw
  小型キャンバス.value.height = sh
  const sctx = 小型キャンバス.value.getContext('2d')
  if (!sctx) return
  sctx.drawImage(動画要素.value, 0, 0, sw, sh)
  const current = sctx.getImageData(0, 0, sw, sh)

  if (前回小画像.value) {
    const diff = 差分計算(current, 前回小画像.value)
    if (diff > 自動送信変化率パーセント.value) {
      最終変化時刻.value = Date.now()
      安定後送信済み.value = false
    }
  }
  前回小画像.value = current

  const now = Date.now()
  const stable = now - 最終変化時刻.value >= 自動送信待機秒.value * 1000
  const forced = 自動送信強制秒.value > 0 && 最終送信時刻.value > 0 && now - 最終送信時刻.value >= 自動送信強制秒.value * 1000

  if ((stable && !安定後送信済み.value) || forced) {
    const dataUrl = 描画キャンバス.value.toDataURL('image/jpeg', 0.8)
    画像送信(dataUrl)
    最終送信時刻.value = now
    if (stable) 安定後送信済み.value = true
  } else {
    画像プレビュー.value = 描画キャンバス.value.toDataURL('image/jpeg', 0.6)
  }
}

// ===================== 送信 =====================

function 画像送信(dataUrl: string | null) {
  if (!dataUrl || !WebSocket接続中.value || 送信中.value) return
  送信中.value = true
  接続状態.value = 'sending'
  画像プレビュー.value = dataUrl

  // フラッシュ演出
  if (フラッシュタイマーID !== null) { window.clearTimeout(フラッシュタイマーID); フラッシュタイマーID = null }
  フラッシュ中.value = true
  フラッシュタイマーID = window.setTimeout(() => { フラッシュ中.value = false; フラッシュタイマーID = null }, 200)

  const base64 = dataUrl.includes('base64,') ? dataUrl.split('base64,', 2)[1]! : dataUrl
  emit('submit-image', { text: 入力テキスト.value.trim(), mimeType: 'image/jpeg', base64 })

  送信中.value = false
  window.setTimeout(() => {
    if (接続状態.value === 'sending') 接続状態.value = 'connecting'
  }, 250)
}

// ===================== Watchers =====================

watch(() => props.autoShowSelection, (value) => {
  if (value && WebSocket接続中.value) {
    選択ポップアップ表示.value = true
  }
}, { immediate: true })

watch(() => props.active, (active) => {
  if (active === false) {
    キャプチャ停止()
    画像プレビュー.value = null
    if (ファイル入力.value) {
      ファイル入力.value.value = ''
    }
    選択ポップアップ表示.value = false
  } else if (active && props.autoShowSelection && WebSocket接続中.value) {
    選択ポップアップ表示.value = true
  }
}, { immediate: true })

watch(WebSocket接続中, (v) => {
  if (!v) {
    キャプチャ停止()
    選択ポップアップ表示.value = false
    接続状態.value = 'disconnected'
  } else if (接続状態.value === 'disconnected') {
    接続状態.value = 'connecting'
    if (props.autoShowSelection) {
      選択ポップアップ表示.value = true
    }
  }
})

watch(自動送信強制秒, () => {
  if (ファイル画像モード.value && 選択画像.value) ファイル画像強制送信タイマー再設定()
})

onMounted(() => {
  接続状態.value = WebSocket接続中.value ? 'connecting' : 'disconnected'
  nextTick(テキストエリア自動調整)
  window.addEventListener('resize', テキストエリア自動調整)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', テキストエリア自動調整)
  if (ファイルダイアログ確認タイマー.value) {
    window.clearInterval(ファイルダイアログ確認タイマー.value)
    ファイルダイアログ確認タイマー.value = null
  }
  キャプチャ停止()
})

defineExpose({
  接続状態,
  状態表示テキスト,
  WebSocket接続中,
})
</script>

<template>
  <section class="image-container">
    <div class="image-area" :class="{ flashing: フラッシュ中, monitoring: 接続状態 !== 'disconnected' }">
      <div class="image-preview" :class="{ disabled: !WebSocket接続中 }" @click="選択表示">
      <div v-if="!画像プレビュー" class="preview-placeholder">
          <span class="preview-icon">📷</span>
          <div>画像表示エリア</div>
          <small>クリックしてリソースを選択</small>
        </div>
        <img v-else :src="画像プレビュー" alt="プレビュー" class="preview-image" />
      </div>

      <video ref="動画要素" class="hidden-el" playsinline muted></video>
      <canvas ref="描画キャンバス" class="hidden-el"></canvas>
      <canvas ref="小型キャンバス" class="hidden-el"></canvas>
      <input ref="ファイル入力" type="file" accept="image/*" class="hidden-el" @change="ファイル変更処理" />
    </div>

    <!-- テキスト入力 + 自動送信設定 -->
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
            placeholder="画像についてのメッセージを入力..."
            maxlength="5000"
            :disabled="!WebSocket接続中"
            @input="テキストエリア自動調整"
          ></textarea>
        </div>

        <button
          class="image-send-btn"
          :class="{ 'ws-disabled': !WebSocket接続中, 'has-text': 入力テキスト.length > 0 }"
          type="button"
          :disabled="!入力テキスト.trim() || !WebSocket接続中"
          title="送信"
          @click="送信ボタン処理"
        >
          <img src="/icons/sending.png" alt="送信" />
          <span class="send-live-label">LIVE</span>
        </button>

        <div class="auto-send-settings">
          <div class="auto-send-line auto-send-line-top">
            <span class="auto-send-label">自動送信</span>
            <span class="auto-send-label auto-send-paren">(待機
              <select v-model.number="自動送信待機秒" class="auto-send-select">
                <option :value="1">1</option>
                <option :value="2">2</option>
                <option :value="3">3</option>
                <option :value="5">5</option>
              </select>秒)</span>
          </div>
          <div class="auto-send-line">
            <span class="auto-send-label">変化</span>
            <select v-model.number="自動送信変化率パーセント" class="auto-send-select">
              <option :value="1">1</option>
              <option :value="2">2</option>
              <option :value="3">3</option>
              <option :value="5">5</option>
              <option :value="10">10</option>
              <option :value="20">20</option>
            </select>
            <span class="auto-send-unit">%</span>
            <span class="auto-send-or">or</span>
            <span class="auto-send-label">経過</span>
            <select v-model.number="自動送信強制秒" class="auto-send-select">
              <option :value="0">切</option>
              <option :value="60">60</option>
              <option :value="300">300</option>
              <option :value="600">600</option>
            </select>
            <span class="auto-send-unit">秒</span>
          </div>
        </div>
      </div>
    </div>

    <!-- リソース選択ポップアップ -->
    <div v-if="選択ポップアップ表示" class="selection-popup" @click.self="選択取消">
      <div class="selection-dialog">
        <div class="selection-title">リソース選択</div>
        <div class="selection-options">
          <div class="selection-option" @click="選択処理('file')">
            📁 画像ファイル選択
          </div>
          <div class="selection-option" @click="選択処理('camera')">
            <span class="option-icon">📷</span> カメラキャプチャ
          </div>
          <div class="selection-option" @click="選択処理('desktop')">
            🖥️ デスクトップキャプチャ
          </div>
        </div>
        <button class="selection-cancel" @click="選択取消">キャンセル</button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.image-container {
  background: #101010;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  width: 100%;
  height: 100%;
  position: relative;
}

.image-area {
  flex: 1;
  padding: 2px;
  overflow-y: auto;
  background: #101010;
  position: relative;
  box-sizing: border-box;
}

.image-area.monitoring { animation: pulse-border 2.5s infinite; }

@keyframes pulse-border {
  0%, 100% { background: #ff4444; }
  50% { background: rgba(255, 68, 68, 0.15); }
}

.image-area.flashing::after {
  content: '';
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.55);
  animation: flash-once 0.2s ease-out forwards;
  pointer-events: none;
  z-index: 10;
}

@keyframes flash-once {
  0% { opacity: 1; }
  30% { opacity: 0.8; }
  100% { opacity: 0; }
}

.image-preview {
  width: 100%;
  height: 100%;
  border: none;
  background: #101010;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.image-preview.disabled { cursor: not-allowed; opacity: 0.6; }

.preview-placeholder { text-align: center; color: #666; }
.preview-icon { font-size: 48px; display: block; margin-bottom: 12px; opacity: 0.6; }
.preview-placeholder small { display: block; margin-top: 8px; font-size: 12px; color: #999; }
.preview-image { max-width: 100%; max-height: 100%; object-fit: contain; }

.hidden-el { display: none; }

/* 選択ポップアップ */
.selection-popup {
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.selection-dialog {
  background: white;
  border-radius: 2px;
  padding: 30px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  min-width: 300px;
  text-align: center;
}

.selection-title {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 20px;
  color: #333;
}

.selection-options { display: flex; flex-direction: column; gap: 15px; margin-bottom: 20px; }

.selection-option {
  padding: 15px 20px;
  border: 2px solid #e0e0e0;
  border-radius: 2px;
  background: white;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 16px;
}

.selection-option:hover {
  border-color: #667eea;
  background: #f8f9ff;
}

.option-icon {
  margin-right: 8px;
}

.selection-cancel {
  padding: 10px 20px;
  background: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 2px;
  cursor: pointer;
  font-size: 14px;
  color: #666;
}

.selection-cancel:hover { background: #e0e0e0; }

/* コントロールエリア */
.control-area {
  padding: 10px 20px 0 20px;
  background: #101010;
  border-top: 1px solid #2c2c2c;
  display: flex;
  flex-direction: column;
}

.text-input-area {
  display: flex;
  gap: 10px;
  align-items: flex-end;
  min-width: 0;
}

.text-input-area.drag-over {
  background: rgba(102, 126, 234, 0.2);
  border: 2px dashed #667eea;
  border-radius: 4px;
  padding: 8px;
}

.input-container { position: relative; flex: 1; min-width: 0; }

.prompt-symbol {
  position: absolute;
  left: 8px;
  top: 16px;
  color: #fff;
  font-family: 'Courier New', monospace;
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
  box-sizing: border-box;
}

.input-field.at-limit { font-size: 8px; line-height: 1.1; }
.input-field:disabled { border-color: #808080; color: #666; background: rgba(128, 128, 128, 0.1); }
.input-field:focus { border-color: #fff; }
.input-field::placeholder { color: #888; }

.image-send-btn {
  border: 2px solid #667eea;
  border-radius: 2px;
  cursor: pointer;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  width: 56px;
  height: 48px;
  margin-bottom: 20px;
  background: rgba(255, 255, 255, 0.95);
  flex-shrink: 0;
}

.image-send-btn img { width: 34px; height: 34px; object-fit: contain; pointer-events: none; filter: brightness(0); }

.send-live-label {
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
}

.image-send-btn:hover:not(:disabled) { background: rgba(240, 240, 240, 0.95); border-color: #5a6fd8; }
.image-send-btn.has-text { background: #667eea; border-color: #667eea; }
.image-send-btn.has-text img { filter: brightness(0) invert(1); }
.image-send-btn.has-text .send-live-label { color: #fff; }
.image-send-btn.has-text:hover:not(:disabled) { background: #5a6fd8; border-color: #5a6fd8; }
.image-send-btn:disabled:not(.ws-disabled) { background: rgba(255, 255, 255, 0.95); border-color: #667eea; cursor: not-allowed; opacity: 1; }
.image-send-btn:disabled:not(.ws-disabled) img { filter: brightness(0); }
.image-send-btn.ws-disabled { background: #808080 !important; border-color: #808080 !important; cursor: not-allowed; opacity: 1; }
.image-send-btn.ws-disabled img { filter: brightness(0) invert(1) !important; }
.image-send-btn.ws-disabled .send-live-label { color: #fff; }

/* 自動送信設定 */
.auto-send-settings {
  min-width: 168px;
  margin-bottom: 20px;
  padding: 2px 6px;
  border: 1px solid rgba(102, 126, 234, 0.45);
  background: rgba(20, 24, 38, 0.85);
  color: #d6def8;
  font-size: 10px;
  border-radius: 2px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.auto-send-line { display: flex; align-items: center; gap: 3px; height: 20px; white-space: nowrap; }
.auto-send-line-top { justify-content: space-between; }
.auto-send-label { color: #d6def8; white-space: nowrap; line-height: 1; }
.auto-send-paren { display: flex; align-items: center; gap: 2px; }
.auto-send-unit { color: #97a8df; white-space: nowrap; }
.auto-send-or { color: #97a8df; margin: 0 3px; white-space: nowrap; }

.auto-send-select {
  width: 44px;
  height: 18px;
  border: 1px solid rgba(102, 126, 234, 0.65);
  background: rgba(6, 9, 16, 0.95);
  color: #fff;
  border-radius: 2px;
  font-size: 10px;
  padding: 0 2px;
  position: relative;
  top: 6px;
}

@media (max-width: 480px) {
  .text-input-area { flex-wrap: wrap; }
  .image-send-btn { width: 100%; margin-bottom: 10px; }
  .auto-send-settings { width: 100%; }
}
</style>
