<script setup>
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1". See LICENSE.
import {computed,ref,watch,onMounted,onBeforeUnmount,nextTick} from 'vue';
import {アプリアイコン} from './アプリアイコン.mjs';
import {アイコン移動} from './アイコン移動.mjs';
import 配置 from './円周配置.cjs';
import './マイクロランチャー.css';
const props=defineProps({appState:Object,cliState:Object,state:Object,online:Boolean,switching:Boolean});
const emit=defineEmits(['restore','mini','select']);
const expanded=ref(false),busy=ref(false),stage=ref(null),moving=ref(false);
let foldTimer,clickTimer,disposed=false;
function activity(){clearTimeout(foldTimer);if(expanded.value&&!moving.value)foldTimer=setTimeout(()=>{void toggle();},10*60*1000);}
const move=アイコン移動(window.aidiyWindow,{開始(){moving.value=true;clearTimeout(clickTimer);clearTimeout(foldTimer);},終了(){moving.value=false;activity();}});
function coreClick(event){if(move.click())return;clearTimeout(clickTimer);if(event.detail===0){void toggle();return;}clickTimer=setTimeout(()=>{void toggle();},400);}
function coreDouble(){if(move.double())return;clearTimeout(clickTimer);emit('mini');}
function startMove(event){if(!props.switching&&!busy.value)move.down(event);}
const apps=computed(()=>[...props.appState.項目.value.map(item=>({...item,kind:'app',icon:アプリアイコン[item.id]})),...props.cliState.項目.value.map(item=>({...item,kind:'cli',icon:`CLI_${item.id}.svg`}))]);
const orbit=computed(()=>配置.円周配置(apps.value.length));
watch(()=>apps.value.length,async count=>{if(expanded.value)await window.aidiyWindow?.expandMicro(true,count);});
watch(()=>props.online,value=>{if(value){void props.appState.読込();void props.cliState.読込();}},{immediate:true});
function disabled(item){return !props.online||!props.appState.フォルダ.value||props.appState.選択中.value||Boolean(props.appState.処理中.value)&&!(item.kind==='cli'&&props.appState.処理中.value.startsWith('cli:'));}
function launch(item){if(disabled(item))return;if(item.kind==='cli')void props.cliState.起動(item.id,{確認省略:true});else void props.appState.起動(item.id);}
async function toggle(){
 if(busy.value||props.switching)return;busy.value=true;
 try{
  if(!expanded.value){if(window.aidiyWindow&&await window.aidiyWindow.expandMicro(true,apps.value.length)!==true)return;expanded.value=true;await nextTick();activity();}
  else {clearTimeout(foldTimer);expanded.value=false;await nextTick();await new Promise(resolve=>setTimeout(resolve,460));if(!disposed)await window.aidiyWindow?.expandMicro(false);}
 }finally{busy.value=false;}
}
function key(event){if(event.key==='Escape'){event.preventDefault();if(moving.value){move.finish();return;}if(expanded.value)void toggle();else emit('restore');}}
onMounted(()=>{document.documentElement.classList.add('micro-mode');window.addEventListener('keydown',key);stage.value?.querySelector('.micro-core')?.focus();});
onBeforeUnmount(()=>{disposed=true;move.finish();clearTimeout(foldTimer);clearTimeout(clickTimer);document.documentElement.classList.remove('micro-mode');window.removeEventListener('keydown',key);});
</script>
<template>
<section ref="stage" class="micro-launcher" :class="{expanded,moving}" :style="{'--radius':`${orbit.半径}px`,'--menu-size':`${orbit.幅}px`}" aria-label="アイコン化ランチャー" @pointermove="activity" @pointerdown="activity" @keydown="activity" @focusin="activity">
 <div class="micro-deploy" :inert="!expanded">
  <div class="micro-orbit micro-app-orbit" aria-label="アプリとCLI">
   <div v-for="(item,index) in apps" :key="item.kind+item.id" class="micro-position" :style="{'--angle':`${index*360/apps.length-90}deg`,'--stagger':`${index*22}ms`}">
    <div class="micro-upright"><button data-micro-hit class="micro-app" :data-app="item.kind==='app'?item.id:undefined" :data-cli="item.kind==='cli'?item.id:undefined" :disabled="disabled(item)" :title="item.名前+' を起動 — '+appState.フォルダ.value" :aria-label="item.名前+' を起動'" @click="launch(item)"><img :src="item.icon" alt="" width="40" height="40"></button></div>
   </div>
  </div>
 </div>
 <div data-micro-hit class="micro-move" title="ドラッグして移動" @pointerdown="startMove" @pointermove="move.move" @pointerup="move.finish" @pointercancel="move.finish" @lostpointercapture="move.finish"></div>
 <button data-micro-hit class="micro-core" @pointerdown="startMove" @pointermove="move.move" @pointerup="move.finish" @pointercancel="move.finish" @lostpointercapture="move.finish" @dragstart.prevent :aria-expanded="expanded" :aria-busy="busy" :title="(expanded?'メニューを閉じる':'ランチャーを開く')+' — '+appState.フォルダ.value+'（ドラッグで移動・ダブルクリックでランチャー表示・Escで戻る）'" aria-label="円形ランチャーを開閉" @click="coreClick" @dblclick.prevent="coreDouble"><span class="micro-mark"><img :src="expanded?'AiDiy_diag.png':'AiDiy.png'" alt="AiDiy" width="40" height="40"></span></button>
</section>
</template>
