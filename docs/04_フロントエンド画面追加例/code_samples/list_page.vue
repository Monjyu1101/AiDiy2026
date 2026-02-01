<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '@/api/client'
import C新テーブル一覧テーブル from './components/C新テーブル一覧テーブル.vue'
import { qAlert } from '@/utils/qAlert'

const router = useRouter()
const items = ref<any[]>([])
const loading = ref(false)

const fetchItems = async () => {
  loading.value = true
  try {
    const response = await apiClient.post('/core/C新テーブル/一覧')
    if (response.data.status === 'OK') {
      items.value = response.data.data.items
    }
  } catch (error) {
    console.error(error)
    await qAlert('データの取得に失敗しました')
  } finally {
    loading.value = false
  }
}

const handleEdit = (row: any) => {
  router.push({ path: '/C管理/C新テーブル/編集', query: { 新ID: row.新ID } })
}

const handleNew = () => {
  router.push('/C管理/C新テーブル/編集')
}

onMounted(() => {
  fetchItems()
})
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h1>C新テーブル一覧</h1>
      <button @click="handleNew" class="btn-primary">新規作成</button>
    </div>

    <div v-if="loading" class="loading">読込中...</div>

    <!-- 日本語タグは使えないので component :is を使う -->
    <component
      v-else
      :is="C新テーブル一覧テーブル"
      :items="items"
      @row-dblclick="handleEdit"
    />
  </div>
</template>

<style scoped>
.page-container { padding: 20px; }
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.btn-primary {
  padding: 10px 20px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
.loading { text-align: center; padding: 20px; }
</style>
