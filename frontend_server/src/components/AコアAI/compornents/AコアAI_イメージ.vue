<!--
  -*- coding: utf-8 -*-

  ------------------------------------------------
  COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
  This software is licensed under the MIT License.
  https://github.com/monjyu1101
  Thank you for keeping the rules.
  ------------------------------------------------
-->

<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from 'vue';
import type { IWebSocketClient } from '@/api/websocket';

const props = defineProps<{
  autoShowSelection?: boolean;
  socketId?: string;
  active?: boolean;
  wsConnected?: boolean;
  チャンネル?: number;
  wsClient?: IWebSocketClient | null;
}>();

const emit = defineEmits<{
  selectionCancel: [];
  selectionComplete: [];
  close: [];
}>();

const imagePreview = ref<string | null>(null);
const fileInput = ref<HTMLInputElement | null>(null);
const showSelectionPopup = ref(false);
const connectionStatus = ref<'disconnected' | 'connecting' | 'sending'>('disconnected');
const videoEl = ref<HTMLVideoElement | null>(null);
const canvasEl = ref<HTMLCanvasElement | null>(null);
const smallCanvasEl = ref<HTMLCanvasElement | null>(null);
const mediaStream = ref<MediaStream | null>(null);
const captureTimer = ref<number | null>(null);
const lastChangeAt = ref<number>(0);
const lastSendAt = ref<number>(0);
const prevSmallImageData = ref<ImageData | null>(null);
const isSending = ref(false);
const sentSinceStable = ref(false);
const isWsConnected = ref(false);
const isSelectingFile = ref(false);
const fileDialogPending = ref(false);
const fileDialogChanged = ref(false);
const fileDialogCheckTimer = ref<number | null>(null);
const fileImageTimer = ref<number | null>(null);
const selectedFileImage = ref<HTMLImageElement | null>(null);
const isFileImageMode = ref(false);

const CAPTURE_INTERVAL_MS = 500;
const STABLE_DURATION_MS = 1500;
const FORCE_SEND_INTERVAL_MS = 60000;
const DIFF_THRESHOLD = 3;

// リソース選択を表示
const showSelection = () => {
  if (!isWsConnected.value) return;
  showSelectionPopup.value = true;
};

// リソース選択をキャンセル
const cancelSelection = () => {
  showSelectionPopup.value = false;
  stopCapture();
  emit('selectionCancel');
};

// 選択オプションを処理
const handleSelection = (option: string) => {
  if (!isWsConnected.value) return;
  showSelectionPopup.value = false;

  switch (option) {
    case 'file':
      selectFile();
      break;
    case 'camera':
      captureCamera();
      break;
    case 'desktop':
      captureDesktop();
      break;
  }
};

// ファイル選択
const selectFile = () => {
  if (!isWsConnected.value) return;
  if (fileInput.value) {
    fileInput.value.value = '';
  }
  isSelectingFile.value = true;
  fileDialogPending.value = true;
  fileDialogChanged.value = false;
  const handleFocus = () => {
    if (!fileDialogPending.value) return;
    if (fileDialogCheckTimer.value) {
      window.clearInterval(fileDialogCheckTimer.value);
      fileDialogCheckTimer.value = null;
    }
    const startAt = Date.now();
    fileDialogCheckTimer.value = window.setInterval(() => {
      if (!fileDialogPending.value) {
        if (fileDialogCheckTimer.value) {
          window.clearInterval(fileDialogCheckTimer.value);
          fileDialogCheckTimer.value = null;
        }
        return;
      }
      if (fileDialogChanged.value) {
        fileDialogPending.value = false;
        isSelectingFile.value = false;
        if (fileDialogCheckTimer.value) {
          window.clearInterval(fileDialogCheckTimer.value);
          fileDialogCheckTimer.value = null;
        }
        return;
      }
      const hasFile = !!(fileInput.value && fileInput.value.files && fileInput.value.files.length > 0);
      if (hasFile) {
        fileDialogPending.value = false;
        isSelectingFile.value = false;
        if (fileDialogCheckTimer.value) {
          window.clearInterval(fileDialogCheckTimer.value);
          fileDialogCheckTimer.value = null;
        }
        return;
      }
      if (Date.now() - startAt >= 2000) {
        fileDialogPending.value = false;
        isSelectingFile.value = false;
        if (fileDialogCheckTimer.value) {
          window.clearInterval(fileDialogCheckTimer.value);
          fileDialogCheckTimer.value = null;
        }
        emit('selectionCancel');
      }
    }, 100);
  };
  window.addEventListener('focus', handleFocus, { once: true });
  fileInput.value?.click();
};

// ファイル選択時の処理
const handleFileChange = (event: Event) => {
  fileDialogChanged.value = true;
  fileDialogPending.value = false;
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];

  if (file && file.type.startsWith('image/')) {
    console.log('[イメージ] ファイル画像選択完了 - ロード開始');

    const reader = new FileReader();
    reader.onload = (e) => {
      const dataUrl = e.target?.result as string;

      // Imageオブジェクトを作成
      const img = new Image();
      img.onload = () => {
        console.log('[イメージ] 画像ロード完了 - サイズ:', img.naturalWidth, 'x', img.naturalHeight);
        // キャプチャと同じロジックで定期送信開始
        startFileImageCapture(img);
        emit('selectionComplete');
      };
      img.onerror = () => {
        console.error('[イメージ] 画像ロードエラー');
        emit('selectionCancel');
      };
      img.src = dataUrl;
    };
    reader.readAsDataURL(file);
  } else {
    emit('selectionCancel');
  }
  isSelectingFile.value = false;
};

const startCapture = async (stream: MediaStream) => {
  stopCapture();
  mediaStream.value = stream;
  connectionStatus.value = 'connecting';
  lastChangeAt.value = Date.now();
  lastSendAt.value = Date.now();
  sentSinceStable.value = false;

  if (videoEl.value) {
    videoEl.value.srcObject = stream;
    try {
      await videoEl.value.play();
    } catch (error) {
      console.error('[イメージ] video再生エラー:', error);
    }
  }

  captureTimer.value = window.setInterval(() => {
    captureFrame();
  }, CAPTURE_INTERVAL_MS);
};

const stopFileImageTimer = () => {
  if (fileImageTimer.value) {
    console.log('[イメージ] 定期送信タイマーを停止 - ID:', fileImageTimer.value);
    window.clearInterval(fileImageTimer.value);
    fileImageTimer.value = null;
  }
  selectedFileImage.value = null;
  isFileImageMode.value = false;
};

// ファイル画像のキャプチャフレーム処理（キャプチャと同じロジック）
const captureFileImageFrame = () => {
  if (!selectedFileImage.value || !canvasEl.value) {
    console.log('[イメージ] キャプチャスキップ - img:', !!selectedFileImage.value, 'canvas:', !!canvasEl.value);
    return;
  }

  const img = selectedFileImage.value;
  const width = img.naturalWidth || img.width;
  const height = img.naturalHeight || img.height;

  canvasEl.value.width = width;
  canvasEl.value.height = height;
  const ctx = canvasEl.value.getContext('2d');
  if (!ctx) return;

  ctx.drawImage(img, 0, 0, width, height);
  const dataUrl = canvasEl.value.toDataURL('image/jpeg', 0.8);

  console.log('[イメージ] 静止画フレームキャプチャ完了 - サイズ:', width, 'x', height);

  // プレビュー更新
  imagePreview.value = dataUrl;

  // 画像送信
  sendImage(dataUrl);
};

// ファイル画像の定期キャプチャ開始
const startFileImageCapture = (img: HTMLImageElement) => {
  stopFileImageTimer();
  stopCapture(); // 既存のビデオキャプチャは停止

  selectedFileImage.value = img;
  isFileImageMode.value = true;
  connectionStatus.value = 'connecting';
  lastSendAt.value = Date.now();

  console.log('[イメージ] 静止画キャプチャモード開始');

  // 最初の送信
  captureFileImageFrame();

  // 60秒間隔で送信
  fileImageTimer.value = window.setInterval(() => {
    console.log('[イメージ] 定期送信タイマー発火 - 60秒経過');
    captureFileImageFrame();
  }, FORCE_SEND_INTERVAL_MS);

  console.log('[イメージ] タイマー設定完了 - ID:', fileImageTimer.value, '間隔:', FORCE_SEND_INTERVAL_MS, 'ms (60秒)');
};

const stopCapture = () => {
  if (captureTimer.value) {
    window.clearInterval(captureTimer.value);
    captureTimer.value = null;
  }
  if (mediaStream.value) {
    for (const track of mediaStream.value.getTracks()) {
      track.stop();
    }
    mediaStream.value = null;
  }
  if (videoEl.value) {
    videoEl.value.srcObject = null;
  }
  prevSmallImageData.value = null;
  stopFileImageTimer();
  connectionStatus.value = 'disconnected';
};

// 自動選択ポップアップ表示
watch(() => props.autoShowSelection, (newValue) => {
  if (newValue) {
    showSelectionPopup.value = true;
  }
}, { immediate: true });

watch(
  () => props.active,
  (isActive) => {
    if (isActive === false) {
      // コンポーネントが非アクティブになった時のみクリーンアップ
      stopCapture();
      stopFileImageTimer();
      imagePreview.value = null;
      if (fileInput.value) {
        fileInput.value.value = '';
      }
      showSelectionPopup.value = false;
    }
    // isActive === true の時は何もしない（タイマーは維持）
  },
  { immediate: true }
);

watch(
  () => props.wsConnected,
  (connected) => {
    const isConnected = !!connected;
    isWsConnected.value = isConnected;
    if (!isConnected) {
      stopCapture();
      stopFileImageTimer();
      showSelectionPopup.value = false;
      connectionStatus.value = 'disconnected';
    } else if (connectionStatus.value === 'disconnected') {
      connectionStatus.value = 'connecting';
    }
    if (isConnected && props.autoShowSelection) {
      showSelectionPopup.value = true;
    }
  },
  { immediate: true }
);

// カメラキャプチャ
const captureCamera = async () => {
  try {
    if (!isWsConnected.value) return;
    const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
    await startCapture(stream);
    emit('selectionComplete');
  } catch (error) {
    console.error('[イメージ] カメラ取得エラー:', error);
    stopCapture();
    emit('selectionCancel');
  }
};

// デスクトップキャプチャ
const captureDesktop = async () => {
  try {
    if (!isWsConnected.value) return;
    const stream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: false });
    await startCapture(stream);
    emit('selectionComplete');
  } catch (error) {
    console.error('[イメージ] 画面共有取得エラー:', error);
    stopCapture();
    emit('selectionCancel');
  }
};

const calcDiff = (a: ImageData, b: ImageData) => {
  const len = a.data.length;
  if (len !== b.data.length) return 999;
  let sum = 0;
  for (let i = 0; i < len; i += 4) {
    sum += Math.abs(a.data[i] - b.data[i]);
    sum += Math.abs(a.data[i + 1] - b.data[i + 1]);
    sum += Math.abs(a.data[i + 2] - b.data[i + 2]);
  }
  return sum / (len / 4) / 3;
};

const captureFrame = () => {
  if (!videoEl.value || !canvasEl.value || !smallCanvasEl.value) return;
  if (videoEl.value.readyState < 2) return;

  const width = videoEl.value.videoWidth || 640;
  const height = videoEl.value.videoHeight || 360;

  canvasEl.value.width = width;
  canvasEl.value.height = height;
  const ctx = canvasEl.value.getContext('2d');
  if (!ctx) return;
  ctx.drawImage(videoEl.value, 0, 0, width, height);

  const smallWidth = 64;
  const smallHeight = 36;
  smallCanvasEl.value.width = smallWidth;
  smallCanvasEl.value.height = smallHeight;
  const sctx = smallCanvasEl.value.getContext('2d');
  if (!sctx) return;
  sctx.drawImage(videoEl.value, 0, 0, smallWidth, smallHeight);
  const currentSmall = sctx.getImageData(0, 0, smallWidth, smallHeight);

  if (prevSmallImageData.value) {
    const diff = calcDiff(currentSmall, prevSmallImageData.value);
    if (diff > DIFF_THRESHOLD) {
      lastChangeAt.value = Date.now();
      sentSinceStable.value = false;
    }
  }
  prevSmallImageData.value = currentSmall;

  const now = Date.now();
  const isStable = now - lastChangeAt.value >= STABLE_DURATION_MS;
  const forceSend = lastSendAt.value > 0 && (now - lastSendAt.value >= FORCE_SEND_INTERVAL_MS);

  if ((isStable && !sentSinceStable.value) || forceSend) {
    const dataUrl = canvasEl.value.toDataURL('image/jpeg', 0.8);
    sendImage(dataUrl);
    lastSendAt.value = now;
    if (isStable) {
      sentSinceStable.value = true;
    }
  } else {
    imagePreview.value = canvasEl.value.toDataURL('image/jpeg', 0.6);
  }
};

const sendImage = async (dataUrl: string | null) => {
  if (!dataUrl) {
    console.log('[イメージ] 送信スキップ - dataUrlなし');
    return;
  }
  if (!isWsConnected.value) {
    console.log('[イメージ] 送信スキップ - WebSocket未接続');
    return;
  }
  if (isSending.value) {
    console.log('[イメージ] 送信スキップ - 送信中');
    return;
  }
  isSending.value = true;
  connectionStatus.value = 'sending';
  imagePreview.value = dataUrl;

  console.log('[イメージ] 画像送信開始 - データサイズ:', dataUrl.length, 'bytes');

  try {
    const base64Payload = dataUrl.includes('base64,')
      ? dataUrl.split('base64,', 2)[1]
      : dataUrl;
    if (!props.wsClient || !props.wsClient.isConnected()) {
      console.log('[イメージ] 送信スキップ - WebSocket未接続');
      return;
    }
    props.wsClient.send({
      ソケットID: props.socketId ?? '',
      チャンネル: -1,
      メッセージ識別: 'input_image',
      メッセージ内容: 'image/png',
      ファイル名: base64Payload,
      サムネイル画像: null
    });
    console.log('[イメージ] 画像送信完了');
  } catch (error) {
    console.error('[イメージ] 画像送信エラー:', error);
  } finally {
    isSending.value = false;
    if (connectionStatus.value === 'sending') {
      connectionStatus.value = 'connecting';
    }
  }
};

// ステータステキスト
const getStatusText = () => {
  const statusMap = {
    disconnected: '切断',
    connecting: '接続中',
    sending: '送信中'
  };
  return statusMap[connectionStatus.value];
};

onMounted(() => {
  connectionStatus.value = 'disconnected';
  isWsConnected.value = !!props.wsConnected;
});

onBeforeUnmount(() => {
  stopCapture();
  stopFileImageTimer();
});
</script>

<template>
  <div class="image-container show">
    <div class="image-header">
      <button class="close-btn" @click="emit('close')" title="閉じる">×</button>
      <h1>Live Capture</h1>
      <div class="image-status">
        <div :class="['image-status-dot', connectionStatus]"></div>
        <span>{{ getStatusText() }}</span>
      </div>
    </div>

    <div class="image-area">
      <div class="image-preview" :class="{ disabled: !isWsConnected }" @click="showSelection">
        <div v-if="!imagePreview" class="preview-placeholder">
          <span class="preview-icon">📷</span>
          <div>画像表示エリア</div>
          <small>クリックしてリソースを選択</small>
        </div>
        <img v-else :src="imagePreview" alt="プレビュー" class="preview-image" />
      </div>

      <video ref="videoEl" class="hidden-video" playsinline muted></video>
      <canvas ref="canvasEl" class="hidden-canvas"></canvas>
      <canvas ref="smallCanvasEl" class="hidden-canvas"></canvas>

      <input
        ref="fileInput"
        type="file"
        accept="image/*"
        style="display: none"
        :disabled="!isWsConnected"
        @change="handleFileChange"
      />
    </div>

    <!-- 選択ポップアップ（コンテナ内に移動） -->
    <div v-if="showSelectionPopup" class="selection-popup" @click.self="cancelSelection">
      <div class="selection-dialog">
        <div class="selection-title">リソース選択</div>
        <div class="selection-options">
          <div class="selection-option" @click="handleSelection('file')">
            📁 画像ファイル選択
          </div>
          <div class="selection-option" @click="handleSelection('camera')">
            <span class="option-icon">📷</span> カメラキャプチャ
          </div>
          <div class="selection-option" @click="handleSelection('desktop')">
            🖥️ デスクトップキャプチャ
          </div>
        </div>
        <button class="selection-cancel" @click="cancelSelection">キャンセル</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.image-container {
  background: #e8f5e9; /* 淡い緑 */
  border-radius: 2px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  width: 100%;
  height: 100%;
  position: relative; /* 追加: selection-popupの基準にする */
}

.image-header {
  background: #c8c8c8;
  color: #333;
  padding: 5px 10%;
  text-align: center;
  position: relative;
}

.image-header h1 {
  font-size: 22px;
  font-weight: bold;
  margin: 0;
  height: 28px;
  line-height: 28px;
}

.close-btn {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  background: transparent;
  border: none;
  font-size: 24px;
  color: #333;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  line-height: 24px;
  text-align: center;
  transition: all 0.2s ease;
}

.close-btn:hover {
  color: #ff4444;
  transform: translateY(-50%) scale(1.2);
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
  padding: 20px;
  overflow-y: auto;
  background: #44ff44; /* 鮮やかな緑 */
  position: relative;
  box-sizing: border-box;
}

.image-preview {
  width: 100%;
  height: 100%;
  border: 2px dashed #81c784;
  border-radius: 2px;
  background: #e8f5e9; /* 淡い緑 */
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.image-preview:hover {
  border-color: #66bb6a;
  background: #e8f5e9; /* ホバー時も淡い緑 */
}
.image-preview.disabled {
  cursor: not-allowed;
  opacity: 0.6;
  border-color: #a5d6a7;
  background: #e8f5e9; /* 淡い緑 */
}
.image-preview.disabled:hover {
  border-color: #a5d6a7;
  background: #e8f5e9; /* 淡い緑 */
}

.preview-placeholder {
  text-align: center;
  color: #666;
}

.preview-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 12px;
  opacity: 0.6;
}

.preview-placeholder small {
  display: block;
  margin-top: 8px;
  font-size: 12px;
  color: #999;
}

.preview-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.hidden-video,
.hidden-canvas {
  display: none;
}

.selection-popup {
  position: absolute; /* fixedからabsoluteに変更 */
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
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

.selection-options {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 20px;
}

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

.selection-cancel:hover {
  background: #e0e0e0;
}
</style>

