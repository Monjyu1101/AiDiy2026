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
import { ref, onMounted, computed, watch, onBeforeUnmount } from 'vue';
import dayjs from 'dayjs';
import apiClient from '../../api/client';
import TransitionTable from './components/V商品推移表テーブル.vue';
import { useRoute, useRouter } from 'vue-router';

const DISPLAY_DAYS = 32;

// 状態管理
const route = useRoute();
const router = useRouter();
const currentDate = ref(dayjs().startOf('day')); // 表示開始日
const 日付リスト = ref<string[]>([]);
const 商品データ = ref<any[]>([]);
const 商品一覧 = ref<any[]>([]);
const isLoading = ref(false);
const message = ref('');
const messageType = ref('info');
let messageTimer: ReturnType<typeof setTimeout> | null = null;
const lastModifiedTime = ref<string | null>(null);
let autoRefreshTimer: ReturnType<typeof setInterval> | null = null;

const normalizeQueryValue = (value: any): any => (Array.isArray(value) ? value[0] : value);

const parseStartDate = (value: any): any => {
  if (!value) return null;
  const normalized = String(value).trim().replace(/\//g, '-');
  if (!normalized) return null;
  const parsed = dayjs(normalized);
  if (!parsed.isValid()) return null;
  return parsed.startOf('day');
};

const applyQueryParams = (query: any) => {
  const raw = normalizeQueryValue(query.開始日付);
  const parsed = parseStartDate(raw);
  currentDate.value = parsed || dayjs().startOf('day');
};

// 期間計算 (開始日から32日固定)
const startDate = computed(() => currentDate.value.format('YYYY-MM-DD'));
const endDate = computed(() => currentDate.value.add(DISPLAY_DAYS - 1, 'day').format('YYYY-MM-DD'));

// 表示用期間文字列
const periodDisplay = computed(() => {
  const startText = currentDate.value.format('MM/DD');
  const endText = currentDate.value.add(DISPLAY_DAYS - 1, 'day').format('MM/DD');
  return `${startText} ～ ${endText}`;
});

const buildDateList = (startDateStr: string): string[] => {
  const base = dayjs(startDateStr);
  if (!base.isValid()) return [];
  return Array.from({ length: DISPLAY_DAYS }, (_, index) =>
    base.add(index, 'day').format('YYYY-MM-DD')
  );
};

const applyFallbackDateList = () => {
  日付リスト.value = buildDateList(startDate.value);
};

const applyFallbackProducts = (items: any[]) => {
  if (!Array.isArray(items) || items.length === 0) return;
  商品データ.value = items.map((item: any) => ({
    商品ID: item.商品ID ?? '',
    商品名: item.商品名 ?? '',
    日別データ: []
  }));
};

const 表示商品データ = computed(() => {
  if (商品データ.value.length > 0) return 商品データ.value;
  if (商品一覧.value.length === 0) return [];
  return 商品一覧.value.map((item: any) => ({
    商品ID: item.商品ID ?? '',
    商品名: item.商品名 ?? '',
    日別データ: []
  }));
});

const loadProductList = async () => {
  try {
    const response = await apiClient.post('/apps/V商品/一覧');
    if (response.data.status === 'OK') {
      const data = response.data.data;
      const items = Array.isArray(data) ? data : data?.items ?? [];
      商品一覧.value = items;
      if (商品データ.value.length === 0) {
        applyFallbackProducts(items);
      }
    }
  } catch (error) {
    // 取得できない場合は空表示のままにする
  }
};

// APIデータ取得
const fetchData = async () => {
  isLoading.value = true;
  message.value = '';
  
  try {
    const payload = {
      開始日付: startDate.value,
      終了日付: endDate.value
    };
    
    // axiosインスタンスを使用するか、直接axiosを使うか。ここでは直接。
    // 認証トークンが必要な場合はstoreから取得するロジックが必要だが、
    // 既存のaxios設定(interceptor)があればそれに任せる。
    // ここでは簡易的にlocalStorageから取得してみる、あるいはTトラン.vueなどを参照。
    // AuthStoreを使うのがベスト。
    
    // Auth Storeからトークン取得（簡易実装）
    const response = await apiClient.post('/apps/V商品推移表/一覧', payload);
    
    if (response.data.status === 'OK') {
      const data = response.data.data;
      const list = Array.isArray(data?.日付リスト) ? data.日付リスト : [];
      const products = Array.isArray(data?.商品推移データ) ? data.商品推移データ : [];
      日付リスト.value = list.length ? list : buildDateList(startDate.value);
      商品データ.value = products.length ? products : 商品データ.value;
    } else {
      applyFallbackDateList();
    }
    
  } catch (error) {
    applyFallbackDateList();
  } finally {
    isLoading.value = false;
  }
};

const showMessage = (msg: string, type = 'info') => {
  message.value = msg;
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
  try {
    const response = await apiClient.post('/apps/V商品推移表/最終更新日時', {
      開始日付: startDate.value,
      終了日付: endDate.value
    });
    if (response.data.status === 'OK') {
      lastModifiedTime.value = response.data.data?.最終更新日時 ?? null;
    }
  } catch (error) {
    lastModifiedTime.value = null;
  }
};

const checkForUpdates = async () => {
  try {
    const response = await apiClient.post('/apps/V商品推移表/最終更新日時', {
      開始日付: startDate.value,
      終了日付: endDate.value
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
      await fetchData();
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

// ナビゲーション操作
const moveMonth = async (months: number) => {
  currentDate.value = currentDate.value.add(months, 'month');
  router.replace({ path: route.path, query: { 開始日付: startDate.value } });
  await fetchData();
};

const moveDay = async (days: number) => {
  currentDate.value = currentDate.value.add(days, 'day');
  applyFallbackDateList();
  router.replace({ path: route.path, query: { 開始日付: startDate.value } });
  await fetchData();
};

onMounted(() => {
  applyQueryParams(route.query);
  applyFallbackDateList();
  loadProductList();
  fetchData();
  initLastModified();
  startAutoRefresh();
});

onBeforeUnmount(() => {
  stopAutoRefresh();
});

watch(() => route.query.開始日付, () => {
  applyQueryParams(route.query);
  applyFallbackDateList();
  fetchData();
  initLastModified();
});
</script>

<template>
  <div class="page-container">
    <h2 class="page-title">【 V商品推移表 】</h2>
    
    <!-- ナビゲーション -->
    <div class="navigation">
      <button class="nav-button" @click="moveMonth(-1)">◀ 前月</button>
      <button class="nav-button period-nav" @click="moveDay(-1)">◁ 前日</button>
      
      <div class="current-period">{{ periodDisplay }}</div>
      
      <button class="nav-button period-nav" @click="moveDay(1)">翌日 ▷</button>
      <button class="nav-button" @click="moveMonth(1)">翌月 ▶</button>
    </div>
    
    <!-- メッセージ -->
    <div v-if="message" class="message" :class="'message-' + messageType">
      {{ message }}
    </div>

    <!-- コンテンツ -->
    <div class="content">
        <div v-if="isLoading" class="loading">
            <div class="spinner"></div>
            <div>読み込み中...</div>
        </div>
        
        <TransitionTable 
            v-else
            :日付リスト="日付リスト" 
            :商品データ="表示商品データ" 
        />
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
.nav-button:hover:not(:disabled) {
  background-color: #0056b3;
}
.nav-button:disabled {
    background-color: #ccc;
    cursor: not-allowed;
}

.nav-button.period-nav {
  background-color: #bfe3f6;
  color: #1f3b57;
}
.nav-button.period-nav:hover:not(:disabled) {
  background-color: #a9d4ee;
}

.current-period {
  font-weight: bold;
  font-size: 22px;
  text-align: center;
  flex-grow: 1;
  color: #5a4a3a;
}

.content {
  padding: 0 10px 10px 10px;
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden; /* テーブルのスクロールはテーブルコンテナに任せる */
}

.loading {
  text-align: center;
  padding: 40px;
  color: #5a4a3a;
}
.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #d2bb95;
  border-radius: 50%;
  width: 30px;
  height: 30px;
  animation: spin 1s linear infinite;
  margin: 0 auto 10px;
}
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.message {
  padding: 10px;
  margin: 0 10px 5px;
  border-radius: 5px;
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
</style>

