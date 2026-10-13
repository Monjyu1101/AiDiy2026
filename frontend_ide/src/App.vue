<!-- COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
Licensed under "AiDiy 公開利用ライセンス v1.1".
Commercial use requires prior written consent from all copyright holders.
See LICENSE for full terms. Thank you for keeping the rules.
https://github.com/monjyu1101/AiDiy2026 -->
<script setup>
import { ref, reactive, provide, nextTick, onMounted, onBeforeUnmount } from 'vue';
import CodePanel from './components/CodePanel.vue';
import TermPanel from './components/TermPanel.vue';
import LivePanel from './components/LivePanel.vue';
import SpaceView from './components/SpaceView.vue';
import StatusBar from './components/StatusBar.vue';
import TerminalWelcome from './components/TerminalWelcome.vue';
import ViewerWindow from './components/ViewerWindow.vue';
import FileAnalysisDialog from './components/FileAnalysisDialog.vue';
import FileHistoryDialog from './components/FileHistoryDialog.vue';
import DraftHandoffDialog from './components/DraftHandoffDialog.vue';
import { validConnectionState } from './connection-state.js';
import { createDraftTargetRegistry } from './draft-target-registry.js';
const analysis=ref(null);
const history=ref(null),draftRequest=ref(null),codePanel=ref(),livePanel=ref();
const draftRegistry=createDraftTargetRegistry(),pinnedViewers=new Map();
provide('openFileDraft',request=>{draftRequest.value=request;});
provide('registerPinnedViewer',opened=>{if(opened&&state.value.active)pinnedViewers.set(opened,{sessionKey:session,projectPath:state.value.project?.path});});
provide('openFileHistory',(file,root)=>{history.value={file:{path:file.path,name:file.name},root};});
// ビューアの3分消去やファイル切替から独立して、解析対象を保持する。
provide('openFileAnalysis',(file,root)=>{analysis.value={file:{path:file.path,name:file.name},root};});
const { config }=defineProps({config:Object});
// IDEのピン留めで開いた独立ウィンドウ（URLの #viewer=ファイル）。IDE本体の画面・接続監視は動かさない。
const viewerPath=config.kind==='ide'&&location.hash.startsWith('#viewer=')?decodeURIComponent(location.hash.slice('#viewer='.length)):'';
const state=ref({active:false}),base=reactive({term:'',code:config.kind==='code'?(config.host?'host':config.base||''):'',live:config.kind==='live'?(config.host?'host':config.base||''):''});
const statusError=ref('');
const error=ref(''),pending=ref(false),panelOpen=ref(false),tab=ref('code'),liveOpen=ref(false),viewMode=ref('3d');
const desktop=!!window.aidiyWindow;let timer,disposed=false,revision=0,polling=false,session='';
const lifetime=new AbortController();
async function status(){
  if(polling||pending.value||disposed)return;polling=true;const run=revision,own=session;
  try{
    const r=await fetch('/api/connection',{cache:'no-store',signal:AbortSignal.any([lifetime.signal,AbortSignal.timeout(5000)])});
    if(!r.ok)throw Error();const data=await r.json();
    // 一時的なHTTP失敗・壊れた応答は利用終了の証拠ではない。子パネルやPTYを破棄しない。
    if(!validConnectionState(data))throw Error();
    if(disposed||run!==revision||own!==session)return;statusError.value='';update(data);const confirmed=session;
    if(desktop){
      try{const children=await window.aidiyWindow.childWindows();if(!disposed&&run===revision&&session===confirmed)liveOpen.value=!!children?.live;}
      catch{if(!disposed&&run===revision&&session===confirmed)statusError.value='子ウィンドウの状態を確認できません。次の確認で再試行します。';}
    }
  }catch{if(!disposed&&run===revision&&session===own)statusError.value='サーバーの状態を確認できません。作業を保持して再試行します。';}
  finally{polling=false;}
}
function update(data){
  if(disposed)return;
  const next=data.active?`${data.mode}:${data.startedAt}:${data.project?.path||''}`:'';
  if(next!==session){analysis.value=null;history.value=null;draftRequest.value=null;pinnedViewers.clear();for(const key of Object.keys(opening))delete opening[key];session=next;base.code='';base.live='';base.term='';panelOpen.value=false;tab.value='code';liveOpen.value=false;viewMode.value='3d';}
  state.value=data;error.value=data.message||'';
}
async function start(action){
  if(pending.value)return;pending.value=true;revision++;error.value='';statusError.value='';
  if(action==='disconnect')update({active:false});
  try{if(action==='disconnect'&&desktop)await window.aidiyWindow.endSession();const response=await fetch('/api/connection/'+action,{method:'POST',signal:AbortSignal.timeout(7000)});if(!response.ok)throw Error(await response.text());update(await response.json());}
  catch(e){error.value=e.message;}finally{pending.value=false;}
}
const launching=ref('');
async function openWindow(kind){
  if(launching.value)return;launching.value=kind;error.value='';
  try{const result=await window.aidiyWindow.openApp(kind);if(!result?.ok)throw Error(result?.error||'画面を開けません。');if(kind==='live')liveOpen.value=true;return result;}
  catch(e){error.value=e.message;return{ok:false,error:e.message};}finally{launching.value='';}
}
const opening={};
async function openPanel(kind){
  if(config.kind==='ide'&&!state.value.active)return;
  if(kind==='live'&&config.kind==='ide'&&state.value.mode!=='online')return;
  tab.value=kind;panelOpen.value=true;
  if(base[kind])return;
  const own=session;
  try{
    const request=opening[kind]??=fetch('/api/panels/'+kind,{method:'POST'}).then(async response=>{if(!response.ok)throw Error(await response.text());return response.json();});
    const result=await request;if(!disposed&&own===session)base[kind]=result.url;
  }catch(e){if(!disposed&&own===session)error.value=e.message;}finally{if(own===session)delete opening[kind];}
}
const panels=()=>[codePanel.value,livePanel.value].filter(Boolean);
async function confirmDraftSession(request,expected){
  const run=revision,own=session;
  const response=await fetch('/api/connection',{cache:'no-store',signal:AbortSignal.any([lifetime.signal,AbortSignal.timeout(5000)])});
  if(!response.ok)throw Error('IDEの利用状態を確認できません。接続を確認して再試行してください。');
  const current=await response.json();
  if(!validConnectionState(current))throw Error('IDEの利用状態を確認できません。');
  if(disposed||run!==revision||own!==session)throw Error('IDEの利用状態が変わりました。連携先を選び直してください。');
  update(current);
  if(!current.active||current.project?.path!==request.projectPath||expected&&expected!==session)throw Error('IDEの利用状態が変わりました。連携先を選び直してください。');
  return{sessionKey:session,projectPath:current.project.path,mode:current.mode};
}
function parentDraftAPI(){
  try{const parent=window.opener;if(parent&&!parent.closed&&parent.location.origin===location.origin&&parent.aidiyDraftLink)return parent.aidiyDraftLink;}catch{}
  throw Error('起動元のIDEへ接続できません。IDEからこのファイルを開き直してください。');
}
function verifyPinned(sender,request){
  const linked=pinnedViewers.get(sender);
  if(!linked||sender.closed||linked.sessionKey!==session||linked.projectPath!==request.projectPath)throw Error('ピン留め元のIDEの利用が終了しました。IDEから開き直してください。');
  return linked;
}
async function loadDraftTargets(request){
  if(desktop){const result=await window.aidiyWindow.draftTargets();if(result?.projectPath!==request.projectPath)throw Error('連携先のプロジェクトが一致しません。');return result;}
  if(viewerPath)return parentDraftAPI().list(window,request);
  const current=await confirmDraftSession(request);await nextTick();
  return{ok:true,...current,targets:draftRegistry.targets(panels(),current.projectPath)};
}
async function insertFileDraft(request,sourceGuard=()=>{}){
  if(desktop)return window.aidiyWindow.insertDraft(request);
  if(viewerPath)return parentDraftAPI().insert(window,request);
  const current=await confirmDraftSession(request,request.sessionKey);
  sourceGuard();
  const result=draftRegistry.insert(panels(),current,request);
  if(result.ok){const chosen=draftRegistry.targets(panels(),current.projectPath).find(item=>item.id===request.targetId);tab.value=chosen.kind;panelOpen.value=true;}
  return result;
}
async function launchDraftTarget(kind,request){
  if(desktop)return openWindow(kind);
  if(viewerPath)return parentDraftAPI().launch(window,kind,request);
  await confirmDraftSession(request,request.sessionKey);
  if(kind==='live'&&state.value.mode!=='online')throw Error('LiveはAiDiy接続利用で起動してください。');
  await openPanel(kind);await nextTick();
  return base[kind]?{ok:true}:{ok:false,error:error.value||'画面を開けません。'};
}
const draftLink={
  async list(sender,request){const linked=verifyPinned(sender,request);const current=await confirmDraftSession(request,linked.sessionKey);verifyPinned(sender,request);return{ok:true,...current,targets:draftRegistry.targets(panels(),current.projectPath)};},
  async insert(sender,request){verifyPinned(sender,request);return insertFileDraft(request,()=>verifyPinned(sender,request));},
  async launch(sender,kind,request){const linked=verifyPinned(sender,request);await confirmDraftSession(request,linked.sessionKey);verifyPinned(sender,request);return launchDraftTarget(kind,{...request,sessionKey:linked.sessionKey});},
};
onMounted(async()=>{
  if(config.kind==='ide'&&!desktop&&!viewerPath)window.aidiyDraftLink=draftLink;
  if(config.host||viewerPath)return;
  if(config.kind==='ide'){await status();if(!disposed)timer=setInterval(status,10000);}
  else if(!base[config.kind])await openPanel(config.kind);
});
onBeforeUnmount(()=>{disposed=true;revision++;lifetime.abort();clearInterval(timer);pinnedViewers.clear();if(window.aidiyDraftLink===draftLink)delete window.aidiyDraftLink;});
</script>
<template>
  <DraftHandoffDialog v-if="draftRequest" :request="draftRequest" :load-targets="loadDraftTargets" :insert-draft="insertFileDraft" :launch-target="launchDraftTarget" @close="draftRequest=null" />
  <FileAnalysisDialog v-if="analysis" :key="analysis.root+'|'+analysis.file.path" :file="analysis.file" :root="analysis.root" @close="analysis=null" />
  <FileHistoryDialog v-if="history" :key="history.root+'|'+history.file.path" :file="history.file" :root="history.root" @close="history=null" />
  <ViewerWindow v-if="viewerPath" :path="viewerPath" :desktop="desktop" />
  <div v-else class="development-app" :class="[config.kind,{'vscode-host':config.host,'desktop-window':desktop}]" :data-app="config.kind">
    <template v-if="config.kind==='ide'">
      <div class="ide-heading"><StatusBar title="AiDiy IDE" :connected="state.connected" :mode="state.mode" :busy="state.connecting||pending" :desktop="desktop" clock-pulse />
        <div class="component-toolbar">
          <div class="ide-project-actions">
            <span class="ide-project-name" :title="state.project?.path">プロジェクト: {{ state.project?.name }}</span>
            <nav v-if="state.active" class="ide-view-modes" aria-label="ファイルの表示モード"><button :aria-pressed="viewMode==='3d'" @click="viewMode='3d'">3D</button><button :aria-pressed="viewMode==='2d'" @click="viewMode='2d'">2D</button></nav>
          </div>
          <div class="ide-toolbar-right">
            <nav v-if="state.active&&desktop" class="ai-launchers" aria-label="別ウィンドウを開く"><button :disabled="!!launching" title="ターミナルを別ウィンドウで開く" @click="openWindow('term')">{{ launching==='term'?'起動中…':'＋ Term' }}</button><button :disabled="!!launching" title="コード支援を別ウィンドウで開く" @click="openWindow('code')">{{ launching==='code'?'起動中…':'＋ Code' }}</button><button v-if="state.mode==='online'&&!liveOpen" :disabled="!!launching" title="音声会話を別ウィンドウで開く" @click="openWindow('live')">{{ launching==='live'?'起動中…':'＋ Live' }}</button></nav>
            <nav v-else-if="state.active" class="ai-launchers" aria-label="パネルを開く"><button :aria-pressed="panelOpen&&tab==='term'" @click="openPanel('term')">Term</button><button :aria-pressed="panelOpen&&tab==='code'" @click="openPanel('code')">Code</button><button v-if="state.mode==='online'" :aria-pressed="panelOpen&&tab==='live'" @click="openPanel('live')">Live</button></nav>
            <nav><template v-if="!state.active"><button :disabled="pending" @click="start('connect')">AiDiy接続利用</button><button :disabled="pending" @click="start('offline')">オフライン利用</button></template><button v-else :disabled="pending" @click="start('disconnect')">{{ desktop?'終了':'利用終了' }}</button></nav>
          </div>
        </div>
      </div>
      <TerminalWelcome v-if="!state.active" kind="ide" :icon="config.icon" />
      <template v-else>
        <SpaceView :key="`${state.mode}:${state.startedAt}:${state.project?.path||''}`" :started-at="state.startedAt" :view-mode="viewMode" />
        <aside v-if="!desktop" v-show="panelOpen" class="ai-popup"><nav class="ai-tabs" role="tablist"><button role="tab" :aria-selected="tab==='term'" @click="openPanel('term')">Term</button><button role="tab" :aria-selected="tab==='code'" @click="openPanel('code')">Code</button><button v-if="state.mode==='online'" role="tab" :aria-selected="tab==='live'" @click="openPanel('live')">Live</button><button class="close" aria-label="パネルを閉じる" @click="panelOpen=false">×</button></nav>
          <CodePanel ref="codePanel" v-if="base.code" v-show="tab==='code'" :key="base.code" :base="base.code" :icon="config.icon" embedded />
          <LivePanel ref="livePanel" v-if="base.live&&state.mode==='online'" v-show="panelOpen&&tab==='live'" :visible="panelOpen&&tab==='live'" :key="base.live" :base="base.live" :icon="config.icon" />
          <TermPanel v-if="base.term" v-show="tab==='term'" :key="base.term" :base="base.term" :icon="config.icon" :visible="panelOpen&&tab==='term'" linked />
          <p v-if="!base[tab]" class="panel-loading">読み込み中…</p>
        </aside>
      </template>
    </template>
    <CodePanel v-else-if="config.kind==='code'&&base.code" :base="config.host?'':base.code" :host="config.host" :embedded="config.linked" :linked="config.linked" :icon="config.icon" :desktop="desktop" />
    <LivePanel v-else-if="config.kind==='live'&&base.live" :base="config.host?'':base.live" :config="config.live||{}" :linked="config.linked" :icon="config.icon" :desktop="desktop" />
    <TermPanel v-else-if="config.kind==='term'&&base.term" :base="base.term" :icon="config.icon" :desktop="desktop" :linked="config.linked" />
    <p v-else class="panel-loading">読み込み中…</p>
    <p v-if="error||statusError" class="app-error" role="alert">{{ error||statusError }}</p>
  </div>
</template>
