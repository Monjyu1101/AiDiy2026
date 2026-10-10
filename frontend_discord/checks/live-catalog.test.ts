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
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { ライブ候補読込 } from '../src/live-catalog';

test('2つのJSONのモデル・声・表示順を読み、FreeAIもGeminiの一覧を使う', () => {
  const directory = mkdtempSync(join(tmpdir(), 'aidiy-live-catalog-'));
  try {
    const gemini = { models: { second: '2', first: '1' }, voices: { Kore: '声2', Zephyr: '声1' } };
    const openai = { models: { realtime: 'Realtime' }, voices: { cedar: 'Cedar', marin: 'Marin' } };
    writeFileSync(join(directory, 'AiDiy_live_gemini.json'), '\uFEFF' + JSON.stringify(gemini));
    writeFileSync(join(directory, 'AiDiy_live_openai.json'), JSON.stringify(openai));
    const catalog = ライブ候補読込(directory);
    assert.deepEqual(catalog.models.freeai_live, gemini.models);
    assert.deepEqual(Object.keys(catalog.models.gemini_live), ['second', 'first']);
    assert.deepEqual(catalog.voices.gemini_live, gemini.voices);
    assert.deepEqual(catalog.voices.freeai_live, gemini.voices);
    assert.deepEqual(catalog.models.openai_live, openai.models);
    assert.deepEqual(Object.keys(catalog.voices.openai_live), ['cedar', 'marin']);
    writeFileSync(join(directory, 'AiDiy_live_openai.json'), '{broken');
    assert.throws(() => ライブ候補読込(directory), /AiDiy_live_openai.json/);
    writeFileSync(join(directory, 'AiDiy_live_openai.json'), JSON.stringify({ models: {}, voices: [] }));
    assert.throws(() => ライブ候補読込(directory), /読み込めません/);
  } finally { rmSync(directory, { recursive: true, force: true }); }
});
