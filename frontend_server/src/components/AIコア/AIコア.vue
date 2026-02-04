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
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import apiClient from '@/api/client';
import AI設定再起動 from './dialog/AI設定再起動.vue';
import { AIコアWebSocket, createWebSocketUrl, type IWebSocketClient } from '@/api/websocket';
import AIコアチャット from './compornents/AIチャット.vue';
import AIコアイメージ from './compornents/AIイメージ.vue';
import AIコアコード from './compornents/AIコード.vue';
import { AudioStreamProcessor } from './AI音声処理';

const route = useRoute();
const router = useRouter();

// ソケットID（全コンポーネント共通）
const ソケットID = ref('');

// 親WebSocket接続（音声・画像用のみ、チャンネル-1）
const wsClient = ref<IWebSocketClient | null>(null);
const wsConnected = ref(false);

// モデル設定情報
const モデル設定 = ref({
  CHAT_AI: '',
  LIVE_AI: '',
  CODE_AI1: '',
  CODE_AI2: '',
  CODE_AI3: '',
  CODE_AI4: ''
});

const chatMode = ref<'chat' | 'live' | 'code1' | 'code2' | 'code3' | 'code4'>('live');

// エラーメッセージ
const errorMessage = ref('');

// 各コンポーネントの表示状態（初期値は全てfalse、WebSocket接続で初期値受信後に有効化）
const showChat = ref(false);
const showImage = ref(false);
const showAgent1 = ref(false);
const showAgent2 = ref(false);
const showAgent3 = ref(false);
const showAgent4 = ref(false);

// 音声・画像制御（初期値は全てfalse、WebSocket接続で初期値受信後に有効化）
const enableMicrophone = ref(false);
const enableSpeaker = ref(false);
const enableCamera = ref(false);

// チャット数カウント
const chatCount = ref(0);
const enableChatButton = ref(false);

// エージェント1～4カウント
const agent1Count = ref(0);
const enableAgent1Button = ref(false);
const agent2Count = ref(0);
const enableAgent2Button = ref(false);
const agent3Count = ref(0);
const enableAgent3Button = ref(false);
const agent4Count = ref(0);
const enableAgent4Button = ref(false);

// キャプチャ画像
const capturedImage = ref<string | null>(null);

// 自動選択ポップアップ表示フラグ
const autoShowSelection = ref(false);

// チェックボックスパネルの表示/非表示
const showModelConfig = ref(false);

// 音声処理プロセッサ
let audioProcessor: AudioStreamProcessor | null = null;

// ビジュアライザー表示状態を同期
const syncVisualizerVisibility = () => {
  if (!audioProcessor) return;
  audioProcessor.updateVisualizerVisibility(enableMicrophone.value, enableSpeaker.value);
};

const syncLiveSampleRate = () => {
  if (!audioProcessor) return;
  const liveAi = モデル設定.value.LIVE_AI || '';
  const provider = liveAi === 'openai_live' ? 'openai' : liveAi;
  audioProcessor.setSampleRate(provider);
};

// チャットボタンクリック時
const toggleChat = () => {
  enableChatButton.value = !enableChatButton.value;
  showChat.value = enableChatButton.value;
};

// エージェント1ボタンクリック時
const toggleAgent1 = () => {
  enableAgent1Button.value = !enableAgent1Button.value;
  showAgent1.value = enableAgent1Button.value;
};

// エージェント2ボタンクリック時
const toggleAgent2 = () => {
  enableAgent2Button.value = !enableAgent2Button.value;
  showAgent2.value = enableAgent2Button.value;
};

// エージェント3ボタンクリック時
const toggleAgent3 = () => {
  enableAgent3Button.value = !enableAgent3Button.value;
  showAgent3.value = enableAgent3Button.value;
};

// エージェント4ボタンクリック時
const toggleAgent4 = () => {
  enableAgent4Button.value = !enableAgent4Button.value;
  showAgent4.value = enableAgent4Button.value;
};

// カメラボタンクリック時
const handleCameraClick = () => {
  if (enableCamera.value) {
    enableCamera.value = false;
    showImage.value = false;
    autoShowSelection.value = false;
    capturedImage.value = null;
    return;
  }
  autoShowSelection.value = false;
  nextTick(() => {
    autoShowSelection.value = true;
  });
  showImage.value = true;
  enableCamera.value = true;
};

// イメージ選択がキャンセルされた時
const handleImageSelectionCancel = () => {
  showImage.value = false;
  enableCamera.value = false;
  autoShowSelection.value = false;
  capturedImage.value = null;
};

// 各コンポーネントを閉じるハンドラー
const handleCloseChat = () => {
  showChat.value = false;
  enableChatButton.value = false; // ボタンもオフに
};

const handleCloseImage = () => {
  showImage.value = false;
  enableCamera.value = false;
  autoShowSelection.value = false;
  capturedImage.value = null;
};

const handleCloseAgent1 = () => {
  showAgent1.value = false;
  enableAgent1Button.value = false; // ボタンもオフに
};

const handleCloseAgent2 = () => {
  showAgent2.value = false;
  enableAgent2Button.value = false; // ボタンもオフに
};

const handleCloseAgent3 = () => {
  showAgent3.value = false;
  enableAgent3Button.value = false; // ボタンもオフに
};

const handleCloseAgent4 = () => {
  showAgent4.value = false;
  enableAgent4Button.value = false; // ボタンもオフに
};

// イメージチェックボックスの変更を監視
const handleImageCheckboxChange = async (newValue: boolean, oldValue: boolean) => {
  // OFFからONになった時のみ選択ポップアップを表示
  if (newValue && !oldValue) {
    autoShowSelection.value = true;
  }
};

// WebSocket接続を初期化
const initializeWebSocket = async (既存ソケットID?: string) => {
  try {
    const wsUrl = createWebSocketUrl('/core/ws/AIコア');
    console.log('[AIコア] WebSocket接続開始:', wsUrl, 'ソケットID:', 既存ソケットID);

    wsClient.value = new AIコアWebSocket(wsUrl, 既存ソケットID, -1);

    // メッセージハンドラを登録（connect()の前に登録）
    wsClient.value.on('init', (message) => {
      console.log('[AIコア] 初期化完了:', message.ソケットID);
      
      const 初期データ = message.メッセージ内容 || {};
      
      // モデル設定を保存
      if (初期データ.モデル設定) {
        モデル設定.value = {
          CHAT_AI: 初期データ.モデル設定.CHAT_AI || '',
          LIVE_AI: 初期データ.モデル設定.LIVE_AI || '',
          CODE_AI1: 初期データ.モデル設定.CODE_AI1 || '',
          CODE_AI2: 初期データ.モデル設定.CODE_AI2 || '',
          CODE_AI3: 初期データ.モデル設定.CODE_AI3 || '',
          CODE_AI4: 初期データ.モデル設定.CODE_AI4 || ''
        };
        console.log('[AIコア] モデル設定:', モデル設定.value);
      }

      syncLiveSampleRate();
      
      // サーバーから受信した初期値でボタン状態を設定
      if (初期データ.ボタン) {
        enableSpeaker.value = 初期データ.ボタン.スピーカー ?? true; // デフォルトオン
        enableMicrophone.value = 初期データ.ボタン.マイク || false;
        enableCamera.value = false; // 常にオフで開始
        enableChatButton.value = 初期データ.ボタン.チャット ?? true; // デフォルトオン
        enableAgent1Button.value = 初期データ.ボタン.エージェント1 || false;
        enableAgent2Button.value = 初期データ.ボタン.エージェント2 || false;
        enableAgent3Button.value = 初期データ.ボタン.エージェント3 || false;
        enableAgent4Button.value = 初期データ.ボタン.エージェント4 || false;
        chatMode.value = 初期データ.ボタン.チャットモード || 'live';
        console.log('[AIコア] ボタン状態を初期化:', 初期データ.ボタン);
      } else {
        chatMode.value = 'live';
      }

      showImage.value = enableCamera.value; // 常にfalse
      syncVisualizerVisibility();

      // WebSocket接続確立フラグを設定（子コンポーネントのマウント前に設定）
      wsConnected.value = true;
      console.log('[AIコア] WebSocket接続確立完了');
      saveState();

      // nextTickで画面状態を復元（子コンポーネントがマウントされてから）
      nextTick(() => {
        console.log('[AIコア] 画面状態を復元開始');
        // ボタン状態から画面状態を復元
        showChat.value = enableChatButton.value;
        showAgent1.value = enableAgent1Button.value;
        showAgent2.value = enableAgent2Button.value;
        showAgent3.value = enableAgent3Button.value;
        showAgent4.value = enableAgent4Button.value;
        console.log('[AIコア] 画面状態復元完了:', {
          showChat: showChat.value,
          showAgent1: showAgent1.value,
          showAgent2: showAgent2.value,
          showAgent3: showAgent3.value,
          showAgent4: showAgent4.value
        });
      });
    });

    wsClient.value.on('streaming_started', (message) => {
      console.log('[AIコア] ストリーミング開始:', message);
    });

    wsClient.value.on('heartbeat', (message) => {
      console.log('[AIコア] ハートビート:', message.count);
    });

    // チャンネル登録/解除の確認メッセージ
    wsClient.value.on('channel_registered', (message) => {
      console.log('[AIコア] チャンネル登録確認:', message);
    });

    wsClient.value.on('channel_unregistered', (message) => {
      console.log('[AIコア] チャンネル解除確認:', message);
    });

    // operations 返信は受け取らない

    wsClient.value.on('error', (message) => {
      console.error('[AIコア] エラー:', message.error);
    });

    // 音声メッセージハンドラー
    wsClient.value.on('output_audio', (message) => {
      console.log('[AIコア] 音声出力受信');
      if (audioProcessor) {
        audioProcessor.handleAudioMessage(message);
      }
    });

    wsClient.value.on('cancel_audio', () => {
      console.log('[AIコア] 音声キャンセル');
      if (audioProcessor) {
        audioProcessor.cancelAudioOutput();
      }
    });

    // 接続を確立してソケットIDを取得
    console.log('[AIコア] WebSocket.connect()呼び出し');
    const 取得ソケットID = await wsClient.value.connect();
    ソケットID.value = 取得ソケットID;
    console.log('[AIコア] WebSocket接続完了 ソケットID:', 取得ソケットID);

    return 取得ソケットID;
  } catch (error) {
    console.error('[AIコア] WebSocket接続エラー:', error);
    wsConnected.value = false;
    throw error;
  }
};

// 初期化処理
onMounted(async () => {
  const URLのセッションID = (route.query.セッションID as string) || (route.query.ソケットID as string);
  console.log('[AIコア] ========================================');
  console.log('[AIコア] 初期化開始');
  console.log('[AIコア] URLからのセッションID:', URLのセッションID);
  console.log('[AIコア] ========================================');

  // 音声処理プロセッサを初期化
  audioProcessor = new AudioStreamProcessor(wsClient, ソケットID, enableSpeaker);
  audioProcessor.setupOutputAudio();

  // ビジュアライザーセットアップ（DOM確実に準備されるまで待つ）
  setTimeout(() => {
    console.log('[AIコア] ビジュアライザー要素を検索中...');
    const audioBarsElement = document.getElementById('audioBars');
    const overlayElement = document.getElementById('audioVisualizerOverlay');
    console.log('[AIコア] ビジュアライザー要素:', { audioBarsElement, overlayElement });

    if (audioProcessor && audioBarsElement && overlayElement) {
      audioProcessor.setupAudioVisualizer(audioBarsElement, overlayElement);
      console.log('[AIコア] ビジュアライザーセットアップ完了');
      syncVisualizerVisibility();
    } else {
      console.error('[AIコア] ビジュアライザー要素が見つかりません', {
        audioProcessor: !!audioProcessor,
        audioBarsElement: !!audioBarsElement,
        overlayElement: !!overlayElement
      });
    }
  }, 500);

  try {
    // REST APIで初期化（ソケットIDのみ取得）
    const response = await apiClient.post('/core/AIコア/初期化', {
      ソケットID: URLのセッションID || '',
      セッションID: URLのセッションID || ''
    });

    if (response.data.status === 'OK') {
      const data = response.data.data;
      ソケットID.value = data.ソケットID;

      if (!URLのセッションID) {
        const newUrl = `${window.location.pathname}?セッションID=${ソケットID.value}`;
        window.location.href = newUrl;
        return;
      }
    }

    // WebSocket接続を確立（RESTで取得したソケットIDを使用）
    console.log('[AIコア] WebSocket接続を開始...');
    const 確立済みソケットID = await initializeWebSocket(ソケットID.value || URLのセッションID);
    console.log('[AIコア] ========================================');
    console.log('[AIコア] ✅ 初期化完了');
    console.log('[AIコア] ソケットID:', 確立済みソケットID);
    console.log('[AIコア] wsConnected:', wsConnected.value);
    console.log('[AIコア] ========================================');
  } catch (error) {
    console.error('[AIコア] ========================================');
    console.error('[AIコア] ❌ 初期化エラー:', error);
    console.error('[AIコア] ========================================');
    errorMessage.value = `初期化失敗: ${error}`;
  }
});

// コンポーネント破棄時にWebSocket接続を切断
onBeforeUnmount(() => {
  // 音声処理のクリーンアップ
  if (audioProcessor) {
    audioProcessor.cleanup();
    audioProcessor = null;
  }

  if (wsClient.value) {
    console.log('[AIコア] WebSocket接続を切断します');
    wsClient.value.disconnect();
    wsClient.value = null;
    wsConnected.value = false;
  }
});

// 画面状態が変わったら保存
const saveState = async () => {
  if (!ソケットID.value) return;

  const ボタン = {
    スピーカー: enableSpeaker.value,
    マイク: enableMicrophone.value,
    カメラ: enableCamera.value,
    チャット: enableChatButton.value,
    エージェント1: enableAgent1Button.value,
    エージェント2: enableAgent2Button.value,
    エージェント3: enableAgent3Button.value,
    エージェント4: enableAgent4Button.value,
    チャットモード: chatMode.value
  };

  try {
    if (wsClient.value && wsConnected.value) {
      wsClient.value.updateState({}, ボタン); // 画面状態は空オブジェクト
      console.log('[AIコア] 状態更新 (WebSocket):', { ボタン });
    }
  } catch (error) {
    console.error('[AIコア] 状態保存エラー:', error);
  }
};

// showChat等の監視は不要（ボタンで直接制御するため削除）
// イメージだけ個別に監視（キャプチャ選択が必要なため）
watch(showImage, async (newValue, oldValue) => {
  if (newValue && !oldValue) {
    // OFFからONになった時はキャプチャ選択を促す
    await handleImageCheckboxChange(newValue, oldValue);
  }
  saveState();
});

watch([enableMicrophone, enableSpeaker, enableCamera], () => {
  if (!enableCamera.value) {
    showImage.value = false;
    capturedImage.value = null;
  } else {
    showImage.value = true;
  }
  saveState();
});

watch(() => モデル設定.value.LIVE_AI, () => {
  syncLiveSampleRate();
});

// マイクボタンの状態変化を監視
watch(enableMicrophone, async (newValue, oldValue) => {
  if (!audioProcessor) return;

  // ビジュアライザー表示状態を更新
  audioProcessor.updateVisualizerVisibility(newValue, enableSpeaker.value);

  if (newValue && !oldValue) {
    // マイクON
    console.log('[AIコア] マイク起動');
    const result = await audioProcessor.startMicrophone();
    if (!result.success) {
      console.error('[AIコア] マイク起動失敗:', result.error);
      errorMessage.value = result.error || 'マイクの起動に失敗しました。';
      enableMicrophone.value = false;
    }
  } else if (!newValue && oldValue) {
    // マイクOFF
    console.log('[AIコア] マイク停止');
    audioProcessor.stopMicrophone();
  }
});

// スピーカーボタンの状態変化を監視
watch(enableSpeaker, (newValue, oldValue) => {
  if (!audioProcessor) return;

  // ビジュアライザー表示状態を更新
  audioProcessor.updateVisualizerVisibility(enableMicrophone.value, newValue);

  if (!newValue && oldValue) {
    // スピーカーOFF時は再生中の音声をクリア
    console.log('[AIコア] スピーカーOFF - 音声クリア');
    audioProcessor.clearAudioPlayback();
  }

  // 状態を保存
  saveState();
});

// チャットボタンの状態変化を監視
watch(enableChatButton, () => {
  saveState();
});

// エージェント1～4ボタンの状態変化を監視
watch(enableAgent1Button, () => {
  saveState();
});

watch(enableAgent2Button, () => {
  saveState();
});

watch(enableAgent3Button, () => {
  saveState();
});

watch(enableAgent4Button, () => {
  saveState();
});

watch(chatMode, () => {
  saveState();
});

// 表示中のパネル数をカウント
const visiblePanelCount = computed(() => {
  let count = 0;
  if (showChat.value) count++;
  if (showImage.value) count++;
  if (showAgent1.value) count++;
  if (showAgent2.value) count++;
  if (showAgent3.value) count++;
  if (showAgent4.value) count++;
  return count;
});

// パネル数に応じたレイアウトクラス
const gridLayoutClass = computed(() => {
  const count = visiblePanelCount.value;
  if (count === 0) return 'layout-empty';
  if (count === 1) return 'layout-single';
  if (count === 2) return 'layout-double';
  if (count === 3) return 'layout-triple';
  if (count === 4) return 'layout-quad';
  return 'layout-multi'; // 5枚以上
});
</script>

<template>
  <div class="ai-core-view">
    <!-- WebSocket接続状態インジケーター -->
    <div class="ws-status" :class="{ connected: wsConnected }">
      <span class="ws-status-dot"></span>
      <span class="ws-status-text">{{ wsConnected ? 'WS接続中' : 'WS切断' }}</span>
    </div>

    <!-- 音声ビジュアライザー（WS接続状態の左側） -->
    <div id="audioVisualizerOverlay" class="audio-visualizer-overlay">
      <div id="audioBars" class="audio-bars"></div>
    </div>

    <!-- エラーメッセージ表示 -->
    <div v-if="errorMessage" class="error-message">
      <button class="error-close" @click="errorMessage = ''">×</button>
      <strong>エラー:</strong> {{ errorMessage }}
    </div>

    <!-- 音声・画像制御フローティングアイコン -->
    <div class="floating-controls">
      <button
        class="floating-icon microphone-icon"
        :class="{ active: enableMicrophone }"
        :disabled="!wsConnected"
        @click="enableMicrophone = !enableMicrophone"
        title="マイク"
      >
        <img src="/icons/microphone.png" alt="マイク" />
      </button>
      <button
        class="floating-icon speaker-icon"
        :class="{ inactive: !enableSpeaker, active: enableSpeaker }"
        :disabled="!wsConnected"
        @click="enableSpeaker = !enableSpeaker"
        title="スピーカー"
      >
        <img src="/icons/speaker.png" alt="スピーカー" />
      </button>
      <button
        class="floating-icon chat-icon"
        :class="{ inactive: !enableChatButton, active: enableChatButton }"
        :disabled="!wsConnected"
        @click="toggleChat"
        title="チャット"
      >
        {{ chatCount }}
      </button>
      <button
        class="floating-icon agent-icon"
        :class="{ inactive: !enableAgent1Button, active: enableAgent1Button }"
        :disabled="!wsConnected"
        @click="toggleAgent1"
        title="コード1"
      >
        1
      </button>
      <button
        class="floating-icon camera-icon"
        :class="{ active: enableCamera }"
        :disabled="!wsConnected"
        @click="handleCameraClick"
        title="カメラ"
      >
        <img src="/icons/camera.png" alt="カメラ" />
      </button>
      <button
        class="floating-icon agent-icon"
        :class="{ inactive: !enableAgent2Button, active: enableAgent2Button }"
        :disabled="!wsConnected"
        @click="toggleAgent2"
        title="コード2"
      >
        2
      </button>
      <button
        class="floating-icon agent-icon"
        :class="{ inactive: !enableAgent3Button, active: enableAgent3Button }"
        :disabled="!wsConnected"
        @click="toggleAgent3"
        title="コード3"
      >
        3
      </button>
      <button
        class="floating-icon agent-icon"
        :class="{ inactive: !enableAgent4Button, active: enableAgent4Button }"
        :disabled="!wsConnected"
        @click="toggleAgent4"
        title="コード4"
      >
        4
      </button>
      <button
        class="floating-icon config-icon"
        :disabled="!wsConnected"
        @click="showModelConfig = true"
        title="モデル設定"
      >
        <img src="/icons/setting.png" alt="設定" class="icon-image" />
      </button>
    </div>

    <!-- コンポーネントグリッド -->
    <div class="components-grid" :class="gridLayoutClass">
      <!-- チャット -->
      <div v-show="showChat" class="component-panel">
        <AIコアチャット 
          :socket-id="ソケットID"
          :チャンネル="0"
          :chat-ai="モデル設定.CHAT_AI"
          :live-ai="モデル設定.LIVE_AI"
          :chat-mode="chatMode"
          :input-ws-client="wsClient"
          :input-connected="wsConnected"
          @mode-change="chatMode = $event"
          @activate="showChat = true; enableChatButton = true"
          @close="handleCloseChat" 
        />
      </div>

      <!-- エージェント1 -->
      <div v-show="showAgent1" class="component-panel">
        <AIコアコード
          key="code-1"
          :socket-id="ソケットID"
          :チャンネル="1"
          :code-ai="モデル設定.CODE_AI1"
          :input-ws-client="wsClient"
          :input-connected="wsConnected"
          @activate="showAgent1 = true; enableAgent1Button = true"
          @close="handleCloseAgent1"
        />
      </div>

      <!-- イメージ -->
      <div v-show="showImage" class="component-panel">
        <AIコアイメージ
          :auto-show-selection="autoShowSelection"
          :socket-id="ソケットID"
          :active="showImage"
          :ws-connected="wsConnected"
          :ws-client="wsClient ?? null"
          :チャンネル="0"
          @selection-cancel="handleImageSelectionCancel"
          @selection-complete="autoShowSelection = false"
          @close="handleCloseImage"
        />
      </div>

      <!-- エージェント2 -->
      <div v-show="showAgent2" class="component-panel">
        <AIコアコード
          key="code-2"
          :socket-id="ソケットID"
          :チャンネル="2"
          :code-ai="モデル設定.CODE_AI2"
          :input-ws-client="wsClient"
          :input-connected="wsConnected"
          @activate="showAgent2 = true; enableAgent2Button = true"
          @close="handleCloseAgent2"
        />
      </div>

      <!-- エージェント3 -->
      <div v-show="showAgent3" class="component-panel">
        <AIコアコード
          key="code-3"
          :socket-id="ソケットID"
          :チャンネル="3"
          :code-ai="モデル設定.CODE_AI3"
          :input-ws-client="wsClient"
          :input-connected="wsConnected"
          @activate="showAgent3 = true; enableAgent3Button = true"
          @close="handleCloseAgent3"
        />
      </div>

      <!-- エージェント4 -->
      <div v-show="showAgent4" class="component-panel">
        <AIコアコード
          key="code-4"
          :socket-id="ソケットID"
          :チャンネル="4"
          :code-ai="モデル設定.CODE_AI4"
          :input-ws-client="wsClient"
          :input-connected="wsConnected"
          @activate="showAgent4 = true; enableAgent4Button = true"
          @close="handleCloseAgent4"
        />
      </div>
    </div>
    <AI設定再起動
      :is-open="showModelConfig"
      @close="showModelConfig = false"
    />
  </div>
</template>

<style scoped>
.ai-core-view {
  width: 100%;
  height: calc(100vh - 100px);
  position: relative;
  background: #1a1a1a;
  overflow: hidden;
}

/* WebSocket接続状態インジケーター（マイクボタンの真上） */
.ws-status {
  position: absolute;
  top: 12px;
  right: 20px;
  background: rgba(50, 50, 50, 0.9);
  border: 2px solid #ff4444;
  border-radius: 4px;
  padding: 0 12px;
  height: 27px;
  display: flex;
  align-items: center;
  gap: 8px;
  z-index: 1000;
  font-size: 11px;
  color: #ff4444;
  transition: all 0.3s ease;
}

.ws-status.connected {
  border-color: #44ff44;
  color: #44ff44;
}

.ws-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ff4444;
  animation: pulse-red 1.5s infinite;
}

.ws-status.connected .ws-status-dot {
  background: #44ff44;
  animation: pulse-green 1.5s infinite;
}

.ws-status-text {
  font-weight: bold;
  font-family: 'Courier New', monospace;
}

@keyframes pulse-red {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(255, 68, 68, 0.7);
  }
  50% {
    box-shadow: 0 0 0 6px rgba(255, 68, 68, 0);
  }
}

@keyframes pulse-green {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(68, 255, 68, 0.7);
  }
  50% {
    box-shadow: 0 0 0 6px rgba(68, 255, 68, 0);
  }
}

/* エラーメッセージ */
.error-message {
  position: absolute;
  top: 60px;
  left: 10px;
  right: 10px;
  background: rgba(255, 68, 68, 0.95);
  color: white;
  border: 2px solid #cc0000;
  border-radius: 4px;
  padding: 12px 40px 12px 12px;
  z-index: 998;
  font-size: 12px;
  font-family: 'Courier New', monospace;
  word-wrap: break-word;
  max-width: 600px;
}

.error-close {
  position: absolute;
  top: 4px;
  right: 4px;
  background: rgba(255, 255, 255, 0.3);
  color: white;
  border: none;
  border-radius: 2px;
  width: 24px;
  height: 24px;
  cursor: pointer;
  font-size: 16px;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.error-close:hover {
  background: rgba(255, 255, 255, 0.5);
}

/* 音声・画像制御フローティングアイコン */
.floating-controls {
  position: absolute;
  top: 50px;
  right: 20px; /* 元に戻す */
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 1000;
}

/* フローティングアイコン基本スタイル・WS接続後に白ベース */
.floating-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 2px solid transparent;
  background: rgba(255, 255, 255, 0.95);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(128, 128, 128, 0.3);
}

.floating-icon img {
  width: 21px;
  height: 21px;
  object-fit: contain;
  pointer-events: none;
  filter: brightness(0); /* 黒アイコン */
}

.floating-icon:hover {
  transform: scale(1.05);
}


/* マイク→OFF時は白地に赤枠 */
.floating-icon.microphone-icon {
  border-color: #ff4444;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 2px 8px rgba(255, 68, 68, 0.3);
}

.floating-icon.microphone-icon img {
  filter: brightness(0); /* 黒アイコン */
}

.floating-icon.microphone-icon:hover {
  box-shadow: 0 4px 12px rgba(255, 68, 68, 0.4);
}

/* マイク→ON時は赤色でブリンク */
.floating-icon.microphone-icon.active {
  background: #ff4444;
  border-color: #ff4444;
  animation: pulse 2.5s infinite;
  box-shadow: 0 2px 8px rgba(255, 68, 68, 0.5);
}

.floating-icon.microphone-icon.active img {
  filter: brightness(0) invert(1); /* 白アイコン */
}

/* スピーカー→OFF時は白地に水色枠 */
.floating-icon.speaker-icon.inactive {
  border-color: #00bfff;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 2px 8px rgba(68, 255, 68, 0.3);
}

.floating-icon.speaker-icon.inactive img {
  filter: brightness(0); /* 黒アイコン */
}

.floating-icon.speaker-icon.inactive:hover {
  box-shadow: 0 4px 12px rgba(0, 191, 255, 0.4);
}

/* スピーカー→ON時は水色でブリンク */
.floating-icon.speaker-icon {
  background: #00bfff;
  border-color: #00bfff;
  box-shadow: 0 2px 8px rgba(68, 255, 68, 0.3);
}

.floating-icon.speaker-icon img {
  filter: brightness(0); /* 黒アイコン */
}

.floating-icon.speaker-icon:hover {
  box-shadow: 0 4px 12px rgba(0, 191, 255, 0.4);
}

.floating-icon.speaker-icon.active {
  animation: pulse 2.5s infinite;
}

/* カメラ（イメージ）→OFF時は暗いグレーに暗い緑枠 */
.floating-icon.camera-icon {
  border-color: #2e7d32; /* 暗い緑 */
  background: #888888; /* 暗いグレー */
  box-shadow: 0 2px 8px rgba(0, 191, 255, 0.3);
  border-radius: 0; /* フラット */
  width: 28px; /* 少し小さく */
  height: 28px; /* 少し小さく */
  margin-left: 2px; /* 中央に配置 */
}

.floating-icon.camera-icon img {
  filter: brightness(0); /* 黒アイコン */
}

.floating-icon.camera-icon:hover {
  box-shadow: 0 4px 12px rgba(68, 255, 68, 0.4);
}

/* カメラ（イメージ）→ON時は淡い緑でブリンク */
.floating-icon.camera-icon.active {
  background: #e8f5e9; /* 淡い緑 */
  border-color: #44ff44;
  animation: pulse 2.5s infinite;
  box-shadow: 0 2px 8px rgba(68, 255, 68, 0.5);
  border-radius: 0; /* フラット */
  width: 28px; /* 少し小さく */
  height: 28px; /* 少し小さく */
  margin-left: 2px; /* 中央に配置 */
}

.floating-icon.camera-icon.active img {
  filter: none; /* アイコンはそのまま */
}

/* チャットボタン→disable時は灰色背景、黒文字 */
.floating-icon.chat-icon:disabled {
  background: #cccccc;
  border-color: #cccccc;
  color: #000000;
  cursor: not-allowed;
  opacity: 0.6;
  border-radius: 0; /* フラット */
  width: 28px; /* 少し小さく */
  height: 28px; /* 少し小さく */
  margin-left: 2px; /* 中央に配置 */
  font-size: 17px;
}

/* チャットボタン→OFF時は暗いグレー背景に暗い緑枠、黒文字 */
.floating-icon.chat-icon.inactive {
  border-color: #2e7d32; /* 暗い緑 */
  background: #888888; /* 暗いグレー */
  color: #000000;
  font-weight: 900;
  font-size: 17px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0; /* フラット */
  width: 28px; /* 少し小さく */
  height: 28px; /* 少し小さく */
  margin-left: 2px; /* 中央に配置 */
}

.floating-icon.chat-icon.inactive:hover {
  box-shadow: 0 4px 12px rgba(68, 255, 68, 0.4);
}

/* チャットボタン→ON時は黒背景に緑枠、鮮やかな緑文字 */
.floating-icon.chat-icon.active {
  background: #000000;
  border-color: #44ff44;
  color: #00ff00; /* コンソール風の鮮やかな緑 */
  font-weight: 900;
  font-size: 17px;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: pulse 2.5s infinite;
  box-shadow: 0 2px 8px rgba(0, 255, 0, 0.5);
  border-radius: 0; /* フラット */
  width: 28px; /* 少し小さく */
  height: 28px; /* 少し小さく */
  margin-left: 2px; /* 中央に配置 */
}

.floating-icon.chat-icon:hover {
  box-shadow: 0 4px 12px rgba(68, 255, 68, 0.4);
}

/* エージェントボタン→disable時は灰色背景、黒文字 */
.floating-icon.agent-icon:disabled {
  background: #cccccc;
  border-color: #cccccc;
  color: #000000;
  cursor: not-allowed;
  opacity: 0.6;
  border-radius: 0; /* フラット */
  width: 28px; /* 少し小さく */
  height: 28px; /* 少し小さく */
  margin-left: 2px; /* 中央に配置 */
  font-size: 17px;
}

/* エージェントボタン→OFF時は暗いグレー背景に暗い緑枠、黒文字 */
.floating-icon.agent-icon.inactive {
  border-color: #2e7d32; /* 暗い緑 */
  background: #888888; /* 暗いグレー */
  color: #000000;
  font-weight: 900;
  font-size: 17px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0; /* フラット */
  width: 28px; /* 少し小さく */
  height: 28px; /* 少し小さく */
  margin-left: 2px; /* 中央に配置 */
}

.floating-icon.agent-icon.inactive:hover {
  box-shadow: 0 4px 12px rgba(68, 255, 68, 0.4);
}

/* エージェントボタン→ON時は黒背景に緑枠、鮮やかな緑文字 */
.floating-icon.agent-icon.active {
  background: #000000;
  border-color: #44ff44;
  color: #00ff00; /* コンソール風の鮮やかな緑 */
  font-weight: 900;
  font-size: 17px;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: pulse 2.5s infinite;
  box-shadow: 0 2px 8px rgba(0, 255, 0, 0.5);
  border-radius: 0; /* フラット */
  width: 28px; /* 少し小さく */
  height: 28px; /* 少し小さく */
  margin-left: 2px; /* 中央に配置 */
}

.floating-icon.agent-icon:hover {
  box-shadow: 0 4px 12px rgba(68, 255, 68, 0.4);
}

/* config icon */
.floating-icon.config-icon {
  background: #ffffff;
  border: 2px solid #ffffff;
  color: #000000;
  box-shadow: 0 2px 8px rgba(255, 255, 255, 0.3);
  padding: 3px;
}

.floating-icon.config-icon .icon-image {
  width: 29px;
  height: 29px;
  display: block;
  filter: brightness(0);
}

.floating-icon.config-icon:hover {
  box-shadow: 0 4px 12px rgba(255, 255, 255, 0.5);
}

.floating-icon.config-icon:disabled {
  background: #888888;
  border-color: #888888;
  box-shadow: none;
}

.floating-icon.config-icon:disabled .icon-image {
  filter: brightness(0.6);
}

/* ボタン無効時のスタイル */
.floating-icon:disabled {
  background: #808080 !important;
  border-color: #808080 !important;
  cursor: not-allowed !important;
  box-shadow: 0 2px 8px rgba(128, 128, 128, 0.3) !important;
  animation: none !important;
}

.floating-icon:disabled img {
  filter: brightness(0) invert(1) !important; /* 白アイコン */
}

.floating-icon:disabled:hover {
  transform: none !important;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
  }
}

/* 音声ビジュアライザー（WS接続中インジケーターの左側） */
.audio-visualizer-overlay {
  position: absolute;
  top: 12px;
  right: 140px;
  width: 170px;
  height: 27px;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(0, 0, 0, 0.25);
  border-radius: 4px;
  overflow: visible;
  z-index: 999;
  display: none; /* 初期は非表示 */
  align-items: flex-end;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  pointer-events: none;
  padding: 0 2px;
}

.audio-bars {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  height: 100%;
  width: 100%;
  gap: 1px;
}

.audio-bar-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  justify-content: flex-end;
  height: 100%;
  gap: 0px;
  min-width: 1px;
}

.audio-bar {
  width: 100%;
  min-height: 2px;
  height: 10%;
  transition: height 0.05s ease-out;
  border-radius: 0px;
}

.audio-bar.input-audio {
  background: #ff4444;
  order: 2;
}

.audio-bar.output-audio {
  background: #44ff44;
  order: 1;
}

/* コンポーネントグリッド - 基本設定 */
.components-grid {
  display: grid;
  gap: 16px;
  padding: 16px;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
  transition: all 0.3s ease;
}

/* レイアウト: 0枚（空） */
.layout-empty {
  grid-template-columns: 1fr;
  grid-template-rows: 1fr;
  place-items: center;
}

.layout-empty::after {
  content: 'コンポーネントが選択されていません';
  color: #666;
  font-size: 18px;
}

/* レイアウト: 1枚（全画面） */
.layout-single {
  grid-template-columns: 1fr;
  grid-template-rows: 1fr;
  padding-left: 20%;
  padding-right: 20%;
}

/* レイアウト: 2枚（左右分割） */
.layout-double {
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: 1fr;
  padding-left: 10%;
  padding-right: 10%;
  column-gap: 10%;
}

/* レイアウト: 3枚（横並び） */
.layout-triple {
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: 1fr;
}

/* レイアウト: 4枚（2×2グリッド） */
.layout-quad {
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: repeat(2, 1fr);
}

/* レイアウト: 5枚以上（3×2グリッド） */
.layout-multi {
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: repeat(2, 1fr);
}

.component-panel {
  background: #000;
  border: 1px solid #333;
  border-radius: 2px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
  transition: all 0.3s ease;
  min-height: 0;
  min-width: 0;
}

.component-panel:hover {
  border-color: #81c784; /* 淡い緑 */
  box-shadow: 0 0 20px rgba(129, 199, 132, 0.8); /* 全方向均等な影 */
}

/* レスポンシブ対応 */
@media (max-width: 1400px) {
  .layout-multi {
    grid-template-columns: repeat(2, 1fr);
    grid-template-rows: repeat(3, 1fr);
  }

  .layout-triple {
    grid-template-columns: 1fr;
    grid-template-rows: repeat(3, 1fr);
  }
}

@media (max-width: 900px) {
  .layout-double,
  .layout-triple,
  .layout-quad,
  .layout-multi {
    grid-template-columns: 1fr;
    grid-template-rows: auto;
  }

  .component-panel {
    min-height: 400px;
  }

  /* 小さい画面ではビジュアライザーを非表示 */
  .audio-visualizer-overlay {
    display: none !important;
  }
}

/* 縦長画面での調整 */
@media (max-aspect-ratio: 1/1) {
  /* 1枚表示は上下に余白 */
  .layout-single {
    padding-top: 10%;
    padding-bottom: 10%;
  }

  /* 2枚表示は上下配置 */
  .layout-double {
    grid-template-columns: 1fr;
    grid-template-rows: repeat(2, 1fr);
    padding-left: 16px;
    padding-right: 16px;
    column-gap: 16px;
    row-gap: 16px;
  }
}

/* コンポーネント内のスタイル調整 */
.component-panel :deep(.chat-container),
.component-panel :deep(.image-container),
.component-panel :deep(.agent-container) {
  width: 100%;
  height: 100%;
  border-radius: 0;
  box-shadow: none;
}
</style>


