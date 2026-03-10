#!/usr/bin/env node
// -*- coding: utf-8 -*-
//
// M得意先 コンポーネントセットアップスクリプト
// 実行方法: node setup-tokui.mjs
//

import { mkdirSync, writeFileSync, existsSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const dir = resolve(__dirname, 'src/components/Mマスタ/M得意先')
const subdir = resolve(dir, 'components')

if (existsSync(dir)) {
  console.log('[skip] M得意先 ディレクトリは既に存在します:', dir)
  process.exit(0)
}

mkdirSync(subdir, { recursive: true })
console.log('[OK] ディレクトリ作成:', dir)
console.log('[OK] ディレクトリ作成:', subdir)

// M得意先一覧テーブル.vue
writeFileSync(resolve(subdir, 'M得意先一覧テーブル.vue'), `\
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
import { ref, reactive, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import apiClient from '../../../../api/client';
import qTublerFrame from '../../../_share/qTublerFrame.vue';

const router = useRouter();

const 得意先一覧 = ref([]);
const pageSize = ref(100);
const currentPage = ref(1);
const sortKey = ref('得意先ID');
const sortOrder = ref('asc');
const filters = reactive({
  得意先ID: '',
  得意先名: '',
  得意先備考: '',
  更新日時: '',
  更新利用者名: ''
});
const rowKey = '得意先ID';
const columns = [
  { key: '得意先ID', label: '得意先ID', width: '120px', sortable: true },
  { key: '得意先名', label: '得意先名', width: '240px', sortable: true },
  { key: '得意先備考', label: '得意先備考', width: '260px', sortable: true },
  { key: '更新日時', label: '更新日時', width: '160px', sortable: true },
  { key: '更新利用者名', label: '更新利用者名', width: '130px', sortable: true }
];

const message = ref('');
const messageType = ref('success');

const setMessage = (text, type = 'success') => {
  message.value = text;
  messageType.value = type;
};

const hasFilter = computed(() => {
  return Object.values(filters).some((value) => String(value || '').trim() !== '');
});
const filteredRows = computed(() => {
  return 得意先一覧.value.filter((row) => {
    return columns.every((column) => {
      const filterValue = (filters[column.key] || '').trim();
      if (!filterValue) return true;
      const cellValue = row?.[column.key] ?? '';
      return String(cellValue).toLowerCase().includes(filterValue.toLowerCase());
    });
  });
});
const totalCount = computed(() => filteredRows.value.length);
const totalAll = computed(() => 得意先一覧.value.length);
const totalPages = computed(() => Math.max(1, Math.ceil(totalCount.value / pageSize.value)));
const sortedRows = computed(() => {
  const rows = [...filteredRows.value];
  if (!sortKey.value) return rows;
  rows.sort((a, b) => {
    const aValue = a?.[sortKey.value] ?? '';
    const bValue = b?.[sortKey.value] ?? '';
    const aNum = Number(aValue);
    const bNum = Number(bValue);
    const isNumeric = !Number.isNaN(aNum) && !Number.isNaN(bNum);
    let result = 0;
    if (isNumeric) {
      result = aNum - bNum;
    } else {
      result = String(aValue).localeCompare(String(bValue), 'ja');
    }
    return sortOrder.value === 'desc' ? -result : result;
  });
  return rows;
});
const pagedRows = computed(() => {
  const startIndex = (currentPage.value - 1) * pageSize.value;
  return sortedRows.value.slice(startIndex, startIndex + pageSize.value);
});

const handleSort = (column) => {
  if (!column.sortable) return;
  if (sortKey.value === column.key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortKey.value = column.key;
    sortOrder.value = 'asc';
  }
};

const goToPage = (page) => {
  if (page < 1 || page > totalPages.value) return;
  currentPage.value = page;
};

const openDetail = (row) => {
  router.push({ path: '/Mマスタ/M得意先/編集', query: { モード: '編集', 得意先ID: row.得意先ID } });
};

const loadData = async () => {
  message.value = '';
  try {
    const res = await apiClient.post('/apps/V得意先/一覧');
    if (res.data.status === 'OK') {
      const data = res.data.data;
      const items = Array.isArray(data) ? data : data?.items ?? [];
      得意先一覧.value = items;
      currentPage.value = 1;
    } else {
      setMessage(res.data.message || 'M得意先一覧の取得に失敗しました。', 'error');
    }
  } catch (e) {
    setMessage('M得意先一覧の取得でエラーが発生しました。', 'error');
  }
};

onMounted(async () => {
  await loadData();
});

defineExpose({
  loadData
});
<\/script>

<template>
  <qTublerFrame
    :columns="columns"
    :rows="pagedRows"
    :rowKey="rowKey"
    :sortKey="sortKey"
    :sortOrder="sortOrder"
    :message="message"
    :messageType="messageType"
    :hasFilter="hasFilter"
    :totalCount="totalCount"
    :totalAll="totalAll"
    :currentPage="currentPage"
    :totalPages="totalPages"
    @sort="handleSort"
    @page="goToPage"
  >
    <template #filter="{ column }">
      <input
        v-if="filters[column.key] !== undefined"
        v-model="filters[column.key]"
        class="filter-input"
        type="text"
      />
    </template>
    <template #cell="{ row, column, value }">
      <template v-if="column.key === '得意先ID'">
        <a href="#" class="id-link" @click.prevent="openDetail(row)">{{ row.得意先ID }}</a>
      </template>
      <template v-else>
        {{ value ?? '' }}
      </template>
    </template>
  </qTublerFrame>
</template>
`, { encoding: 'utf-8' })
console.log('[OK] ファイル作成: components/M得意先一覧テーブル.vue')

// M得意先一覧.vue
writeFileSync(resolve(dir, 'M得意先一覧.vue'), `\
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
import { ref, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import 得意先一覧テーブル from './components/M得意先一覧テーブル.vue';

const router = useRouter();
const route = useRoute();
const 得意先一覧テーブルRef = ref(null);
const message = ref('');
const messageType = ref('success');

const handleReload = () => {
  得意先一覧テーブルRef.value?.loadData();
};

const openCreate = () => {
  router.push({ path: '/Mマスタ/M得意先/編集', query: { モード: '新規' } });
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
<\/script>

<template>
  <div class="page-container">
    <h2 class="page-title">【 M得意先 】</h2>

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

        <component :is="得意先一覧テーブル" ref="得意先一覧テーブルRef" />
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
.btn-primary { background-color: #007bff; color: white; }
.btn-primary:hover { background-color: #0056b3; }
.btn-success { background-color: #28a745; color: white; }
.btn-success:hover { background-color: #1e7e34; }
.message {
  padding: 10px;
  border-radius: 0;
  flex: 1;
  min-width: 220px;
}
.message-success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
.message-error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
<\/style>
`, { encoding: 'utf-8' })
console.log('[OK] ファイル作成: M得意先一覧.vue')

// M得意先編集.vue
writeFileSync(resolve(dir, 'M得意先編集.vue'), `\
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
import { ref, onMounted, reactive, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import apiClient from '../../../api/client';
import { qConfirm } from '../../../utils/qAlert';

const route = useRoute();
const router = useRouter();

const mode = ref('edit');
const activeTab = ref('content');
const detailData = ref(null);
const message = ref('');
const messageType = ref('success');

const form = reactive({
  得意先ID: '',
  得意先名: '',
  得意先備考: ''
});

const errors = reactive({
  得意先ID: '',
  得意先名: '',
  得意先備考: ''
});

const touched = reactive({
  得意先ID: false,
  得意先名: false,
  得意先備考: false
});

const isCreateMode = computed(() => mode.value === 'create');
const isEditMode = computed(() => mode.value === 'edit');
const isViewMode = computed(() => mode.value === 'view');
const requiredFields = computed(() => ['得意先ID', '得意先名']);

const showMessage = (text, type = 'success') => {
  message.value = text;
  messageType.value = type;
};

const resetValidation = () => {
  Object.keys(errors).forEach((key) => { errors[key] = ''; });
  Object.keys(touched).forEach((key) => { touched[key] = false; });
};

const resetForm = () => {
  form.得意先ID = '';
  form.得意先名 = '';
  form.得意先備考 = '';
};

const applyDataToForm = (data) => {
  form.得意先ID = data?.得意先ID || '';
  form.得意先名 = data?.得意先名 || '';
  form.得意先備考 = data?.得意先備考 || '';
};

const validateField = (field, showMsg = true) => {
  const value = String(form[field] ?? '').trim();
  if (!requiredFields.value.includes(field)) { errors[field] = ''; return true; }
  if (!value) { errors[field] = showMsg ? \`\${field}は必須です。\` : 'ERROR'; return false; }
  errors[field] = '';
  return true;
};

const handleBlur = (field) => { touched[field] = true; validateField(field); };
const handleInput = (field) => { if (touched[field]) validateField(field); };

const validateForm = () => {
  let isValid = true;
  let firstErrorField = null;
  requiredFields.value.forEach((field) => {
    touched[field] = true;
    if (!validateField(field, false)) {
      isValid = false;
      if (!firstErrorField) firstErrorField = field;
    }
  });
  if (firstErrorField) {
    const fieldMap = { '得意先ID': 'form-client-id', '得意先名': 'form-client-name' };
    const el = document.getElementById(fieldMap[firstErrorField]);
    if (el) el.focus();
  }
  return isValid;
};

const loadDetail = async (clientId) => {
  message.value = '';
  try {
    const res = await apiClient.post('/apps/M得意先/取得', { 得意先ID: String(clientId) });
    if (res.data.status === 'OK' && res.data.data) {
      detailData.value = res.data.data;
      applyDataToForm(res.data.data);
    } else {
      showMessage(res.data.message || '得意先情報の取得に失敗しました。', 'error');
    }
  } catch (e) {
    showMessage('得意先情報の取得でエラーが発生しました。', 'error');
  }
};

const applyQueryParams = async (query) => {
  message.value = '';
  resetValidation();
  activeTab.value = 'content';
  if (query.モード === '新規') {
    mode.value = 'create'; detailData.value = null; resetForm(); return;
  }
  if (query.モード === '表示' && query.得意先ID) {
    mode.value = 'view'; await loadDetail(query.得意先ID); return;
  }
  if (query.得意先ID) {
    mode.value = 'edit'; await loadDetail(query.得意先ID); return;
  }
  mode.value = 'create'; detailData.value = null; resetForm();
};

const backToList = () => { router.push({ path: '/Mマスタ/M得意先/一覧' }); };

const saveData = async () => {
  message.value = '';
  if (!validateForm()) { showMessage('入力内容を確認してください。', 'error'); activeTab.value = 'content'; return; }
  try {
    let res;
    if (isCreateMode.value) {
      res = await apiClient.post('/apps/M得意先/登録', {
        得意先ID: form.得意先ID, 得意先名: form.得意先名, 得意先備考: form.得意先備考
      });
    } else {
      res = await apiClient.post('/apps/M得意先/変更', {
        得意先ID: form.得意先ID, 得意先名: form.得意先名, 得意先備考: form.得意先備考
      });
    }
    if (res.data.status === 'OK') {
      router.push({ path: '/Mマスタ/M得意先/一覧', query: { message: res.data.message, type: 'success' } });
    } else {
      showMessage(res.data.message || (isCreateMode.value ? '登録に失敗しました。' : '更新に失敗しました。'), 'error');
    }
  } catch (e) {
    showMessage(isCreateMode.value ? '登録に失敗しました。' : '更新に失敗しました。', 'error');
  }
};

const deleteData = async () => {
  if (!form.得意先ID) return;
  const confirmed = await qConfirm(\`M得意先「\${form.得意先ID}」を削除しますか？この操作は取り消せません。\`);
  if (!confirmed) return;
  try {
    const res = await apiClient.post('/apps/M得意先/削除', { 得意先ID: form.得意先ID });
    if (res.data.status === 'OK') {
      router.push({ path: '/Mマスタ/M得意先/一覧', query: { message: res.data.message, type: 'success' } });
    } else {
      showMessage(res.data.message || '削除に失敗しました。', 'error');
    }
  } catch (e) {
    showMessage('削除に失敗しました。', 'error');
  }
};

onMounted(async () => { await applyQueryParams(route.query); });
watch(() => route.query, async (query) => { await applyQueryParams(query); });
<\/script>

<template>
  <div class="page-container">
    <h2 class="page-title">【 M得意先 】</h2>

    <div class="content">
      <div class="section">
        <div class="toolbar">
          <button class="btn btn-secondary" @click="backToList">一覧に戻る</button>
          <div
            v-if="message"
            :class="['message', messageType === 'error' ? 'message-error' : 'message-success']"
          >
            {{ message }}
          </div>
        </div>

        <form class="detail-form" @submit.prevent="saveData">
          <div class="tab-header">
            <button type="button" class="tab-btn" :class="{ active: activeTab === 'content' }" @click="activeTab = 'content'">内容</button>
            <button type="button" class="tab-btn" :class="{ active: activeTab === 'others' }" @click="activeTab = 'others'">その他</button>
          </div>

          <div class="detail-panel">
            <template v-if="activeTab === 'content'">
              <div class="detail-row row-id">
                <div class="detail-label">得意先ID<span class="required-mark">*</span></div>
                <div class="detail-value">
                  <div class="value-column">
                    <div class="input-wrap">
                      <input
                        id="form-client-id"
                        type="text"
                        v-model="form.得意先ID"
                        :readonly="!isCreateMode || isViewMode"
                        class="detail-input id-input"
                        :class="{ 'input-error': errors.得意先ID }"
                        @blur="handleBlur('得意先ID')"
                        @input="handleInput('得意先ID')"
                      />
                      <span v-if="errors.得意先ID" class="input-alert">!</span>
                    </div>
                    <div v-if="errors.得意先ID && errors.得意先ID !== 'ERROR'" class="field-error">{{ errors.得意先ID }}</div>
                  </div>
                </div>
              </div>

              <div class="detail-row row-name">
                <div class="detail-label">得意先名<span class="required-mark">*</span></div>
                <div class="detail-value">
                  <div class="value-column">
                    <div class="input-wrap">
                      <input
                        id="form-client-name"
                        type="text"
                        v-model="form.得意先名"
                        class="detail-input name-input"
                        :class="{ 'input-error': errors.得意先名 }"
                        :readonly="isViewMode"
                        @blur="handleBlur('得意先名')"
                        @input="handleInput('得意先名')"
                      />
                      <span v-if="errors.得意先名" class="input-alert">!</span>
                    </div>
                    <div v-if="errors.得意先名 && errors.得意先名 !== 'ERROR'" class="field-error">{{ errors.得意先名 }}</div>
                  </div>
                </div>
              </div>

              <div class="detail-row row-remarks">
                <div class="detail-label">得意先備考</div>
                <div class="detail-value">
                  <div class="input-wrap">
                    <textarea
                      id="form-client-remarks"
                      v-model="form.得意先備考"
                      class="detail-textarea remarks-textarea"
                      rows="3"
                      :readonly="isViewMode"
                    ></textarea>
                  </div>
                </div>
              </div>
            </template>

            <template v-if="activeTab === 'others'">
              <div class="detail-row row-datetime">
                <div class="detail-label">登録日時</div>
                <div class="detail-value">
                  <input type="text" :value="detailData?.登録日時 || ''" class="detail-input w-2x center-input" readonly />
                </div>
              </div>
              <div class="detail-row row-user">
                <div class="detail-label">登録利用者</div>
                <div class="detail-value">
                  <input type="text" :value="detailData?.登録利用者名 || ''" class="detail-input w-2x center-input" readonly />
                </div>
              </div>
              <div class="detail-row row-terminal">
                <div class="detail-label">登録端末</div>
                <div class="detail-value">
                  <input type="text" :value="detailData?.登録端末ID || ''" class="detail-input w-2x center-input" readonly />
                </div>
              </div>
              <div class="detail-row row-datetime">
                <div class="detail-label">更新日時</div>
                <div class="detail-value">
                  <input type="text" :value="detailData?.更新日時 || ''" class="detail-input w-2x center-input" readonly />
                </div>
              </div>
              <div class="detail-row row-user">
                <div class="detail-label">更新利用者</div>
                <div class="detail-value">
                  <input type="text" :value="detailData?.更新利用者名 || ''" class="detail-input w-2x center-input" readonly />
                </div>
              </div>
              <div class="detail-row row-terminal">
                <div class="detail-label">更新端末</div>
                <div class="detail-value">
                  <input type="text" :value="detailData?.更新端末ID || ''" class="detail-input w-2x center-input" readonly />
                </div>
              </div>
            </template>
          </div>

          <div class="form-buttons" v-if="!isViewMode">
            <button type="submit" class="btn btn-success">{{ isCreateMode ? '登録' : '更新' }}</button>
            <button v-if="isEditMode" type="button" class="btn btn-danger" @click="deleteData">削除</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-container { width: 100%; height: 100%; display: flex; flex-direction: column; background: linear-gradient(135deg, #faf7f2 0%, #f5f1e8 50%, #f0ebe0 100%); }
.page-title { background: linear-gradient(135deg, #e6d5b7 0%, #dcc8a6 50%, #d2bb95 100%); margin: 0 0 5px 0; font-size: 14px; width: 100%; box-sizing: border-box; padding: 10px 20px 10px 40px; height: 35px; line-height: 20px; color: #5a4a3a; font-weight: bold; box-shadow: 0 2px 4px rgba(210, 187, 149, 0.3); }
.content { padding: 8px 20px 20px 20px; flex: 1; display: flex; flex-direction: column; min-height: 0; }
.section { margin-bottom: 0; flex: 1; display: flex; flex-direction: column; min-height: 0; }
.toolbar { margin-bottom: 8px; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.detail-form { display: flex; flex-direction: column; gap: 0; }
.tab-header { display: flex; gap: 2px; margin-bottom: 0; border-bottom: 1px solid #ccc; padding-left: 0; }
.tab-btn { padding: 8px 24px; background: #f1f1f1; border: 1px solid #ccc; border-bottom: none; cursor: pointer; font-size: 14px; color: #555; border-radius: 4px 4px 0 0; margin-bottom: -1px; position: relative; top: 1px; }
.tab-btn.active { background: #fff; color: #007bff; font-weight: bold; border-bottom: 1px solid #fff; z-index: 1; }
.tab-btn:hover:not(.active) { background: #e9e9e9; }
.detail-panel { display: flex; flex-direction: column; width: 100%; max-width: 700px; background: transparent; border: none; box-shadow: none; padding: 0; box-sizing: border-box; }
.detail-row { display: flex; width: 100%; margin-top: -1px; }
.detail-row.row-id, .detail-row.row-name, .detail-row.row-remarks, .detail-row.row-datetime, .detail-row.row-user, .detail-row.row-terminal { width: fit-content; }
.detail-label { display: flex; align-items: center; justify-content: flex-end; color: #333; font-weight: 600; text-align: right; padding: 8px 12px; border: 1px solid #b3e5fc; background: #e1f5fe; min-height: 40px; width: 160px; flex-shrink: 0; box-sizing: border-box; border-radius: 0; z-index: 1; }
.detail-value { display: flex; align-items: center; width: 100%; color: #333; padding: 4px 12px; border: 1px solid #ccc; border-left: none; background: #fff; min-height: 40px; box-sizing: border-box; border-radius: 0; }
.row-id .detail-value, .row-name .detail-value, .row-remarks .detail-value, .row-datetime .detail-value, .row-user .detail-value, .row-terminal .detail-value { width: auto; }
.value-column { width: 100%; display: flex; flex-direction: column; justify-content: center; gap: 2px; }
.detail-input { width: 100%; height: 28px; padding: 0 8px; padding-right: 26px; border: 1px solid #d1d5db; border-radius: 4px; background: #fff; font-size: 14px; box-sizing: border-box; margin: 0; }
.detail-input:focus, .detail-textarea:focus { outline: none; border-color: #007bff; box-shadow: inset 0 0 0 1px rgba(0, 123, 255, 0.2); }
.detail-input.input-error, .detail-textarea.input-error { border-color: #dc2626; background-color: #fff8f8; }
.detail-input[readonly] { color: #555; background-color: #f8f9fa; }
.id-input { width: 160px; text-align: center; }
.name-input { width: 320px; }
.center-input { text-align: center; }
.detail-textarea { height: auto; min-height: 60px; padding: 4px 8px; border: 1px solid #d1d5db; border-radius: 4px; background: #fff; font-size: 14px; box-sizing: border-box; margin: 4px 0; resize: vertical; font-family: inherit; }
.remarks-textarea { width: 320px; }
.w-2x { width: 320px !important; }
.input-wrap { position: relative; width: 100%; margin: 0; display: flex; align-items: center; }
.input-alert { position: absolute; top: 50%; right: 8px; transform: translateY(-50%); width: 18px; height: 18px; border-radius: 0; background: #dc2626; color: #fff; font-weight: 700; font-size: 12px; display: flex; align-items: center; justify-content: center; pointer-events: none; }
.field-error { font-size: 11px; color: #dc2626; line-height: 1; margin: 0; padding: 0; }
.required-mark { color: #dc2626; font-weight: 700; margin-left: 4px; }
.form-buttons { margin-top: 8px; padding-top: 8px; border-top: 1px solid #ccc; display: flex; justify-content: flex-start; gap: 10px; }
.btn { padding: 10px 20px; border: none; border-radius: 0; cursor: pointer; font-size: 14px; margin: 0; }
.btn-success { background-color: #28a745; color: white; }
.btn-success:hover { background-color: #1e7e34; }
.btn-danger { background-color: #dc3545; color: white; }
.btn-danger:hover { background-color: #c82333; }
.btn-secondary { background-color: #6c757d; color: white; }
.btn-secondary:hover { background-color: #545b62; }
.message { padding: 10px; border-radius: 5px; flex: 1; min-width: 220px; }
.message-success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
.message-error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
<\/style>
`, { encoding: 'utf-8' })
console.log('[OK] ファイル作成: M得意先編集.vue')

console.log('\n✅ M得意先 コンポーネント全ファイル作成完了！')
