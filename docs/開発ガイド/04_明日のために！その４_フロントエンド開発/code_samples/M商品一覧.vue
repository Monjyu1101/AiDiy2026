<!--
 -*- coding: utf-8 -*-

 -------------------------------------------------------------------------
 COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
 Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
 Commercial use requires prior written consent from all copyright holders.
 See LICENSE for full terms. Thank you for keeping the rules.
 https://github.com/monjyu1101/AiDiy2026
 -------------------------------------------------------------------------
-->

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import 商品一覧テーブル from './components/M商品一覧テーブル.vue';
import { qMessage } from '../../../utils/qAlert';

const router = useRouter();
const route = useRoute();
const 商品一覧テーブルRef = ref(null);
const includeInactive = ref(false);

// ==================================================
// 戻URLユーティリティ
// query値は配列になる場合があるため normalizeQueryValue で文字列化する。
// ==================================================
const normalizeQueryValue = (value: string | string[] | null | undefined): string | null =>
  Array.isArray(value) ? value[0] ?? null : value ?? null;
const toHalfwidthUrl = (value: string): string => value.replace(/？/g, '?').replace(/＆/g, '&').replace(/＝/g, '=');

// この一覧画面自身が戻URL付きで呼ばれた場合（例: 別の画面から戻ってきた場合）
const 戻URL = computed(() => {
  const value = normalizeQueryValue(route.query.戻URL as string | string[] | undefined);
  return value ? String(value) : '';
});

// 編集画面へ渡す戻URL: 現在の一覧URLからメッセージ系クエリと戻URLを除いたもの
// 編集完了後に「ここ（一覧）に戻ってくる」ために使う
const 編集戻URL = computed(() => {
  const query = { ...route.query };
  delete query.message;
  delete query.type;
  delete query.戻URL;
  return router.resolve({ path: route.path, query }).fullPath;
});

const handleReload = () => {
  商品一覧テーブルRef.value?.loadData();
};

// 新規作成画面へ: 編集戻URLを渡す
const openCreate = () => {
  const query: Record<string, string> = { モード: '新規', 戻URL: 編集戻URL.value };
  router.push({ path: '/Mマスタ/M商品/編集', query });
};

const showMessage = (msg: string, type?: string) => {
  void qMessage(msg, type || 'success');
};

// message/type クエリを URL から除去する（表示後にURLをクリーンアップ）
const clearMessageQuery = (query: typeof route.query) => {
  const nextQuery = { ...query };
  delete nextQuery.message;
  delete nextQuery.type;
  router.replace({ path: route.path, query: nextQuery });
};

// この一覧画面が戻URL付きで呼ばれた場合の「戻る」ハンドラ
const handleCancel = () => {
  if (!戻URL.value) return;
  router.push(toHalfwidthUrl(戻URL.value));
};

onMounted(() => {
  if (route.query.message) {
    const text = normalizeQueryValue(route.query.message as string | string[] | undefined);
    const type = normalizeQueryValue(route.query.type as string | string[] | undefined);
    showMessage(String(text ?? ''), type ? String(type) : undefined);
    clearMessageQuery(route.query);
  }
});

watch(() => route.query.message, (newMessage) => {
  if (newMessage) {
    const text = normalizeQueryValue(newMessage as string | string[] | undefined);
    const type = normalizeQueryValue(route.query.type as string | string[] | undefined);
    showMessage(String(text ?? ''), type ? String(type) : undefined);
    clearMessageQuery(route.query);
  }
});
</script>

<template>
  <div class="page-container">
    <!-- タイトルバー: 戻URLがある場合は「戻る」ボタンを右端に表示 -->
    <h2 class="page-title">
      <span class="title-text">【 M商品 】</span>
      <button v-if="戻URL" class="btn-return" @click="handleCancel">戻る</button>
    </h2>

    <div class="content">
      <div class="section">
        <div class="toolbar">
          <div class="toolbar-left">
            <div class="search-area">
              <button class="btn btn-primary" @click="handleReload">再検索</button>
              <!-- 無効レコードも一覧に表示するかどうか -->
              <label class="checkbox-label">
                <input type="checkbox" v-model="includeInactive" />
                無効も検索
              </label>
            </div>
          </div>
          <div class="toolbar-right">
            <button class="btn btn-success" @click="openCreate">新規</button>
          </div>
        </div>

        <!--
          :includeInactive  — 無効レコードの表示/非表示をテーブルへ伝える
          :戻URL="編集戻URL" — 一覧行クリック時に編集画面へ渡す戻URL（編集完了後にここへ戻る）
        -->
        <component
          :is="商品一覧テーブル"
          ref="商品一覧テーブルRef"
          :includeInactive="includeInactive"
          :戻URL="編集戻URL"
        />
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
  display: flex;
  align-items: center;
}

.title-text {
  flex: 1;
}

.btn-return {
  margin-left: auto;
  height: 24px;
  padding: 0 12px;
  border: none;
  border-radius: 0;
  cursor: pointer;
  font-size: 12px;
  background-color: #dc3545;
  color: #fff;
}

.btn-return:hover {
  background-color: #c82333;
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
  align-items: flex-start;
  justify-content: space-between;
}

.toolbar-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.search-area {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
}

.toolbar-right {
  display: flex;
  align-items: flex-start;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 0;
  cursor: pointer;
  font-size: 14px;
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

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 14px;
  cursor: pointer;
  color: #5a4a3a;
  user-select: none;
}

.checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
  margin: 0;
}
</style>
