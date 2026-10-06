export const LIVE_KEYS: Record<string, { model: string; voice: string }> = {
  freeai_live: { model: 'LIVE_FREEAI_MODEL', voice: 'LIVE_FREEAI_VOICE' },
  gemini_live: { model: 'LIVE_GEMINI_MODEL', voice: 'LIVE_GEMINI_VOICE' },
  openai_live: { model: 'LIVE_OPENAI_MODEL', voice: 'LIVE_OPENAI_VOICE' },
};
export type LiveCatalog = {
  models: Record<string, Record<string, string>>;
  voices: Record<string, Record<string, string>>;
};

// 候補は AiDiy_live_*.json 由来の一覧だけ。保存済み設定で候補を増やさない。
export function ライブ選択エラー(settings: Record<string, string>, catalog: LiveCatalog): string {
  const provider = settings.LIVE_AI_NAME, keys = LIVE_KEYS[provider];
  if (!keys || !Object.hasOwn(catalog.models, provider)) return 'ライブAIを候補から選び直してください。';
  if (!Object.hasOwn(catalog.models[provider] || {}, settings[keys.model] || ''))
    return 'ライブモデルが候補にありません。モデルを選び直してください。';
  if (!Object.hasOwn(catalog.voices[provider] || {}, settings[keys.voice] || ''))
    return '音声が候補にありません。声を選び直してください。';
  return '';
}
