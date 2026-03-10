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
const normalizeQueryValue = (value: any): string | null => (Array.isArray(value) ? value[0] : value);
const toHalfwidthUrl = (value: string): string => value.replace(/？/g, '?').replace(/＆/g, '&').replace(/＝/g, '=');
const 戻URL = computed(() => {
  const value = normalizeQueryValue(route.query.戻URL);
  return value ? String(value) : '';
});

// ==================================================
// 状態管理
// ==================================================
const mode = ref('edit');
const activeTab = ref('content');
const detailData = ref(null);
const message = ref('');
const messageType = ref('success');

const form = reactive({
  棚卸伝票ID: '',
  棚卸日: '',
  商品ID: '',
  実棚数量: '',
  棚卸備考: ''
});

const errors = reactive({
  棚卸日: '',
  商品ID: '',
  実棚数量: ''
});

const touched = reactive({
  棚卸日: false,
  商品ID: false,
  実棚数量: false
});

const 商品一覧 = ref([]);

// ==================================================
// 計算プロパティ
// ==================================================
const isCreateMode = computed(() => mode.value === 'create');
const isEditMode = computed(() => mode.value === 'edit');
const isViewMode = computed(() => mode.value === 'view');
const requiredFields = computed(() => ['棚卸日', '商品ID', '実棚数量']);

// ==================================================
// ユーティリティ関数
// ==================================================
const showMessage = (text: string, type: string = 'success') => {
  message.value = text;
  messageType.value = type;
};

const resetValidation = () => {
  Object.keys(errors).forEach((key) => {
    errors[key] = '';
  });
  Object.keys(touched).forEach((key) => {
    touched[key] = false;
  });
};

const resetForm = () => {
  form.棚卸伝票ID = '';
  form.棚卸日 = '';
  form.商品ID = '';
  form.実棚数量 = '';
  form.棚卸備考 = '';
};

const applyDataToForm = (data) => {
  form.棚卸伝票ID = data?.棚卸伝票ID || '';
  form.棚卸日 = data?.棚卸日 || '';
  form.商品ID = data?.商品ID || '';
  form.実棚数量 = data?.実棚数量 || '';
  form.棚卸備考 = data?.棚卸備考 || '';
};

// ==================================================
// バリデーション
// ==================================================
const validateField = (field, showMessage = true) => {
  const value = String(form[field] ?? '').trim();

  if (!requiredFields.value.includes(field)) {
    errors[field] = '';
    return true;
  }
  if (!value) {
    errors[field] = showMessage ? `${field}は必須です。` : 'ERROR';
    return false;
  }

  errors[field] = '';
  return true;
};

const handleBlur = (field) => {
  touched[field] = true;
  validateField(field);
};

const handleInput = (field) => {
  if (touched[field]) {
    validateField(field);
  }
};

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
    const fieldMap = {
      '棚卸日': 'form-date',
      '商品ID': 'form-product-id',
      '実棚数量': 'form-quantity'
    };
    const elementId = fieldMap[firstErrorField];
    if (elementId) {
      const element = document.getElementById(elementId);
      if (element) element.focus();
    }
  }

  return isValid;
};

// ==================================================
// マスターデータ取得
// ==================================================
const loadMasterData = async () => {
  try {
    const res = await apiClient.post('/apps/M商品/一覧');

    if (res.data.status === 'OK') {
      const data = res.data.data;
      商品一覧.value = Array.isArray(data) ? data : data?.items ?? [];
    }
  } catch (e) {
    showMessage('マスターデータの取得でエラーが発生しました。', 'error');
  }
};

// ==================================================
// 詳細データ取得
// ==================================================
const loadDetail = async (id) => {
  message.value = '';
  try {
    const res = await apiClient.post('/apps/T商品棚卸/取得', { 棚卸伝票ID: String(id) });
    if (res.data.status === 'OK' && res.data.data) {
      detailData.value = res.data.data;
      applyDataToForm(res.data.data);
    } else {
      showMessage(res.data.message || '商品棚卸情報の取得に失敗しました。', 'error');
    }
  } catch (e) {
    showMessage('商品棚卸情報の取得でエラーが発生しました。', 'error');
  }
};

// ==================================================
// ルーティング処理
// ==================================================
const applyQueryParams = async (query: any) => {
  message.value = '';
  resetValidation();
  activeTab.value = 'content';

  if (query.モード === '新規') {
    mode.value = 'create';
    detailData.value = null;
    resetForm();

    // デフォルト値設定（今日の日付）
    const now = new Date();
    form.棚卸日 = now.toISOString().slice(0, 10);
    const queryDate = normalizeQueryValue(query.棚卸日);
    const queryProductId = normalizeQueryValue(query.商品ID);
    if (queryDate) {
      form.棚卸日 = String(queryDate);
    }
    if (queryProductId) {
      form.商品ID = String(queryProductId);
    }
    return;
  }

  if (query.モード === '表示' && query.棚卸伝票ID) {
    mode.value = 'view';
    await loadDetail(query.棚卸伝票ID);
    return;
  }

  if (query.棚卸伝票ID) {
    mode.value = 'edit';
    await loadDetail(query.棚卸伝票ID);
    return;
  }

  mode.value = 'create';
  detailData.value = null;
  resetForm();
};

const buildListQuery = (extra = {}) => {
  const query: Record<string, any> = { ...extra };
  if (戻URL.value) {
    query.戻URL = 戻URL.value;
  }
  return Object.keys(query).length ? query : undefined;
};

const handleSuccess = (messageText) => {
  if (戻URL.value) {
    router.push(toHalfwidthUrl(戻URL.value));
    return;
  }
  router.push({
    path: '/Tトラン/T商品棚卸/一覧',
    query: buildListQuery({ message: messageText, type: 'success' })
  });
};

const backToList = () => {
  router.push({ path: '/Tトラン/T商品棚卸/一覧', query: buildListQuery() });
};

const handleReturn = () => {
  if (!戻URL.value) return;
  router.push(toHalfwidthUrl(戻URL.value));
};

// ==================================================
// CRUD操作
// ==================================================
const saveData = async () => {
  message.value = '';
  if (!validateForm()) {
    showMessage('入力内容を確認してください。', 'error');
    activeTab.value = 'content';
    return;
  }
  try {
    let res;
    if (isCreateMode.value) {
      // 新規作成時は棚卸伝票IDを送らない（自動採番）
      res = await apiClient.post('/apps/T商品棚卸/登録', {
        棚卸日: form.棚卸日,
        商品ID: form.商品ID,
        実棚数量: Number(form.実棚数量),
        棚卸備考: form.棚卸備考
      });
    } else {
      res = await apiClient.post('/apps/T商品棚卸/変更', {
        棚卸日: form.棚卸日,
        商品ID: form.商品ID,
        実棚数量: Number(form.実棚数量),
        棚卸備考: form.棚卸備考
      }, {
        params: { 棚卸伝票ID: form.棚卸伝票ID }
      });
    }

    if (res.data.status === 'OK') {
      handleSuccess(res.data.message);
    } else {
      showMessage(res.data.message || (isCreateMode.value ? '登録に失敗しました。' : '更新に失敗しました。'), 'error');
    }
  } catch (e) {
    showMessage(isCreateMode.value ? '登録に失敗しました。' : '更新に失敗しました。', 'error');
  }
};

const deleteData = async () => {
  if (!form.棚卸伝票ID) return;

  const confirmed = await qConfirm(`T商品棚卸「${form.棚卸伝票ID}」を削除しますか？この操作は取り消せません。`);
  if (!confirmed) return;

  try {
    const res = await apiClient.post('/apps/T商品棚卸/削除', { 棚卸伝票ID: form.棚卸伝票ID });
    if (res.data.status === 'OK') {
      handleSuccess(res.data.message);
    } else {
      showMessage(res.data.message || '削除に失敗しました。', 'error');
    }
  } catch (e) {
    showMessage('削除に失敗しました。', 'error');
  }
};

// ==================================================
// 初期化
// ==================================================
onMounted(async () => {
  await loadMasterData();
  await applyQueryParams(route.query);
});

watch(() => route.query, async (query) => {
  await applyQueryParams(query);
});
</script>

<template>
  <div class="page-container">
    <h2 class="page-title">
      <span class="title-text">【 T商品棚卸 】{{ isCreateMode ? '新規登録' : '編集' }}</span>
      <button v-if="戻URL" class="btn-return" @click="handleReturn">戻る</button>
    </h2>

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
            <button
              type="button"
              class="tab-btn"
              :class="{ active: activeTab === 'content' }"
              @click="activeTab = 'content'"
            >
              内容
            </button>
            <button
              type="button"
              class="tab-btn"
              :class="{ active: activeTab === 'others' }"
              @click="activeTab = 'others'"
            >
              その他
            </button>
          </div>

          <div class="detail-panel">
            <template v-if="activeTab === 'content'">
              <div v-if="!isCreateMode" class="detail-row row-id">
                <div class="detail-label">棚卸伝票ID</div>
                <div class="detail-value">
                  <input
                    type="text"
                    v-model="form.棚卸伝票ID"
                    class="detail-input id-input center-input"
                    readonly
                  />
                </div>
              </div>

              <div class="detail-row row-date">
                <div class="detail-label">棚卸日<span class="required-mark">*</span></div>
                <div class="detail-value">
                  <div class="value-column">
                    <div class="input-wrap">
                      <input
                        id="form-date"
                        type="date"
                        v-model="form.棚卸日"
                        class="detail-input date-input"
                        :class="{ 'input-error': errors.棚卸日 }"
                        :readonly="isViewMode"
                        @blur="handleBlur('棚卸日')"
                        @input="handleInput('棚卸日')"
                      />
                      <span v-if="errors.棚卸日" class="input-alert">!</span>
                    </div>
                    <div v-if="errors.棚卸日 && errors.棚卸日 !== 'ERROR'" class="field-error">{{ errors.棚卸日 }}</div>
                  </div>
                </div>
              </div>

              <div class="detail-row row-select">
                <div class="detail-label">商品<span class="required-mark">*</span></div>
                <div class="detail-value">
                  <div class="value-column">
                    <div class="input-wrap">
                      <select
                        id="form-product-id"
                        v-model="form.商品ID"
                        class="detail-input select-input"
                        :class="{ 'input-error': errors.商品ID }"
                        :disabled="isViewMode"
                        @blur="handleBlur('商品ID')"
                        @change="handleInput('商品ID')"
                      >
                        <option value="">選択してください</option>
                        <option v-for="item in 商品一覧" :key="item.商品ID" :value="item.商品ID">
                          {{ item.商品名 }} ({{ item.商品ID }})
                        </option>
                      </select>
                      <span v-if="errors.商品ID" class="input-alert">!</span>
                    </div>
                    <div v-if="errors.商品ID && errors.商品ID !== 'ERROR'" class="field-error">{{ errors.商品ID }}</div>
                  </div>
                </div>
              </div>

              <div class="detail-row row-number">
                <div class="detail-label">実棚数量<span class="required-mark">*</span></div>
                <div class="detail-value">
                  <div class="value-column">
                    <div class="input-wrap">
                      <input
                        id="form-quantity"
                        type="number"
                        v-model="form.実棚数量"
                        class="detail-input number-input"
                        :class="{ 'input-error': errors.実棚数量 }"
                        :readonly="isViewMode"
                        @blur="handleBlur('実棚数量')"
                        @input="handleInput('実棚数量')"
                      />
                      <span v-if="errors.実棚数量" class="input-alert">!</span>
                    </div>
                    <div v-if="errors.実棚数量 && errors.実棚数量 !== 'ERROR'" class="field-error">{{ errors.実棚数量 }}</div>
                  </div>
                </div>
              </div>

              <div class="detail-row row-remarks">
                <div class="detail-label">棚卸備考</div>
                <div class="detail-value">
                  <div class="input-wrap">
                    <textarea
                      v-model="form.棚卸備考"
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
                  <input
                    type="text"
                    :value="detailData?.登録日時 || ''"
                    class="detail-input w-2x center-input"
                    readonly
                  />
                </div>
              </div>
              <div class="detail-row row-user">
                <div class="detail-label">登録利用者</div>
                <div class="detail-value">
                  <input
                    type="text"
                    :value="detailData?.登録利用者名 || ''"
                    class="detail-input w-2x center-input"
                    readonly
                  />
                </div>
              </div>
              <div class="detail-row row-terminal">
                <div class="detail-label">登録端末</div>
                <div class="detail-value">
                  <input
                    type="text"
                    :value="detailData?.登録端末ID || ''"
                    class="detail-input w-2x center-input"
                    readonly
                  />
                </div>
              </div>
              <div class="detail-row row-datetime">
                <div class="detail-label">更新日時</div>
                <div class="detail-value">
                  <input
                    type="text"
                    :value="detailData?.更新日時 || ''"
                    class="detail-input w-2x center-input"
                    readonly
                  />
                </div>
              </div>
              <div class="detail-row row-user">
                <div class="detail-label">更新利用者</div>
                <div class="detail-value">
                  <input
                    type="text"
                    :value="detailData?.更新利用者名 || ''"
                    class="detail-input w-2x center-input"
                    readonly
                  />
                </div>
              </div>
              <div class="detail-row row-terminal">
                <div class="detail-label">更新端末</div>
                <div class="detail-value">
                  <input
                    type="text"
                    :value="detailData?.更新端末ID || ''"
                    class="detail-input w-2x center-input"
                    readonly
                  />
                </div>
              </div>
            </template>
          </div>

          <div class="form-buttons" v-if="!isViewMode">
            <button type="submit" class="btn btn-success">
              {{ isCreateMode ? '登録' : '更新' }}
            </button>
            <button v-if="isEditMode" type="button" class="btn btn-danger" @click="deleteData">削除</button>
          </div>
        </form>
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
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.detail-form {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.tab-header {
  display: flex;
  gap: 2px;
  margin-bottom: 0;
  border-bottom: 1px solid #ccc;
  padding-left: 0;
}

.tab-btn {
  padding: 8px 24px;
  background: #f1f1f1;
  border: 1px solid #ccc;
  border-bottom: none;
  cursor: pointer;
  font-size: 14px;
  color: #555;
  border-radius: 4px 4px 0 0;
  margin-bottom: -1px;
  position: relative;
  top: 1px;
}

.tab-btn.active {
  background: #fff;
  color: #007bff;
  font-weight: bold;
  border-bottom: 1px solid #fff;
  z-index: 1;
}

.tab-btn:hover:not(.active) {
  background: #e9e9e9;
}

.detail-panel {
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 700px;
  background: transparent;
  border: none;
  box-shadow: none;
  padding: 0;
  box-sizing: border-box;
}

.detail-row {
  display: flex;
  width: 100%;
  margin-top: -1px;
}

.row-remarks + .row-remarks {
  margin-top: 0;
}

.detail-row.row-id,
.detail-row.row-date,
.detail-row.row-select,
.detail-row.row-number,
.detail-row.row-remarks,
.detail-row.row-datetime,
.detail-row.row-user,
.detail-row.row-terminal {
  width: fit-content;
}

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
  border-radius: 0;
  z-index: 1;
}

.detail-value {
  display: flex;
  align-items: center;
  width: 100%;
  color: #333;
  padding: 4px 12px;
  border: 1px solid #ccc;
  border-left: none;
  background: #fff;
  min-height: 40px;
  box-sizing: border-box;
  border-radius: 0;
}

.row-id .detail-value,
.row-date .detail-value,
.row-select .detail-value,
.row-number .detail-value,
.row-remarks .detail-value,
.row-datetime .detail-value,
.row-user .detail-value,
.row-terminal .detail-value {
  width: auto;
}

.value-column {
  width: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 2px;
}

.detail-input {
  width: 100%;
  height: 28px;
  padding: 0 8px;
  padding-right: 26px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  background: #fff;
  font-size: 14px;
  box-sizing: border-box;
  margin: 0;
}

.detail-input:focus,
.detail-textarea:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: inset 0 0 0 1px rgba(0, 123, 255, 0.2);
}

.detail-input.input-error,
.detail-textarea.input-error {
  border-color: #dc2626;
  background-color: #fff8f8;
}

.detail-input.input-error:focus {
  border-color: #dc2626;
  box-shadow: inset 0 0 0 1px rgba(220, 38, 38, 0.2);
}

.detail-input[readonly],
.detail-input[disabled] {
  color: #555;
  background-color: #f8f9fa;
}

.id-input {
  width: 160px;
  text-align: center;
}

.date-input {
  width: 180px;
}

.select-input {
  width: 320px;
  padding-right: 8px;
}

.number-input {
  width: 120px;
  text-align: right;
}

.remarks-textarea {
  width: 320px;
}

.detail-textarea {
  height: auto;
  min-height: 60px;
  padding: 4px 8px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  background: #fff;
  font-size: 14px;
  box-sizing: border-box;
  margin: 4px 0;
  resize: vertical;
  font-family: inherit;
}

.center-input {
  text-align: center;
}

.w-2x {
  width: 320px !important;
}

.input-wrap {
  position: relative;
  width: 100%;
  margin: 0;
  display: flex;
  align-items: center;
}

.input-alert {
  position: absolute;
  top: 50%;
  right: 8px;
  transform: translateY(-50%);
  width: 18px;
  height: 18px;
  border-radius: 0;
  background: #dc2626;
  color: #fff;
  font-weight: 700;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.field-error {
  font-size: 11px;
  color: #dc2626;
  line-height: 1;
  margin: 0;
  padding: 0;
}

.required-mark {
  color: #dc2626;
  font-weight: 700;
  margin-left: 4px;
}

.form-buttons {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #ccc;
  display: flex;
  justify-content: flex-start;
  gap: 10px;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 0;
  cursor: pointer;
  font-size: 14px;
  margin: 0;
}

.btn-success {
  background-color: #28a745;
  color: white;
}

.btn-success:hover {
  background-color: #1e7e34;
}

.btn-danger {
  background-color: #dc3545;
  color: white;
}

.btn-danger:hover {
  background-color: #c82333;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background-color: #545b62;
}

.message {
  padding: 10px;
  border-radius: 5px;
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

@media (max-width: 720px) {
  .detail-panel {
    max-width: 100%;
    grid-template-columns: 1fr;
    row-gap: 4px;
    padding: 8px;
  }

  .detail-row {
    display: contents;
  }

  .detail-value {
    width: 100%;
    padding: 2px 12px;
    align-items: center;
  }

  .detail-label {
    width: 100%;
    text-align: left;
    justify-content: flex-start;
    border-right: none;
  }
}
</style>

