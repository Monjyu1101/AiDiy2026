<!-- COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
Licensed under "AiDiy 公開利用ライセンス v1.1".
Commercial use requires prior written consent from all copyright holders.
See LICENSE for full terms. Thank you for keeping the rules.
https://github.com/monjyu1101/AiDiy2026 -->
<script setup>
import {computed,useId} from 'vue';
import {browserGlassFrame,browserGlassMap} from './ガラス屈折.js';
const props=defineProps({frame:Object});
const frame=computed(()=>browserGlassFrame(props.frame));
const id='browser-glass-'+useId();
const horizontal=computed(()=>frame.value?browserGlassMap(frame.value.width,'x',12*frame.value.zoom):'');
const vertical=computed(()=>frame.value?browserGlassMap(frame.value.height,'y',12*frame.value.zoom):'');
</script>
<template>
 <!-- 別Electron窓を跨ぐbackdropではなく、本文から取得した実ピクセルの縁だけを変位する。 -->
 <svg v-if="frame" class="browser-glass-edge" :viewBox="`0 0 ${frame.width} ${frame.height}`" preserveAspectRatio="none" aria-hidden="true" focusable="false">
  <defs>
   <mask :id="id+'-rim'" maskUnits="userSpaceOnUse" x="0" y="0" :width="frame.width" :height="frame.height">
    <rect :width="frame.width" :height="frame.height" fill="white"/>
    <rect :x="12*frame.zoom" :y="12*frame.zoom" :width="Math.max(0,frame.width-24*frame.zoom)" :height="Math.max(0,frame.height-24*frame.zoom)" fill="black"/>
   </mask>
   <filter :id="id+'-bend'" filterUnits="userSpaceOnUse" primitiveUnits="userSpaceOnUse" x="0" y="0" :width="frame.width" :height="frame.height" color-interpolation-filters="sRGB">
    <feImage :href="horizontal" x="0" y="0" :width="frame.width" :height="frame.height" preserveAspectRatio="none" result="horizontal"/>
    <feDisplacementMap in="SourceGraphic" in2="horizontal" :scale="20*frame.zoom" xChannelSelector="R" yChannelSelector="B" result="bend-x"/>
    <feImage :href="vertical" x="0" y="0" :width="frame.width" :height="frame.height" preserveAspectRatio="none" result="vertical"/>
    <feDisplacementMap in="bend-x" in2="vertical" :scale="20*frame.zoom" xChannelSelector="B" yChannelSelector="G"/>
   </filter>
  </defs>
  <g :mask="`url(#${id}-rim)`">
   <image :href="frame.src" :x="frame.x" :y="frame.y" :width="frame.captureWidth" :height="frame.captureHeight" preserveAspectRatio="none" :filter="`url(#${id}-bend)`"/>
  </g>
 </svg>
</template>
<style scoped>
.browser-glass-edge{position:absolute;inset:-1px;width:calc(100% + 2px);height:calc(100% + 2px);z-index:0;pointer-events:none;user-select:none;overflow:hidden;border-radius:inherit}
</style>
