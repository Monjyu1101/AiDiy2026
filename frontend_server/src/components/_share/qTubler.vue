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
import type { Column } from '@/types/qTubler';

const props = defineProps({
  columns: {
    type: Array as () => Column[],
    required: true
  },
  rows: {
    type: Array as () => any[],
    default: () => []
  },
  rowKey: {
    type: [String, Function] as any,
    default: 'id'
  },
  emptyText: {
    type: String,
    default: 'データがありません。'
  },
  caption: {
    type: String,
    default: ''
  },
  sortKey: {
    type: String,
    default: ''
  },
  sortOrder: {
    type: String,
    default: 'asc'
  }
});

const emit = defineEmits(['sort']);

const resolveRowKey = (row: any, index: number): string | number => {
  if (typeof props.rowKey === 'function') {
    return props.rowKey(row, index);
  }
  if (typeof props.rowKey === 'string' && row?.[props.rowKey] !== undefined) {
    return row[props.rowKey];
  }
  return index;
};

const columnStyle = (column: Column): { width: string | undefined; textAlign: 'left' | 'right' | 'center' } => ({
  width: column.width || undefined,
  textAlign: column.align || 'left'
});

const isSortable = (column: Column): boolean => column.sortable !== false;

const handleSort = (column: Column) => {
  if (!isSortable(column)) return;
  emit('sort', column);
};
</script>

<template>
  <div class="common-table">
    <table>
      <caption v-if="caption">{{ caption }}</caption>
      <thead>
        <tr>
          <th v-for="column in columns" :key="column.key" :style="columnStyle(column)">
            <button
              v-if="isSortable(column)"
              type="button"
              class="sort-button"
              @click="handleSort(column)"
            >
              <span>{{ column.label }}</span>
              <span v-if="sortKey === column.key" class="sort-indicator">
                {{ sortOrder === 'desc' ? '▼' : '▲' }}
              </span>
              <span v-else class="sort-indicator sort-indicator-muted">↕</span>
            </button>
            <span v-else>{{ column.label }}</span>
          </th>
          <th class="dummy-column"></th>
        </tr>
        <tr v-if="$slots.filter">
          <th v-for="column in columns" :key="column.key" :style="columnStyle(column)">
            <slot name="filter" :column="column"></slot>
          </th>
          <th class="dummy-column"></th>
        </tr>
      </thead>
      <tbody v-if="rows.length">
        <tr v-for="(row, index) in rows" :key="resolveRowKey(row, index)">
          <td v-for="column in columns" :key="column.key" :style="columnStyle(column)">
            <slot name="cell" :row="row" :column="column" :value="row[column.key]">
              {{ row[column.key] ?? '' }}
            </slot>
          </td>
          <td class="dummy-column"></td>
        </tr>
      </tbody>
      <tbody v-else>
        <tr>
          <td class="empty" :colspan="columns.length + 1">{{ emptyText }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.common-table {
  width: 100%;
  border: 1px solid #cbd5e1;
  border-radius: 0;
  overflow: auto;
  box-shadow: none;
  background-color: #f1f5f9;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  color: #1e293b;
  background-color: transparent;
}

caption {
  text-align: left;
  padding: 8px;
  font-weight: bold;
  font-size: 14px;
}

th,
td {
  padding: 6px 10px;
  border-bottom: 1px solid #e2e8f0;
  border-right: 1px solid #e5e7eb;
  vertical-align: middle;
  white-space: nowrap;
}

.dummy-column {
  width: auto;
  padding: 0;
  border-right: none !important;
  pointer-events: none;
}

th:last-child,
td:last-child {
  border-right: none;
}

th {
  background: #37474f;
  color: #fff;
  font-weight: 600;
  letter-spacing: 0.02em;
  font-size: 13px;
  line-height: 1.2;
  border-color: #263238;
}

thead th {
  padding: 2px 10px;
  height: auto;
  border-bottom: none;
}

thead tr:first-child th {
  padding-top: 4px;
  padding-bottom: 0;
}

thead tr:nth-child(2) th {
  padding: 0 10px 2px 10px;
  background: #37474f;
  border-bottom: 2px solid #263238;
}

.sort-button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0;
  border: 0;
  background: transparent;
  font: inherit;
  color: #fff;
  cursor: pointer;
  transition: color 0.15s;
}

.sort-button:hover {
  color: #b0bec5;
}

.sort-indicator {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.8);
  transition: color 0.15s;
}

.sort-button:hover .sort-indicator {
  color: #fff;
}

.sort-indicator-muted {
  opacity: 0.4;
}

tbody tr:nth-child(even) {
  background: #f9fafb;
}

tbody tr:hover {
  background: #e0f2fe;
  transition: background 0.15s;
}

tbody tr {
  border-bottom: 1px solid #f1f5f9;
  background-color: #fff;
}

tbody td {
  color: #475569;
}

.empty {
  text-align: center;
  padding: 40px 20px;
  color: #94a3b8;
  font-size: 14px;
}
</style>

<style>
/* 共通テーブルフッタースタイル */
.table-footer {
  margin-top: 0;
  padding: 5px 6px;
  background: #37474f;
  border: 1px solid #263238;
  border-top: 0;
  border-radius: 0;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  font-size: 12px;
  color: #fff;
  flex-shrink: 0;
}

.table-count {
  min-width: 160px;
}

.pager {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}

.pager-btn {
  min-width: 34px;
  padding: 6px 10px;
  border: 1px solid #546e7a;
  background: #546e7a;
  color: #fff;
  font-size: 12px;
  border-radius: 0;
  cursor: pointer;
}

.pager-btn:hover {
  background: #607d8b;
}

.pager-btn.active {
  background: #263238;
  color: #fff;
  border-color: #263238;
}

.pager-btn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.pager-current {
  min-width: 32px;
  text-align: center;
  font-weight: 600;
  color: #fff;
}

/* 共通フィルター入力スタイル */
.filter-input {
  display: block;
  width: 100%;
  padding: 2px 6px;
  border: 1px solid #cbd5e1;
  border-radius: 0;
  margin: 0;
  font-size: 13px;
  background: #fff;
  line-height: 1.2;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.filter-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.filter-input::placeholder {
  color: #94a3b8;
}

/* 共通IDリンクスタイル */
.id-link {
  color: #2563eb;
  text-decoration: none;
  font-weight: 600;
  transition: color 0.15s;
}

.id-link:hover {
  color: #1d4ed8;
  text-decoration: underline;
}

/* 共通メッセージスタイル */
.message {
  padding: 10px;
  border-radius: 0;
  margin-bottom: 10px;
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

