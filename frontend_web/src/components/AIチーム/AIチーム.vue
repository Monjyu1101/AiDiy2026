<script setup lang="ts">
import { onMounted } from 'vue';
import AiTeamMembers from './AIチーム_メンバー.vue';
import AiTeamViewer from './AIチーム_立体表示.vue';
import AiTeamWorkList from './AIチーム_作業一覧.vue';
import { 状態情報 } from './AIチーム_型';
import { useAIチーム } from './useAIチーム';

const {
  エージェント一覧,
  選択中ID,
  召喚対象ID,
  要員読込中,
  要員読込エラー,
  召喚中,
  排除中ID,
  選択中エージェント,
  稼働数,
  相談数,
  瞑想数,
  召喚可能要員一覧,
  要員一覧を読み込む,
  選択要員を召喚,
  選択要員を排除,
  状態を更新,
} = useAIチーム();

onMounted(要員一覧を読み込む);
</script>

<template>
  <section class="team-page">
    <header class="team-header">
      <div class="title-block">
        <div class="eyebrow"><span class="live-dot"></span>CONTINUOUS AGENT SPACE</div>
        <div class="title-row">
          <h1>AIチーム</h1>
          <span class="mock-badge">MOCKUP</span>
        </div>
        <p>自律エージェントたちが、仕事をしたり、雑談したり、瞑想したり。</p>
      </div>

      <div class="summary">
        <div class="summary-item">
          <span class="summary-value">{{ エージェント一覧.length }}</span>
          <span class="summary-label">要員数</span>
        </div>
        <div class="summary-item active">
          <span class="summary-value">{{ 稼働数 }}</span>
          <span class="summary-label">作業中</span>
        </div>
        <div class="summary-item">
          <span class="summary-value">{{ 相談数 }}</span>
          <span class="summary-label">相談中</span>
        </div>
        <div class="summary-item">
          <span class="summary-value">{{ 瞑想数 }}</span>
          <span class="summary-label">瞑想中</span>
        </div>
      </div>

    </header>

    <div class="workspace">
      <AiTeamMembers
        :エージェント一覧="エージェント一覧"
        :選択中ID="選択中ID"
        :選択中エージェント="選択中エージェント"
        :排除中ID="排除中ID"
        :状態情報="状態情報"
        :召喚可能要員一覧="召喚可能要員一覧"
        :召喚対象ID="召喚対象ID"
        :召喚中="召喚中"
        :要員読込中="要員読込中"
        :要員読込エラー="要員読込エラー"
        :召喚実行="選択要員を召喚"
        :要員再読込="要員一覧を読み込む"
        @select="選択中ID = $event"
        @expel="選択要員を排除"
        @update:summon-target="召喚対象ID = $event"
      />
      <AiTeamViewer
        :エージェント一覧="エージェント一覧"
        :選択中ID="選択中ID"
        :要員読込中="要員読込中"
        :要員読込エラー="要員読込エラー"
        @select="選択中ID = $event"
        @retry="要員一覧を読み込む"
        @state-change="状態を更新"
      />
      <AiTeamWorkList />
    </div>
  </section>
</template>

<style scoped>
.team-page {
  --panel: rgba(11, 24, 37, 0.94);
  --line: rgba(139, 206, 231, 0.14);
  --muted: #7891a3;
  min-height: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  color: #edf8ff;
  background: radial-gradient(circle at 48% -20%, rgba(50, 163, 203, 0.16), transparent 42%), #07111d;
}

.team-header {
  min-height: 108px;
  display: grid;
  grid-template-columns: minmax(320px, 1fr) auto;
  align-items: center;
  gap: 30px;
  padding: 16px 24px;
  border-bottom: 1px solid var(--line);
  background: rgba(7, 17, 29, 0.92);
  z-index: 4;
}

.eyebrow {
  color: #5ddaf7;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.16em;
}

.live-dot {
  width: 7px;
  height: 7px;
  display: inline-block;
  margin-right: 7px;
  border-radius: 50%;
  background: #5ce3a1;
  box-shadow: 0 0 12px #5ce3a1;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 3px 0 2px;
}

.title-row h1 {
  margin: 0;
  font-size: 26px;
}

.mock-badge {
  padding: 3px 8px;
  border: 1px solid rgba(155, 132, 255, 0.48);
  border-radius: 999px;
  color: #c9bbff;
  font-size: 9px;
}

.title-block p {
  margin: 0;
  color: #8ca5b8;
  font-size: 12px;
}

.summary {
  display: flex;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: rgba(14, 30, 45, 0.66);
}

.summary-item {
  min-width: 76px;
  padding: 10px 14px;
  text-align: center;
}

.summary-value,
.summary-label {
  display: block;
}

.summary-value {
  font-size: 20px;
  font-weight: 760;
}

.summary-item.active .summary-value {
  color: #62e7b0;
}

.summary-label {
  color: var(--muted);
  font-size: 10px;
}

.workspace {
  min-height: 0;
  flex: 1;
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr);
}

@media (max-width: 1180px) {
  .workspace {
    grid-template-columns: minmax(0, 1fr);
  }

  .summary {
    display: none;
  }
}

@media (max-width: 760px) {
  .team-page {
    height: auto;
    overflow: visible;
  }

  .team-header {
    grid-template-columns: 1fr;
    gap: 12px;
    padding: 14px 16px;
  }

  .workspace {
    display: flex;
    flex-direction: column;
  }
}
</style>
