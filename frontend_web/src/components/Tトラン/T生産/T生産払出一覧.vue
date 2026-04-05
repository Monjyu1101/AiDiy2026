<!--
  -*- coding: utf-8 -*-

  -------------------------------------------------------------------------
  COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
  Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
  Commercial use requires prior written consent from all copyright holders.
  See LICENSE for full terms. Thank you for keeping the rules.
  https://github.com/monjyu1101
  -------------------------------------------------------------------------
-->

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import apiClient from '../../../api/client';
import 払出一覧テーブル from './components/T生産払出一覧テーブル.vue';
import { qMessage } from '../../../utils/qAlert';

const router = useRouter();
const route = useRoute();
const 払出一覧テーブルRef = ref<any>(null);
const 件数制限 = ref(true);
const 無効も表示 = ref(false);
const 有効列表示 = computed(() => 無効も表示.value);
const 開始日付 = ref('');
const 終了日付 = ref('');
const 生産区分ID = ref('');
const 生産工程ID = ref('');
const 払出商品ID = ref('');
const 生産工程一覧 = ref<any[]>([]);
const 生産区分一覧 = ref<any[]>([]);
const 商品一覧 = ref<any[]>([]);

const normalizeQueryValue = (value: any): string | null => (Array.isArray(value) ? value[0] : value);
const toHalfwidthUrl = (value: string): string => value.replace(/？/g, '?').replace(/＆/g, '&').replace(/＝/g, '=');
const normalizeRouteUrl = (value: string): string => {
  const h = toHalfwidthUrl(value);
  try { return decodeURIComponent(h); } catch { return h; }
};

const 戻URL = computed(() => {
  const value = normalizeQueryValue(route.query.戻URL);
  return value ? String(value) : '';
});
const 編集戻URL = computed(() => {
  const query = { ...route.query };
  delete query.message;
  delete query.type;
  delete query.戻URL;
  return router.resolve({ path: route.path, query }).fullPath;
});

const handleReload = () => {
  払出一覧テーブルRef.value?.loadData();
};

const showMessage = (msg: string, type: string) => {
  void qMessage(msg, type || 'success');
};

const applyQueryParams = (query: any) => {
  開始日付.value  = String(normalizeQueryValue(query.開始日付)  ?? '');
  終了日付.value  = String(normalizeQueryValue(query.終了日付)  ?? '');
  生産区分ID.value = String(normalizeQueryValue(query.生産区分ID) ?? '');
  生産工程ID.value = String(normalizeQueryValue(query.生産工程ID) ?? '');
  払出商品ID.value = String(normalizeQueryValue(query.払出商品ID) ?? '');
};

const clearMessageQuery = (query: any) => {
  const nextQuery = { ...query };
  delete nextQuery.message;
  delete nextQuery.type;
  router.replace({ path: route.path, query: nextQuery });
};

const loadProcessList = async () => {
  try {
    const res = await apiClient.post('/apps/M生産工程/一覧');
    if (res.data.status === 'OK') {
      const data = res.data.data;
      生産工程一覧.value = Array.isArray(data) ? data : data?.items ?? [];
    }
  } catch { /* 無視 */ }
};

const loadCategoryList = async () => {
  try {
    const res = await apiClient.post('/apps/M生産区分/一覧');
    if (res.data.status === 'OK') {
      const data = res.data.data;
      生産区分一覧.value = Array.isArray(data) ? data : data?.items ?? [];
    }
  } catch { /* 無視 */ }
};

const loadProductList = async () => {
  try {
    const res = await apiClient.post('/apps/M商品/一覧');
    if (res.data.status === 'OK') {
      const data = res.data.data;
      商品一覧.value = Array.isArray(data) ? data : data?.items ?? [];
    }
  } catch { /* 無視 */ }
};

const handleCancel = () => {
  if (!戻URL.value) return;
  router.push(normalizeRouteUrl(戻URL.value));
};

applyQueryParams(route.query);

onMounted(async () => {
  const hasRouteMessage = Boolean(route.query.message);
  if (hasRouteMessage) {
    const text = normalizeQueryValue(route.query.message);
    const type = normalizeQueryValue(route.query.type);
    showMessage(String(text ?? ''), type ? String(type) : undefined);
    clearMessageQuery(route.query);
  }
  await loadProcessList();
  await loadCategoryList();
  await loadProductList();
});

watch(() => route.query.message, (newMessage) => {
  if (newMessage) {
    const text = normalizeQueryValue(newMessage);
    const type = normalizeQueryValue(route.query.type);
    showMessage(String(text ?? ''), type ? String(type) : undefined);
    clearMessageQuery(route.query);
  }
});

watch(() => [route.query.開始日付, route.query.終了日付, route.query.生産区分ID, route.query.生産工程ID, route.query.払出商品ID], () => {
  applyQueryParams(route.query);
  if (払出一覧テーブルRef.value) handleReload();
});
</script>

<template>
  <div class="page-container">
    <h2 class="page-title">
      <span class="title-text">【 T生産払出一覧 】</span>
      <button v-if="戻URL" class="btn-return" @click="handleCancel">戻る</button>
    </h2>

    <div class="content">
      <div class="section">
        <div class="toolbar">
          <div class="toolbar-left">
            <div class="search-panel">
              <div class="detail-row">
                <div class="detail-label">日付範囲</div>
                <div class="detail-value">
                  <div class="date-range">
                    <input type="date" v-model="開始日付" class="detail-input date-input" />
                    <span class="range-separator">〜</span>
                    <input type="date" v-model="終了日付" class="detail-input date-input" />
                  </div>
                </div>
              </div>
              <div class="detail-row">
                <div class="detail-label">生産区分</div>
                <div class="detail-value">
                  <select v-model="生産区分ID" class="detail-input select-input">
                    <option value="">すべて</option>
                    <option v-for="item in 生産区分一覧" :key="item.生産区分ID" :value="item.生産区分ID">
                      {{ item.生産区分ID }} : {{ item.生産区分名 }}
                    </option>
                  </select>
                </div>
              </div>
              <div class="detail-row">
                <div class="detail-label">生産工程</div>
                <div class="detail-value">
                  <select v-model="生産工程ID" class="detail-input select-input">
                    <option value="">すべて</option>
                    <option v-for="item in 生産工程一覧" :key="item.生産工程ID" :value="item.生産工程ID">
                      {{ item.生産工程ID }} : {{ item.生産工程名 }}
                    </option>
                  </select>
                </div>
              </div>
              <div class="detail-row">
                <div class="detail-label">払出商品</div>
                <div class="detail-value">
                  <select v-model="払出商品ID" class="detail-input select-input">
                    <option value="">すべて</option>
                    <option v-for="item in 商品一覧" :key="item.商品ID" :value="item.商品ID">
                      {{ item.商品ID }} : {{ item.商品名 }}
                    </option>
                  </select>
                </div>
              </div>
            </div>
            <button class="btn btn-primary" @click="handleReload">再検索</button>
          </div>
        </div>

        <div class="table-options">
          <label class="checkbox-label">
            <input type="checkbox" v-model="件数制限" @change="handleReload" />
            件数制限
          </label>
          <label class="checkbox-label">
            <input type="checkbox" v-model="無効も表示" @change="handleReload" />
            無効も表示
          </label>
        </div>

        <component
          :is="払出一覧テーブル"
          ref="払出一覧テーブルRef"
          :開始日付="開始日付"
          :終了日付="終了日付"
          :生産区分ID="生産区分ID"
          :生産工程ID="生産工程ID"
          :払出商品ID="払出商品ID"
          :件数制限="件数制限"
          :無効も表示="無効も表示"
          :有効列表示="有効列表示"
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

.title-text { flex: 1; }

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
.btn-return:hover { background-color: #c82333; }

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

.search-panel {
  display: flex;
  flex-direction: column;
  gap: 0;
  width: fit-content;
  --range-width: 360px;
}

.detail-row {
  display: flex;
  width: 100%;
  margin-top: -1px;
}
.detail-row:first-child { margin-top: 0; }

.detail-label {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  color: #333;
  font-weight: 600;
  text-align: right;
  padding: 8px 12px;
  border: 1px solid #b3e5fc;
  background: #e1f5fe;
  min-height: 40px;
  width: 160px;
  flex-shrink: 0;
  box-sizing: border-box;
}

.detail-value {
  display: flex;
  align-items: center;
  width: auto;
  color: #333;
  padding: 4px 12px;
  border: 1px solid #ccc;
  border-left: none;
  background: #fff;
  min-height: 40px;
  box-sizing: border-box;
  border-radius: 0;
}

.detail-input {
  height: 28px;
  padding: 0 8px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  background: #fff;
  font-size: 14px;
  box-sizing: border-box;
  margin: 0;
}
.detail-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: inset 0 0 0 1px rgba(0, 123, 255, 0.2);
}

.date-range {
  display: flex;
  align-items: center;
  gap: 8px;
  width: var(--range-width);
}
.range-separator { color: #666; font-weight: 600; }
.date-input { width: 160px; text-align: center; }
.select-input {
  width: var(--range-width);
  padding-right: 8px;
}
.text-input { width: var(--range-width); }

.toolbar {
  margin-bottom: 8px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.toolbar-left {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  flex-wrap: wrap;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 0;
  cursor: pointer;
  font-size: 14px;
}

.btn-primary { background-color: #007bff; color: white; }
.btn-primary:hover { background-color: #0056b3; }

.table-options {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 8px;
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
