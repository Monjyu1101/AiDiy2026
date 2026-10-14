<!-- COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
Licensed under "AiDiy 公開利用ライセンス v1.1".
Commercial use requires prior written consent from all copyright holders.
See LICENSE for full terms. Thank you for keeping the rules.
https://github.com/monjyu1101/AiDiy2026 -->
<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import { Terminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import '@xterm/xterm/css/xterm.css';
import StatusBar from './StatusBar.vue';
import TerminalWelcome from './TerminalWelcome.vue';
import { terminalCompletion, cliCompletions } from '../terminal-completion.js';
const props = defineProps({ base: String, icon: String, desktop: Boolean, linked: Boolean, visible: { type: Boolean, default: true } });
const container = ref(null), connected = ref(false), status = ref('起動中'), project = ref(''), shell = ref(''), error = ref('');
const completion = ref(''), toolsOnline = ref(false);
const toolsEnabled = ref(true), toolsChanging = ref(false), socketReady = ref(false);
const ghostRows = ref([]);
const inputStarted = ref(false);
const completionDescription = computed(() => cliCompletions[completion.value.split(' ')[0]]?.description || '');
const projectName = computed(() => project.value.replace(/[\\/]+$/, '').split(/[\\/]/).pop() || project.value);
let terminal, fit, socket, observer, input, key, resize, cursor, scroll, render, completionEnabled = false, disposed = false;
function startInput() {
  if (!connected.value || inputStarted.value) return;
  inputStarted.value = true;
  nextTick(() => { if (!disposed) { fitTerminal(); updateCompletion(); } });
}
async function clearDisplay() {
  terminal.clear();
  inputStarted.value = false;
  await nextTick();
  if (disposed) return;
  fitTerminal(); updateCompletion(); terminal.focus();
}
function updateCompletion() {
  completion.value = connected.value && completionEnabled ? terminalCompletion(terminal.buffer.active) : '';
  ghostRows.value = [];
  if (!completion.value || !props.visible) return;
  const buffer = terminal.buffer.active, screen = container.value.querySelector('.xterm-screen');
  if (!screen) return;
  const bounds = screen.getBoundingClientRect(), outer = container.value.getBoundingClientRect();
  const width = bounds.width / terminal.cols, height = bounds.height / terminal.rows;
  let x = buffer.cursorX, y = buffer.baseY + buffer.cursorY - buffer.viewportY;
  const previous = x > 0 ? buffer.getLine(buffer.baseY + buffer.cursorY)?.getCell(x - 1)?.getChars() : '';
  let suffix = (previous === ' ' ? '' : ' ') + cliCompletions[completion.value.split(' ')[0]].options;
  // コマンド直後の空白は透過のままにして、端末自身のカーソルを隠さない。
  if (suffix.startsWith(' ')) { x++; suffix = suffix.slice(1); }
  const rows = [];
  while (suffix && y < terminal.rows) {
    if (x >= terminal.cols) { x = 0; y++; continue; }
    const text = suffix.slice(0, terminal.cols - x);
    if (y >= 0) rows.push({ text, style: { left: `${bounds.left - outer.left + x * width}px`, top: `${bounds.top - outer.top + y * height}px`, width: `${(terminal.cols - x) * width}px`, height: `${height}px`, lineHeight: `${height}px` } });
    suffix = suffix.slice(text.length); x = 0; y++;
  }
  ghostRows.value = rows;
}
function send(value) { if (socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify(value)); }
function toggleTools() {
  if (!socketReady.value || toolsChanging.value) return;
  toolsChanging.value = true;
  send({ type: 'tools-check', enabled: !toolsEnabled.value });
}
function fitTerminal() {
  if (!props.visible || !container.value?.clientWidth || !container.value?.clientHeight) return;
  fit?.fit();
}
function connect() {
  if (disposed) return;
  inputStarted.value = false;
  socketReady.value = false; toolsChanging.value = false;
  socket?.close(); completion.value = ''; completionEnabled = false; terminal.reset(); connected.value = false; error.value = ''; status.value = '起動中';
  const url = new URL(props.base + 'socket', location.href); url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
  const current = socket = new WebSocket(url);
  current.onopen = () => { if (current !== socket || disposed) return current.close(); fitTerminal(); send({ type: 'start', cols: terminal.cols, rows: terminal.rows }); };
  current.onmessage = event => {
    if (current !== socket || disposed) return;
    const message = JSON.parse(event.data);
    if (message.type === 'ready') { connected.value = true; socketReady.value = true; toolsOnline.value = !!message.toolsOnline; toolsEnabled.value = !!message.toolsEnabled; completionEnabled = !!message.completion; status.value = '実行中'; project.value = message.project; shell.value = message.shell; terminal.focus(); }
    if (message.type === 'tools') { toolsOnline.value = !!message.online; toolsEnabled.value = !!message.enabled; toolsChanging.value = false; }
    if (message.type === 'data') terminal.write(message.data, () => { if (current === socket && current.readyState === WebSocket.OPEN) { current.send(JSON.stringify({ type: 'ack', length: message.data.length })); updateCompletion(); } });
    if (message.type === 'exit') { connected.value = false; completion.value = ''; status.value = `終了 (${message.exitCode})`; terminal.writeln(`\r\n[シェルが終了しました: ${message.exitCode}]`); }
    if (message.type === 'error') { error.value = message.message; status.value = 'エラー'; }
  };
  current.onclose = () => { if (current !== socket || disposed) return; socketReady.value = false; toolsChanging.value = false; connected.value = false; toolsOnline.value = false; completion.value = ''; if (status.value === '実行中' || status.value === '起動中') status.value = '切断'; };
  current.onerror = () => { if (current === socket && !disposed) error.value = '端末に接続できません。「再起動」で接続し直してください。'; };
}
watch(() => props.visible, async visible => { if (visible) { await nextTick(); fitTerminal(); terminal?.focus(); } });
onMounted(() => {
  terminal = new Terminal({ cursorBlink: true, fontSize: 14, fontFamily: 'Consolas, "Noto Sans Mono", monospace', scrollback: 5000,
    theme: { background: '#080b10', foreground: '#dce6f2', cursor: '#81e4e8', selectionBackground: '#365b78' } });
  fit = new FitAddon(); terminal.loadAddon(fit); terminal.open(container.value); fitTerminal();
  terminal.attachCustomKeyEventHandler(event => {
    // 選択がある時だけCtrl+Cをコピーに使い、それ以外はシェルへの割り込み。
    if (event.type === 'keydown' && (event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'c' && terminal.hasSelection()) {
      void navigator.clipboard.writeText(terminal.getSelection()).catch(() => { error.value = 'コピーできません。'; }); return false;
    }
    return true;
  });
  input = terminal.onData(data => { if (!connected.value) return; for (let i = 0; i < data.length; i += 16000) send({ type: 'input', data: data.slice(i, i + 16000) }); });
  key = terminal.onKey(startInput);
  container.value.addEventListener('input', startInput, true);
  container.value.addEventListener('paste', startInput, true);
  resize = terminal.onResize(({ cols, rows }) => { if (connected.value) send({ type: 'resize', cols, rows }); });
  cursor = terminal.onCursorMove(updateCompletion);
  scroll = terminal.onScroll(updateCompletion);
  render = terminal.onRender(updateCompletion);
  observer = new ResizeObserver(fitTerminal); observer.observe(container.value);
  connect();
});
onBeforeUnmount(() => { disposed = true; socket?.close(); observer?.disconnect(); input?.dispose(); key?.dispose(); container.value?.removeEventListener('input', startInput, true); container.value?.removeEventListener('paste', startInput, true); resize?.dispose(); cursor?.dispose(); scroll?.dispose(); render?.dispose(); terminal?.dispose(); });
</script>
<template>
  <section class="term-component" :class="{ 'desktop-window': desktop, 'term-waiting': !inputStarted }">
    <StatusBar :title="linked ? 'AiDiy IDE / Term' : 'AiDiy Term'" :mode="toolsEnabled ? 'online' : 'offline'" :status="toolsEnabled ? '' : '確認OFF'" :connected="toolsOnline" :desktop="desktop" clock-pulse />
    <div class="component-toolbar"><span :title="project">プロジェクト: {{ projectName }}</span><nav><button class="auto-connect" role="switch" :aria-checked="toolsEnabled" :title="`tools接続確認 ${toolsEnabled ? 'ON' : 'OFF'}`" :disabled="!socketReady || toolsChanging" @click="toggleTools"><span>tools接続確認</span><span class="auto-connect-track" aria-hidden="true"><span class="auto-connect-thumb"></span></span></button><button @click="clearDisplay">表示クリア</button><button v-if="!connected" @click="connect">再起動</button></nav></div>
    <div v-if="!inputStarted" class="term-welcome"><TerminalWelcome kind="term" :icon="icon || '/development/AiDiy.png'" /></div>
    <div class="term-screen" aria-label="ターミナル"><div ref="container" class="term-viewport"><div v-if="completion" class="term-completion" role="status" :aria-label="`${completion}（Tabで補完）`"><span v-for="(row, i) in ghostRows" :key="i" class="term-ghost-row" :style="row.style" aria-hidden="true">{{ row.text }}</span></div></div></div>
    <div class="term-meta"><span :title="completionDescription">{{ completion ? 'Tabで補完 · Enterで実行' : `${shell} · ${status}` }}</span><span :title="'toolsサーバーの稼働状態'">tools {{ !toolsEnabled ? '確認OFF' : toolsOnline ? 'オンライン' : 'オフライン' }}</span></div>
    <p v-if="error" class="term-error" role="alert">{{ error }}</p>
  </section>
</template>
<style scoped>
.term-component{height:100%;min-height:0;min-width:0;display:flex;flex-direction:column;background:#080b10;color:var(--foreground);font:var(--vscode-font-size,13px)/1.65 var(--vscode-font-family,"Segoe UI","Yu Gothic UI",sans-serif);container:term-panel / size}
.component-toolbar button{padding:2px 7px;border-color:var(--border);font-size:11px;line-height:1.4;background:transparent}
.term-welcome{flex:1;min-height:0;overflow:auto;background:var(--surface);container-type:size}
.term-waiting .term-screen{flex:none;height:84px;max-height:30%;border-top:1px solid var(--border)}
.term-meta{display:flex;justify-content:space-between;gap:8px;flex:none;padding:2px 8px;color:var(--muted);font-size:10px;border-top:1px solid var(--border)}
.term-meta>span:first-child{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.term-meta>span:last-child{flex:none;white-space:nowrap}
.term-screen{position:relative;flex:1;min-height:0;min-width:0;padding:8px;overflow:hidden}.term-error{color:#ffbac3;margin:6px 10px;font-size:12px}
/* FitAddonには余白を除いた領域を渡し、小さな画面でも最後の入力行を切らない。 */
.term-viewport{position:relative;width:100%;height:100%;min-width:0;min-height:0}
.term-completion{pointer-events:none}.term-ghost-row{position:absolute;z-index:4;white-space:pre;overflow:hidden;font:14px Consolas,"Noto Sans Mono",monospace;color:#77818f;background:#080b10}
/* 単独窓・IDE内タブとも、低い時は起動案内より端末の数行を優先する。 */
@container term-panel (max-height:240px){
 .term-welcome{display:none}
 .term-waiting .term-screen{flex:1;height:auto;max-height:none;border-top:0}
 .term-error{flex:none;max-height:1.65em;overflow:auto;margin:2px 8px;overflow-wrap:anywhere}
}
@container (max-height:240px){
 .term-welcome :deep(.terminal-welcome){padding:4px 0}
 .term-welcome :deep(.welcome-mark){width:36px;height:36px;margin-bottom:6px}
 .term-welcome :deep(.welcome-mark img){width:28px;height:28px}
 .term-welcome :deep(.welcome-eyebrow){font-size:9px;margin-bottom:4px}
 .term-welcome :deep(h1){font-size:16px;margin-bottom:4px}
 .term-welcome :deep(.welcome-caption){font-size:9px;line-height:1.4}
}
</style>
