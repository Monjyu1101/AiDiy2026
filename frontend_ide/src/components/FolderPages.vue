<!-- COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
Licensed under "AiDiy 公開利用ライセンス v1.1".
Commercial use requires prior written consent from all copyright holders.
See LICENSE for full terms. Thank you for keeping the rules.
https://github.com/monjyu1101/AiDiy2026 -->
<script setup>
import { computed, ref, shallowRef, watch, nextTick, onBeforeUnmount } from 'vue';
import FileTypeIcon from './FileTypeIcon.vue';
import { indexFolderPages, createFolderPageMemory, folderPageTurnPlan } from '../folder-pages.js';
const props = defineProps({ tree: Object, current: { type: String, default: '' }, selected: String, unlistedParent: String, marks: Object, active: Boolean, color: Function });
const emit = defineEmits(['select', 'clear', 'refresh', 'toggle-explorer', 'activity']);
const pages = computed(() => props.active ? indexFolderPages(props.tree, props.marks) : new Map());
const page = computed(() => pages.value.get(props.current));
const entries = computed(() => page.value?.entries || []);
const trail = computed(() => props.current.split('/').filter(Boolean));
const memory = createFolderPageMemory(), body = ref(), cursor = ref(''), turn = shallowRef(null);
const pageTurn = computed(() => turn.value?.direction || '');
const turnPath = computed(() => turn.value?.incoming.path || ''), turnSkipped = computed(() => turn.value?.skipped || 0);
const turnDuration = ref(1000);
let turnSteps = [], turnSerial = 0, pointerTurn = false;
const motionQuery = typeof matchMedia === 'function' ? matchMedia('(prefers-reduced-motion: reduce)') : null;
function motionChanged(event) { if (event.matches) cancelTurns(); }
motionQuery?.addEventListener?.('change', motionChanged);
// 操作・現在地は常に最終目的地。重ねる経由ページと旧ページは表示専用にする。
const layers = computed(() => {
  const live = { id: `live:${props.current}`, path: props.current, entries: entries.value, cursor: cursor.value, selected: props.selected, live: true };
  if (!turn.value) return [live];
  const { id, incoming, outgoing } = turn.value;
  return [live, ...(incoming.path === props.current ? [] : [{ ...incoming, id: `${id}:incoming` }]), { ...outgoing, id, outgoing: true }];
});
function bindBody(element, layer) {
  if (layer.live) body.value = element;
  else if (element) element.scrollTop = layer.scrollTop;
}
let disposed = false, restoration = 0, pendingFocus = false, presentedPath = props.current;
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
function snapshot(path, visible = false) {
  const items = pages.value.get(path)?.entries || [];
  const state = visible ? { cursor: cursor.value, scrollTop: body.value?.scrollTop || 0 } : memory.restore(path, items);
  return { path, entries: items.map(entry => ({ ...entry })), ...state, selected: props.selected };
}
function cancelTurns() { turnSteps = []; turn.value = null; }
function pointerStart() { pointerTurn = !!turn.value; }
function pointerCancel() { pointerTurn = false; }
function settleClick(event) {
  const covered = pointerTurn || !!turn.value; pointerTurn = false;
  if (!covered) return;
  // 旧ページに見える行へのクリックで、下に隠れた別の項目を開かない。
  cancelTurns(); event.preventDefault(); event.stopPropagation();
}
function showNextTurn(outgoing) {
  const step = turnSteps.shift();
  turn.value = step ? { ...step, id: ++turnSerial, outgoing, incoming: snapshot(step.path) } : null;
}
function startTurns(previous, path, enabled) {
  cancelTurns();
  turnSteps = enabled ? folderPageTurnPlan(previous, path) : [];
  // 実際に重ねる枚数へ総時間を配り、1枚でも深い移動でも全体を約1秒に揃える。
  turnDuration.value = 1000 / Math.max(1, turnSteps.length);
  if (turnSteps.length) showNextTurn(snapshot(previous, true));
}
function finishTurn(event, id) {
  // 同じ方向の連打や経由ページでも、破棄済みの旧要素から届く終了通知を再適用しない。
  if (!turn.value || id !== turn.value.id || event.target !== event.currentTarget || event.animationName !== `folder-page-${pageTurn.value}`) return;
  if (event.type === 'animationcancel') cancelTurns();
  else showNextTurn(turn.value.incoming);
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
function pointerMove(event) { if (event.buttons && event.target === body.value) { cancelTurns(); activity(); } }
function keydown(event) {
  if (!props.active || event.defaultPrevented || event.isComposing) return;
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'b') { event.preventDefault(); event.stopPropagation(); emit('toggle-explorer'); return; }
  if (event.target?.closest?.('input, textarea, select, [contenteditable="true"]')) return;
  if (event.key === 'Backspace' || (event.altKey && event.key === 'ArrowLeft')) { event.preventDefault(); event.stopPropagation(); back(); return; }
  if (event.key === 'Escape') { event.preventDefault(); event.stopPropagation(); if (props.selected) emit('clear'); else back(); return; }
  if (event.key.toLowerCase() === 'r' && !event.ctrlKey && !event.metaKey && !event.altKey) { event.preventDefault(); emit('refresh'); return; }
  // パンくずと親ボタンは通常のTab/Enter操作。項目リストだけにロービング選択を適用する。
  if (!body.value?.contains(event.target)) return;
  if (turn.value && ['Enter', ' ', 'ArrowRight'].includes(event.key)) { event.preventDefault(); cancelTurns(); activity(); return; }
  cancelTurns();
  if (['ArrowDown', 'ArrowUp', 'Home', 'End', 'PageDown', 'PageUp'].includes(event.key)) activity();
  const index = entries.value.findIndex(entry => entry.path === cursor.value);
  if (['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) {
    event.preventDefault();
    void move(event.key === 'Home' ? 0 : event.key === 'End' ? entries.value.length - 1 : index + (event.key === 'ArrowDown' ? 1 : -1));
  } else if (event.key === 'ArrowLeft') { event.preventDefault(); back(); }
  else if (event.key === 'ArrowRight' && entries.value[index]?.type === 'dir') { event.preventDefault(); select(entries.value[index]); }
  else if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); if (entries.value[index]) select(entries.value[index]); }
}
watch([() => props.current, () => props.active, pages], ([path, active, index], [previous, wasActive, previousIndex]) => {
  // 一覧更新と移動が同じtickでも、旧ページのカーソルを保存してから一度だけ復元する。
  const moved = path !== previous || active !== wasActive;
  if (moved && wasActive) save(previous);
  if (moved) startTurns(previous || '', path, active && wasActive && index === previousIndex && !motionQuery?.matches);
  else cancelTurns();
  presentedPath = path;
  if (active) void restore(moved, moved);
}, { immediate: true });
watch(() => props.selected, selected => {
  if (presentedPath === props.current && entries.value.some(entry => entry.path === selected)) { cursor.value = selected; memory.save(props.current, { cursor: selected }); }
});
onBeforeUnmount(() => { disposed = true; restoration++; cancelTurns(); motionQuery?.removeEventListener?.('change', motionChanged); memory.clear(); });
</script>
<template>
  <section v-if="active" class="folder-pages" aria-label="2D フォルダページ" @keydown="keydown" @wheel.passive="activity" @touchmove.passive="activity" @pointerdown="activity" @pointermove="pointerMove">
    <header class="folder-page-heading">
      <button v-if="trail.length" title="親フォルダへ戻る（Backspace）" @click="back">← 親へ</button>
      <nav aria-label="現在のフォルダ">
        <button :aria-current="!trail.length ? 'location' : undefined" @click="navigate('')">{{ tree?.n }}</button>
        <template v-for="(name, index) in trail" :key="index"><span aria-hidden="true">›</span><button :aria-current="index===trail.length-1 ? 'location' : undefined" @click="navigate(trail.slice(0,index+1).join('/'))">{{ name }}</button></template>
      </nav>
      <button class="folder-page-refresh" title="一覧を更新" aria-label="一覧を更新" @click="emit('refresh')">↻</button>
    </header>
    <p v-if="unlistedParent!==undefined" class="folder-page-reference-note" role="status">検索ファイルの親フォルダ「{{ unlistedParent || '/' }}」は現在の一覧にありません。プレビューは開いたままです。該当ページへ移動するには、フィルターをOFFにして一覧を更新し、検索結果を選び直してください。</p>
    <div class="folder-page-summary" role="status">{{ page?.folders.length || 0 }} フォルダ · {{ page?.files.length || 0 }} ファイル<span v-if="pageTurn" class="folder-page-turn-status" aria-hidden="true">ページ移動 {{ turnPath || '/' }}{{ turnSkipped ? '（'+turnSkipped+'階層省略）' : '' }}</span><span v-else>この階層の直下</span></div>
    <div class="folder-page-stack" :style="{'--page-turn-duration':turnDuration+'ms'}" @pointerdown.capture="pointerStart" @pointercancel.capture="pointerCancel" @click.capture="settleClick" @wheel.capture.passive="cancelTurns" @touchmove.capture.passive="cancelTurns">
      <div v-for="layer in layers" :key="layer.id" :ref="element => bindBody(element,layer)" class="folder-page-body" :class="layer.live ? '' : ['folder-page-sheet',layer.outgoing ? 'page-turn-'+pageTurn : 'folder-page-underlay']" :data-page-path="layer.path" :data-page-layer="layer.live ? 'live' : layer.outgoing ? 'outgoing' : 'incoming'" :tabindex="layer.live ? 0 : undefined" :role="layer.live ? 'listbox' : undefined" :aria-label="layer.live ? 'フォルダとファイル' : undefined" :aria-hidden="layer.live ? undefined : true" :inert="!layer.live" :aria-activedescendant="layer.live && cursor ? 'folder-page-entry-'+entries.findIndex(entry=>entry.path===cursor) : undefined" @scroll="layer.live && layer.path===current && save(layer.path)" @animationend="finishTurn($event,layer.id)" @animationcancel="finishTurn($event,layer.id)">
        <div class="folder-page-items">
          <div v-for="(entry,index) in layer.entries" :id="layer.live ? 'folder-page-entry-'+index : undefined" :key="entry.path" class="folder-page-entry" :class="{folder:entry.type==='dir',striped:!!entry.striped,marked:!!entry.marked,selected:layer.selected===entry.path}" :data-cursor="layer.cursor===entry.path" :role="layer.live ? 'option' : undefined" :aria-selected="layer.live ? cursor===entry.path : undefined" :aria-label="layer.live ? entry.name+(entry.type==='dir'?' フォルダ':' ファイル') : undefined" :title="entry.path" @click="layer.live && select(entry)">
            <span class="folder-page-icon" aria-hidden="true"><FileTypeIcon :name="entry.name" :directory="entry.type==='dir'" /></span>
            <span class="folder-page-name">{{ entry.name }}</span>
            <span v-if="entry.type==='dir'" class="folder-page-meta">{{ entry.count }} ファイル<span v-if="entry.marked" class="folder-page-mark"> · 対象 {{ entry.marked }}</span></span>
            <span v-else class="folder-page-meta"><span class="folder-page-size">{{ formatSize(entry.size) }}</span><time :datetime="new Date(entry.mtime).toISOString()">{{ formatDate(entry.mtime) }}</time></span>
          </div>
          <p v-if="!layer.entries.length" class="folder-page-empty">この階層に表示できるフォルダ・ファイルはありません</p>
        </div>
      </div>
      <svg v-if="turn" :key="'edge:'+turn.id" class="folder-page-turn-edge" :class="'page-turn-'+pageTurn" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true" focusable="false"><line x1="100" y1="0" x2="0" y2="100" vector-effect="non-scaling-stroke" /></svg>
    </div>
    <footer>フォルダを開くと次のページへ · ↑↓ 選択 · Enter 開く · Backspace 親へ</footer>
  </section>
</template>
