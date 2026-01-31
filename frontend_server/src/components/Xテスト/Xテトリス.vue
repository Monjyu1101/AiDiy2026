<!--
  -*- coding: utf-8 -*-

  ------------------------------------------------
  COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
  This software is licensed under the MIT License.
  https://github.com/monjyu1101
  Thank you for keeping the rules.
  ------------------------------------------------
-->

<template>
  <div class="iframe-wrapper">
    <iframe
      class="game-frame"
      :src="frameSrc"
      title="Xテトリス"
      frameborder="0"
      allow="autoplay; fullscreen"
      loading="lazy"
    ></iframe>
  </div>
</template>

<script setup lang="ts">
const baseUrl = import.meta.env.BASE_URL || '/';
const frameSrc = `${baseUrl}Xテトリス/index.html`;
</script>

<style scoped>
.iframe-wrapper {
  width: 100%;
  height: 100%;
}

.game-frame {
  width: 100%;
  height: 100%;
  border: 0;
  display: block;
}
</style>

