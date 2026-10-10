<!-- COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
Licensed under "AiDiy 公開利用ライセンス v1.1".
Commercial use requires prior written consent from all copyright holders.
See LICENSE for full terms. Thank you for keeping the rules.
https://github.com/monjyu1101/AiDiy2026 -->
<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
const props = defineProps({ title: String, status: String, mode: String, connected: Boolean, busy: Boolean, active: Boolean, desktop: Boolean, clockPulse: Boolean });
const maximized = ref(false);
const pulseLevel = ref(0);
let pulseTimer;
// Webのタイトル下線と同じ時刻・式・50ms更新。絶対値なので明滅は4.5秒周期。
function updatePulse(){pulseLevel.value=Math.round(255*Math.abs(Math.sin(((Date.now()/1000)%9)/9*Math.PI*2)));}
const pulseStyle = computed(()=>props.clockPulse?{
  backgroundColor:props.mode==='offline'?`rgb(${pulseLevel.value}, 0, 0)`:props.connected?`rgb(0, ${pulseLevel.value}, ${pulseLevel.value})`:'rgb(0, 0, 0)',
  animation:'none',opacity:1,
}:undefined);
async function updateWindow() { if (props.desktop) maximized.value = !!(await window.aidiyWindow?.isMaximized?.()); }
async function action(value) { await window.aidiyWindow?.[value]?.(); await updateWindow(); }
onMounted(() => { void updateWindow(); window.addEventListener('resize', updateWindow);if(props.clockPulse){updatePulse();pulseTimer=setInterval(updatePulse,50);} });
onBeforeUnmount(() => {window.removeEventListener('resize', updateWindow);clearInterval(pulseTimer);});
</script>
<template>
  <header class="panel-brand" :class="{ desktop }">
    <span class="connection-label" role="status"><i :class="{ online: connected, active: active || busy }"></i>{{ status || (busy ? '接続中' : connected ? '接続済み' : '未接続') }}</span>
    <strong>{{ title }}</strong>
    <span v-if="desktop" class="window-actions" :class="{ 'window-maximized': maximized }"><button @click="action('minimize')" title="最小化" aria-label="最小化"><span class="window-minimize"></span></button><button @click="action('maximize')" :title="maximized ? '元のサイズに戻す' : '最大化'" :aria-label="maximized ? '元のサイズに戻す' : '最大化'"><span class="window-maximize"></span></button><button @click="action('close')" title="閉じる" aria-label="終了">×</button></span>
  </header>
  <div class="connection-bar" :class="{ online: connected && mode !== 'offline', offline: mode === 'offline' }" :style="pulseStyle"></div>
</template>
