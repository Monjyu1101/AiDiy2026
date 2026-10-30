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

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { SlackBot } from '../src/接続/Bot接続';
import { SlackAPIエラー, type SlackAPI } from '../src/接続/ネットワーク接続';
import type { Code接続 } from '../src/コード/コード会話';
import { ts比較, 本文分割 } from '../src/接続/コマンド処理';
import { botUserId, channelId, config, teamId, userId, waitFor } from './helpers';

type 投稿 = Record<string, unknown> & { ts: string };

function 偽Slack(team = teamId) {
  const history: 投稿[] = [{ type: 'message', subtype: 'channel_join', user: userId, text: '参加', ts: '100.000001' }];
  const replies = new Map<string, 投稿[]>();
  const posts: Record<string, string>[] = [];
  const updates: Record<string, string>[] = [];
  const calls: string[] = [];
  let seq = 0;
  const api: SlackAPI = async (method, params) => {
    calls.push(method);
    switch (method) {
      case 'auth.test': return { ok: true, team_id: team, user_id: botUserId };
      case 'conversations.history': {
        assert.equal(params.channel, channelId);
        const newer = history.filter(m => !params.oldest || ts比較(m.ts, params.oldest) > 0);
        return { ok: true, messages: [...newer].reverse().slice(0, Number(params.limit)) };
      }
      case 'conversations.replies': {
        const list = replies.get(params.ts) ?? [];
        return { ok: true, messages: [{ type: 'message', user: userId, text: 'root', ts: params.ts }, ...list.filter(m => ts比較(m.ts, params.oldest) > 0)] };
      }
      case 'chat.postMessage': {
        const ts = `900.${String(++seq).padStart(6, '0')}`;
        posts.push({ ...params, ts });
        // Bot の投稿もスレッド返信として取得結果に現れる。
        replies.set(params.thread_ts, [...replies.get(params.thread_ts) ?? [], { type: 'message', bot_id: 'B1', user: botUserId, text: params.text, ts }]);
        return { ok: true, ts };
      }
      case 'chat.update': updates.push(params); return { ok: true };
    }
    throw new SlackAPIエラー(method, 'unknown_method');
  };
  const 投稿追加 = (message: Partial<投稿> & { ts: string }) => history.push({ type: 'message', user: userId, ...message });
  const 返信追加 = (root: string, message: Partial<投稿> & { ts: string }) => replies.set(root, [...replies.get(root) ?? [], { type: 'message', user: userId, ...message } as 投稿]);
  return { api, posts, updates, calls, 投稿追加, 返信追加 };
}

function 偽Code() {
  const runs: { key: string; text: string }[] = [];
  const code = {
    実行中: () => false, 停止: () => {}, リセット: () => {}, 終了: async () => {},
    実行: async (key: string, text: string) => { runs.push({ key, text }); return `回答:${text}`; },
  } as unknown as Code接続;
  return { code, runs };
}

test('起動前の投稿は無視し、許可ユーザーの新規投稿へスレッドで返信する', async () => {
  const slack = 偽Slack(); const { code, runs } = 偽Code();
  const bot = new SlackBot(config(), slack.api, code, { interval: 60_000 });
  try {
    await bot.起動();
    slack.投稿追加({ text: 'こんにちは &lt;b&gt;', ts: '101.000001' });
    slack.投稿追加({ user: 'U0OTHERUSR1', text: '他人', ts: '101.000002' });
    slack.投稿追加({ bot_id: 'B9', text: 'bot', ts: '101.000003' });
    slack.投稿追加({ subtype: 'message_changed', text: '編集', ts: '101.000004' });
    await bot.巡回();
    await waitFor(() => slack.updates.length === 1);
    assert.deepEqual(runs, [{ key: `${teamId}:${channelId}:101.000001`, text: 'こんにちは <b>' }]);
    assert.equal(slack.posts[0].thread_ts, '101.000001'); assert.equal(slack.posts[0].text, '考えています…');
    assert.equal(slack.updates[0].text, '回答:こんにちは &lt;b&gt;');
    // 同じ範囲を再取得しても二重に実行しない。
    await bot.巡回(); await bot.巡回();
    assert.equal(runs.length, 1);
  } finally { await bot.終了(); }
});

test('スレッド内の続きは同じ会話キーで処理し、Bot 自身の投稿は無視する', async () => {
  const slack = 偽Slack(); const { code, runs } = 偽Code();
  const bot = new SlackBot(config(), slack.api, code, { interval: 60_000 });
  try {
    await bot.起動();
    slack.投稿追加({ text: '最初', ts: '102.000001' });
    await bot.巡回(); await waitFor(() => slack.updates.length === 1);
    slack.返信追加('102.000001', { text: '続き', ts: '103.000001', thread_ts: '102.000001' });
    await bot.巡回(); await waitFor(() => runs.length === 2);
    assert.equal(runs[1].key, runs[0].key); assert.equal(runs[1].text, '続き');
    await waitFor(() => slack.updates.length === 2);
    await bot.巡回(); await bot.巡回();
    assert.equal(runs.length, 2);
  } finally { await bot.終了(); }
});

test('コマンドに応答し、長い回答は分割して投稿する', async () => {
  const slack = 偽Slack(); const { code } = 偽Code();
  (code as unknown as { 実行: () => Promise<string> }).実行 = async () => 'あ'.repeat(8000);
  const bot = new SlackBot(config(), slack.api, code, { interval: 60_000 });
  try {
    await bot.起動();
    slack.投稿追加({ text: '!aidiy status', ts: '104.000001' });
    slack.投稿追加({ text: `<@${botUserId}> help`, ts: '104.000002' });
    slack.投稿追加({ text: '長文', ts: '104.000003' });
    await bot.巡回();
    await waitFor(() => slack.posts.length >= 5);
    assert.match(slack.posts[0].text, /Code: 待機中/);
    assert.match(slack.posts[1].text, /話しかけてください/);
    const chunks = 本文分割('あ'.repeat(8000));
    assert.equal(slack.updates[0].text, chunks[0]);
    assert.deepEqual(slack.posts.slice(3).map(p => p.text), chunks.slice(1));
  } finally { await bot.終了(); }
});

test('別ワークスペースの token は起動時に拒否する', async () => {
  const slack = 偽Slack('T0OTHERTEAM'); const { code } = 偽Code();
  const bot = new SlackBot(config(), slack.api, code, { interval: 60_000 });
  await assert.rejects(bot.起動(), /一致しません/);
  assert.ok(!slack.calls.includes('conversations.history'));
});
