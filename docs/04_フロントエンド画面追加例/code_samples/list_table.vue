<script setup lang="ts">
import { defineProps, defineEmits } from 'vue'
import qTubler from '@/components/_share/qTubler.vue'
import type { Column } from '@/types/qTubler'

defineProps<{
  items: any[]
}>()

const emit = defineEmits(['row-dblclick'])

// カラム定義（テーブルに合わせて変更）
const columns: Column[] = [
  { key: '新ID', label: '新ID', width: '150px', sortable: true },
  { key: '新名', label: '新名', width: '200px', sortable: true },
  { key: '新備考', label: '備考', width: '300px', sortable: true },
  { key: '更新日時', label: '更新日時', width: '180px', sortable: true },
]

const handleRowDblClick = (row: any) => {
  emit('row-dblclick', row)
}
</script>

<template>
  <qTubler
    :columns="columns"
    :data="items"
    :pageSize="20"
    @row-dblclick="handleRowDblClick"
  />
</template>
