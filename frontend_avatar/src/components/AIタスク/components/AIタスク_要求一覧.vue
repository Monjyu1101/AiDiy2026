<!--
  -*- coding: utf-8 -*-

  -------------------------------------------------------------------------
  COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
  Licensed under "AiDiy 公開利用ライセンス v1.1".
  Commercial use requires prior written consent from all copyright holders.
  See LICENSE for full terms. Thank you for keeping the rules.
  https://github.com/monjyu1101/AiDiy2026
  -------------------------------------------------------------------------
-->

<script setup lang="ts">
// AIタスク_要求一覧: タスク要求表のタブラー表示 + 新規/タスクIDクリックで AIタスク_要求編集ダイアログ
// 5秒ごとに利用者ID単位の最大更新日時を確認し、変化時だけ一覧を再取得する
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import type { Column } from '@/types';
import { taskClient } from '@/api/client';
import qTublerFrame from '@/_share/qTublerFrame.vue';
import qBooleanCheckbox from '@/_share/qBooleanCheckbox.vue';
import { qConfirm, qMessage } from '@/utils/qAlert';
import AIタスク要求編集 from '../dialog/AIタスク_要求編集.vue';
import AIタスク応答内容 from '../dialog/AIタスク_応答内容.vue';

const props = defineProps({
  利用者ID: { type: String, default: '' },
  選択タスクID: { type: String, default: '' },
  showHeader: { type: Boolean, default: true }
});
const emit = defineEmits(['select']);

const rows = ref<Record<string, any>[]>([]);
const sortKey = ref('');
const sortOrder = ref('desc');
const currentPage = ref(1);
const pageSize = ref(100);
const rowKey = 'タスクID';

const columns: Column[] = [
  { key: '選択', label: '選', width: '46px', sortable: false, align: 'center' },
  { key: 'タスクID', label: 'タスクID', width: '150px', sortable: true, align: 'center' },
  { key: 'タイトル', label: 'タイトル', width: '170px', sortable: true },
  { key: '実行有効', label: '実行有効', width: '60px', sortable: true, align: 'center' },
  { key: '状態', label: '状態', width: '90px', sortable: true, align: 'center' },
  { key: 'PID', label: 'PID', width: '60px', sortable: false, align: 'center' },
  { key: '開始日時', label: '開始日時', width: '140px', sortable: true, align: 'center' },
  { key: '終了日時', label: '終了日時', width: '140px', sortable: true, align: 'center' },
  { key: '次回実行日時', label: '次回日時', width: '140px', sortable: true, align: 'center' },
  { key: '実行回数', label: '実行回数', width: '70px', sortable: false, align: 'right' },
  { key: '応答タイトル', label: '応答タイトル', width: '110px', sortable: false },
  { key: '応答内容', label: '応答内容', width: '240px', sortable: false }
];

const totalCount = computed(() => rows.value.length);
const totalPages = computed(() => Math.max(1, Math.ceil(totalCount.value / pageSize.value)));
const sortedRows = computed(() => {
  const list = [...rows.value];
  if (!sortKey.value) return list;
  list.sort((a, b) => {
    const result = String(a?.[sortKey.value] ?? '').localeCompare(String(b?.[sortKey.value] ?? ''), 'ja');
    return sortOrder.value === 'desc' ? -result : result;
  });
  return list;
});
const pagedRows = computed(() => {
  const startIndex = (currentPage.value - 1) * pageSize.value;
  return sortedRows.value.slice(startIndex, startIndex + pageSize.value);
});

const handleSort = (column: Column) => {
  if (column.sortable === false) return;
  if (sortKey.value === column.key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortKey.value = column.key;
    sortOrder.value = 'asc';
  }
};

const goToPage = (page: number) => {
  if (page < 1 || page > totalPages.value) return;
  currentPage.value = page;
};

// ==================================================
// 一覧データ取得
// ==================================================
let refreshTimer: ReturnType<typeof setInterval> | null = null;
let dialogChannel: BroadcastChannel | null = null;
let 初期選択済み = false;
let 要求最大更新日時 = '';

const 利用者ID取得 = () => props.利用者ID.trim();

const 最大更新日時計算 = (items: Record<string, any>[]) => {
  return items.reduce((max, row) => {
    const 更新日時 = String(row.更新日時 ?? '');
    return 更新日時 > max ? 更新日時 : max;
  }, '');
};

const loadData = async () => {
  try {
    const 利用者ID = 利用者ID取得();
    if (!利用者ID) return;
    const 前状態 = new Map(rows.value.map((row) => [row.タスクID, `${row.状態}|${row.更新日時}`]));
    const res = await taskClient.post('/task/タスク要求/一覧', {
      利用者ID
    });
    if (res.data.status === 'OK') {
      rows.value = res.data.data?.items ?? [];
      要求最大更新日時 = 最大更新日時計算(rows.value);
      if (!初期選択済み && !props.選択タスクID && rows.value.length > 0) {
        初期選択済み = true;
        emit('select', rows.value[0]);
      }
      // 選択中タスクの状態・更新日時が変わっていたら再選択でフロー図・明細を更新する
      if (props.選択タスクID) {
        const 選択行 = rows.value.find((row) => row.タスクID === props.選択タスクID);
        if (選択行 && 前状態.size > 0
            && 前状態.get(選択行.タスクID) !== `${選択行.状態}|${選択行.更新日時}`) {
          emit('select', 選択行);
        }
      }
    } else {
      void qMessage(res.data.message || 'タスク要求一覧の取得に失敗しました。', 'error');
    }
  } catch (e) {
    void qMessage('タスク要求一覧の取得でエラーが発生しました。backend_task (8093) の起動を確認してください。', 'error');
  }
};

const 更新確認 = async () => {
  try {
    const 利用者ID = 利用者ID取得();
    if (!利用者ID) return;
    const res = await taskClient.post('/task/タスク要求/最大更新日時', { 利用者ID });
    if (res.data.status !== 'OK') return;
    const 最大更新日時 = String(res.data.data?.最大更新日時 ?? '');
    if (最大更新日時 !== 要求最大更新日時) {
      await loadData();
    }
  } catch {
    // 自動更新確認の失敗は、通常操作を邪魔しない
  }
};

const 自動更新開始 = () => {
  if (refreshTimer) clearInterval(refreshTimer);
  refreshTimer = setInterval(() => void 更新確認(), 5000);
};

const selectRow = (row: Record<string, any>) => {
  emit('select', row);
};

// 実行有効欄クリック: 確認のうえタスク要求・タスク明細の実行有効フラグをまとめて切り替える
const 実行有効切替 = async (row: Record<string, any>) => {
  const 新実行有効 = !row.実行有効;
  const confirmed = await qConfirm(`タスクを${新実行有効 ? '有効化' : '無効化'}しますか？`);
  if (!confirmed) return;
  try {
    const res = await taskClient.post('/task/タスク要求/実行有効切替', {
      利用者ID: 利用者ID取得(),
      タスクID: String(row.タスクID ?? ''),
      実行有効: 新実行有効
    });
    if (res.data.status === 'OK') {
      void qMessage(res.data.message || (新実行有効 ? 'タスクを有効化しました。' : 'タスクを無効化しました。'));
      await loadData();
      if (row.タスクID === props.選択タスクID) {
        const 選択行 = rows.value.find((r) => r.タスクID === row.タスクID);
        if (選択行) emit('select', 選択行);
      }
    } else {
      void qMessage(res.data.message || '実行有効フラグの変更に失敗しました。', 'error');
    }
  } catch (e) {
    void qMessage('実行有効フラグの変更でエラーが発生しました。backend_task (8093) の起動を確認してください。', 'error');
  }
};

// ==================================================
// タスク追加/修正ダイアログ
// ==================================================
const dialogOpen = ref(false);
const 編集タスク = ref<Record<string, any> | null>(null);

const 新規ダイアログ表示 = () => {
  if (window.desktopApi?.openTaskDialogWindow) {
    void window.desktopApi.openTaskDialogWindow({
      kind: 'request',
      利用者ID: props.利用者ID,
      編集タスク: null
    });
    return;
  }
  編集タスク.value = null;
  dialogOpen.value = true;
};

const 修正ダイアログ表示 = (row: Record<string, any>) => {
  selectRow(row);
  if (window.desktopApi?.openTaskDialogWindow) {
    void window.desktopApi.openTaskDialogWindow({
      kind: 'request',
      利用者ID: props.利用者ID,
      編集タスク: { ...row }
    });
    return;
  }
  編集タスク.value = row;
  dialogOpen.value = true;
};

const 登録完了 = async (item: Record<string, any> | null) => {
  await loadData();
  if (item) selectRow(item);
};

// ==================================================
// 応答内容表示ダイアログ
// ==================================================
const 応答内容ダイアログ表示 = ref(false);
const 応答内容タイトル = ref('');
const 応答内容表示値 = ref('');

const 応答内容を開く = (row: Record<string, any>) => {
  const 内容 = String(row.応答内容 ?? '');
  if (!内容.trim()) return;
  const タイトル = `応答内容 - ${row.タスクID}${row.応答タイトル ? ' / ' + row.応答タイトル : ''}`;
  if (window.desktopApi?.openTaskDialogWindow) {
    void window.desktopApi.openTaskDialogWindow({
      kind: 'response',
      タイトル,
      内容
    });
    return;
  }
  応答内容タイトル.value = タイトル;
  応答内容表示値.value = 内容;
  応答内容ダイアログ表示.value = true;
};

const handleRowDblClick = (row: Record<string, any>) => {
  応答内容を開く(row);
};

onMounted(async () => {
  if (window.desktopApi?.openTaskDialogWindow) {
    dialogChannel = new BroadcastChannel('avatar-task-dialog');
    dialogChannel.addEventListener('message', (event: MessageEvent) => {
      const payload = event.data;
      if (!payload || typeof payload !== 'object' || payload.type !== 'task-dialog-registered') return;
      if (payload.kind !== 'request') return;
      void 登録完了((payload.item ?? null) as Record<string, any> | null);
    });
  }
  await loadData();
  自動更新開始();
});

onBeforeUnmount(() => {
  if (refreshTimer) clearInterval(refreshTimer);
  dialogChannel?.close();
  dialogChannel = null;
});

defineExpose({ loadData, 新規ダイアログ表示 });
</script>

<template>
  <div class="request-panel">
    <div v-if="props.showHeader" class="panel-header">
      <span class="panel-title">【タスク要求】</span>
      <button class="new-button" @click="新規ダイアログ表示">新規</button>
    </div>

    <div class="panel-body">
      <qTublerFrame
        :columns="columns"
        :rows="pagedRows"
        :rowKey="rowKey"
        :sortKey="sortKey"
        :sortOrder="sortOrder"
        :totalCount="totalCount"
        :totalAll="totalCount"
        :currentPage="currentPage"
        :totalPages="totalPages"
        @sort="handleSort"
        @page="goToPage"
        @row-click="selectRow"
        @row-dblclick="handleRowDblClick"
      >
        <template #cell="{ row, column, value }">
          <template v-if="column.key === '選択'">
            <button
              type="button"
              class="select-indicator"
              :class="{ active: row.タスクID === props.選択タスクID }"
              title="このタスク要求を選択"
              @click="selectRow(row)"
            >
              <span v-if="row.タスクID === props.選択タスクID">▶</span>
            </button>
          </template>
          <template v-else-if="column.key === 'タスクID'">
            <a
              href="#"
              class="id-link dialog-link"
              :class="{ 'selected-link': row.タスクID === props.選択タスクID }"
              @click.prevent="修正ダイアログ表示(row)"
            >{{ value ?? '' }}</a>
          </template>
          <template v-else-if="column.key === 'タイトル'">
            {{ value ?? '' }}
          </template>
          <template v-else-if="column.key === '実行有効'">
            <button
              type="button"
              class="valid-toggle"
              title="有効化/無効化を切り替え"
              @click="実行有効切替(row)"
            >
              <qBooleanCheckbox :checked="Boolean(row.実行有効)" ariaLabel="実行有効状態" />
            </button>
          </template>
          <template v-else-if="column.key === '応答内容'">
            <a
              v-if="String(value ?? '').trim()"
              href="#"
              class="id-link"
              @click.prevent="応答内容を開く(row)"
            >{{ value }}</a>
            <template v-else>{{ value ?? '' }}</template>
          </template>
          <template v-else>
            {{ value ?? '' }}
          </template>
        </template>
      </qTublerFrame>
    </div>

    <component
      :is="AIタスク要求編集"
      :is-open="dialogOpen"
      :利用者ID="props.利用者ID"
      :編集タスク="編集タスク"
      :最終タスク="rows[0] ?? null"
      @close="dialogOpen = false"
      @registered="登録完了"
    />

    <AIタスク応答内容
      :is-open="応答内容ダイアログ表示"
      :タイトル="応答内容タイトル"
      :内容="応答内容表示値"
      @close="応答内容ダイアログ表示 = false"
    />
  </div>
</template>

<style scoped>
.request-panel {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: transparent;
  color: #ddd;
}

/* 見出しはアバター画面の紫タイトルバー（_WindowShell purple）と同色 */
.panel-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 8px;
  height: 28px;
  box-sizing: border-box;
  background: linear-gradient(135deg, rgba(108, 78, 196, 0.94), rgba(143, 104, 221, 0.9));
  border-bottom: 1px solid rgba(93, 68, 168, 0.95);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.16),
    inset 0 -1px 0 rgba(44, 24, 101, 0.3);
  flex-shrink: 0;
}

.panel-title {
  font-size: 13px;
  color: #fff;
  font-weight: bold;
  letter-spacing: 1px;
}

.new-button {
  margin-left: auto;
  height: 22px;
  padding: 0 14px;
  border: none;
  border-radius: 0;
  background-color: #28a745;
  color: #fff;
  font-size: 12px;
  cursor: pointer;
}

.new-button:hover {
  background-color: #1e7e34;
}

.panel-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 8px;
}

/* 表の行がない領域はパネルの黒地を見せる */
.panel-body :deep(.common-table) {
  background-color: transparent;
}

/* データなし表示は表の中央に置く */
.panel-body :deep(.common-table table:has(td.empty)) {
  height: 100%;
}

/* 表は黒文字（行ゼブラは qTubler 標準のまま） */
.panel-body :deep(tbody td) {
  color: #000;
  padding: 2px 6px;
  font-size: 10px;
  line-height: 1.15;
}

.panel-body :deep(tbody tr:nth-child(odd)) {
  background-color: #fff;
}

.panel-body :deep(tbody tr:nth-child(even)) {
  background-color: #eef3f8;
}

.panel-body :deep(tbody tr:hover) {
  background-color: #dceeff;
}

.panel-body :deep(tbody tr:has(.selected-link) td) {
  background-color: #c7d2fe;
  color: #111827;
  font-weight: 600;
  box-shadow: inset 0 1px 0 rgba(79, 70, 229, 0.45), inset 0 -1px 0 rgba(79, 70, 229, 0.45);
}

.panel-body :deep(tbody tr:has(.selected-link) td:first-child) {
  box-shadow:
    inset 4px 0 0 #6c4ec4,
    inset 0 1px 0 rgba(79, 70, 229, 0.45),
    inset 0 -1px 0 rgba(79, 70, 229, 0.45);
}

.panel-body :deep(tbody td a),
.panel-body :deep(tbody td button) {
  font-size: inherit;
}

.panel-body :deep(.table-footer) {
  min-height: 28px;
  padding: 2px 6px;
  gap: 8px;
  flex-wrap: nowrap;
  box-sizing: border-box;
  font-size: 11px;
}

.panel-body :deep(.table-count) {
  min-width: 120px;
}

.panel-body :deep(.pager) {
  gap: 3px;
  flex-wrap: nowrap;
}

.panel-body :deep(.pager-btn) {
  min-width: 26px;
  height: 20px;
  padding: 0 6px;
  font-size: 11px;
  line-height: 18px;
}

.panel-body :deep(.pager-current) {
  min-width: 24px;
  font-size: 11px;
}

.valid-toggle {
  background: none;
  border: none;
  border-bottom: 1px solid #000;
  padding: 0;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
}

.valid-toggle :deep(.readonly-checkbox) {
  width: 12px;
  height: 12px;
}

.valid-toggle :deep(.readonly-checkbox-mark) {
  font-size: 9px;
}

.id-link {
  color: #000;
  font-weight: normal;
  text-decoration: none;
}

.dialog-link {
  text-decoration: underline;
  text-underline-offset: 2px;
}

.selected-link {
  color: #111827;
  font-weight: 700;
}

.select-indicator {
  width: 100%;
  height: 16px;
  padding: 0;
  border: none;
  border-bottom: 1px solid transparent;
  background: transparent;
  color: #6c4ec4;
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
  cursor: pointer;
}

.select-indicator.active {
  border-bottom-color: #6c4ec4;
}

.id-link:hover {
  text-decoration: underline;
}
</style>
