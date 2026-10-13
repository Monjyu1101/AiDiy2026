<!-- COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
Licensed under "AiDiy 公開利用ライセンス v1.1".
Commercial use requires prior written consent from all copyright holders.
See LICENSE for full terms. Thank you for keeping the rules.
https://github.com/monjyu1101/AiDiy2026 -->
<script setup>
import { ref, reactive, provide, onMounted, onBeforeUnmount } from 'vue';
import CodePanel from './components/CodePanel.vue';
import TermPanel from './components/TermPanel.vue';
import LivePanel from './components/LivePanel.vue';
import SpaceView from './components/SpaceView.vue';
import StatusBar from './components/StatusBar.vue';
import TerminalWelcome from './components/TerminalWelcome.vue';
import ViewerWindow from './components/ViewerWindow.vue';
import FileAnalysisDialog from './components/FileAnalysisDialog.vue';
import FileHistoryDialog from './components/FileHistoryDialog.vue';
const analysis=ref(null);
const history=ref(null);
provide('openFileHistory',(file,root)=>{history.value={file:{path:file.path,name:file.name},root};});
// ビューアの3分消去やファイル切替から独立して、解析対象を保持する。
provide('openFileAnalysis',(file,root)=>{analysis.value={file:{path:file.path,name:file.name},root};});
const { config }=defineProps({config:Object});
// IDEのピン留めで開いた独立ウィンドウ（URLの #viewer=ファイル）。IDE本体の画面・接続監視は動かさない。
const viewerPath=config.kind==='ide'&&location.hash.startsWith('#viewer=')?decodeURIComponent(location.hash.slice('#viewer='.length)):'';
const state=ref({active:false}),base=reactive({term:'',code:config.kind==='code'?(config.host?'host':config.base||''):'',live:config.kind==='live'?(config.host?'host':config.base||''):''});
const error=ref(''),pending=ref(false),panelOpen=ref(false),tab=ref('code'),liveOpen=ref(false);
const desktop=!!window.aidiyWindow;let timer,disposed=false,revision=0,polling=false,session='';
async function status(){
  if(polling||pending.value||disposed)return;polling=true;const run=revision;
  try{const r=await fetch('/api/connection',{cache:'no-store',signal:AbortSignal.timeout(5000)});if(!r.ok)throw Error();const data=await r.json();const children=desktop?await window.aidiyWindow.childWindows():null;if(run===revision){update(data);if(children)liveOpen.value=children.live;}}
  catch{if(run===revision)update({active:false,message:'サーバーに接続できません。'});}finally{polling=false;}
}
function update(data){
  if(disposed)return;
  const next=data.active?`${data.mode}:${data.startedAt}`:'';
  if(next!==session){analysis.value=null;history.value=null;for(const key of Object.keys(opening))delete opening[key];session=next;base.code='';base.live='';base.term='';panelOpen.value=false;tab.value='code';liveOpen.value=false;}
  state.value=data;error.value=data.message||'';
}
async function start(action){
  if(pending.value)return;pending.value=true;revision++;error.value='';
  if(action==='disconnect')update({active:false});
  try{if(action==='disconnect'&&desktop)await window.aidiyWindow.endSession();const response=await fetch('/api/connection/'+action,{method:'POST',signal:AbortSignal.timeout(7000)});if(!response.ok)throw Error(await response.text());update(await response.json());}
  catch(e){error.value=e.message;}finally{pending.value=false;}
}
const launching=ref('');
async function openWindow(kind){
  if(launching.value)return;launching.value=kind;error.value='';
  try{const result=await window.aidiyWindow.openApp(kind);if(!result?.ok)throw Error(result?.error||'画面を開けません。');if(kind==='live')liveOpen.value=true;}
  catch(e){error.value=e.message;}finally{launching.value='';}
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
  }catch(e){error.value=e.message;}finally{if(own===session)delete opening[kind];}
}
onMounted(async()=>{
  if(config.host||viewerPath)return;
  if(config.kind==='ide'){await status();timer=setInterval(status,5000);}
  else if(!base[config.kind])await openPanel(config.kind);
});
onBeforeUnmount(()=>{disposed=true;revision++;clearInterval(timer);});
</script>
<template>
  <FileAnalysisDialog v-if="analysis" :key="analysis.root+'|'+analysis.file.path" :file="analysis.file" :root="analysis.root" @close="analysis=null" />
  <FileHistoryDialog v-if="history" :key="history.root+'|'+history.file.path" :file="history.file" :root="history.root" @close="history=null" />
  <ViewerWindow v-if="viewerPath" :path="viewerPath" :desktop="desktop" />
  <div v-else class="development-app" :class="[config.kind,{'vscode-host':config.host,'desktop-window':desktop}]" :data-app="config.kind">
    <template v-if="config.kind==='ide'">
      <div class="ide-heading"><StatusBar title="AiDiy IDE" :connected="state.connected" :mode="state.mode" :busy="state.connecting||pending" :desktop="desktop" clock-pulse />
        <div class="component-toolbar">
          <div class="ide-project-actions">
            <span class="ide-project-name" :title="state.project?.path">プロジェクト: {{ state.project?.name }}</span>
            <nav v-if="state.active&&desktop" class="ai-launchers" aria-label="別ウィンドウを開く"><button :disabled="!!launching" title="ターミナルを別ウィンドウで開く" @click="openWindow('term')">{{ launching==='term'?'起動中…':'＋ Term' }}</button><button :disabled="!!launching" title="コード支援を別ウィンドウで開く" @click="openWindow('code')">{{ launching==='code'?'起動中…':'＋ Code' }}</button><button v-if="state.mode==='online'&&!liveOpen" :disabled="!!launching" title="音声会話を別ウィンドウで開く" @click="openWindow('live')">{{ launching==='live'?'起動中…':'＋ Live' }}</button></nav>
            <button v-else-if="state.active" class="ai-panel-toggle" :aria-expanded="panelOpen" @click="panelOpen ? panelOpen=false : openPanel(tab)">☰ {{ state.mode==='offline'?'Term / Code':'Term / Code / Live' }}</button>
          </div>
          <nav><template v-if="!state.active"><button :disabled="pending" @click="start('connect')">AiDiy接続利用</button><button :disabled="pending" @click="start('offline')">オフライン利用</button></template><button v-else :disabled="pending" @click="start('disconnect')">{{ desktop?'終了':'利用終了' }}</button></nav>
        </div>
      </div>
      <TerminalWelcome v-if="!state.active" kind="ide" :icon="config.icon" />
      <template v-else>
        <SpaceView :key="state.startedAt" :started-at="state.startedAt" />
        <aside v-if="!desktop" v-show="panelOpen" class="ai-popup"><nav class="ai-tabs" role="tablist"><button role="tab" :aria-selected="tab==='term'" @click="openPanel('term')">Term</button><button role="tab" :aria-selected="tab==='code'" @click="openPanel('code')">Code</button><button v-if="state.mode==='online'" role="tab" :aria-selected="tab==='live'" @click="openPanel('live')">Live</button><button class="close" aria-label="パネルを閉じる" @click="panelOpen=false">×</button></nav>
          <CodePanel v-if="base.code" v-show="tab==='code'" :key="base.code" :base="base.code" :icon="config.icon" embedded />
          <LivePanel v-if="base.live&&panelOpen&&tab==='live'&&state.mode==='online'" :key="base.live" :base="base.live" :icon="config.icon" />
          <TermPanel v-if="base.term" v-show="tab==='term'" :key="base.term" :base="base.term" :icon="config.icon" :visible="panelOpen&&tab==='term'" linked />
          <p v-if="!base[tab]" class="panel-loading">読み込み中…</p>
        </aside>
      </template>
    </template>
    <CodePanel v-else-if="config.kind==='code'&&base.code" :base="config.host?'':base.code" :host="config.host" :embedded="config.linked" :linked="config.linked" :icon="config.icon" :desktop="desktop" />
    <LivePanel v-else-if="config.kind==='live'&&base.live" :base="config.host?'':base.live" :config="config.live||{}" :linked="config.linked" :icon="config.icon" :desktop="desktop" />
    <TermPanel v-else-if="config.kind==='term'&&base.term" :base="base.term" :icon="config.icon" :desktop="desktop" :linked="config.linked" />
    <p v-else class="panel-loading">読み込み中…</p>
    <p v-if="error" class="app-error" role="alert">{{ error }}</p>
  </div>
</template>
