<script setup lang="ts">
// AIタスク_フロー図: タスク明細から開始〜終了のフローを mermaid 図で表示し、
// クリティカルパス（最長所要経路）を強調表示する
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue';
import type { PropType } from 'vue';
import mermaid from 'mermaid';

const props = defineProps({
  タスクID: { type: String, default: '' },
  タイトル: { type: String, default: '' },
  マーメイド記号: { type: String, default: '' },
  明細: { type: Array as PropType<Record<string, any>[]>, default: () => [] }
});

mermaid.initialize({
  startOnLoad: false,
  theme: 'default',
  themeVariables: {
    background: '#12101a',
    primaryColor: '#ffffff',
    primaryBorderColor: '#8f68dd',
    primaryTextColor: '#333333',
    lineColor: '#9c8fd0'
  }
});

const diagramHost = ref<HTMLElement | null>(null);
const renderError = ref('');
let renderSeq = 0;

interface パス結果 {
  経路SEQ: number[];
}

// クリティカルパス（最長依存経路）を求める
function クリティカルパス計算(rows: Record<string, any>[]): パス結果 {
  const dist: Record<number, number> = {};
  const prev: Record<number, number | null> = {};
  const sorted = [...rows].sort((a, b) => Number(a.明細SEQ) - Number(b.明細SEQ));

  for (const row of sorted) {
    const seq = Number(row.明細SEQ);
    const preds = String(row.先行SEQ || '')
      .split(',')
      .map((s) => Number(s.trim()))
      .filter((n) => !Number.isNaN(n) && n >= 0 && dist[n] !== undefined);
    let base = 0;
    let bestPred: number | null = null;
    for (const p of preds) {
      if (bestPred === null || dist[p] > base) {
        base = dist[p];
        bestPred = p;
      }
    }
    dist[seq] = base + 1;
    prev[seq] = bestPred;
  }

  // 後続を持たない工程のうち、最長のものを終点とする
  const hasSuccessor = new Set<number>();
  for (const row of sorted) {
    for (const s of String(row.先行SEQ || '').split(',')) {
      const n = Number(s.trim());
      if (!Number.isNaN(n) && n > 0) hasSuccessor.add(n);
    }
  }
  let goal: number | null = null;
  let goalDist = -1;
  for (const row of sorted) {
    const seq = Number(row.明細SEQ);
    if (!hasSuccessor.has(seq) && dist[seq] > goalDist) {
      goal = seq;
      goalDist = dist[seq];
    }
  }

  const 経路SEQ: number[] = [];
  let cursor = goal;
  while (cursor !== null && cursor !== undefined) {
    経路SEQ.unshift(cursor);
    cursor = prev[cursor] ?? null;
  }
  return { 経路SEQ };
}

const クリティカルパス = computed(() => クリティカルパス計算(props.明細));

const クリティカルパス表示 = computed(() => {
  const { 経路SEQ } = クリティカルパス.value;
  if (経路SEQ.length === 0) return '';
  const byName = new Map(props.明細.map((row) => [Number(row.明細SEQ), String(row.タイトル || '')]));
  const names = 経路SEQ.map((seq) => byName.get(seq) ?? String(seq));
  return names.join(' → ');
});

// mermaid 図テキストを生成する（標準は上から下の TD）
function マーメイド生成(rows: Record<string, any>[], direction: string): string {
  const { 経路SEQ } = クリティカルパス.value;
  const critNodes = new Set(経路SEQ);
  const critEdges = new Set<string>();
  for (let i = 0; i < 経路SEQ.length - 1; i += 1) {
    critEdges.add(`${経路SEQ[i]}>${経路SEQ[i + 1]}`);
  }

  const lines: string[] = [`flowchart ${direction}`];

  const sorted = [...rows].sort((a, b) => Number(a.明細SEQ) - Number(b.明細SEQ));
  const predsMap = new Map<number, number[]>();
  for (const row of sorted) {
    const seq = Number(row.明細SEQ);
    const preds = String(row.先行SEQ || '')
      .split(',')
      .map((s) => Number(s.trim()))
      .filter((n) => !Number.isNaN(n) && n >= 0 && n !== seq);
    predsMap.set(seq, preds);
    const タイトル = String(row.タイトル || '').replace(/["\[\]<>]/g, '');
    if (seq === 0 || seq === 9999) {
      lines.push(`  N${seq}(("${タイトル}"))`);
    } else {
      lines.push(`  N${seq}["${タイトル}"]`);
    }
  }

  // エッジ定義（linkStyle 用に出現順を記録する）
  const edgeKeys: string[] = [];
  for (const row of sorted) {
    const seq = Number(row.明細SEQ);
    const preds = predsMap.get(seq) ?? [];
    for (const p of preds) {
      lines.push(`  N${p} --> N${seq}`);
      edgeKeys.push(`${p}>${seq}`);
    }
  }

  // クリティカルパスの強調
  lines.push('  classDef crit fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#1b5e20;');
  lines.push('  classDef term fill:#f5f1e8,stroke:#2e7d32,color:#2e7d32;');
  if (sorted.some((row) => Number(row.明細SEQ) === 0)) {
    lines.push('  class N0 term;');
  }
  if (sorted.some((row) => Number(row.明細SEQ) === 9999)) {
    lines.push('  class N9999 term;');
  }
  if (critNodes.size > 0) {
    lines.push(`  class ${[...critNodes].map((seq) => `N${seq}`).join(',')} crit;`);
  }
  edgeKeys.forEach((key, index) => {
    if (critEdges.has(key)) {
      lines.push(`  linkStyle ${index} stroke:#66bb6a,stroke-width:2.5px;`);
    }
  });

  return lines.join('\n');
}

async function 図描画() {
  renderError.value = '';
  await nextTick();
  const host = diagramHost.value;
  if (!host) return;
  if (props.明細.length === 0) {
    host.innerHTML = '';
    return;
  }
  renderSeq += 1;
  const seq = renderSeq;
  try {
    // 標準は縦表示 TD。明示的な縦方向指定だけ反映する
    const 指定 = props.マーメイド記号.trim().toUpperCase();
    const direction = ['TD', 'TB'].includes(指定)
      ? 指定
      : 'TD';
    const code = マーメイド生成(props.明細, direction);
    const { svg } = await mermaid.render(`taskflow${seq}`, code);
    if (seq !== renderSeq) return; // 後発の描画が始まっていたら古い結果は捨てる
    host.innerHTML = svg;
  } catch (e) {
    if (seq !== renderSeq) return;
    host.innerHTML = '';
    renderError.value = 'フロー図の描画に失敗しました。';
  }
}

watch([() => props.明細, () => props.マーメイド記号], 図描画, { deep: true });

let resizeTimer: ReturnType<typeof setTimeout> | null = null;
const handleResize = () => {
  if (resizeTimer) clearTimeout(resizeTimer);
  resizeTimer = setTimeout(図描画, 300);
};

onMounted(() => {
  window.addEventListener('resize', handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
  if (resizeTimer) clearTimeout(resizeTimer);
});
</script>

<template>
  <div class="flow-panel">
    <div class="panel-header">
      <span class="panel-title">【フロー図】</span>
      <span v-if="props.タスクID" class="panel-subtitle">{{ props.タスクID }} {{ props.タイトル }}</span>
    </div>

    <div class="panel-body">
      <div v-if="!props.タスクID" class="panel-placeholder">
        タスク要求を選択してください
      </div>
      <template v-else>
        <div v-if="renderError" class="panel-error">{{ renderError }}</div>
        <div ref="diagramHost" class="diagram-host"></div>
        <div v-if="クリティカルパス表示" class="critical-path">
          <span class="critical-label">クリティカルパス:</span>
          {{ クリティカルパス表示 }}
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.flow-panel {
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

.panel-subtitle {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.85);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.panel-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: auto;
  padding: 8px;
}

.panel-placeholder {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(220, 214, 247, 0.55);
  font-size: 13px;
}

.panel-error {
  color: #ef5350;
  font-size: 12px;
  padding: 4px;
}

.diagram-host {
  flex: 1;
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: auto;
}

/* viewBox を保ったままパネル一杯に拡大表示する（mermaid の inline max-width を打ち消す） */
.diagram-host :deep(svg) {
  width: 100% !important;
  height: 100% !important;
  max-width: none !important;
}

.critical-path {
  flex-shrink: 0;
  border-top: 1px solid rgba(118, 97, 204, 0.5);
  padding: 8px 4px 2px;
  font-size: 12px;
  color: #bbb;
  line-height: 1.5;
}

.critical-label {
  color: #66bb6a;
  margin-right: 6px;
}
</style>
