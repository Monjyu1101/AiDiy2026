<!--
  -*- coding: utf-8 -*-

  ------------------------------------------------
  COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
  This software is licensed under the MIT License.
  https://github.com/monjyu1101
  Thank you for keeping the rules.
  ------------------------------------------------
-->

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import 車両一覧テーブル from './components/M車両一覧テーブル.vue';

const router = useRouter();
const route = useRoute();
const 車両一覧テーブルRef = ref(null);
const message = ref('');
const messageType = ref('success');

const handleReload = () => {
  車両一覧テーブルRef.value?.loadData();
};

const openCreate = () => {
  router.push({ path: '/Mマスタ/M車両/編集', query: { モード: '新規' } });
};

const showMessage = (msg, type) => {
  message.value = msg;
  messageType.value = type || 'success';
  setTimeout(() => {
    message.value = '';
  }, 3000);
};

onMounted(() => {
  if (route.query.message) {
    showMessage(route.query.message, route.query.type);
    router.replace({ path: route.path });
  }
});

watch(() => route.query.message, (newMessage) => {
  if (newMessage) {
    showMessage(newMessage, route.query.type);
    router.replace({ path: route.path });
  }
});
</script>

<template>
  <div class="page-container">
    <h2 class="page-title">【 M車両 】</h2>

    <div class="content">
      <div class="section">
        <div class="toolbar">
          <button class="btn btn-primary" @click="handleReload">再検索</button>
          <button class="btn btn-success" @click="openCreate">新規</button>
          <div
            v-if="message"
            :class="['message', messageType === 'error' ? 'message-error' : 'message-success']"
          >
            {{ message }}
          </div>
        </div>

        <component :is="車両一覧テーブル" ref="車両一覧テーブルRef" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #faf7f2 0%, #f5f1e8 50%, #f0ebe0 100%);
}

.page-title {
  background: linear-gradient(135deg, #e6d5b7 0%, #dcc8a6 50%, #d2bb95 100%);
  margin: 0 0 5px 0;
  font-size: 14px;
  width: 100%;
  box-sizing: border-box;
  padding: 10px 20px 10px 40px;
  height: 35px;
  line-height: 20px;
  color: #5a4a3a;
  font-weight: bold;
  box-shadow: 0 2px 4px rgba(210, 187, 149, 0.3);
}

.content {
  padding: 8px 20px 20px 20px;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.section {
  margin-bottom: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.toolbar {
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 0;
  cursor: pointer;
  font-size: 14px;
  margin-right: 10px;
  margin-bottom: 0;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover {
  background-color: #0056b3;
}

.btn-success {
  background-color: #28a745;
  color: white;
}

.btn-success:hover {
  background-color: #1e7e34;
}

.message {
  padding: 10px;
  border-radius: 0;
  flex: 1;
  min-width: 220px;
}

.message-success {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.message-error {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}
</style>

