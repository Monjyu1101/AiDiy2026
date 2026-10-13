<!-- COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
Licensed under "AiDiy 公開利用ライセンス v1.1".
Commercial use requires prior written consent from all copyright holders.
See LICENSE for full terms. Thank you for keeping the rules.
https://github.com/monjyu1101/AiDiy2026 -->
<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import ModalDialog from './ModalDialog.vue';
const props=defineProps({request:Object,loadTargets:Function,insertDraft:Function,launchTarget:Function});
const emit=defineEmits(['close']);
const snapshot=ref(null),selected=ref(''),busy=ref(false),error=ref('');
let generation=0,disposed=false;
const targets=computed(()=>snapshot.value?.targets||[]);
const target=computed(()=>targets.value.find(item=>item.id===selected.value));
async function refresh(){
  if(busy.value)return;const run=++generation;busy.value=true;error.value='';
  try{const result=await props.loadTargets(props.request);if(disposed||run!==generation)return;if(!result?.ok)throw Error(result?.error||'連携先を確認できません。');
    snapshot.value=result;
    selected.value=result.targets.length===1?result.targets[0].id:result.targets.some(item=>item.id===selected.value)?selected.value:'';
  }catch(e){if(!disposed&&run===generation){snapshot.value=null;selected.value='';error.value=e.message;}}
  finally{if(!disposed&&run===generation)busy.value=false;}
}
async function insert(){
  if(busy.value||!target.value)return;const run=++generation;busy.value=true;error.value='';
  const request={targetId:target.value.id,contextId:target.value.contextId,sessionKey:snapshot.value.sessionKey,projectPath:props.request.projectPath,text:props.request.text};
  try{const result=await props.insertDraft(request);if(disposed||run!==generation)return;if(!result?.ok)throw Error(result?.error||'下書きに追加できません。');emit('close');}
  catch(e){if(!disposed&&run===generation)error.value=e.message;}
  finally{if(!disposed&&run===generation)busy.value=false;}
}
async function launch(kind){
  if(busy.value||!props.launchTarget)return;busy.value=true;error.value='';
  try{const result=await props.launchTarget(kind,props.request);if(result?.ok===false)throw Error(result.error||'起動できません。');}
  catch(e){error.value=e.message;}
  finally{busy.value=false;}
  if(!disposed&&!error.value)await refresh();
}
onMounted(refresh);onBeforeUnmount(()=>{disposed=true;generation++;});
</script>
<template>
  <ModalDialog label="Code / Live の下書きへ追加" :locked="busy" @close="emit('close')">
    <h3>Code / Live の下書きへ追加</h3>
    <p class="draft-source">{{ request.path }}{{ request.selection?'（選択範囲）':'' }}</p>
    <p>起動中の連携先の入力欄へ追加します。既存の下書きを残し、送信はその画面で行います。</p>
    <label v-if="targets.length>1">連携先<select v-model="selected" :disabled="busy" aria-label="下書きの連携先"><option disabled value="">連携先を選択してください</option><option v-for="item in targets" :key="item.id" :value="item.id">{{ item.label }}</option></select></label>
    <p v-else-if="targets.length===1">連携先: {{ targets[0].label }}</p>
    <p v-else-if="!busy&&!error">起動中のCode / Liveがありません。IDEの「＋ Code」または「＋ Live」から起動してください。</p>
    <p v-if="target&&request.text.length>target.maxLength" class="error">選択範囲が連携先の入力上限を超えています。範囲を短くしてください。</p>
    <p v-if="error" class="error" role="alert">{{ error }}</p>
    <p v-if="busy" role="status">確認中…</p>
    <div class="dialog-actions draft-actions">
      <template v-if="!targets.length&&snapshot&&launchTarget"><button :disabled="busy" @click="launch('code')">＋ Code を起動</button><button v-if="snapshot.mode==='online'" :disabled="busy" @click="launch('live')">＋ Live を起動</button></template>
      <button :disabled="busy" @click="refresh">連携先を再確認</button>
      <button :disabled="busy||!target||request.text.length>target.maxLength" @click="insert">下書きへ追加</button>
      <button :disabled="busy" @click="emit('close')">キャンセル</button>
    </div>
  </ModalDialog>
</template>
