<!-- COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
Licensed under "AiDiy 公開利用ライセンス v1.1".
Commercial use requires prior written consent from all copyright holders.
See LICENSE for full terms. Thank you for keeping the rules.
https://github.com/monjyu1101/AiDiy2026 -->
<script setup>
import { computed, ref, watch, nextTick, onBeforeUnmount } from 'vue';
import { indexFolderPages, createFolderPageMemory, folderPageTurnPlan } from '../folder-pages.js';
const props = defineProps({ tree: Object, current: { type: String, default: '' }, selected: String, unlistedParent: String, marks: Object, active: Boolean, color: Function });
const emit = defineEmits(['select', 'clear', 'refresh', 'toggle-explorer', 'activity']);
const pages = computed(() => props.active ? indexFolderPages(props.tree, props.marks) : new Map());
const page = computed(() => pages.value.get(props.current));
const entries = computed(() => page.value?.entries || []);
const trail = computed(() => props.current.split('/').filter(Boolean));
const memory = createFolderPageMemory(), body = ref(), cursor = ref(''), pageTurn = ref('');
const turnCount = ref(1), turnDuration = ref(300), turnPath = ref(''), turnSkipped = ref(0);
let turnGroups = [], turnGroup = 0, turnIndex = 0;
let disposed = false, restoration = 0, pendingFocus = false;
const formatSize = size => size < 1024 ? `${size} B` : size < 1024 ** 2 ? `${(size / 1024).toFixed(1)} KB` : `${(size / 1024 ** 2).toFixed(1)} MB`;
const formatDate = mtime => new Date(mtime).toLocaleString('ja-JP', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
function save(path = props.current) {
  memory.save(path, { cursor: cursor.value, scrollTop: body.value?.scrollTop || 0 });
}
async function restore(focus = false, preferSelected = false) {
  pendingFocus ||= focus;
  const run = ++restoration, path = props.current;
  const state = memory.restore(path, entries.value, preferSelected ? props.selected : '');
  cursor.value = state.cursor;
  await nextTick();
  if (disposed || run !== restoration || path !== props.current || !props.active) return;
  if (body.value) body.value.scrollTop = state.scrollTop;
  if (pendingFocus) { pendingFocus = false; body.value?.focus({ preventScroll: true }); }
}
function select(entry) {
  cursor.value = entry.path; save();
  body.value?.focus({ preventScroll: true });
  emit('select', { type: entry.type, path: entry.path, source: 'page' });
}
function navigate(path) { save(); emit('select', { type: 'dir', path, source: 'page' }); }
function back() { if (trail.value.length) navigate(trail.value.slice(0, -1).join('/')); }
function turnLabel() {
  const step = turnGroups[turnGroup]?.[turnIndex];
  turnPath.value = step?.path || ''; turnSkipped.value = step?.skipped || 0;
}
function showTurnGroup() {
  const group = turnGroups[turnGroup]; turnIndex = 0;
  pageTurn.value = group?.[0].direction || ''; turnCount.value = group?.length || 1; turnLabel();
}
function startTurns(previous, path, enabled) {
  const steps = enabled ? folderPageTurnPlan(previous, path) : [];
  turnGroups = []; turnGroup = 0;
  for (const step of steps) {
    if (turnGroups.at(-1)?.[0].direction !== step.direction) turnGroups.push([]);
    turnGroups.at(-1).push(step);
  }
  turnDuration.value = steps.length > 1 ? 180 : 300;
  showTurnGroup();
}
function isCurrentTurn(event) {
  return event.target === body.value && event.currentTarget === body.value && event.animationName === `folder-page-${pageTurn.value}`;
}
function nextTurn(event) {
  if (!isCurrentTurn(event)) return;
  turnIndex = Math.min(turnIndex + 1, (turnGroups[turnGroup]?.length || 1) - 1); turnLabel();
}
function finishTurn(event) {
  // 連続移動で消えた前ページのanimationend/cancelは、次ページの演出を終了させない。
  if (!isCurrentTurn(event)) return;
  if (event.type === 'animationcancel') turnGroups = [];
  turnGroup++; showTurnGroup();
}
async function move(index) {
  const entry = entries.value[Math.max(0, Math.min(entries.value.length - 1, index))];
  if (!entry) return;
  const path = props.current;
  cursor.value = entry.path; save();
  await nextTick();
  if (!disposed && props.active && path === props.current && cursor.value === entry.path) body.value?.querySelector('[data-cursor="true"]')?.scrollIntoView({ block: 'nearest' });
}
// 復元・scrollIntoView・レイアウトによるscrollは保存だけ。実際の入力だけを手動操作として伝える。
function activity() { if (props.active) emit('activity'); }
function pointerMove(event) { if (event.buttons && event.target === body.value) activity(); }
function keydown(event) {
  if (!props.active || event.defaultPrevented || event.isComposing) return;
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'b') { event.preventDefault(); event.stopPropagation(); emit('toggle-explorer'); return; }
  if (event.target?.closest?.('input, textarea, select, [contenteditable="true"]')) return;
  if (event.key === 'Backspace' || (event.altKey && event.key === 'ArrowLeft')) { event.preventDefault(); event.stopPropagation(); back(); return; }
  if (event.key === 'Escape') { event.preventDefault(); event.stopPropagation(); if (props.selected) emit('clear'); else back(); return; }
  if (event.key.toLowerCase() === 'r' && !event.ctrlKey && !event.metaKey && !event.altKey) { event.preventDefault(); emit('refresh'); return; }
  // パンくずと親ボタンは通常のTab/Enter操作。項目リストだけにロービング選択を適用する。
  if (!body.value?.contains(event.target)) return;
  if (['ArrowDown', 'ArrowUp', 'Home', 'End', 'PageDown', 'PageUp'].includes(event.key)) activity();
  const index = entries.value.findIndex(entry => entry.path === cursor.value);
  if (['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) {
    event.preventDefault();
    void move(event.key === 'Home' ? 0 : event.key === 'End' ? entries.value.length - 1 : index + (event.key === 'ArrowDown' ? 1 : -1));
  } else if (event.key === 'ArrowLeft') { event.preventDefault(); back(); }
  else if (event.key === 'ArrowRight' && entries.value[index]?.type === 'dir') { event.preventDefault(); select(entries.value[index]); }
  else if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); if (entries.value[index]) select(entries.value[index]); }
}
watch([() => props.current, () => props.active], ([path, active], [previous, wasActive]) => {
  // パス変更とモード切替が同じtickでも、まだ描画されている旧ページへ位置を保存する。
  if (wasActive) save(previous);
  const reduced = typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;
  startTurns(previous || '', path, active && wasActive && !reduced);
  if (active) void restore(true, true);
}, { immediate: true });
watch(entries, () => { if (props.active) void restore(); });
watch(() => props.selected, selected => {
  if (entries.value.some(entry => entry.path === selected)) { cursor.value = selected; memory.save(props.current, { cursor: selected }); }
});
onBeforeUnmount(() => { disposed = true; restoration++; memory.clear(); });
</script>
<template>
  <section v-if="active" class="folder-pages" aria-label="2D フォルダページ" @keydown="keydown" @wheel.passive="activity" @touchmove.passive="activity" @pointerdown="activity" @pointermove="pointerMove">
    <header class="folder-page-heading">
      <button :disabled="!trail.length" title="親フォルダへ戻る（Backspace）" @click="back">← 親へ</button>
      <nav aria-label="現在のフォルダ">
        <button :aria-current="!trail.length ? 'location' : undefined" @click="navigate('')">{{ tree?.n }}</button>
        <template v-for="(name, index) in trail" :key="index"><span aria-hidden="true">›</span><button :aria-current="index===trail.length-1 ? 'location' : undefined" @click="navigate(trail.slice(0,index+1).join('/'))">{{ name }}</button></template>
      </nav>
      <button class="folder-page-refresh" title="一覧を更新" aria-label="一覧を更新" @click="emit('refresh')">↻</button>
    </header>
    <p v-if="unlistedParent!==undefined" class="folder-page-reference-note" role="status">検索ファイルの親フォルダ「{{ unlistedParent || '/' }}」は現在の一覧にありません。プレビューは開いたままです。該当ページへ移動するには、フィルターをOFFにして一覧を更新し、検索結果を選び直してください。</p>
    <div class="folder-page-summary" role="status">{{ page?.folders.length || 0 }} フォルダ · {{ page?.files.length || 0 }} ファイル<span v-if="pageTurn" class="folder-page-turn-status" aria-hidden="true">ページ移動 {{ turnPath || '/' }}{{ turnSkipped ? '（'+turnSkipped+'階層省略）' : '' }}</span><span v-else>この階層の直下</span></div>
    <div :key="current" ref="body" class="folder-page-body" :class="pageTurn ? 'page-turn-'+pageTurn : ''" :style="{'--page-turn-count':turnCount,'--page-turn-duration':turnDuration+'ms'}" tabindex="0" role="listbox" aria-label="フォルダとファイル" :aria-activedescendant="cursor ? 'folder-page-entry-'+entries.findIndex(entry=>entry.path===cursor) : undefined" @scroll="save()" @animationiteration="nextTurn" @animationend="finishTurn" @animationcancel="finishTurn">
      <div class="folder-page-items">
        <div v-for="(entry,index) in entries" :id="'folder-page-entry-'+index" :key="entry.path" class="folder-page-entry" :class="{folder:entry.type==='dir',marked:!!entry.marked,selected:selected===entry.path}" :data-cursor="cursor===entry.path" role="option" :aria-selected="cursor===entry.path" :aria-label="entry.name+(entry.type==='dir'?' フォルダ':' ファイル')" :title="entry.path" @click="select(entry)">
          <span class="folder-page-icon" :style="{color:entry.type==='dir' ? undefined : color?.(entry.name)}" aria-hidden="true">{{ entry.type==='dir' ? '▸ 📁' : '●' }}</span>
          <span class="folder-page-name">{{ entry.name }}</span>
          <span v-if="entry.type==='dir'" class="folder-page-meta">{{ entry.count }} ファイル<span v-if="entry.marked" class="folder-page-mark"> · 対象 {{ entry.marked }}</span></span>
          <span v-else class="folder-page-meta">{{ formatSize(entry.size) }}<time :datetime="new Date(entry.mtime).toISOString()">{{ formatDate(entry.mtime) }}</time></span>
        </div>
        <p v-if="!entries.length" class="folder-page-empty">この階層に表示できるフォルダ・ファイルはありません</p>
      </div>
    </div>
    <footer>フォルダを開くと次のページへ · ↑↓ 選択 · Enter 開く · Backspace 親へ</footer>
  </section>
</template>
