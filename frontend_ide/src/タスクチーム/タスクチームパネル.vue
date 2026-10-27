<!-- COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
Licensed under "AiDiy 公開利用ライセンス v1.1". See LICENSE for full terms. -->
<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue';
import StatusBar from '../共通表示/状態バー.vue';
import TaskPanel from './components/AIタスク/AIタスク.vue';
import TeamPanel from './components/AIチーム/AIチーム.vue';
import TaskRequest from './components/AIタスク/windows/AIタスク_要求ウィンドウ.vue';
import TaskFlow from './components/AIタスク/windows/AIタスク_フローウィンドウ.vue';
import TaskDetail from './components/AIタスク/windows/AIタスク_明細ウィンドウ.vue';
import TaskEditor from './components/AIタスク/windows/AIタスク_編集ウィンドウ.vue';
import { resolveTaskView, createTaskSession, createTaskSelectionCache } from './task-session';
import apiClient, { token } from './api/client';
const props = defineProps<{ config: { kind: 'task' | 'team'; taskTeamBase: string; project?: string } }>();
const desktop = !!window.aidiyWindow;
const taskView = resolveTaskView(props.config.kind, window.location.hash, window.aidiyWindow);
const suffix = ({ request: '要求', flow: 'フロー図', detail: '明細', dialog: '編集' } as Record<string, string>)[taskView] || '';
const title = props.config.kind === 'task' ? `AiDiy Task${suffix ? ' / ' + suffix : ''}` : 'AiDiy Team';
const connected = ref(false), port = ref(8093), checking = ref(true);
const user = ref<Record<string, string> | null>(null), userId = ref(''), password = ref('');
const error = ref(''), busy = ref(false), restoring = ref(taskView !== 'combined' || !!token());
let disposed = false, revision = 0, timer: ReturnType<typeof setTimeout>;
const lifetime = new AbortController();
let sessionSync: ReturnType<typeof createTaskSession> | null = null;
let selectionCache: ReturnType<typeof createTaskSelectionCache> | null = null;
const openViews = ref<string[]>(taskView === 'combined' || taskView === 'dialog' ? [] : [taskView]);
let windowTimer: ReturnType<typeof setTimeout>;
let windowsPolling = false;
async function refreshTaskWindows() {
  if (disposed || windowsPolling) return; windowsPolling = true;
  try { const state = await window.aidiyWindow?.taskWindows('state'); if (!disposed) openViews.value = state?.views || []; } catch {}
  finally { windowsPolling = false; if (!disposed) { clearTimeout(windowTimer); windowTimer = setTimeout(refreshTaskWindows, 2000); } }
}
async function openTaskWindows(view: string) {
  if (!['request', 'flow', 'detail'].includes(view)) return;
  error.value = '';
  try {
    const result = await window.aidiyWindow?.taskWindows('open', { view });
    if (result?.ok === false) throw Error(result.error || 'タスクウィンドウを開けません。');
    clearTimeout(windowTimer); await refreshTaskWindows();
  } catch (cause) { if (!disposed) error.value = cause instanceof Error ? cause.message : 'タスクウィンドウを開けません。'; }
}
function clearSession(message = '') { selectionCache?.dispose(); selectionCache = null; revision++; token(''); user.value = null; password.value = ''; error.value = message; busy.value = false; restoring.value = false; }
async function receiveSession(value: string) {
  if (disposed) return;
  clearSession();
  if (!value) return;
  const run = ++revision; token(value); restoring.value = true;
  try {
    await currentUser(run);
    if (!disposed && run === revision && user.value) selectionCache = createTaskSelectionCache();
  } catch { if (!disposed && run === revision) clearSession('認証を確認できませんでした。再ログインしてください。'); }
  finally { if (!disposed && run === revision) restoring.value = false; }
}

async function health() {
  try {
    const response = await fetch(props.config.taskTeamBase + '/status', { cache: 'no-store', signal: AbortSignal.any([lifetime.signal, AbortSignal.timeout(5000)]) });
    if (!response.ok) throw Error();
    const result = await response.json();
    if (!disposed) { connected.value = result.connected === true; if (Number.isInteger(result.port)) port.value = result.port; }
  } catch { if (!disposed) connected.value = false; }
  finally { if (!disposed) { checking.value = false; timer = setTimeout(health, 5000); } }
}
function logout(message = '') {
  clearSession(message);
  if (sessionSync) void sessionSync.set('').catch(() => { if (!disposed) error.value = '他のタスク画面へのログアウト通知に失敗しました。'; });
}
function expired() { logout('認証の有効期限が切れました。再ログインしてください。'); }
async function currentUser(run: number) {
  const response = await apiClient.post('/core/auth/現在利用者', {});
  if (response.data.status !== 'OK' || !response.data.data?.利用者ID) throw Error(response.data.message || '利用者情報を取得できませんでした。');
  if (!disposed && run === revision) user.value = response.data.data;
}
async function login() {
  if (busy.value) return;
  busy.value = true; error.value = ''; const run = ++revision;
  try {
    const response = await apiClient.post('/core/auth/ログイン', { 利用者ID: userId.value, パスワード: password.value });
    if (disposed || run !== revision) return;
    if (response.data.status !== 'OK' || !response.data.data?.access_token) throw Error(response.data.message || 'ログインに失敗しました。');
    token(response.data.data.access_token); password.value = '';
    if (sessionSync) await sessionSync.set(token()); else await currentUser(run);
  } catch (cause) { if (!disposed && run === revision) logout(cause instanceof Error ? cause.message : 'ログインできませんでした。'); }
  finally { if (!disposed && run === revision) busy.value = false; }
}
onMounted(async () => {
  window.addEventListener('taskteam-auth-expired', expired); void health();
  if (taskView !== 'combined') {
    token('');
    sessionSync = createTaskSession({ api: window.aidiyWindow, applyToken: receiveSession });
    if (taskView !== 'dialog') void refreshTaskWindows();
    try { await sessionSync.start(); }
    catch { if (!disposed) clearSession('認証状態を取得できません。画面を開き直してください。'); }
    return;
  }

  if (!token()) return;
  const run = revision;
  try { await currentUser(run); }
  catch { if (!disposed && run === revision) logout('認証を確認できませんでした。再ログインしてください。'); }
  finally { if (!disposed) restoring.value = false; }
});
onBeforeUnmount(() => { disposed = true; revision++; clearTimeout(timer); clearTimeout(windowTimer); selectionCache?.dispose(); sessionSync?.dispose(); lifetime.abort(); window.removeEventListener('taskteam-auth-expired', expired); });
</script>
<template>
  <main class="taskteam-shell" :data-app="config.kind">
    <StatusBar :title="title" :connected="connected" :busy="checking" :desktop="desktop" :clock-pulse="true" :status="`Task / Team :${port} ${connected ? '接続済み' : '未接続'}`" />
    <div class="component-toolbar"><span>{{ user ? `${user.利用者名 || user.利用者ID} (${user.利用者ID})` : '利用者認証' }}</span><nav><template v-if="taskView !== 'combined' && taskView !== 'dialog'"><button v-for="view in (['request','flow','detail'] as const).filter(view => view !== taskView && !openViews.includes(view))" :key="view" @click="openTaskWindows(view)">{{ {request:'要求',flow:'フロー図',detail:'明細'}[view] }}</button></template><button v-if="user" @click="logout()">ログアウト</button></nav></div>
    <p v-if="restoring" class="taskteam-message" role="status">認証を確認しています…</p>
    <form v-else-if="!user" class="taskteam-login" @submit.prevent="login">
      <h2>{{ title }}</h2>
      <label>利用者ID<input v-model="userId" autocomplete="username" required :disabled="busy" /></label>
      <label>パスワード<input v-model="password" type="password" autocomplete="current-password" required :disabled="busy" /></label>
      <p v-if="error" class="error" role="alert">{{ error }}</p>
      <button type="submit" :disabled="busy">{{ busy ? 'ログイン中…' : 'ログイン' }}</button>
      <p>Core と Task / Team サーバーを起動してください。</p>
    </form>
    <section v-else class="taskteam-content">
      <p v-if="error" class="error" role="alert">{{ error }}</p>
      <TaskRequest v-if="taskView === 'request'" :key="user.利用者ID" :利用者ID="user.利用者ID" :権限ID="user.権限ID || ''" />
      <TaskFlow v-else-if="taskView === 'flow'" :key="user.利用者ID" />
      <TaskDetail v-else-if="taskView === 'detail'" :key="user.利用者ID" />
      <TaskEditor v-else-if="taskView === 'dialog'" :key="user.利用者ID" :利用者ID="user.利用者ID" />
      <TaskPanel v-else-if="config.kind === 'task'" :利用者ID="user.利用者ID" :権限ID="user.権限ID || ''" />
      <TeamPanel v-else :利用者ID="user.利用者ID" :利用者名="user.利用者名 || user.利用者ID" />
    </section>
  </main>
</template>
<style scoped>
.taskteam-shell{width:100%;height:100%;box-sizing:border-box;border:1px solid #383838;background:#000;display:flex;flex-direction:column;overflow:hidden;color:#d9e0f2}
.taskteam-content{flex:1;min-height:0;overflow:auto;position:relative}
.taskteam-login{width:min(360px,calc(100% - 32px));margin:auto;display:grid;gap:14px;background:#080a10;border:1px solid #343943;padding:24px}
.taskteam-login h2{margin:0;font-size:16px;text-align:center}.taskteam-login label{display:grid;gap:6px}.taskteam-login p{margin:0;font-size:11px;color:#9aa7b8}.taskteam-login .error{color:#ffb7b7}.taskteam-message{padding:12px}
/* コピー元の機能は維持し、外側の操作面は Code と同じ黒・細枠へ揃える。 */
.taskteam-content :deep(.ai-task-view){background:#000}.taskteam-content :deep(.task-grid){gap:4px;padding:4px}.taskteam-content :deep(.task-panel){border:1px solid #343943;background:#080a10;border-radius:0;box-shadow:none}.taskteam-content :deep(.task-panel:hover){border-color:#56606e;box-shadow:none}
.taskteam-shell .taskteam-content :deep(.panel-header){background:#080a10;border-bottom:1px solid #242424;box-shadow:none}
.taskteam-shell .taskteam-content :deep(.panel-title){color:#d9e0f2;font-size:12px;letter-spacing:normal;font-weight:600}
.taskteam-shell .taskteam-content :deep(.scope-toggle){background:#080a10;border:1px solid #343943;border-radius:0;color:#d9e0f2}
.taskteam-shell .taskteam-content :deep(.scope-toggle:hover:not(:disabled)){background:#202737}
.taskteam-shell .taskteam-content :deep(.team-page){background:#000}
.taskteam-shell .taskteam-content :deep(.agent-panel),.taskteam-shell .taskteam-content :deep(.exp-panel),.taskteam-shell .taskteam-content :deep(.pdca-panel),.taskteam-shell .taskteam-content :deep(.talk-panel){background:#080a10;border:1px solid #343943;border-radius:0;box-shadow:none}
.taskteam-shell .taskteam-content :deep(.agent-panel:hover),.taskteam-shell .taskteam-content :deep(.exp-panel:hover),.taskteam-shell .taskteam-content :deep(.pdca-panel:hover),.taskteam-shell .taskteam-content :deep(.talk-panel:hover){border-color:#56606e;box-shadow:none}
</style>
