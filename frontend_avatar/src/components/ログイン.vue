<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  loading: boolean;
  errorMessage: string;
  versions?: {
    chrome?: string;
    electron?: string;
    node?: string;
  };
}>()

const emit = defineEmits<{
  submit: [payload: { 利用者ID: string; パスワード: string }];
}>()

const 利用者ID = ref(localStorage.getItem('avatar_last_user') || 'admin')
const パスワード = ref('********')

function submit() {
  emit('submit', { 利用者ID: 利用者ID.value, パスワード: パスワード.value })
}
</script>

<template>
  <section class="login-shell">
    <form class="login-card" @submit.prevent="submit">
      <div class="title-bar" title="ここをドラッグして移動">
        <span class="title-dot"></span>
        <p class="title-text">AiDiy Desktop Avatar</p>
      </div>

      <div class="card-head">
        <p class="card-eyebrow">利用者認証</p>
      </div>

      <label class="field">
        <input v-model="利用者ID" type="text" autocomplete="username" placeholder="利用者ID" />
      </label>

      <label class="field">
        <input
          v-model="パスワード"
          type="password"
          autocomplete="current-password"
          placeholder="パスワード"
        />
      </label>

      <p v-if="errorMessage" class="error-box">{{ errorMessage }}</p>

      <button class="login-button" type="submit" :disabled="loading">
        {{ loading ? 'ログイン中...' : 'ログイン' }}
      </button>
    </form>
  </section>
</template>

<style scoped>
.login-shell {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
  background: transparent;
}

.login-card {
  width: min(100%, 212px);
  padding: 0 4px 4px;
  border-radius: 0;
  border: 1px solid rgba(118, 97, 204, 0.82);
  background: rgba(2, 2, 4, 0.46);
  box-shadow:
    0 10px 26px rgba(0, 0, 0, 0.24),
    0 0 0 1px rgba(130, 105, 220, 0.18),
    inset 0 0 0 1px rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(12px);
}

.title-bar {
  height: 18px;
  margin: 0 -4px 4px;
  padding: 0 8px;
  border-radius: 0;
  border-bottom: 1px solid rgba(93, 68, 168, 0.95);
  background: linear-gradient(135deg, rgba(108, 78, 196, 0.94), rgba(143, 104, 221, 0.9));
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: move;
  -webkit-app-region: drag;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.16),
    inset 0 -1px 0 rgba(44, 24, 101, 0.28);
}

.title-dot {
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: rgba(246, 241, 255, 0.96);
  box-shadow: 0 0 8px rgba(255, 255, 255, 0.38);
  flex: 0 0 auto;
}

.title-text {
  margin: 0;
  font-size: 0.6rem;
  line-height: 1;
  color: rgba(248, 244, 255, 0.96);
  letter-spacing: 0.04em;
  user-select: none;
  text-shadow: 0 1px 4px rgba(47, 24, 99, 0.32);
}

.card-eyebrow {
  margin: 0;
  font-size: 0.6rem;
  letter-spacing: 0.04em;
  font-weight: 700;
  color: rgba(221, 209, 255, 0.94);
  text-align: center;
  text-shadow: 0 1px 6px rgba(0, 0, 0, 0.42);
}

.card-head {
  margin-bottom: 5px;
}

.field {
  display: block;
  margin-top: 5px;
}

.field input {
  width: 100%;
  padding: 7px 8px;
  border-radius: 0;
  border: 1px solid rgba(106, 85, 185, 0.68);
  background: rgba(54, 54, 62, 0.92);
  font: inherit;
  color: #f8f7ff;
  outline: none;
  font-size: 0.82rem;
  box-shadow:
    0 6px 14px rgba(0, 0, 0, 0.22),
    inset 0 1px 0 rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(6px);
  -webkit-app-region: no-drag;
}

.field input:focus {
  border-color: rgba(141, 110, 230, 0.95);
  box-shadow:
    0 0 0 2px rgba(141, 110, 230, 0.18),
    inset 0 1px 0 rgba(255, 255, 255, 0.16);
}

.field input::placeholder {
  color: #b6b2c6;
}

.error-box {
  margin: 6px 0 0;
  padding: 5px 6px;
  border-radius: 0;
  background: rgba(127, 29, 29, 0.18);
  border: 1px solid rgba(248, 113, 113, 0.18);
  color: #fca5a5;
  font-size: 0.74rem;
  line-height: 1.35;
  backdrop-filter: blur(8px);
  -webkit-app-region: no-drag;
}

.login-button {
  width: 72%;
  margin-top: 6px;
  margin-left: auto;
  margin-right: auto;
  display: block;
  padding: 7px 8px;
  border: 1px solid rgba(141, 110, 230, 0.92);
  border-radius: 0;
  background: linear-gradient(135deg, rgba(108, 78, 196, 0.94), rgba(143, 104, 221, 0.9));
  color: #f8f5ff;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
  font-size: 0.86rem;
  box-shadow:
    0 5px 12px rgba(99, 68, 186, 0.24),
    inset 0 1px 0 rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(10px);
  -webkit-app-region: no-drag;
}

.login-button:disabled {
  background: rgba(103, 114, 148, 0.5);
  border-color: rgba(103, 114, 148, 0.5);
  color: #d1d5db;
  cursor: not-allowed;
  box-shadow: none;
}

@media (max-width: 640px) {
  .login-shell {
    padding: 4px;
  }

  .login-card {
    width: min(100%, 206px);
  }
}
</style>
