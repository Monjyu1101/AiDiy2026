<script setup lang="ts">
import アバター from '@/components/アバター.vue'
import WindowShell from '@/components/WindowShell.vue'

type PanelKey = 'chat' | 'file' | 'image' | 'code1' | 'code2' | 'code3' | 'code4'

defineProps<{
  sessionId: string;
  userLabel: string;
  liveModel: string;
  connectionReady: boolean;
  transportState: string;
  inputConnected: boolean;
  chatConnected: boolean;
  audioConnected: boolean;
  micEnabled: boolean;
  speakerEnabled: boolean;
  micLevel: number;
  speakerLevel: number;
  panelVisibility: Record<PanelKey, boolean>;
  coreBusy: boolean;
  coreError: string;
}>()

const emit = defineEmits<{
  toggleMicrophone: [];
  toggleSpeaker: [];
  togglePanel: [panel: PanelKey];
  reconnect: [];
  logout: [];
}>()
</script>

<template>
  <component :is="WindowShell" title="AiDiy Desktop Avatar" theme="purple" :closable="false">
    <template #title-right>
      <span class="mini-pill" :class="{ ok: connectionReady, warn: !connectionReady }">
        {{ transportState }}
      </span>
      <span class="mini-pill" :class="{ ok: inputConnected }">input</span>
      <span class="mini-pill" :class="{ ok: chatConnected }">chat</span>
      <span class="mini-pill" :class="{ ok: audioConnected }">audio</span>
    </template>

    <div class="core-panel-body">
      <component
        :is="アバター"
        :session-id="sessionId"
        :user-name="userLabel"
        :live-model="liveModel"
        :input-connected="inputConnected"
        :audio-connected="audioConnected"
        :mic-enabled="micEnabled"
        :speaker-enabled="speakerEnabled"
        :mic-level="micLevel"
        :speaker-level="speakerLevel"
        :ui-visible="true"
      />

      <aside class="panel-icons">
        <button
          class="tool-button microphone-button"
          :class="{ active: micEnabled }"
          type="button"
          title="マイク"
          @click="emit('toggleMicrophone')"
        >
          <img src="/icons/microphone.png" alt="マイク" />
        </button>
        <button
          class="tool-button speaker-button"
          :class="{ inactive: !speakerEnabled, active: speakerEnabled }"
          type="button"
          title="スピーカー"
          @click="emit('toggleSpeaker')"
        >
          <img src="/icons/speaker.png" alt="スピーカー" />
        </button>
        <button
          class="tool-button file-button"
          :class="{ inactive: !panelVisibility.file, active: panelVisibility.file }"
          type="button"
          title="AIファイル"
          @click="emit('togglePanel', 'file')"
        >
          <img src="/icons/folder.png" alt="ファイル" />
        </button>
        <button
          class="tool-button chat-button"
          :class="{ inactive: !panelVisibility.chat, active: panelVisibility.chat }"
          type="button"
          title="AIチャット"
          @click="emit('togglePanel', 'chat')"
        >
          0
        </button>
        <button
          class="tool-button agent-button"
          :class="{ inactive: !panelVisibility.code1, active: panelVisibility.code1 }"
          type="button"
          title="AIコード1"
          @click="emit('togglePanel', 'code1')"
        >
          1
        </button>
        <button
          class="tool-button camera-button"
          :class="{ inactive: !panelVisibility.image, active: panelVisibility.image }"
          type="button"
          title="AIイメージ"
          @click="emit('togglePanel', 'image')"
        >
          <img src="/icons/camera.png" alt="イメージ" />
        </button>
        <button
          class="tool-button agent-button"
          :class="{ inactive: !panelVisibility.code2, active: panelVisibility.code2 }"
          type="button"
          title="AIコード2"
          @click="emit('togglePanel', 'code2')"
        >
          2
        </button>
        <button
          class="tool-button agent-button"
          :class="{ inactive: !panelVisibility.code3, active: panelVisibility.code3 }"
          type="button"
          title="AIコード3"
          @click="emit('togglePanel', 'code3')"
        >
          3
        </button>
        <button
          class="tool-button agent-button"
          :class="{ inactive: !panelVisibility.code4, active: panelVisibility.code4 }"
          type="button"
          title="AIコード4"
          @click="emit('togglePanel', 'code4')"
        >
          4
        </button>
        <button class="tool-button sync-button" type="button" title="再接続" @click="emit('reconnect')">S</button>
        <button class="tool-button exit-button" type="button" title="ログアウト" @click="emit('logout')">
          EXIT
        </button>
      </aside>

      <div v-if="coreBusy || coreError" class="panel-toast" :class="{ error: coreError }">
        {{ coreError || 'AIコアへ接続しています...' }}
      </div>
    </div>
  </component>
</template>
