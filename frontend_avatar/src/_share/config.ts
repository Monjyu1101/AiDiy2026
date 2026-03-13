import type { ModelSettings } from '@/types'

function resolveHttpBaseUrl(): string {
  if (import.meta.env.VITE_CORE_BASE_URL) {
    return import.meta.env.VITE_CORE_BASE_URL
  }

  if (import.meta.env.DEV) {
    return '/'
  }

  return 'http://127.0.0.1:8091'
}

function resolveWebSocketEndpoint(): string {
  if (import.meta.env.VITE_CORE_WS_URL) {
    return import.meta.env.VITE_CORE_WS_URL
  }

  if (typeof window !== 'undefined' && window.location.protocol.startsWith('http')) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${protocol}//${window.location.host}/core/ws/AIコア`
  }

  return 'ws://127.0.0.1:8091/core/ws/AIコア'
}

export const CORE_BASE_URL = resolveHttpBaseUrl()
export const AI_WS_ENDPOINT = resolveWebSocketEndpoint()
export const DEFAULT_VRM_MODEL_URL = '/vrm/AiDiy_Sample_M.vrm'
export const DEFAULT_VRMA_FILES = [
  '/vrma/VRMA_01.vrma',
  '/vrma/VRMA_02.vrma',
  '/vrma/VRMA_03.vrma',
  '/vrma/VRMA_04.vrma',
  '/vrma/VRMA_05.vrma',
  '/vrma/VRMA_06.vrma',
  '/vrma/VRMA_07.vrma',
]

export function defaultModelSettings(): ModelSettings {
  return {
    CHAT_AI_NAME: 'gemini_chat',
    LIVE_AI_NAME: 'gemini_live',
    CODE_AI1_NAME: 'claude_code',
    CODE_AI2_NAME: 'openai_code',
    CODE_AI3_NAME: 'gemini_code',
    CODE_AI4_NAME: 'freeai_code',
  }
}