<!-- COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
Licensed under "AiDiy 公開利用ライセンス v1.1".
Commercial use requires prior written consent from all copyright holders.
See LICENSE for full terms. Thank you for keeping the rules.
https://github.com/monjyu1101/AiDiy2026 -->
<script setup>
import { ref, shallowRef, computed, onMounted, onBeforeUnmount, watch, nextTick, inject } from 'vue';
import { panelRect, popupFeatures } from '../ファイル閲覧/パネル別窓.js';
import { createFolderMonitor } from '../ファイル閲覧/フォルダ監視.js';
import { scanWarning } from '../ファイル閲覧/走査警告.js';
import SpaceCanvas from '../開発スペース/宇宙キャンバス.vue';
import FolderPages from '../ファイル閲覧/フォルダページ.vue';
import FileExplorer from '../ファイル閲覧/ファイル一覧.vue';
import FileViewer from '../ファイル閲覧/ファイルビューア.vue';
const props=defineProps({startedAt:Number,viewMode:{type:String,default:'3d'}});
const pagesReady=ref(props.viewMode==='2d');
watch(()=>props.viewMode,mode=>{if(mode==='2d')pagesReady.value=true;});
const scan=shallowRef(),selected=shallowRef(),trail=ref([]),focus=shallowRef();
const unlistedParent=computed(()=>{const file=selected.value,parent=file?.path.split('/').slice(0,-1).join('/');return file?.unlisted&&parent!==trail.value.join('/')?parent:undefined;});
const explorer=ref(),explorerDetached=ref(false);
function toggleExplorer(){if(!explorer.value?.focusDetached())open.value=!open.value;}
const open=ref(false),loading=ref(true),error=ref(''),root=ref(),marks=shallowRef({mode:'since',since:props.startedAt,paths:[]});
const autoSpin=ref(true),driving=ref(false),orbitPhase=ref('idle');
const fastWarp=ref(false);
watch(fastWarp,value=>engine?.setFastWarp(value));
const route=shallowRef({mode:'view',paths:[]});
const viewHistory=shallowRef([]);
const viewVoyages=shallowRef({});
watch(route,value=>engine?.route(value));
// ピン留め: 今のプレビューを閉じ、同じファイルを宇宙パネルの外の独立ウィンドウで開く（複数ファイルを並べて見る）。
// Electron 版は IDE の子ウィンドウ（利用終了・セッション切り替えで一緒に閉じる）、Web 版はブラウザの別ウィンドウ。
const pinError=ref('');
const registerPinnedViewer=inject('registerPinnedViewer',null);
let pinning=false,viewerCloseListener;
const viewerWindows=new Map();
function closeViewerWindows(){for(const entry of viewerWindows.values()){clearInterval(entry.timer);entry.window?.close();}viewerWindows.clear();}
function restoreViewer(file){if(!selected.value)void engine?.goTo(file);}
async function pin(file){
  if(pinning)return;pinning=true;pinError.value='';
  try{
    const rect=panelRect(root.value?.querySelector('.viewer-popup'));
    if(window.aidiyWindow?.openViewer){const result=await window.aidiyWindow.openViewer(file.path,rect);if(!result?.ok)throw Error(result?.error||'ビューアを開けません。');viewerWindows.set(file.path,{file});}
    else {
      let entry=viewerWindows.get(file.path);
      if(entry?.window&&!entry.window.closed)entry.window.focus();
      else {
        const opened=window.open('/#viewer='+encodeURIComponent(file.path),`aidiy-viewer-${file.path}`,popupFeatures(rect));
        if(!opened)throw Error('ポップアップがブロックされました。');
        registerPinnedViewer?.(opened);
        entry={file,window:opened,timer:setInterval(()=>{if(opened.closed){clearInterval(entry.timer);viewerWindows.delete(file.path);restoreViewer(file);}},250)};
        viewerWindows.set(file.path,entry);
      }
    }
    engine.clear();
  }catch(e){pinError.value=e.message;}finally{pinning=false;}
}
// 最終更新ファイルの表示: 起動直後の最終更新と、その後の新しい最終更新を宇宙へ予約する。
// 宇宙は自動探索 ON・オープニング後・追いかけてよい状態になってから、そのファイルまでワープして開く。
function onLatest(file){engine?.requestFollow(file.files.map(item=>item.path));}
function onFreshness(){void engine?.refresh(undefined,{fresh:false});}
// フィルター（左下、既定 ON）: 宇宙とエクスプローラーを AiDiy のバックアップ対象だけにする。
const filter=ref(true);
watch(filter,on=>engine?.setFilter(on));
// ピン留めしていないビューアは最後の操作から5分で閉じ、自動探索が ON なら彗星軌道へ戻る。
// 別ファイルの表示と、ビューア内のスクロール・ボタン操作で期限を数え直す。
const PREVIEW_LIFETIME=300_000;let previewTimer;
function armPreviewTimer(){clearTimeout(previewTimer);if(!selected.value)return;previewTimer=setTimeout(()=>{if(!selected.value||!engine)return;engine.clear();if(autoSpin.value)engine.setAutoSpin(true);},PREVIEW_LIFETIME);}
watch(()=>selected.value?.path,armPreviewTimer);
let engine, folderMonitor;
const monitorMessage = ref('');
function syncFolderMonitor() {
  folderMonitor?.configure({ enabled: props.viewMode === '2d' && autoSpin.value && !!scan.value && !document.hidden,
    path: trail.value.join('/'), filter: filter.value ? 'backup' : '', session: props.startedAt });
}
watch([()=>props.viewMode, autoSpin, filter, ()=>trail.value.join('/'), ()=>props.startedAt, ()=>!!scan.value], syncFolderMonitor);

watch(()=>props.startedAt,value=>{explorerNavigation.value=null;void engine?.refresh(value);});
// 一覧からの移動中は選んだ行を保持し、中間階層を一覧へ送り返さない。
const explorerNavigation=shallowRef(null);
async function selectExplorer(entry){
  explorerNavigation.value=entry;
  try{await engine?.goTo(entry);}
  finally{if(explorerNavigation.value===entry)explorerNavigation.value=null;}
}
function change(value){if('scan'in value){scan.value=value.scan;selected.value=value.selected;trail.value=value.trail;focus.value=value.focus;viewHistory.value=value.journal||[];viewVoyages.value=value.voyages||{};}if('autoSpin'in value)autoSpin.value=value.autoSpin;if('driving'in value)driving.value=value.driving;if('orbitPhase'in value)orbitPhase.value=value.orbitPhase;loading.value=value.loading;if('error'in value)error.value=value.error||'';}
function layout({preview:plannedPreview}={}){
  const element=root.value;
  const preview=plannedPreview??!!element?.querySelector('.viewer-popup');
  const explorer=open.value?element?.querySelector('.explorer-panel')?.getBoundingClientRect():null;
  const list=element?.querySelector('.route-file-list')?.getBoundingClientRect();
  const top=parseFloat(getComputedStyle(element).getPropertyValue('--workspace-top'))||78;
  const bottom=innerHeight-60;
  let left=16,right=innerWidth-16,upper=top,lower=bottom;
  if(innerHeight>=innerWidth){
    if(preview){
      lower=innerHeight/2-8;
      if(explorer)left=explorer.right+8;
      if(list)right=list.left-8;
    }else{
      // ビューア非表示では一覧の開閉によらず画面そのものの中央を使う。
      upper=0;lower=innerHeight;
    }
  }else{
    if(explorer)left=Math.max(left,explorer.right+8);
    if(list)left=Math.max(left,list.right+8);
    if(preview)right=innerWidth*0.67-24;
  }
  const centerX=(left+right)/2,centerY=(upper+lower)/2;
  root.value?.style.setProperty('--focus-x',`${centerX}px`);
  return{centerX,centerY,preview:!!preview};
}
watch(marks,value=>engine?.marks(value));
function documentKey(event){const frame=root.value?.querySelector('.viewer-popup iframe');if(!frame||event.origin!==location.origin||event.source!==frame.contentWindow||event.data?.type!=='aidiy-ide-document-key')return;if(event.data.key==='explorer')toggleExplorer();else if(event.data.key==='close')engine.clear();}
function ready(value){engine=value;engine.marks(marks.value);engine.route(route.value);window.aidiyIDE=engine;void engine.refresh(props.startedAt);}
// 共通ビューアでのEscも2Dのまま使える。本文入力やダイアログのキー操作は奪わない。
function pageKey(event){
  if(props.viewMode!=='2d'||event.defaultPrevented||event.isComposing)return;
  if(event.target?.closest?.('input, textarea, select, [contenteditable="true"], .ai-component, dialog, [role="dialog"]'))return;
  if(event.key==='Escape'){event.preventDefault();if(selected.value)engine?.clear();else if(trail.value.length)void engine?.ascend(trail.value.length-1);}
  else if(event.key==='Backspace'||event.altKey&&event.key==='ArrowLeft'){event.preventDefault();if(trail.value.length)void engine?.ascend(trail.value.length-1);}
}
// 軌跡バーは狭い画面で折り返す。固定高さでページの見出しを隠さないよう、変更時だけ計測する。
let pageLayoutObserver;
function pageLayout(){
  const element=root.value;if(!element)return;
  const top=parseFloat(getComputedStyle(element).getPropertyValue('--workspace-top'))||78;
  const bottom=element.querySelector('.explorer-routes')?.getBoundingClientRect().bottom||top;
  element.style.setProperty('--folder-page-top',`${Math.max(top+48,bottom+8)}px`);
}
onMounted(async()=>{
  window.addEventListener('pagehide',closeViewerWindows);
  viewerCloseListener=window.aidiyWindow?.onViewerClosed?.(path=>{const entry=viewerWindows.get(path);viewerWindows.delete(path);if(entry)restoreViewer(entry.file);});
  folderMonitor = createFolderMonitor({ apply: (context,result) => engine?.applyFolderSnapshot(context,result) ?? false, report: message => { monitorMessage.value=message; } });
  document.addEventListener('visibilitychange',syncFolderMonitor);syncFolderMonitor();
  window.addEventListener('message',documentKey);window.addEventListener('keydown',pageKey);window.addEventListener('resize',pageLayout);
  await nextTick();pageLayout();
  const routes=root.value?.querySelector('.explorer-routes');
  if(routes&&typeof ResizeObserver!=='undefined'){pageLayoutObserver=new ResizeObserver(pageLayout);pageLayoutObserver.observe(routes);}
});
onBeforeUnmount(()=>{viewerCloseListener?.();window.removeEventListener('pagehide',closeViewerWindows);closeViewerWindows();folderMonitor?.close();document.removeEventListener('visibilitychange',syncFolderMonitor);clearTimeout(previewTimer);pageLayoutObserver?.disconnect();if(window.aidiyIDE===engine)delete window.aidiyIDE;window.removeEventListener('message',documentKey);window.removeEventListener('keydown',pageKey);window.removeEventListener('resize',pageLayout);});
</script>
<template>
  <section ref="root" class="space-view" :class="{'explorer-open':open&&!explorerDetached,viewing:!!selected,'mode-2d':viewMode==='2d'}" data-component="SpaceView">
    <SpaceCanvas :mode="viewMode" :layout="layout" @ready="ready" @change="change" @toggle-explorer="toggleExplorer" />
    <FolderPages v-if="scan&&pagesReady" :active="viewMode==='2d'" :tree="scan.tree" :current="trail.join('/')" :selected="selected?.path" :unlisted-parent="unlistedParent" :monitor-message="monitorMessage" :reload="()=>engine?.refresh()" :marks="marks" :color="name=>engine?.color(name)||'#bac7da'" @select="selectExplorer" @activity="engine?.interact()" @clear="engine?.clear()" @refresh="engine?.refresh()" @toggle-explorer="toggleExplorer" />
    <div class="space-flight-controls">
      <button v-show="viewMode==='3d'" class="space-motion-toggle space-fast-warp-toggle" role="switch" aria-label="高速ワープ" :aria-checked="fastWarp" title="別フォルダのファイルを選ぶと、1回のワープで目的フォルダへ移動" @click="fastWarp=!fastWarp"><span>高速ワープ</span><span class="motion-switch" aria-hidden="true"></span><span aria-hidden="true">{{ fastWarp?'ON':'OFF' }}</span></button>
      <div class="space-auto-explore">
        <div v-if="viewMode==='3d'&&autoSpin&&['planning','aligning'].includes(orbitPhase)" class="space-orbit-status" role="status" aria-live="polite">探索軌道計算中<span aria-hidden="true">…</span></div>
        <button class="space-motion-toggle" :class="{driving:autoSpin&&driving}" role="switch" aria-label="自動探索" :aria-checked="autoSpin" :title="viewMode==='2d'?'最終更新のファイルを自動で開く（手動操作中は待機）':autoSpin&&driving?'自動探索中':''" @click="engine?.setAutoSpin(!autoSpin)"><span>自動探索</span><span class="motion-switch" aria-hidden="true"></span><span aria-hidden="true">{{ autoSpin?'ON':'OFF' }}</span></button>
      </div>
    </div>
    <FileExplorer ref="explorer" @detached="value=>explorerDetached=value" v-model:open="open" :view-history="viewHistory" :view-voyages="viewVoyages" :tree="scan?.tree" :scan="scan" :root="scan?.root" :selected="explorerNavigation ? (explorerNavigation.type==='file' ? explorerNavigation.path : undefined) : selected?.path" :current="explorerNavigation ? (explorerNavigation.type==='dir' ? explorerNavigation.path : explorerNavigation.path.split('/').slice(0,-1).join('/')) : trail.join('/')" :navigating="!!explorerNavigation" :started-at="startedAt" :color="name=>engine?.color(name)||'#bac7da'" @select="selectExplorer" @clear="engine?.clear()" @marks="value=>marks=value" @latest="onLatest" @freshness="onFreshness" @route="value=>route=value" @clear-view-history="engine?.clearViewHistory()" :filter="filter" />
    <p v-if="scan?.truncated&&!open" class="space-scan-warning" role="status">{{ scanWarning(scan) }}</p>
    <button class="space-filter-toggle" role="switch" aria-label="フィルター" :aria-checked="filter" title="AiDiy のバックアップ対象のファイルだけを表示" @click="filter=!filter"><span>フィルター</span><span class="motion-switch" aria-hidden="true"></span><span aria-hidden="true">{{ filter?'ON':'OFF' }}</span></button>
    <FileViewer v-if="selected" :file="selected" :root="scan?.root" @activity="armPreviewTimer" @close="engine.clear()" @pin="pin" />
    <p v-if="pinError" class="app-error" role="alert">{{ pinError }}</p>
    <nav v-if="scan" v-show="viewMode==='3d'" class="space-breadcrumb"><button @click="engine.ascend(0)">{{ scan.tree.n }}</button><template v-for="(name,i) in trail" :key="i"><span>›</span><button @click="engine.ascend(i+1)">{{ name }}</button></template></nav>
    <div v-if="!scan&&(loading||error)" class="space-loading">{{ error||'読み込み中…' }}</div>
    <div v-else-if="error" class="space-notice" role="status"><span>{{ error }}</span><button aria-label="案内を閉じる" @click="error=''">×</button></div>
  </section>
</template>

<style scoped>
.space-scan-warning{position:absolute;left:16px;bottom:52px;z-index:35;max-width:min(340px,calc(100vw - 32px));margin:0;padding:6px 8px;color:#ffe28a;background:#080c1af2;font-size:var(--file-font-size,10px)}
.space-notice{position:fixed;left:50%;bottom:66px;transform:translateX(-50%);z-index:45;display:flex;align-items:start;gap:8px;max-width:min(680px,calc(100vw - 32px));padding:8px 10px;background:#251e10f2;color:#ffe5a2;border:1px solid #7c6740;font-size:var(--file-font-size,11px);pointer-events:none}.space-notice button{flex:none;pointer-events:auto;padding:0 5px}.mode-2d .space-notice{background:#f5e8c9;color:#74521f;border-color:#d8c398}
</style>
