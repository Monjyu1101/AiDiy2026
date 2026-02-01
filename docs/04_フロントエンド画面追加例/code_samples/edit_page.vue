<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import apiClient from '@/api/client'
import { qAlert, qConfirm } from '@/utils/qAlert'

const router = useRouter()
const route = useRoute()

const 新ID = ref('')
const 新名 = ref('')
const 新備考 = ref('')
const isNewMode = ref(true)

const fetchItem = async () => {
  const id = route.query.新ID as string
  if (!id) {
    isNewMode.value = true
    return
  }

  isNewMode.value = false
  try {
    const response = await apiClient.post('/core/C新テーブル/取得', { 新ID: id })
    if (response.data.status === 'OK') {
      const item = response.data.data
      新ID.value = item.新ID
      新名.value = item.新名
      新備考.value = item.新備考 || ''
    }
  } catch (error) {
    console.error(error)
    await qAlert('データの取得に失敗しました')
  }
}

const handleSave = async () => {
  if (!新ID.value || !新名.value) {
    await qAlert('必須項目を入力してください')
    return
  }

  try {
    const data = {
      新ID: 新ID.value,
      新名: 新名.value,
      新備考: 新備考.value || null
    }

    const endpoint = isNewMode.value ? '/core/C新テーブル/登録' : '/core/C新テーブル/変更'
    const response = await apiClient.post(endpoint, data)

    if (response.data.status === 'OK') {
      await qAlert(isNewMode.value ? '作成しました' : '更新しました')
      router.back()
    } else {
      await qAlert(`エラー: ${response.data.message}`)
    }
  } catch (error) {
    console.error(error)
    await qAlert('保存に失敗しました')
  }
}

const handleDelete = async () => {
  if (isNewMode.value) return

  const confirmed = await qConfirm('削除してもよろしいですか？')
  if (!confirmed) return

  try {
    const response = await apiClient.post('/core/C新テーブル/削除', { 新ID: 新ID.value })
    if (response.data.status === 'OK') {
      await qAlert('削除しました')
      router.back()
    } else {
      await qAlert(`エラー: ${response.data.message}`)
    }
  } catch (error) {
    console.error(error)
    await qAlert('削除に失敗しました')
  }
}

const handleCancel = () => {
  router.back()
}

onMounted(() => {
  fetchItem()
})
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h1>{{ isNewMode ? 'C新テーブル 新規作成' : 'C新テーブル 編集' }}</h1>
    </div>

    <div class="form-container">
      <div class="form-group">
        <label>新ID <span class="required">*</span></label>
        <input v-model="新ID" :disabled="!isNewMode" type="text" class="form-control" />
      </div>

      <div class="form-group">
        <label>新名 <span class="required">*</span></label>
        <input v-model="新名" type="text" class="form-control" />
      </div>

      <div class="form-group">
        <label>備考</label>
        <textarea v-model="新備考" class="form-control" rows="3"></textarea>
      </div>

      <div class="button-group">
        <button @click="handleSave" class="btn-primary">保存</button>
        <button v-if="!isNewMode" @click="handleDelete" class="btn-danger">削除</button>
        <button @click="handleCancel" class="btn-secondary">キャンセル</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-container { padding: 20px; }
.form-container { max-width: 600px; margin: 0 auto; }
.form-group { margin-bottom: 20px; }
.form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
.required { color: red; }
.form-control { width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px; }
.button-group { display: flex; gap: 10px; margin-top: 30px; }
.btn-primary, .btn-danger, .btn-secondary {
  padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer;
}
.btn-primary { background-color: #007bff; color: white; }
.btn-danger { background-color: #dc3545; color: white; }
.btn-secondary { background-color: #6c757d; color: white; }
</style>
