import { mkdirSync, readFileSync, renameSync, rmSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { dirname, join } from 'node:path';
import { randomUUID } from 'node:crypto';

export type CodeModel = { provider: string; model: string };
export type LiveModel = Record<string, string>;
export const LIVE_KEYS: Record<string, { model: string; voice: string }> = {
  freeai_live: { model: 'LIVE_FREEAI_MODEL', voice: 'LIVE_FREEAI_VOICE' },
  gemini_live: { model: 'LIVE_GEMINI_MODEL', voice: 'LIVE_GEMINI_VOICE' },
  openai_live: { model: 'LIVE_OPENAI_MODEL', voice: 'LIVE_OPENAI_VOICE' },
};

export function モデル保存先(kind: 'code' | 'live') {
  return join(homedir(), '.aidiy', `aidiy_${kind}_model.json`);
}
function コード設定(value: unknown): CodeModel {
  const data = value as CodeModel;
  if (!data || typeof data.provider !== 'string' || typeof data.model !== 'string'
      || data.provider.length > 200 || data.model.length > 300 || data.model === '__manual__')
    throw new Error('モデル指定が不正です。');
  return { provider: data.provider.trim(), model: data.provider.trim() ? data.model.trim() : '' };
}
function ライブ設定(value: unknown): LiveModel {
  const data = value as LiveModel, key = data && LIVE_KEYS[data.LIVE_AI_NAME];
  if (!key || Object.keys(data).some(name => !['LIVE_AI_NAME', key.model, key.voice].includes(name))
      || typeof data[key.model] !== 'string' || !data[key.model].trim() || data[key.model].length > 300
      || (data[key.voice] !== undefined && (typeof data[key.voice] !== 'string' || data[key.voice].length > 100)))
    throw new Error('ライブモデル指定が不正です。');
  return { LIVE_AI_NAME: data.LIVE_AI_NAME, [key.model]: data[key.model].trim(),
    ...(data[key.voice]?.trim() ? { [key.voice]: data[key.voice].trim() } : {}) };
}
function 読込<T>(file: string, validate: (value: unknown) => T): T | undefined {
  try { return validate(JSON.parse(readFileSync(file, 'utf8'))); }
  catch { return undefined; } // 未保存・破損時は既定設定を使う。
}
function 保存<T>(file: string, value: unknown, validate: (value: unknown) => T) {
  const settings = validate(value);
  mkdirSync(dirname(file), { recursive: true, mode: 0o700 });
  const temporary = `${file}.${randomUUID()}.tmp`;
  try {
    writeFileSync(temporary, JSON.stringify(settings, null, 2) + '\n', { encoding: 'utf8', mode: 0o600, flag: 'wx' });
    renameSync(temporary, file);
  } finally { rmSync(temporary, { force: true }); }
  return settings;
}
export const コードモデル読込 = (file = モデル保存先('code')) => 読込(file, コード設定);
export const コードモデル保存 = (value: unknown, file = モデル保存先('code')) => 保存(file, value, コード設定);
export const ライブモデル読込 = (file = モデル保存先('live')) => 読込(file, ライブ設定);
export const ライブモデル保存 = (value: unknown, file = モデル保存先('live')) => 保存(file, value, ライブ設定);
