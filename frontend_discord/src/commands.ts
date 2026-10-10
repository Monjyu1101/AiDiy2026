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

import type { Discord設定 } from './config';

export type コマンド = { name: 'chat' | 'live' | 'leave' | 'stop' | 'new' | 'status' | 'help'; text: string };
export const メンション禁止 = { parse: [] as ('users' | 'roles' | 'everyone')[], repliedUser: false };

export function コマンド解析(content: string, prefix: string, botId: string): コマンド | undefined {
  const triggers = [prefix, `<@${botId}>`, `<@!${botId}>`];
  const trigger = triggers.find(value => content === value || content.startsWith(`${value} `) || content.startsWith(`${value}\n`));
  // 設定した利用者の通常投稿を、そのままチャットとして受け付ける。
  if (!trigger) return content.trim() ? { name: 'chat', text: content.trim() } : undefined;
  const body = content.slice(trigger.length).trim();
  if (!body) return { name: 'help', text: '' };
  const match = /^(\S+)(?:\s+([\s\S]*))?$/.exec(body)!;
  const name = match[1].toLowerCase();
  if (['chat', 'live', 'leave', 'stop', 'new', 'status', 'help'].includes(name)) return { name: name as コマンド['name'], text: (match[2] || '').trim() };
  return { name: 'chat', text: body };
}

export function 利用許可(config: Discord設定, guildId: string | null, channelId: string, userId: string, bot = false): boolean {
  return !bot && guildId === config.guildId && channelId === config.textChannelId && userId === config.userId;
}

export function 会話キー(guildId: string, channelId: string, userId: string): string {
  return `${guildId}:${channelId}:${userId}`;
}

// Discord の2000文字制限をUTF-16単位で満たし、サロゲートペアを分断しない。
export function 本文分割(text: string, limit = 1900): string[] {
  if (limit < 2) throw new Error('分割上限は2文字以上にしてください。');
  const parts: string[] = [];
  let current = '';
  for (const char of text) {
    if (current.length + char.length > limit) { parts.push(current); current = ''; }
    current += char;
  }
  if (current) parts.push(current);
  return parts;
}
