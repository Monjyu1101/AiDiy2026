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

const プロパティ = defineProps<{
  autoShowSelection?: boolean;
  socketId?: string;
  active?: boolean;
  wsConnected?: boolean;
  チャンネル?: number;
  wsClient?: IWebSocketClient | null;
}>();

const 通知 = defineEmits<{
  selectionCancel: [];
  selectionComplete: [];
  close: [];
}>();

const 画像プレビュー = ref<string | null>(null);
const ファイル入力 = ref<HTMLInputElement | null>(null);
const 選択ポップアップ表示 = ref(false);
const 接続状態 = ref<'disconnected' | 'connecting' | 'sending'>('disconnected');
const 動画要素 = ref<HTMLVideoElement | null>(null);
const 描画キャンバス = ref<HTMLCanvasElement | null>(null);
const 小型キャンバス = ref<HTMLCanvasElement | null>(null);
const メディアストリーム = ref<MediaStream | null>(null);
const キャプチャタイマー = ref<number | null>(null);
const 最終変化時刻 = ref<number>(0);
const 最終送信時刻 = ref<number>(0);
const 前回小画像 = ref<ImageData | null>(null);
const 送信中 = ref(false);
const 安定後送信済み = ref(false);
const WebSocket接続中 = ref(false);
const ファイル選択中 = ref(false);
const ファイルダイアログ待機中 = ref(false);
const ファイルダイアログ変更済み = ref(false);
const ファイルダイアログ確認タイマー = ref<number | null>(null);
const ファイル画像タイマー = ref<number | null>(null);
const 選択画像 = ref<HTMLImageElement | null>(null);
const ファイル画像モード = ref(false);

const CAPTURE_INTERVAL_MS = 500;
const STABLE_DURATION_MS = 1500;
const FORCE_SEND_INTERVAL_MS = 60000;
const DIFF_THRESHOLD = 3;

// リソース選択を表示
const 選択表示 = () => {
  if (!WebSocket接続中.value) return;
  選択ポップアップ表示.value = true;
};

// リソース選択をキャンセル
const 選択取消 = () => {
  選択ポップアップ表示.value = false;
  キャプチャ停止();
  通知('selectionCancel');
};

// 選択オプションを処理
const 選択処理 = (option: string) => {
  if (!WebSocket接続中.value) return;
  選択ポップアップ表示.value = false;

  switch (option) {
    case 'file':
      ファイル選択();
      break;
    case 'camera':
      カメラキャプチャ();
      break;
    case 'desktop':
      画面共有キャプチャ();
      break;
  }
};

// ファイル選択
const ファイル選択 = () => {
  if (!WebSocket接続中.value) return;
  if (ファイル入力.value) {
    ファイル入力.value.value = '';
  }
  ファイル選択中.value = true;
  ファイルダイアログ待機中.value = true;
  ファイルダイアログ変更済み.value = false;
  const フォーカス処理 = () => {
    if (!ファイルダイアログ待機中.value) return;
    if (ファイルダイアログ確認タイマー.value) {
      window.clearInterval(ファイルダイアログ確認タイマー.value);
      ファイルダイアログ確認タイマー.value = null;
    }
    const 開始時刻 = Date.now();
    ファイルダイアログ確認タイマー.value = window.setInterval(() => {
      if (!ファイルダイアログ待機中.value) {
        if (ファイルダイアログ確認タイマー.value) {
          window.clearInterval(ファイルダイアログ確認タイマー.value);
          ファイルダイアログ確認タイマー.value = null;
        }
        return;
      }
      if (ファイルダイアログ変更済み.value) {
        ファイルダイアログ待機中.value = false;
        ファイル選択中.value = false;
        if (ファイルダイアログ確認タイマー.value) {
          window.clearInterval(ファイルダイアログ確認タイマー.value);
          ファイルダイアログ確認タイマー.value = null;
        }
        return;
      }
      const ファイル有無 = !!(ファイル入力.value && ファイル入力.value.files && ファイル入力.value.files.length > 0);
      if (ファイル有無) {
        ファイルダイアログ待機中.value = false;
        ファイル選択中.value = false;
        if (ファイルダイアログ確認タイマー.value) {
          window.clearInterval(ファイルダイアログ確認タイマー.value);
          ファイルダイアログ確認タイマー.value = null;
        }
        return;
      }
      if (Date.now() - 開始時刻 >= 2000) {
        ファイルダイアログ待機中.value = false;
        ファイル選択中.value = false;
        if (ファイルダイアログ確認タイマー.value) {
          window.clearInterval(ファイルダイアログ確認タイマー.value);
          ファイルダイアログ確認タイマー.value = null;
        }
        通知('selectionCancel');
      }
    }, 100);
  };
  window.addEventListener('focus', フォーカス処理, { once: true });
  ファイル入力.value?.click();
};

// ファイル選択時の処理
const ファイル変更処理 = (イベント: Event) => {
  ファイルダイアログ変更済み.value = true;
  ファイルダイアログ待機中.value = false;
  const 対象要素 = イベント.target as HTMLInputElement;
  const 選択ファイル = 対象要素.files?.[0];

  if (選択ファイル && 選択ファイル.type.startsWith('image/')) {
    console.log('[イメージ] ファイル画像選択完了 - ロード開始');

    const 読込 = new FileReader();
    読込.onload = (e) => {
      const データURL = e.target?.result as string;

      // Imageオブジェクトを作成
      const 画像 = new Image();
      画像.onload = () => {
        console.log('[イメージ] 画像ロード完了 - サイズ:', 画像.naturalWidth, 'x', 画像.naturalHeight);
        // キャプチャと同じロジックで定期送信開始
        ファイル画像キャプチャ開始(画像);
        通知('selectionComplete');
      };
      画像.onerror = () => {
        console.error('[イメージ] 画像ロードエラー');
        通知('selectionCancel');
      };
      画像.src = データURL;
    };
    読込.readAsDataURL(選択ファイル);
  } else {
    通知('selectionCancel');
  }
  ファイル選択中.value = false;
};

const キャプチャ開始 = async (映像ストリーム: MediaStream) => {
  キャプチャ停止();
  メディアストリーム.value = 映像ストリーム;
  接続状態.value = 'connecting';
  最終変化時刻.value = Date.now();
  最終送信時刻.value = Date.now();
  安定後送信済み.value = false;

  if (動画要素.value) {
    動画要素.value.srcObject = 映像ストリーム;
    try {
      await 動画要素.value.play();
    } catch (error) {
      console.error('[イメージ] video再生エラー:', error);
    }
  }

  キャプチャタイマー.value = window.setInterval(() => {
    フレーム取得();
  }, CAPTURE_INTERVAL_MS);
};

const ファイル画像タイマー停止 = () => {
  if (ファイル画像タイマー.value) {
    console.log('[イメージ] 定期送信タイマーを停止 - ID:', ファイル画像タイマー.value);
    window.clearInterval(ファイル画像タイマー.value);
    ファイル画像タイマー.value = null;
  }
  選択画像.value = null;
  ファイル画像モード.value = false;
};

// ファイル画像のキャプチャフレーム処理（キャプチャと同じロジック）
const ファイル画像フレーム取得 = () => {
  if (!選択画像.value || !描画キャンバス.value) {
    console.log('[イメージ] キャプチャスキップ - img:', !!選択画像.value, 'canvas:', !!描画キャンバス.value);
    return;
  }

  const 画像 = 選択画像.value;
  const 幅 = 画像.naturalWidth || 画像.width;
  const 高さ = 画像.naturalHeight || 画像.height;

  描画キャンバス.value.width = 幅;
  描画キャンバス.value.height = 高さ;
  const 描画コンテキスト = 描画キャンバス.value.getContext('2d');
  if (!描画コンテキスト) return;

  描画コンテキスト.drawImage(画像, 0, 0, 幅, 高さ);
  const データURL = 描画キャンバス.value.toDataURL('image/jpeg', 0.8);

  console.log('[イメージ] 静止画フレームキャプチャ完了 - サイズ:', 幅, 'x', 高さ);

  // プレビュー更新
  画像プレビュー.value = データURL;

  // 画像送信
  画像送信(データURL);
};

// ファイル画像の定期キャプチャ開始
const ファイル画像キャプチャ開始 = (画像: HTMLImageElement) => {
  ファイル画像タイマー停止();
  キャプチャ停止(); // 既存のビデオキャプチャは停止

  選択画像.value = 画像;
  ファイル画像モード.value = true;
  接続状態.value = 'connecting';
  最終送信時刻.value = Date.now();

  console.log('[イメージ] 静止画キャプチャモード開始');

  // 最初の送信
  ファイル画像フレーム取得();

  // 60秒間隔で送信
  ファイル画像タイマー.value = window.setInterval(() => {
    console.log('[イメージ] 定期送信タイマー発火 - 60秒経過');
    ファイル画像フレーム取得();
  }, FORCE_SEND_INTERVAL_MS);

  console.log('[イメージ] タイマー設定完了 - ID:', ファイル画像タイマー.value, '間隔:', FORCE_SEND_INTERVAL_MS, 'ms (60秒)');
};

const キャプチャ停止 = () => {
  if (キャプチャタイマー.value) {
    window.clearInterval(キャプチャタイマー.value);
    キャプチャタイマー.value = null;
  }
  if (メディアストリーム.value) {
    for (const トラック of メディアストリーム.value.getTracks()) {
      トラック.stop();
    }
    メディアストリーム.value = null;
  }
  if (動画要素.value) {
    動画要素.value.srcObject = null;
  }
  前回小画像.value = null;
  ファイル画像タイマー停止();
  接続状態.value = 'disconnected';
};

// 自動選択ポップアップ表示
watch(() => プロパティ.autoShowSelection, (新値) => {
  if (新値) {
    選択ポップアップ表示.value = true;
  }
}, { immediate: true });

watch(
  () => プロパティ.active,
  (稼働中) => {
    if (稼働中 === false) {
      // コンポーネントが非アクティブになった時のみクリーンアップ
      キャプチャ停止();
      ファイル画像タイマー停止();
      画像プレビュー.value = null;
      if (ファイル入力.value) {
        ファイル入力.value.value = '';
      }
      選択ポップアップ表示.value = false;
    }
    // 稼働中 === true の時は何もしない（タイマーは維持）
  },
  { immediate: true }
);

watch(
  () => プロパティ.wsConnected,
  (接続フラグ) => {
    const 接続中 = !!接続フラグ;
    WebSocket接続中.value = 接続中;
    if (!接続中) {
      キャプチャ停止();
      ファイル画像タイマー停止();
      選択ポップアップ表示.value = false;
      接続状態.value = 'disconnected';
    } else if (接続状態.value === 'disconnected') {
      接続状態.value = 'connecting';
    }
    if (接続中 && プロパティ.autoShowSelection) {
      選択ポップアップ表示.value = true;
    }
  },
  { immediate: true }
);

// カメラキャプチャ
const カメラキャプチャ = async () => {
  try {
    if (!WebSocket接続中.value) return;
    const 映像ストリーム = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
    await キャプチャ開始(映像ストリーム);
    通知('selectionComplete');
  } catch (error) {
    console.error('[イメージ] カメラ取得エラー:', error);
    キャプチャ停止();
    通知('selectionCancel');
  }
};

// デスクトップキャプチャ
const 画面共有キャプチャ = async () => {
  try {
    if (!WebSocket接続中.value) return;
    const 映像ストリーム = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: false });
    await キャプチャ開始(映像ストリーム);
    通知('selectionComplete');
  } catch (error) {
    console.error('[イメージ] 画面共有取得エラー:', error);
    キャプチャ停止();
    通知('selectionCancel');
  }
};

const 差分計算 = (画像A: ImageData, 画像B: ImageData) => {
  const データ長 = 画像A.data.length;
  if (データ長 !== 画像B.data.length) return 999;
  let 差分合計 = 0;
  for (let i = 0; i < データ長; i += 4) {
    差分合計 += Math.abs(画像A.data[i] - 画像B.data[i]);
    差分合計 += Math.abs(画像A.data[i + 1] - 画像B.data[i + 1]);
    差分合計 += Math.abs(画像A.data[i + 2] - 画像B.data[i + 2]);
  }
  return 差分合計 / (データ長 / 4) / 3;
};

const フレーム取得 = () => {
  if (!動画要素.value || !描画キャンバス.value || !小型キャンバス.value) return;
  if (動画要素.value.readyState < 2) return;

  const 幅 = 動画要素.value.videoWidth || 640;
  const 高さ = 動画要素.value.videoHeight || 360;

  描画キャンバス.value.width = 幅;
  描画キャンバス.value.height = 高さ;
  const 描画コンテキスト = 描画キャンバス.value.getContext('2d');
  if (!描画コンテキスト) return;
  描画コンテキスト.drawImage(動画要素.value, 0, 0, 幅, 高さ);

  const 小幅 = 64;
  const 小高さ = 36;
  小型キャンバス.value.width = 小幅;
  小型キャンバス.value.height = 小高さ;
  const 小型コンテキスト = 小型キャンバス.value.getContext('2d');
  if (!小型コンテキスト) return;
  小型コンテキスト.drawImage(動画要素.value, 0, 0, 小幅, 小高さ);
  const 現在小画像 = 小型コンテキスト.getImageData(0, 0, 小幅, 小高さ);

  if (前回小画像.value) {
    const 差分 = 差分計算(現在小画像, 前回小画像.value);
    if (差分 > DIFF_THRESHOLD) {
      最終変化時刻.value = Date.now();
      安定後送信済み.value = false;
    }
  }
  前回小画像.value = 現在小画像;

  const 現在時刻 = Date.now();
  const 安定中 = 現在時刻 - 最終変化時刻.value >= STABLE_DURATION_MS;
  const 強制送信 = 最終送信時刻.value > 0 && (現在時刻 - 最終送信時刻.value >= FORCE_SEND_INTERVAL_MS);

  if ((安定中 && !安定後送信済み.value) || 強制送信) {
    const データURL = 描画キャンバス.value.toDataURL('image/jpeg', 0.8);
    画像送信(データURL);
    最終送信時刻.value = 現在時刻;
    if (安定中) {
      安定後送信済み.value = true;
    }
  } else {
    画像プレビュー.value = 描画キャンバス.value.toDataURL('image/jpeg', 0.6);
  }
};

const 画像送信 = async (データURL: string | null) => {
  if (!データURL) {
    console.log('[イメージ] 送信スキップ - dataUrlなし');
    return;
  }
  if (!WebSocket接続中.value) {
    console.log('[イメージ] 送信スキップ - WebSocket未接続');
    return;
  }
  if (送信中.value) {
    console.log('[イメージ] 送信スキップ - 送信中');
    return;
  }
  送信中.value = true;
  接続状態.value = 'sending';
  画像プレビュー.value = データURL;

  console.log('[イメージ] 画像送信開始 - データサイズ:', データURL.length, 'bytes');

  try {
    const Base64データ = データURL.includes('base64,')
      ? データURL.split('base64,', 2)[1]
      : データURL;
    if (!プロパティ.wsClient || !プロパティ.wsClient.isConnected()) {
      console.log('[イメージ] 送信スキップ - WebSocket未接続');
      return;
    }
    プロパティ.wsClient.send({
      ソケットID: プロパティ.socketId ?? '',
      チャンネル: -1,
      メッセージ識別: 'input_image',
      メッセージ内容: 'image/png',
      ファイル名: Base64データ,
      サムネイル画像: null
    });
    console.log('[イメージ] 画像送信完了');
  } catch (error) {
    console.error('[イメージ] 画像送信エラー:', error);
  } finally {
    送信中.value = false;
    if (接続状態.value === 'sending') {
      接続状態.value = 'connecting';
    }
  }
};

// ステータステキスト
const 状態表示テキスト = () => {
  const 状態表示一覧 = {
    disconnected: '切断',
    connecting: '接続中',
    sending: '送信中'
  };
  return 状態表示一覧[接続状態.value];
};

onMounted(() => {
  接続状態.value = 'disconnected';
  WebSocket接続中.value = !!プロパティ.wsConnected;
});

onBeforeUnmount(() => {
  キャプチャ停止();
  ファイル画像タイマー停止();
});
</script>

<template>
  <div class="image-container show">
    <div class="image-header">
      <button class="close-btn" @click="通知('close')" title="閉じる">×</button>
      <h1>Live Capture</h1>
      <div class="image-status">
        <div :class="['image-status-dot', 接続状態]"></div>
        <span>{{ 状態表示テキスト() }}</span>
      </div>
    </div>

    <div class="image-area">
      <div class="image-preview" :class="{ disabled: !WebSocket接続中 }" @click="選択表示">
        <div v-if="!画像プレビュー" class="preview-placeholder">
          <span class="preview-icon">📷</span>
          <div>画像表示エリア</div>
          <small>クリックしてリソースを選択</small>
        </div>
        <img v-else :src="画像プレビュー" alt="プレビュー" class="preview-image" />
      </div>

      <video ref="動画要素" class="hidden-video" playsinline muted></video>
      <canvas ref="描画キャンバス" class="hidden-canvas"></canvas>
      <canvas ref="小型キャンバス" class="hidden-canvas"></canvas>

      <input
        ref="ファイル入力"
        type="file"
        accept="image/*"
        style="display: none"
        :disabled="!WebSocket接続中"
        @change="ファイル変更処理"
      />
    </div>

    <!-- 選択ポップアップ（コンテナ内に移動） -->
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


