<script setup lang="ts">
import { ref } from 'vue';
import AiTeamMemberSummon from './dialog/AIチーム_メンバー召喚.vue';
import type { エージェント, チーム要員, 状態表示 } from './AIチーム_型';
import { use自由配置パネル } from './use自由配置パネル';

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
      <div class="progress-track"><span></span></div>
      <small>コンテキスト使用量 42%</small>
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

.progress-track {
  height: 3px;
  margin: 12px 0 6px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(120, 151, 169, 0.15);
}

.progress-track span {
  width: 42%;
  height: 100%;
  display: block;
  border-radius: inherit;
  background: linear-gradient(90deg, #58d4f0, #68e8ad);
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
