<!-- COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
Licensed under "AiDiy 公開利用ライセンス v1.1".
Commercial use requires prior written consent from all copyright holders.
See LICENSE for full terms. Thank you for keeping the rules.
https://github.com/monjyu1101/AiDiy2026 -->
<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue';
const props = defineProps({ title: String, status: String, mode: String, connected: Boolean, busy: Boolean, active: Boolean, desktop: Boolean, clockPulse: Boolean, windowApi: Object, windowContext: Object, allowAll: Boolean, allDisplays: Boolean, allBusy: Boolean, hideClose: Boolean });
const emit = defineEmits(['toggle-all']);
const currentWindow = props.windowContext || window;
const maximized = ref(false);
const pulseLevel = ref(0);
let pulseTimer;
// Webのタイトル下線と同じ時刻・式・50ms更新。絶対値なので明滅は4.5秒周期。
function updatePulse(){pulseLevel.value=Math.round(255*Math.abs(Math.sin(((Date.now()/1000)%9)/9*Math.PI*2)));}
// 黒い未接続バー・非表示の画面では20回/秒のVue更新を止め、復帰時に現在時刻へ揃える。
function syncPulse(){clearInterval(pulseTimer);pulseTimer=undefined;if(props.clockPulse&&!document.hidden&&(props.mode==='offline'||props.connected)){updatePulse();pulseTimer=setInterval(updatePulse,50);}}
watch(()=>[props.clockPulse,props.mode,props.connected],syncPulse);
const pulseStyle = computed(()=>props.clockPulse?{
  backgroundColor:props.mode==='offline'?`rgb(${pulseLevel.value}, 0, 0)`:props.connected?`rgb(0, ${pulseLevel.value}, ${pulseLevel.value})`:'rgb(0, 0, 0)',
  animation:'none',opacity:1,
}:undefined);
async function updateWindow() { if (props.desktop) maximized.value = !!(await (props.windowApi || currentWindow.aidiyWindow)?.isMaximized?.()); }
async function action(value) { await (props.windowApi || currentWindow.aidiyWindow)?.[value]?.(); await updateWindow(); }
onMounted(() => { void updateWindow(); currentWindow.addEventListener('resize', updateWindow);document.addEventListener('visibilitychange',syncPulse);syncPulse(); });
onBeforeUnmount(() => {currentWindow.removeEventListener('resize', updateWindow);document.removeEventListener('visibilitychange',syncPulse);clearInterval(pulseTimer);});
</script>
<template>
  <header class="panel-brand" :class="{ desktop }">
    <span class="connection-label" role="status"><i :class="{ online: connected, active: active || busy }"></i>{{ status || (busy ? '接続中' : connected ? '接続済み' : '未接続') }}</span>
    <strong>{{ title }}</strong>
    <span v-if="desktop" class="window-actions" :class="{ 'window-maximized': maximized }"><button v-if="allowAll" class="window-all" :aria-pressed="allDisplays" :disabled="allBusy" :title="allDisplays?'VRモードを終了':'VRモード：全ディスプレイに宇宙空間を広げる'" aria-label="VRモード" @click="emit('toggle-all')">VR</button><button @click="action('minimize')" title="最小化" aria-label="最小化"><span class="window-minimize"></span></button><button @click="action('maximize')" :title="maximized ? '元のサイズに戻す' : '最大化'" :aria-label="maximized ? '元のサイズに戻す' : '最大化'"><span class="window-maximize"></span></button><button v-if="!hideClose" @click="action('close')" title="閉じる" aria-label="終了">×</button></span>
  </header>
  <div class="connection-bar" :class="{ online: connected && mode !== 'offline', offline: mode === 'offline' }" :style="pulseStyle"></div>
</template>
