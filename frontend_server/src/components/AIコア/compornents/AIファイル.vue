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
import { ref, watch, onMounted, onBeforeUnmount, computed } from 'vue';
import { AIコアWebSocket, createWebSocketUrl, type IWebSocketClient } from '@/api/websocket';
import apiClient from '@/api/client';
import { シキHTML生成 } from '@/utils/shiki';

const プロパティ = defineProps<{
  セッションID?: string;
  active?: boolean;
  wsConnected?: boolean;
  wsClient?: IWebSocketClient | null;
}>();

const 通知 = defineEmits<{
  close: [];
}>();

// 出力WebSocket（channel="file" でサーバーからの返信を受信）
const 出力WebSocket = ref<IWebSocketClient | null>(null);
const 出力接続済み = ref(false);

// ファイルエントリ型
type ファイルエントリ = { パス: string; 更新日時: string };

// ファイルリストデータ
const プロジェクトパス = ref<string>('');
const バックアップベースパス = ref<string>('');
const 最終ファイル日時 = ref<string | null>(null);
const 最終ファイルリスト = ref<ファイルエントリ[]>([]);
const 作業ファイル日時 = ref<string | null>(null);
const 作業ファイルリスト = ref<ファイルエントリ[]>([]);
const 左読込中 = ref(false);
const 右読込中 = ref(false);
const 左展開中フォルダ = ref<Set<string>>(new Set());
const 右展開中フォルダ = ref<Set<string>>(new Set());

// 選択ファイル内容
const 選択ファイル名 = ref<string>('');
const 選択ファイルパス = ref<string>('');
const ファイル内容テキスト = ref<string | null>(null);
const ファイル内容ハイライトHTML = ref<string>('');
const ファイル内容画像 = ref<string | null>(null);
const ファイル内容エラー = ref<string | null>(null);
const ファイル読込中 = ref(false);
const ファイルダウンロード中 = ref(false);
let ハイライト要求連番 = 0;
let テンプリスト自動送信タイマー: ReturnType<typeof setInterval> | null = null;

const 画像拡張子 = new Set(['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'svg', 'ico']);

type ツリーノード種別 = 'folder' | 'file';
type ツリーノード = {
  名前: string;
  パス: string;
  種別: ツリーノード種別;
  更新日時?: string;
  子ノード: ツリーノード[];
};
type ツリー表示行 = {
  キー: string;
  名前: string;
  パス: string;
  種別: ツリーノード種別;
  深さ: number;
  展開中: boolean;
  更新日時?: string;
};
type ツリー内部ノード = {
  名前: string;
  パス: string;
  種別: ツリーノード種別;
  更新日時?: string;
  子Map: Map<string, ツリー内部ノード>;
};

const パス正規化 = (パス: string): string => {
  return (パス ?? '').replace(/\\/g, '/').replace(/^\/+|\/+$/g, '');
};

const 更新日時が本日 = (更新日時?: string): boolean => {
  if (!更新日時) return false;
  const now = new Date();
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, '0');
  const d = String(now.getDate()).padStart(2, '0');
  const 今日 = `${y}/${m}/${d}`;
  return 更新日時.trim().replace(/-/g, '/').startsWith(今日);
};

const 日時文字列をDate化 = (日時?: string | null): Date | null => {
  if (!日時) return null;
  const 正規化 = 日時.trim().replace(/-/g, '/');
  const m = 正規化.match(/^(\d{4})\/(\d{2})\/(\d{2})\s+(\d{2}):(\d{2})(?::(\d{2}))?$/);
  if (!m) return null;
  const 年 = Number(m[1]);
  const 月 = Number(m[2]) - 1;
  const 日 = Number(m[3]);
  const 時 = Number(m[4]);
  const 分 = Number(m[5]);
  const 秒 = Number(m[6] ?? '0');
  const d = new Date(年, 月, 日, 時, 分, 秒);
  return Number.isNaN(d.getTime()) ? null : d;
};

const 日時文字列正規化 = (日時?: string | null): string | null => {
  const d = 日時文字列をDate化(日時);
  if (!d) return null;
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const h = String(d.getHours()).padStart(2, '0');
  const mm = String(d.getMinutes()).padStart(2, '0');
  const s = String(d.getSeconds()).padStart(2, '0');
  return `${y}/${m}/${day} ${h}:${mm}:${s}`;
};

const 右側更新日時表示 = (更新日時?: string): string => {
  const 正規化 = 日時文字列正規化(更新日時);
  if (!正規化) return 更新日時 ?? '';
  const parts = 正規化.split(' ');
  return parts.length >= 2 ? parts[1] : 正規化;
};

const 右更新日時が現在から10分以内 = (更新日時?: string): boolean => {
  const 対象 = 日時文字列をDate化(更新日時);
  if (!対象) return false;
  const 現在 = new Date();
  const 差分ms = 現在.getTime() - 対象.getTime();
  return 差分ms >= 0 && 差分ms <= 10 * 60 * 1000;
};

const ノード並び替え = (a: ツリーノード, b: ツリーノード): number => {
  if (a.種別 !== b.種別) {
    return a.種別 === 'folder' ? -1 : 1;
  }
  return a.名前.localeCompare(b.名前, 'ja');
};

const ファイル一覧をツリー化 = (ファイル一覧: ファイルエントリ[]): ツリーノード[] => {
  const ルートMap = new Map<string, ツリー内部ノード>();

  for (const エントリ of ファイル一覧) {
    const 正規パス = パス正規化(エントリ.パス);
    if (!正規パス) continue;

    const セグメント = 正規パス.split('/').filter(Boolean);
    if (セグメント.length === 0) continue;

    let 現在Map = ルートMap;
    let 累積パス = '';
    for (let i = 0; i < セグメント.length; i++) {
      const 名前 = セグメント[i];
      const isFile = i === セグメント.length - 1;
      累積パス = 累積パス ? `${累積パス}/${名前}` : 名前;

      let 既存 = 現在Map.get(名前);
      if (!既存) {
        既存 = {
          名前,
          パス: 累積パス,
          種別: isFile ? 'file' : 'folder',
          更新日時: isFile ? エントリ.更新日時 : undefined,
          子Map: new Map<string, ツリー内部ノード>(),
        };
        現在Map.set(名前, 既存);
      } else if (!isFile && 既存.種別 === 'file') {
        既存.種別 = 'folder';
        既存.更新日時 = undefined;
      }

      if (!isFile) {
        現在Map = 既存.子Map;
      }
    }
  }

  const 内部を外部へ = (内部: ツリー内部ノード): ツリーノード => {
    const 子ノード = Array.from(内部.子Map.values()).map(内部を外部へ).sort(ノード並び替え);
    return {
      名前: 内部.名前,
      パス: 内部.パス,
      種別: 内部.種別,
      更新日時: 内部.更新日時,
      子ノード,
    };
  };

  return Array.from(ルートMap.values()).map(内部を外部へ).sort(ノード並び替え);
};

const ツリー行化 = (ノード一覧: ツリーノード[], 展開中フォルダ: Set<string>, 深さ = 0): ツリー表示行[] => {
  const 行一覧: ツリー表示行[] = [];
  for (const ノード of ノード一覧) {
    const 展開中 = ノード.種別 === 'folder' ? 展開中フォルダ.has(ノード.パス) : false;
    行一覧.push({
      キー: `${ノード.種別}:${ノード.パス}`,
      名前: ノード.名前,
      パス: ノード.パス,
      種別: ノード.種別,
      深さ,
      展開中,
      更新日時: ノード.更新日時,
    });
    if (ノード.種別 === 'folder' && 展開中) {
      行一覧.push(...ツリー行化(ノード.子ノード, 展開中フォルダ, 深さ + 1));
    }
  }
  return 行一覧;
};

const 全フォルダパス取得 = (ファイル一覧: ファイルエントリ[]): string[] => {
  const パスSet = new Set<string>();
  for (const エントリ of ファイル一覧) {
    const 正規パス = パス正規化(エントリ.パス);
    if (!正規パス) continue;
    const セグメント = 正規パス.split('/').filter(Boolean);
    let 累積パス = '';
    for (let i = 0; i < セグメント.length - 1; i++) {
      累積パス = 累積パス ? `${累積パス}/${セグメント[i]}` : セグメント[i];
      パスSet.add(累積パス);
    }
  }
  return Array.from(パスSet);
};

const 最終ファイルツリー = computed(() => ファイル一覧をツリー化(最終ファイルリスト.value));
const 作業ファイルツリー = computed(() => ファイル一覧をツリー化(作業ファイルリスト.value));
const 最終ファイル行 = computed(() => ツリー行化(最終ファイルツリー.value, 左展開中フォルダ.value));
const 作業ファイル行 = computed(() => ツリー行化(作業ファイルツリー.value, 右展開中フォルダ.value));

const フォルダ開閉 = (フォルダパス: string, isBackup: boolean) => {
  const 展開中 = isBackup ? 左展開中フォルダ : 右展開中フォルダ;
  const 次 = new Set(展開中.value);
  if (次.has(フォルダパス)) {
    次.delete(フォルダパス);
  } else {
    次.add(フォルダパス);
  }
  展開中.value = 次;
};

const ツリー行クリック = (行: ツリー表示行, isBackup: boolean) => {
  if (行.種別 === 'folder') {
    フォルダ開閉(行.パス, isBackup);
    return;
  }
  ファイルクリック(行.パス, isBackup);
};

const 下部ファイル表示クリア = () => {
  ハイライト要求連番++;
  選択ファイル名.value = '';
  選択ファイルパス.value = '';
  ファイル内容テキスト.value = null;
  ファイル内容ハイライトHTML.value = '';
  ファイル内容画像.value = null;
  ファイル内容エラー.value = null;
  ファイル読込中.value = false;
  ファイルダウンロード中.value = false;
};

const ファイル内容ハイライト生成 = async (ファイル名: string, 内容: string) => {
  const 現在連番 = ++ハイライト要求連番;
  try {
    const html = await シキHTML生成(内容, ファイル名);
    if (現在連番 !== ハイライト要求連番) return;
    ファイル内容ハイライトHTML.value = html;
  } catch {
    if (現在連番 !== ハイライト要求連番) return;
    ファイル内容ハイライトHTML.value = '';
  }
};

const ファイルクリック = async (ファイル名: string, isBackup: boolean) => {
  選択ファイル名.value = ファイル名;
  ファイル内容テキスト.value = null;
  ファイル内容ハイライトHTML.value = '';
  ファイル内容画像.value = null;
  ファイル内容エラー.value = null;
  ファイル読込中.value = true;

  // パス解決: バックアップはCODE_BASE_PATH絶対パス＋ファイル名、tempは"temp/xxx"をそのまま使用
  const パス = isBackup
    ? (プロジェクトパス.value ? プロジェクトパス.value.replace(/\\/g, '/') + '/' + ファイル名 : ファイル名)
    : ファイル名;
  選択ファイルパス.value = パス;

  try {
    const res = await apiClient.post('/core/files/内容取得', { ファイル名: パス });
    if (res.data.status !== 'OK') {
      ファイル内容エラー.value = res.data.message ?? 'エラー';
      return;
    }
    const base64 = res.data.data.base64_data as string;
    const ext = ファイル名.split('.').pop()?.toLowerCase() ?? '';
    if (画像拡張子.has(ext)) {
      const mime = ext === 'svg' ? 'image/svg+xml' : ext === 'jpg' || ext === 'jpeg' ? 'image/jpeg' : `image/${ext}`;
      ファイル内容画像.value = `data:${mime};base64,${base64}`;
    } else {
      const bytes = Uint8Array.from(atob(base64), c => c.charCodeAt(0));
      const テキスト = new TextDecoder('utf-8').decode(bytes);
      ファイル内容テキスト.value = テキスト;
      void ファイル内容ハイライト生成(ファイル名, テキスト);
    }
  } catch (e: any) {
    ファイル内容エラー.value = e?.message ?? '取得失敗';
  } finally {
    ファイル読込中.value = false;
  }
};

const ファイルダウンロード = async () => {
  if (!選択ファイルパス.value || ファイルダウンロード中.value) return;

  ファイルダウンロード中.value = true;
  try {
    const res = await apiClient.post('/core/files/内容取得', { ファイル名: 選択ファイルパス.value });
    if (res.data.status !== 'OK') {
      ファイル内容エラー.value = res.data.message ?? 'ダウンロード失敗';
      return;
    }

    const base64 = res.data.data.base64_data as string;
    const bytes = Uint8Array.from(atob(base64), c => c.charCodeAt(0));
    const blob = new Blob([bytes], { type: 'application/octet-stream' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 選択ファイル名.value.split(/[\\/]/).pop() || 'download';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (e: any) {
    ファイル内容エラー.value = e?.message ?? 'ダウンロード失敗';
  } finally {
    ファイルダウンロード中.value = false;
  }
};

// files_backup / files_temp を非同期で要求する
const ファイルリスト要求 = () => {
  if (!プロパティ.wsClient || !プロパティ.wsClient.isConnected()) return;
  下部ファイル表示クリア();
  左読込中.value = true;
  右読込中.value = true;
  プロパティ.wsClient.send({
    セッションID: プロパティ.セッションID ?? '',
    チャンネル: 'file',
    メッセージ識別: 'files_backup',
    メッセージ内容: ''
  });
  プロパティ.wsClient.send({
    セッションID: プロパティ.セッションID ?? '',
    チャンネル: 'file',
    メッセージ識別: 'files_temp',
    メッセージ内容: ''
  });
};

const テンプリスト要求 = () => {
  if (!プロパティ.wsClient || !プロパティ.wsClient.isConnected()) return;
  プロパティ.wsClient.send({
    セッションID: プロパティ.セッションID ?? '',
    チャンネル: 'file',
    メッセージ識別: 'files_temp',
    メッセージ内容: ''
  });
};

const テンプリスト自動送信開始 = () => {
  if (テンプリスト自動送信タイマー) return;
  テンプリスト自動送信タイマー = setInterval(() => {
    if (!プロパティ.active) return;
    void テンプリスト要求();
  }, 10_000);
};

const テンプリスト自動送信停止 = () => {
  if (!テンプリスト自動送信タイマー) return;
  clearInterval(テンプリスト自動送信タイマー);
  テンプリスト自動送信タイマー = null;
};

// files_backup 受信処理
const バックアップリスト受信処理 = (受信データ: any) => {
  const 内容 = 受信データ.メッセージ内容;
  if (!内容) return;
  const 新日時 = 内容.最終ファイル日時 ?? null;
  const 新件数 = (内容.ファイルリスト ?? []).length;
  // 件数・最終更新日時が同じなら表示更新不要
  if (新日時 === 最終ファイル日時.value && 新件数 === 最終ファイルリスト.value.length) {
    左読込中.value = false;
    return;
  }
  プロジェクトパス.value = 内容.プロジェクトパス ?? '';
  バックアップベースパス.value = 内容.バックアップベースパス ?? '';
  最終ファイル日時.value = 新日時;
  最終ファイルリスト.value = 内容.ファイルリスト ?? [];
  左展開中フォルダ.value = new Set();
  左読込中.value = false;
};

// files_temp 受信処理
const テンプリスト受信処理 = (受信データ: any) => {
  const 内容 = 受信データ.メッセージ内容;
  if (!内容) return;
  const 正規化日時 = 日時文字列正規化(内容.作業ファイル日時);
  const 新日時 = 正規化日時 ?? 内容.作業ファイル日時 ?? null;
  const 新リスト = ((内容.ファイルリスト ?? []) as ファイルエントリ[]).map((f) => ({
    パス: f.パス,
    更新日時: 日時文字列正規化(f.更新日時) ?? (f.更新日時 ?? ''),
  }));
  const 新件数 = 新リスト.length;
  // 件数・最終更新日時が同じなら表示更新不要
  if (新日時 === 作業ファイル日時.value && 新件数 === 作業ファイルリスト.value.length) {
    右読込中.value = false;
    return;
  }
  作業ファイル日時.value = 新日時;
  作業ファイルリスト.value = 新リスト;
  右展開中フォルダ.value = new Set(全フォルダパス取得(作業ファイルリスト.value));
  右読込中.value = false;

  if (新日時) {
    const 最終日時一致ファイル = 新リスト.find((f) => f.更新日時 === 新日時)
      ?? 新リスト.find((f) => f.更新日時.slice(0, 16) === 新日時.slice(0, 16));
    if (最終日時一致ファイル) {
      void ファイルクリック(最終日時一致ファイル.パス, false);
    }
  }
};

// 出力ソケット接続（channel="file"）
const 出力ソケット接続 = async () => {
  if (!プロパティ.セッションID) return;
  const wsUrl = createWebSocketUrl('/core/ws/AIコア');
  出力WebSocket.value = new AIコアWebSocket(wsUrl, プロパティ.セッションID, 'file');
  出力WebSocket.value.on('files_backup', バックアップリスト受信処理);
  出力WebSocket.value.on('files_temp', テンプリスト受信処理);
  try {
    await 出力WebSocket.value.connect();
    出力接続済み.value = true;
    console.log('[AIファイル] 出力ソケット接続完了 (ch=file)');
  } catch (error) {
    出力接続済み.value = false;
    console.error('[AIファイル] 出力ソケット接続エラー:', error);
  }
};

const 出力ソケット切断 = () => {
  if (出力WebSocket.value) {
    出力WebSocket.value.off('files_backup', バックアップリスト受信処理);
    出力WebSocket.value.off('files_temp', テンプリスト受信処理);
    出力WebSocket.value.disconnect();
    出力WebSocket.value = null;
  }
  出力接続済み.value = false;
};

// アクティブになったらリスト要求
watch(() => プロパティ.active, (新値) => {
  if (新値) {
    ファイルリスト要求();
    テンプリスト自動送信開始();
  } else {
    テンプリスト自動送信停止();
  }
});

// セッションID変化時にソケット再接続
watch(() => プロパティ.セッションID, async (newId, oldId) => {
  if (!newId || newId === oldId) return;
  出力ソケット切断();
  await 出力ソケット接続();
  if (プロパティ.active) {
    ファイルリスト要求();
  }
});

onMounted(async () => {
  await 出力ソケット接続();
  if (プロパティ.active) {
    ファイルリスト要求();
    テンプリスト自動送信開始();
  }
});

onBeforeUnmount(() => {
  テンプリスト自動送信停止();
  出力ソケット切断();
});
</script>

<template>
  <div class="file-container show">
    <div class="file-header">
      <button class="close-btn" @click="通知('close')" title="閉じる">×</button>
      <h1>File Manager</h1>
      <button class="reload-btn" @click="ファイルリスト要求" title="再読込" :disabled="左読込中 || 右読込中">↺</button>
    </div>

    <div class="file-body">
      <!-- 上段: 左右分割 -->
      <div class="upper-area">

        <!-- 上段左: 最終バックアップのファイルツリー -->
        <div class="tree-panel left-panel">
          <div class="panel-header">
            最終バックアップ
            <span v-if="プロジェクトパス" class="panel-project">{{ プロジェクトパス }}</span>
            <span class="header-spacer"></span>
            <span v-if="最終ファイルリスト.length > 0" class="panel-count">({{ 最終ファイルリスト.length }})</span>
            <span v-if="最終ファイル日時" class="panel-datetime">{{ 最終ファイル日時 }}</span>
          </div>
          <div class="panel-content">
            <div v-if="左読込中" class="placeholder-content">
              <span class="placeholder-icon">⏳</span>
              <div>読込中...</div>
            </div>
            <div v-else-if="最終ファイルリスト.length === 0" class="placeholder-content">
              <span class="placeholder-icon">🗂️</span>
              <div>バックアップなし</div>
            </div>
            <ul v-else class="tree-list">
              <li
                v-for="行 in 最終ファイル行"
                :key="`left-${行.キー}`"
                class="tree-item"
                :class="{
                  folder: 行.種別 === 'folder',
                  selected: 行.種別 === 'file' && 選択ファイル名 === 行.パス
                }"
                @click="ツリー行クリック(行, true)"
              >
                <span class="tree-indent" :style="{ width: `${行.深さ * 14}px` }"></span>
                <span class="tree-toggle">
                  {{ 行.種別 === 'folder' ? (行.展開中 ? '▾' : '▸') : ' ' }}
                </span>
                <span class="tree-icon">
                  {{ 行.種別 === 'folder' ? (行.展開中 ? '📂' : '📁') : '📄' }}
                </span>
                <span class="tree-name">{{ 行.名前 }}</span>
                <span
                  v-if="行.種別 === 'file' && 行.更新日時"
                  class="tree-datetime"
                  :class="{ 'tree-datetime-today': 更新日時が本日(行.更新日時) }"
                >
                  {{ 行.更新日時 }}
                </span>
              </li>
            </ul>
          </div>
        </div>

        <!-- 上段右: tempフォルダのファイルツリー -->
        <div class="tree-panel right-panel">
          <div class="panel-header">
            tempフォルダ(1時間以内)
            <span class="header-spacer"></span>
            <span v-if="作業ファイルリスト.length > 0" class="panel-count">({{ 作業ファイルリスト.length }})</span>
            <span v-if="作業ファイル日時" class="panel-datetime">{{ 作業ファイル日時 }}</span>
          </div>
          <div class="panel-content">
            <div v-if="右読込中" class="placeholder-content">
              <span class="placeholder-icon">⏳</span>
              <div>読込中...</div>
            </div>
            <div v-else-if="作業ファイルリスト.length === 0" class="placeholder-content">
              <span class="placeholder-icon">📁</span>
              <div>ファイルなし</div>
            </div>
            <ul v-else class="tree-list">
              <li
                v-for="行 in 作業ファイル行"
                :key="`right-${行.キー}`"
                class="tree-item"
                :class="{
                  folder: 行.種別 === 'folder',
                  selected: 行.種別 === 'file' && 選択ファイル名 === 行.パス
                }"
                @click="ツリー行クリック(行, false)"
              >
                <span class="tree-indent" :style="{ width: `${行.深さ * 14}px` }"></span>
                <span class="tree-toggle">
                  {{ 行.種別 === 'folder' ? (行.展開中 ? '▾' : '▸') : ' ' }}
                </span>
                <span class="tree-icon">
                  {{ 行.種別 === 'folder' ? (行.展開中 ? '📂' : '📁') : '📄' }}
                </span>
                <span class="tree-name">{{ 行.名前 }}</span>
                <span
                  v-if="行.種別 === 'file' && 行.更新日時"
                  class="tree-datetime"
                  :class="{ 'tree-datetime-recent': 右更新日時が現在から10分以内(行.更新日時) }"
                >
                  {{ 右側更新日時表示(行.更新日時) }}
                </span>
              </li>
            </ul>
          </div>
        </div>

      </div>

      <!-- 下段: 選択ファイル内容表示 -->
      <div class="lower-area">
        <div class="panel-header">
          <span>ファイル内容</span>
          <span class="header-spacer"></span>
          <span v-if="選択ファイル名" class="panel-datetime">{{ 選択ファイル名 }}</span>
          <button
            class="download-btn"
            @click="ファイルダウンロード"
            :disabled="!選択ファイルパス || ファイル読込中 || ファイルダウンロード中"
            title="ダウンロード"
          >
            ⬇
          </button>
        </div>
        <div class="panel-content">
          <div v-if="ファイル読込中" class="placeholder-content">
            <span class="placeholder-icon">⏳</span>
            <div>読込中...</div>
          </div>
          <div v-else-if="ファイル内容エラー" class="placeholder-content">
            <span class="placeholder-icon">⚠️</span>
            <div>{{ ファイル内容エラー }}</div>
          </div>
          <img v-else-if="ファイル内容画像" :src="ファイル内容画像" class="file-image" />
          <div
            v-else-if="ファイル内容テキスト !== null && ファイル内容ハイライトHTML"
            class="file-text file-highlight"
            v-html="ファイル内容ハイライトHTML"
          ></div>
          <pre v-else-if="ファイル内容テキスト !== null" class="file-text">{{ ファイル内容テキスト }}</pre>
          <div v-else class="placeholder-content">
            <span class="placeholder-icon">📄</span>
            <div>上のツリーからファイルを選択すると<br>テキストまたは画像を表示します</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.file-container {
  background: #000000;
  border-radius: 2px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  width: 100%;
  height: 100%;
}

.file-header {
  background: #c8c8c8;
  color: #333;
  padding: 5px 10%;
  text-align: center;
  position: relative;
  flex-shrink: 0;
}

.file-header h1 {
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

.reload-btn {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  background: #22c55e;
  border: 1px solid #16a34a;
  border-radius: 2px;
  font-size: 18px;
  color: #ffffff;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  line-height: 22px;
  text-align: center;
  transition: all 0.15s ease;
}

.reload-btn:hover:not(:disabled) {
  background: #34d399;
  border-color: #22c55e;
  color: #ffffff;
  transform: translateY(-50%) scale(1.2);
}

.reload-btn:disabled {
  opacity: 0.4;
  background: #1f8a4b;
  border-color: #166a39;
  color: #ffffff;
  cursor: not-allowed;
}

/* ボディ全体: 上下分割 */
.file-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  gap: 1px;
  background: #333;
  padding: 1px;
  box-sizing: border-box;
}

/* 上段: 左右分割 */
.upper-area {
  flex: 1;
  display: flex;
  gap: 1px;
  overflow: hidden;
  min-height: 0;
}

/* 下段 */
.lower-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #0a0a0a;
  overflow: hidden;
  min-height: 0;
}

/* ツリーパネル共通 */
.tree-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #0a0a0a;
  overflow: hidden;
}

.panel-header {
  background: rgba(102, 126, 234, 0.08);
  color: #b8c5f2;
  font-size: 12px;
  font-weight: bold;
  padding: 4px 10px;
  flex-shrink: 0;
  border-bottom: 1px solid rgba(102, 126, 234, 0.3);
  display: flex;
  align-items: center;
  gap: 8px;
}

.panel-project {
  font-size: 10px;
  font-weight: normal;
  color: #b8c5f2;
  opacity: 0.8;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 40%;
}

.panel-count {
  font-size: 10px;
  font-weight: normal;
  color: #97a8df;
}

.panel-datetime {
  font-size: 10px;
  font-weight: normal;
  color: #97a8df;
}

.header-spacer {
  flex: 1;
}

.lower-area .panel-header {
  background: rgba(102, 126, 234, 0.08);
  color: #b8c5f2;
  border-bottom: 1px solid rgba(102, 126, 234, 0.3);
}

.download-btn {
  margin-left: 4px;
  background: #667eea;
  border: 1px solid #5568c8;
  border-radius: 2px;
  color: #ffffff;
  font-size: 14px;
  line-height: 14px;
  cursor: pointer;
  padding: 0;
  width: 18px;
  height: 18px;
  transition: transform 0.15s ease, background-color 0.15s ease, border-color 0.15s ease, opacity 0.15s ease;
}

.download-btn:hover:not(:disabled) {
  background: #768cf0;
  border-color: #667eea;
  color: #ffffff;
  transform: translateY(1px);
}

.download-btn:disabled {
  opacity: 0.35;
  background: #4b5da8;
  border-color: #3f4f8f;
  color: #ffffff;
  cursor: not-allowed;
}

.panel-content {
  flex: 1;
  overflow: auto;
  padding: 4px 8px;
  box-sizing: border-box;
}

.lower-area .panel-content {
  display: flex;
  align-items: center;
  justify-content: center;
}

.panel-content::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.panel-content::-webkit-scrollbar-track {
  background: #0a0a0a;
}

.panel-content::-webkit-scrollbar-thumb {
  background: rgba(102, 126, 234, 0.45);
  border-radius: 2px;
}

.placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #7480ac;
  font-size: 12px;
  text-align: center;
  gap: 8px;
}

.placeholder-icon {
  font-size: 32px;
  opacity: 0.4;
}

/* ファイルツリー */
.tree-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.tree-item {
  display: flex;
  align-items: center;
  font-family: 'Courier New', monospace;
  font-size: 11px;
  color: #b3bde2;
  padding: 1px 4px;
  white-space: nowrap;
  cursor: pointer;
  border-radius: 2px;
  user-select: none;
}

.tree-item:hover {
  background: rgba(102, 126, 234, 0.12);
  color: #d6def8;
}

.tree-item.folder {
  color: #ffffff;
}

.tree-item.folder .tree-name {
  color: #ffffff;
}

.tree-item:not(.folder) .tree-name {
  color: #00ff66;
}

.tree-item:hover:not(.folder) .tree-name {
  color: #66ff9b;
}

.tree-item:hover.folder .tree-name {
  color: #ffffff;
}

.tree-item.selected {
  background: rgba(102, 126, 234, 0.26);
  color: #edf2ff;
}

.tree-item.selected:not(.folder) .tree-name {
  color: #ffffff;
}

.tree-indent {
  flex: 0 0 auto;
}

.tree-toggle {
  width: 12px;
  text-align: center;
  flex: 0 0 auto;
  color: #9cadf0;
}

.tree-icon {
  width: 14px;
  text-align: center;
  flex: 0 0 auto;
  margin-right: 4px;
}

.tree-name {
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
  min-width: 0;
}

.tree-datetime {
  flex-shrink: 0;
  margin-left: 6px;
  font-size: 9px;
  color: #7a90b8;
  white-space: nowrap;
}

.tree-datetime-today {
  color: #ffffff;
}

.tree-datetime-recent {
  color: #ffffff;
}

.file-text {
  font-family: 'Courier New', monospace;
  font-size: 11px;
  color: #ffffff;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
  line-height: 1.5;
  width: 100%;
  align-self: flex-start;
}

.file-highlight {
  width: 100%;
  align-self: flex-start;
}

.file-highlight :deep(pre.shiki-pre) {
  margin: 0;
  padding: 0;
  background: #0a0a0a !important;
  white-space: pre-wrap;
  word-break: break-all;
  line-height: 1.5;
}

.file-highlight :deep(pre.shiki-pre code) {
  font-family: 'Courier New', monospace;
  font-size: 11px;
  white-space: pre-wrap;
  word-break: break-all;
  color: #ffffff;
}

.file-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  display: block;
  margin: auto;
}
</style>
