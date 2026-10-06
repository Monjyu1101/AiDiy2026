import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import type { LiveCatalog } from '../../frontend_vscode/aidiy_live/src/model-catalog';
import { プロジェクトルート, 設定エラー } from './config';

export function ライブ候補読込(directory = join(プロジェクトルート, '_config')): LiveCatalog {
  const read = (name: string) => {
    try {
      const data = JSON.parse(readFileSync(join(directory, name), 'utf8').replace(/^\uFEFF/, ''));
      for (const key of ['models', 'voices']) {
        const values = data?.[key];
        if (!values || typeof values !== 'object' || Array.isArray(values)
            || Object.entries(values).some(([id, label]) => !id.trim() || typeof label !== 'string')) throw new Error();
      }
      return data as { models: Record<string, string>; voices: Record<string, string> };
    } catch { throw new 設定エラー(`${name} のモデル・音声候補を読み込めません。設定ファイルを確認してください。`); }
  };
  const gemini = read('AiDiy_live_gemini.json'), openai = read('AiDiy_live_openai.json');
  return {
    models: { freeai_live: gemini.models, gemini_live: gemini.models, openai_live: openai.models },
    voices: { freeai_live: gemini.voices, gemini_live: gemini.voices, openai_live: openai.voices },
  };
}
