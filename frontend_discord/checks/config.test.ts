import { test } from 'node:test';
import assert from 'node:assert/strict';
import { resolve } from 'node:path';
import { 設定解析, プロジェクトルート } from '../src/config';
import { defaults } from './helpers';

test('PORT_CORE、共通モデル、作業フォルダを読み込み、元設定は変更しない', () => {
  const data = { ...defaults, PORT_CORE: '18091', CODE_BASE_PATH: '../frontend_vscode', LIVE_AI_NAME: 'openai_live',
    CODE_AIDIY_HERMES_MODEL: 'openai_oauth/gpt-6.1-sol', CODE_MAX_TURNS: 999 };
  const before = JSON.stringify(data);
  const result = 設定解析(data);
  assert.equal(new URL(result.coreUrl).port, '18091');
  assert.equal(decodeURI(new URL(result.coreUrl).pathname), '/core/ws/AIコア');
  assert.equal(result.folder, resolve(プロジェクトルート, 'frontend_vscode'));
  assert.equal(result.liveModels.LIVE_AI_NAME, 'openai_live');
  assert.equal(JSON.stringify(data), before);
  assert.equal(result.provider, 'openai_oauth');
  assert.equal(result.model, 'gpt-6.1-sol');
  assert.equal(result.maxTurns, 999);
});

test('未設定・不正ID・空の許可範囲・不正な共通設定を拒否し秘密値をエラーに出さない', () => {
  for (const change of [
    { DISCORD_BOT_TOKEN: '' }, { DISCORD_GUILD_ID: '' }, { DISCORD_ALLOWED_USER_ID: '' },
    { DISCORD_ALLOWED_USER_ID: 222222222222222222 }, { DISCORD_TEXT_CHANNEL_ID: [] },
    { DISCORD_VOICE_CHANNEL_ID: '' }, { DISCORD_ALLOWED_USER_ID: ['222222222222222222'] },
    { PORT_CORE: 'secret-value' }, { PORT_CORE: 65536 }, { PORT_CORE: true },
    { CODE_MAX_TURNS: 0 }, { CODE_MAX_TURNS: true },
    { CODE_BASE_PATH: './does-not-exist-secret-value' }, { CODE_AIDIY_HERMES_MODEL: 123 },
    { LIVE_AI_NAME: 123 },
  ]) {
    assert.throws(() => 設定解析({ ...defaults, ...change }), error => {
      assert.ok(error instanceof Error); assert.ok(!error.message.includes('secret-value')); return true;
    });
  }
  const parsed = 設定解析(defaults);
  assert.equal(parsed.userId, defaults.DISCORD_ALLOWED_USER_ID);
  assert.equal(parsed.textChannelId, defaults.DISCORD_TEXT_CHANNEL_ID);
  assert.equal(parsed.voiceChannelId, defaults.DISCORD_VOICE_CHANNEL_ID);
});

test('空欄・1文字・< で始まるトークンの仮設定を拒否する', () => {
  for (const token of ['', '   ', '<', '>', '(', ')', '[', ']', '{', '}', 'a', '<secret-placeholder>', '  <secret-placeholder  ']) {
    assert.throws(() => 設定解析({ ...defaults, DISCORD_BOT_TOKEN: token }), error => {
      assert.ok(error instanceof Error);
      assert.match(error.message, /DISCORD_BOT_TOKEN/);
      assert.doesNotMatch(error.message, /secret-placeholder/);
      return true;
    });
  }
});

test('全Liveベンダーで共通設定を使い、廃止したDiscord設定では上書きしない', () => {
  for (const [name, prefix] of [['freeai_live', 'FREEAI'], ['gemini_live', 'GEMINI'], ['openai_live', 'OPENAI']]) {
    const data = { ...defaults, LIVE_AI_NAME: name, [`LIVE_${prefix}_MODEL`]: 'common-model', [`LIVE_${prefix}_VOICE`]: 'common-voice',
      DISCORD_LIVE_AI_NAME: 'old-provider', DISCORD_LIVE_MODEL: 'old-model', DISCORD_LIVE_VOICE: 'old-voice',
      DISCORD_CORE_URL: 'http://old-host:9999', DISCORD_CODE_BASE_PATH: './old-folder',
      DISCORD_CODE_CLI: 'old-cli', DISCORD_CODE_PYTHON: 'old-python', DISCORD_COMMAND_PREFIX: '!old',
      DISCORD_CODE_PROVIDER: 'old-provider', DISCORD_CODE_MODEL: 'old-model', DISCORD_CODE_MAX_TURNS: 1,
      DISCORD_CODE_TIMEOUT_SECONDS: 1 };
    const before = JSON.stringify(data);
    const result = 設定解析(data);
    assert.equal(result.liveModels.LIVE_AI_NAME, name);
    assert.equal(result.liveModels[`LIVE_${prefix}_MODEL`], 'common-model');
    assert.equal(result.liveModels[`LIVE_${prefix}_VOICE`], 'common-voice');
    const baseline = 設定解析(defaults);
    for (const key of ['coreUrl', 'folder', 'cli', 'python', 'prefix', 'provider', 'model', 'maxTurns', 'timeoutMs'] as const) {
      assert.equal(result[key], baseline[key]);
    }
    assert.equal(JSON.stringify(data), before);
  }
  assert.equal(設定解析({ ...defaults, CODE_AIDIY_HERMES_MODEL: 'freeai/gemini-test' }).model, 'freeai/gemini-test');
  assert.equal(設定解析({ ...defaults, CODE_AIDIY_HERMES_MODEL: 'freeai/gemini-test' }).provider, '');
});
