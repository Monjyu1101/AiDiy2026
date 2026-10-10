/*!
 * -*- coding: utf-8 -*-
 *
 * -------------------------------------------------------------------------
 * COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
 * Licensed under "AiDiy 公開利用ライセンス v1.1".
 * Commercial use requires prior written consent from all copyright holders.
 * See LICENSE for full terms. Thank you for keeping the rules.
 * https://github.com/monjyu1101/AiDiy2026
 * -------------------------------------------------------------------------
 */

import { 設定解析, プロジェクトルート } from '../src/config';

export const guildId = '111111111111111111';
export const userId = '222222222222222222';
export const textId = '333333333333333333';
export const voiceId = '444444444444444444';
export const botId = '555555555555555555';
export const defaults = {
  DISCORD_BOT_TOKEN: 'test-token', DISCORD_GUILD_ID: guildId,
  DISCORD_ALLOWED_USER_ID: userId, DISCORD_TEXT_CHANNEL_ID: textId, DISCORD_VOICE_CHANNEL_ID: voiceId,
};
export const config = () => 設定解析(defaults, プロジェクトルート);
export async function waitFor(condition: () => boolean, timeout = 3000) {
  const until = Date.now() + timeout;
  while (!condition()) {
    if (Date.now() >= until) throw new Error('検証の待機時間を超えました。');
    await new Promise(resolve => setTimeout(resolve, 10));
  }
}
