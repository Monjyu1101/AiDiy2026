<script setup>
import {ref,computed,onMounted,onBeforeUnmount} from 'vue';
const props=defineProps({online:Boolean,enabled:Boolean,checking:Boolean,connected:Boolean,compact:Boolean,switching:Boolean});
defineEmits(['restore','mini']);
const desktop=ref(false),maximized=ref(false),pin=ref({pinned:false,locked:false}),pinBusy=ref(false);
const pinTitle=computed(()=>pin.value.locked?'VRモード中はピン止めを解除できません':pin.value.pinned?'ピン止めを解除（最前面 OFF）':'ピン止め（最前面 ON）');
let unsubscribePin,disposed=false,pinVersion=0;
function applyPin(value){if(!disposed&&typeof value?.pinned==='boolean'&&typeof value?.locked==='boolean')pin.value=value;}
async function togglePin(){if(pinBusy.value||pin.value.locked)return;pinBusy.value=true;try{applyPin(await window.aidiyWindow?.togglePin?.());}catch{}finally{pinBusy.value=false;}}
async function update(){try{maximized.value=!!(await window.aidiyWindow?.isMaximized?.());}catch{}}
async function action(value){try{await window.aidiyWindow?.[value]?.();await update();}catch{}}
onMounted(()=>{
 desktop.value=!!window.aidiyWindow;void update();window.addEventListener('resize',update);
 unsubscribePin=window.aidiyWindow?.onPinState?.(value=>{pinVersion++;applyPin(value);});
 const version=pinVersion;
 Promise.resolve(window.aidiyWindow?.getPinState?.()).then(value=>{if(version===pinVersion)applyPin(value);}).catch(()=>{});
});
onBeforeUnmount(()=>{disposed=true;unsubscribePin?.();window.removeEventListener('resize',update);});
</script>
<template>
<header class="panel-brand" :class="{desktop,compact}">
 <span class="connection-label" role="status"><i :class="{online:online&&enabled&&connected}" aria-hidden="true"></i>{{!connected?'診断 未接続':!enabled?'Tools 確認OFF':checking?'Tools 確認中':online?'Tools 接続中':'Tools 未接続'}}</span>
 <strong>{{compact?'AiDiy 起動メニュー':'AiDiy Diag'}}</strong>
 <span class="window-actions" :class="{'window-maximized':maximized}">
  <button v-if="!compact" class="title-mini-switch" :disabled="!connected||switching" @click="$emit('mini')" title="起動メニュー" aria-label="起動メニュー">起動メニュー</button>
  <button v-if="desktop" @click="action('minimize')" title="最小化" aria-label="最小化"><span class="window-minimize"></span></button>
  <button v-if="desktop||compact" :class="{'mini-restore':compact}" :disabled="switching" @click="compact?$emit('restore'):action('maximize')" :title="compact||maximized?'元のサイズに戻す':'最大化'" :aria-label="compact||maximized?'元のサイズに戻す':'最大化'"><span class="window-maximize"></span></button>
  <template v-if="desktop"><button class="window-pin" :class="{pinned:pin.pinned}" :aria-pressed="pin.pinned" :disabled="pin.locked||pinBusy" :title="pinTitle" :aria-label="pinTitle" @click="togglePin"><span aria-hidden="true">📌</span></button><button @click="action('close')" title="閉じる" aria-label="終了">×</button></template>
 </span>
</header>
<div class="connection-bar" :class="{online:online&&enabled&&connected,offline:!enabled}" aria-hidden="true"></div>
</template>
