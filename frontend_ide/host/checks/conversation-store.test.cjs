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

const { test } = require('node:test');
const assert = require('node:assert/strict');
const { mkdtempSync, mkdirSync, rmSync, readdirSync, writeFileSync, symlinkSync, existsSync } = require('node:fs');
const { tmpdir } = require('node:os');
const { join } = require('node:path');
const { 会話保存先, 会話一覧, 会話書込, 会話削除 } = require('../out/conversation-store.cjs');

const entry = (id, 更新日時) => ({ id, 更新日時, 初回依頼: `依頼${id}`, メッセージ: [{ 種別: 'user', 本文: 'こんにちは' }], provider: 'aidiy_hermes', model: 'auto' });

test('Code 会話履歴: プロジェクトの _AIDIY/aidiy_code/histories/ へ1会話1ファイルで保存・新しい順に読込・削除', t => {
  const project = mkdtempSync(join(tmpdir(), 'aidiy-code-history-'));
  t.after(() => rmSync(project, { recursive: true, force: true }));
  assert.equal(会話保存先(project), undefined, '保存前はフォルダを作らない');
  const folder = 会話保存先(project, true);
  assert.equal(folder, join(project, '_AIDIY', 'aidiy_code', 'histories'));
  会話書込(folder, entry('a-1', 100)); 会話書込(folder, entry('b-2', 200));
  writeFileSync(join(folder, 'broken.json'), '{');
  writeFileSync(join(folder, 'c-3.json'), JSON.stringify({ ...entry('other', 300) }));  // ファイル名とIDが違う記録は使わない
  assert.deepEqual(会話一覧(folder).map(item => item.id), ['b-2', 'a-1']);
  assert.deepEqual(readdirSync(folder).filter(name => name.endsWith('.tmp')), [], '一時ファイルを残さない');
  会話削除(folder, 'a-1'); 会話削除(folder, '../outside');
  assert.deepEqual(会話一覧(folder).map(item => item.id), ['b-2']);
  assert.throws(() => 会話書込(folder, entry('../bad', 1)), /会話ID/);
});

test('Code 会話履歴: リンクでプロジェクト外へ書き出さない', t => {
  const project = mkdtempSync(join(tmpdir(), 'aidiy-code-history-')), outside = mkdtempSync(join(tmpdir(), 'aidiy-code-outside-'));
  t.after(() => { rmSync(project, { recursive: true, force: true }); rmSync(outside, { recursive: true, force: true }); });
  symlinkSync(outside, join(project, '_AIDIY'), process.platform === 'win32' ? 'junction' : 'dir');
  assert.throws(() => 会話保存先(project, true), /プロジェクト外/);
  assert.equal(existsSync(join(outside, 'aidiy_code')), false);
});
