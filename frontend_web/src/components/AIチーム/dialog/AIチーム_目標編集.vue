<!--
  -*- coding: utf-8 -*-

  -------------------------------------------------------------------------
  COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
  Licensed under "AiDiy 公開利用ライセンス v1.1".
  Commercial use requires prior written consent from all copyright holders.
  See LICENSE for full terms. Thank you for keeping the rules.
  https://github.com/monjyu1101/AiDiy2026
  -------------------------------------------------------------------------
-->

<script setup lang="ts">
// Aチーム目標の保守: 左に登録済パス一覧、右にパス選択・パス入力・チーム目標入力
import { computed, ref, watch } from 'vue';
import apiClient from '../../../api/client';
import { useAuthStore } from '../../../stores/auth';
import { qConfirm, qMessage } from '../../../utils/qAlert';
import type { チーム目標, チーム要員 } from '../AIチーム_型';

const props = defineProps<{ isOpen: boolean }>();

const emit = defineEmits<{
  close: [];
  saved: [item: チーム目標];
}>();

const 既定パス = '../';
const 既定動員要員数 = 2;
const 既定パターン: 'SPDCA' | 'PlanDo' = 'PlanDo';
const パターン選択肢: { value: 'SPDCA' | 'PlanDo'; label: string }[] = [
  { value: 'SPDCA', label: 'SPDCA（相談→計画→実行→評価→改善）' },
  { value: 'PlanDo', label: 'PlanDo（計画→実行）' },
];
const パターン正規化 = (値: unknown): 'SPDCA' | 'PlanDo' =>
  値 === 'SPDCA' || 値 === 'PlanDo' ? 値 : 既定パターン;
const authStore = useAuthStore();
const 利用者ID = computed(() => String(authStore.user?.利用者ID ?? 'admin'));
const 利用者名 = computed(() => String(authStore.user?.利用者名 ?? authStore.user?.利用者ID ?? 'admin'));

const 目標一覧 = ref<チーム目標[]>([]);
const プロジェクト選択肢 = ref<{ value: string; label: string }[]>([]);
const 選択パス = ref('');
const 入力パス = ref(既定パス);
const 入力目標 = ref('');
const 入力改善ループ = ref(false);
const 入力最大ループ回数 = ref(1);
const 入力動員要員数 = ref(既定動員要員数);
const 入力パターン = ref<'SPDCA' | 'PlanDo'>(既定パターン);
const 最大ループ回数選択肢 = Array.from({ length: 99 }, (_, index) => index + 1);
// 相談へ動員できるのは admin 以外の有効要員だけなので、その人数を動員要員数の上限にする
const 有効要員数 = ref(1);
const 動員要員数選択肢 = computed(() =>
  Array.from({ length: Math.max(1, 有効要員数.value) }, (_, index) => index + 1),
);
const 動員要員数を丸める = (人数: unknown) =>
  Math.min(Math.max(1, 有効要員数.value), Math.max(1, Number(人数 ?? 既定動員要員数)));
const 読込中 = ref(false);
const 保存中 = ref(false);
const 削除中 = ref(false);

const 選択中か = (パス: string) => 入力パス.value.trim() === パス;
const 既定パス選択中 = computed(() => 入力パス.value.trim() === 既定パス);
const 登録済み = computed(() =>
  目標一覧.value.some((項目) => 項目.CODE_BASE_PATH === 入力パス.value.trim()),
);

const 目標一覧読込 = async () => {
  読込中.value = true;
  try {
    const response = await apiClient.post('/team/目標/一覧', {});
    if (response.data?.status !== 'OK') {
      void qMessage(response.data?.message || 'チーム目標一覧を取得できませんでした。', 'error');
      return;
    }
    目標一覧.value = (response.data.data?.items ?? []) as チーム目標[];
  } catch {
    void qMessage('チーム目標一覧の取得でエラーが発生しました。backend_team (8094) を確認してください。', 'error');
  } finally {
    読込中.value = false;
  }
};

const プロジェクト選択肢読込 = async () => {
  try {
    const response = await apiClient.post('/task/プロジェクト選択肢', {});
    const options = response.data?.status === 'OK' ? response.data.data?.選択肢 ?? {} : {};
    プロジェクト選択肢.value = Object.entries(options).map(([value, label]) => ({
      value,
      label: `${String(label)} (${value})`,
    }));
  } catch {
    プロジェクト選択肢.value = [];
  }
};

const 有効要員数読込 = async () => {
  try {
    const response = await apiClient.post('/team/要員/一覧', { 無効も表示: false });
    const items = (response.data?.status === 'OK' ? response.data.data?.items ?? [] : []) as チーム要員[];
    // admin は相談の動員対象外なので数に含めない
    有効要員数.value = Math.max(1, items.filter((要員) => 要員.要員ID !== 'admin').length);
  } catch {
    有効要員数.value = 1;
  }
};

const 一覧から選ぶ = (項目: チーム目標) => {
  選択パス.value = プロジェクト選択肢.value.some((option) => option.value === 項目.CODE_BASE_PATH)
    ? 項目.CODE_BASE_PATH
    : '';
  入力パス.value = 項目.CODE_BASE_PATH;
  入力目標.value = 項目.チーム目標;
  入力改善ループ.value = Boolean(項目.改善ループ);
  入力最大ループ回数.value = Math.min(99, Math.max(1, Number(項目.最大ループ回数 ?? 1)));
  入力動員要員数.value = 動員要員数を丸める(項目.動員要員数);
  入力パターン.value = パターン正規化(項目.パターン);
};

watch(選択パス, (value) => {
  if (!value) return;
  入力パス.value = value;
  const 既存 = 目標一覧.value.find((項目) => 項目.CODE_BASE_PATH === value);
  if (既存) {
    入力目標.value = 既存.チーム目標;
    入力改善ループ.value = Boolean(既存.改善ループ);
    入力最大ループ回数.value = Math.min(99, Math.max(1, Number(既存.最大ループ回数 ?? 1)));
    入力動員要員数.value = 動員要員数を丸める(既存.動員要員数);
    入力パターン.value = パターン正規化(既存.パターン);
  }
});

watch(
  () => props.isOpen,
  async (open) => {
    if (!open) return;
    選択パス.value = '';
    入力パス.value = 既定パス;
    入力目標.value = '';
    入力改善ループ.value = false;
    入力最大ループ回数.value = 1;
    入力パターン.value = 既定パターン;
    // 選択肢の上限は有効要員数に依存するため、読込後に丸め直す
    await Promise.all([目標一覧読込(), プロジェクト選択肢読込(), 有効要員数読込()]);
    入力動員要員数.value = 動員要員数を丸める(既定動員要員数);
    // 最終更新の 1 件を初期表示にする（掲示板に出ている目標をそのまま編集できる）
    const 先頭 = 目標一覧.value[0];
    if (先頭) 一覧から選ぶ(先頭);
  },
  { immediate: true },
);

const 保存 = async () => {
  const パス = 入力パス.value.trim();
  const 目標 = 入力目標.value.trim();
  if (!パス) {
    void qMessage('CODE_BASE_PATH を入力してください。', 'error');
    return;
  }
  if (!目標) {
    void qMessage('チーム目標を入力してください。', 'error');
    return;
  }
  保存中.value = true;
  try {
    const response = await apiClient.post('/team/目標/保存', {
      CODE_BASE_PATH: パス,
      チーム目標: 目標,
      改善ループ: 入力改善ループ.value,
      最大ループ回数: 入力最大ループ回数.value,
      動員要員数: 入力動員要員数.value,
      パターン: 入力パターン.value,
      操作利用者ID: 利用者ID.value,
      操作利用者名: 利用者名.value,
      操作端末ID: 'frontend_web',
    });
    if (response.data?.status !== 'OK') {
      void qMessage(response.data?.message || 'チーム目標を保存できませんでした。', 'error');
      return;
    }
    const item = response.data.data?.item as チーム目標 | undefined;
    // 保存した内容をそのまま親へ渡す（改善一覧パネルの表示・非表示はこの値で切り替わる）
    emit('saved', {
      ...(item ?? { CODE_BASE_PATH: パス, チーム目標: 目標, 更新日時: '' }),
      改善ループ: 入力改善ループ.value,
      最大ループ回数: 入力最大ループ回数.value,
      動員要員数: 入力動員要員数.value,
      パターン: 入力パターン.value,
    });
    // 1件保存したら用は済むのでダイアログを閉じる
    emit('close');
  } catch {
    void qMessage('チーム目標の保存でエラーが発生しました。backend_team (8094) を確認してください。', 'error');
  } finally {
    保存中.value = false;
  }
};

const 削除 = async () => {
  const パス = 入力パス.value.trim();
  if (!パス || 既定パス選択中.value) return;
  if (!(await qConfirm(`${パス} のチーム目標を削除しますか？`))) return;
  削除中.value = true;
  try {
    const response = await apiClient.post('/team/目標/削除', {
      CODE_BASE_PATH: パス,
      操作利用者ID: 利用者ID.value,
      操作利用者名: 利用者名.value,
      操作端末ID: 'frontend_web',
    });
    if (response.data?.status !== 'OK') {
      void qMessage(response.data?.message || 'チーム目標を削除できませんでした。', 'error');
      return;
    }
    void qMessage(response.data.message || 'チーム目標を削除しました。');
    await 目標一覧読込();
    const 先頭 = 目標一覧.value[0];
    if (先頭) {
      一覧から選ぶ(先頭);
      emit('saved', 先頭);
    }
  } catch {
    void qMessage('チーム目標の削除でエラーが発生しました。backend_team (8094) を確認してください。', 'error');
  } finally {
    削除中.value = false;
  }
};
</script>

<template>
  <Teleport to="body">
    <div v-if="isOpen" class="dialog-overlay" @click.self="emit('close')">
      <section class="dialog-content" role="dialog" aria-modal="true" aria-label="チーム目標保守">
        <header class="dialog-header">
          <h3>【チーム目標】保守</h3>
          <button type="button" class="dialog-close" aria-label="閉じる" @click="emit('close')">×</button>
        </header>

        <div class="dialog-body">
          <div class="goal-layout">
            <aside class="goal-list">
              <div class="goal-list-head">
                <span>登録済パス</span>
                <b>{{ 目標一覧.length }}</b>
              </div>
              <p v-if="読込中" class="goal-list-empty">読み込み中…</p>
              <p v-else-if="目標一覧.length === 0" class="goal-list-empty">登録がありません</p>
              <ul v-else class="goal-list-body">
                <li v-for="項目 in 目標一覧" :key="項目.CODE_BASE_PATH">
                  <button
                    type="button"
                    class="goal-list-item"
                    :class="{ active: 選択中か(項目.CODE_BASE_PATH) }"
                    @click="一覧から選ぶ(項目)"
                  >
                    <span class="goal-list-path">{{ 項目.CODE_BASE_PATH }}</span>
                    <span class="goal-list-text">{{ 項目.チーム目標 }}</span>
                    <span class="goal-list-date">{{ 項目.更新日時 }}</span>
                  </button>
                </li>
              </ul>
            </aside>

            <div class="goal-form">
              <div class="detail-row one-line-row">
                <div class="detail-label">パス選択</div>
                <div class="detail-value">
                  <select v-model="選択パス" class="detail-select">
                    <option value="">（選択してください）</option>
                    <option v-for="option in プロジェクト選択肢" :key="option.value" :value="option.value">
                      {{ option.label }}
                    </option>
                  </select>
                </div>
              </div>
              <div class="detail-row one-line-row">
                <div class="detail-label">
                  パス入力<span class="required-mark">*</span>
                </div>
                <div class="detail-value">
                  <input v-model.trim="入力パス" type="text" class="detail-input" placeholder="../" />
                </div>
              </div>
              <div class="detail-row request-row">
                <div class="detail-label">
                  チーム目標<span class="required-mark">*</span>
                </div>
                <div class="detail-value">
                  <textarea
                    v-model="入力目標"
                    class="detail-textarea"
                    placeholder="よく考えて、行うべきことを実行する。"
                  ></textarea>
                </div>
              </div>
              <div class="detail-row one-line-row">
                <div class="detail-label">ループ実行</div>
                <div class="detail-value">
                  <div class="loop-settings">
                    <label class="valid-checkbox-label">
                    <input
                      v-model="入力改善ループ"
                      type="checkbox"
                      class="valid-checkbox"
                      aria-label="改善ループの切り替え"
                    />
                    <span
                      class="valid-checkbox-mark"
                      :class="{ 'valid-checkbox-inactive': !入力改善ループ }"
                    >{{ 入力改善ループ ? '✅' : '☐' }}</span>
                    </label>
                    <label class="max-loop-label" for="最大ループ回数">最大ループ回数</label>
                    <select id="最大ループ回数" v-model.number="入力最大ループ回数" class="max-loop-select">
                      <option v-for="回数 in 最大ループ回数選択肢" :key="回数" :value="回数">
                        {{ 回数 === 99 ? '99（無制限）' : 回数 }}
                      </option>
                    </select>
                    <label class="mobilize-label" for="動員要員数">動員要員数</label>
                    <select id="動員要員数" v-model.number="入力動員要員数" class="mobilize-select">
                      <option v-for="人数 in 動員要員数選択肢" :key="人数" :value="人数">
                        {{ 人数 }}
                      </option>
                    </select>
                  </div>
                </div>
              </div>
              <div class="detail-row one-line-row">
                <div class="detail-label">パターン</div>
                <div class="detail-value">
                  <select id="パターン" v-model="入力パターン" class="detail-select">
                    <option v-for="option in パターン選択肢" :key="option.value" :value="option.value">
                      {{ option.label }}
                    </option>
                  </select>
                </div>
              </div>
              <p class="goal-note">
                CODE_BASE_PATH ごとに 1 件です。同じパスを保存すると上書きされ、
                更新日時が最新の目標がチーム空間の掲示板に表示されます。
              </p>
            </div>
          </div>
        </div>

        <footer class="dialog-footer">
          <button type="button" class="dialog-button primary" :disabled="保存中" @click="保存">
            {{ 保存中 ? '保存中…' : 登録済み ? '更新' : '登録' }}
          </button>
          <button
            type="button"
            class="dialog-button danger"
            :disabled="削除中 || 既定パス選択中 || !登録済み"
            @click="削除"
          >
            {{ 削除中 ? '削除中…' : '削除' }}
          </button>
          <button type="button" class="dialog-button" @click="emit('close')">閉じる</button>
        </footer>
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.dialog-overlay {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgba(0, 0, 0, 0.72);
}

.dialog-content {
  width: min(980px, 96vw);
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid rgba(143, 104, 221, 0.75);
  border-radius: 4px;
  color: #e5e7eb;
  background: #07080c;
  box-shadow: 0 0 24px rgba(60, 42, 128, 0.65);
}

.dialog-header {
  min-height: 34px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 8px 0 14px;
  background: linear-gradient(135deg, #4668cd, #6c4ec4, #8f68dd);
}

.dialog-header h3 {
  margin: 0;
  color: #fff;
  font-size: 13px;
  letter-spacing: 1px;
}

.dialog-close {
  border: 0;
  color: #fff;
  background: transparent;
  cursor: pointer;
  font-size: 18px;
}

.dialog-body {
  min-height: 0;
  padding: 12px;
  overflow-y: auto;
}

.goal-layout {
  display: grid;
  grid-template-columns: 268px minmax(0, 1fr);
  gap: 12px;
}

.goal-list {
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid #4b5563;
  border-radius: 4px;
  background: #10131a;
}

.goal-list-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  color: #fff;
  background: linear-gradient(135deg, #37474f, rgba(70, 104, 205, 0.74));
  font-size: 12px;
  font-weight: 600;
}

.goal-list-head b { color: #9dffce; }

.goal-list-empty {
  margin: 0;
  padding: 12px 10px;
  color: #8b98a5;
  font-size: 11px;
}

.goal-list-body {
  max-height: 320px;
  margin: 0;
  padding: 0;
  overflow-y: auto;
  list-style: none;
}

.goal-list-item {
  width: 100%;
  display: grid;
  gap: 2px;
  padding: 7px 10px;
  border: 0;
  border-bottom: 1px solid rgba(75, 85, 99, 0.6);
  color: #d7dee6;
  background: transparent;
  cursor: pointer;
  text-align: left;
}

.goal-list-item:hover { background: rgba(70, 104, 205, 0.18); }
.goal-list-item.active { background: rgba(143, 104, 221, 0.28); }

.goal-list-path {
  color: #9ceaff;
  font-size: 12px;
  font-weight: 700;
  word-break: break-all;
}

.goal-list-text {
  overflow: hidden;
  color: #cbd5e1;
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.goal-list-date { color: #7f8b99; font-size: 10px; }

.goal-form {
  min-width: 0;
}

.detail-row {
  display: flex;
  width: 100%;
  margin-top: -1px;
  flex: 0 0 auto;
}

.detail-label {
  width: 120px;
  min-height: 34px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 6px 10px;
  border: 1px solid rgba(93, 68, 168, 0.85);
  color: #fff;
  background: linear-gradient(135deg, #37474f, rgba(70, 104, 205, 0.74));
  box-sizing: border-box;
  font-size: 13px;
  font-weight: 600;
  z-index: 1;
}

.detail-value {
  min-width: 0;
  min-height: 34px;
  flex: 1;
  display: flex;
  align-items: center;
  padding: 3px 10px;
  border: 1px solid #4b5563;
  border-left: 0;
  background: #10131a;
  box-sizing: border-box;
  font-size: 13px;
}

.request-row .detail-value { align-items: stretch; }

.detail-input,
.detail-select,
.detail-textarea {
  width: 100%;
  min-width: 0;
  padding: 4px 8px;
  border: 1px solid #4b5563;
  border-radius: 4px;
  color: #f3f4f6;
  background: #05070b;
  box-sizing: border-box;
  font: inherit;
}

.detail-input,
.detail-select { height: 26px; }

.detail-input {
  margin: 0;
  padding: 0 8px;
}

.detail-select {
  max-width: 100%;
  min-height: 26px;
  display: block;
  align-self: center;
  margin: 0;
  padding: 0 28px 0 8px;
  line-height: normal;
  appearance: auto;
}

.one-line-row,
.one-line-row .detail-label,
.one-line-row .detail-value {
  height: 34px;
  min-height: 34px;
}

.detail-textarea {
  min-height: 190px;
  resize: vertical;
}

.required-mark {
  margin-left: 2px;
  color: #dc2626;
}

.valid-checkbox-label {
  width: 52px;
  height: 26px;
  min-height: 26px;
  padding: 0 8px;
  border: 1px solid #4b5563;
  border-radius: 4px;
  color: #16a34a;
  background: #05070b;
  box-sizing: border-box;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 14px;
  font-weight: 700;
  user-select: none;
}

.valid-checkbox-label:focus-within {
  border-color: #8f68dd;
  box-shadow: inset 0 0 0 1px rgba(143, 104, 221, 0.35);
}

.valid-checkbox {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}

.valid-checkbox-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #16a34a;
  font-size: 16px;
  line-height: 1;
}

.valid-checkbox-inactive {
  color: #d1d5db;
}

.loop-settings {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
}

.max-loop-label {
  margin-left: auto;
  color: #cbd5e1;
  font-size: 12px;
  white-space: nowrap;
}

.max-loop-select {
  width: 112px;
  height: 26px;
  padding: 0 6px;
  border: 1px solid #4b5563;
  border-radius: 4px;
  color: #f3f4f6;
  background: #05070b;
  box-sizing: border-box;
  font: inherit;
}

.mobilize-label {
  color: #cbd5e1;
  font-size: 12px;
  white-space: nowrap;
}

.mobilize-select {
  width: 52px;
  height: 26px;
  padding: 0 6px;
  border: 1px solid #4b5563;
  border-radius: 3px;
  color: #e5e7eb;
  background: #0f172a;
}

.goal-note {
  margin: 10px 2px 0;
  color: #8b98a5;
  font-size: 11px;
  line-height: 1.6;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 10px 12px;
  border-top: 1px solid rgba(75, 85, 99, 0.8);
  background: #0a0c12;
}

.dialog-button {
  min-width: 96px;
  height: 30px;
  padding: 0 14px;
  border: 1px solid #4b5563;
  border-radius: 4px;
  color: #e5e7eb;
  background: #151a24;
  cursor: pointer;
  font-size: 13px;
}

.dialog-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.dialog-button.primary {
  border-color: rgba(143, 104, 221, 0.9);
  background: linear-gradient(135deg, #4668cd, #8f68dd);
  font-weight: 700;
}

.dialog-button.danger {
  border-color: rgba(220, 38, 38, 0.7);
  color: #ffd9d9;
  background: rgba(120, 30, 30, 0.55);
}

@media (max-width: 760px) {
  .goal-layout { grid-template-columns: minmax(0, 1fr); }
  .goal-list-body { max-height: 180px; }
}
</style>
