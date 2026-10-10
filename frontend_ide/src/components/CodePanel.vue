<!-- COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
Licensed under "AiDiy 公開利用ライセンス v1.1".
Commercial use requires prior written consent from all copyright holders.
See LICENSE for full terms. Thank you for keeping the rules.
https://github.com/monjyu1101/AiDiy2026 -->
<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue';
import MarkdownIt from 'markdown-it';
import { codeTransport } from '../transports/code.js';
import { visibleStreamContent } from '../../host/src/stream-control';
import StatusBar from './StatusBar.vue';
import TerminalWelcome from './TerminalWelcome.vue';
import TerminalProgress from './TerminalProgress.vue';
import ModalDialog from './ModalDialog.vue';
import { chatArrival } from '../engines/chat-arrival';
const props = defineProps({ base: String, host: Boolean, icon: String, embedded: Boolean, linked: Boolean, desktop: Boolean });
const state = reactive({ メッセージ: [], 履歴: [], 進捗: [], 信頼済み: false, 自動接続: true });
const prompt = ref(''), error = ref(''), pending = ref(false), history = ref(false), picker = ref(false), catalogBusy = ref(false);
const stopPending = ref(false);
const autoPending = ref(false), deleteTarget = ref(null), deleting = ref(false), catalogReady = ref(false);
let catalogProvider = '';
const providers = ref([]), models = ref([]), provider = ref(''), model = ref(''), custom = ref(''), checks = ref(0);
const conversation = ref(), input = ref(), sendButton = ref(), progress = ref('');
const stream = ref();
const sendIcon = computed(() => new URL('sending.png', new URL(props.icon || '/development/AiDiy.png', location.href)).href);
const stopIcon = computed(() => new URL('abort.png', sendIcon.value).href);
const rows = new Map();
const arrivals = chatArrival(scroll);
let revision = 0, resizeObserver, checksRestored = false;
function scroll() { if (conversation.value) conversation.value.scrollTop = conversation.value.scrollHeight; }
const markdown = new MarkdownIt({ html: false, linkify: false, breaks: true });
markdown.renderer.rules.image = (tokens, index) => markdown.utils.escapeHtml(tokens[index].content);
const offline = computed(() => state.実行モード === 'offline' || (state.オフライン対応 && !state.接続済み));
const busy = computed(() => !!state.実行中 || !!state.モデル変更中 || pending.value);
const operable = computed(() => state.信頼済み && state.画面接続済み !== false);
const allowed = computed(() => state.信頼済み && state.画面接続済み !== false && !!state.作業フォルダ && (offline.value || state.接続済み));
const canSend = computed(() => allowed.value && !busy.value && prompt.value.trim());
const canStop = computed(() => allowed.value && state.実行中 && !state.停止中 && !stopPending.value);
const modelLabel = computed(() => `${state.provider || '自動'} - ${state.model || (state.provider ? '既定モデル' : 'AIコアの設定')}`);
const sortedHistory = computed(() => [...state.履歴].sort((a, b) => b.更新日時 - a.更新日時));
const canApplyModel = computed(() => catalogReady.value && !catalogBusy.value && !busy.value && operable.value &&
  (model.value === '__custom__' ? !!custom.value.trim() : !offline.value || models.value.some(item => item.id === model.value)));
const transport = codeTransport(props, receive);
let disposed = false;
function receive(packet) {
  if (disposed) return;
  if (packet.type === 'state') {
    const first = !state.会話ID;
    const changed = !!state.会話ID && state.会話ID !== packet.会話ID;
    const previous = state.メッセージ.map(item => `${item.種別}:${item.本文}`);
    if (first || changed) { revision++; arrivals.reset(); }
    const own = revision;
    Object.assign(state, packet, { 自動接続: packet.自動接続 !== false, 画面接続済み: packet.画面接続済み !== false }); pending.value = false; autoPending.value = false; error.value = packet.接続エラー || '';
    if (deleteTarget.value && (packet.実行中 || !state.履歴.some(item => item.id === deleteTarget.value.id))) deleteTarget.value = null;
    if (changed || !packet.実行中 || packet.停止中) stopPending.value = false;
    if (!checksRestored && [0, 1, 2, 3].includes(packet.検証回数)) { checks.value = packet.検証回数; checksRestored = true; }
    if (changed) { prompt.value = ''; progress.value = ''; }
    progress.value = (packet.進捗 || []).map(line => visibleStreamContent(String(line))).filter(Boolean).join('\n');
    const messages = packet.メッセージ || [];
    void nextTick(() => {
      if (disposed || own !== revision) return;
      stream.value?.sync(progress.value, first || changed);
      if (!first && !changed) {
        messages.forEach((item, i) => {
          if (previous[i] !== `${item.種別}:${item.本文}` && ['user', 'assistant'].includes(item.種別)) arrivals.show(rows.get(i), item.種別, item.本文, '', i);
        });
      }
      scroll();
    });
  } else if (packet.type === 'showConversation') { history.value = false; nextTick(scroll); }
  else if (packet.type === 'accepted') { prompt.value = ''; pending.value = false; }
  else if (packet.type === 'modelCatalog') {
    if (!picker.value || (packet.provider || '') !== catalogProvider) return;
    const items = (packet.items || []).filter(item => typeof item?.id === 'string' && typeof item.label === 'string');
    if (!packet.provider) {
      providers.value = items;
      provider.value = items.some(item => item.id === state.provider) ? state.provider : offline.value ? items[0]?.id || '' : '';
      void changeProvider();
    } else {
      models.value = items;
      model.value = provider.value === state.provider ? state.model || '' : offline.value ? 'auto' : '';
      if (offline.value && !items.some(item => item.id === model.value)) model.value = items[0]?.id || '';
      custom.value = provider.value === state.provider ? state.model || '' : '';
      catalogBusy.value = false; catalogReady.value = true;
    }
  } else if (['modelCatalogError', 'transportError', 'error'].includes(packet.type)) {
    if (packet.type === 'modelCatalogError' && (!picker.value || (packet.provider || '') !== catalogProvider)) return;
    error.value = packet.message || packet.error || '処理に失敗しました。'; pending.value = false; catalogBusy.value = false;
    stopPending.value = false; autoPending.value = false;
    if (packet.type === 'modelCatalogError') catalogReady.value = false;
    arrivals.cancelReservation();
    if (packet.type === 'transportError') { revision++; state.画面接続済み = false; arrivals.reset(); stream.value?.reset(); }
  } else if (packet.メッセージ識別 === 'output_stream') {
    stream.value?.packet(String(packet.メッセージ内容 || ''));
  }
}
async function send(type, data = {}) {
  error.value = '';
  try { await transport.send({ type, ...data }); return true; }
  catch (e) { error.value = e.message; pending.value = false; catalogBusy.value = false; return false; }
}
async function submit() {
  if (!canSend.value) return;
  pending.value = true;
  arrivals.reserve(input.value, prompt.value, state.メッセージ.length);
  if (!await send('input_text', { メッセージ識別: 'input_text', メッセージ内容: prompt.value, self_check_loop: offline.value ? 0 : Number(checks.value) })) arrivals.cancelReservation();
}
async function stop() {
  if (!canStop.value) return;
  stopPending.value = true;
  if (!await send('cancel_run', { メッセージ識別: 'cancel_run', メッセージ内容: '強制停止！' })) stopPending.value = false;
}
async function openModels() {
  if (busy.value || !operable.value || picker.value) return;
  provider.value = ''; model.value = ''; custom.value = ''; providers.value = []; models.value = [];
  picker.value = true;
  await requestCatalog('');
}
async function requestCatalog(value) {
  catalogProvider = value; catalogBusy.value = true; catalogReady.value = false;
  await send('chooseModel', { provider: value });
}
async function changeProvider() {
  model.value = ''; custom.value = ''; models.value = [];
  if (provider.value) await requestCatalog(provider.value);
  else { catalogProvider = ''; catalogBusy.value = false; catalogReady.value = !offline.value; }
}
async function applyModel() {
  if (!canApplyModel.value) return;
  catalogBusy.value = true;
  if (await send('setModel', { provider: provider.value, model: model.value === '__custom__' ? custom.value.trim() : model.value })) picker.value = false;
  catalogBusy.value = false;
}
async function toggleAuto() { if (busy.value || autoPending.value || !operable.value) return; autoPending.value = true; if (!await send('autoConnect', { enabled: !state.自動接続 })) autoPending.value = false; }
async function deleteHistory() { if (!deleteTarget.value || busy.value || deleting.value || !operable.value) return; deleting.value = true; if (await send('deleteHistory', { id: deleteTarget.value.id })) deleteTarget.value = null; deleting.value = false; }
function historyDate(value) { const date = new Date(value); if (Number.isNaN(date.getTime())) return ''; const pad = n => String(n).padStart(2, '0'); return `${date.getFullYear()}/${pad(date.getMonth() + 1)}/${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`; }
function link(event) { const a = event.target.closest('a'); if (a) { event.preventDefault(); transport.link(a.href); } }
function copyInput(text) { prompt.value = text; nextTick(() => { input.value?.focus(); input.value?.setSelectionRange(text.length, text.length); scroll(); }); }
watch(prompt, text => transport.saveDraft(text));
watch(offline, () => { picker.value = false; });
onMounted(() => { prompt.value = transport.draft(); resizeObserver = new ResizeObserver(scroll); resizeObserver.observe(conversation.value); void transport.start(); });
onBeforeUnmount(() => { disposed = true; revision++; arrivals.dispose(); resizeObserver?.disconnect(); transport.dispose(); });
</script>
<template>
  <section class="ai-component code-component" :class="{ running: busy, 'desktop-window': desktop }" data-component="CodePanel">
    <StatusBar :title="linked ? 'AiDiy IDE / Code' : 'AiDiy Code'" :mode="state.自動接続 ? 'online' : 'offline'" :connected="state.接続済み" :busy="state.接続中" :active="state.実行中" :desktop="desktop" clock-pulse />
    <div class="component-toolbar"><span :title="state.作業フォルダ?.パス">プロジェクト: {{ state.作業フォルダ?.名前 }}</span><nav>
      <button v-if="!embedded" class="auto-connect" role="switch" :aria-checked="state.自動接続" :title="`自動接続 ${state.自動接続 ? 'ON' : 'OFF'}`" :disabled="busy || autoPending || !operable" @click="toggleAuto"><span>自動接続</span><span class="auto-connect-track" aria-hidden="true"><span class="auto-connect-thumb"></span></span></button>
      <button :disabled="busy || autoPending || !operable || (!offline && !state.接続済み) || (!state.作業フォルダ && !state.新規可能)" @click="send('new')">＋ 新規</button><button :aria-expanded="history" @click="arrivals.reset(); history = !history">{{ history ? '戻る' : '一覧' }}</button>
    </nav></div>
    <div v-if="history" class="history-list" role="list">
      <p v-if="!sortedHistory.length" class="history-empty">このフォルダに会話履歴はありません</p>
      <div v-for="item in sortedHistory" :key="item.id" class="history-row" :class="{ active: item.id === state.会話ID }" role="listitem">
        <button class="history-open" :disabled="busy || !operable" :title="item.題名" :aria-label="`会話を開く: ${item.題名}`" @click="send('selectHistory', { id: item.id }); history = false"><span class="history-date">{{ historyDate(item.更新日時) }}</span><span class="history-title">{{ item.題名 }}</span></button>
        <button class="history-delete" :disabled="busy || !operable" @click="deleteTarget = item" :aria-label="`会話を削除: ${item.題名}`">削除</button>
      </div>
    </div>
    <main v-show="!history" ref="conversation" class="conversation" @click="link">
      <TerminalWelcome v-if="!state.メッセージ.length" :key="state.会話ID" :icon="icon" :started="!!prompt" />
      <article v-for="(item, i) in state.メッセージ" :ref="el => el ? rows.set(i, el) : rows.delete(i)" :key="`${state.会話ID}:${i}`" :class="['message', item.種別]">
        <div v-if="item.種別 === 'user'" class="content user-text" title="クリックして入力欄へ戻す" @click="copyInput(item.本文)">{{ item.本文 }}</div>
        <div v-else-if="item.種別 === 'assistant'" class="content" v-html="markdown.render(item.本文 || '')"></div>
        <div v-else class="content">{{ item.本文 }}</div>
      </article>
    </main>
    <TerminalProgress :hidden="history" ref="stream" :running="!!state.実行中" @resize="scroll" />
    <footer v-show="!history" class="composer">
      <div v-if="state.添付" class="attachment">{{ state.添付 }} <button :disabled="busy || !operable" @click="send('removeAttachment')">×</button></div>
      <p v-if="!state.信頼済み && host" class="error">VS Codeでワークスペースを信頼してください。</p><p v-if="error" role="alert" class="error">{{ error }}</p>
      <form :class="{ running: state.実行中 }" @submit.prevent="submit"><div class="prompt-frame"><textarea ref="input" v-model="prompt" rows="3" maxlength="200000" placeholder="AiDiyに依頼する…" aria-label="Codeへの依頼" @keydown.tab="event => { if (!event.shiftKey && !event.altKey && !event.ctrlKey && !event.metaKey && !event.isComposing && canSend) { event.preventDefault(); sendButton.focus(); } }"></textarea></div>
        <div class="composer-actions"><div class="keyboard-hint">Enter で改行 · Tab → Enter で送信</div><div class="composer-meta"><button type="button" :disabled="busy || autoPending || !operable || (!offline && !state.作業フォルダ)" @click="openModels"><span class="model-caption">モデル</span> <span class="model-chevron">▾</span></button><span class="model-label" :title="modelLabel">{{ modelLabel }}</span></div>
          <div class="verification-options"><label>検証</label><select :value="offline ? 0 : checks" :disabled="offline" aria-label="検証回数" @change="checks = Number($event.target.value); checksRestored = true; send('setSelfCheckLoop', { count: checks })"><option v-for="n in [0,1,2,3]" :key="n" :value="n">{{ n }}回</option></select><span class="verification-hint">0回:バックアップ・検証無</span></div>
          <button v-if="state.実行中" type="button" class="stop" :disabled="!canStop" aria-label="実行を停止" title="実行を停止" @click="stop"><img class="stop-icon" :src="stopIcon" alt=""><span class="stop-label" aria-hidden="true">STOP</span></button>
          <button v-else ref="sendButton" type="submit" class="send" :class="{ 'ws-disabled': !allowed }" :disabled="!canSend" aria-label="送信"><img :src="sendIcon" alt=""></button>
        </div>
      </form>
    </footer>
    <ModalDialog v-if="picker" label="モデル選択" @close="picker = false"><h3>コードAIとモデル</h3>
      <p>{{ offline ? 'aidiy_hermes を直接実行します。オンラインとは別のモデルを保存します。' : 'AIコアのコードAIを選択します。' }}</p>
      <label>コードAI<select v-model="provider" :disabled="catalogBusy || offline" @change="changeProvider"><option v-if="!offline" value="">自動（AIコアの設定）</option><option v-for="p in providers" :key="p.id" :value="p.id">{{ p.label || p.id }}</option></select></label>
      <label>モデル<select v-model="model" :disabled="catalogBusy || !provider || !catalogReady"><option v-if="!offline" value="">{{ provider ? '既定モデル（プロバイダの設定）' : 'AIコアの設定を使用' }}</option><option v-for="m in models" :key="m.id" :value="m.id">{{ m.label || m.id }}</option><option v-if="!offline && provider === state.provider && state.model && !models.some(m => m.id === state.model)" :value="state.model">{{ state.model }}（現在のモデル）</option><option v-if="!offline && provider" value="__custom__">一覧にないモデル ID を入力…</option></select></label>
      <input v-if="model === '__custom__'" v-model="custom" maxlength="300" autocomplete="off" spellcheck="false" aria-label="モデル名"><p v-if="catalogBusy">読み込み中…</p><p v-if="error" class="error">{{ error }}</p>
      <button :disabled="!canApplyModel" @click="applyModel">選択する</button><button @click="picker = false">閉じる</button>
    </ModalDialog>
    <ModalDialog v-if="deleteTarget" label="会話の削除" :locked="deleting" @close="deleteTarget = null"><h3>この会話を削除しますか？</h3><p>{{ deleteTarget.題名 }}</p><p>削除した会話は元に戻せません。</p><p v-if="error" class="error">{{ error }}</p><button :disabled="busy || deleting || !operable" @click="deleteHistory">削除する</button><button :disabled="deleting" @click="deleteTarget = null">キャンセル</button></ModalDialog>
  </section>
</template>
