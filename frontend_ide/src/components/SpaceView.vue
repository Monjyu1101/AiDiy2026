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
const autoSpin=ref(true);
let engine;
function change(value){if('scan'in value){scan.value=value.scan;selected.value=value.selected;trail.value=value.trail;focus.value=value.focus;}if('autoSpin'in value)autoSpin.value=value.autoSpin;loading.value=value.loading;if(value.error)error.value=value.error;}
function layout(){
  const preview=root.value?.querySelector('.viewer-popup');
  if(innerHeight>=innerWidth){
    root.value?.style.setProperty('--focus-x',`${innerWidth/2}px`);
    return{left:0,right:innerWidth,centerY:innerHeight*(preview?0.25:0.5)};
  }
  const explorer=root.value?.querySelector('.explorer-panel');
  const right=preview?preview.getBoundingClientRect().left-8:innerWidth;
  const left=preview&&open.value?Math.min(right,explorer.getBoundingClientRect().right+8):0;
  root.value?.style.setProperty('--focus-x',`${preview?(left+right)/2:innerWidth/2}px`);
  return{left,right,preview:!!preview};
}
watch(marks,value=>engine?.marks(value));
function documentKey(event){const frame=root.value?.querySelector('.viewer-popup iframe');if(!frame||event.origin!==location.origin||event.source!==frame.contentWindow||event.data?.type!=='aidiy-ide-document-key')return;if(event.data.key==='explorer')open.value=!open.value;else if(event.data.key==='close')engine.clear();}
onMounted(()=>{engine=createSpace(canvas.value,{tooltip:tooltip.value},{change,layout,toggleExplorer:()=>open.value=!open.value});engine.marks(marks.value);window.aidiyIDE=engine;window.addEventListener('message',documentKey);void engine.refresh(props.startedAt);});
onBeforeUnmount(()=>{engine?.dispose();if(window.aidiyIDE===engine)delete window.aidiyIDE;window.removeEventListener('message',documentKey);});
</script>
<template>
  <section ref="root" class="space-view" :class="{'explorer-open':open,viewing:!!selected}" data-component="SpaceView">
    <canvas ref="canvas" class="space-canvas"></canvas><div ref="tooltip" id="tooltip" hidden></div>
    <button class="space-motion-toggle" role="switch" aria-label="視点移動" :aria-checked="autoSpin" @click="engine?.setAutoSpin(!autoSpin)"><span>視点移動</span><span class="motion-switch" aria-hidden="true"></span><span aria-hidden="true">{{ autoSpin?'ON':'OFF' }}</span></button>
    <FileExplorer v-model:open="open" :tree="scan?.tree" :root="scan?.root" :selected="selected?.path" :current="trail.join('/')" :started-at="startedAt" :color="name=>engine?.color(name)||'#bac7da'" @select="entry=>engine?.goTo(entry)" @clear="engine?.clear()" @marks="value=>marks=value" />
    <FileViewer v-if="selected" :file="selected" :root="scan?.root" @close="engine.clear()" />
    <nav v-if="scan" class="space-breadcrumb"><button @click="engine.ascend(0)">{{ scan.tree.n }}</button><template v-for="(name,i) in trail" :key="i"><span>›</span><button @click="engine.ascend(i+1)">{{ name }}</button></template></nav>
    <div v-if="loading||error" class="space-loading">{{ error||'読み込み中…' }}</div>
  </section>
</template>
