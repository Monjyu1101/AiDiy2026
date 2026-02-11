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
import { ref, onMounted, onBeforeUnmount, nextTick, computed, watch } from 'vue';
import { AIコアWebSocket, createWebSocketUrl, type IWebSocketClient } from '@/api/websocket';

// Props
const プロパティ = defineProps<{
  セッションID?: string;
  チャンネル?: number;
  chatAi?: string;
  liveAi?: string;
  chatMode?: 'chat' | 'live' | 'code1' | 'code2' | 'code3' | 'code4';
  inputWsClient?: IWebSocketClient | null;
  inputConnected?: boolean;
}>();

// Emits
const 通知 = defineEmits<{
  close: [];
  'mode-change': ['chat' | 'live' | 'code1' | 'code2' | 'code3' | 'code4'];
  activate: [];
}>();

const 出力WebSocket = ref<IWebSocketClient | null>(null);
const 出力接続済み = ref(false);
const WebSocket接続中 = computed(() => (プロパティ.inputConnected ?? false) && 出力接続済み.value);
const セッションID = computed(() => プロパティ.セッションID ?? '');
const チャットAI = computed(() => プロパティ.chatAi ?? '');
const ライブAI = computed(() => プロパティ.liveAi ?? '');

// チャット履歴
interface メッセージ {
  role: 'input_text' | 'output_text' | 'input_file' | 'output_file' | 'recognition_input' | 'recognition_output' | 'input_request' | 'output_request' | 'welcome_text';
  content: string;
  id: string;
  kind?: 'text' | 'file';
  render?: 'effect' | 'static';
  fileName?: string | null;
  thumbnail?: string | null;
  isStream?: boolean;
  isCollapsed?: boolean;
}

const メッセージ一覧 = ref<メッセージ[]>([]);
const 入力テキスト = ref('');
const 選択モード = ref<'chat' | 'live' | 'code1' | 'code2' | 'code3' | 'code4'>(プロパティ.chatMode || 'live');
const チャット領域 = ref<HTMLElement | null>(null);
const テキストエリア = ref<HTMLTextAreaElement | null>(null);
const ドラッグ中 = ref(false);
let メッセージID連番 = 0;

// テキストエリアの自動リサイズ
const テキストエリア自動調整 = () => {
  if (テキストエリア.value) {
    テキストエリア.value.style.height = 'auto';
    テキストエリア.value.style.height = テキストエリア.value.scrollHeight + 'px';
  }
};

const 新規メッセージID = () => {
  const ソケット = セッションID.value || 'nosocket';
  const チャンネル = プロパティ.チャンネル ?? 0;
  return `chat-${ソケット}-${チャンネル}-${メッセージID連番++}`;
};

const ファイルメッセージ追加 = (role: メッセージ['role'], fileName?: string | null, thumbnail?: string | null) => {
  メッセージ一覧.value.push({
    role,
    content: '',
    id: 新規メッセージID(),
    kind: 'file',
    render: 'static',
    fileName: fileName ?? null,
    thumbnail: thumbnail ?? null
  });
  最下部スクロール();
};

type 演出状態 = {
  container: HTMLElement;
  textSpan: HTMLElement;
  cursorSpan: HTMLElement;
  queue: string[];
  running: boolean;
  ready: boolean;
  finalizeOnEmpty: boolean;
};

const 演出状態Map = new Map<string, 演出状態>();

const 速度設定 = (文字数: number) => {
  // 参考実装: int(文字列長/50) + 1 文字ずつ表示、10ms統一間隔
  const batch = Math.floor(文字数 / 50) + 1;
  return { interval: 10, batch };
};

const 演出初期化 = (メッセージID: string, 表示領域: HTMLElement, カーソル色: string = '#00ff00') => {
  表示領域.innerHTML = '';
  
  // テキスト要素
  const textSpan = document.createElement('span');
  textSpan.className = 'terminal-text';
  表示領域.appendChild(textSpan);
  
  // カーソル要素（テキストの後ろに兄弟要素として配置）
  const cursorSpan = document.createElement('span');
  cursorSpan.className = 'terminal-cursor';
  cursorSpan.textContent = '\u0020';  // Unicode半角スペース
  cursorSpan.style.display = 'inline-block';
  cursorSpan.style.width = '8px';
  cursorSpan.style.backgroundColor = カーソル色;
  cursorSpan.style.color = '#000000';
  表示領域.appendChild(cursorSpan);

  // JavaScript で明滅制御（0.3秒周期）
  let blinkVisible = true;
  const blinkInterval = setInterval(() => {
    if (blinkVisible) {
      cursorSpan.style.backgroundColor = 'transparent';
    } else {
      cursorSpan.style.backgroundColor = カーソル色;
    }
    blinkVisible = !blinkVisible;
  }, 300);

  const state: 演出状態 = {
    container: 表示領域,
    textSpan,
    cursorSpan,
    queue: [],
    running: false,
    ready: false,
    finalizeOnEmpty: false
  };
  演出状態Map.set(メッセージID, state);

  最下部スクロール();

  console.log(`[チャット演出] ${メッセージID}: 0.5秒待機開始（カーソル明滅中）カーソル色=${カーソル色}`);
  // 表示開始まで0.5秒点滅（参考実装: 500ms）
  window.setTimeout(() => {
    state.ready = true;
    console.log(`[チャット演出] ${メッセージID}: 0.5秒待機完了、テキスト表示開始`);
    演出実行(メッセージID);
  }, 500);
  
  // 演出完了時にクリアできるように保存
  (state as any).blinkInterval = blinkInterval;
};

const 演出キュー追加 = (メッセージID: string, 文字列: string, finalize: boolean) => {
  const state = 演出状態Map.get(メッセージID);
  if (!state) return;
  if (文字列) {
    state.queue.push(文字列);
  }
  if (finalize) {
    state.finalizeOnEmpty = true;
  }
  演出実行(メッセージID);
};

const 演出実行 = (メッセージID: string) => {
  const state = 演出状態Map.get(メッセージID);
  if (!state || state.running || !state.ready) return;
  if (state.queue.length === 0) {
    if (state.finalizeOnEmpty) {
      // カーソルを削除
      if (state.cursorSpan && state.cursorSpan.parentNode) {
        state.cursorSpan.remove();
      }
      // 明滅タイマーをクリア
      if ((state as any).blinkInterval) {
        clearInterval((state as any).blinkInterval);
      }
      console.log(`[チャット演出] ${メッセージID}: 完了（カーソル削除）`);
      演出状態Map.delete(メッセージID);
      最下部スクロール();
    }
    return;
  }
  state.running = true;
  const chunk = state.queue.shift() ?? '';
  const { interval, batch } = 速度設定(chunk.length);
  let index = 0;

  const tick = () => {
    const end = Math.min(index + batch, chunk.length);
    if (end > index) {
      state.textSpan.textContent += chunk.slice(index, end);
      index = end;
      nextTick(() => 最下部スクロール());
    }
    if (index >= chunk.length) {
      state.running = false;
      nextTick(() => 最下部スクロール());
      演出実行(メッセージID);
      return;
    }
    window.setTimeout(tick, interval);
  };

  tick();
};

const ターミナルメッセージ追加 = (role: メッセージ['role'], 内容: string, 追加オプション?: Partial<メッセージ>, finalize = true) => {
  const メッセージID = 新規メッセージID();
  メッセージ一覧.value.push({
    role,
    content: 内容,
    id: メッセージID,
    kind: 'text',
    render: 'effect',
    ...(追加オプション || {})
  });

  // roleに応じたカーソル色を決定
  let カーソル色 = '#00ff00';  // デフォルト緑
  switch (role) {
    case 'input_text':
      カーソル色 = '#ffffff';  // 白
      break;
    case 'input_request':
      カーソル色 = '#ffaa66';  // オレンジ
      break;
    case 'output_text':
      カーソル色 = '#00ff00';  // 緑
      break;
    case 'output_request':
      カーソル色 = '#00ffff';  // シアン
      break;
    case 'welcome_text':
      カーソル色 = '#00ff00';  // 緑（output_textと同じ）
      break;
    case 'recognition_input':
      カーソル色 = '#e5e7eb';  // グレー
      break;
    case 'recognition_output':
      カーソル色 = '#9ae6b4';  // ライトグリーン
      break;
  }

  nextTick(() => {
    const メッセージ要素 = document.getElementById(メッセージID);
    if (!メッセージ要素) return;
    const bubbleElement = メッセージ要素.querySelector('.bubble-content') as HTMLElement | null;
    if (!bubbleElement) return;
    演出初期化(メッセージID, bubbleElement, カーソル色);
    演出キュー追加(メッセージID, 内容, finalize);
  });
};

// WebSocketイベントハンドラ
const ウェルカム内容 = ref<string>('');

const 受信内容文字列 = (受信データ: any) => {
  const 内容 = 受信データ.メッセージ内容 ?? 受信データ.text ?? '';
  if (!内容) return '';
  return typeof 内容 === 'string' ? 内容 : JSON.stringify(内容);
};

const ウェルカム受信処理 = (受信データ: any) => {
  // 通知('activate'); // welcome_infoでは画面表示しない
  console.log('[チャット] welcome_info受信:', 受信データ);
  const 内容 = 受信内容文字列(受信データ);
  if (!内容) return;
  ウェルカム内容.value = 内容;
};
const 入力テキスト受信処理 = (受信データ: any) => {
  通知('activate');
  console.log('[チャット] input_text受信:', 受信データ);
  const 内容 = 受信内容文字列(受信データ);
  if (!内容) {
    console.log('[チャット] input_text 内容なしでスキップ');
    return;
  }
  console.log('[チャット] input_text表示開始:', 内容);
  ターミナルメッセージ追加('input_text', 内容);
};

const 入力リクエスト受信処理 = (受信データ: any) => {
  通知('activate');
  console.log('[チャット] input_request受信:', 受信データ);
  const 内容 = 受信内容文字列(受信データ);
  if (!内容) {
    console.log('[チャット] input_request 内容なしでスキップ');
    return;
  }
  console.log('[チャット] input_request表示開始:', 内容);
  ターミナルメッセージ追加('input_request', 内容);
};

const 入力ファイル受信処理 = (受信データ: any) => {
  通知('activate');
  const ファイル名 = 受信データ.ファイル名 ?? null;
  const サムネイル = 受信データ.サムネイル画像 ?? null;
  ファイルメッセージ追加('input_file', ファイル名, サムネイル);
};

const 出力テキスト受信処理 = (受信データ: any) => {
  通知('activate');
  console.log('[チャット] output_text受信:', 受信データ);
  const 内容 = 受信内容文字列(受信データ);
  if (!内容) {
    console.log('[チャット] output_text 内容なしでスキップ');
    return;
  }
  console.log('[チャット] output_text表示開始:', 内容);
  ターミナルメッセージ追加('output_text', 内容);
};

const 出力リクエスト受信処理 = (受信データ: any) => {
  通知('activate');
  console.log('[チャット] output_request受信:', 受信データ);
  const 内容 = 受信内容文字列(受信データ);
  if (!内容) {
    console.log('[チャット] output_request 内容なしでスキップ');
    return;
  }
  console.log('[チャット] output_request表示開始:', 内容);
  ターミナルメッセージ追加('output_request', 内容);
};

const ウェルカムテキスト受信処理 = (受信データ: any) => {
  // 通知('activate'); // welcome_textでは画面表示しない
  console.log('[チャット] welcome_text受信:', 受信データ);
  const 内容 = 受信内容文字列(受信データ);
  if (!内容) {
    console.log('[チャット] welcome_text 内容なしでスキップ');
    return;
  }
  console.log('[チャット] welcome_text表示開始:', 内容);
  ターミナルメッセージ追加('welcome_text', 内容);
};

const 出力ファイル受信処理 = (受信データ: any) => {
  通知('activate');
  const ファイル名 = 受信データ.ファイル名 ?? null;
  const サムネイル = 受信データ.サムネイル画像 ?? null;
  ファイルメッセージ追加('output_file', ファイル名, サムネイル);
};

const 音声入力受信処理 = (受信データ: any) => {
  通知('activate');
  const 内容 = 受信内容文字列(受信データ);
  if (!内容) return;
  ターミナルメッセージ追加('recognition_input', 内容);
};

const 音声出力受信処理 = (受信データ: any) => {
  通知('activate');
  const 内容 = 受信内容文字列(受信データ);
  if (!内容) return;
  ターミナルメッセージ追加('recognition_output', 内容);
};

// ストリーム表示用の一時メッセージID
let ストリームメッセージID: string | null = null;

const 出力ストリーム受信処理 = (受信データ: any) => {
  通知('activate');
  console.log('[チャット] output_stream受信:', 受信データ);
  const 内容 = 受信内容文字列(受信データ);
  if (!内容) return;

  // 処理開始
  if (内容 === '<<< 処理開始 >>>') {
    const メッセージID = `stream-${新規メッセージID()}`;
    ストリームメッセージID = メッセージID;
    メッセージ一覧.value.push({
      role: 'output_text',
      content: `${内容}\n`,
      id: メッセージID,
      kind: 'text',
      render: 'effect',
      isStream: true
    });
    nextTick(() => {
      const メッセージ要素 = document.getElementById(メッセージID);
      if (!メッセージ要素) return;
      const bubbleElement = メッセージ要素.querySelector('.bubble-content') as HTMLElement | null;
      if (!bubbleElement) return;
      演出初期化(メッセージID, bubbleElement);
      演出キュー追加(メッセージID, `${内容}\n`, false);
    });
    return;
  }

  // 処理終了
  if (内容 === '<<< 処理終了 >>>') {
    const 対象メッセージ = メッセージ一覧.value.find(m => m.id === ストリームメッセージID);
    if (対象メッセージ) {
      対象メッセージ.content += `${内容}\n`;
      対象メッセージ.isCollapsed = true;
    }
    if (ストリームメッセージID) {
      演出キュー追加(ストリームメッセージID, `${内容}\n`, true);
    }
    ストリームメッセージID = null;
    最下部スクロール();
    return;
  }

  // ストリーム内容を追加
  const 対象メッセージ = メッセージ一覧.value.find(m => m.id === ストリームメッセージID);
  if (対象メッセージ) {
    対象メッセージ.content += `${内容}\n`;
    if (ストリームメッセージID) {
      演出キュー追加(ストリームメッセージID, `${内容}\n`, false);
    }
    最下部スクロール();
  }
};

// 折りたたみ/展開切り替え
const 折りたたみ切替 = (メッセージID: string) => {
  const 対象メッセージ = メッセージ一覧.value.find(m => m.id === メッセージID);
  if (対象メッセージ && 対象メッセージ.isStream) {
    対象メッセージ.isCollapsed = !対象メッセージ.isCollapsed;
  }
};

const WSハンドラ登録 = (クライアント?: IWebSocketClient | null) => {
  if (!クライアント) return;
  const ch = プロパティ.チャンネル ?? 0;

  クライアント.on('welcome_info', ウェルカム受信処理);
  クライアント.on('input_text', 入力テキスト受信処理);
  クライアント.on('input_request', 入力リクエスト受信処理);
  クライアント.on('input_file', 入力ファイル受信処理);
  クライアント.on('output_text', 出力テキスト受信処理);
  クライアント.on('output_request', 出力リクエスト受信処理);
  クライアント.on('welcome_text', ウェルカムテキスト受信処理);
  クライアント.on('output_stream', 出力ストリーム受信処理);
  クライアント.on('output_file', 出力ファイル受信処理);
  クライアント.on('recognition_input', 音声入力受信処理);
  クライアント.on('recognition_output', 音声出力受信処理);

  console.log(`[チャット] ハンドラー登録完了 (チャンネル=${ch})`);
};

const WSハンドラ解除 = (クライアント?: IWebSocketClient | null) => {
  if (!クライアント) return;
  const ch = プロパティ.チャンネル ?? 0;

  クライアント.off('welcome_info', ウェルカム受信処理);
  クライアント.off('input_text', 入力テキスト受信処理);
  クライアント.off('input_request', 入力リクエスト受信処理);
  クライアント.off('input_file', 入力ファイル受信処理);
  クライアント.off('output_text', 出力テキスト受信処理);
  クライアント.off('output_request', 出力リクエスト受信処理);
  クライアント.off('welcome_text', ウェルカムテキスト受信処理);
  クライアント.off('output_stream', 出力ストリーム受信処理);
  クライアント.off('output_file', 出力ファイル受信処理);
  クライアント.off('recognition_input', 音声入力受信処理);
  クライアント.off('recognition_output', 音声出力受信処理);

  console.log(`[チャット] ハンドラー削除完了 (チャンネル=${ch})`);
};

const 出力ソケット接続 = async () => {
  const チャンネル = プロパティ.チャンネル ?? 0;
  if (!セッションID.value) {
    console.warn('[チャット] セッションID未確定のため出力ソケットを保留');
    return;
  }

  const wsUrl = createWebSocketUrl('/core/ws/AIコア');
  出力WebSocket.value = new AIコアWebSocket(wsUrl, セッションID.value, チャンネル);
  WSハンドラ登録(出力WebSocket.value);

  try {
    await 出力WebSocket.value.connect();
    出力接続済み.value = true;
    console.log(`[チャット] 出力ソケット接続完了 (チャンネル=${チャンネル})`);
  } catch (error) {
    出力接続済み.value = false;
    console.error('[チャット] 出力ソケット接続エラー:', error);
  }
};

onMounted(() => {
  const チャンネル = プロパティ.チャンネル ?? 0;
  console.log(`[チャット] ========== onMounted開始 ==========`);
  console.log(`[チャット] チャンネル=${チャンネル}`);
  console.log(`[チャット] セッションID=${セッションID.value}`);
  console.log(`[チャット] inputWsClient=${!!プロパティ.inputWsClient}`);
  console.log(`[チャット] inputConnected=${プロパティ.inputConnected}`);
  出力ソケット接続();
  console.log(`[チャット] ========== onMounted完了 ==========`);
});

watch(() => プロパティ.セッションID, (新ID, 旧ID) => {
  if (!新ID || 新ID === 旧ID) return;
  if (出力WebSocket.value) {
    WSハンドラ解除(出力WebSocket.value);
    出力WebSocket.value.disconnect();
    出力WebSocket.value = null;
    出力接続済み.value = false;
  }
  出力ソケット接続();
});

watch(
  () => プロパティ.chatMode,
  (新モード) => {
    if (!新モード || 新モード === 選択モード.value) return;
    選択モード.value = 新モード;
  }
);

watch(選択モード, (新モード) => {
  通知('mode-change', 新モード);
});

// クリーンアップ
onBeforeUnmount(() => {
  if (出力WebSocket.value) {
    WSハンドラ解除(出力WebSocket.value);
    出力WebSocket.value.disconnect();
    出力WebSocket.value = null;
  }
  出力接続済み.value = false;
});

// メッセージ送信
const メッセージ送信 = async () => {
  if (!入力テキスト.value.trim() || !WebSocket接続中.value) return;

  const 送信内容 = 入力テキスト.value.trim();
  入力テキスト.value = '';

  // テキストエリアの高さをリセット
  nextTick(() => {
    テキストエリア自動調整();
  });

  // WebSocket経由でメッセージを送信（サーバーが即座にエコーバック）
  if (プロパティ.inputWsClient && プロパティ.inputWsClient.isConnected()) {
    const 基本チャンネル = プロパティ.チャンネル ?? 0;
    const 現在モード = 選択モード.value;
    const コードモード = 現在モード.startsWith('code');
    const 出力先チャンネル = コードモード ? Number(現在モード.replace('code', '')) || 1 : 基本チャンネル;
    const 送信モード = コードモード ? 'code' : 現在モード;
    const メッセージ識別 = コードモード ? 'input_request' : 'input_text';
    console.log(`[チャット] WebSocket経由でメッセージ送信 (${メッセージ識別}):`, {
      userMessage: 送信内容,
      チャンネル: 出力先チャンネル,
      mode: 送信モード
    });
    if (コードモード) {
      // codeモードでも入力値をチャンネル0に表示・履歴保存する
      プロパティ.inputWsClient.send({
        セッションID: セッションID.value,
        チャンネル: -1,
        出力先チャンネル: 0,
        メッセージ識別: 'input_text',
        メッセージ内容: 送信内容,
        ファイル名: 'code',
        サムネイル画像: null
      });
    }
    プロパティ.inputWsClient.send({
      セッションID: セッションID.value,
      チャンネル: -1,
      出力先チャンネル: 出力先チャンネル,
      メッセージ識別: メッセージ識別,
      メッセージ内容: 送信内容,
      ファイル名: 送信モード,  // chat, live, code
      サムネイル画像: null
    });
  } else {
    console.log('[チャット] WebSocket未接続のため送信失敗');
  }
};

// ファイルをBase64に変換
const ファイルをBase64読込 = (入力ファイル: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const 読込 = new FileReader();
    読込.onload = () => {
      const result = 読込.result;
      if (typeof result === 'string') {
        const commaIndex = result.indexOf(',');
        resolve(commaIndex >= 0 ? result.slice(commaIndex + 1) : result);
        return;
      }
      if (result instanceof ArrayBuffer) {
        const bytes = new Uint8Array(result);
        let binary = '';
        for (let i = 0; i < bytes.length; i++) {
          binary += String.fromCharCode(bytes[i]);
        }
        resolve(window.btoa(binary));
        return;
      }
      reject(new Error('不明なファイル形式です'));
    };
    読込.onerror = () => reject(読込.error || new Error('ファイル読み込みに失敗しました'));
    読込.readAsDataURL(入力ファイル);
  });
};

const 入力ファイル送信 = async (入力ファイル: File) => {
  if (!プロパティ.inputWsClient || !プロパティ.inputWsClient.isConnected()) return;
  try {
    const Base64データ = await ファイルをBase64読込(入力ファイル);
    const 基本チャンネル = プロパティ.チャンネル ?? 0;
    const 現在モード = 選択モード.value;
    const コードモード = 現在モード.startsWith('code');
    const 出力先チャンネル = コードモード ? Number(現在モード.replace('code', '')) || 1 : 基本チャンネル;
    プロパティ.inputWsClient.send({
      セッションID: セッションID.value,
      チャンネル: -1,  // 入力は常に-1
      出力先チャンネル: 出力先チャンネル,  // バックエンドが振り分け
      メッセージ識別: 'input_file',
      メッセージ内容: Base64データ,
      ファイル名: 入力ファイル.name,
      サムネイル画像: null
    });
  } catch (error) {
    console.error('[チャット] ファイル送信エラー:', error);
    ターミナルメッセージ追加('output_text', 'ファイル送信に失敗しました。');
  }
};

// ドラッグ&ドロップ
const ドラッグオーバー処理 = (イベント: DragEvent) => {
  イベント.preventDefault();
  if (!WebSocket接続中.value) return;
  ドラッグ中.value = true;
};

const ドラッグ離脱処理 = (イベント: DragEvent) => {
  イベント.preventDefault();
  if (イベント.currentTarget === イベント.target) {
    ドラッグ中.value = false;
  }
};

const ドロップ処理 = async (イベント: DragEvent) => {
  イベント.preventDefault();
  ドラッグ中.value = false;
  if (!WebSocket接続中.value) return;
  const ファイル一覧 = イベント.dataTransfer?.files;
  if (!ファイル一覧 || ファイル一覧.length === 0) return;
  for (const ファイル of Array.from(ファイル一覧)) {
    await 入力ファイル送信(ファイル);
  }
};

// 自動スクロール
const 最下部スクロール = () => {
  nextTick(() => {
    if (チャット領域.value) {
      チャット領域.value.scrollTop = チャット領域.value.scrollHeight;
    }
  });
};

// ステータステキスト
const 接続状態表示 = computed(() => {
  return WebSocket接続中.value ? '接続中' : '切断';
});

// Enterキーで改行（送信しない）
// const handleKeydown = (e: KeyboardEvent) => {
//   if (e.key === 'Enter' && !e.shiftKey) {
//     e.preventDefault();
//     メッセージ送信();
//   }
// };
</script>

<template>
  <div class="chat-container show">
    <div class="header">
      <button class="close-btn" @click="通知('close')" title="閉じる">×</button>
      <h1>AiDiy AI <span v-if="チャットAI || ライブAI" class="model-info">({{ チャットAI }}, {{ ライブAI }})</span></h1>
      <div class="status">
        <span :class="['status-dot', WebSocket接続中 ? 'connecting' : 'disconnected']"></span>
        <span>{{ 接続状態表示 }}</span>
      </div>
    </div>

    <div ref="チャット領域" class="chat-area">
      <div class="welcome-message" v-if="ウェルカム内容">
        {{ ウェルカム内容 }}
      </div>

      <div
        v-for="(メッセージ項目, index) in メッセージ一覧"
        :key="メッセージ項目.id"
        :id="メッセージ項目.id"
        :class="['message', メッセージ項目.role, メッセージ項目.kind === 'file' ? 'is-file' : '', メッセージ項目.isStream ? 'stream-output' : '', メッセージ項目.isCollapsed ? 'collapsed' : '']"
      >
        <div
          class="message-bubble"
          @click="メッセージ項目.isStream && メッセージ項目.isCollapsed ? 折りたたみ切替(メッセージ項目.id) : null"
          :style="{ cursor: メッセージ項目.isStream && メッセージ項目.isCollapsed ? 'pointer' : 'default' }"
        >
          <div v-if="メッセージ項目.isStream && メッセージ項目.isCollapsed" class="collapsed-wrapper">
            <span class="collapsed-indicator">...</span>
            <span class="collapsed-arrow">◀</span>
          </div>
          <div v-show="!(メッセージ項目.isStream && メッセージ項目.isCollapsed)" class="bubble-content">
            <template v-if="メッセージ項目.kind === 'file'">
              <div class="file-message">
                <div class="file-name"><span v-if="メッセージ項目.role === 'input_file'">ファイル入力: </span><span v-if="メッセージ項目.role === 'output_file'">ファイル出力: </span>{{ メッセージ項目.fileName || 'ファイル受信' }}</div>
                <img
                  v-if="メッセージ項目.thumbnail"
                  class="file-thumbnail"
                  :src="`data:image/png;base64,${メッセージ項目.thumbnail}`"
                  alt="thumbnail"
                />
              </div>
            </template>
            <template v-else-if="メッセージ項目.render === 'static'">
              {{ メッセージ項目.content }}
            </template>
            <template v-else-if="メッセージ項目.render === 'effect'">
              <!-- ターミナルエフェクトがここに直接DOMを書き込む -->
            </template>
          </div>
          <span
            v-if="メッセージ項目.isStream && !メッセージ項目.isCollapsed"
            class="expand-indicator"
            @click.stop="折りたたみ切替(メッセージ項目.id)"
            title="折りたたむ"
          >▼</span>
        </div>
      </div>

    </div>

    <div class="control-area">
      <!-- テキスト入力エリア -->
      <div
        class="text-input-area"
        :class="{ 'drag-over': ドラッグ中 }"
        @dragover="ドラッグオーバー処理"
        @dragleave="ドラッグ離脱処理"
        @drop="ドロップ処理"
      >
        <div class="input-container">
          <span class="prompt-symbol">&gt;</span>
          <textarea
            v-model="入力テキスト"
            class="input-field"
            placeholder="メッセージを入力..."
            maxlength="500"
            :disabled="!WebSocket接続中"
            @input="テキストエリア自動調整"
            ref="テキストエリア"
          ></textarea>
        </div>
      </div>

      <!-- モード選択（縦並び） -->
      <div class="mode-panel">
        <div class="mode-selector">
          <label class="mode-option">
            <input type="radio" v-model="選択モード" value="chat" name="mode" />
            <span>Chat</span>
          </label>
          <label class="mode-option">
            <input type="radio" v-model="選択モード" value="live" name="mode" />
            <span>Live</span>
          </label>
          <label class="mode-option">
            <input type="radio" v-model="選択モード" value="code1" name="mode" />
            <span>Code1</span>
          </label>
        </div>

        <div class="code-selector">
          <label class="mode-option">
            <input type="radio" v-model="選択モード" value="code2" name="mode" />
            <span>Code2</span>
          </label>
          <label class="mode-option">
            <input type="radio" v-model="選択モード" value="code3" name="mode" />
            <span>Code3</span>
          </label>
          <label class="mode-option">
            <input type="radio" v-model="選択モード" value="code4" name="mode" />
            <span>Code4</span>
          </label>
        </div>
      </div>

      <!-- 送信ボタン -->
      <button
        class="chat-send-btn"
        :class="{
          'ws-disabled': !WebSocket接続中,
          'has-text': 入力テキスト.length > 0
        }"
        @click="メッセージ送信"
        :disabled="!入力テキスト.trim() || !WebSocket接続中"
        title="送信"
      >
        <img src="/icons/sending.png" alt="送信" />
      </button>
    </div>
  </div>
</template>

<style scoped>
.chat-container {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 2px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
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
  height: 28px;
  line-height: 28px;
}

.header h1 .model-info {
  font-size: 14px;
  font-weight: normal;
  color: #666;
  margin-left: 8px;
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

.status-dot.disconnected { background: #888888; }
.status-dot.connecting { background: #44ff44; }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.chat-area {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  overflow-x: auto;
  background: #000000;
  position: relative;
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
  font-family: 'Courier New', monospace;
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
  font-family: 'Courier New', monospace;
  font-size: 11px;
  white-space: pre-wrap;
}

.message.input_text .message-bubble {
  color: #ffffff;
  border-left: 4px solid rgba(255, 255, 255, 0.7);
}

.message.input_file .message-bubble {
  color: #ffffff;
  border-left: 4px solid rgba(255, 255, 255, 0.7);
}

.message.input_request .message-bubble {
  color: #ffaa66;
  border-left: 4px solid rgba(255, 170, 102, 0.7);
}

.message.input_request .message-bubble::before {
  content: "REQ > ";
  font-weight: bold;
  color: #ffaa66;
}

.message.recognition_input .message-bubble {
  color: #e5e7eb;
  border-left: 4px solid rgba(187, 187, 187, 0.7);
}

.message.output_text .message-bubble {
  color: #00ff00;
  border-left: 4px solid rgba(0, 255, 0, 0.7);
  min-width: 200px;
}

.message.output_request .message-bubble {
  color: #00ffff;
  border-left: 4px solid rgba(0, 255, 255, 0.7);
  min-width: 200px;
}

.message.welcome_text .message-bubble {
  color: #00ff00;
  border-left: 4px solid rgba(0, 255, 0, 0.7);
  min-width: 200px;
}

.message.stream-output .message-bubble {
  background: rgba(0, 255, 0, 0.08);
  border-radius: 4px;
  padding: 8px 12px;
  position: relative;
}

.message.stream-output.collapsed .message-bubble {
  padding: 4px 8px;
}

.collapsed-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  cursor: pointer;
}

.collapsed-indicator {
  color: #00cc00;
  font-weight: bold;
  font-size: 16px;
}

.collapsed-arrow {
  color: #00cc00;
  font-size: 14px;
}

.expand-indicator {
  position: absolute;
  top: 4px;
  right: 8px;
  color: #00cc00;
  font-size: 12px;
  cursor: pointer;
  user-select: none;
}

.expand-indicator:hover {
  color: #00ff00;
}

.message.output_file .message-bubble {
  color: #00ff00;
  border-left: 4px solid rgba(0, 255, 0, 0.7);
}

.message.recognition_output .message-bubble {
  color: #9ae6b4;
  border-left: 4px solid rgba(0, 153, 204, 0.7);
}

.terminal-typing {
  display: inline;
}

.terminal-text {
  display: inline;
}

.terminal-cursor {
  display: inline !important;
  background-color: #00ff00 !important;
  color: #000000 !important;
  padding: 0 2px !important;
  margin-left: 0 !important;
  font-family: 'Courier New', monospace !important;
  font-weight: bold !important;
}

.terminal-text {
  display: inline;
  white-space: pre-wrap;
  font-family: 'Courier New', monospace;
  line-height: 1.1;
}

.terminal-text.typing::after {
  content: '█';
  color: #ffffff;
  font-weight: bold;
  margin-left: 0px;
}

@keyframes cursor-blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

@keyframes cursor-rapid-blink {
  0%, 49% { 
    background-color: #00ff00;
    color: #000000;
  }
  50%, 100% { 
    background-color: transparent;
    color: #00ff00;
  }
}

.terminal-cursor-typing {
  display: inline;
  color: #ffffff !important;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  font-weight: bold;
  opacity: 1 !important;
  animation: none !important;
}

.file-message {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.message.is-file .message-bubble {
  display: block;
}

.message.output_file.is-file .message-bubble {
  min-width: 0;
}

.file-name {
  font-family: 'Courier New', monospace;
  font-size: 11px;
  color: #ffffff;
}

.message.output_file .file-name {
  color: #00ff00;
}

.file-thumbnail {
  max-width: 240px;
  max-height: 180px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 2px;
  object-fit: contain;
  background: #111;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* スクロールバーのスタイル（細く） */
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

.control-area {
  padding: 10px 20px 0 20px;
  background: #202020;
  border-top: 1px solid #484848;
  display: flex;
  flex-direction: row;
  gap: 10px;
  align-items: flex-end;
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
  font-family: 'Courier New', monospace;
  font-weight: normal;
  position: relative;
  top: -4px;
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
  font-family: 'Courier New', monospace;
  font-weight: bold;
  font-size: 16px;
  pointer-events: none;
  z-index: 1;
}

.input-field {
  width: 100%;
  padding: 10px 16px 6px 30px;
  border: 2px solid rgba(255, 255, 255, 0.5); /* カーソルがないとき薄い白 */
  border-radius: 0;
  outline: none;
  font-size: 14px;
  background: transparent;
  color: #e0e0e0;
  box-sizing: border-box;
  resize: none;
  min-height: 60px;
  max-height: 150px;
  overflow-y: auto;
  font-family: inherit;
  line-height: 1.4;
  height: 60px; /* 初期高さ */
}

.input-field:disabled {
  border-color: #808080;
  color: #666;
  background: rgba(128, 128, 128, 0.1);
}

.input-field:focus {
  border-color: #ffffff; /* 鮮やかな白 */
}

.input-field::placeholder {
  color: #888;
}

/* 送信ボタン：デフォルトは白背景に青紫枠（フラットデザイン） */
.chat-send-btn {
  border: 2px solid #667eea;
  border-radius: 2px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  box-shadow: none;
  padding: 0;
  width: 56px;
  height: 48px;
  margin-bottom: 20px;
  background: rgba(255, 255, 255, 0.95); /* 白背景 */
  color: white;
  flex-shrink: 0;
}

.chat-send-btn img {
  width: 34px;
  height: 34px;
  object-fit: contain;
  pointer-events: none;
  filter: brightness(0); /* 黒アイコン */
}

.chat-send-btn:hover:not(:disabled) {
  background: rgba(240, 240, 240, 0.95);
  border-color: #5a6fd8;
}

/* テキスト1文字以上入力：青紫色 */
.chat-send-btn.has-text {
  background: #667eea;
  border-color: #667eea;
}

.chat-send-btn.has-text img {
  filter: brightness(0) invert(1); /* 白アイコン */
}

.chat-send-btn.has-text:hover:not(:disabled) {
  background: #5a6fd8;
  border-color: #5a6fd8;
}

/* テキストなし時（disabled）：白背景に青紫枠を維持 */
.chat-send-btn:disabled:not(.ws-disabled) {
  background: rgba(255, 255, 255, 0.95);
  border-color: #667eea;
  cursor: not-allowed;
  opacity: 1;
}

.chat-send-btn:disabled:not(.ws-disabled) img {
  filter: brightness(0); /* 黒アイコン */
}

/* WS接続前：灰色 */
.chat-send-btn.ws-disabled {
  background: #808080 !important;
  border-color: #808080 !important;
  box-shadow: none;
  cursor: not-allowed;
  opacity: 1;
}

.chat-send-btn.ws-disabled img {
  filter: brightness(0) invert(1) !important; /* 白アイコン */
}

.chat-send-btn.ws-disabled:hover {
  transform: none;
}
</style>

