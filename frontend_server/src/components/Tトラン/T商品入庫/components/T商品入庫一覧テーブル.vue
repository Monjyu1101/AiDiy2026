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
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import apiClient from '../../../../api/client';
import qTublerFrame from '../../../_share/qTublerFrame.vue';
import type { Column } from '../../../../types/qTubler';

const router = useRouter();

const props = defineProps({
  開始日付: {
    type: String,
    default: ''
  },
  終了日付: {
    type: String,
    default: ''
  },
  商品ID: {
    type: String,
    default: ''
  },
  戻URL: {
    type: String,
    default: ''
  }
});

const 商品入庫一覧 = ref([]);
const pageSize = ref(100);
const currentPage = ref(1);
const sortKey = ref('入庫日');
const sortOrder = ref('desc');
const filters = reactive({
  入庫伝票ID: '',
  入庫日: '',
  商品名: '',
  入庫数量: '',
  入庫備考: '',
  更新日時: '',
  更新利用者名: ''
});
const rowKey = '入庫伝票ID';
const columns: Column[] = [
  { key: '入庫伝票ID', label: '入庫伝票ID', width: '120px', sortable: true },
  { key: '入庫日', label: '入庫日', width: '120px', sortable: true, align: 'center' },
  { key: '商品名', label: '商品名', width: '150px', sortable: true },
  { key: '入庫数量', label: '入庫数量', width: '100px', sortable: true, align: 'right' },
  { key: '入庫備考', label: '入庫備考', width: '220px', sortable: true },
  { key: '更新日時', label: '更新日時', width: '160px', sortable: true },
  { key: '更新利用者名', label: '更新利用者名', width: '130px', sortable: true }
];

const message = ref('');
const messageType = ref('success');

const setMessage = (text, type = 'success') => {
  message.value = text;
  messageType.value = type;
};

const hasFilter = computed((): boolean => {
  return Boolean(Object.values(filters).some((value) => String(value || '').trim() !== '') ||
    props.開始日付 ||
    props.終了日付 ||
    props.商品ID);
});
const filteredRows = computed(() => {
  return 商品入庫一覧.value.filter((row) => {
    // 列フィルタのチェック
    const columnMatch = columns.every((column) => {
      const filterValue = (filters[column.key] || '').trim();
      if (!filterValue) return true;
      const cellValue = row?.[column.key] ?? '';
      return String(cellValue).toLowerCase().includes(filterValue.toLowerCase());
    });

    if (!columnMatch) return false;

    // 日付条件のチェック
    const rowDate = String(row?.['入庫日'] ?? '').slice(0, 10);

    if (props.開始日付) {
      if (!rowDate || rowDate < props.開始日付) return false;
    }

    if (props.終了日付) {
      if (!rowDate || rowDate > props.終了日付) return false;
    }

    if (props.商品ID) {
      const rowProductId = String(row?.商品ID ?? '');
      if (rowProductId !== String(props.商品ID)) return false;
    }

    return true;
  });
});
const totalCount = computed(() => filteredRows.value.length);
const totalAll = computed(() => 商品入庫一覧.value.length);
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
  const query: Record<string, any> = { モード: '編集', 入庫伝票ID: row.入庫伝票ID };
  if (props.戻URL) {
    query.戻URL = props.戻URL;
  }
  router.push({ path: '/Tトラン/T商品入庫/編集', query });
};

// ==================================================
// 一覧データ取得
// ==================================================
const loadData = async () => {
  message.value = '';
  try {
    const payload: Record<string, string> = {};
    if (props.開始日付) payload.開始日付 = String(props.開始日付);
    if (props.終了日付) payload.終了日付 = String(props.終了日付);
    const res = await apiClient.post(
      '/apps/V商品入庫/一覧',
      Object.keys(payload).length ? payload : undefined
    );
    if (res.data.status === 'OK') {
      const data = res.data.data;
      const items = Array.isArray(data) ? data : data?.items ?? [];
      商品入庫一覧.value = items;
      currentPage.value = 1;
    } else {
      setMessage(res.data.message || 'T商品入庫一覧の取得に失敗しました。', 'error');
    }
  } catch (e) {
    setMessage('T商品入庫一覧の取得でエラーが発生しました。', 'error');
  }
};

// ==================================================
// 初期化
// ==================================================
onMounted(async () => {
  await loadData();
});

defineExpose({
  loadData
});
</script>

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
      <template v-if="column.key === '入庫伝票ID'">
        <a href="#" class="id-link" @click.prevent="openDetail(row)">{{ row.入庫伝票ID }}</a>
      </template>
      <template v-else>
        {{ value ?? '' }}
      </template>
    </template>
  </qTublerFrame>
</template>

