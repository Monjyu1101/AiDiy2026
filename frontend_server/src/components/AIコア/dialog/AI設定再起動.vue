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
import { ref, watch, reactive, computed, nextTick } from 'vue';
import { useRoute } from 'vue-router';
import apiClient from '@/api/client';
import RebootDialog from './再起動カウントダウン.vue';

const route = useRoute();

const props = defineProps<{
  isOpen: boolean;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'saved'): void;
}>();

const loading = ref(false);
const errorMessage = ref('');
const availableModels = ref<Record<string, any>>({});
const currentSettings = ref<Record<string, any>>({});
const codeBaseOptions = ref<Record<string, string>>({});
const showRebootDialog = ref(false);
const isInitializing = ref(false);

const selections = reactive({
  chatAi: '',
  chatModel: '',
  liveAi: '',
  liveModel: '',
  liveVoice: '',
  codeAi1: '',
  codeModel1: '',
  codeAi2: '',
  codeModel2: '',
  codeAi3: '',
  codeModel3: '',
  codeAi4: '',
  codeModel4: '',
  codeBasePath: ''
});

const CHAT_MODEL_KEYS: Record<string, string> = {
  gemini: 'CHAT_GEMINI_MODEL',
  freeai: 'CHAT_FREEAI_MODEL',
  openrt: 'CHAT_OPENRT_MODEL'
};

const LIVE_MODEL_KEYS: Record<string, string> = {
  gemini: 'LIVE_GEMINI_MODEL',
  freeai: 'LIVE_FREEAI_MODEL',
  openai: 'LIVE_OPENAI_MODEL'
};

const LIVE_VOICE_KEYS: Record<string, string> = {
  gemini: 'LIVE_GEMINI_VOICE',
  freeai: 'LIVE_FREEAI_VOICE',
  openai: 'LIVE_OPENAI_VOICE'
};

const CODE_MODEL_KEYS: Record<string, string> = {
  claude_sdk: 'CODE_CLAUDE_SDK_MODEL',
  claude_cli: 'CODE_CLAUDE_CLI_MODEL',
  copilot_cli: 'CODE_COPILOT_CLI_MODEL',
  gemini_cli: 'CODE_GEMINI_CLI_MODEL',
  codex_cli: 'CODE_CODEX_CLI_MODEL'
};

const chatAiOptions = computed(() => Object.keys(availableModels.value?.chat_models || {}));
const liveAiOptions = computed(() => Object.keys(availableModels.value?.live_models || {}));
const codeAiOptions = computed(() => Object.keys(availableModels.value?.code_models || {}));

const chatModelOptions = computed(() => {
  const models = availableModels.value?.chat_models?.[selections.chatAi] || {};
  return Object.entries(models).map(([value, label]) => ({ value, label: label || value }));
});

const liveModelOptions = computed(() => {
  const models = availableModels.value?.live_models?.[selections.liveAi] || {};
  return Object.entries(models).map(([value, label]) => ({ value, label: label || value }));
});

const liveVoiceOptions = computed(() => {
  const voices = availableModels.value?.live_voices?.[selections.liveAi] || {};
  return Object.entries(voices).map(([value, label]) => ({ value, label: label || value }));
});

const codeModelOptions1 = computed(() => {
  const models = availableModels.value?.code_models?.[selections.codeAi1] || {};
  return Object.entries(models).map(([value, label]) => ({ value, label: label || value }));
});

const codeModelOptions2 = computed(() => {
  const models = availableModels.value?.code_models?.[selections.codeAi2] || {};
  return Object.entries(models).map(([value, label]) => ({ value, label: label || value }));
});

const codeModelOptions3 = computed(() => {
  const models = availableModels.value?.code_models?.[selections.codeAi3] || {};
  return Object.entries(models).map(([value, label]) => ({ value, label: label || value }));
});

const codeModelOptions4 = computed(() => {
  const models = availableModels.value?.code_models?.[selections.codeAi4] || {};
  return Object.entries(models).map(([value, label]) => ({ value, label: label || value }));
});

const codeBasePath = computed(() => selections.codeBasePath || currentSettings.value?.CODE_BASE_PATH || '');
const codeBaseOptionsList = computed(() =>
  Object.entries(codeBaseOptions.value || {}).map(([value, label]) => ({ value, label }))
);

const loadConfig = async () => {
  loading.value = true;
  errorMessage.value = '';
  try {
    // URLからソケットIDを取得
    const ソケットID = (route.query.セッションID as string) || (route.query.ソケットID as string);

    if (!ソケットID) {
      errorMessage.value = 'ソケットIDが見つかりません。画面をリロードしてください。';
      loading.value = false;
      return;
    }

    const response = await apiClient.post('/core/AIコア/モデル情報/取得', {
      ソケットID
    });

    if (response?.data?.status === 'OK') {
      const data = response.data.data;
      availableModels.value = data.available_models || {};
      currentSettings.value = data.モデル設定 || {};
      codeBaseOptions.value = data.external_root_dic || {};

      isInitializing.value = true;
      const chatModels = availableModels.value.chat_models || {};
      const liveModels = availableModels.value.live_models || {};
      const liveVoices = availableModels.value.live_voices || {};
      const codeModels = availableModels.value.code_models || {};

      selections.chatAi = currentSettings.value.CHAT_AI || chatAiOptions.value[0] || '';
      selections.liveAi = currentSettings.value.LIVE_AI || liveAiOptions.value[0] || '';
      selections.codeAi1 = currentSettings.value.CODE_AI1 || codeAiOptions.value[0] || '';
      selections.codeAi2 = currentSettings.value.CODE_AI2 || codeAiOptions.value[0] || '';
      selections.codeAi3 = currentSettings.value.CODE_AI3 || codeAiOptions.value[0] || '';
      selections.codeAi4 = currentSettings.value.CODE_AI4 || codeAiOptions.value[0] || '';
      selections.codeBasePath = currentSettings.value.CODE_BASE_PATH || Object.keys(codeBaseOptions.value || {})[0] || '';

      const chatKey = CHAT_MODEL_KEYS[selections.chatAi];
      selections.chatModel = (chatKey && currentSettings.value[chatKey]) || Object.keys(chatModels?.[selections.chatAi] || {})[0] || '';

      const liveKey = LIVE_MODEL_KEYS[selections.liveAi];
      selections.liveModel = (liveKey && currentSettings.value[liveKey]) || Object.keys(liveModels?.[selections.liveAi] || {})[0] || '';

      const voiceKey = LIVE_VOICE_KEYS[selections.liveAi];
      selections.liveVoice = (voiceKey && currentSettings.value[voiceKey]) || Object.keys(liveVoices?.[selections.liveAi] || {})[0] || '';

      selections.codeModel1 = currentSettings.value.CODE_AI1_MODEL || Object.keys(codeModels?.[selections.codeAi1] || {})[0] || '';
      selections.codeModel2 = currentSettings.value.CODE_AI2_MODEL || Object.keys(codeModels?.[selections.codeAi2] || {})[0] || '';
      selections.codeModel3 = currentSettings.value.CODE_AI3_MODEL || Object.keys(codeModels?.[selections.codeAi3] || {})[0] || '';
      selections.codeModel4 = currentSettings.value.CODE_AI4_MODEL || Object.keys(codeModels?.[selections.codeAi4] || {})[0] || '';
      await nextTick();
      isInitializing.value = false;
    } else {
      errorMessage.value = response?.data?.message || '取得に失敗しました';
    }
  } catch (error: any) {
    errorMessage.value = `取得エラー: ${error?.response?.data?.message || error?.message || error}`;
  } finally {
    if (isInitializing.value) {
      await nextTick();
      isInitializing.value = false;
    }
    loading.value = false;
  }
};

const handleCancel = () => {
  emit('close');
};

const handleSave = async () => {
  loading.value = true;
  errorMessage.value = '';
  try {
    // URLからソケットIDを取得
    const ソケットID = (route.query.セッションID as string) || (route.query.ソケットID as string);

    if (!ソケットID) {
      errorMessage.value = 'ソケットIDが見つかりません。画面をリロードしてください。';
      loading.value = false;
      return;
    }

    const nextSettings = { ...currentSettings.value };
    nextSettings.CHAT_AI = selections.chatAi;
    nextSettings.LIVE_AI = selections.liveAi;
    nextSettings.CODE_AI1 = selections.codeAi1;
    nextSettings.CODE_AI1_MODEL = selections.codeModel1;
    nextSettings.CODE_AI2 = selections.codeAi2;
    nextSettings.CODE_AI2_MODEL = selections.codeModel2;
    nextSettings.CODE_AI3 = selections.codeAi3;
    nextSettings.CODE_AI3_MODEL = selections.codeModel3;
    nextSettings.CODE_AI4 = selections.codeAi4;
    nextSettings.CODE_AI4_MODEL = selections.codeModel4;
    if (selections.codeBasePath) {
      nextSettings.CODE_BASE_PATH = selections.codeBasePath;
    }

    const chatKey = CHAT_MODEL_KEYS[selections.chatAi];
    if (chatKey) {
      nextSettings[chatKey] = selections.chatModel;
    }

    const liveKey = LIVE_MODEL_KEYS[selections.liveAi];
    if (liveKey) {
      nextSettings[liveKey] = selections.liveModel;
    }

    const voiceKey = LIVE_VOICE_KEYS[selections.liveAi];
    if (voiceKey) {
      nextSettings[voiceKey] = selections.liveVoice;
    }

    const response = await apiClient.post('/core/AIコア/モデル情報/設定', {
      ソケットID,
      モデル設定: nextSettings,
      再起動要求: {
        reboot1: false,
        reboot2: true
      }
    });

    if (response?.data?.status === 'OK') {
      // emit('saved'); // Replaced by reload
      // emit('close'); // Replaced by reload
      showRebootDialog.value = true;
    } else {
      errorMessage.value = response?.data?.message || '保存に失敗しました';
    }
  } catch (error: any) {
    errorMessage.value = `保存エラー: ${error?.response?.data?.message || error?.message || error}`;
  } finally {
    loading.value = false;
  }
};

watch(
  () => selections.chatAi,
  (newValue) => {
    const models = availableModels.value?.chat_models?.[newValue] || {};
    const key = CHAT_MODEL_KEYS[newValue];
    selections.chatModel = (key && currentSettings.value[key]) || Object.keys(models)[0] || '';
  }
);

watch(
  () => selections.liveAi,
  (newValue) => {
    const models = availableModels.value?.live_models?.[newValue] || {};
    const voices = availableModels.value?.live_voices?.[newValue] || {};
    const modelKey = LIVE_MODEL_KEYS[newValue];
    const voiceKey = LIVE_VOICE_KEYS[newValue];
    selections.liveModel = (modelKey && currentSettings.value[modelKey]) || Object.keys(models)[0] || '';
    selections.liveVoice = (voiceKey && currentSettings.value[voiceKey]) || Object.keys(voices)[0] || '';
  }
);

watch(
  () => selections.codeAi1,
  (newValue) => {
    if (isInitializing.value) return;
    const models = availableModels.value?.code_models?.[newValue] || {};
    const newModel = currentSettings.value.CODE_AI1_MODEL || Object.keys(models)[0] || '';
    selections.codeModel1 = newModel;
    // AI1変更時、AI2-4に両方（AIとMODEL）をコピー
    selections.codeAi2 = newValue;
    selections.codeAi3 = newValue;
    selections.codeAi4 = newValue;
    selections.codeModel2 = selections.codeModel1;
    selections.codeModel3 = selections.codeModel1;
    selections.codeModel4 = selections.codeModel1;
  }
);

watch(
  () => selections.codeModel1,
  (newValue) => {
    if (isInitializing.value) return;
    // AI1_MODEL変更時、AI2-4に両方（AIとMODEL）をコピー
    selections.codeAi2 = selections.codeAi1;
    selections.codeAi3 = selections.codeAi1;
    selections.codeAi4 = selections.codeAi1;
    selections.codeModel2 = newValue;
    selections.codeModel3 = newValue;
    selections.codeModel4 = newValue;
  }
);

watch(
  () => selections.codeAi2,
  (newValue) => {
    if (isInitializing.value) return;
    // AI2個別変更時は、現在のモデル値を維持（AI1の影響を受けない）
    if (!availableModels.value?.code_models?.[newValue]) return;
    const models = Object.keys(availableModels.value.code_models[newValue]);
    if (models.length > 0 && !models.includes(selections.codeModel2)) {
      selections.codeModel2 = models[0];
    }
  }
);

watch(
  () => selections.codeAi3,
  (newValue) => {
    if (isInitializing.value) return;
    // AI3個別変更時は、現在のモデル値を維持（AI1の影響を受けない）
    if (!availableModels.value?.code_models?.[newValue]) return;
    const models = Object.keys(availableModels.value.code_models[newValue]);
    if (models.length > 0 && !models.includes(selections.codeModel3)) {
      selections.codeModel3 = models[0];
    }
  }
);

watch(
  () => selections.codeAi4,
  (newValue) => {
    if (isInitializing.value) return;
    // AI4個別変更時は、現在のモデル値を維持（AI1の影響を受けない）
    if (!availableModels.value?.code_models?.[newValue]) return;
    const models = Object.keys(availableModels.value.code_models[newValue]);
    if (models.length > 0 && !models.includes(selections.codeModel4)) {
      selections.codeModel4 = models[0];
    }
  }
);

watch(
  () => props.isOpen,
  (isOpen) => {
    if (isOpen) {
      loadConfig();
    }
  }
);
</script>

<template>
  <div
    v-if="isOpen"
    class="config-panel-overlay"
    role="dialog"
    aria-modal="true"
    aria-labelledby="configPanelTitle"
    @click.self="handleCancel"
  >
    <div class="config-panel" role="document">
      <div class="config-panel-header" id="configPanelTitle">
        <button class="config-panel-close" type="button" @click="handleCancel">×</button>
        <div class="config-panel-title">モデル設定 / 再起動</div>
        <div class="config-panel-spacer" aria-hidden="true"></div>
      </div>
      <div class="config-panel-body">
        <p v-if="loading" class="config-panel-placeholder">設定を読み込み中です…</p>
        <p v-else-if="errorMessage" class="config-panel-error">{{ errorMessage }}</p>
        <div v-else class="config-panel-content">
          <p class="config-panel-description">AI設定を選択してください。</p>
          <div class="config-panel-form">
            <div class="config-panel-section">
              <div class="config-panel-section-header">Chat AI</div>
              <div class="config-panel-field">
                <label class="config-panel-label" for="config-chat-ai-select">CHAT_AI:</label>
                <div class="config-panel-control">
                  <select id="config-chat-ai-select" v-model="selections.chatAi" class="config-panel-select">
                    <option v-for="ai in chatAiOptions" :key="ai" :value="ai">{{ ai }}</option>
                  </select>
                </div>
              </div>
              <div class="config-panel-field">
                <label class="config-panel-label" for="config-chat-model-select">CHAT_MODEL:</label>
                <div class="config-panel-control">
                  <select id="config-chat-model-select" v-model="selections.chatModel" class="config-panel-select">
                    <option v-for="model in chatModelOptions" :key="model.value" :value="model.value">{{ model.label }}</option>
                  </select>
                </div>
              </div>
            </div>

            <div class="config-panel-section">
              <div class="config-panel-section-header">Live AI</div>
              <div class="config-panel-field">
                <label class="config-panel-label" for="config-live-ai-select">LIVE_AI:</label>
                <div class="config-panel-control">
                  <select id="config-live-ai-select" v-model="selections.liveAi" class="config-panel-select">
                    <option v-for="ai in liveAiOptions" :key="ai" :value="ai">{{ ai }}</option>
                  </select>
                </div>
              </div>
              <div class="config-panel-field">
                <label class="config-panel-label" for="config-live-model-select">LIVE_MODEL:</label>
                <div class="config-panel-control">
                  <select id="config-live-model-select" v-model="selections.liveModel" class="config-panel-select">
                    <option v-for="model in liveModelOptions" :key="model.value" :value="model.value">{{ model.label }}</option>
                  </select>
                </div>
              </div>
              <div class="config-panel-field">
                <label class="config-panel-label" for="config-live-voice-select">LIVE_VOICE:</label>
                <div class="config-panel-control">
                  <select id="config-live-voice-select" v-model="selections.liveVoice" class="config-panel-select">
                    <option v-for="voice in liveVoiceOptions" :key="voice.value" :value="voice.value">{{ voice.label }}</option>
                  </select>
                </div>
              </div>
            </div>

            <div class="config-panel-section">
              <div class="config-panel-section-header">Code AI</div>
              <div v-if="codeBaseOptionsList.length > 0" class="config-panel-field">
                <label class="config-panel-label" for="config-code-base-path">CODE_BASE_PATH:</label>
                <div class="config-panel-control">
                  <select
                    id="config-code-base-path"
                    v-model="selections.codeBasePath"
                    class="config-panel-select"
                  >
                    <option v-for="opt in codeBaseOptionsList" :key="opt.value" :value="opt.value">
                      {{ opt.label }}
                    </option>
                  </select>
                </div>
              </div>
              <div class="config-panel-field">
                <label class="config-panel-label" for="config-code-ai1-select">CODE_AI1:</label>
                <div class="config-panel-control">
                  <select id="config-code-ai1-select" v-model="selections.codeAi1" class="config-panel-select">
                    <option v-for="ai in codeAiOptions" :key="ai" :value="ai">{{ ai }}</option>
                  </select>
                </div>
              </div>
              <div class="config-panel-field">
                <label class="config-panel-label" for="config-code-model1-select">CODE_MODEL1:</label>
                <div class="config-panel-control">
                  <select id="config-code-model1-select" v-model="selections.codeModel1" class="config-panel-select">
                    <option v-for="model in codeModelOptions1" :key="model.value" :value="model.value">{{ model.label }}</option>
                  </select>
                </div>
              </div>
              <div class="config-panel-field">
                <label class="config-panel-label" for="config-code-ai2-select">CODE_AI2:</label>
                <div class="config-panel-control">
                  <select id="config-code-ai2-select" v-model="selections.codeAi2" class="config-panel-select">
                    <option v-for="ai in codeAiOptions" :key="ai" :value="ai">{{ ai }}</option>
                  </select>
                </div>
              </div>
              <div class="config-panel-field">
                <label class="config-panel-label" for="config-code-model2-select">CODE_MODEL2:</label>
                <div class="config-panel-control">
                  <select id="config-code-model2-select" v-model="selections.codeModel2" class="config-panel-select">
                    <option v-for="model in codeModelOptions2" :key="model.value" :value="model.value">{{ model.label }}</option>
                  </select>
                </div>
              </div>
              <div class="config-panel-field">
                <label class="config-panel-label" for="config-code-ai3-select">CODE_AI3:</label>
                <div class="config-panel-control">
                  <select id="config-code-ai3-select" v-model="selections.codeAi3" class="config-panel-select">
                    <option v-for="ai in codeAiOptions" :key="ai" :value="ai">{{ ai }}</option>
                  </select>
                </div>
              </div>
              <div class="config-panel-field">
                <label class="config-panel-label" for="config-code-model3-select">CODE_MODEL3:</label>
                <div class="config-panel-control">
                  <select id="config-code-model3-select" v-model="selections.codeModel3" class="config-panel-select">
                    <option v-for="model in codeModelOptions3" :key="model.value" :value="model.value">{{ model.label }}</option>
                  </select>
                </div>
              </div>
              <div class="config-panel-field">
                <label class="config-panel-label" for="config-code-ai4-select">CODE_AI4:</label>
                <div class="config-panel-control">
                  <select id="config-code-ai4-select" v-model="selections.codeAi4" class="config-panel-select">
                    <option v-for="ai in codeAiOptions" :key="ai" :value="ai">{{ ai }}</option>
                  </select>
                </div>
              </div>
              <div class="config-panel-field">
                <label class="config-panel-label" for="config-code-model4-select">CODE_MODEL4:</label>
                <div class="config-panel-control">
                  <select id="config-code-model4-select" v-model="selections.codeModel4" class="config-panel-select">
                    <option v-for="model in codeModelOptions4" :key="model.value" :value="model.value">{{ model.label }}</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="config-panel-actions">
        <button type="button" @click="handleCancel">キャンセル</button>
        <button type="button" class="primary" :disabled="loading" @click="handleSave">設定/再起動</button>
      </div>
    </div>
  </div>

  <RebootDialog :show="showRebootDialog" :wait-seconds="15" />
</template>

<style scoped>
.config-panel-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.config-panel {
  width: min(720px, 92vw);
  max-height: 90vh;
  background: #ffffff;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.25);
  display: flex;
  flex-direction: column;
  border: 1px solid #e2e8f0;
}

.config-panel-header {
  padding: 8px 12px;
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  letter-spacing: 0.02em;
  display: grid;
  grid-template-columns: 28px 1fr 28px;
  align-items: center;
}

.config-panel-title {
  text-align: center;
}

.config-panel-close {
  width: 24px;
  height: 24px;
  border: 1px solid #cbd5f5;
  background: #ffffff;
  color: #0f172a;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
}

.config-panel-close:hover {
  background: #eff6ff;
}

.config-panel-spacer {
  width: 24px;
  height: 24px;
}

.config-panel-body {
  padding: 8px 12px;
  background: #ffffff;
  overflow-y: auto;
  flex: 1;
}

.config-panel-placeholder {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
}

.config-panel-error {
  margin: 0;
  padding: 12px;
  background: #fee2e2;
  border: 1px solid #dc2626;
  border-radius: 6px;
  color: #b91c1c;
  font-size: 14px;
  font-weight: 600;
}

.config-panel-description {
  margin: 0 0 4px 0;
  color: #475569;
  font-size: 11px;
}

.config-panel-form {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.config-panel-section {
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  padding: 4px 8px 2px 8px;
  display: flex;
  flex-direction: column;
  gap: 0;
  background: #eef2f7;
}

.config-panel-section-header {
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 2px 0;
  font-size: 11px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  border-left: 3px solid #2563eb;
  padding-left: 6px;
}

.config-panel-field {
  display: grid;
  grid-template-columns: 120px 1fr;
  gap: 4px;
  align-items: center;
  padding: 0;
  margin: 0;
  background: transparent;
  border: none;
  border-radius: 0;
}

.config-panel-label {
  font-size: 11px;
  color: #334155;
  text-align: right;
  margin: 0;
  padding: 0;
}

.config-panel-control {
  width: 100%;
  margin: 0;
  padding: 0;
}

.config-panel-select {
  width: 100%;
  height: 22px;
  border: 1px solid #cbd5f5;
  border-radius: 3px;
  padding: 0 4px;
  font-size: 11px;
  background: #ffffff;
  color: #0f172a;
  margin: 0;
}


.config-panel-actions {
  padding: 8px 12px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
}

.config-panel-actions button {
  border: 1px solid #cbd5f5;
  background: #ffffff;
  color: #0f172a;
  padding: 6px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.config-panel-actions button:hover:not(:disabled) {
  background: #eff6ff;
}

.config-panel-actions button.primary {
  background: #2563eb;
  border-color: #2563eb;
  color: #ffffff;
}

.config-panel-actions button.primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.config-panel-actions button.primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 1000px) {
  .config-panel-field {
    grid-template-columns: 1fr;
  }
}
</style>
