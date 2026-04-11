// -*- coding: utf-8 -*-

// -------------------------------------------------------------------------
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
// -------------------------------------------------------------------------

export interface AuthUser {
  利用者ID: string;
  利用者名?: string;
  権限ID?: string;
  [key: string]: unknown;
}

export type MessageKind =
  | 'system'
  | 'user'
  | 'assistant'
  | 'recognition-user'
  | 'recognition-assistant'
  | 'input-request'
  | 'output-request'
  | 'input-file'
  | 'output-file'
  | 'stream'

export interface ChatMessage {
  id: string;
  kind: MessageKind;
  text: string;
  timestamp: string;
  fileName?: string | null;
  thumbnail?: string | null;
  isStream?: boolean;
  isCollapsed?: boolean;
}

export interface ModelSettings {
  CHAT_AI_NAME: string;
  LIVE_AI_NAME: string;
  CODE_AI1_NAME: string;
  CODE_AI2_NAME: string;
  CODE_AI3_NAME: string;
  CODE_AI4_NAME: string;
}
