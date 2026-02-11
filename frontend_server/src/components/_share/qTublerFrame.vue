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
import { useSlots } from 'vue';
import type { PropType } from 'vue';
import qTubler from './qTubler.vue';
import type { Column } from '@/types/qTubler';

const props = defineProps({
  columns: {
    type: Array as PropType<Column[]>,
    required: true
  },
  rows: {
    type: Array,
    default: () => []
  },
  rowKey: {
    type: [String, Function],
    default: 'id'
  },
  sortKey: {
    type: String,
    default: ''
  },
  sortOrder: {
    type: String,
    default: 'asc'
  },
  message: {
    type: String,
    default: ''
  },
  messageType: {
    type: String,
    default: 'success'
  },
  hasFilter: {
    type: Boolean,
    default: false
  },
  totalCount: {
    type: Number,
    default: 0
  },
  totalAll: {
    type: Number,
    default: 0
  },
  currentPage: {
    type: Number,
    default: 1
  },
  totalPages: {
    type: Number,
    default: 1
  }
});

const emit = defineEmits(['sort', 'page']);
const slots = useSlots();

const changePage = (page: number) => {
  if (page < 1 || page > props.totalPages) return;
  emit('page', page);
};
</script>

<template>
  <div class="table-wrapper">
    <div
      v-if="message"
      :class="['message', messageType === 'error' ? 'message-error' : 'message-success']"
    >
      {{ message }}
    </div>
    <div class="table-container">
      <qTubler
        :columns="columns"
        :rows="rows"
        :rowKey="rowKey"
        :sortKey="sortKey"
        :sortOrder="sortOrder"
        @sort="emit('sort', $event)"
      >
        <template v-if="slots.filter" #filter="{ column }">
          <slot name="filter" :column="column"></slot>
        </template>
        <template v-if="slots.cell" #cell="{ row, column, value }">
          <slot name="cell" :row="row" :column="column" :value="value"></slot>
        </template>
      </qTubler>
    </div>
    <div class="table-footer">
      <div class="table-count">
        <template v-if="hasFilter">
          絞込 {{ totalCount }} 件 / 全 {{ totalAll }} 件
        </template>
        <template v-else>
          全 {{ totalAll }} 件
        </template>
      </div>
      <div class="pager">
        <button class="pager-btn" :disabled="currentPage === 1" @click="changePage(1)">
          &lt;&lt;
        </button>
        <button class="pager-btn" :disabled="currentPage === 1" @click="changePage(currentPage - 1)">
          &lt;
        </button>
        <span class="pager-current">{{ currentPage }}</span>
        <button class="pager-btn" :disabled="currentPage === totalPages" @click="changePage(currentPage + 1)">
          &gt;
        </button>
        <button class="pager-btn" :disabled="currentPage === totalPages" @click="changePage(totalPages)">
          &gt;&gt;
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.table-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.table-container {
  overflow: auto;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.table-container :deep(.common-table) {
  flex: 1;
  min-height: 100%;
}
</style>

