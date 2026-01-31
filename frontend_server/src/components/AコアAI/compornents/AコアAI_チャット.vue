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
import { ref, onMounted, onBeforeUnmount, nextTick, computed, watch } from 'vue';
import { AコアAIWebSocket, createWebSocketUrl, type IWebSocketClient } from '@/api/websocket';

// Props
const props = defineProps<{
  socketId?: string;
  チャンネル?: number;
  chatAi?: string;
  liveAi?: string;
  chatMode?: 'chat' | 'live' | 'code1' | 'code2' | 'code3' | 'code4';
  inputWsClient?: IWebSocketClient | null;
  inputConnected?: boolean;
}>();

// Emits
const emit = defineEmits<{
  close: [];
  'mode-change': ['chat' | 'live' | 'code1' | 'code2' | 'code3' | 'code4'];
}>();

const outputWsClient = ref<IWebSocketClient | null>(null);
const outputConnected = ref(false);
const isWsConnected = computed(() => (props.inputConnected ?? false) && outputConnected.value);

// チャット履歴
interface Message {
  role: 'input_text' | 'output_text' | 'input_file' | 'output_file' | 'recognition_input' | 'recognition_output';
  content: string;
  isTyping?: boolean;
  terminalEffect?: any;
  id: string;
  kind?: 'text' | 'file';
  render?: 'effect' | 'static';
  fileName?: string | null;
  thumbnail?: string | null;
  isStream?: boolean;
  isCollapsed?: boolean;
}

const messages = ref<Message[]>([]);
const inputText = ref('');
const selectedMode = ref<'chat' | 'live' | 'code1' | 'code2' | 'code3' | 'code4'>(props.chatMode || 'live');
const chatArea = ref<HTMLElement | null>(null);
const textareaRef = ref<HTMLTextAreaElement | null>(null);
const isDragOver = ref(false);
let messageIdCounter = 0;

// テキストエリアの自動リサイズ
const autoResize = () => {
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto';
    textareaRef.value.style.height = textareaRef.value.scrollHeight + 'px';
  }
};

// ターミナルエフェクト関数
const createTerminalEffect = (container: HTMLElement, text: string, messageType: string) => {
  const typingSpeed = 10;
  const initialDelay = 300;

  // メッセージタイプに応じたカーソル色
  const cursorColors: { [key: string]: string } = {
    'input_text': '#ffffff',
    'recognition_input': '#bbbbbb',
    'output_text': '#00ff00',
    'recognition_output': '#0099cc'
  };

  const cursorColor = cursorColors[messageType] || '#00ff00';

  let isStopped = false;
  let currentIndex = 0;
  let cursorElement: HTMLElement | null = null;
  let initialTimer: number | null = null;

  // テキストコンテナを作成
  const textContainer = document.createElement('span');
  textContainer.className = 'terminal-text typing'; // typingクラスを追加
  container.appendChild(textContainer);

  // 文字配列準備
  const characters = text.split('');

  // 文字列長に基づいた表示単位計算: int(文字列長/50) + 1 文字ずつ表示
  const batchSize = Math.floor(text.length / 50) + 1;

  // 文字単位表示アニメーション
  const startTyping = async () => {
    try {
      for (currentIndex = 0; currentIndex < characters.length; currentIndex += batchSize) {
        if (isStopped) break;

        // バッチサイズ分の文字を一度に表示
        const endIndex = Math.min(currentIndex + batchSize, characters.length);

        for (let i = currentIndex; i < endIndex; i++) {
          const charSpan = document.createElement('span');
          charSpan.textContent = characters[i];
          textContainer.appendChild(charSpan);
        }

        // 40ms間隔で待機（4倍遅く）
        await new Promise(resolve => setTimeout(resolve, 40));

        // スクロール
        scrollToBottom();
      }

      // タイピング完了処理
      if (!isStopped) {
        // typingクラスを削除してカーソルを消す
        textContainer.classList.remove('typing');

        // 最後のスクロール
        scrollToBottom();
      }
    } catch (error) {
      console.error('ターミナルエフェクトエラー:', error);
    }
  };

  // 初期遅延後にタイピング開始
  initialTimer = window.setTimeout(async () => {
    if (!isStopped) {
      await startTyping();
    }
  }, initialDelay);

  // 制御オブジェクトを返す
  return {
    stop: () => {
      isStopped = true;
      if (initialTimer) {
        clearTimeout(initialTimer);
        initialTimer = null;
      }
      // typingクラスを削除
      if (textContainer) {
        textContainer.classList.remove('typing');
      }
    }
  };
};

// ターミナルエフェクト付きでメッセージを追加
const addMessageWithEffect = (role: Message['role'], content: string) => {
  const messageId = `message-${messageIdCounter++}`;
  messages.value.push({
    role,
    content,
    isTyping: true,
    id: messageId,
    kind: 'text',
    render: 'effect'
  });

  nextTick(() => {
    const messageElement = document.getElementById(messageId);
    if (messageElement) {
      const bubbleElement = messageElement.querySelector('.bubble-content') as HTMLElement;
      if (bubbleElement) {
        // 既存のコンテンツをクリア
        bubbleElement.innerHTML = '';
        // ターミナルエフェクトを開始
        const effect = createTerminalEffect(bubbleElement, content, role);
        const message = messages.value.find(m => m.id === messageId);
        if (message) {
          message.terminalEffect = effect;
          message.isTyping = false;
        }
      }
    }
  });
};

const addFileMessage = (role: Message['role'], fileName?: string | null, thumbnail?: string | null) => {
  const messageId = `message-${messageIdCounter++}`;
  messages.value.push({
    role,
    content: '',
    id: messageId,
    kind: 'file',
    render: 'static',
    fileName: fileName ?? null,
    thumbnail: thumbnail ?? null
  });
  scrollToBottom();
};

// WebSocketイベントハンドラ
const welcomeInfo = ref<string>('');

const handleWelcomeInfo = (message: any) => {
  console.log('[チャット] welcome_info受信:', message);
  const content = message.メッセージ内容 ?? message.text ?? '';
  if (!content) return;
  const text = typeof content === 'string' ? content : JSON.stringify(content);
  welcomeInfo.value = text;
};
const handleInputText = (message: any) => {
  console.log('[チャット] input_text受信:', message);
  const content = message.メッセージ内容 ?? message.text ?? '';
  if (!content) {
    console.log('[チャット] input_text 内容なしでスキップ');
    return;
  }
  console.log('[チャット] input_text表示開始:', content);
  addMessageWithEffect('input_text', content);
};

const handleInputFile = (message: any) => {
  const filePath = message.ファイル名 ?? null;
  const thumbnail = message.サムネイル画像 ?? null;
  addFileMessage('input_file', filePath, thumbnail);
};

const handleOutputText = (message: any) => {
  console.log('[チャット] output_text受信:', message);
  const content = message.メッセージ内容 ?? message.text ?? '';
  if (!content) {
    console.log('[チャット] output_text 内容なしでスキップ');
    return;
  }
  console.log('[チャット] output_text表示開始:', content);
  addMessageWithEffect('output_text', content);
};

const handleOutputFile = (message: any) => {
  const filePath = message.ファイル名 ?? null;
  const thumbnail = message.サムネイル画像 ?? null;
  addFileMessage('output_file', filePath, thumbnail);
};

const handleRecognitionInput = (message: any) => {
  const content = message.メッセージ内容 ?? message.text ?? '';
  if (!content) return;
  const messageId = `message-${messageIdCounter++}`;
  messages.value.push({
    role: 'recognition_input',
    content,
    id: messageId,
    kind: 'text',
    render: 'static'
  });
  scrollToBottom();
};

const handleRecognitionOutput = (message: any) => {
  const content = message.メッセージ内容 ?? message.text ?? '';
  if (!content) return;
  const messageId = `message-${messageIdCounter++}`;
  messages.value.push({
    role: 'recognition_output',
    content,
    id: messageId,
    kind: 'text',
    render: 'static'
  });
  scrollToBottom();
};

// ストリーム表示用の一時メッセージID
let streamMessageId: string | null = null;
let streamBubbleElement: HTMLElement | null = null;

const handleOutputStream = (message: any) => {
  console.log('[チャット] output_stream受信:', message);
  const content = message.メッセージ内容 ?? message.text ?? '';
  if (!content) return;

  // 処理開始
  if (content === '<<< 処理開始 >>>') {
    // メッセージブロックを作成
    streamMessageId = `stream-${messageIdCounter++}`;
    messages.value.push({
      role: 'output_text',
      content: '',
      id: streamMessageId,
      kind: 'text',
      render: 'effect',
      isTyping: false,
      isStream: true
    });

    // DOMを取得してターミナルエフェクトで処理開始メッセージを追加
    nextTick(() => {
      const messageElement = document.getElementById(streamMessageId!);
      if (messageElement) {
        streamBubbleElement = messageElement.querySelector('.bubble-content') as HTMLElement;
        if (streamBubbleElement) {
          streamBubbleElement.innerHTML = '';
          // 処理開始メッセージをターミナルエフェクトで追加
          const startContainer = document.createElement('span');
          streamBubbleElement.appendChild(startContainer);
          createTerminalEffect(startContainer, content + '\n', 'output_text');
        }
      }
      scrollToBottom();
    });
    return;
  }

  // 処理終了
  if (content === '<<< 処理終了 >>>') {
    if (streamBubbleElement) {
      // 処理終了メッセージをターミナルエフェクトで追加
      const endContainer = document.createElement('span');
      streamBubbleElement.appendChild(endContainer);
      createTerminalEffect(endContainer, content + '\n', 'output_text');

      // 折りたたみ設定
      const message = messages.value.find(m => m.id === streamMessageId);
      if (message) {
        message.isCollapsed = true;
      }

      // クリーンアップ
      streamMessageId = null;
      streamBubbleElement = null;
    }
    scrollToBottom();
    return;
  }

  // ストリーム内容を追加
  if (streamBubbleElement) {
    // 新しいコンテンツをターミナルエフェクトで追加
    const contentContainer = document.createElement('span');
    streamBubbleElement.appendChild(contentContainer);
    createTerminalEffect(contentContainer, content + '\n', 'output_text');
    scrollToBottom();
  }
};

// 折りたたみ/展開切り替え
const toggleCollapse = (messageId: string) => {
  const message = messages.value.find(m => m.id === messageId);
  if (message && message.isStream) {
    message.isCollapsed = !message.isCollapsed;
  }
};

const registerWsHandlers = (client?: IWebSocketClient | null) => {
  if (!client) return;
  const ch = props.チャンネル ?? 0;
  
  client.on('welcome_info', handleWelcomeInfo);
  client.on('input_text', handleInputText);
  client.on('input_file', handleInputFile);
  client.on('output_text', handleOutputText);
  client.on('output_stream', handleOutputStream);
  client.on('output_file', handleOutputFile);
  client.on('recognition_input', handleRecognitionInput);
  client.on('recognition_output', handleRecognitionOutput);
  
  console.log(`[チャット] ハンドラー登録完了 (チャンネル=${ch})`);
};

const unregisterWsHandlers = (client?: IWebSocketClient | null) => {
  if (!client) return;
  const ch = props.チャンネル ?? 0;
  
  client.off('welcome_info', handleWelcomeInfo);
  client.off('input_text', handleInputText);
  client.off('input_file', handleInputFile);
  client.off('output_text', handleOutputText);
  client.off('output_stream', handleOutputStream);
  client.off('output_file', handleOutputFile);
  client.off('recognition_input', handleRecognitionInput);
  client.off('recognition_output', handleRecognitionOutput);
  
  console.log(`[チャット] ハンドラー削除完了 (チャンネル=${ch})`);
};

const connectOutputSocket = async () => {
  const チャンネル = props.チャンネル ?? 0;
  if (!props.socketId) {
    console.warn('[チャット] socketId未確定のため出力ソケットを保留');
    return;
  }

  const wsUrl = createWebSocketUrl('/ws/AコアAI');
  outputWsClient.value = new AコアAIWebSocket(wsUrl, props.socketId, チャンネル);
  registerWsHandlers(outputWsClient.value);

  try {
    await outputWsClient.value.connect();
    outputConnected.value = true;
    console.log(`[チャット] 出力ソケット接続完了 (チャンネル=${チャンネル})`);
  } catch (error) {
    outputConnected.value = false;
    console.error('[チャット] 出力ソケット接続エラー:', error);
  }
};

onMounted(() => {
  const チャンネル = props.チャンネル ?? 0;
  console.log(`[チャット] ========== onMounted開始 ==========`);
  console.log(`[チャット] チャンネル=${チャンネル}`);
  console.log(`[チャット] socketId=${props.socketId}`);
  console.log(`[チャット] inputWsClient=${!!props.inputWsClient}`);
  console.log(`[チャット] inputConnected=${props.inputConnected}`);
  connectOutputSocket();
  console.log(`[チャット] ========== onMounted完了 ==========`);
});

watch(() => props.socketId, (newId, oldId) => {
  if (!newId || newId === oldId) return;
  if (outputWsClient.value) {
    unregisterWsHandlers(outputWsClient.value);
    outputWsClient.value.disconnect();
    outputWsClient.value = null;
    outputConnected.value = false;
  }
  connectOutputSocket();
});

watch(
  () => props.chatMode,
  (newMode) => {
    if (!newMode || newMode === selectedMode.value) return;
    selectedMode.value = newMode;
  }
);

watch(selectedMode, (newMode) => {
  emit('mode-change', newMode);
});

// クリーンアップ
onBeforeUnmount(() => {
  if (outputWsClient.value) {
    unregisterWsHandlers(outputWsClient.value);
    outputWsClient.value.disconnect();
    outputWsClient.value = null;
  }
  outputConnected.value = false;
});

// メッセージ送信
const sendMessage = async () => {
  if (!inputText.value.trim() || !isWsConnected.value) return;

  const userMessage = inputText.value.trim();
  inputText.value = '';

  // テキストエリアの高さをリセット
  nextTick(() => {
    autoResize();
  });

  // WebSocket経由でメッセージを送信（サーバーが即座にエコーバック）
  if (props.inputWsClient && props.inputWsClient.isConnected()) {
    const baseChannel = props.チャンネル ?? 0;
    const mode = selectedMode.value;
    const isCodeMode = mode.startsWith('code');
    const 出力先チャンネル = isCodeMode ? Number(mode.replace('code', '')) || 1 : baseChannel;
    const 送信モード = isCodeMode ? 'code' : mode;
    console.log('[チャット] WebSocket経由でメッセージ送信 (input_text):', {
      userMessage,
      チャンネル: 出力先チャンネル,
      mode: 送信モード
    });
    props.inputWsClient.send({
      ソケットID: props.socketId ?? '',
      チャンネル: -1,
      出力先チャンネル: 出力先チャンネル,
      メッセージ識別: 'input_text',
      メッセージ内容: userMessage,
      ファイル名: 送信モード,  // chat, live, code
      サムネイル画像: null
    });
  } else {
    console.log('[チャット] WebSocket未接続のため送信失敗');
  }
};

// ファイルをBase64に変換
const readFileAsBase64 = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result;
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
    reader.onerror = () => reject(reader.error || new Error('ファイル読み込みに失敗しました'));
    reader.readAsDataURL(file);
  });
};

const sendInputFile = async (file: File) => {
  if (!props.inputWsClient || !props.inputWsClient.isConnected()) return;
  try {
    const base64Data = await readFileAsBase64(file);
    const baseChannel = props.チャンネル ?? 0;
    const mode = selectedMode.value;
    const isCodeMode = mode.startsWith('code');
    const 出力先チャンネル = isCodeMode ? Number(mode.replace('code', '')) || 1 : baseChannel;
    props.inputWsClient.send({
      ソケットID: props.socketId ?? '',
      チャンネル: -1,  // 入力は常に-1
      出力先チャンネル: 出力先チャンネル,  // バックエンドが振り分け
      メッセージ識別: 'input_file',
      メッセージ内容: base64Data,
      ファイル名: file.name,
      サムネイル画像: null
    });
  } catch (error) {
    console.error('[チャット] ファイル送信エラー:', error);
    addMessageWithEffect('output_text', 'ファイル送信に失敗しました。');
  }
};

// ドラッグ&ドロップ
const handleDragOver = (event: DragEvent) => {
  event.preventDefault();
  if (!isWsConnected.value) return;
  isDragOver.value = true;
};

const handleDragLeave = (event: DragEvent) => {
  event.preventDefault();
  if (event.currentTarget === event.target) {
    isDragOver.value = false;
  }
};

const handleDrop = async (event: DragEvent) => {
  event.preventDefault();
  isDragOver.value = false;
  if (!isWsConnected.value) return;
  const files = event.dataTransfer?.files;
  if (!files || files.length === 0) return;
  for (const file of Array.from(files)) {
    await sendInputFile(file);
  }
};

// 自動スクロール
const scrollToBottom = () => {
  nextTick(() => {
    if (chatArea.value) {
      chatArea.value.scrollTop = chatArea.value.scrollHeight;
    }
  });
};

// ステータステキスト
const statusText = computed(() => {
  return isWsConnected.value ? '接続中' : '切断';
});

// Enterキーで改行（送信しない）
// const handleKeydown = (e: KeyboardEvent) => {
//   if (e.key === 'Enter' && !e.shiftKey) {
//     e.preventDefault();
//     sendMessage();
//   }
// };
</script>

<template>
  <div class="chat-container show">
    <div class="header">
      <button class="close-btn" @click="emit('close')" title="閉じる">×</button>
      <h1>AiDiy AI <span v-if="chatAi || liveAi" class="model-info">({{ chatAi }}, {{ liveAi }})</span></h1>
      <div class="status">
        <span :class="['status-dot', isWsConnected ? 'connecting' : 'disconnected']"></span>
        <span>{{ statusText }}</span>
      </div>
    </div>

    <div ref="chatArea" class="chat-area">
      <div class="welcome-message" v-if="welcomeInfo">
        {{ welcomeInfo }}
      </div>

      <div
        v-for="(message, index) in messages"
        :key="message.id"
        :id="message.id"
        :class="['message', message.role, message.kind === 'file' ? 'is-file' : '', message.isStream ? 'stream-output' : '', message.isCollapsed ? 'collapsed' : '']"
      >
        <div
          class="message-bubble"
          @click="message.isStream && message.isCollapsed ? toggleCollapse(message.id) : null"
          :style="{ cursor: message.isStream && message.isCollapsed ? 'pointer' : 'default' }"
        >
          <div v-if="message.isStream && message.isCollapsed" class="collapsed-wrapper">
            <span class="collapsed-indicator">...</span>
            <span class="collapsed-arrow">◀</span>
          </div>
          <div v-show="!(message.isStream && message.isCollapsed)" class="bubble-content">
            <template v-if="message.kind === 'file'">
              <div class="file-message">
                <div class="file-name"><span v-if="message.role === 'input_file'">ファイル入力: </span><span v-if="message.role === 'output_file'">ファイル出力: </span>{{ message.fileName || 'ファイル受信' }}</div>
                <img
                  v-if="message.thumbnail"
                  class="file-thumbnail"
                  :src="`data:image/png;base64,${message.thumbnail}`"
                  alt="thumbnail"
                />
              </div>
            </template>
            <template v-else-if="message.render === 'static'">
              {{ message.content }}
            </template>
            <template v-else-if="message.render === 'effect'">
              <!-- ターミナルエフェクトがここに直接DOMを書き込む -->
            </template>
          </div>
          <span
            v-if="message.isStream && !message.isCollapsed"
            class="expand-indicator"
            @click.stop="toggleCollapse(message.id)"
            title="折りたたむ"
          >▼</span>
        </div>
      </div>

    </div>

    <div class="control-area">
      <!-- テキスト入力エリア -->
      <div
        class="text-input-area"
        :class="{ 'drag-over': isDragOver }"
        @dragover="handleDragOver"
        @dragleave="handleDragLeave"
        @drop="handleDrop"
      >
        <div class="input-container">
          <span class="prompt-symbol">&gt;</span>
          <textarea
            v-model="inputText"
            class="input-field"
            placeholder="メッセージを入力..."
            maxlength="500"
            :disabled="!isWsConnected"
            @input="autoResize"
            ref="textareaRef"
          ></textarea>
        </div>
      </div>

      <!-- モード選択（縦並び） -->
      <div class="mode-panel">
        <div class="mode-selector">
          <label class="mode-option">
            <input type="radio" v-model="selectedMode" value="chat" name="mode" />
            <span>Chat</span>
          </label>
          <label class="mode-option">
            <input type="radio" v-model="selectedMode" value="live" name="mode" />
            <span>Live</span>
          </label>
          <label class="mode-option">
            <input type="radio" v-model="selectedMode" value="code1" name="mode" />
            <span>Code1</span>
          </label>
        </div>

        <div class="code-selector">
          <label class="mode-option">
            <input type="radio" v-model="selectedMode" value="code2" name="mode" />
            <span>Code2</span>
          </label>
          <label class="mode-option">
            <input type="radio" v-model="selectedMode" value="code3" name="mode" />
            <span>Code3</span>
          </label>
          <label class="mode-option">
            <input type="radio" v-model="selectedMode" value="code4" name="mode" />
            <span>Code4</span>
          </label>
        </div>
      </div>

      <!-- 送信ボタン -->
      <button
        class="chat-send-btn"
        :class="{
          'ws-disabled': !isWsConnected,
          'has-text': inputText.length > 0
        }"
        @click="sendMessage"
        :disabled="!inputText.trim() || !isWsConnected"
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

.message.recognition_input .message-bubble {
  color: #e5e7eb;
  border-left: 4px solid rgba(187, 187, 187, 0.7);
}

.message.output_text .message-bubble {
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
  display: inline-block;
  width: 8px;
  height: 14px;
  background-color: #00ff00;
  margin-left: 1px;
  animation: blink 1s infinite;
  vertical-align: text-bottom;
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
