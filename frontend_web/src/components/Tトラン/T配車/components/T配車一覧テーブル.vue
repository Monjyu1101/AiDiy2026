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
  車両ID: {
    type: String,
    default: ''
  },
  戻URL: {
    type: String,
    default: ''
  }
});

const 配車一覧 = ref([]);
const pageSize = ref(100);
const currentPage = ref(1);
const sortKey = ref('配車開始日時');
const sortOrder = ref('desc');
const filters = reactive({
  配車伝票ID: '',
  配車開始日時: '',
  配車終了日時: '',
  車両名: '',
  配車区分名: '',
  配車内容: '',
  更新日時: '',
  更新利用者名: ''
});
const rowKey = '配車伝票ID';
const columns: Column[] = [
  { key: '配車伝票ID', label: '配車伝票ID', width: '120px', sortable: true },
  { key: '配車開始日時', label: '開始日時', width: '160px', sortable: true, align: 'center' },
  { key: '配車終了日時', label: '終了日時', width: '160px', sortable: true, align: 'center' },
  { key: '車両名', label: '車両名', width: '150px', sortable: true },
  { key: '配車区分名', label: '配車区分', width: '120px', sortable: true },
  { key: '配車内容', label: '配車内容', width: '220px', sortable: true },
  { key: '更新日時', label: '更新日時', width: '160px', sortable: true },
  { key: '更新利用者名', label: '更新利用者名', width: '130px', sortable: true }
];

const formatDateTime = (val: string | null | undefined) => {
  if (!val) return '';
  const s = String(val);
  if (s.length >= 16) {
    return s.substring(0, 10) + ' ' + s.substring(11, 16);
  }
  return s;
};

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
    props.車両ID);
});
const filteredRows = computed(() => {
  return 配車一覧.value.filter((row) => {
    // 列フィルタのチェック
    const columnMatch = columns.every((column) => {
      const filterValue = (filters[column.key] || '').trim();
      if (!filterValue) return true;
      const cellValue = row?.[column.key] ?? '';
      return String(cellValue).toLowerCase().includes(filterValue.toLowerCase());
    });

    if (!columnMatch) return false;

    // 日付条件のチェック
    const startDate = String(row?.['配車開始日時'] ?? '').slice(0, 10);
    const endDate = String(row?.['配車終了日時'] ?? '').slice(0, 10);

    if (props.開始日付) {
      const startOk =
        (startDate && startDate >= props.開始日付) ||
        (endDate && endDate >= props.開始日付);
      if (!startOk) return false;
    }

    if (props.終了日付) {
      const endOk =
        (startDate && startDate <= props.終了日付) ||
        (endDate && endDate <= props.終了日付);
      if (!endOk) return false;
    }

    if (props.車両ID) {
      const rowVehicleId = String(row?.車両ID ?? '');
      if (rowVehicleId !== String(props.車両ID)) return false;
    }

    return true;
  });
});
const totalCount = computed(() => filteredRows.value.length);
const totalAll = computed(() => 配車一覧.value.length);
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
  const query: Record<string, any> = { モード: '編集', 配車伝票ID: row.配車伝票ID };
  if (props.戻URL) {
    query.戻URL = props.戻URL;
  }
  router.push({ path: '/Tトラン/T配車/編集', query });
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
      '/apps/V配車/一覧',
      Object.keys(payload).length ? payload : undefined
    );
    if (res.data.status === 'OK') {
      const data = res.data.data;
      const items = Array.isArray(data) ? data : data?.items ?? [];
      配車一覧.value = items;
      currentPage.value = 1;
    } else {
      setMessage(res.data.message || 'T配車一覧の取得に失敗しました。', 'error');
    }
  } catch (e) {
    setMessage('T配車一覧の取得でエラーが発生しました。', 'error');
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
      <template v-if="column.key === '配車伝票ID'">
        <a href="#" class="id-link" @click.prevent="openDetail(row)">{{ row.配車伝票ID }}</a>
      </template>
      <template v-else-if="['配車開始日時', '配車終了日時'].includes(column.key)">
        {{ formatDateTime(value) }}
      </template>
      <template v-else>
        {{ value ?? '' }}
      </template>
    </template>
  </qTublerFrame>
</template>



