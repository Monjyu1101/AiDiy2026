<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import apiClient from '@/lib/api'
import { AI_WS_ENDPOINT } from '@/lib/config'
import { AIWebSocket } from '@/lib/websocket'

type ファイル項目 = {
  パス: string
  更新日時: string
}

const props = defineProps<{
  sessionId: string;
}>()

const タブ = ref<'backup' | 'temp'>('backup')
const バックアップ一覧 = ref<ファイル項目[]>([])
const テンポラリ一覧 = ref<ファイル項目[]>([])
const 選択ファイルパス = ref('')
const エディタ内容 = ref('')
const 読込中 = ref(false)
const 保存中 = ref(false)
const エラー = ref('')
const プロジェクトパス = ref('')
const 最終ファイル日時 = ref('')
const 作業ファイル日時 = ref('')
const 接続済み = ref(false)
const テキスト編集可能 = ref(true)

let fileSocket: AIWebSocket | null = null

const 現在一覧 = computed(() => (タブ.value === 'backup' ? バックアップ一覧.value : テンポラリ一覧.value))
const 接続状態表示 = computed(() => (接続済み.value ? '接続中' : '切断'))

async function connectFileSocket() {
  if (!props.sessionId) return
  fileSocket?.disconnect()
  fileSocket = new AIWebSocket(AI_WS_ENDPOINT, props.sessionId, 'file')
  fileSocket.onStateChange((connected) => {
    接続済み.value = connected
  })
  fileSocket.on('files_backup', (message) => {
    const payload = (message.メッセージ内容 || {}) as Record<string, unknown>
    バックアップ一覧.value = Array.isArray(payload.ファイルリスト) ? (payload.ファイルリスト as ファイル項目[]) : []
    プロジェクトパス.value = String(payload.プロジェクトパス || '')
    最終ファイル日時.value = String(payload.最終ファイル日時 || '')
  })
  fileSocket.on('files_temp', (message) => {
    const payload = (message.メッセージ内容 || {}) as Record<string, unknown>
    テンポラリ一覧.value = Array.isArray(payload.ファイルリスト) ? (payload.ファイルリスト as ファイル項目[]) : []
    作業ファイル日時.value = String(payload.作業ファイル日時 || '')
  })
  try {
    await fileSocket.connect()
    requestLists()
  } catch (error) {
    エラー.value = error instanceof Error ? error.message : 'file channel 接続失敗'
  }
}

function requestLists() {
  if (!fileSocket?.isConnected()) return
  fileSocket.send({
    セッションID: props.sessionId,
    チャンネル: 'file',
    メッセージ識別: 'files_backup',
    メッセージ内容: { 要求日時: 0 },
  })
  fileSocket.send({
    セッションID: props.sessionId,
    チャンネル: 'file',
    メッセージ識別: 'files_temp',
    メッセージ内容: { 要求日時: 60 },
  })
}

function decodeBase64(base64: string, path: string) {
  const binary = atob(base64)
  const bytes = Uint8Array.from(binary, (ch) => ch.charCodeAt(0))
  const ext = path.split('.').pop()?.toLowerCase() || ''
  const encoding = ext === 'bat' || ext === 'cmd' ? 'shift_jis' : 'utf-8'
  try {
    return new TextDecoder(encoding).decode(bytes)
  } catch {
    return new TextDecoder('utf-8').decode(bytes)
  }
}

function isTextFile(path: string) {
  const ext = path.split('.').pop()?.toLowerCase() || ''
  return ['py', 'ts', 'tsx', 'js', 'jsx', 'json', 'md', 'txt', 'html', 'css', 'vue', 'yml', 'yaml', 'toml', 'ini', 'cmd', 'bat', 'ps1', 'sh', 'log'].includes(ext)
}

async function openFile(path: string) {
  if (!path) return
  読込中.value = true
  エラー.value = ''
  選択ファイルパス.value = path
  try {
    const response = await apiClient.post('/core/files/内容取得', { ファイル名: path })
    if (response.data.status !== 'OK') {
      throw new Error(response.data.message || 'ファイル内容取得失敗')
    }
    テキスト編集可能.value = isTextFile(path)
    エディタ内容.value = テキスト編集可能.value
      ? decodeBase64(response.data.data.base64_data, path)
      : 'このファイルはテキスト編集対象外です。'
  } catch (error) {
    エラー.value = error instanceof Error ? error.message : 'ファイルを開けませんでした。'
  } finally {
    読込中.value = false
  }
}

async function saveFile() {
  if (!選択ファイルパス.value || !テキスト編集可能.value) return
  保存中.value = true
  エラー.value = ''
  try {
    const response = await apiClient.post('/core/files/内容更新', {
      ファイル名: 選択ファイルパス.value,
      内容: エディタ内容.value,
    })
    if (response.data.status !== 'OK') {
      throw new Error(response.data.message || '保存失敗')
    }
    fileSocket?.send({
      セッションID: props.sessionId,
      チャンネル: 'file',
      メッセージ識別: 'files_save',
      メッセージ内容: { ファイル名: 選択ファイルパス.value },
    })
    requestLists()
  } catch (error) {
    エラー.value = error instanceof Error ? error.message : '保存できませんでした。'
  } finally {
    保存中.value = false
  }
}

watch(() => props.sessionId, () => {
  if (props.sessionId) {
    void connectFileSocket()
  }
})

onMounted(() => {
  if (props.sessionId) {
    void connectFileSocket()
  }
})

onBeforeUnmount(() => {
  fileSocket?.disconnect()
  fileSocket = null
})
</script>

<template>
  <section class="file-container">
    <div class="file-header">
      <h1>AiDiy File</h1>
      <div class="status">
        <span :class="['status-dot', 接続済み ? 'connecting' : 'disconnected']"></span>
        <span>{{ 接続状態表示 }}</span>
      </div>
    </div>

    <div class="meta-bar">
      <span>PROJECT: {{ プロジェクトパス || '未取得' }}</span>
      <span>BACKUP: {{ 最終ファイル日時 || '-' }}</span>
      <span>TEMP: {{ 作業ファイル日時 || '-' }}</span>
      <button class="meta-button" type="button" @click="requestLists">REFRESH</button>
    </div>

    <div class="file-layout">
      <aside class="file-sidebar">
        <div class="tab-buttons">
          <button class="tab-button" :class="{ active: タブ === 'backup' }" type="button" @click="タブ = 'backup'">BACKUP</button>
          <button class="tab-button" :class="{ active: タブ === 'temp' }" type="button" @click="タブ = 'temp'">TEMP</button>
        </div>

        <div class="file-list">
          <button
            v-for="item in 現在一覧"
            :key="item.パス"
            class="file-item"
            :class="{ active: 選択ファイルパス === item.パス }"
            type="button"
            @click="openFile(item.パス)"
          >
            <strong>{{ item.パス }}</strong>
            <span>{{ item.更新日時 }}</span>
          </button>
          <div v-if="現在一覧.length === 0" class="empty-list">ファイルはありません。</div>
        </div>
      </aside>

      <section class="editor-pane">
        <div class="editor-toolbar">
          <span class="path-label">{{ 選択ファイルパス || 'ファイルを選択してください' }}</span>
          <div class="editor-actions">
            <button class="meta-button" type="button" :disabled="!選択ファイルパス || 読込中" @click="openFile(選択ファイルパス)">RELOAD</button>
            <button class="meta-button save" type="button" :disabled="!選択ファイルパス || 保存中 || !テキスト編集可能" @click="saveFile">SAVE</button>
          </div>
        </div>

        <textarea
          v-model="エディタ内容"
          class="editor"
          :disabled="!選択ファイルパス || 読込中 || !テキスト編集可能"
          placeholder="左の一覧からファイルを選択してください"
        ></textarea>

        <div v-if="エラー" class="error-box">{{ エラー }}</div>
      </section>
    </div>
  </section>
</template>

<style scoped>
.file-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #111;
}

.file-header {
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

.file-header h1 {
  margin: 0;
  font-size: 22px;
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

.status-dot.disconnected { background: #888; }
.status-dot.connecting { background: #44ff44; }

.meta-bar {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 8px 12px;
  background: #1a1a1a;
  color: #d0d7e2;
  font-family: "Courier New", monospace;
  font-size: 11px;
  border-bottom: 1px solid #2c2c2c;
}

.file-layout {
  flex: 1;
  display: grid;
  grid-template-columns: 300px 1fr;
  min-height: 0;
}

.file-sidebar {
  border-right: 1px solid #2c2c2c;
  background: #0d0d0d;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.tab-buttons {
  display: grid;
  grid-template-columns: 1fr 1fr;
}

.tab-button,
.meta-button {
  height: 32px;
  border: 1px solid #667eea;
  background: rgba(255, 255, 255, 0.92);
  color: #000;
  cursor: pointer;
  font-family: "Courier New", monospace;
  font-size: 12px;
  font-weight: bold;
}

.tab-button.active {
  background: #667eea;
  color: #fff;
}

.meta-button.save {
  background: #667eea;
  color: #fff;
}

.meta-button:disabled {
  background: #808080;
  border-color: #808080;
  color: #fff;
  cursor: not-allowed;
}

.file-list {
  flex: 1;
  overflow: auto;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.file-item {
  text-align: left;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: #151515;
  color: #dce3ee;
  padding: 8px;
  cursor: pointer;
  display: grid;
  gap: 4px;
}

.file-item strong,
.file-item span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-item strong {
  font-size: 12px;
}

.file-item span {
  color: #8e9aac;
  font-size: 10px;
}

.file-item.active {
  border-color: #44ff44;
  background: #050505;
}

.empty-list {
  color: #7f8a99;
  font-family: "Courier New", monospace;
  padding: 8px;
}

.editor-pane {
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-bottom: 1px solid #2c2c2c;
  background: #151515;
}

.path-label {
  color: #dde5f0;
  font-family: "Courier New", monospace;
  font-size: 11px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.editor-actions {
  display: flex;
  gap: 8px;
}

.editor {
  flex: 1;
  width: 100%;
  resize: none;
  border: none;
  outline: none;
  background: #000;
  color: #e5ecf5;
  padding: 14px;
  font-family: "Consolas", "Courier New", monospace;
  font-size: 13px;
  line-height: 1.5;
}

.editor:disabled {
  color: #7f8a99;
}

.error-box {
  padding: 8px 12px;
  color: #ffb4b4;
  background: rgba(127, 29, 29, 0.22);
  border-top: 1px solid rgba(255, 98, 98, 0.28);
  font-size: 12px;
}

@media (max-width: 980px) {
  .file-layout {
    grid-template-columns: 1fr;
  }

  .file-sidebar {
    border-right: none;
    border-bottom: 1px solid #2c2c2c;
    max-height: 220px;
  }

  .meta-bar,
  .editor-toolbar {
    flex-wrap: wrap;
  }
}
</style>
