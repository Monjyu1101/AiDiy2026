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
import { ref, computed, onMounted, watch, nextTick, onBeforeUnmount } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import apiClient from '../../api/client';
import DailyTable from './components/S配車_日表示テーブル.vue';

const route = useRoute();
const router = useRouter();

const 車両リスト = ref([]);
const 配車リスト = ref([]);
const isLoading = ref(false);
const message = ref('');
const messageType = ref('info');
let messageTimer: ReturnType<typeof setTimeout> | null = null;
const lastModifiedTime = ref<string | null>(null);
const 表示日付 = ref(null);
let autoRefreshTimer: ReturnType<typeof setInterval> | null = null;

const normalizeQueryValue = (value) => (Array.isArray(value) ? value[0] : value);
const toVisibleUrlValue = (value) => value.replace(/\?/g, '？').replace(/&/g, '＆').replace(/=/g, '＝');

const formatDate = (date) => {
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${month}/${day}`;
};

const formatDateISO = (date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const addDays = (date, days) => {
  const next = new Date(date);
  next.setDate(next.getDate() + days);
  return next;
};

const dateDisplay = computed(() => {
  if (!表示日付.value) return '';
  return `${formatDate(表示日付.value)}`;
});

const showMessage = (text, type = 'info') => {
  message.value = text;
  messageType.value = type;
  if (messageTimer) {
    clearTimeout(messageTimer);
  }
  messageTimer = setTimeout(() => {
    message.value = '';
    messageTimer = null;
  }, 3000);
};

const initLastModified = async () => {
  if (!表示日付.value) return;
  try {
    const target = formatDateISO(表示日付.value);
    const response = await apiClient.post('/apps/S配車_日表示/最終更新日時', {
      開始日付: target,
      終了日付: target
    });
    if (response.data.status === 'OK') {
      lastModifiedTime.value = response.data.data?.最終更新日時 ?? null;
    }
  } catch (error) {
    lastModifiedTime.value = null;
  }
};

const checkForUpdates = async () => {
  if (!表示日付.value) return;
  try {
    const target = formatDateISO(表示日付.value);
    const response = await apiClient.post('/apps/S配車_日表示/最終更新日時', {
      開始日付: target,
      終了日付: target
    });
    if (response.data.status !== 'OK') return;
    const currentLastModified = response.data.data?.最終更新日時;
    // nullまたはundefinedまたは空文字列の場合は何もしない
    if (currentLastModified === null || currentLastModified === undefined || currentLastModified === '') {
      return;
    }
    if (lastModifiedTime.value === null || lastModifiedTime.value === undefined || lastModifiedTime.value === '') {
      lastModifiedTime.value = currentLastModified;
      return;
    }
    const currentTime = new Date(currentLastModified);
    const previousTime = new Date(lastModifiedTime.value);
    if (Number.isNaN(currentTime.getTime()) || Number.isNaN(previousTime.getTime())) return;
    if (currentTime > previousTime) {
      lastModifiedTime.value = currentLastModified;
      await loadSchedules();
      showMessage(`データが更新されました。[${previousTime.toISOString()}→${currentTime.toISOString()}]`, 'success');
    }
  } catch (error) {
    // 無視
  }
};

const startAutoRefresh = () => {
  if (autoRefreshTimer) clearInterval(autoRefreshTimer);
  autoRefreshTimer = setInterval(checkForUpdates, 30000);
};

const stopAutoRefresh = () => {
  if (autoRefreshTimer) {
    clearInterval(autoRefreshTimer);
    autoRefreshTimer = null;
  }
};

const applyQueryParams = (query) => {
  const startDate = normalizeQueryValue(query.開始日付)
    || normalizeQueryValue(query.start_date)
    || normalizeQueryValue(query.return_date);
  if (!startDate) return false;
  const parsed = new Date(startDate);
  if (Number.isNaN(parsed.getTime())) return false;
  表示日付.value = new Date(parsed.getFullYear(), parsed.getMonth(), parsed.getDate());
  return true;
};

const ensureCurrentDate = () => {
  if (表示日付.value) return;
  const today = new Date();
  表示日付.value = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  // 初期ロード時、表示日付がセットされたらロードする
};

const loadVehicles = async () => {
  isLoading.value = true;
  try {
    const response = await apiClient.post('/apps/S配車_日表示/車両一覧');
    if (response.data.status === 'OK') {
      車両リスト.value = response.data.data?.車両一覧 ?? [];
    } else {
      showMessage('車両一覧の取得に失敗しました。', 'error');
    }
  } catch (error) {
    showMessage('車両一覧の取得でエラーが発生しました。', 'error');
  } finally {
    isLoading.value = false;
  }
};

const loadSchedules = async () => {
  if (!表示日付.value) return;
  try {
    const response = await apiClient.post('/apps/S配車_日表示/配車一覧', {
      対象日付: formatDateISO(表示日付.value)
    });
    if (response.data.status === 'OK') {
      配車リスト.value = response.data.data?.配車一覧 ?? [];
    } else {
      showMessage('配車一覧の取得に失敗しました。', 'error');
    }
  } catch (error) {
    showMessage('配車一覧の取得でエラーが発生しました。', 'error');
  }
};

const updateScheduleByResize = async ({ schedule, direction, deltaHours }) => {
  const start = new Date(schedule.配車開始日時);
  const end = new Date(schedule.配車終了日時);
  let newStart = start;
  let newEnd = end;

  if (direction === 'left') {
    newStart = new Date(start);
    newStart.setHours(newStart.getHours() + deltaHours);
  } else {
    newEnd = new Date(end);
    newEnd.setHours(newEnd.getHours() + deltaHours);
  }

  if (newStart >= newEnd) {
    showMessage('開始日時は終了日時より前でなければなりません。', 'error');
    // 再読み込みして元に戻す
    await loadSchedules();
    return;
  }

  try {
    const response = await apiClient.post('/apps/S配車_日表示/リサイズ更新', {
      配車伝票ID: schedule.配車伝票ID,
      変更後開始日時: newStart.toISOString(),
      変更後終了日時: newEnd.toISOString()
    });
    if (response.data.status === 'OK') {
      showMessage('配車期間を更新しました。', 'success');
    } else {
      showMessage(response.data.message || '配車期間の更新に失敗しました。', 'error');
    }
  } catch (error) {
    showMessage('配車期間の更新でエラーが発生しました。', 'error');
  }
  await loadSchedules();
};

const handleDropUpdate = async ({ scheduleId, vehicleId, timeSlot }) => {
  const schedule = 配車リスト.value.find((item) => item.配車伝票ID === scheduleId);
  if (!schedule) return;

  const existingStart = new Date(schedule.配車開始日時);
  const existingEnd = new Date(schedule.配車終了日時);
  const duration = existingEnd.getTime() - existingStart.getTime();

  const newStartDate = new Date(表示日付.value);
  const hour = parseInt(timeSlot.split(':')[0], 10);
  newStartDate.setHours(hour, 0, 0, 0);
  const newEndDate = new Date(newStartDate.getTime() + duration);

  try {
    const response = await apiClient.post('/apps/S配車_日表示/ドラッグ更新', {
      配車伝票ID: scheduleId,
      車両ID: String(vehicleId),
      変更後日付: formatDateISO(newStartDate),
      変更後開始日時: newStartDate.toISOString(),
      変更後終了日時: newEndDate.toISOString()
    });
    if (response.data.status === 'OK') {
      showMessage('配車予定を更新しました。', 'success');
    } else {
      showMessage(response.data.message || '配車予定の更新に失敗しました。', 'error');
    }
  } catch (error) {
    showMessage('配車予定の更新でエラーが発生しました。', 'error');
  }
  await loadSchedules();
};

const openEditForm = (scheduleId = null, vehicleId = null, timeSlot = null) => {
  const baseDate = formatDateISO(表示日付.value);
  const returnPath = {
    path: '/Sスケジュール/S配車_日表示',
    query: { 開始日付: baseDate }
  };
  const resolvedReturnUrl = toVisibleUrlValue(router.resolve(returnPath).fullPath);
  
  if (scheduleId) {
    const queryString = `配車伝票ID=${encodeURIComponent(scheduleId)}&戻URL=${resolvedReturnUrl}`;
    router.push(`/Tトラン/T配車/編集?${queryString}`);
  } else if (vehicleId && timeSlot) {
    const normalizedTime = timeSlot.padStart(5, '0');
    const [hourPart, minutePart] = normalizedTime.split(':');
    const startDate = new Date(`${baseDate}T${hourPart}:${minutePart}`);
    const endDate = new Date(startDate.getTime() + 60 * 60 * 1000);
    const startDateTime = `${baseDate}T${normalizedTime}`;
    const endDateTime = `${baseDate}T${String(endDate.getHours()).padStart(2, '0')}:${String(endDate.getMinutes()).padStart(2, '0')}`;

    const queryString = `モード=${encodeURIComponent('新規')}&車両ID=${encodeURIComponent(String(vehicleId))}&配車開始日時=${encodeURIComponent(startDateTime)}&配車終了日時=${encodeURIComponent(endDateTime)}&戻URL=${resolvedReturnUrl}`;
    router.push(`/Tトラン/T配車/編集?${queryString}`);
  }
};

const moveDay = async (delta) => {
  表示日付.value = addDays(表示日付.value, delta);
  router.replace({ path: route.path, query: { 開始日付: formatDateISO(表示日付.value) } });
  await loadSchedules();
};

const moveWeek = async (delta) => {
  表示日付.value = addDays(表示日付.value, delta * 7);
  router.replace({ path: route.path, query: { 開始日付: formatDateISO(表示日付.value) } });
  await loadSchedules();
};

const initialize = async () => {
  applyQueryParams(route.query);
  ensureCurrentDate();
  await loadVehicles();
  await loadSchedules();
  await initLastModified();
  startAutoRefresh();
};

onMounted(() => {
  initialize();
});

onBeforeUnmount(() => {
  stopAutoRefresh();
});

watch(() => route.query, async (query) => {
  if (applyQueryParams(query)) {
    await loadSchedules();
    await initLastModified();
  }
});
</script>

<template>
  <div class="page-container">
    <h2 class="page-title">【 S配車_日表示 】</h2>

    <div class="navigation">
      <button class="nav-button" @click="moveWeek(-1)">&#x25c0; 前週</button>
      <button class="nav-button period-nav" @click="moveDay(-1)">&#x25c1; 前日</button>
      <div class="current-period">{{ dateDisplay }}</div>
      <button class="nav-button period-nav" @click="moveDay(1)">翌日 &#x25b7;</button>
      <button class="nav-button" @click="moveWeek(1)">翌週 &#x25b6;</button>
    </div>

    <div v-if="message" class="message" :class="`message-${messageType}`">
      {{ message }}
    </div>

    <div class="table-container">
      <DailyTable
        :車両リスト="車両リスト"
        :配車リスト="配車リスト"
        :対象日付="表示日付"
        @update-schedule-resize="updateScheduleByResize"
        @update-schedule-drop="handleDropUpdate"
        @open-edit-form="openEditForm"
      />
    </div>

    <div v-if="isLoading" class="loading">読み込み中...</div>
  </div>
</template>

<style scoped>
.page-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #faf7f2 0%, #f5f1e8 50%, #f0ebe0 100%);
  color: #333;
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

.navigation {
  display: flex;
  align-items: center;
  margin: 5px 10px;
  padding: 5px 10px;
  background-color: #f8f9fa;
  border-radius: 5px;
  gap: 10px;
}

.nav-button {
  padding: 5px 15px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 3px;
  cursor: pointer;
  font-size: 14px;
}

.nav-button:hover {
  background-color: #0056b3;
}

.nav-button.period-nav {
  background-color: #bfe3f6;
  color: #1f3b57;
}

.nav-button.period-nav:hover {
  background-color: #a9d4ee;
}

.current-period {
  font-weight: bold;
  font-size: 22px;
  text-align: center;
  flex-grow: 1;
  color: #5a4a3a;
}

.table-container {
  flex: 1;
  overflow: auto;
}

.message {
  padding: 10px;
  border-radius: 5px;
  margin: 0 10px 10px 10px;
}

.message-info {
  background-color: #e3f2fd;
  color: #1565c0;
}

.message-success {
  background-color: #d4edda;
  color: #155724;
}

.message-error {
  background-color: #f8d7da;
  color: #721c24;
}

.loading {
  padding: 10px 15px;
  color: #5a4a3a;
}
</style>

