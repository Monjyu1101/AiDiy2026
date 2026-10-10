<!-- COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
Licensed under "AiDiy 公開利用ライセンス v1.1".
Commercial use requires prior written consent from all copyright holders.
See LICENSE for full terms. Thank you for keeping the rules.
https://github.com/monjyu1101/AiDiy2026 -->
<script setup>
import { ref, watch } from 'vue';
const props = defineProps({ icon: String, kind: { default: 'code' }, started: Boolean });
const inputStarted = ref(false);
watch(() => props.started, value => { if (value) inputStarted.value = true; }, { immediate: true });
const lines = {
  code: ['LET’S BUILD SOMETHING', 'WHAT WILL YOU BUILD?', 'IT STARTS HERE.'],
  live: ['LET’S START A CONVERSATION', 'CONNECT, THEN TURN YOUR MIC ON.', 'YOU CAN ALSO TYPE TO CHAT.'],
  ide: ['FROM WORKSPACE TO OUTER SPACE.', 'MAKE SPACE FOR YOUR IDEAS.', 'CONNECT TO AIDIY OR EXPLORE OFFLINE.'],
};
</script>
<template>
  <div class="terminal-welcome" :class="[kind, { 'welcome-input-started': inputStarted }]" lang="en">
    <div class="welcome-mark" aria-hidden="true"><img :src="icon" alt=""></div>
    <p class="welcome-eyebrow"><span class="welcome-type"><span class="welcome-text">{{ lines[kind][0] }}</span></span></p>
    <h1><span class="welcome-type"><span class="welcome-text">{{ lines[kind][1] }}</span></span></h1>
    <p class="welcome-caption"><span class="welcome-type"><span class="welcome-text">{{ lines[kind][2] }}</span></span></p>
  </div>
</template>
