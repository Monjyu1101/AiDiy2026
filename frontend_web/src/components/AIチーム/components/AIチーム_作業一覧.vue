<script setup lang="ts">
// AIチーム_改善一覧: 掲示板に出ているプロジェクトの目標ループ（PDCA）の実行状況を一覧表示する
// 5秒ごとにプロジェクト単位の最大更新日時を確認し、変化時だけ一覧を再取得する
// 表示するのは目標ループがオンのときだけ（オフのときは AIチーム.vue 側で描画しない）
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import apiClient from '../../../api/client';
import AIチーム_応答内容 from '../dialog/AIチーム_応答内容.vue';
import type { チーム改善 } from '../AIチーム_型';
import { use自由配置パネル } from '../use自由配置パネル';

const props = defineProps<{
  /** 掲示板に表示中のプロジェクト（CODE_BASE_PATH）。この分だけを一覧する */
  プロジェクト: string;
}>();

const 改善一覧 = ref<チーム改善[]>([]);
const 読込中 = ref(false);
const 読込エラー = ref('');
let refreshTimer: ReturnType<typeof setInterval> | null = null;
let 改善最大更新日時 = '';
let 改善取得中 = false;

const 対象プロジェクト = computed(() => String(props.プロジェクト ?? '').trim());
const 実行中件数 = computed(() => 改善一覧.value.filter((改善) => !改善.終了日時).length);

const {
  panelRef,
  位置,
  zIndex,
  開いている,
  開閉を切替,
  ドラッグ開始,
  ドラッグ中,
  ドラッグ終了,
} = use自由配置パネル('AIチーム_改善一覧位置', 'center', 'bottom');

const 最大更新日時取得 = async (): Promise<string> => {
  const response = await apiClient.post('/team/改善/最大更新日時', {
    プロジェクト: 対象プロジェクト.value,
  });
  if (response.data?.status !== 'OK') return 改善最大更新日時;
  return String(response.data?.data?.最大更新日時 ?? '');
};

const 改善一覧読込 = async (読込表示 = true) => {
  if (改善取得中) return;
  改善取得中 = true;
  if (読込表示) {
    読込中.value = true;
    読込エラー.value = '';
  }
  try {
    // 一覧取得中に更新が入った場合は、次回確認で拾えるよう基準を先に取得する。
    const newBaseline = await 最大更新日時取得();
    const response = await apiClient.post('/team/改善/一覧', {
      プロジェクト: 対象プロジェクト.value,
    });
    if (response.data?.status !== 'OK') {
      throw new Error(response.data?.message || 'チーム改善を取得できませんでした');
    }
    const items = response.data?.data?.items;
    if (!Array.isArray(items)) throw new Error('チーム改善の応答形式が正しくありません');
    改善一覧.value = items as チーム改善[];
    改善最大更新日時 = newBaseline;
    読込エラー.value = '';
  } catch (error) {
    if (読込表示) {
      読込エラー.value = error instanceof Error ? error.message : 'チーム改善を取得できませんでした';
    }
  } finally {
    if (読込表示) 読込中.value = false;
    改善取得中 = false;
  }
};

const 更新確認 = async () => {
  try {
    if (改善取得中) return;
    const maxUpdatedAt = await 最大更新日時取得();
    if (maxUpdatedAt !== 改善最大更新日時) await 改善一覧読込(false);
  } catch {
    // 自動更新確認の失敗は、通常操作を邪魔しない。
  }
};

const 自動更新開始 = () => {
  if (refreshTimer) clearInterval(refreshTimer);
  refreshTimer = setInterval(() => void 更新確認(), 5000);
};

// 掲示板のプロジェクトが変わったら、その分の改善へ切り替える
watch(対象プロジェクト, () => {
  改善最大更新日時 = '';
  void 改善一覧読込();
});

const 内容ダイアログ表示 = ref(false);
const 内容タイトル = ref('');
const 内容要求値 = ref('');
const 内容応答値 = ref('');
const 内容まとめ値 = ref('');

// ダブルクリックで チーム目標 / 応答内容 を共通ダイアログに表示する
const 内容を開く = (改善: チーム改善) => {
  const 目標 = String(改善.チーム目標 ?? '');
  const 応答 = String(改善.応答内容 ?? '');
  const まとめ = String(改善.まとめ内容 ?? '');
  if (!目標.trim() && !応答.trim() && !まとめ.trim()) return;
  内容タイトル.value = `${区分表示(改善.PDCA区分)} - ${改善.要員ID || 改善.改善ID}`;
  内容要求値.value = 目標;
  内容応答値.value = 応答;
  内容まとめ値.value = まとめ;
  内容ダイアログ表示.value = true;
};

const 区分名 = {
  S: '相談',
  P: '計画',
  D: '実行',
  C: '評価',
  A: '改善',
} as Record<string, string>;
const 区分表示 = (区分: string) => `${区分}（${区分名[区分] ?? '不明'}）`;

const 状況class = (改善: チーム改善) => ({
  waiting: ['準備中', '準備完了', '待機'].includes(改善.状況),
  running: 改善.状況 === '実行中',
  completed: ['完了', '済'].includes(改善.状況),
  stopped: ['エラー', '中止'].includes(改善.状況),
});

const 行状態クラス = (改善: チーム改善) => (['完了', '済'].includes(改善.状況) ? '' : 'row-inactive');

const 日時表示 = (値: string) => String(値 ?? '').replace(/^\d{4}-/, '').slice(0, 14);

onMounted(async () => {
  await 改善一覧読込();
  自動更新開始();
});

onBeforeUnmount(() => {
  if (refreshTimer) clearInterval(refreshTimer);
});
</script>

<template>
  <aside
    ref="panelRef"
    class="pdca-panel"
    :class="{ collapsed: !開いている }"
    :style="{ transform: `translate3d(${位置.x}px, ${位置.y}px, 0)`, zIndex }"
  >
    <div
      class="panel-header drag-handle"
      title="ドラッグして移動"
      @pointerdown="ドラッグ開始"
      @pointermove="ドラッグ中"
      @pointerup="ドラッグ終了"
      @pointercancel="ドラッグ終了"
    >
      <button
        type="button"
        class="collapse-toggle"
        :title="開いている ? '閉じる' : '開く'"
        :aria-expanded="開いている"
        @pointerdown.stop
        @click="開閉を切替"
      >{{ 開いている ? '▼' : '▶' }}</button>
      <span class="panel-title">【目標ループ】</span>
      <span class="panel-count">{{ 改善一覧.length }}件</span>
      <span class="panel-total">実行中 {{ 実行中件数 }}</span>
    </div>

    <div v-if="開いている" class="panel-project" :title="対象プロジェクト">
      {{ 対象プロジェクト || '（掲示板のプロジェクト未設定）' }}
    </div>

    <div v-if="開いている" class="table-frame">
      <table>
        <thead>
          <tr>
            <th>ループ</th>
            <th>何を（PDCA）</th>
            <th>誰が</th>
            <th>開始日時</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="改善 in 改善一覧"
            :key="改善.改善ID"
            :class="行状態クラス(改善)"
            @dblclick="内容を開く(改善)"
          >
            <td class="loop-number">{{ 改善.ループ || '－' }}</td>
            <td>
              <strong>{{ 区分表示(改善.PDCA区分) }}</strong>
              <small>
                <span class="status-badge" :class="状況class(改善)">{{ 改善.状況 || '－' }}</span>
                {{ 改善.終了日時 ? `終了 ${日時表示(改善.終了日時)}` : '実行中' }}
              </small>
            </td>
            <td class="member-id">{{ 改善.要員ID }}</td>
            <td class="done-at">{{ 日時表示(改善.開始日時) }}</td>
          </tr>
        </tbody>
      </table>

      <div v-if="読込中" class="panel-message">チーム改善を読み込んでいます…</div>
      <div v-else-if="読込エラー" class="panel-message error">
        <span>{{ 読込エラー }}</span>
        <button type="button" @click="() => 改善一覧読込()">再読込</button>
      </div>
      <div v-else-if="改善一覧.length === 0" class="panel-message">
        まだ目標ループの記録はありません。空き時間に相談（S）から始まります。
      </div>
      <div v-else class="panel-hint">行をダブルクリックでチーム目標・応答内容を表示</div>
    </div>
  </aside>

  <AIチーム_応答内容
    :is-open="内容ダイアログ表示"
    :タイトル="内容タイトル"
    :要求内容="内容要求値"
    :内容="内容応答値"
    :まとめ内容="内容まとめ値"
    @close="内容ダイアログ表示 = false"
  />
</template>

<style scoped>
.pdca-panel {
  width: 470px;
  max-width: calc(100% - 24px);
  /* 画面縦幅の 50% までに収め、あふれる分は本体側で縦スクロールさせる。
     縦の狭い画面では画面割合が置き場所（.workspace）を超えてしまうので、そちらも上限にする */
  max-height: min(50vh, calc(100% - 36px));
  position: absolute;
  top: 0;
  left: 0;
  padding: 18px 14px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid rgba(93, 68, 168, 0.95);
  background: rgba(11, 24, 37, 0.94);
  box-shadow: 0 18px 45px rgba(2, 8, 14, 0.42);
  z-index: 7;
  will-change: transform;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, opacity 0.18s ease;
}

.pdca-panel:hover {
  border-color: rgba(154, 120, 235, 0.95);
  box-shadow:
    0 18px 45px rgba(2, 8, 14, 0.42),
    0 0 0 1px rgba(154, 120, 235, 0.4),
    0 0 16px rgba(154, 120, 235, 0.4);
}

.panel-header {
  flex: none;
  display: flex;
  align-items: center;
  gap: 8px;
  margin: -18px -14px 8px;
  padding: 0 10px;
  height: 28px;
  box-sizing: border-box;
  background: linear-gradient(135deg, rgba(108, 78, 196, 0.78), rgba(143, 104, 221, 0.72));
  border-bottom: 1px solid rgba(93, 68, 168, 0.95);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.16),
    inset 0 -1px 0 rgba(44, 24, 101, 0.3);
}

.collapse-toggle {
  flex: none;
  width: 18px;
  height: 18px;
  margin-left: -2px;
  padding: 0;
  border: none;
  border-radius: 2px;
  background: transparent;
  color: rgba(255, 255, 255, 0.82);
  font-size: 10px;
  line-height: 1;
  cursor: pointer;
}

.collapse-toggle:hover {
  background: rgba(255, 255, 255, 0.16);
}

/* 閉じたときはタイトルバーだけを残す（本体側の余白を消す）。
   草原を広く見せたいので、折り畳み中は薄くして背景を透かす（触れると戻る） */
.pdca-panel.collapsed {
  padding-bottom: 0;
  opacity: 0.34;
}

.pdca-panel.collapsed:hover,
.pdca-panel.collapsed:focus-within {
  opacity: 1;
}

.pdca-panel.collapsed .panel-header {
  margin-bottom: 0;
}

.panel-title {
  color: rgba(255, 255, 255, 0.82);
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 1px;
  white-space: nowrap;
}

.panel-count {
  color: #e4ddff;
  font-size: 10px;
  font-weight: 700;
}

.panel-total {
  margin-left: auto;
  color: #9dffce;
  font-size: 10px;
  font-weight: 700;
}

.drag-handle {
  cursor: move;
  touch-action: none;
  user-select: none;
}

.panel-project {
  flex: none;
  margin-bottom: 8px;
  overflow: hidden;
  color: #7bbbd0;
  font-family: Consolas, monospace;
  font-size: 9px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.table-frame {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  border: 1px solid rgba(139, 206, 231, 0.12);
}

table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

th {
  padding: 4px 8px;
  color: #718b9b;
  background: rgba(18, 38, 54, 0.9);
  text-align: left;
  font-size: 9px;
}

th:first-child {
  width: 38px;
  text-align: center;
}

th:nth-child(3) {
  width: 78px;
}

th:last-child {
  width: 92px;
}

td {
  padding: 3px 8px;
  border-top: 1px solid rgba(139, 206, 231, 0.08);
  color: #d8e8ef;
  vertical-align: middle;
  font-size: 10px;
  line-height: 1.25;
}

tbody tr {
  cursor: pointer;
  transition: background 0.15s ease;
}

tbody tr:hover {
  background: rgba(75, 125, 151, 0.12);
}

/* 行カラーリング: 完了以外（準備中・実行中・エラー）は灰色 */
tbody tr.row-inactive {
  background: rgba(255, 255, 255, 0.03);
}

tbody tr.row-inactive td {
  color: #5f7686;
}

tbody tr.row-inactive td small {
  color: #4a5b68;
}

td strong {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

td small {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-top: 0;
  overflow: hidden;
  color: #60798a;
  font-size: 8px;
  white-space: nowrap;
}

.member-id {
  color: #9ceaff;
  font-family: Consolas, monospace;
  font-size: 9px;
}

.loop-number {
  color: #c9a8ff;
  font-family: Consolas, monospace;
  font-weight: 700;
  text-align: center;
}

.done-at {
  color: #8fa6b4;
  font-family: Consolas, monospace;
  font-size: 9px;
}

.status-badge {
  display: inline-block;
  width: 48px;
  padding: 0;
  border: 1px solid #60798a;
  border-radius: 999px;
  text-align: center;
  font-size: 8px;
}

.status-badge.waiting {
  color: #ffd580;
  border-color: rgba(255, 213, 128, 0.4);
}

.status-badge.running {
  color: #9dffce;
  border-color: rgba(157, 255, 206, 0.4);
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

.panel-message button {
  padding: 5px 8px;
  border: 1px solid rgba(135, 114, 255, 0.48);
  border-radius: 7px;
  color: #d8ceff;
  background: rgba(101, 76, 190, 0.18);
  cursor: pointer;
  font-size: 9px;
}

.panel-hint {
  padding: 5px 8px;
  border-top: 1px solid rgba(139, 206, 231, 0.08);
  color: #5f7686;
  text-align: right;
  font-size: 8px;
}

@media (max-width: 760px) {
  .pdca-panel {
    width: min(430px, calc(100% - 24px));
  }
}
</style>
