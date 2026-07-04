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
// AIタスク_フローウィンドウ (Electron task2): 要求ウィンドウの選択タスクを
// BroadcastChannel(avatar-task-sync) で受け取り、明細を取得してフロー図を表示する
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { taskClient } from '@/api/client';
import AIタスクフロー図 from '../components/AIタスク_フロー図.vue';

const props = defineProps({
  利用者ID: { type: String, default: '' }
});

const 選択タスクID = ref('');
const 選択タイトル = ref('');
const 選択マーメイド記号 = ref('');
const 明細rows = ref<Record<string, any>[]>([]);
let channel: BroadcastChannel | null = null;

async function 明細読込() {
  if (!選択タスクID.value || !props.利用者ID) {
    明細rows.value = [];
    return;
  }
  try {
    const res = await taskClient.post('/task/タスク明細/一覧', {
      利用者ID: props.利用者ID,
      タスクID: 選択タスクID.value
    });
    明細rows.value = res.data.status === 'OK' ? (res.data.data?.items ?? []) : [];
  } catch {
    明細rows.value = [];
  }
}

onMounted(() => {
  channel = new BroadcastChannel('avatar-task-sync');
  channel.addEventListener('message', (event: MessageEvent) => {
    const payload = event.data;
    if (!payload || typeof payload !== 'object') return;
    if (payload.type === 'task-selected') {
      選択タスクID.value = String(payload.タスクID ?? '');
      選択タイトル.value = String(payload.タイトル ?? '');
      選択マーメイド記号.value = String(payload.マーメイド記号 ?? '');
      void 明細読込();
    }
  });
  // 要求ウィンドウへ現在の選択を要求する
  channel.postMessage({ type: 'request-task-selection' });
});

onBeforeUnmount(() => {
  channel?.close();
  channel = null;
});
</script>

<template>
  <div class="task-window-body">
    <component
      :is="AIタスクフロー図"
      :タスクID="選択タスクID"
      :タイトル="選択タイトル"
      :マーメイド記号="選択マーメイド記号"
      :明細="明細rows"
      :showHeader="false"
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
