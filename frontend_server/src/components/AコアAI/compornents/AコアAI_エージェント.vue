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
import { ref, onMounted, onBeforeUnmount, watch, computed, nextTick } from 'vue';
import { AコアAIWebSocket, createWebSocketUrl, type IWebSocketClient } from '@/api/websocket';

const props = defineProps<{
  socketId?: string;
  チャンネル?: number;
  codeAi?: string;
  inputWsClient?: IWebSocketClient | null;
  inputConnected?: boolean;
}>();

const emit = defineEmits<{
  close: [];
}>();

const outputWsClient = ref<IWebSocketClient | null>(null);
const outputConnected = ref(false);
const isWsConnected = computed(() => (props.inputConnected ?? false) && outputConnected.value);

// メッセージ構造体
interface Message {
  id: string;
  role: 'input_text' | 'output_text' | 'input_file' | 'output_file';
  content: string;
  render: 'effect' | 'static';
  kind: 'text' | 'file';
  fileName?: string | null;
  thumbnail?: string | null;
  terminalEffect?: any;
  isStream?: boolean;
  isCollapsed?: boolean;
}

let messageIdCounter = 0;
const messages = ref<Message[]>([]);
const contentArea = ref<HTMLElement | null>(null);

const connectionStatus = computed<'disconnected' | 'connected'>(() => (
  isWsConnected.value ? 'connected' : 'disconnected'
));

// テキスト入力関連
const inputText = ref('');
const textareaRef = ref<HTMLTextAreaElement | null>(null);
const isLoading = ref(false);
const isDragOver = ref(false);

// メッセージ送信（input_textとして送信）
const sendMessage = async () => {
  if (!inputText.value.trim() || isLoading.value || !isWsConnected.value) return;

  const message = inputText.value.trim();
  inputText.value = '';

  // テキストエリアの高さをリセット
  if (textareaRef.value) {
    textareaRef.value.style.height = '60px';
  }

  // ローカル表示はせず、サーバーからのエコーバックで表示

  // input_textとして送信（入力チャンネル=-1、出力先チャンネルで振り分け）
  if (props.inputWsClient && props.inputWsClient.isConnected()) {
    const 出力先チャンネル = props.チャンネル ?? 0;
    props.inputWsClient.send({
      ソケットID: props.socketId ?? '',
      チャンネル: -1,  // 入力は常に-1
      出力先チャンネル: 出力先チャンネル,  // バックエンドが振り分け
      メッセージ識別: 'input_text',
      メッセージ内容: message
    });
  }
};

// 画像ファイル送信（input_fileとして送信）
const sendInputFile = async (file: File) => {
  if (!props.inputWsClient || !isWsConnected.value) return;

  try {
    const reader = new FileReader();
    reader.onload = async (e) => {
      const base64Data = e.target?.result as string;
      const 出力先チャンネル = props.チャンネル ?? 0;

      // ローカルフィードバック表示は不要（サーバーからのエコーバックで表示）

      props.inputWsClient?.send({
        ソケットID: props.socketId ?? '',
        チャンネル: -1,  // 入力は常に-1
        出力先チャンネル: 出力先チャンネル,  // バックエンドが振り分け
        メッセージ識別: 'input_file',
        メッセージ内容: base64Data,
        ファイル名: file.name,
        サムネイル画像: null
      });
    };
    reader.readAsDataURL(file);
  } catch (error) {
    console.error('[エージェント] ファイル送信エラー:', error);
    addLine('[エラー] ファイル送信に失敗しました。');
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

// テキストエリアの自動リサイズ
const autoResize = () => {
  if (!textareaRef.value) return;
  textareaRef.value.style.height = '60px';
  const scrollHeight = textareaRef.value.scrollHeight;
  if (scrollHeight > 60) {
    textareaRef.value.style.height = Math.min(scrollHeight, 150) + 'px';
  }
};

// 自動スクロール
const scrollToBottom = () => {
  nextTick(() => {
    if (contentArea.value) {
      contentArea.value.scrollTop = contentArea.value.scrollHeight;
    }
  });
};

// ターミナルエフェクト関数
const createTerminalEffect = (container: HTMLElement, text: string, messageType: string) => {
  const typingSpeed = 10;
  const initialDelay = 300;

  // メッセージタイプに応じたカーソル色
  const cursorColors: { [key: string]: string } = {
    'input_text': '#ffffff',
    'output_text': '#ffaa00',
    'input_file': '#ffffff',
    'output_file': '#ffaa00'
  };

  const cursorColor = cursorColors[messageType] || '#ffaa00';

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
  const messageId = `agent-message-${messageIdCounter++}`;
  messages.value.push({
    id: messageId,
    role,
    content,
    render: 'effect',
    kind: 'text'
  });

  nextTick(() => {
    const messageElement = document.getElementById(messageId);
    if (messageElement) {
      const bubbleElement = messageElement.querySelector('.content-area') as HTMLElement;
      if (bubbleElement) {
        // 既存のコンテンツをクリア
        bubbleElement.innerHTML = '';
        // ターミナルエフェクトを開始
        const effect = createTerminalEffect(bubbleElement, content, role);
        const message = messages.value.find(m => m.id === messageId);
        if (message) {
          message.terminalEffect = effect;
        }
      }
    }
  });
};

const addFileMessage = (role: Message['role'], fileName?: string | null, thumbnail?: string | null) => {
  const messageId = `agent-message-${messageIdCounter++}`;
  messages.value.push({
    id: messageId,
    role,
    content: '',
    render: 'static',
    kind: 'file',
    fileName: fileName ?? null,
    thumbnail: thumbnail ?? null
  });
  scrollToBottom();
};

// ターミナル風の出力を追加
const addLine = (text: string) => {
  messages.value.push({
    id: `agent-message-${messageIdCounter++}`,
    role: 'output_text',
    content: text,
    render: 'static',
    kind: 'text'
  });
  scrollToBottom();
};

// WebSocketイベントハンドラ
const hasWelcomeInfo = ref(false);
const welcomeInfo = ref<string>('');

const handleWelcomeInfo = (message: any) => {
  const content = message.メッセージ内容 ?? message.text ?? '';
  if (!content) return;
  const text = typeof content === 'string' ? content : JSON.stringify(content);
  welcomeInfo.value = text;
  hasWelcomeInfo.value = true;
};
const handleInputText = (message: any) => {
  const content = message.メッセージ内容 ?? message.text ?? '';
  if (!content) return;
  const text = typeof content === 'string' ? content : JSON.stringify(content);
  addMessageWithEffect('input_text', `> ${text}`);
};

const handleInputFile = (message: any) => {
  const fileName = message.ファイル名 ?? null;
  const thumbnail = message.サムネイル画像 ?? null;
  addFileMessage('input_file', fileName, thumbnail);
};

const handleOutputText = (message: any) => {
  const content = message.メッセージ内容 ?? message.text ?? '';
  if (!content) return;
  const text = typeof content === 'string' ? content : JSON.stringify(content);
  addMessageWithEffect('output_text', text);
};

const handleOutputFile = (message: any) => {
  const fileName = message.ファイル名 ?? null;
  const thumbnail = message.サムネイル画像 ?? null;
  addFileMessage('output_file', fileName, thumbnail);
};

// ストリーム表示用の一時メッセージID
let streamMessageId: string | null = null;
let streamBubbleElement: HTMLElement | null = null;

const handleOutputStream = (message: any) => {
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
      isStream: true
    });

    // DOMを取得してターミナルエフェクトで処理開始メッセージを追加
    nextTick(() => {
      const messageElement = document.getElementById(streamMessageId!);
      if (messageElement) {
        const contentArea = messageElement.querySelector('.content-area') as HTMLElement;
        if (contentArea) {
          streamBubbleElement = contentArea;
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
  
  console.log(`[エージェント${ch}] ハンドラ登録完了`);
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
  
  console.log(`[エージェント${ch}] ハンドラ削除完了`);
};

const connectOutputSocket = async () => {
  const チャンネル = props.チャンネル ?? 0;
  if (!props.socketId) {
    console.warn(`[エージェント${チャンネル}] socketId未確定のため出力ソケットを保留`);
    return;
  }

  const wsUrl = createWebSocketUrl('/ws/AコアAI');
  outputWsClient.value = new AコアAIWebSocket(wsUrl, props.socketId, チャンネル);
  registerWsHandlers(outputWsClient.value);

  try {
    await outputWsClient.value.connect();
    outputConnected.value = true;
    console.log(`[エージェント${チャンネル}] 出力ソケット接続完了`);
  } catch (error) {
    outputConnected.value = false;
    console.error(`[エージェント${チャンネル}] 出力ソケット接続エラー:`, error);
  }
};

onMounted(() => {
  const チャンネル = props.チャンネル ?? 0;
  console.log(`[エージェント${チャンネル}] ========== onMounted開始 ==========`);
  console.log(`[エージェント${チャンネル}] チャンネル=${チャンネル}`);
  console.log(`[エージェント${チャンネル}] socketId=${props.socketId}`);
  console.log(`[エージェント${チャンネル}] inputWsClient=${!!props.inputWsClient}`);
  console.log(`[エージェント${チャンネル}] inputConnected=${props.inputConnected}`);
  connectOutputSocket();
  console.log(`[エージェント${チャンネル}] ========== onMounted完了 ==========`);
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

onBeforeUnmount(() => {
  if (outputWsClient.value) {
    unregisterWsHandlers(outputWsClient.value);
    outputWsClient.value.disconnect();
    outputWsClient.value = null;
  }
  outputConnected.value = false;
});

// ステータステキスト
const getStatusText = () => {
  const statusMap = {
    disconnected: '切断',
    connected: '接続中'
  };
  return statusMap[connectionStatus.value];
};
</script>

<template>
  <div class="agent-container show">
    <div class="agent-header">
      <button class="close-btn" @click="emit('close')" title="閉じる">×</button>
      <h1>Code Agent ({{ チャンネル }}) <span v-if="codeAi" class="model-info">({{ codeAi }})</span></h1>
      <div class="agent-status">
        <div :class="['agent-status-dot', connectionStatus]"></div>
        <span>{{ getStatusText() }}</span>
      </div>
    </div>

    <div ref="contentArea" class="agent-content">
      <div class="welcome-message" v-if="welcomeInfo">
        {{ welcomeInfo }}
      </div>

      <div
        v-for="message in messages"
        :key="message.id"
        :id="message.id"
        :class="['terminal-line', message.role, message.isStream ? 'stream-output' : '', message.isCollapsed ? 'collapsed' : '']"
      >
        <div
          class="line-content"
          @click="message.isStream && message.isCollapsed ? toggleCollapse(message.id) : null"
          :style="{ cursor: message.isStream && message.isCollapsed ? 'pointer' : 'default' }"
        >
          <div v-if="message.isStream && message.isCollapsed" class="collapsed-wrapper">
            <span class="collapsed-indicator">...</span>
            <span class="collapsed-arrow">◀</span>
          </div>
          <div v-show="!(message.isStream && message.isCollapsed)" class="content-area">
            <template v-if="message.kind === 'file'">
              <div class="file-message">
                <div class="file-name">
                  <span v-if="message.role === 'input_file'">ファイル入力: </span>
                  <span v-if="message.role === 'output_file'">ファイル出力: </span>
                  {{ message.fileName || 'ファイル受信' }}
                </div>
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
            :disabled="isLoading || !isWsConnected"
            @input="autoResize"
            ref="textareaRef"
          ></textarea>
        </div>

        <button
          class="agent-send-btn"
          :class="{
            'ws-disabled': !isWsConnected,
            'has-text': inputText.length > 0
          }"
          @click="sendMessage"
          :disabled="!inputText.trim() || isLoading || !isWsConnected"
          title="送信"
        >
          <img src="/icons/sending.png" alt="送信" />
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.agent-container {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 2px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  width: 100%;
  height: 100%;
}

.agent-header {
  background: #c8c8c8;
  color: #333;
  padding: 5px 20px;
  text-align: center;
  position: relative;
}

.agent-header h1 {
  font-size: 22px;
  font-weight: bold;
  margin: 0;
  height: 28px;
  line-height: 28px;
}

.agent-header h1 .model-info {
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

.agent-status {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: bold;
}

.agent-status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.agent-status-dot.disconnected { background: #888888; }
.agent-status-dot.connected { background: #44ff44; }
.agent-status-dot.sending { background: #ff4444; }

.agent-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  overflow-x: auto;
  background: #000000;
  color: #00ff00;
  font-family: 'Courier New', monospace;
  font-size: 11px;
  line-height: 1.5;
  white-space: pre;
  box-sizing: border-box;
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


.terminal-line {
  margin: 0;
  padding: 0;
}

.line-content {
  display: inline;
  position: relative;
}

.terminal-text {
  display: inline;
  white-space: pre-wrap;
  font-family: 'Courier New', monospace;
  line-height: 1.1;
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

.terminal-line.input_text .line-content {
  color: #ffffff;
}

.terminal-line.output_text .line-content {
  color: #00ff00;
}

.terminal-line.stream-output .line-content {
  background: rgba(0, 255, 0, 0.08);
  border-radius: 4px;
  padding: 8px 12px;
  display: block;
  position: relative;
}

.terminal-line.stream-output.collapsed .line-content {
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

.terminal-line.input_file .line-content,
.terminal-line.output_file .line-content {
  display: block;
}

.file-message {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
}

/* input_file: 白いボーダー */
.terminal-line.input_file .file-message {
  border-left: 4px solid rgba(255, 255, 255, 0.7);
}

/* output_file: 緑のボーダー */
.terminal-line.output_file .file-message {
  border-left: 4px solid rgba(0, 255, 0, 0.7);
}

/* input_fileのサムネイルは非表示 */
.terminal-line.input_file .file-thumbnail {
  display: none;
}

/* output_fileのサムネイルも非表示 */
.terminal-line.output_file .file-thumbnail {
  display: none;
}

.file-name {
  font-size: 11px;
  font-family: 'Courier New', monospace;
  color: #ffffff;
}

/* output_fileのファイル名は緑 */
.terminal-line.output_file .file-name {
  color: #00ff00;
}

.file-thumbnail {
  max-width: 320px;
  max-height: 240px;
  border-radius: 2px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.file-thumbnail:hover {
  opacity: 0.8;
  transform: scale(1.02);
}

.terminal-cursor {
  display: inline-block;
  width: 8px;
  height: 14px;
  background-color: #ffaa00;
  margin-left: 1px;
  animation: blink 1s infinite;
  vertical-align: text-bottom;
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

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* スクロールバーのスタイル（細く） */
.agent-content::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.agent-content::-webkit-scrollbar-track {
  background: #1a1a1a;
}

.agent-content::-webkit-scrollbar-thumb {
  background: #666666;
  border-radius: 2px;
}

.agent-content::-webkit-scrollbar-thumb:hover {
  background: #888888;
}

/* テキスト入力エリア */
.control-area {
  padding: 10px 20px 0 20px; /* チャットと同じpadding */
  background: #000000; /* 黒背景を維持 */
  border-top: 1px solid #333;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 15px; /* チャットと同じgap */
}

.text-input-area {
  display: flex;
  gap: 10px;
  align-items: flex-end;
}

.text-input-area.drag-over {
  background: rgba(102, 126, 234, 0.2);
  border: 2px dashed #667eea;
  border-radius: 4px;
  padding: 8px;
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
  border: 2px solid rgba(255, 255, 255, 0.5);
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
  height: 60px;
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

/* 送信ボタン */
.agent-send-btn {
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
  background: rgba(255, 255, 255, 0.95);
  color: white;
  margin-left: 10px;
}

.agent-send-btn img {
  width: 34px;
  height: 34px;
  object-fit: contain;
  pointer-events: none;
  filter: brightness(0);
}

.agent-send-btn:hover:not(:disabled) {
  background: rgba(240, 240, 240, 0.95);
  border-color: #5a6fd8;
}

.agent-send-btn.has-text {
  background: #667eea;
  border-color: #667eea;
}

.agent-send-btn.has-text img {
  filter: brightness(0) invert(1);
}

.agent-send-btn.has-text:hover:not(:disabled) {
  background: #5a6fd8;
  border-color: #5a6fd8;
}

.agent-send-btn:disabled:not(.ws-disabled) {
  background: rgba(255, 255, 255, 0.95);
  border-color: #667eea;
  cursor: not-allowed;
  opacity: 1;
}

.agent-send-btn:disabled:not(.ws-disabled) img {
  filter: brightness(0);
}

.agent-send-btn.ws-disabled {
  background: #808080 !important;
  border-color: #808080 !important;
  box-shadow: none;
  cursor: not-allowed;
  opacity: 1;
}

.agent-send-btn.ws-disabled img {
  filter: brightness(0) invert(1) !important;
}

.agent-send-btn.ws-disabled:hover {
  transform: none;
}
</style>

