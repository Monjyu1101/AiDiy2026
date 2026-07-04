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
// AIタスク_要求編集ダイアログ: マスタ保守と同じラベル/内容の行レイアウト
// 新規: AI登録 API で仮タスク（準備中）を作成する
// 修正: 更新登録 API で実行中プロセスを停止してからタスク要求を更新する（準備開始で再分解）
import { ref, computed, watch } from 'vue';
import type { PropType } from 'vue';
import apiClient, { taskClient } from '@/api/client';
import { qMessage } from '@/utils/qAlert';

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  利用者ID: { type: String, default: '' },
  編集タスク: { type: Object as PropType<Record<string, any> | null>, default: null }
});
const emit = defineEmits(['close', 'registered']);

const プロジェクト選択肢 = ref<{ value: string; label: string }[]>([]);
const 選択プロジェクト = ref('');
const 入力プロジェクト = ref('');
const 入力要求内容 = ref('');
const 入力TASK_AI_NAME = ref('claude_cli');
const 入力TASK_AI_MODEL = ref('auto');
const 入力有効 = ref(true);
const 入力状況 = ref('準備開始');
const 状況選択肢 = ['準備開始', '中止'];
// 新規時は準備開始で固定、修正時は切替可能
const 状況変更可 = ref(false);
const 登録中 = ref(false);
const 参照中 = ref(false);
const TASK_CODE_MODELS既定 = {
  claude_sdk: { auto: 'auto' },
  claude_cli: { auto: 'auto' },
  copilot_cli: { auto: 'auto' },
  codex_cli: { auto: 'auto' },
  antigravity_cli: { auto: 'auto' },
  opencode_cli: { auto: 'auto' },
  aidiy_hermes: { auto: 'auto' },
};
const availableModels = ref<Record<string, any>>({ code_models: { ...TASK_CODE_MODELS既定 } });
const currentSettings = ref<Record<string, any>>({});
const taskAiOptions = computed(() => Object.keys(availableModels.value?.code_models || {}));
const taskModelOptions = computed(() => {
  const models = availableModels.value?.code_models?.[入力TASK_AI_NAME.value] || {};
  return Object.entries(models).map(([value, label]) => ({ value, label: label || value }));
});

const 修正モード = computed(() => !!props.編集タスク);
const タスクID表示 = computed(() => 修正モード.value ? String(props.編集タスク?.タスクID ?? '') : '(新規)');

const authStorage = window.desktopApi ? localStorage : sessionStorage;
const 最終TASK_AI_NAMEキー = 'ai_task_last_TASK_AI_NAME';
const 最終TASK_AI_MODELキー = 'ai_task_last_TASK_AI_MODEL';

function chooseAvailable(current: any, candidates: string[]) {
  const value = String(current || '');
  return value && candidates.includes(value) ? value : candidates[0] || '';
}

async function モデル選択肢読込() {
  try {
    const res = await apiClient.post('/core/AIコア/モデル情報/TASK選択肢', {});
    if (res.data.status === 'OK') {
      availableModels.value = res.data.data?.available_models || { code_models: {} };
      currentSettings.value = res.data.data?.モデル設定 || {};
      const codeModels = { ...TASK_CODE_MODELS既定, ...(availableModels.value.code_models || {}) };
      for (const ai of Object.keys(codeModels)) {
        if (!codeModels[ai] || Object.keys(codeModels[ai]).length === 0) {
          codeModels[ai] = { auto: 'auto' };
        }
      }
      availableModels.value.code_models = codeModels;
    }
  } catch {
    availableModels.value = { code_models: { ...TASK_CODE_MODELS既定 } };
    currentSettings.value = { TASK_AI_NAME: 'claude_cli', TASK_AI_MODEL: 'auto' };
  }
}

const 選択肢読込 = async () => {
  try {
    const res = await taskClient.post('/task/プロジェクト選択肢', {});
    if (res.data.status === 'OK') {
      const 選択肢 = res.data.data?.選択肢 ?? {};
      プロジェクト選択肢.value = Object.entries(選択肢).map(([value, label]) => ({
        value,
        label: `${label} (${value})`
      }));
    }
  } catch (e) {
    プロジェクト選択肢.value = [];
  }
};

const 入力初期化 = () => {
  if (!props.isOpen) return;
  const 編集 = props.編集タスク;
  選択プロジェクト.value = '';
  入力プロジェクト.value = 編集 ? String(編集.プロジェクト ?? '') : '';
  入力要求内容.value = 編集 ? String(編集.要求内容 ?? '') : '';
  入力有効.value = 編集 ? Boolean(編集.有効) : true;
  入力状況.value = '準備開始';
  状況変更可.value = !!編集;
  void モデル選択肢読込().then(() => {
    const ai候補 = taskAiOptions.value;
    if (編集) {
      入力TASK_AI_NAME.value = chooseAvailable(編集.TASK_AI_NAME || 'claude_cli', ai候補) || 'claude_cli';
      入力TASK_AI_MODEL.value = chooseAvailable(編集.TASK_AI_MODEL || 'auto', Object.keys(availableModels.value?.code_models?.[入力TASK_AI_NAME.value] || {})) || 'auto';
    } else {
      const lastAi = authStorage.getItem(最終TASK_AI_NAMEキー) || currentSettings.value.TASK_AI_NAME || 'claude_cli';
      const lastModel = authStorage.getItem(最終TASK_AI_MODELキー) || currentSettings.value.TASK_AI_MODEL || 'auto';
      入力TASK_AI_NAME.value = chooseAvailable(lastAi, ai候補) || 'claude_cli';
      入力TASK_AI_MODEL.value = chooseAvailable(lastModel, Object.keys(availableModels.value?.code_models?.[入力TASK_AI_NAME.value] || {})) || 'auto';
    }
  });
  void 選択肢読込();
};

watch([() => props.isOpen, () => props.編集タスク], 入力初期化, { immediate: true });

watch(選択プロジェクト, (value) => {
  if (value) 入力プロジェクト.value = value;
});

watch(入力TASK_AI_NAME, (newValue) => {
  const models = Object.keys(availableModels.value?.code_models?.[newValue] || {});
  if (models.length > 0 && !models.includes(入力TASK_AI_MODEL.value)) {
    入力TASK_AI_MODEL.value = models[0]!;
  }
});

const フォルダ参照 = async () => {
  参照中.value = true;
  try {
    const res = await apiClient.post('/core/AIコア/フォルダ参照', {
      初期パス: 入力プロジェクト.value || ''
    });
    if (res.data.status === 'OK') {
      const 選択パス = String(res.data.data?.選択パス ?? '').replace(/\\/g, '/');
      if (選択パス) 入力プロジェクト.value = 選択パス;
    } else {
      void qMessage(res.data.message || 'フォルダ参照に失敗しました。', 'error');
    }
  } catch (e) {
    void qMessage('フォルダ参照でエラーが発生しました。', 'error');
  } finally {
    参照中.value = false;
  }
};

const 登録 = async () => {
  if (!入力要求内容.value.trim()) {
    void qMessage('要求内容を入力してください。', 'error');
    return;
  }
  登録中.value = true;
  try {
    const res = 修正モード.value
      ? await taskClient.post('/task/タスク要求/更新登録', {
          利用者ID: props.利用者ID,
          タスクID: String(props.編集タスク?.タスクID ?? ''),
          プロジェクト: 入力プロジェクト.value.trim(),
          要求内容: 入力要求内容.value.trim(),
          TASK_AI_NAME: 入力TASK_AI_NAME.value.trim() || 'claude_cli',
          TASK_AI_MODEL: 入力TASK_AI_MODEL.value.trim() || 'auto',
          有効: 入力有効.value,
          状況: 入力状況.value
        })
      : await taskClient.post('/task/タスク要求/AI登録', {
          利用者ID: props.利用者ID,
          プロジェクト: 入力プロジェクト.value.trim(),
          要求内容: 入力要求内容.value.trim(),
          TASK_AI_NAME: 入力TASK_AI_NAME.value.trim() || 'claude_cli',
          TASK_AI_MODEL: 入力TASK_AI_MODEL.value.trim() || 'auto',
          有効: 入力有効.value
        });
    if (res.data.status === 'OK') {
      authStorage.setItem(最終TASK_AI_NAMEキー, 入力TASK_AI_NAME.value.trim() || 'claude_cli');
      authStorage.setItem(最終TASK_AI_MODELキー, 入力TASK_AI_MODEL.value.trim() || 'auto');
      void qMessage(res.data.message || 'タスクを準備中として登録しました。');
      emit('registered', res.data.data?.item ?? null);
      emit('close');
    } else {
      void qMessage(res.data.message || 'タスクの登録に失敗しました。', 'error');
    }
  } catch (e) {
    void qMessage('タスクの登録でエラーが発生しました。backend_task (8093) の起動を確認してください。', 'error');
  } finally {
    登録中.value = false;
  }
};
</script>

<template>
  <div v-if="props.isOpen" class="dialog-overlay" @click.self="emit('close')">
    <div class="dialog-content">
      <header class="dialog-header">
        <h3>【タスク要求】{{ 修正モード ? '(修正)' : '(新規)' }}</h3>
        <button class="dialog-close" @click="emit('close')">×</button>
      </header>
      <div class="dialog-body">
        <div class="detail-row">
          <div class="detail-label">タスクID</div>
          <div class="detail-value">
            <span class="value-text">{{ タスクID表示 }}</span>
          </div>
        </div>
        <div class="detail-row">
          <div class="detail-label">プロジェクト</div>
          <div class="detail-value">
            <select v-model="選択プロジェクト" class="detail-select">
              <option value="">候補から選択してください</option>
              <option v-for="opt in プロジェクト選択肢" :key="opt.value" :value="opt.value">
                {{ opt.label }}
              </option>
            </select>
          </div>
        </div>
        <div class="detail-row">
          <div class="detail-label">フォルダ指定</div>
          <div class="detail-value">
            <div class="value-inline">
              <input
                v-model.trim="入力プロジェクト"
                type="text"
                class="detail-input"
                placeholder="../ または C:/project/"
              />
              <button class="dialog-button" :disabled="参照中" @click="フォルダ参照">参照</button>
            </div>
          </div>
        </div>
        <div class="detail-row">
          <div class="detail-label">要求内容<span class="required-mark">*</span></div>
          <div class="detail-value">
            <textarea
              v-model="入力要求内容"
              class="detail-textarea"
              rows="6"
              placeholder="AI に依頼する要求内容を記入してください"
            ></textarea>
          </div>
        </div>
        <div class="detail-row">
          <div class="detail-label">TASK_AI_NAME</div>
          <div class="detail-value">
            <select v-model="入力TASK_AI_NAME" class="detail-select">
              <option v-for="ai in taskAiOptions" :key="ai" :value="ai">{{ ai }}</option>
            </select>
          </div>
        </div>
        <div class="detail-row">
          <div class="detail-label">TASK_AI_MODEL</div>
          <div class="detail-value">
            <select v-model="入力TASK_AI_MODEL" class="detail-select">
              <option v-for="model in taskModelOptions" :key="model.value" :value="model.value">{{ model.label }}</option>
            </select>
          </div>
        </div>
        <div class="detail-row">
          <div class="detail-label">有効</div>
          <div class="detail-value">
            <label class="valid-checkbox-label">
              <input
                v-model="入力有効"
                type="checkbox"
                class="valid-checkbox"
                aria-label="有効の切り替え"
              />
              <span class="valid-checkbox-mark" :class="{ 'valid-checkbox-inactive': !入力有効 }">{{ 入力有効 ? '✅' : '☐' }}</span>
            </label>
          </div>
        </div>
        <div class="detail-row">
          <div class="detail-label">状況</div>
          <div class="detail-value">
            <div class="status-segment">
              <button
                v-for="状況 in 状況選択肢"
                :key="状況"
                type="button"
                class="segment-btn"
                :class="{ active: 入力状況 === 状況 }"
                :disabled="!状況変更可"
                @click="入力状況 = 状況"
              >{{ 状況 }}</button>
            </div>
          </div>
        </div>
      </div>
      <footer class="dialog-footer">
        <button class="dialog-button" @click="emit('close')">キャンセル</button>
        <button class="dialog-button primary" :disabled="登録中" @click="登録">
          {{ 登録中 ? '登録中...' : '登録' }}
        </button>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.72);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.dialog-content {
  background: #07080c;
  color: #e5e7eb;
  width: 560px;
  max-width: 92%;
  border: 1px solid rgba(143, 104, 221, 0.75);
  border-radius: 4px;
  box-shadow: 0 0 24px rgba(60, 42, 128, 0.65);
  display: flex;
  flex-direction: column;
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 8px 0 14px;
  height: 32px;
  box-sizing: border-box;
  background: linear-gradient(135deg, rgba(70, 104, 205, 0.96), rgba(108, 78, 196, 0.96), rgba(143, 104, 221, 0.92));
  border-bottom: 1px solid rgba(93, 68, 168, 0.95);
  border-radius: 4px 4px 0 0;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.16),
    inset 0 -1px 0 rgba(18, 18, 38, 0.45);
}

.dialog-header h3 {
  margin: 0;
  font-size: 13px;
  font-weight: bold;
  color: #fff;
  letter-spacing: 1px;
}

.dialog-close {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.86);
  font-size: 18px;
  cursor: pointer;
}

.dialog-close:hover {
  color: #fff;
}

.dialog-body {
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 0;
  background: #07080c;
}

/* マスタ保守と同じラベル / 内容の行レイアウト */
.detail-row {
  display: flex;
  width: 100%;
  margin-top: -1px;
}

.detail-label {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  color: #ffffff;
  font-weight: 600;
  font-size: 13px;
  text-align: right;
  padding: 8px 12px;
  border: 1px solid rgba(93, 68, 168, 0.85);
  background: linear-gradient(135deg, rgba(55, 71, 79, 0.98), rgba(70, 104, 205, 0.74));
  min-height: 40px;
  width: 120px;
  flex-shrink: 0;
  box-sizing: border-box;
  z-index: 1;
}

.detail-value {
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 0;
  color: #e5e7eb;
  padding: 4px 12px;
  border: 1px solid rgba(75, 85, 99, 0.95);
  border-left: none;
  background: #10131a;
  min-height: 40px;
  box-sizing: border-box;
}

.required-mark {
  color: #dc2626;
  margin-left: 2px;
}

.value-text {
  font-size: 14px;
}

.value-inline {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  min-width: 0;
  flex-wrap: nowrap;
}

.detail-input,
.detail-select,
.detail-textarea {
  width: 100%;
  padding: 4px 8px;
  border: 1px solid #4b5563;
  border-radius: 4px;
  background: #05070b;
  color: #f3f4f6;
  font-size: 14px;
  font-family: inherit;
  box-sizing: border-box;
}

.detail-input::placeholder,
.detail-textarea::placeholder {
  color: #6b7280;
}

.detail-input {
  height: 28px;
  padding: 0 8px;
  min-width: 0;
}

.detail-select {
  height: 28px;
}

.detail-textarea {
  margin: 4px 0;
  resize: vertical;
}

.detail-input:focus,
.detail-select:focus,
.detail-textarea:focus {
  outline: none;
  border-color: #8f68dd;
  box-shadow: inset 0 0 0 1px rgba(143, 104, 221, 0.35);
}

/* マスタ保守と同じ有効欄（入力欄風ボックス + 中央の ✅/☐） */
.valid-checkbox-label {
  width: 320px;
  min-height: 28px;
  padding: 0 8px;
  border: 1px solid #4b5563;
  border-radius: 4px;
  background: #05070b;
  box-sizing: border-box;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 14px;
  user-select: none;
  color: #16a34a;
  font-weight: 700;
  gap: 0;
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
  line-height: 1;
  font-size: 16px;
  color: #16a34a;
}

.valid-checkbox-inactive {
  color: #d1d5db;
}

.status-segment {
  display: flex;
  gap: 6px;
}

.segment-btn {
  background: #05070b;
  color: #cbd5e1;
  border: 1px solid #4b5563;
  border-radius: 4px;
  padding: 4px 14px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.segment-btn.active {
  color: #fff;
  border-color: #8f68dd;
  background: rgba(108, 78, 196, 0.85);
  font-weight: 600;
}

.segment-btn:disabled {
  cursor: default;
}

.segment-btn:disabled:not(.active) {
  opacity: 0.4;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 10px 14px;
  border-top: 1px solid rgba(93, 68, 168, 0.85);
  background: #07080c;
}

.dialog-button {
  background: #1f2937;
  color: #f3f4f6;
  border: 1px solid #4b5563;
  border-radius: 0;
  padding: 6px 16px;
  font-size: 13px;
  white-space: nowrap;
  cursor: pointer;
  transition: all 0.2s ease;
}

.value-inline .dialog-button {
  flex: 0 0 56px;
  height: 28px;
  padding: 0 10px;
}

.dialog-button:hover {
  border-color: #8f68dd;
}

.dialog-button.primary {
  background: #28a745;
  color: #fff;
  border-color: #28a745;
}

.dialog-button.primary:hover {
  background: #1e7e34;
  border-color: #1e7e34;
}

.dialog-button:disabled {
  opacity: 0.5;
  cursor: default;
}
</style>
