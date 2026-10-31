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

// 履歴は新しい順、スレッドは古い順。ページ間の失敗も外部通信なしで再現する。
function 巡回準備(pageSize = 100, cursorPaging = true) {
  const history: 投稿[] = [], replies = new Map<string, 投稿[]>();
  const posts: Record<string, string>[] = [], updates: Record<string, string>[] = [];
  const calls: { method: string; params: Record<string, string> }[] = [];
  const { code, runs } = 偽Code();
  let failPage = '', placeholder: Promise<Record<string, unknown>> | undefined;
  const api: SlackAPI = async (method, params) => {
    calls.push({ method, params: { ...params } });
    if (method === 'conversations.history' || method === 'conversations.replies') {
      assert.equal(params.channel, channelId);
      if (failPage === method && params.cursor) throw new SlackAPIエラー(method, 'network_error');
      const source = method === 'conversations.history' ? history : replies.get(params.ts) ?? [];
      const list = source.filter(m => ts比較(m.ts, params.oldest) > 0 && (!params.latest || ts比較(m.ts, params.latest) < 0));
      list.sort((a, b) => (method === 'conversations.history' ? -1 : 1) * ts比較(a.ts, b.ts));
      const offset = Number(params.cursor || 0), size = Math.min(Number(params.limit), pageSize);
      const more = offset + size < list.length;
      return { ok: true, messages: list.slice(offset, offset + size), has_more: more,
        response_metadata: { next_cursor: cursorPaging && more ? String(offset + size) : '' } };
    }
    if (method === 'chat.postMessage') {
      posts.push({ ...params });
      if (params.text === '考えています…' && placeholder) return placeholder;
      return { ok: true, ts: `900.${String(posts.length).padStart(6, '0')}` };
    }
    if (method === 'chat.update') { updates.push({ ...params }); return { ok: true }; }
    throw new Error(`Unexpected method: ${method}`);
  };
  const bot = new SlackBot(config(), api, code);
  const message = (ts: string, text: string): 投稿 => ({ type: 'message', user: userId, ts, text });
  return { bot, code, runs, history, replies, posts, updates, calls, message,
    fail: (method: string) => { failPage = method; },
    holdPlaceholder: (pending?: Promise<Record<string, unknown>>) => { placeholder = pending; } };
}
const 処理待ち = async () => { for (let i = 0; i < 100; i++) await Promise.resolve(); };

test('履歴が100件を超えても全ページを古い順に処理し、次の巡回で再実行しない', async () => {
  const f = 巡回準備();
  try {
    for (let i = 1; i <= 101; i++) f.history.push(f.message(`${i}.000001`, `要求${i}`));
    await f.bot.巡回(); await 処理待ち(); await f.bot.巡回(); await 処理待ち();
    assert.deepEqual(f.runs.map(item => item.text), Array.from({ length: 101 }, (_, i) => `要求${i + 1}`));
    const calls = f.calls.filter(call => call.method === 'conversations.history');
    assert.deepEqual(calls.map(call => [call.params.oldest, call.params.cursor]), [['0', undefined], ['0', '100'], ['101.000001', undefined]]);
  } finally { await f.bot.終了(); }
});

test('履歴の2ページ目が失敗したらカーソルも実行も進めず、復旧時に全件を一度ずつ処理する', async () => {
  const f = 巡回準備(2);
  try {
    for (let i = 1; i <= 3; i++) f.history.push(f.message(`${i}.000001`, `要求${i}`));
    f.fail('conversations.history');
    await assert.rejects(f.bot.巡回(), { error: 'network_error' }); await 処理待ち();
    assert.equal(f.runs.length, 0);
    f.fail(''); await f.bot.巡回(); await 処理待ち(); await f.bot.巡回(); await 処理待ち();
    assert.deepEqual(f.runs.map(item => item.text), ['要求1', '要求2', '要求3']);
    assert.equal(f.calls.filter(call => call.method === 'conversations.history')[2].params.oldest, '0');
  } finally { await f.bot.終了(); }
});

test('スレッド返信も全ページを取得し、途中失敗では既読位置を進めない', async () => {
  const f = 巡回準備(2);
  try {
    f.history.push(f.message('1.000001', '開始')); await f.bot.巡回(); await 処理待ち();
    f.replies.set('1.000001', [2, 3, 4].map(i => f.message(`${i}.000001`, '!aidiy status')));
    f.fail('conversations.replies');
    await assert.rejects(f.bot.巡回(), { error: 'network_error' }); await 処理待ち();
    assert.equal(f.posts.filter(post => post.text.startsWith('Code:')).length, 0);
    f.fail(''); await f.bot.巡回(); await 処理待ち(); await f.bot.巡回(); await 処理待ち();
    assert.equal(f.posts.filter(post => post.text.startsWith('Code:')).length, 3);
    const calls = f.calls.filter(call => call.method === 'conversations.replies');
    assert.equal(calls.at(-1)?.params.oldest, '4.000001');
  } finally { await f.bot.終了(); }
});

test('has_more だけの応答も時刻でページを進め、履歴とスレッドの欠落を防ぐ', async () => {
  const f = 巡回準備(2, false);
  try {
    for (let i = 1; i <= 3; i++) f.history.push(f.message(`${i}.000001`, `要求${i}`));
    await f.bot.巡回(); await 処理待ち();
    assert.deepEqual(f.runs.map(item => item.text), ['要求1', '要求2', '要求3']);
    f.replies.set('3.000001', [4, 5, 6].map(i => f.message(`${i}.000001`, '!aidiy status')));
    // 直近スレッドは履歴取得と同時に一度巡回済み。round-robinで戻るまで待つ。
    for (let i = 0; i < 3; i++) await f.bot.巡回();
    await 処理待ち();
    assert.equal(f.posts.filter(post => post.text.startsWith('Code:')).length, 3);
    assert.ok(f.calls.some(call => call.method === 'conversations.history' && call.params.latest === '2.000001'));
    assert.ok(f.calls.some(call => call.method === 'conversations.replies' && call.params.oldest === '5.000001'));
  } finally { await f.bot.終了(); }
});

test('循環カーソルや進めないhas_moreは拒否し、履歴位置を失わない', async () => {
  for (const mode of ['cursor', 'time'] as const) {
    const { code, runs } = 偽Code(); let calls = 0;
    const bot = new SlackBot(config(), async (_method, params) => {
      calls++; assert.equal(params.oldest, '0');
      return { messages: mode === 'cursor' ? [{ type: 'message', user: userId, text: '要求', ts: '1.000001' }] : [],
        has_more: true, response_metadata: { next_cursor: mode === 'cursor' ? 'same' : '' } };
    }, code);
    try {
      await assert.rejects(bot.巡回(), { error: 'invalid_response' }); await 処理待ち();
      assert.equal(runs.length, 0); assert.equal(calls, mode === 'cursor' ? 2 : 1);
    } finally { await bot.終了(); }
  }
});

test('同じスレッドの要求とstopを同じ巡回で受けても、未開始の要求を実行しない', async () => {
  const f = 巡回準備();
  try {
    f.history.push(f.message('1.000001', '開始')); await f.bot.巡回(); await 処理待ち();
    f.replies.set('1.000001', [f.message('2.000001', '取り消す要求'), f.message('2.000002', '!aidiy stop')]);
    await f.bot.巡回(); await 処理待ち();
    assert.deepEqual(f.runs.map(item => item.text), ['開始']);
    assert.ok(f.posts.some(post => post.text.startsWith('停止を要求しました')));
  } finally { await f.bot.終了(); }
});

test('考えています投稿の待機中のstopは後続のCLI起動を防ぎ、次の要求は実行できる', async () => {
  const f = 巡回準備(); let release!: (value: Record<string, unknown>) => void;
  try {
    f.holdPlaceholder(new Promise(resolve => { release = resolve; }));
    f.history.push(f.message('1.000001', '取り消す要求')); await f.bot.巡回(); await 処理待ち();
    assert.equal(f.runs.length, 0);
    f.replies.set('1.000001', [f.message('2.000001', '!aidiy stop')]);
    await f.bot.巡回(); await 処理待ち();
    f.holdPlaceholder(); release({ ok: true, ts: '10.000001' }); await 処理待ち();
    assert.equal(f.runs.length, 0);
    assert.ok(f.updates.some(update => update.ts === '10.000001' && update.text.includes('停止')));
    f.replies.get('1.000001')!.push(f.message('3.000001', '次の要求'));
    await f.bot.巡回(); await 処理待ち();
    assert.deepEqual(f.runs.map(item => item.text), ['次の要求']);
  } finally { release?.({ ok: true }); await f.bot.終了(); }
});

test('stopは同じスレッドの実行と待ち行列だけを停止し、別スレッドには影響しない', async () => {
  const f = 巡回準備(); const running = new Map<string, (text: string) => void>(), stopped: string[] = [];
  const mutable = f.code as unknown as { 実行中(key: string): boolean; 停止(key: string): void; 実行(key: string, text: string): Promise<string> };
  mutable.実行中 = key => running.has(key);
  mutable.停止 = key => { stopped.push(key); running.get(key)?.('停止しました'); running.delete(key); };
  mutable.実行 = (key, text) => { f.runs.push({ key, text }); return new Promise(resolve => { running.set(key, resolve); }); };
  try {
    f.history.push(f.message('1.000001', '実行中'), f.message('2.000001', '別スレッド'));
    await f.bot.巡回(); await 処理待ち();
    f.replies.set('1.000001', [f.message('3.000001', '待機中'), f.message('3.000002', '!aidiy stop')]);
    await f.bot.巡回(); await 処理待ち();
    assert.deepEqual(f.runs.map(item => item.text), ['実行中', '別スレッド']);
    assert.deepEqual(stopped, [`${teamId}:${channelId}:1.000001`]);
    assert.equal(running.has(`${teamId}:${channelId}:2.000001`), true);
  } finally { for (const done of running.values()) done('終了'); await 処理待ち(); await f.bot.終了(); }
});

test('stop直後の新要求は、取り消した10件の待ち行列とは別に受け付ける', async () => {
  const f = 巡回準備();
  try {
    f.history.push(f.message('1.000001', '開始')); await f.bot.巡回(); await 処理待ち();
    f.replies.set('1.000001', [...Array.from({ length: 10 }, (_, i) => f.message(`2.${String(i + 1).padStart(6, '0')}`, `取消${i}`)),
      f.message('3.000001', '!aidiy stop'), f.message('3.000002', '次の要求')]);
    await f.bot.巡回(); await 処理待ち();
    assert.deepEqual(f.runs.map(item => item.text), ['開始', '次の要求']);
    assert.ok(!f.posts.some(post => post.text.includes('返信待ちのメッセージが多い')));
  } finally { await f.bot.終了(); }
});

test('ページ境界で同じ投稿が重なっても一度だけ実行する', async () => {
  const { code, runs } = 偽Code(); let first = true;
  const message = (ts: string) => ({ type: 'message', user: userId, text: ts, ts });
  const bot = new SlackBot(config(), async (method, params) => {
    if (method === 'conversations.history') {
      if (params.cursor) return { messages: [message('2.000001'), message('1.000001')] };
      if (first) { first = false; return { messages: [message('3.000001'), message('2.000001')], response_metadata: { next_cursor: 'next' } }; }
      return { messages: [] };
    }
    if (method === 'conversations.replies') return { messages: [] };
    return { ok: true };
  }, code);
  try {
    await bot.巡回(); await 処理待ち(); await bot.巡回(); await 処理待ち();
    assert.deepEqual(runs.map(item => item.text), ['1.000001', '2.000001', '3.000001']);
  } finally { await bot.終了(); }
});

test('追加ページ取得中に切断したら、遅れて届いた投稿を実行しない', async () => {
  const { code, runs } = 偽Code(); let release!: (value: Record<string, unknown>) => void, calls = 0;
  const pending = new Promise<Record<string, unknown>>(resolve => { release = resolve; });
  const bot = new SlackBot(config(), async (_method, params) => {
    calls++;
    if (params.cursor) return pending;
    return { messages: [{ type: 'message', user: userId, text: '未実行', ts: '2.000001' }], response_metadata: { next_cursor: 'next' } };
  }, code);
  try {
    const poll = bot.巡回(); await 処理待ち(); assert.equal(calls, 2);
    await bot.終了(); release({ messages: [{ type: 'message', user: userId, text: '遅延', ts: '1.000001' }] });
    await poll; await 処理待ち(); assert.equal(runs.length, 0); assert.equal(calls, 2);
  } finally { release?.({ messages: [] }); await bot.終了(); }
});

test('stopを繰り返しても新要求の順序と会話キーを保つ', async () => {
  const f = 巡回準備();
  try {
    f.history.push(f.message('1.000001', '開始')); await f.bot.巡回(); await 処理待ち();
    f.replies.set('1.000001', [f.message('2.000001', '取消'), f.message('2.000002', '!aidiy stop'),
      f.message('2.000003', '!aidiy stop'), f.message('2.000004', '再開1'), f.message('2.000005', '再開2')]);
    await f.bot.巡回(); await 処理待ち();
    assert.deepEqual(f.runs.map(item => item.text), ['開始', '再開1', '再開2']);
    assert.equal(new Set(f.runs.map(item => item.key)).size, 1);
    assert.ok(f.posts.some(post => post.text === '実行中のコード要求はありません。'));
  } finally { await f.bot.終了(); }
});
