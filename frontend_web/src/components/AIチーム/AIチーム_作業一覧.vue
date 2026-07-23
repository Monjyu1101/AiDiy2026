<script setup lang="ts">
// 5秒ごとに利用者ID単位の最大更新日時を確認し、変化時だけ一覧を再取得する
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import apiClient from '../../api/client';
import { useAuthStore } from '../../stores/auth';
import TeamWorkEdit from './dialog/Aチーム作業編集.vue';
import type { チーム作業 } from './AIチーム_型';
import { use自由配置パネル } from './use自由配置パネル';

const authStore = useAuthStore();
const 利用者ID = computed(() => String(authStore.user?.利用者ID ?? 'admin'));
const 作業一覧 = ref<チーム作業[]>([]);
const 読込中 = ref(false);
const 読込エラー = ref('');
const 編集ダイアログ表示 = ref(false);
const 編集作業 = ref<チーム作業 | null>(null);
let refreshTimer: ReturnType<typeof setInterval> | null = null;
let 作業最大更新日時 = '';

const {
  panelRef,
  位置,
  zIndex,
  ドラッグ開始,
  ドラッグ中,
  ドラッグ終了,
} = use自由配置パネル('AIチーム_作業一覧位置', 'right');

const 最大更新日時取得 = async (): Promise<string> => {
  const response = await apiClient.post('/team/作業/最大更新日時', {
    利用者ID: 利用者ID.value,
  });
  if (response.data?.status !== 'OK') return 作業最大更新日時;
  return String(response.data?.data?.最大更新日時 ?? '');
};

const 作業一覧読込 = async () => {
  if (読込中.value) return;
  読込中.value = true;
  読込エラー.value = '';
  try {
    // 一覧取得中に更新が入った場合は、次回確認で拾えるよう基準を先に取得する。
    const newBaseline = await 最大更新日時取得();
    const response = await apiClient.post('/team/作業/一覧', { 利用者ID: 利用者ID.value });
    if (response.data?.status !== 'OK') {
      throw new Error(response.data?.message || 'チーム作業を取得できませんでした');
    }
    const items = response.data?.data?.items;
    if (!Array.isArray(items)) throw new Error('チーム作業の応答形式が正しくありません');
    作業一覧.value = items as チーム作業[];
    作業最大更新日時 = newBaseline;
  } catch (error) {
    読込エラー.value = error instanceof Error ? error.message : 'チーム作業を取得できませんでした';
  } finally {
    読込中.value = false;
  }
};

const 更新確認 = async () => {
  try {
    if (読込中.value) return;
    const maxUpdatedAt = await 最大更新日時取得();
    if (maxUpdatedAt !== 作業最大更新日時) await 作業一覧読込();
  } catch {
    // 自動更新確認の失敗は、通常操作を邪魔しない。
  }
};

const 自動更新開始 = () => {
  if (refreshTimer) clearInterval(refreshTimer);
  refreshTimer = setInterval(() => void 更新確認(), 5000);
};

const 新規作業を開く = () => {
  編集作業.value = null;
  編集ダイアログ表示.value = true;
};

const 作業を開く = (work: チーム作業) => {
  編集作業.value = work;
  編集ダイアログ表示.value = true;
};

const 保存後処理 = (work: チーム作業) => {
  const index = 作業一覧.value.findIndex((item) => item.作業ID === work.作業ID);
  if (index >= 0) 作業一覧.value.splice(index, 1, work);
  else 作業一覧.value.unshift(work);
};

const 状態class = (status: チーム作業['状態']) => ({
  waiting: ['準備開始', '準備中', '準備完了', '待機'].includes(status),
  working: status === '実行中',
  completed: status === '完了',
  stopped: status === 'エラー' || status === '中止',
});

onMounted(async () => {
  await 作業一覧読込();
  自動更新開始();
});

onBeforeUnmount(() => {
  if (refreshTimer) clearInterval(refreshTimer);
});
</script>

<template>
  <aside
    ref="panelRef"
    class="task-panel"
    :style="{ transform: `translate3d(${位置.x}px, ${位置.y}px, 0)`, zIndex }"
  >
    <div
      class="panel-heading drag-handle"
      title="ドラッグして移動"
      @pointerdown="ドラッグ開始"
      @pointermove="ドラッグ中"
      @pointerup="ドラッグ終了"
      @pointercancel="ドラッグ終了"
    >
      <div>
        <span class="panel-kicker">TEAM WORK</span>
        <h2>チーム作業</h2>
      </div>
      <div class="heading-actions">
        <span class="task-count">{{ 作業一覧.length }}件</span>
        <button type="button" @pointerdown.stop @click="新規作業を開く">＋ 追加</button>
      </div>
    </div>

    <div class="table-frame">
      <table>
        <thead>
          <tr>
            <th>作業ID</th>
            <th>タイトル</th>
            <th>状態</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="work in 作業一覧" :key="work.作業ID" @click="作業を開く(work)">
            <td class="work-id">{{ work.作業ID }}</td>
            <td>
              <strong>{{ work.タイトル || '（タイトルなし）' }}</strong>
              <small>{{ work.TEAM_AI_NAME }} / {{ work.TEAM_AI_MODEL }}</small>
            </td>
            <td>
              <span class="status-badge" :class="状態class(work.状態)">{{ work.状態 }}</span>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="読込中" class="panel-message">チーム作業を読み込んでいます…</div>
      <div v-else-if="読込エラー" class="panel-message error">
        <span>{{ 読込エラー }}</span>
        <button type="button" @click="作業一覧読込">再読込</button>
      </div>
      <div v-else-if="作業一覧.length === 0" class="panel-message">
        登録済みのチーム作業はありません。
      </div>
    </div>
  </aside>

  <component
    :is="TeamWorkEdit"
    :isOpen="編集ダイアログ表示"
    :編集作業="編集作業"
    :最終作業="作業一覧[0] ?? null"
    @close="編集ダイアログ表示 = false"
    @saved="保存後処理"
  />
</template>

<style scoped>
.task-panel {
  width: 430px;
  max-width: calc(100% - 24px);
  max-height: calc(100% - 36px);
  position: absolute;
  top: 0;
  left: 0;
  padding: 18px 14px;
  overflow-y: auto;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: rgba(11, 24, 37, 0.94);
  box-shadow: 0 18px 45px rgba(2, 8, 14, 0.42);
  z-index: 7;
  will-change: transform;
}

.panel-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin: 0 2px 14px;
}

.panel-heading h2 {
  margin: 2px 0 0;
  font-size: 16px;
}

.drag-handle {
  cursor: move;
  touch-action: none;
  user-select: none;
}

.panel-kicker {
  color: #5ddaf7;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.16em;
}

.heading-actions {
  display: grid;
  justify-items: end;
  gap: 5px;
}

.task-count {
  color: #7e98aa;
  font-size: 10px;
  font-weight: 700;
}

.heading-actions button,
.panel-message button {
  padding: 5px 8px;
  border: 1px solid rgba(135, 114, 255, 0.48);
  border-radius: 7px;
  color: #d8ceff;
  background: rgba(101, 76, 190, 0.18);
  cursor: pointer;
  font-size: 9px;
}

.table-frame {
  overflow: hidden;
  border: 1px solid rgba(139, 206, 231, 0.12);
  border-radius: 10px;
}

table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

th {
  padding: 7px 8px;
  color: #718b9b;
  background: rgba(18, 38, 54, 0.9);
  text-align: left;
  font-size: 9px;
}

th:first-child {
  width: 112px;
}

th:last-child {
  width: 56px;
  text-align: center;
}

td {
  padding: 8px;
  border-top: 1px solid rgba(139, 206, 231, 0.08);
  color: #d8e8ef;
  vertical-align: middle;
  font-size: 10px;
}

tbody tr {
  cursor: pointer;
  transition: background 0.15s ease;
}

tbody tr:hover {
  background: rgba(75, 125, 151, 0.12);
}

.work-id {
  color: #7bbbd0;
  font-family: Consolas, monospace;
  font-size: 8px;
}

td strong,
td small {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

td small {
  margin-top: 3px;
  color: #60798a;
  font-size: 8px;
}

.status-badge {
  display: inline-block;
  width: 48px;
  padding: 3px 0;
  border: 1px solid #60798a;
  border-radius: 999px;
  text-align: center;
  font-size: 8px;
}

.status-badge.waiting {
  color: #ffd580;
  border-color: rgba(255, 213, 128, 0.4);
}

.status-badge.working {
  color: #65e8b7;
  border-color: rgba(101, 232, 183, 0.4);
}

.status-badge.completed {
  color: #7bbdff;
  border-color: rgba(123, 189, 255, 0.4);
}

.status-badge.stopped {
  color: #ff9bab;
  border-color: rgba(255, 155, 171, 0.4);
}

.panel-message {
  min-height: 96px;
  display: grid;
  place-items: center;
  gap: 8px;
  padding: 16px;
  color: #718b9b;
  text-align: center;
  font-size: 10px;
}

.panel-message.error {
  color: #ff9bab;
}

@media (max-width: 760px) {
  .task-panel {
    width: min(430px, calc(100% - 24px));
    max-height: calc(100% - 24px);
  }
}
</style>
