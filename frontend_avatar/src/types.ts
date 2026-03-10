export interface AuthUser {
  利用者ID: string;
  利用者名?: string;
  権限ID?: string;
  [key: string]: unknown;
}

export interface ChatMessage {
  id: string;
  kind: 'system' | 'user' | 'assistant' | 'recognition-user' | 'recognition-assistant';
  text: string;
  timestamp: string;
}

export interface ModelSettings {
  CHAT_AI_NAME: string;
  LIVE_AI_NAME: string;
  CODE_AI1_NAME: string;
  CODE_AI2_NAME: string;
  CODE_AI3_NAME: string;
  CODE_AI4_NAME: string;
}
