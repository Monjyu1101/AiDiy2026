<script setup>
import {ref,onMounted,onBeforeUnmount} from 'vue';
const props=defineProps({online:Boolean,enabled:Boolean,checking:Boolean,connected:Boolean,compact:Boolean,switching:Boolean});
defineEmits(['restore','mini']);
const desktop=ref(false),maximized=ref(false);
async function update(){try{maximized.value=!!(await window.aidiyWindow?.isMaximized?.());}catch{}}
async function action(value){try{await window.aidiyWindow?.[value]?.();await update();}catch{}}
onMounted(()=>{desktop.value=!!window.aidiyWindow;void update();window.addEventListener('resize',update);});
onBeforeUnmount(()=>window.removeEventListener('resize',update));
</script>
<template>
<header class="panel-brand" :class="{desktop,compact}">
 <span class="connection-label" role="status"><i :class="{online:online&&enabled&&connected}" aria-hidden="true"></i>{{!connected?'診断 未接続':!enabled?'Tools 確認OFF':checking?'Tools 確認中':online?'Tools 接続中':'Tools 未接続'}}</span>
 <strong>{{compact?'AiDiy 起動':'AiDiy Diag'}}</strong>
 <span class="window-actions" :class="{'window-maximized':maximized}"><button v-if="!compact" class="title-mini-switch" :disabled="!connected||switching" @click="$emit('mini')" title="ミニ表示" aria-label="ミニ表示">ミニ表示</button><button v-else class="mini-restore" :disabled="switching" @click="$emit('restore')" title="通常表示" aria-label="通常表示">↗</button><template v-if="desktop"><button @click="action('minimize')" title="最小化" aria-label="最小化"><span class="window-minimize"></span></button><button v-if="!compact" @click="action('maximize')" :title="maximized?'元のサイズに戻す':'最大化'" :aria-label="maximized?'元のサイズに戻す':'最大化'"><span class="window-maximize"></span></button><button @click="action('close')" title="閉じる" aria-label="終了">×</button></template></span>
</header>
<div class="connection-bar" :class="{online:online&&enabled&&connected,offline:!enabled}" aria-hidden="true"></div>
</template>
