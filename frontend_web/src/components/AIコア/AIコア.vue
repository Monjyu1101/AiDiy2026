<!--
  -*- coding: utf-8 -*-

  -------------------------------------------------------------------------
  COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
  Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
  Commercial use requires prior written consent from all copyright holders.
  See LICENSE for full terms. Thank you for keeping the rules.
  https://github.com/monjyu1101
  -------------------------------------------------------------------------
-->

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import apiClient from '@/api/client';
import AI設定再起動 from './dialog/AI設定再起動.vue';
import { AIコアWebSocket, createWebSocketUrl, type IWebSocketClient } from '@/api/websocket';
import AIコアチャット from './compornents/AIチャット.vue';
import AIコアイメージ from './compornents/AIイメージ.vue';
import AIコアコード from './compornents/AIコード.vue';
import AIコアファイル from './compornents/AIファイル.vue';
import { AudioStreamProcessor } from './AI音声処理';

// セッションID（全コンポーネント共通）
const セッションID = ref('');

// inputチャンネル（送信専用）
const inputSocket = ref<IWebSocketClient | null>(null);
// audioチャンネル
const audioSocket = ref<IWebSocketClient | null>(null);
// coreチャンネル（init/welcome/heartbeat受信）
const coreSocket = ref<IWebSocketClient | null>(null);
const 入力接続済み = ref(false);
const 音声接続済み = ref(false);
const 接続初期化中 = ref(true);

// モデル設定情報
const モデル設定 = ref({
  CHAT_AI_NAME: '',
  LIVE_AI_NAME: '',
  CODE_AI1_NAME: '',
  CODE_AI2_NAME: '',
  CODE_AI3_NAME: '',
  CODE_AI4_NAME: ''
});

const チャットモード = ref<'chat' | 'live' | 'code1' | 'code2' | 'code3' | 'code4'>('live');

// エラーメッセージ
const エラーメッセージ = ref('');
const 入力ウェルカム情報 = ref('');
const 入力ウェルカム本文 = ref('');
const AIコアビュー要素 = ref<HTMLElement | null>(null);
const ガイド要素 = ref<HTMLElement | null>(null);
const ガイドホバー中 = ref(false);

const 受信内容文字列 = (受信データ: any) => {
  const 内容 = 受信データ?.メッセージ内容 ?? 受信データ?.text ?? '';
  if (!内容) return '';
  return typeof 内容 === 'string' ? 内容 : JSON.stringify(内容);
};

const 入力ウェルカム情報表示 = computed(() => 入力ウェルカム情報.value.trim());
const 入力ウェルカム本文表示 = computed(() => 入力ウェルカム本文.value.trim());

const ガイド領域マウス移動 = (event: MouseEvent) => {
  if (!入力ウェルカム本文表示.value || !ガイド要素.value) {
    ガイドホバー中.value = false;
    return;
  }
  const rect = ガイド要素.value.getBoundingClientRect();
  const x = event.clientX;
  const y = event.clientY;
  ガイドホバー中.value = x >= rect.left && x <= rect.right && y >= rect.top && y <= rect.bottom;
};

const ガイド領域マウス離脱 = () => {
  ガイドホバー中.value = false;
};

// 各コンポーネントの表示状態（初期値は全てfalse、WebSocket接続で初期値受信後に有効化）
// ※ ボタン配置順: マイク → スピーカー → ファイル → チャット → 1 → イメージ → 2 → 3 → 4 → 設定
const イメージ表示中 = ref(false);   // イメージ
const ファイル表示中 = ref(false);    // ファイル
const チャット表示中 = ref(false);    // チャット
const エージェント1表示中 = ref(false);  // コード1
const エージェント2表示中 = ref(false);  // コード2
const エージェント3表示中 = ref(false);  // コード3
const エージェント4表示中 = ref(false);  // コード4

// レイアウト計算用フラグ（退場アニメーション完了後にfalseになる）
const イメージレイアウト = ref(false);
const ファイルレイアウト = ref(false);
const チャットレイアウト = ref(false);
const エージェント1レイアウト = ref(false);
const エージェント2レイアウト = ref(false);
const エージェント3レイアウト = ref(false);
const エージェント4レイアウト = ref(false);

// 音声・画像制御（初期値は全てfalse、WebSocket接続で初期値受信後に有効化）
const マイク有効 = ref(false);
const スピーカー有効 = ref(false);
const カメラ有効 = ref(false);
const ファイルボタン有効 = ref(false);

// チャット数カウント
const チャット数 = ref(0);
const チャットボタン有効 = ref(false);

// エージェント1～4カウント
const エージェント1数 = ref(0);
const エージェント1ボタン有効 = ref(false);
const エージェント2数 = ref(0);
const エージェント2ボタン有効 = ref(false);
const エージェント3数 = ref(0);
const エージェント3ボタン有効 = ref(false);
const エージェント4数 = ref(0);
const エージェント4ボタン有効 = ref(false);

// キャプチャ画像
const キャプチャ画像 = ref<string | null>(null);

// 自動選択ポップアップ表示フラグ
const 自動選択表示 = ref(false);

// チェックボックスパネルの表示/非表示
const モデル設定表示 = ref(false);

// 音声処理プロセッサ
let 音声処理機: AudioStreamProcessor | null = null;

// ビジュアライザー表示状態を同期
const ビジュアライザー表示同期 = () => {
  if (!音声処理機) return;
  音声処理機.updateVisualizerVisibility(マイク有効.value, スピーカー有効.value);
};

const Liveサンプルレート同期 = () => {
  if (!音声処理機) return;
  const liveAi = モデル設定.value.LIVE_AI_NAME || '';
  const provider = liveAi === 'openai_live' ? 'openai' : liveAi;
  音声処理機.setSampleRate(provider);
};

// ファイルボタンクリック時
const ファイル切替 = () => {
  ファイルボタン有効.value = !ファイルボタン有効.value;
  if (ファイルボタン有効.value) {
    ファイルレイアウト.value = true;
    ファイル表示中.value = true;
  } else {
    ファイル表示中.value = false;
    // ファイルレイアウト.valueは@after-leaveで更新
  }
};

// チャットボタンクリック時
const チャット切替 = () => {
  チャットボタン有効.value = !チャットボタン有効.value;
  if (チャットボタン有効.value) {
    チャットレイアウト.value = true;
    チャット表示中.value = true;
  } else {
    チャット表示中.value = false;
    // チャットレイアウト.valueは@after-leaveで更新
  }
};

// エージェント1ボタンクリック時
const エージェント1切替 = () => {
  エージェント1ボタン有効.value = !エージェント1ボタン有効.value;
  if (エージェント1ボタン有効.value) {
    エージェント1レイアウト.value = true;
    エージェント1表示中.value = true;
  } else {
    エージェント1表示中.value = false;
  }
};

// エージェント2ボタンクリック時
const エージェント2切替 = () => {
  エージェント2ボタン有効.value = !エージェント2ボタン有効.value;
  if (エージェント2ボタン有効.value) {
    エージェント2レイアウト.value = true;
    エージェント2表示中.value = true;
  } else {
    エージェント2表示中.value = false;
  }
};

// エージェント3ボタンクリック時
const エージェント3切替 = () => {
  エージェント3ボタン有効.value = !エージェント3ボタン有効.value;
  if (エージェント3ボタン有効.value) {
    エージェント3レイアウト.value = true;
    エージェント3表示中.value = true;
  } else {
    エージェント3表示中.value = false;
  }
};

// エージェント4ボタンクリック時
const エージェント4切替 = () => {
  エージェント4ボタン有効.value = !エージェント4ボタン有効.value;
  if (エージェント4ボタン有効.value) {
    エージェント4レイアウト.value = true;
    エージェント4表示中.value = true;
  } else {
    エージェント4表示中.value = false;
  }
};

// イメージボタンクリック時
const カメラ切替 = () => {
  if (カメラ有効.value) {
    カメラ有効.value = false;
    イメージ表示中.value = false;
    自動選択表示.value = false;
    キャプチャ画像.value = null;
    // イメージレイアウト.valueは@after-leaveで更新
    return;
  }
  自動選択表示.value = false;
  nextTick(() => {
    自動選択表示.value = true;
  });
  イメージレイアウト.value = true;
  イメージ表示中.value = true;
  カメラ有効.value = true;
};

// イメージ選択がキャンセルされた時
const イメージ選択キャンセル = () => {
  イメージ表示中.value = false;
  カメラ有効.value = false;
  自動選択表示.value = false;
  キャプチャ画像.value = null;
};

// 各コンポーネントを閉じるハンドラー
const ファイル閉じる = () => {
  ファイル表示中.value = false;
  ファイルボタン有効.value = false;
};

const チャット閉じる = () => {
  チャット表示中.value = false;
  チャットボタン有効.value = false;
};

const イメージ閉じる = () => {
  イメージ表示中.value = false;
  カメラ有効.value = false;
  自動選択表示.value = false;
  キャプチャ画像.value = null;
};

const エージェント1閉じる = () => {
  エージェント1表示中.value = false;
  エージェント1ボタン有効.value = false; // ボタンもオフに
};

const エージェント2閉じる = () => {
  エージェント2表示中.value = false;
  エージェント2ボタン有効.value = false; // ボタンもオフに
};

const エージェント3閉じる = () => {
  エージェント3表示中.value = false;
  エージェント3ボタン有効.value = false; // ボタンもオフに
};

const エージェント4閉じる = () => {
  エージェント4表示中.value = false;
  エージェント4ボタン有効.value = false; // ボタンもオフに
};

// 退場アニメーション完了後のハンドラー（レイアウト更新）
const ファイル退場後 = () => { ファイルレイアウト.value = false; };
const チャット退場後 = () => { チャットレイアウト.value = false; };
const イメージ退場後 = () => { イメージレイアウト.value = false; };
const エージェント1退場後 = () => { エージェント1レイアウト.value = false; };
const エージェント2退場後 = () => { エージェント2レイアウト.value = false; };
const エージェント3退場後 = () => { エージェント3レイアウト.value = false; };
const エージェント4退場後 = () => { エージェント4レイアウト.value = false; };

// イメージチェックボックスの変更を監視
const イメージチェックボックス変更 = async (newValue: boolean, oldValue: boolean) => {
  // OFFからONになった時のみ選択ポップアップを表示
  if (newValue && !oldValue) {
    自動選択表示.value = true;
  }
};

// WebSocket接続を初期化
const WebSocket初期化 = async (既存セッションID?: string) => {
  try {
    接続初期化中.value = true;
    const wsUrl = createWebSocketUrl('/core/ws/AIコア');
    console.log('[AIコア] WebSocket接続開始:', wsUrl, 'セッションID:', 既存セッションID);

    入力ウェルカム情報.value = '';
    入力ウェルカム本文.value = '';

    // coreチャンネルを先に接続（init・制御メッセージ・welcome を一括受信）
    if (coreSocket.value) {
      try { coreSocket.value.disconnect(); } catch (e) { /* no-op */ }
      coreSocket.value = null;
    }
    const wsCoreWs = new AIコアWebSocket(wsUrl, 既存セッションID, 'core');

    wsCoreWs.on('init', (message) => {
      console.log('[AIコア] 初期化完了:', message.セッションID);
      if (message.セッションID) {
        セッションID.value = message.セッションID;
      }

      const 初期データ = message.メッセージ内容 || {};

      if (初期データ.モデル設定) {
        モデル設定.value = {
          CHAT_AI_NAME: 初期データ.モデル設定.CHAT_AI_NAME || '',
          LIVE_AI_NAME: 初期データ.モデル設定.LIVE_AI_NAME || '',
          CODE_AI1_NAME: 初期データ.モデル設定.CODE_AI1_NAME || '',
          CODE_AI2_NAME: 初期データ.モデル設定.CODE_AI2_NAME || '',
          CODE_AI3_NAME: 初期データ.モデル設定.CODE_AI3_NAME || '',
          CODE_AI4_NAME: 初期データ.モデル設定.CODE_AI4_NAME || ''
        };
        console.log('[AIコア] モデル設定:', モデル設定.value);
      }

      Liveサンプルレート同期();

      if (初期データ.ボタン) {
        マイク有効.value = 初期データ.ボタン.マイク || false;
        スピーカー有効.value = 初期データ.ボタン.スピーカー ?? true;
        ファイルボタン有効.value = 初期データ.ボタン.ファイル || false;
        チャットボタン有効.value = 初期データ.ボタン.チャット ?? true;
        エージェント1ボタン有効.value = 初期データ.ボタン.エージェント1 || false;
        カメラ有効.value = false;
        エージェント2ボタン有効.value = 初期データ.ボタン.エージェント2 || false;
        エージェント3ボタン有効.value = 初期データ.ボタン.エージェント3 || false;
        エージェント4ボタン有効.value = 初期データ.ボタン.エージェント4 || false;
        チャットモード.value = 初期データ.ボタン.チャットモード || 'live';
        console.log('[AIコア] ボタン状態を初期化:', 初期データ.ボタン);
      } else {
        チャットモード.value = 'live';
      }

      イメージレイアウト.value = カメラ有効.value;
      イメージ表示中.value = カメラ有効.value;
      ビジュアライザー表示同期();
      console.log('[AIコア] WebSocket初期化完了（音声WS待機中）');

      nextTick(() => {
        ファイルレイアウト.value = ファイルボタン有効.value;
        ファイル表示中.value = ファイルボタン有効.value;
        チャットレイアウト.value = チャットボタン有効.value;
        チャット表示中.value = チャットボタン有効.value;
        エージェント1レイアウト.value = エージェント1ボタン有効.value;
        エージェント1表示中.value = エージェント1ボタン有効.value;
        エージェント2レイアウト.value = エージェント2ボタン有効.value;
        エージェント2表示中.value = エージェント2ボタン有効.value;
        エージェント3レイアウト.value = エージェント3ボタン有効.value;
        エージェント3表示中.value = エージェント3ボタン有効.value;
        エージェント4レイアウト.value = エージェント4ボタン有効.value;
        エージェント4表示中.value = エージェント4ボタン有効.value;
      });
    });

    wsCoreWs.on('welcome_info', (message) => {
      const 内容 = 受信内容文字列(message);
      if (!内容) return;
      入力ウェルカム情報.value = 内容;
    });
    wsCoreWs.on('welcome_text', (message) => {
      const 内容 = 受信内容文字列(message);
      if (!内容) return;
      入力ウェルカム本文.value = 内容;
    });
    wsCoreWs.on('streaming_started', (message) => {
      console.log('[AIコア] ストリーミング開始:', message);
    });
    wsCoreWs.on('heartbeat', (message) => {
      console.log('[AIコア] ハートビート:', message.count);
    });
    wsCoreWs.on('channel_registered', (message) => {
      console.log('[AIコア] チャンネル登録確認:', message);
    });
    wsCoreWs.on('channel_unregistered', (message) => {
      console.log('[AIコア] チャンネル解除確認:', message);
    });
    wsCoreWs.on('error', (message) => {
      console.error('[AIコア] エラー:', message.error);
    });

    // coreチャンネル接続でセッションIDを確立
    console.log('[AIコア] coreチャンネル接続開始');
    const 取得セッションID = await wsCoreWs.connect();
    セッションID.value = 取得セッションID;
    coreSocket.value = wsCoreWs;
    console.log('[AIコア] coreチャンネル接続完了 セッションID:', 取得セッションID);

    // inputチャンネルを接続（送信専用・ハンドラなし）
    inputSocket.value = new AIコアWebSocket(wsUrl, 取得セッションID, 'input');
    inputSocket.value.connect().catch((e) => console.error('[AIコア] inputチャンネル接続エラー:', e));

    // 音声専用WebSocket接続（チャンネルaudio）
    if (!audioSocket.value || !audioSocket.value.isConnected()) {
      await 音声WebSocket初期化(取得セッションID);
    } else {
      音声接続済み.value = true;
    }
    入力接続済み.value = true;
    接続初期化中.value = false;
    console.log('[AIコア] WebSocket接続確立完了（main + audio）');
    状態保存();
    if (マイク有効.value) {
      await マイク状態適用(true, false);
    }

    return 取得セッションID;
  } catch (error) {
    console.error('[AIコア] WebSocket接続エラー:', error);
    入力接続済み.value = false;
    音声接続済み.value = false;
    接続初期化中.value = true;
    throw error;
  }
};

// 音声専用WebSocket接続を初期化
const 音声WebSocket初期化 = async (既存セッションID: string) => {
  // 既存の音声WSがあれば張り直し
  if (audioSocket.value) {
    try {
      audioSocket.value.disconnect();
    } catch (e) {
      // no-op
    }
    audioSocket.value = null;
  }
  音声接続済み.value = false;

  const wsUrl = createWebSocketUrl('/core/ws/AIコア');
  audioSocket.value = new AIコアWebSocket(wsUrl, 既存セッションID, 'audio');

  audioSocket.value.on('output_audio', (message) => {
    console.log('[AIコア] 音声出力受信(audio)');
    if (音声処理機) {
      音声処理機.handleAudioMessage(message);
    }
  });

  audioSocket.value.on('cancel_audio', () => {
    console.log('[AIコア] 音声キャンセル(audio)');
    if (音声処理機) {
      音声処理機.cancelAudioOutput();
    }
  });

  await audioSocket.value.connect();
  音声接続済み.value = true;
  console.log('[AIコア] 音声WebSocket接続完了(audio)');
};

// 音声WS接続を保証（切断時の再接続用）
const 音声WebSocket接続確認 = async (): Promise<boolean> => {
  if (!セッションID.value) return false;
  if (audioSocket.value && audioSocket.value.isConnected()) {
    音声接続済み.value = true;
    return true;
  }
  try {
    await 音声WebSocket初期化(セッションID.value);
    return !!(audioSocket.value && audioSocket.value.isConnected());
  } catch (e) {
    音声接続済み.value = false;
    return false;
  }
};

const マイク状態適用 = async (newValue: boolean, oldValue: boolean) => {
  if (!音声処理機) return;

  // ビジュアライザー表示状態を更新
  音声処理機.updateVisualizerVisibility(newValue, スピーカー有効.value);

  if (newValue && !oldValue) {
    // 音声専用WSの接続を保証
    const 音声接続OK = await 音声WebSocket接続確認();
    if (!音声接続OK) {
      エラーメッセージ.value = '音声WebSocket(audio)に接続できません。再読み込みしてください。';
      マイク有効.value = false;
      return;
    }

    // マイクON
    console.log('[AIコア] マイク起動');
    const result = await 音声処理機.startMicrophone();
    if (!result.success) {
      console.error('[AIコア] マイク起動失敗:', result.error);
      エラーメッセージ.value = result.error || 'マイクの起動に失敗しました。';
      マイク有効.value = false;
    }
  } else if (!newValue && oldValue) {
    // マイクOFF
    console.log('[AIコア] マイク停止');
    音声処理機.stopMicrophone();
  }
};

// 初期化処理
onMounted(async () => {
  const URLのセッションID = new URLSearchParams(window.location.search).get('セッションID') || '';
  console.log('[AIコア] ========================================');
  console.log('[AIコア] 初期化開始');
  console.log('[AIコア] URLからのセッションID:', URLのセッションID);
  console.log('[AIコア] ========================================');

  // 音声処理プロセッサを初期化
  音声処理機 = new AudioStreamProcessor(audioSocket, セッションID, スピーカー有効);
  音声処理機.setupOutputAudio();

  // ビジュアライザーセットアップ（DOM確実に準備されるまで待つ）
  setTimeout(() => {
    console.log('[AIコア] ビジュアライザー要素を検索中...');
    const audioBarsElement = document.getElementById('audioBars');
    const overlayElement = document.getElementById('audioVisualizerOverlay');
    console.log('[AIコア] ビジュアライザー要素:', { audioBarsElement, overlayElement });

    if (音声処理機 && audioBarsElement && overlayElement) {
      音声処理機.setupAudioVisualizer(audioBarsElement, overlayElement);
      console.log('[AIコア] ビジュアライザーセットアップ完了');
      ビジュアライザー表示同期();
    } else {
      console.error('[AIコア] ビジュアライザー要素が見つかりません', {
        音声処理機: !!音声処理機,
        audioBarsElement: !!audioBarsElement,
        overlayElement: !!overlayElement
      });
    }
  }, 500);

  try {
    // REST APIで初期化（セッションIDのみ取得）
    const response = await apiClient.post('/core/AIコア/初期化', {
      セッションID: URLのセッションID || ''
    });

    if (response.data.status === 'OK') {
      const data = response.data.data;
      セッションID.value = data.セッションID;

      if (!URLのセッションID) {
        const newUrl = `${window.location.pathname}?セッションID=${セッションID.value}`;
        window.location.href = newUrl;
        return;
      }
    }

    // WebSocket接続を確立（RESTで取得したセッションIDを使用）
    console.log('[AIコア] WebSocket接続を開始...');
    const 確立済みセッションID = await WebSocket初期化(セッションID.value || URLのセッションID);
    console.log('[AIコア] ========================================');
    console.log('[AIコア] ✅ 初期化完了');
    console.log('[AIコア] セッションID:', 確立済みセッションID);
    console.log('[AIコア] 入力接続済み:', 入力接続済み.value);
    console.log('[AIコア] ========================================');
  } catch (error) {
    console.error('[AIコア] ========================================');
    console.error('[AIコア] ❌ 初期化エラー:', error);
    console.error('[AIコア] ========================================');
    エラーメッセージ.value = `初期化失敗: ${error}`;
  }
});

// コンポーネント破棄時にWebSocket接続を切断
onBeforeUnmount(() => {
  // 音声処理のクリーンアップ
  if (音声処理機) {
    音声処理機.cleanup();
    音声処理機 = null;
  }

  if (inputSocket.value) {
    console.log('[AIコア] WebSocket接続を切断します');
    inputSocket.value.disconnect();
    inputSocket.value = null;
  }
  if (coreSocket.value) {
    coreSocket.value.disconnect();
    coreSocket.value = null;
  }
  if (audioSocket.value) {
    console.log('[AIコア] 音声WebSocket接続を切断します');
    audioSocket.value.disconnect();
    audioSocket.value = null;
  }
  入力接続済み.value = false;
  音声接続済み.value = false;
  接続初期化中.value = true;
});

// ボタン状態が変わったら保存
const 状態保存 = async () => {
  if (!セッションID.value) return;

  const ボタン = {
    // ボタン配置順: マイク → スピーカー → ファイル → チャット → 1 → イメージ → 2 → 3 → 4
    マイク: マイク有効.value,
    スピーカー: スピーカー有効.value,
    ファイル: ファイルボタン有効.value,
    チャット: チャットボタン有効.value,
    エージェント1: エージェント1ボタン有効.value,
    イメージ: カメラ有効.value,
    エージェント2: エージェント2ボタン有効.value,
    エージェント3: エージェント3ボタン有効.value,
    エージェント4: エージェント4ボタン有効.value,
    チャットモード: チャットモード.value
  };

  try {
    if (inputSocket.value && 入力接続済み.value) {
      inputSocket.value.updateState(ボタン);
      console.log('[AIコア] 状態更新 (WebSocket):', { ボタン });
    }
  } catch (error) {
    console.error('[AIコア] 状態保存エラー:', error);
  }
};

// チャット表示中等の監視は不要（ボタンで直接制御するため削除）
// イメージだけ個別に監視（キャプチャ選択が必要なため）
watch(イメージ表示中, async (newValue, oldValue) => {
  if (newValue && !oldValue) {
    // OFFからONになった時はキャプチャ選択を促す
    await イメージチェックボックス変更(newValue, oldValue);
  }
  状態保存();
});

watch([マイク有効, スピーカー有効, カメラ有効], () => {
  if (!カメラ有効.value) {
    イメージ表示中.value = false;
    // イメージレイアウト.valueは@after-leaveで更新
    キャプチャ画像.value = null;
  } else {
    イメージレイアウト.value = true;
    イメージ表示中.value = true;
  }
  状態保存();
});

watch(() => モデル設定.value.LIVE_AI_NAME, () => {
  Liveサンプルレート同期();
});

// マイクボタンの状態変化を監視
watch(マイク有効, async (newValue, oldValue) => {
  if (接続初期化中.value) return;
  await マイク状態適用(newValue, oldValue);
});

// スピーカーボタンの状態変化を監視
watch(スピーカー有効, (newValue, oldValue) => {
  if (!音声処理機) return;

  // ビジュアライザー表示状態を更新
  音声処理機.updateVisualizerVisibility(マイク有効.value, newValue);

  // 状態を保存
  状態保存();
});

// ファイルボタンの状態変化を監視
watch(ファイルボタン有効, () => {
  状態保存();
});

// チャットボタンの状態変化を監視
watch(チャットボタン有効, () => {
  状態保存();
});

// エージェント1～4ボタンの状態変化を監視
watch(エージェント1ボタン有効, () => {
  状態保存();
});

watch(エージェント2ボタン有効, () => {
  状態保存();
});

watch(エージェント3ボタン有効, () => {
  状態保存();
});

watch(エージェント4ボタン有効, () => {
  状態保存();
});

watch(チャットモード, () => {
  状態保存();
});

// 表示中のパネル数をカウント（レイアウト計算用フラグを使用）
const 表示パネル数 = computed(() => {
  let count = 0;
  // ボタン配置順: マイク → スピーカー → ファイル → チャット → 1 → イメージ → 2 → 3 → 4
  if (ファイルレイアウト.value) count++;
  if (チャットレイアウト.value) count++;
  if (エージェント1レイアウト.value) count++;
  if (イメージレイアウト.value) count++;
  if (エージェント2レイアウト.value) count++;
  if (エージェント3レイアウト.value) count++;
  if (エージェント4レイアウト.value) count++;
  return count;
});

// パネル数に応じたレイアウトクラス
const グリッドレイアウトクラス = computed(() => {
  const count = 表示パネル数.value;
  if (count === 0) return 'layout-empty';
  if (count === 1) return 'layout-single';
  if (count === 2) return 'layout-double';
  if (count === 3) return 'layout-triple';
  if (count === 4) return 'layout-quad';
  return 'layout-multi'; // 5枚以上
});
</script>

<template>
  <!-- WebSocket接続状態インジケーター（fixedレイヤー） -->
  <div class="ws-status" :class="{ connected: 入力接続済み }">
    <span class="ws-status-dot"></span>
    <span class="ws-status-text">{{ 入力接続済み ? '接続中' : '切断中' }}</span>
  </div>

  <!-- 音声ビジュアライザー（fixedレイヤー） -->
  <div id="audioVisualizerOverlay" class="audio-visualizer-overlay">
    <div id="audioBars" class="audio-bars"></div>
  </div>

  <!-- 音声・画像制御フローティングアイコン（fixedレイヤー） -->
  <div class="floating-controls">
    <button
      class="floating-icon microphone-icon"
      :class="{ active: マイク有効 }"
      :disabled="!入力接続済み || !音声接続済み"
      @click="マイク有効 = !マイク有効"
      title="マイク"
    >
      <img src="/icons/microphone.png" alt="マイク" />
    </button>
    <button
      class="floating-icon speaker-icon"
      :class="{ inactive: !スピーカー有効, active: スピーカー有効 }"
      :disabled="!入力接続済み || !音声接続済み"
      @click="スピーカー有効 = !スピーカー有効"
      title="スピーカー"
    >
      <img src="/icons/speaker.png" alt="スピーカー" />
    </button>
    <button
      class="floating-icon file-icon"
      :class="{ inactive: !ファイルボタン有効, active: ファイルボタン有効 }"
      @click="ファイル切替"
      title="ファイル"
    >
      <img src="/icons/folder.png" alt="ファイル" />
    </button>
    <button
      class="floating-icon chat-icon"
      :class="{ inactive: !チャットボタン有効, active: チャットボタン有効 }"
      :disabled="!入力接続済み"
      @click="チャット切替"
      title="チャット"
    >
      {{ チャット数 }}
    </button>
    <button
      class="floating-icon agent-icon"
      :class="{ inactive: !エージェント1ボタン有効, active: エージェント1ボタン有効 }"
      :disabled="!入力接続済み"
      @click="エージェント1切替"
      title="コード1"
    >
      1
    </button>
    <button
      class="floating-icon camera-icon"
      :class="{ active: カメラ有効 }"
      :disabled="!入力接続済み"
      @click="カメラ切替"
      title="イメージ"
    >
      <img src="/icons/camera.png" alt="イメージ" />
    </button>
    <button
      class="floating-icon agent-icon"
      :class="{ inactive: !エージェント2ボタン有効, active: エージェント2ボタン有効 }"
      :disabled="!入力接続済み"
      @click="エージェント2切替"
      title="コード2"
    >
      2
    </button>
    <button
      class="floating-icon agent-icon"
      :class="{ inactive: !エージェント3ボタン有効, active: エージェント3ボタン有効 }"
      :disabled="!入力接続済み"
      @click="エージェント3切替"
      title="コード3"
    >
      3
    </button>
    <button
      class="floating-icon agent-icon"
      :class="{ inactive: !エージェント4ボタン有効, active: エージェント4ボタン有効 }"
      :disabled="!入力接続済み"
      @click="エージェント4切替"
      title="コード4"
    >
      4
    </button>
    <button
      class="floating-icon config-icon"
      :disabled="!入力接続済み"
      @click="モデル設定表示 = true"
      title="モデル設定"
    >
      <img src="/icons/setting.png" alt="設定" class="icon-image" />
    </button>
  </div>

  <div
    ref="AIコアビュー要素"
    class="ai-core-view"
    @mousemove="ガイド領域マウス移動"
    @mouseleave="ガイド領域マウス離脱"
  >
    <!-- エラーメッセージ表示 -->
    <div v-if="エラーメッセージ" class="error-message">
      <button class="error-close" @click="エラーメッセージ = ''">×</button>
      <strong>エラー:</strong> {{ エラーメッセージ }}
    </div>
    <div
      v-if="入力ウェルカム情報表示 || 入力ウェルカム本文表示"
      ref="ガイド要素"
      :class="['core-guide-overlay', { 'is-hover': ガイドホバー中 }]"
    >
      <div v-if="入力ウェルカム情報表示" class="core-guide-info">{{ 入力ウェルカム情報表示 }}</div>
      <pre v-if="入力ウェルカム本文表示" class="core-guide-text">{{ 入力ウェルカム本文表示 }}</pre>
    </div>

    <!-- コンポーネントグリッド -->
    <div class="components-grid" :class="グリッドレイアウトクラス">
      <!-- ファイル -->
      <Transition name="panel-expand" @after-leave="ファイル退場後">
      <div v-show="ファイル表示中" class="component-panel">
        <AIコアファイル
          :セッションID="セッションID"
          :active="ファイル表示中"
          :ws-connected="入力接続済み"
          :ws-client="inputSocket ?? null"
          @close="ファイル閉じる"
        />
      </div>
      </Transition>

      <!-- チャット -->
      <Transition name="panel-expand" @after-leave="チャット退場後">
      <div v-show="チャット表示中" class="component-panel">
        <AIコアチャット
          :セッションID="セッションID"
          チャンネル="0"
          :chat-ai="モデル設定.CHAT_AI_NAME"
          :live-ai="モデル設定.LIVE_AI_NAME"
          :chat-mode="チャットモード"
          :input-ws-client="inputSocket"
          :input-connected="入力接続済み"
          @mode-change="チャットモード = $event"
          @activate="チャット表示中 = true; チャットレイアウト = true; チャットボタン有効 = true"
          @close="チャット閉じる"
        />
      </div>
      </Transition>

      <!-- エージェント1 -->
      <Transition name="panel-expand" @after-leave="エージェント1退場後">
      <div v-show="エージェント1表示中" class="component-panel">
        <AIコアコード
          key="code-1"
          :セッションID="セッションID"
          チャンネル="1"
          :code-ai="モデル設定.CODE_AI1_NAME"
          :input-ws-client="inputSocket"
          :input-connected="入力接続済み"
          @activate="エージェント1表示中 = true; エージェント1レイアウト = true; エージェント1ボタン有効 = true"
          @close="エージェント1閉じる"
        />
      </div>
      </Transition>

      <!-- イメージ -->
      <Transition name="panel-expand" @after-leave="イメージ退場後">
      <div v-show="イメージ表示中" class="component-panel">
        <AIコアイメージ
          :auto-show-selection="自動選択表示"
          :セッションID="セッションID"
          :active="イメージ表示中"
          :ws-connected="入力接続済み"
          :ws-client="inputSocket ?? null"
          チャンネル="input"
          @selection-cancel="イメージ選択キャンセル"
          @selection-complete="自動選択表示 = false"
          @close="イメージ閉じる"
        />
      </div>
      </Transition>

      <!-- エージェント2 -->
      <Transition name="panel-expand" @after-leave="エージェント2退場後">
      <div v-show="エージェント2表示中" class="component-panel">
        <AIコアコード
          key="code-2"
          :セッションID="セッションID"
          チャンネル="2"
          :code-ai="モデル設定.CODE_AI2_NAME"
          :input-ws-client="inputSocket"
          :input-connected="入力接続済み"
          @activate="エージェント2表示中 = true; エージェント2レイアウト = true; エージェント2ボタン有効 = true"
          @close="エージェント2閉じる"
        />
      </div>
      </Transition>

      <!-- エージェント3 -->
      <Transition name="panel-expand" @after-leave="エージェント3退場後">
      <div v-show="エージェント3表示中" class="component-panel">
        <AIコアコード
          key="code-3"
          :セッションID="セッションID"
          チャンネル="3"
          :code-ai="モデル設定.CODE_AI3_NAME"
          :input-ws-client="inputSocket"
          :input-connected="入力接続済み"
          @activate="エージェント3表示中 = true; エージェント3レイアウト = true; エージェント3ボタン有効 = true"
          @close="エージェント3閉じる"
        />
      </div>
      </Transition>

      <!-- エージェント4 -->
      <Transition name="panel-expand" @after-leave="エージェント4退場後">
      <div v-show="エージェント4表示中" class="component-panel">
        <AIコアコード
          key="code-4"
          :セッションID="セッションID"
          チャンネル="4"
          :code-ai="モデル設定.CODE_AI4_NAME"
          :input-ws-client="inputSocket"
          :input-connected="入力接続済み"
          @activate="エージェント4表示中 = true; エージェント4レイアウト = true; エージェント4ボタン有効 = true"
          @close="エージェント4閉じる"
        />
      </div>
      </Transition>

    </div>
    <AI設定再起動
      :is-open="モデル設定表示"
      @close="モデル設定表示 = false"
    />
  </div>
</template>

<style scoped>
.ai-core-view {
  width: 100%;
  height: calc(100vh - 100px);
  position: relative;
  background: #1a1a1a;
  overflow-y: auto;
  overflow-x: hidden;
}

/* 固定UI要素の位置・サイズの共通変数 */
.ws-status,
.audio-visualizer-overlay,
.floating-controls {
  --ws-top: 112px;
  --ws-right: 20px;
  --ws-height: 27px;
  --status-block-gap: 6px;
  --visualizer-height: 27px;
}

/* WebSocket接続状態インジケーター（マイクボタンの真上） */
.ws-status {
  position: fixed;
  top: var(--ws-top);
  right: var(--ws-right);
  background: rgba(50, 50, 50, 0.9);
  border: 2px solid #ff4444;
  border-radius: 4px;
  padding: 0 12px;
  height: var(--ws-height);
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

.core-guide-overlay {
  position: absolute;
  top: 12px;
  left: 16px;
  width: 30vw;
  max-width: 520px;
  min-width: 220px;
  height: calc(100% - 24px);
  overflow: auto;
  z-index: 1;
  pointer-events: none;
  user-select: none;
  direction: rtl; /* 縦スクロールバーを左側へ */
  font-family: 'Courier New', monospace;
  font-size: 10px;
  line-height: 1.35;
}

.core-guide-overlay::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(to left, rgba(26, 26, 26, 0.95) 0%, rgba(26, 26, 26, 0) 13%),
    linear-gradient(to top, rgba(26, 26, 26, 0.95) 0%, rgba(26, 26, 26, 0) 16%);
  z-index: 2;
}

.core-guide-overlay::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.core-guide-overlay::-webkit-scrollbar-track {
  background: rgba(26, 26, 26, 0.35);
}

.core-guide-overlay::-webkit-scrollbar-thumb {
  background: rgba(196, 210, 255, 0.35);
  border-radius: 3px;
}

.core-guide-info {
  margin: 0;
  font-size: 15px;
  line-height: 1.3;
  color: #ffffff;
  text-shadow: none;
  white-space: pre-wrap;
  word-break: break-word;
  direction: ltr;
  text-align: left;
  position: relative;
  z-index: 1;
}

.core-guide-text {
  margin: 21px 0 0;
  color: rgba(216, 225, 255, 0.22);
  white-space: pre-wrap;
  word-break: break-word;
  opacity: 1;
  filter: blur(0.6px);
  text-shadow: 0 0 2px rgba(216, 225, 255, 0.25);
  transition: color 0.45s ease, filter 0.45s ease, text-shadow 0.45s ease;
  direction: ltr;
  text-align: left;
  position: relative;
  z-index: 1;
}

.core-guide-overlay.is-hover .core-guide-text {
  color: #ffffff;
  filter: blur(0);
  text-shadow: 0 0 10px rgba(255, 255, 255, 0.65);
}

/* 音声・画像制御フローティングアイコン */
.floating-controls {
  position: fixed;
  top: calc(var(--ws-top) + var(--ws-height) + var(--visualizer-height) + (var(--status-block-gap) * 2));
  right: var(--ws-right);
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

/* イメージ→OFF時は灰色背景に緑枠、黒アイコン */
.floating-icon.camera-icon {
  border-color: #2e7d32;
  background: #888888;
  box-shadow: 0 2px 8px rgba(68, 255, 68, 0.3);
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

/* イメージ→ON時は黒背景に緑枠ブリンク、白アイコン */
.floating-icon.camera-icon.active {
  background: #000000;
  border-color: #44ff44;
  animation: pulse 2.5s infinite;
  box-shadow: 0 2px 8px rgba(68, 255, 68, 0.5);
  border-radius: 0; /* フラット */
  width: 28px; /* 少し小さく */
  height: 28px; /* 少し小さく */
  margin-left: 2px; /* 中央に配置 */
}

.floating-icon.camera-icon.active img {
  filter: brightness(0) invert(1); /* 白アイコン */
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

/* ファイルボタン共通: 四角 */
.floating-icon.file-icon {
  border-radius: 2px;
}

/* ファイルボタン→OFF時は灰色背景に緑枠、黒アイコン */
.floating-icon.file-icon.inactive {
  border-color: #2e7d32;
  background: #888888;
  box-shadow: 0 2px 8px rgba(68, 255, 68, 0.3);
}

.floating-icon.file-icon.inactive img {
  width: 21px;
  height: 21px;
  object-fit: contain;
  mix-blend-mode: multiply; /* 白背景を灰色に溶け込ませ黒アイコンだけ残す */
}

.floating-icon.file-icon.inactive:hover {
  box-shadow: 0 4px 12px rgba(68, 255, 68, 0.4);
}

/* ファイルボタン→ON時は黒背景に緑枠ブリンク、白アイコン */
.floating-icon.file-icon.active {
  background: #000000;
  border-color: #44ff44;
  animation: pulse 2.5s infinite;
  box-shadow: 0 2px 8px rgba(68, 255, 68, 0.5);
}

.floating-icon.file-icon.active img {
  width: 21px;
  height: 21px;
  object-fit: contain;
  filter: invert(1); /* 白背景→黒、黒アイコン→白 */
}

.floating-icon.file-icon:hover {
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

/* 音声ビジュアライザー（WS接続中インジケーターの直下） */
.audio-visualizer-overlay {
  position: fixed;
  top: calc(var(--ws-top) + var(--ws-height) + var(--status-block-gap));
  right: var(--ws-right);
  width: 170px;
  height: var(--visualizer-height);
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(0, 0, 0, 0.25);
  border-radius: 4px;
  overflow: visible;
  z-index: 999;
  display: none;
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
  gap: 18px;
  padding: 18px;
  width: 100%;
  height: 100%;
  min-height: 100%;
  box-sizing: border-box;
  transition: all 0.3s ease;
  position: relative;
  z-index: 2;
  justify-items: stretch;
  align-items: stretch;
  align-content: stretch;
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
  grid-template-rows: minmax(0, 1fr);
  padding-top: 40px;
  padding-bottom: 40px;
  padding-left: 20%;
  padding-right: 20%;
}

/* レイアウト: 2枚（左右分割） */
.layout-double {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  grid-template-rows: minmax(0, 1fr);
  padding-top: 40px;
  padding-bottom: 40px;
  padding-left: 13%;
  padding-right: 13%;
  column-gap: 4%;
}

/* レイアウト: 3枚（横並び） */
.layout-triple {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  grid-template-rows: minmax(0, 1fr);
  padding-top: 40px;
  padding-bottom: 40px;
}

/* レイアウト: 4枚（2×2グリッド） */
.layout-quad {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  grid-template-rows: repeat(2, minmax(0, 1fr));
}

/* レイアウト: 5枚以上（3×2グリッド） */
.layout-multi {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  grid-template-rows: repeat(2, minmax(0, 1fr));
}

.component-panel {
  background: #000;
  border: 1px solid #333;
  border-radius: 2px;
  overflow: hidden;
  position: relative;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
  transition: all 0.3s ease;
  width: 100%;
  height: 100%;
  min-width: 0;
  min-height: 0;
}

.component-panel:hover {
  border-color: #81c784; /* 淡い緑 */
  box-shadow: 0 0 20px rgba(129, 199, 132, 0.8); /* 全方向均等な影 */
}

/* レスポンシブ対応 */
@media (max-width: 1400px) {
  .layout-multi {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    grid-template-rows: repeat(3, minmax(0, 1fr));
  }

  .layout-triple {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    grid-template-rows: minmax(0, 1fr);
  }
}

@media (max-width: 900px) {
  .ws-status,
  .audio-visualizer-overlay,
  .floating-controls {
    --ws-height: 24px;
    --status-block-gap: 4px;
  }

  .layout-double,
  .layout-triple,
  .layout-quad,
  .layout-multi {
    grid-template-columns: 1fr;
    grid-template-rows: repeat(auto-fit, minmax(320px, 1fr));
  }

  .component-panel {
    width: 100%;
    height: 100%;
    min-height: 320px;
  }

  /* 小さい画面ではビジュアライザーとWS状態を小さく */
  .audio-visualizer-overlay {
    width: 120px;
  }

  .ws-status {
    font-size: 9px;
    padding: 0 8px;
  }

  .floating-controls {
    gap: 6px;
  }

  .floating-icon {
    width: 28px;
    height: 28px;
  }

  .floating-icon img {
    width: 18px;
    height: 18px;
  }
}

/* 縦長画面での調整 */
@media (max-aspect-ratio: 1/1) {
  .layout-single {
    padding-left: 16px;
    padding-right: 16px;
  }

  /* 2枚表示は上下配置 */
  .layout-double {
    grid-template-columns: 1fr;
    grid-template-rows: repeat(2, minmax(0, 1fr));
    padding-left: 16px;
    padding-right: 16px;
    row-gap: 16px;
  }

  /* 固定要素は常に表示 */
  .ws-status,
  .floating-controls {
    display: flex !important;
  }
}

/* コンポーネント内のスタイル調整 */
.component-panel :deep(.chat-container),
.component-panel :deep(.file-container),
.component-panel :deep(.image-container),
.component-panel :deep(.agent-container) {
  width: 100%;
  height: 100%;
  border-radius: 0;
  box-shadow: none;
}

/* パネル展開アニメーション（狭い→広がる） */
.panel-expand-enter-active {
  transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.3s ease;
  transform-origin: center center;
}
.panel-expand-leave-active {
  transition: opacity 0.3s ease;
  pointer-events: none;
}
.panel-expand-enter-from {
  transform: scaleX(0.5) scaleY(0.55);
  opacity: 0.2;
}
.panel-expand-enter-to {
  transform: scaleX(1) scaleY(1);
  opacity: 1;
}
.panel-expand-leave-from {
  opacity: 1;
}
.panel-expand-leave-to {
  opacity: 0;
}
</style>


