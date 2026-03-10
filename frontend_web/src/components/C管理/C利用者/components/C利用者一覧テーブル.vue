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
import type { V利用者 } from '../../../../types';
import apiClient from '../../../../api/client';
import qTublerFrame from '../../../_share/qTublerFrame.vue';

const router = useRouter();

const users = ref<V利用者[]>([]);
const pageSize = ref(100);
const currentPage = ref(1);
const sortKey = ref('利用者ID');
const sortOrder = ref('asc');
const filters = reactive({
  利用者ID: '',
  利用者名: '',
  権限名: '',
  利用者備考: '',
  更新日時: '',
  更新利用者名: ''
});
const rowKey = '利用者ID';
const columns = [
  { key: '利用者ID', label: '利用者ID', width: '100px', sortable: true },
  { key: '利用者名', label: '利用者名', width: '140px', sortable: true },
  { key: '権限名', label: '権限名', width: '120px', sortable: true },
  { key: '利用者備考', label: '利用者備考', width: '250px', sortable: true },
  { key: '更新日時', label: '更新日時', width: '160px', sortable: true },
  { key: '更新利用者名', label: '更新利用者名', width: '130px', sortable: true }
];

const message = ref('');
const messageType = ref('success');

const setMessage = (text: string, type: 'success' | 'error' = 'success') => {
  message.value = text;
  messageType.value = type;
};

const hasFilter = computed(() => {
  return Object.values(filters).some((value) => String(value || '').trim() !== '');
});
const displayRows = computed(() => {
  return users.value.map((user) => ({
    ...user,
    権限名: user.権限名 || user.権限ID || ''
  }));
});
const filteredRows = computed(() => {
  return displayRows.value.filter((row) => {
    return columns.every((column) => {
      const filterValue = (filters[column.key] || '').trim();
      if (!filterValue) return true;
      const cellValue = row?.[column.key] ?? '';
      return String(cellValue).toLowerCase().includes(filterValue.toLowerCase());
    });
  });
});
const totalCount = computed(() => filteredRows.value.length);
const totalAll = computed(() => displayRows.value.length);
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
  router.push({ path: '/C管理/C利用者/編集', query: { モード: '編集', 利用者ID: row.利用者ID } });
};

// ==================================================
// 一覧データ取得
// ==================================================
const loadData = async () => {
  message.value = '';
  try {
    const res = await apiClient.post('/core/V利用者/一覧');
    if (res.data.status === 'OK') {
      const data = res.data.data;
      const items = Array.isArray(data) ? data : data?.items ?? [];
      users.value = items;
      currentPage.value = 1;
    } else {
      setMessage(res.data.message || 'C利用者一覧の取得に失敗しました。', 'error');
    }
  } catch (e) {
    setMessage('C利用者一覧の取得でエラーが発生しました。', 'error');
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
      <template v-if="column.key === '利用者ID'">
        <a href="#" class="id-link" @click.prevent="openDetail(row)">{{ row.利用者ID }}</a>
      </template>
      <template v-else>
        {{ value ?? '' }}
      </template>
    </template>
  </qTublerFrame>
</template>



