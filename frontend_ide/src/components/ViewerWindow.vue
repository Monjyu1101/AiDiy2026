<!-- COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
Licensed under "AiDiy 公開利用ライセンス v1.1".
Commercial use requires prior written consent from all copyright holders.
See LICENSE for full terms. Thank you for keeping the rules.
https://github.com/monjyu1101/AiDiy2026 -->
<script setup>
// ピン留めしたファイルの独立ウィンドウ。宇宙パネルの外で、同じIDEのファイルAPIを使って1ファイルを表示する。
import { ref, onMounted, onBeforeUnmount } from 'vue';
import StatusBar from './StatusBar.vue';
import FileViewer from './FileViewer.vue';
const props=defineProps({path:String,desktop:Boolean});
const state=ref({}),error=ref('');
const name=props.path.split('/').at(-1);
const file={name,path:props.path,mtime:0};
let timer;
// IDEの利用が終わったらファイルAPIは使えないので、状態を見て案内に切り替える（Electron版は子ウィンドウごと閉じる）
async function status(){
  try{const response=await fetch('/api/connection',{cache:'no-store',signal:AbortSignal.timeout(5000)});if(!response.ok)throw Error();state.value=await response.json();error.value=state.value.active?'':'IDEの利用が終了しました。';}
  catch{error.value='IDEに接続できません。';}
}
onMounted(()=>{document.title=`AiDiy IDE / Viewer - ${name}`;void status();timer=setInterval(status,3000);});
onBeforeUnmount(()=>clearInterval(timer));
</script>
<template>
  <div class="development-app viewer-window" :class="{'desktop-window':desktop}" data-app="viewer">
    <StatusBar :title="`Viewer - ${name}`" status="ピン留め" :connected="state.connected" :mode="state.mode" :desktop="desktop" />
    <FileViewer v-if="state.active" :file="file" :root="state.project?.path||''" pinned />
    <p v-else class="panel-loading">{{ error||'読み込み中…' }}</p>
  </div>
</template>
