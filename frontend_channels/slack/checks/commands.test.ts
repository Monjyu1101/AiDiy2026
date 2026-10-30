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
import { コマンド解析, 利用許可, 会話キー, ts比較, 本文復元, 本文エスケープ, 本文分割 } from '../src/接続/コマンド処理';
import { botUserId, channelId, config, teamId, userId } from './helpers';

test('通常の文章をチャットにし、明示したprefix / Botメンションの操作も解釈する', () => {
  assert.deepEqual(コマンド解析('!aidiy 日本語で説明\nしてください', '!aidiy', botUserId), { name: 'chat', text: '日本語で説明\nしてください' });
  assert.deepEqual(コマンド解析(`<@${botUserId}> stop`, '!aidiy', botUserId), { name: 'stop', text: '' });
  assert.deepEqual(コマンド解析('!aidiy-extra new', '!aidiy', botUserId), { name: 'chat', text: '!aidiy-extra new' });
  assert.deepEqual(コマンド解析('雑談です', '!aidiy', botUserId), { name: 'chat', text: '雑談です' });
  assert.deepEqual(コマンド解析('stop', '!aidiy', botUserId), { name: 'chat', text: 'stop' });
  assert.deepEqual(コマンド解析('!aidiy live こんにちは', '!aidiy', botUserId), { name: 'chat', text: 'live こんにちは' }, '音声会話のコマンドは持たない');
  assert.equal(コマンド解析(' \n ', '!aidiy', botUserId), undefined);
  assert.equal(コマンド解析('!aidiy', '!aidiy', botUserId)?.name, 'help');
});

test('他ワークスペース・非許可ユーザー・Bot / アプリ投稿・subtype 付き投稿を拒否する', () => {
  const value = config();
  const base = { type: 'message', user: userId, text: 'こんにちは', ts: '1.000001' };
  assert.equal(利用許可(value, base), true);
  assert.equal(利用許可(value, { ...base, team: teamId }), true);
  for (const patch of [{ team: 'T0OTHERTEAM' }, { user: 'U0OTHERUSER' }, { bot_id: 'B1' }, { app_id: 'A1' }, { subtype: 'message_changed' }, { subtype: 'channel_join' }, { type: 'reaction' }, { text: undefined }, { ts: 1 }]) {
    assert.equal(利用許可(value, { ...base, ...patch }), false, JSON.stringify(patch));
  }
  assert.notEqual(会話キー(teamId, channelId, '1.1'), 会話キー(teamId, channelId, '1.2'));
});

test('ts を桁落ちなく比較し、本文の記号を往復して一斉通知を起こさない', () => {
  assert.equal(ts比較('1700000000.000010', '1700000000.000009'), 1);
  assert.equal(ts比較('9007199254740993.000001', '9007199254740993.000001'), 0);
  assert.equal(ts比較('1.5', '1.400000'), 1);
  assert.equal(本文復元('a &lt;b&gt; &amp;amp;'), 'a <b> &amp;');
  assert.equal(本文エスケープ('<!channel> & <@U1>'), '&lt;!channel&gt; &amp; &lt;@U1&gt;');
  assert.equal(本文復元(本文エスケープ('<x> & y')), '<x> & y');
});

test('日本語と絵文字の長文を Slack の1投稿の目安内で欠落なく分割する', () => {
  const text = 'a'.repeat(3499) + '😀日本語\n'.repeat(2000);
  const parts = 本文分割(text);
  assert.equal(parts.join(''), text);
  assert.ok(parts.every(part => part.length <= 3500 && !/[\uD800-\uDBFF]$/.test(part)));
  assert.throws(() => 本文分割('abc', 1));
});
