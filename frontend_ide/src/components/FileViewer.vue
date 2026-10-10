<!-- COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
Licensed under "AiDiy 公開利用ライセンス v1.1".
Commercial use requires prior written consent from all copyright holders.
See LICENSE for full terms. Thank you for keeping the rules.
https://github.com/monjyu1101/AiDiy2026 -->
<script setup>
import { ref, watch, nextTick, onBeforeUnmount } from 'vue';
import { loadMonaco, monacoLanguage } from '../engines/monaco.js';
const props=defineProps({file:Object,root:String});const emit=defineEmits(['close']);
const data=ref(),error=ref(''),host=ref(),fallback=ref(false),copied=ref(false);
let controller,editor,revision=0;
const params=value=>new URLSearchParams(value).toString();
function disposeEditor(){editor?.getModel()?.dispose();editor?.dispose();editor=undefined;}
watch(()=>props.file,async file=>{
  const run=++revision;controller?.abort();controller=new AbortController();disposeEditor();data.value=null;error.value='';fallback.value=false;
  if(!file)return;
  try{
    const response=await fetch('/api/file?'+new URLSearchParams({path:file.path}),{signal:controller.signal});
    if(!response.ok)throw Error(await response.text());const value=await response.json();if(run!==revision)return;
    data.value=value;
    if(value.tooLarge){error.value='表示できるサイズの上限を超えています。';return;}
    if(value.kind==='text'){
      await nextTick();const monaco=await loadMonaco();if(run!==revision)return;
      if(!monaco){fallback.value=true;return;}
      editor=monaco.editor.create(host.value,{value:value.text,language:monacoLanguage(file.name),theme:'aidiy-space',readOnly:true,domReadOnly:true,automaticLayout:true,fontSize:12,wordWrap:'on',minimap:{enabled:true},scrollBeyondLastLine:false,contextmenu:false});
    }
  }catch(e){if(run===revision)error.value=e.message;}
},{immediate:true});
async function copy(){try{const separator=props.root.includes('\\')?'\\':'/';await navigator.clipboard.writeText(props.root+separator+props.file.path.replaceAll('/',separator));copied.value=true;}catch{error.value='パスをコピーできません。';}}
onBeforeUnmount(()=>{revision++;controller?.abort();disposeEditor();});
</script>
<template>
  <aside class="viewer-popup" data-component="FileViewer"><header><span>{{ file.name }}</span><button @click="copy">{{ copied?'コピーしました':'パスをコピー' }}</button><button aria-label="プレビューを閉じる" @click="emit('close')">×</button></header>
    <p class="viewer-path">{{ file.path }}</p><div class="viewer-meta">{{ data?.kind }} · {{ data?.size?.toLocaleString() }} B</div>
    <p v-if="error" class="error">{{ error }}</p><p v-else-if="!data">読み込み中…</p>
    <div v-else class="viewer-content"><iframe v-if="data.kind==='office'&&!data.tooLarge" :key="file.path" :src="'/office.html?'+params({path:file.path,format:data.format,v:file.mtime})" sandbox="allow-scripts allow-same-origin" :title="file.name+' ビューア'"></iframe>
      <img v-else-if="data.kind==='image'&&!data.tooLarge" :src="'/api/raw?'+params({path:file.path})" :alt="file.name">
      <template v-else-if="data.kind==='text'"><p v-if="data.truncated" class="input-hint">先頭の一部を表示しています。</p><pre v-if="fallback">{{ data.text }}</pre><div v-else ref="host" class="monaco-host"></div></template>
      <p v-else>この形式はプレビューできません。</p>
    </div>
  </aside>
</template>
