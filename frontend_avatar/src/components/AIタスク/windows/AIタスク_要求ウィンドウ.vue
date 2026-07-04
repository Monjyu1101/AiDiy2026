<!--
  -*- coding: utf-8 -*-

  -------------------------------------------------------------------------
  COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
  Licensed under "AiDiy 公開利用ライセンス v1.1".
  Commercial use requires prior written consent from all copyright holders.
  See LICENSE for full terms. Thank you for keeping the rules.
  https://github.com/monjyu1101/AiDiy2026
  -------------------------------------------------------------------------
-->

<script setup lang="ts">
// AIタスク_要求ウィンドウ (Electron task1): タスク要求一覧を単独ウィンドウで表示し、
// 選択タスクを BroadcastChannel(avatar-task-sync) でフロー図 / 明細ウィンドウへ配信する
import { ref, onMounted, onBeforeUnmount } from 'vue';
import AIタスク要求一覧 from '../components/AIタスク_要求一覧.vue';

const props = defineProps({
  利用者ID: { type: String, default: '' }
});

const 選択タスクID = ref('');
const 要求一覧Ref = ref<{ 新規ダイアログ表示: () => void } | null>(null);
let 選択タイトル = '';
let 選択マーメイド記号 = '';
let channel: BroadcastChannel | null = null;

function 選択配信() {
  if (!選択タスクID.value) return;
  channel?.postMessage({
    type: 'task-selected',
    タスクID: 選択タスクID.value,
    タイトル: 選択タイトル,
    マーメイド記号: 選択マーメイド記号
  });
}

function タスク選択(row: Record<string, any>) {
  選択タスクID.value = String(row.タスクID ?? '');
  選択タイトル = String(row.タイトル ?? '');
  選択マーメイド記号 = String(row.マーメイド記号 ?? '');
  選択配信();
}

function 新規ダイアログ表示() {
  要求一覧Ref.value?.新規ダイアログ表示();
}

onMounted(() => {
  channel = new BroadcastChannel('avatar-task-sync');
  channel.addEventListener('message', (event: MessageEvent) => {
    const payload = event.data;
    if (!payload || typeof payload !== 'object') return;
    // フロー図 / 明細ウィンドウの表示開始時に現在の選択を再配信する
    if (payload.type === 'request-task-selection') {
      選択配信();
    }
  });
});

onBeforeUnmount(() => {
  channel?.close();
  channel = null;
});

defineExpose({ 新規ダイアログ表示 });
</script>

<template>
  <div class="task-window-body">
    <component
      :is="AIタスク要求一覧"
      ref="要求一覧Ref"
      :利用者ID="props.利用者ID"
      :選択タスクID="選択タスクID"
      :showHeader="false"
      @select="タスク選択"
    />
  </div>
</template>

<style scoped>
.task-window-body {
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: #12101a;
}
</style>
