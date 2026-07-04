<script setup lang="ts">
// AIタスク_明細編集ダイアログ: タスク明細 1 行の内容を修正する
import { ref, computed, watch } from 'vue';
import type { PropType } from 'vue';
import apiClient from '../../../api/client';
import { qMessage } from '../../../utils/qAlert';
import { useAuthStore } from '../../../stores/auth';

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  編集明細: { type: Object as PropType<Record<string, any> | null>, default: null }
});
const emit = defineEmits(['close', 'registered']);

const authStore = useAuthStore();
const 利用者ID = computed(() => String(authStore.user?.利用者ID ?? ''));

const 入力タイトル = ref('');
const 入力要求内容 = ref('');
const 入力先行SEQ = ref('');
const 入力TASK_AI_NAME = ref('claude_cli');
const 入力TASK_AI_MODEL = ref('auto');
const 入力有効 = ref(true);
const 入力状態 = ref('待機');
const 状態選択肢 = ['待機', '完了', '失敗'];
const 登録中 = ref(false);
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

const タスクID表示 = computed(() => String(props.編集明細?.タスクID ?? ''));
const 明細SEQ表示 = computed(() => String(props.編集明細?.明細SEQ ?? ''));

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

watch(() => props.isOpen, (open) => {
  if (!open) return;
  const 編集 = props.編集明細 ?? {};
  入力タイトル.value = String(編集.タイトル ?? '');
  入力要求内容.value = String(編集.要求内容 ?? '');
  入力先行SEQ.value = String(編集.先行SEQ ?? '');
  void モデル選択肢読込().then(() => {
    入力TASK_AI_NAME.value = chooseAvailable(編集.TASK_AI_NAME || currentSettings.value.TASK_AI_NAME || 'claude_cli', taskAiOptions.value) || 'claude_cli';
    入力TASK_AI_MODEL.value = chooseAvailable(編集.TASK_AI_MODEL || currentSettings.value.TASK_AI_MODEL || 'auto', Object.keys(availableModels.value?.code_models?.[入力TASK_AI_NAME.value] || {})) || 'auto';
  });
  入力有効.value = Boolean(編集.有効);
  const 状態 = String(編集.状態 ?? '待機');
  入力状態.value = 状態選択肢.includes(状態) ? 状態 : '待機';
});

watch(入力TASK_AI_NAME, (newValue) => {
  const models = Object.keys(availableModels.value?.code_models?.[newValue] || {});
  if (models.length > 0 && !models.includes(入力TASK_AI_MODEL.value)) {
    入力TASK_AI_MODEL.value = models[0]!;
  }
});

const 登録 = async () => {
  const タイトル = 入力タイトル.value.trim();
  if (!タイトル) {
    void qMessage('タイトルを入力してください。', 'error');
    return;
  }
  登録中.value = true;
  try {
    const res = await apiClient.post('/task/タスク明細/更新登録', {
      利用者ID: 利用者ID.value,
      タスクID: タスクID表示.value,
      明細SEQ: Number(props.編集明細?.明細SEQ ?? 0),
      タイトル,
      要求内容: 入力要求内容.value.trim(),
      先行SEQ: 入力先行SEQ.value.trim(),
      TASK_AI_NAME: 入力TASK_AI_NAME.value.trim() || 'claude_cli',
      TASK_AI_MODEL: 入力TASK_AI_MODEL.value.trim() || 'auto',
      有効: 入力有効.value,
      状態: 入力状態.value
    });
    if (res.data.status === 'OK') {
      void qMessage(res.data.message || 'タスク明細を更新しました。');
      emit('registered', res.data.data?.item ?? null);
      emit('close');
    } else {
      void qMessage(res.data.message || 'タスク明細の更新に失敗しました。', 'error');
    }
  } catch (e) {
    void qMessage('タスク明細の更新でエラーが発生しました。backend_task (8093) の起動を確認してください。', 'error');
  } finally {
    登録中.value = false;
  }
};
</script>

<template>
  <div v-if="props.isOpen" class="dialog-overlay" @click.self="emit('close')">
    <div class="dialog-content">
      <header class="dialog-header">
        <h3>【タスク明細】(修正)</h3>
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
          <div class="detail-label">SEQ</div>
          <div class="detail-value">
            <span class="value-text">{{ 明細SEQ表示 }}</span>
          </div>
        </div>
        <div class="detail-row">
          <div class="detail-label">タイトル<span class="required-mark">*</span></div>
          <div class="detail-value">
            <input
              v-model.trim="入力タイトル"
              type="text"
              class="detail-input"
              placeholder="明細タイトル"
            />
          </div>
        </div>
        <div class="detail-row">
          <div class="detail-label">要求内容</div>
          <div class="detail-value">
            <textarea
              v-model="入力要求内容"
              class="detail-textarea"
              rows="7"
              placeholder="この明細で実行する内容"
            ></textarea>
          </div>
        </div>
        <div class="detail-row">
          <div class="detail-label">先行SEQ</div>
          <div class="detail-value">
            <input
              v-model.trim="入力先行SEQ"
              type="text"
              class="detail-input"
              placeholder="0 または 1,2"
            />
          </div>
        </div>
        <div class="detail-row one-line-row">
          <div class="detail-label">TASK_AI_NAME</div>
          <div class="detail-value">
            <select v-model="入力TASK_AI_NAME" class="detail-select">
              <option v-for="ai in taskAiOptions" :key="ai" :value="ai">{{ ai }}</option>
            </select>
          </div>
        </div>
        <div class="detail-row one-line-row">
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
          <div class="detail-label">状態</div>
          <div class="detail-value">
            <div class="status-segment">
              <button
                v-for="状態 in 状態選択肢"
                :key="状態"
                type="button"
                class="segment-btn"
                :class="{ active: 入力状態 === 状態 }"
                @click="入力状態 = 状態"
              >{{ 状態 }}</button>
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
  width: 640px;
  max-width: 92%;
  max-height: 92vh;
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
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 0;
  background: #07080c;
  overflow-y: auto;
}

.detail-row {
  display: flex;
  width: 100%;
  margin-top: -1px;
  flex: 0 0 auto;
}

.detail-label {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  color: #ffffff;
  font-weight: 600;
  font-size: 13px;
  text-align: right;
  padding: 6px 10px;
  border: 1px solid rgba(93, 68, 168, 0.85);
  background: linear-gradient(135deg, rgba(55, 71, 79, 0.98), rgba(70, 104, 205, 0.74));
  min-height: 34px;
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
  padding: 3px 10px;
  border: 1px solid rgba(75, 85, 99, 0.95);
  border-left: none;
  background: #10131a;
  min-height: 34px;
  box-sizing: border-box;
}

.required-mark {
  color: #dc2626;
  margin-left: 2px;
}

.value-text {
  font-size: 14px;
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
  height: 26px;
  margin: 0;
  padding: 0 8px;
}

.detail-select {
  display: block;
  height: 26px;
  min-height: 26px;
  margin: 0;
  padding: 0 28px 0 8px;
  line-height: normal;
  appearance: auto;
  align-self: center;
}

.one-line-row,
.one-line-row .detail-label,
.one-line-row .detail-value {
  height: 34px;
  min-height: 34px;
}

.one-line-row .detail-value {
  align-items: center;
  padding-top: 4px;
  padding-bottom: 4px;
}

.detail-textarea {
  margin: 3px 0;
  min-height: 92px;
  max-height: 180px;
  resize: vertical;
}

.detail-input:focus,
.detail-select:focus,
.detail-textarea:focus {
  outline: none;
  border-color: #8f68dd;
  box-shadow: inset 0 0 0 1px rgba(143, 104, 221, 0.35);
}

.valid-checkbox-label {
  width: 320px;
  height: 26px;
  min-height: 26px;
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

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 8px 12px;
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
  cursor: pointer;
  transition: all 0.2s ease;
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
