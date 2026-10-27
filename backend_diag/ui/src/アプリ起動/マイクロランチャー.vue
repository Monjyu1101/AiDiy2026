<script setup>
import {起動モーション} from './起動モーション.mjs';
import './起動モーション.css';
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1". See LICENSE.
import {computed,ref,watch,onMounted,onBeforeUnmount,nextTick} from 'vue';
import {アプリアイコン} from './アプリアイコン.mjs';
import {アイコン移動} from './アイコン移動.mjs';
import 配置 from './円周配置.cjs';
import './マイクロランチャー.css';
const props=defineProps({appState:Object,cliState:Object,state:Object,online:Boolean,switching:Boolean});
const emit=defineEmits(['restore','mini','select']);
const expanded=ref(false),busy=ref(false),stage=ref(null),projectLabel=ref(null),unfolded=ref(false),moving=ref(false);
let foldTimer,clickTimer,labelObserver,disposed=false;
function resizeLabel(){if(disposed||expanded.value||busy.value)return;const height=projectLabel.value?.getBoundingClientRect?.().height;if(height>0)void window.aidiyWindow?.resizeMicroLabel?.(Math.ceil(height));}
watch([()=>props.switching,()=>props.appState.フォルダ.value,busy],async()=>{await nextTick();resizeLabel();});
function activity(){clearTimeout(foldTimer);if(expanded.value&&!moving.value)foldTimer=setTimeout(()=>{void toggle();},10*60*1000);}
const move=アイコン移動(window.aidiyWindow,{開始(){moving.value=true;clearTimeout(clickTimer);clearTimeout(foldTimer);},終了(){moving.value=false;activity();}});
function coreClick(event){if(move.click())return;clearTimeout(clickTimer);if(event.detail===0){void toggle();return;}clickTimer=setTimeout(()=>{void toggle();},400);}
function coreDouble(){if(move.double())return;clearTimeout(clickTimer);emit('mini');}
function startMove(event){if(!props.switching&&!busy.value)move.down(event);}
const apps=computed(()=>[...props.appState.項目.value.map(item=>({...item,kind:'app',icon:アプリアイコン[item.id]})),...props.cliState.項目.value.map(item=>({...item,kind:'cli',icon:`CLI_${item.id}.svg`}))]);
// OSに依存せず、末尾の区切りを除いたフォルダ名だけを表示する。
const projectName=computed(()=>{const folder=String(props.appState.フォルダ.value||'');return folder.replace(/[\\/]+$/,'').split(/[\\/]/).pop()||folder;});
const orbit=computed(()=>配置.円周配置(apps.value.length));
watch(()=>apps.value.length,async count=>{if(expanded.value)await window.aidiyWindow?.expandMicro(true,count);});
watch(()=>props.online,value=>{if(value){void props.appState.読込();void props.cliState.読込();}},{immediate:true});
function disabled(item){return !props.online||(item.kind==='app'&&!props.appState.利用可能(item.id))||!props.appState.フォルダ.value||props.appState.選択中.value||Boolean(props.appState.処理中.value)&&!(item.kind==='cli'&&props.appState.処理中.value.startsWith('cli:'));}
function launch(item,event){if(disabled(item))return;const 開始時=起動モーション(event);if(item.kind==='cli')void props.cliState.起動(item.id,{確認省略:true,開始時});else void props.appState.起動(item.id,{開始時});}
async function toggle(){
 if(busy.value||props.switching)return;busy.value=true;
 try{
  if(!expanded.value){if(window.aidiyWindow&&await window.aidiyWindow.expandMicro(true,apps.value.length)!==true)return;unfolded.value=true;expanded.value=true;await nextTick();activity();}
  else {clearTimeout(foldTimer);expanded.value=false;await nextTick();await new Promise(resolve=>setTimeout(resolve,460));if(!disposed){await window.aidiyWindow?.expandMicro(false);unfolded.value=false;}}
 }finally{busy.value=false;}
}
function key(event){if(event.key==='Escape'){event.preventDefault();if(moving.value){move.finish();return;}if(expanded.value)void toggle();else emit('restore');}}
onMounted(()=>{document.documentElement.classList.add('micro-mode');window.addEventListener('keydown',key);stage.value?.querySelector('.micro-core')?.focus();if(typeof ResizeObserver!=='undefined'&&projectLabel.value){labelObserver=new ResizeObserver(resizeLabel);labelObserver.observe(projectLabel.value);}resizeLabel();});
onBeforeUnmount(()=>{disposed=true;labelObserver?.disconnect();move.finish();clearTimeout(foldTimer);clearTimeout(clickTimer);document.documentElement.classList.remove('micro-mode');window.removeEventListener('keydown',key);});
</script>
<template>
<section ref="stage" class="micro-launcher" :class="{expanded,moving,unfolded}" :style="{'--radius':`${orbit.半径}px`,'--menu-size':`${orbit.幅}px`}" aria-label="アイコン化ランチャー" @pointermove="activity" @pointerdown="activity" @keydown="activity" @focusin="activity">
 <div class="micro-deploy" :inert="!expanded">
  <div class="micro-orbit micro-app-orbit" aria-label="アプリとCLI">
   <div v-for="(item,index) in apps" :key="item.kind+item.id" class="micro-position" :style="{'--angle':`${index*360/apps.length-90}deg`,'--stagger':`${index*22}ms`}">
    <div class="micro-upright"><button data-micro-hit class="micro-app" :data-app="item.kind==='app'?item.id:undefined" :data-cli="item.kind==='cli'?item.id:undefined" :disabled="disabled(item)" :title="(item.kind==='app'&&appState.不可理由(item.id))||item.名前+' を起動 — '+appState.フォルダ.value" :aria-label="item.名前+' を起動'+(item.kind==='app'&&appState.不可理由(item.id)?' — '+appState.不可理由(item.id):'')" @click="launch(item,$event)"><span class="launch-frame launch-frame-40" aria-hidden="true"><img :src="item.icon" alt="" width="40" height="40"><span class="launch-trace"></span></span></button></div>
   </div>
  </div>
 </div>
 <div data-micro-hit class="micro-move" title="ドラッグして移動" @pointerdown="startMove" @pointermove="move.move" @pointerup="move.finish" @pointercancel="move.finish" @lostpointercapture="move.finish"></div>
 <button data-micro-hit class="micro-core" @pointerdown="startMove" @pointermove="move.move" @pointerup="move.finish" @pointercancel="move.finish" @lostpointercapture="move.finish" @dragstart.prevent :aria-expanded="expanded" :aria-busy="busy" :title="(expanded?'メニューを閉じる':'ランチャーを開く')+' — '+appState.フォルダ.value+'（ドラッグで移動・ダブルクリックでランチャー表示・Escで戻る）'" aria-label="円形ランチャーを開閉" @click="coreClick" @dblclick.prevent="coreDouble"><span class="micro-mark"><img :src="expanded?'AiDiy_diag.png':'AiDiy.png'" alt="AiDiy" width="40" height="40"></span></button>
 <span ref="projectLabel" data-micro-hit class="micro-project" :title="projectName" @pointerdown="startMove" @pointermove="move.move" @pointerup="move.finish" @pointercancel="move.finish" @lostpointercapture="move.finish">{{projectName}}<span v-if="online&&state?.進捗表示?.value" class="micro-batch-status" role="status" aria-live="polite" :title="state.進捗表示.value.通知">{{state.進捗表示.value.種別==='stop'?'停止':'一括起動'}}{{state.進捗表示.value.状態==='running'?'中…':state.進捗表示.value.状態==='error'?'要確認':'完了'}}</span></span>
</section>
</template>
