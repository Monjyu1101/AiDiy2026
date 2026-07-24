<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import apiClient from '../../../api/client';
import AiTeamMemberSummon from '../dialog/AIチーム_メンバー召喚.vue';
import type { エージェント, チーム状況, チーム要員, 状態表示 } from '../AIチーム_型';
import { use自由配置パネル } from '../use自由配置パネル';

const props = defineProps<{
  エージェント一覧: エージェント[];
  選択中ID: string;
  選択中エージェント: エージェント | null;
  排除中ID: string;
  状態情報: 状態表示;
  召喚可能要員一覧: チーム要員[];
  召喚対象ID: string;
  召喚中: boolean;
  要員読込中: boolean;
  要員読込エラー: string;
  召喚実行: () => Promise<boolean>;
  要員再読込: () => Promise<void>;
}>();

const emit = defineEmits<{
  select: [id: string];
  expel: [];
  'update:summonTarget': [id: string];
}>();

const 召喚ダイアログ表示 = ref(false);
const {
  panelRef,
  位置,
  zIndex,
  ドラッグ開始,
  ドラッグ中,
  ドラッグ終了,
} = use自由配置パネル('AIチーム_メンバー位置', 'left');

const 召喚ダイアログを開く = () => {
  召喚ダイアログ表示.value = true;
};

const 状況一覧 = ref<チーム状況[]>([]);
let 状況更新Timer: ReturnType<typeof setInterval> | null = null;

const 選択中状況 = computed(
  () => 状況一覧.value.find((item) => item.要員ID === props.選択中エージェント?.id) ?? null,
);

const 状況を読み込む = async () => {
  try {
    const response = await apiClient.post('/team/状況/一覧', {});
    if (response.data?.status !== 'OK') return;
    const items = response.data?.data?.items;
    if (Array.isArray(items)) 状況一覧.value = items as チーム状況[];
  } catch {
    // 自動更新確認の失敗は、通常操作を邪魔しない。
  }
};

onMounted(async () => {
  await 状況を読み込む();
  状況更新Timer = setInterval(() => void 状況を読み込む(), 10000);
});

onBeforeUnmount(() => {
  if (状況更新Timer) clearInterval(状況更新Timer);
});
</script>

<template>
  <aside
    ref="panelRef"
    class="agent-panel"
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
        <span class="panel-kicker">TEAM MEMBERS</span>
        <h2>メンバー</h2>
      </div>
      <div class="heading-actions">
        <span class="member-count">{{ エージェント一覧.length }}名</span>
        <button type="button" @click="召喚ダイアログを開く">＋ 召喚</button>
      </div>
    </div>

    <div class="agent-list">
      <button
        v-for="agent in エージェント一覧"
        :key="agent.id"
        type="button"
        class="agent-card"
        :class="{ selected: agent.id === 選択中ID }"
        @click="emit('select', agent.id)"
      >
        <span class="agent-avatar" :style="{ '--agent-color': agent.色CSS }">
          {{ agent.名前.slice(0, 1) }}
        </span>
        <span class="agent-copy">
          <span class="agent-name-row">
            <strong>{{ agent.名前 }}</strong>
            <span class="state-dot" :style="{ color: 状態情報[agent.状態].色 }">
              {{ 状態情報[agent.状態].記号 }}
            </span>
          </span>
          <span class="agent-role">{{ agent.役割 }} · {{ agent.状態 }}</span>
        </span>
      </button>
    </div>

    <div v-if="選択中エージェント" class="agent-detail">
      <div class="detail-top">
        <span class="detail-pulse" :style="{ background: 選択中エージェント.色CSS }"></span>
        <span>{{ 選択中エージェント.状態 }}</span>
      </div>
      <strong>{{ 選択中エージェント.作業内容 }}</strong>
      <p v-if="選択中エージェント.ひとこと">「{{ 選択中エージェント.ひとこと }}」</p>
      <div v-if="選択中状況" class="status-summary">
        <div class="status-row">
          <span class="status-chip status-waiting">待機 {{ 選択中状況.待機数 }}</span>
          <span class="status-chip status-running">実行 {{ 選択中状況.実行数 }}</span>
          <span class="status-chip status-done">完了 {{ 選択中状況.完了数 }}</span>
          <span class="status-chip status-error">エラー {{ 選択中状況.エラー数 }}</span>
        </div>
        <small>最終更新: {{ 選択中状況.最終更新日時 || '-' }}</small>
      </div>
      <small v-else class="status-empty">直近24時間のAIタスク実績はありません</small>
      <div class="member-action">
        <span v-if="選択中エージェント.id === 'admin'">初期メンバー・退場不可</span>
        <button
          v-else
          type="button"
          :disabled="排除中ID === 選択中エージェント.id"
          @click="emit('expel')"
        >
          {{ 排除中ID === 選択中エージェント.id ? '退場中' : '要員を退場' }}
        </button>
      </div>
    </div>
  </aside>

  <component
    :is="AiTeamMemberSummon"
    :isOpen="召喚ダイアログ表示"
    :召喚可能要員一覧="召喚可能要員一覧"
    :召喚対象ID="召喚対象ID"
    :召喚中="召喚中"
    :要員読込中="要員読込中"
    :要員読込エラー="要員読込エラー"
    :召喚実行="召喚実行"
    :要員再読込="要員再読込"
    @close="召喚ダイアログ表示 = false"
    @update:summon-target="emit('update:summonTarget', $event)"
  />
</template>

<style scoped>
.agent-panel {
  width: 240px;
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
  z-index: 8;
  will-change: transform;
}

.panel-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin: -18px -14px 14px;
  padding: 8px 14px;
  background: linear-gradient(135deg, rgba(108, 78, 196, 0.22), rgba(143, 104, 221, 0.16));
  border-bottom: 1px solid rgba(143, 104, 221, 0.25);
  border-radius: 14px 14px 0 0;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.08),
    inset 0 -1px 0 rgba(44, 24, 101, 0.15);
}

.panel-heading h2 {
  margin: 2px 0 0;
  color: #fff;
  font-size: 16px;
}

.drag-handle {
  cursor: move;
  touch-action: none;
  user-select: none;
}

.heading-actions {
  display: grid;
  justify-items: end;
  gap: 5px;
}

.heading-actions button {
  padding: 5px 8px;
  border: 1px solid rgba(135, 114, 255, 0.48);
  border-radius: 7px;
  color: #d8ceff;
  background: rgba(101, 76, 190, 0.18);
  cursor: pointer;
  font-size: 9px;
}

.panel-kicker {
  color: #5ddaf7;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.16em;
}

.member-count {
  margin-top: 3px;
  color: #7e98aa;
  font-size: 10px;
  font-weight: 700;
}

.agent-list {
  display: grid;
  gap: 5px;
}

.agent-card {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border: 1px solid transparent;
  border-radius: 10px;
  color: #dceaf1;
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.agent-card:hover {
  background: rgba(75, 125, 151, 0.1);
}

.agent-card.selected {
  border-color: rgba(83, 200, 235, 0.3);
  background: linear-gradient(90deg, rgba(48, 146, 184, 0.2), rgba(50, 78, 111, 0.08));
}

.agent-avatar {
  width: 34px;
  height: 34px;
  flex: 0 0 34px;
  display: grid;
  place-items: center;
  border: 1px solid color-mix(in srgb, var(--agent-color) 65%, transparent);
  border-radius: 10px;
  color: var(--agent-color);
  background: color-mix(in srgb, var(--agent-color) 13%, #10202c);
  font-size: 13px;
  font-weight: 800;
}

.agent-copy {
  min-width: 0;
  flex: 1;
}

.agent-name-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.agent-name-row strong {
  font-size: 12px;
}

.agent-role {
  display: block;
  margin-top: 2px;
  overflow: hidden;
  color: #718a9d;
  font-size: 9px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.state-dot {
  font-size: 9px;
}

.agent-detail {
  margin-top: 16px;
  padding: 13px;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: rgba(12, 27, 41, 0.75);
}

.detail-top {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 7px;
  color: #8ba3b2;
  font-size: 9px;
}

.detail-pulse {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.agent-detail strong {
  display: block;
  color: #dcebf2;
  font-size: 11px;
  line-height: 1.5;
}

.agent-detail p {
  margin: 6px 0 0;
  color: #88a9ba;
  font-size: 10px;
  line-height: 1.5;
}

.status-summary {
  margin: 12px 0 6px;
}

.status-row {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-bottom: 6px;
}

.status-chip {
  padding: 3px 7px;
  border: 1px solid rgba(120, 151, 169, 0.3);
  border-radius: 999px;
  color: #b7c9d3;
  background: rgba(120, 151, 169, 0.12);
  font-size: 9px;
  font-weight: 700;
}

.status-chip.status-waiting {
  border-color: rgba(139, 184, 255, 0.4);
  color: #8bb8ff;
  background: rgba(139, 184, 255, 0.12);
}

.status-chip.status-running {
  border-color: rgba(101, 232, 183, 0.4);
  color: #65e8b7;
  background: rgba(101, 232, 183, 0.12);
}

.status-chip.status-done {
  border-color: rgba(120, 151, 169, 0.4);
  color: #9fb4c0;
  background: rgba(120, 151, 169, 0.12);
}

.status-chip.status-error {
  border-color: rgba(255, 107, 129, 0.4);
  color: #ff8fa3;
  background: rgba(255, 107, 129, 0.12);
}

.status-empty {
  display: block;
  margin: 12px 0 6px;
  color: #5f7686;
  font-size: 9px;
}

.agent-detail small {
  color: #5f7686;
  font-size: 8px;
}

.member-action {
  min-height: 28px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  margin-top: 10px;
}

.member-action span {
  color: #6f8797;
  font-size: 9px;
}

.member-action button {
  padding: 6px 9px;
  border: 1px solid rgba(232, 108, 128, 0.38);
  border-radius: 7px;
  color: #ff9bab;
  background: rgba(117, 31, 50, 0.18);
  cursor: pointer;
  font-size: 9px;
}

@media (max-width: 760px) {
  .agent-panel {
    width: min(240px, calc(100% - 24px));
    max-height: calc(100% - 24px);
  }

  .agent-list {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
