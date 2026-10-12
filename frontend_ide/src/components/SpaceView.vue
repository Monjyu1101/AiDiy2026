<!-- COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
Licensed under "AiDiy 公開利用ライセンス v1.1".
Commercial use requires prior written consent from all copyright holders.
See LICENSE for full terms. Thank you for keeping the rules.
https://github.com/monjyu1101/AiDiy2026 -->
<script setup>
import { ref, shallowRef, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import { createSpace } from '../engines/space.js';
import FileExplorer from './FileExplorer.vue';
import FileViewer from './FileViewer.vue';
const props=defineProps({startedAt:Number});
const canvas=ref(),tooltip=ref(),scan=shallowRef(),selected=shallowRef(),trail=ref([]),focus=shallowRef();
const open=ref(false),loading=ref(true),error=ref(''),root=ref(),marks=shallowRef({mode:'since',since:props.startedAt,paths:[]});
const autoSpin=ref(true),driving=ref(false),orbitPhase=ref('idle');
const fastWarp=ref(false);
watch(fastWarp,value=>engine?.setFastWarp(value));
const route=shallowRef({mode:'view',paths:[]});
const viewHistory=shallowRef([]);
watch(route,value=>engine?.route(value));
// ピン留め: 今のプレビューを閉じ、同じファイルを宇宙パネルの外の独立ウィンドウで開く（複数ファイルを並べて見る）。
// Electron 版は IDE の子ウィンドウ（利用終了・セッション切り替えで一緒に閉じる）、Web 版はブラウザの別ウィンドウ。
const pinError=ref('');
async function pin(file){
  pinError.value='';
  try{
    if(window.aidiyWindow?.openViewer){const result=await window.aidiyWindow.openViewer(file.path);if(!result?.ok)throw Error(result?.error||'ビューアを開けません。');}
    else if(!window.open('/#viewer='+encodeURIComponent(file.path),`aidiy-viewer-${file.path}`,'popup,width=680,height=780'))throw Error('ポップアップがブロックされました。');
    engine.clear();
  }catch(e){pinError.value=e.message;}
}
// 最終更新ファイルの表示: 起動直後の最終更新と、その後の新しい最終更新を宇宙へ予約する。
// 宇宙は自動探索 ON・オープニング後・追いかけてよい状態になってから、そのファイルまでワープして開く。
function onLatest(file){engine?.requestFollow(file.path);}
// フィルター（左下、既定 ON）: 宇宙とエクスプローラーを AiDiy のバックアップ対象だけにする。
const filter=ref(true);
watch(filter,on=>engine?.setFilter(on));
// ピン留めしていないビューアは最後の操作から5分で閉じ、自動探索が ON なら彗星軌道へ戻る。
// 別ファイルの表示と、ビューア内のスクロール・ボタン操作で期限を数え直す。
const PREVIEW_LIFETIME=300_000;let previewTimer;
function armPreviewTimer(){clearTimeout(previewTimer);if(!selected.value)return;previewTimer=setTimeout(()=>{if(!selected.value||!engine)return;engine.clear();if(autoSpin.value)engine.setAutoSpin(true);},PREVIEW_LIFETIME);}
watch(()=>selected.value?.path,armPreviewTimer);
let engine;
// 一覧からの移動中は選んだ行を保持し、中間階層を一覧へ送り返さない。
const explorerNavigation=shallowRef(null);
async function selectExplorer(entry){
  explorerNavigation.value=entry;
  try{await engine?.goTo(entry);}
  finally{if(explorerNavigation.value===entry)explorerNavigation.value=null;}
}
function change(value){if('scan'in value){scan.value=value.scan;selected.value=value.selected;trail.value=value.trail;focus.value=value.focus;viewHistory.value=value.journal||[];}if('autoSpin'in value)autoSpin.value=value.autoSpin;if('driving'in value)driving.value=value.driving;if('orbitPhase'in value)orbitPhase.value=value.orbitPhase;loading.value=value.loading;if(value.error)error.value=value.error;}
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
function documentKey(event){const frame=root.value?.querySelector('.viewer-popup iframe');if(!frame||event.origin!==location.origin||event.source!==frame.contentWindow||event.data?.type!=='aidiy-ide-document-key')return;if(event.data.key==='explorer')open.value=!open.value;else if(event.data.key==='close')engine.clear();}
onMounted(()=>{engine=createSpace(canvas.value,{tooltip:tooltip.value},{change,layout,toggleExplorer:()=>open.value=!open.value});engine.marks(marks.value);engine.route(route.value);window.aidiyIDE=engine;window.addEventListener('message',documentKey);void engine.refresh(props.startedAt);});
onBeforeUnmount(()=>{clearTimeout(previewTimer);engine?.dispose();if(window.aidiyIDE===engine)delete window.aidiyIDE;window.removeEventListener('message',documentKey);});
</script>
<template>
  <section ref="root" class="space-view" :class="{'explorer-open':open,viewing:!!selected}" data-component="SpaceView">
    <canvas ref="canvas" class="space-canvas"></canvas><div ref="tooltip" id="tooltip" hidden></div>
    <div class="space-flight-controls">
      <button class="space-motion-toggle space-fast-warp-toggle" role="switch" aria-label="高速ワープ" :aria-checked="fastWarp" title="別フォルダのファイルを選ぶと、1回のワープで目的フォルダへ移動" @click="fastWarp=!fastWarp"><span>高速ワープ</span><span class="motion-switch" aria-hidden="true"></span><span aria-hidden="true">{{ fastWarp?'ON':'OFF' }}</span></button>
      <div class="space-auto-explore">
        <div v-if="autoSpin&&['planning','aligning'].includes(orbitPhase)" class="space-orbit-status" role="status" aria-live="polite">探索軌道計算中<span aria-hidden="true">…</span></div>
        <button class="space-motion-toggle" :class="{driving:autoSpin&&driving}" role="switch" aria-label="自動探索" :aria-checked="autoSpin" :title="autoSpin&&driving?'自動探索中':''" @click="engine?.setAutoSpin(!autoSpin)"><span>自動探索</span><span class="motion-switch" aria-hidden="true"></span><span aria-hidden="true">{{ autoSpin?'ON':'OFF' }}</span></button>
      </div>
    </div>
    <FileExplorer v-model:open="open" :view-history="viewHistory" :tree="scan?.tree" :root="scan?.root" :selected="explorerNavigation ? (explorerNavigation.type==='file' ? explorerNavigation.path : undefined) : selected?.path" :current="explorerNavigation ? (explorerNavigation.type==='dir' ? explorerNavigation.path : explorerNavigation.path.split('/').slice(0,-1).join('/')) : trail.join('/')" :navigating="!!explorerNavigation" :started-at="startedAt" :color="name=>engine?.color(name)||'#bac7da'" @select="selectExplorer" @clear="engine?.clear()" @marks="value=>marks=value" @latest="onLatest" @route="value=>route=value" :filter="filter" />
    <button class="space-filter-toggle" role="switch" aria-label="フィルター" :aria-checked="filter" title="AiDiy のバックアップ対象のファイルだけを表示" @click="filter=!filter"><span>フィルター</span><span class="motion-switch" aria-hidden="true"></span><span aria-hidden="true">{{ filter?'ON':'OFF' }}</span></button>
    <FileViewer v-if="selected" :file="selected" :root="scan?.root" @activity="armPreviewTimer" @close="engine.clear()" @pin="pin" />
    <p v-if="pinError" class="app-error" role="alert">{{ pinError }}</p>
    <nav v-if="scan" class="space-breadcrumb"><button @click="engine.ascend(0)">{{ scan.tree.n }}</button><template v-for="(name,i) in trail" :key="i"><span>›</span><button @click="engine.ascend(i+1)">{{ name }}</button></template></nav>
    <div v-if="loading||error" class="space-loading">{{ error||'読み込み中…' }}</div>
  </section>
</template>
