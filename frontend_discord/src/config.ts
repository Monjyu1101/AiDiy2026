import { readFileSync, statSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

export const プロジェクトルート = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
export const 設定ファイル = resolve(プロジェクトルート, '_config/AiDiy_key.json');

export interface Discord設定 {
  token: string; guildId: string; userId: string; textChannelId: string; voiceChannelId: string;
  prefix: string; coreUrl: string; folder: string; cli: string; python: string;
  provider: string; model: string; maxTurns: number; timeoutMs: number; liveModels: Record<string, string>;
}
export class 設定エラー extends Error {}

export function 設定解析(data: Record<string, unknown>, root = プロジェクトルート): Discord設定 {
  const text = (key: string, fallback = '') => {
    const value = data[key] ?? fallback;
    if (typeof value !== 'string') throw new 設定エラー(`${key} は文字列で指定してください。`);
    return value.trim();
  };
  const integer = (key: string, fallback: number, min: number, max: number) => {
    const raw = data[key] ?? fallback;
    const value = typeof raw === 'number' || typeof raw === 'string' && /^\d+$/.test(raw) ? Number(raw) : NaN;
    if (!Number.isInteger(value) || value < min || value > max) throw new 設定エラー(`${key} は ${min}～${max} の整数で指定してください。`);
    return value;
  };
  const token = text('DISCORD_BOT_TOKEN');
  if (token.length <= 1 || token.startsWith('<') || /\s/.test(token)) {
    throw new 設定エラー('_config/AiDiy_key.json の DISCORD_BOT_TOKEN に Bot トークンを設定してください（空欄・1文字・< で始まる仮設定は使用できません）。');
  }
  const id = (key: string) => {
    const value = text(key);
    if (!/^\d{17,20}$/.test(value)) throw new 設定エラー(`${key} に1つの Discord ID を文字列で設定してください。`);
    return value;
  };
  const guildId = id('DISCORD_GUILD_ID');
  const userId = id('DISCORD_ALLOWED_USER_ID');
  const textChannelId = id('DISCORD_TEXT_CHANNEL_ID');
  const voiceChannelId = id('DISCORD_VOICE_CHANNEL_ID');
  const port = integer('PORT_CORE', 8091, 1, 65535);
  const url = new URL(`ws://127.0.0.1:${port}`);
  url.pathname = '/core/ws/AIコア';
  const folder = resolve(root, 'backend_server', text('CODE_BASE_PATH') || '../');
  try { if (!statSync(folder).isDirectory()) throw new Error(); }
  catch { throw new 設定エラー('CODE_BASE_PATH の作業フォルダが存在しません。'); }
  const liveModels: Record<string, string> = {};
  for (const key of ['LIVE_AI_NAME', 'LIVE_GEMINI_MODEL', 'LIVE_GEMINI_VOICE', 'LIVE_FREEAI_MODEL', 'LIVE_FREEAI_VOICE', 'LIVE_OPENAI_MODEL', 'LIVE_OPENAI_VOICE']) {
    const value = text(key);
    if (value) liveModels[key] = value;
  }
  const hermesModel = text('CODE_AIDIY_HERMES_MODEL') || 'openai_oauth/gpt-6.1-sol';
  // OAuth 指定時は provider も明示し、認証切れを別 provider への退避で隠さない。
  const oauthModel = /^(openai_oauth|xai-oauth)\/(.+)$/.exec(hermesModel);
  return {
    token, guildId, userId, textChannelId, voiceChannelId, prefix: '!aidiy', coreUrl: url.href, folder, liveModels,
    cli: 'aidiy_hermes', python: '',
    provider: oauthModel?.[1] || '', model: oauthModel?.[2] || hermesModel,
    maxTurns: integer('CODE_MAX_TURNS', 999, 1, Number.MAX_SAFE_INTEGER), timeoutMs: 900_000,
  };
}

export function 設定読込(path = 設定ファイル): Discord設定 {
  let data: unknown;
  try { data = JSON.parse(readFileSync(path, 'utf8').replace(/^\uFEFF/, '')); }
  catch { throw new 設定エラー('_config/AiDiy_key.json を UTF-8 の JSON オブジェクトとして読み込めません。'); }
  if (!data || Array.isArray(data) || typeof data !== 'object') throw new 設定エラー('AiDiy_key.json のルートは JSON オブジェクトにしてください。');
  return 設定解析(data as Record<string, unknown>);
}
