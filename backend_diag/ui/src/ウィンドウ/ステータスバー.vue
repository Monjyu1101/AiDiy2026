<script setup>
import {ref,onMounted,onBeforeUnmount} from 'vue';
const props=defineProps({online:Boolean,enabled:Boolean,checking:Boolean,connected:Boolean,compact:Boolean});
const desktop=ref(false),maximized=ref(false);
async function update(){try{maximized.value=!!(await window.aidiyWindow?.isMaximized?.());}catch{}}
async function action(value){try{await window.aidiyWindow?.[value]?.();await update();}catch{}}
onMounted(()=>{desktop.value=!!window.aidiyWindow;void update();window.addEventListener('resize',update);});
onBeforeUnmount(()=>window.removeEventListener('resize',update));
</script>
<template>
<header class="panel-brand" :class="{desktop}">
 <span class="connection-label" role="status"><i :class="{online:online&&enabled&&connected}" aria-hidden="true"></i>{{!connected?'診断 未接続':!enabled?'tools 確認OFF':checking?'tools 確認中':online?'tools 接続済み':'tools 未接続'}}</span>
 <strong>{{compact?'AiDiy 起動':'AiDiy Diag'}}</strong>
 <span v-if="desktop" class="window-actions" :class="{'window-maximized':maximized}"><button @click="action('minimize')" title="最小化" aria-label="最小化"><span class="window-minimize"></span></button><button v-if="!compact" @click="action('maximize')" :title="maximized?'元のサイズに戻す':'最大化'" :aria-label="maximized?'元のサイズに戻す':'最大化'"><span class="window-maximize"></span></button><button @click="action('close')" title="閉じる" aria-label="終了">×</button></span>
</header>
<div class="connection-bar" :class="{online:online&&enabled&&connected,offline:!enabled}" aria-hidden="true"></div>
</template>
