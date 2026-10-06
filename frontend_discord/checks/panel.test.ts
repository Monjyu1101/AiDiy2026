import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { Discordパネル } from '../src/panel';
import { type Discord設定 } from '../src/config';
import { config, waitFor } from './helpers';

const selection = { LIVE_AI_NAME: 'openai_live', LIVE_OPENAI_MODEL: 'test-live-model', LIVE_OPENAI_VOICE: 'marin' };
function fixture() {
  const directory = mkdtempSync(join(tmpdir(), 'aidiy-discord-panel-'));
  const file = join(directory, 'model.json');
  const configurations: Discord設定[] = [];
  let startCount = 0, stopCount = 0, ready = true;
  const create = (value: Discord設定) => {
    configurations.push(value);
    return { 起動: async () => { startCount++; }, 終了: async () => { stopCount++; }, client: { isReady: () => ready } };
  };
  const read = () => ({ ...config(), liveModels: { LIVE_AI_NAME: 'freeai_live', LIVE_FREEAI_MODEL: 'common-model', LIVE_FREEAI_VOICE: 'Zephyr' } });
  const catalog = { models: { freeai_live: { 'common-model': 'Common' }, openai_live: { 'test-live-model': 'Test' } },
    voices: { freeai_live: { Zephyr: 'Zephyr' }, openai_live: { marin: 'Marin', cedar: 'Cedar' } } };
  const panel = () => new Discordパネル(() => {}, read, create, file, () => {}, undefined, undefined, () => catalog);
  return { file, configurations, read, create, panel, catalog, counts: () => [startCount, stopCount], setReady: (value: boolean) => { ready = value; }, cleanup: () => rmSync(directory, { recursive: true, force: true }) };
}

test('候補の順序を維持し、保存済みでも削除されたモデル・声は追加表示・使用しない', async () => {
  const f = fixture();
  try {
    writeFileSync(f.file, JSON.stringify(selection));
    const panel = f.panel();
    delete (f.catalog.voices.openai_live as Record<string, string>).marin;
    const info = await panel.初期情報();
    assert.deepEqual(Object.keys(info.voices.openai_live), ['cedar']);
    assert.match(info.notice, /声を選び直して/);
    assert.throws(() => panel.選択保存(selection), /声を選び直して/);
    assert.deepEqual(JSON.parse(readFileSync(f.file, 'utf8')), selection);
    await panel.開始();
    assert.equal(panel.状態.phase, 'error'); assert.equal(f.configurations.length, 0);
    panel.選択保存({ ...selection, LIVE_OPENAI_VOICE: 'cedar' });
    await panel.開始();
    assert.equal(f.configurations[0].liveModels.LIVE_OPENAI_VOICE, 'cedar');
    await panel.停止();
    delete (f.catalog.models.openai_live as Record<string, string>)['test-live-model'];
    assert.deepEqual((await panel.初期情報()).models.openai_live, {});
    await panel.開始();
    assert.equal(panel.状態.phase, 'error'); assert.equal(f.configurations.length, 1);
    await panel.終了();
  } finally { f.cleanup(); }
});

test('起動時は未接続、初回は共通モデルを使い開始と停止だけで Bot を制御する', async () => {
  const f = fixture(), panel = f.panel();
  try {
    assert.equal(panel.状態.phase, 'idle'); assert.deepEqual(f.counts(), [0, 0]);
    await Promise.all([panel.開始(), panel.開始()]);
    assert.equal(panel.状態.phase, 'connected'); assert.deepEqual(f.counts(), [1, 0]);
    assert.equal(f.configurations[0].liveModels.LIVE_FREEAI_MODEL, 'common-model');
    assert.throws(() => panel.選択保存(selection));
    f.setReady(false); panel.接続確認(); assert.equal(panel.状態.phase, 'reconnecting');
    f.setReady(true); panel.接続確認(); assert.equal(panel.状態.phase, 'connected');
    await Promise.all([panel.停止(), panel.停止()]); assert.deepEqual(f.counts(), [1, 1]);
    await panel.開始(); assert.deepEqual(f.counts(), [2, 1]);
    await panel.終了(); await panel.開始(); assert.deepEqual(f.counts(), [2, 2]);
  } finally { await panel.終了(); f.cleanup(); }
});

test('手動選択は再起動後にも適用され、トークンや共通設定を保存ファイルに混ぜない', async () => {
  const f = fixture(), first = f.panel();
  try {
    first.選択保存(selection);
    first.コード選択保存({ provider: 'openai_oauth', model: 'test-code-model' });
    await first.終了();
    assert.deepEqual(JSON.parse(readFileSync(f.file, 'utf8')), selection);
    const next = f.panel();
    await next.開始();
    assert.equal(f.configurations[0].liveModels.LIVE_AI_NAME, 'openai_live');
    assert.equal(f.configurations[0].liveModels.LIVE_OPENAI_MODEL, 'test-live-model');
    assert.equal(f.configurations[0].provider, 'openai_oauth');
    assert.equal(f.configurations[0].model, 'test-code-model');
    assert.deepEqual(JSON.parse(readFileSync(join(f.file, '../aidiy_discord_code_model.json'), 'utf8')), { provider: 'openai_oauth', model: 'test-code-model' });
    assert.equal(f.read().liveModels.LIVE_AI_NAME, 'freeai_live');
    await next.終了();
    writeFileSync(f.file, '{broken');
    const fallback = f.panel(); await fallback.開始();
    assert.equal(f.configurations[1].liveModels.LIVE_AI_NAME, 'freeai_live'); await fallback.終了();
  } finally { f.cleanup(); }
});

test('login が先に完了してもサーバー情報の受信まで接続中を維持する', async () => {
  const f = fixture(); f.setReady(false);
  const panel = f.panel();
  try {
    const pending = panel.開始();
    await new Promise(resolve => setTimeout(resolve, 0));
    assert.equal(panel.状態.phase, 'connecting');
    f.setReady(true); await pending; assert.equal(panel.状態.phase, 'connected');
  } finally { await panel.終了(); f.cleanup(); }
});

test('接続途中の停止とパネル終了はログイン完了を待たず回収し、遅い結果で復帰しない', async () => {
  const f = fixture(); let finish!: () => void, stopped = 0;
  const panel = new Discordパネル(() => {}, f.read, () => ({
    起動: () => new Promise<void>(resolve => { finish = resolve; }),
    終了: async () => { stopped++; }, client: { isReady: () => true },
  }), f.file, () => {}, undefined, undefined, () => f.catalog);
  try {
    const connecting = panel.開始(); assert.equal(panel.状態.phase, 'connecting');
    await panel.停止(); await connecting; assert.equal(stopped, 1);
    finish(); assert.equal(panel.状態.phase, 'idle');
    const connectingAgain = panel.開始(); await panel.終了(); await connectingAgain;
    finish(); await panel.開始(); assert.equal(stopped, 2); assert.equal(panel.状態.phase, 'idle');
  } finally { await panel.終了(); f.cleanup(); }
});

test('接続失敗は秘密を表示せず回収し、再試行できる。タイムアウトも回収する', async () => {
  const f = fixture(); let attempt = 0, stopped = 0;
  const panel = new Discordパネル(() => {}, f.read, () => ({
    起動: async () => { if (++attempt === 1) throw new Error('secret-token'); },
    終了: async () => { stopped++; }, client: { isReady: () => true },
  }), f.file, () => {}, undefined, undefined, () => f.catalog);
  try {
    await panel.開始(); assert.equal(panel.状態.phase, 'error'); assert.equal(stopped, 1);
    assert.doesNotMatch(panel.状態.message, /secret-token/);
    await panel.開始(); assert.equal(panel.状態.phase, 'connected'); await panel.終了();
    const timeout = new Discordパネル(() => {}, f.read, () => ({
      起動: () => new Promise<void>(() => {}), 終了: async () => { stopped++; }, client: { isReady: () => false },
    }), f.file, () => {}, 10, undefined, () => f.catalog);
    await timeout.開始(); await waitFor(() => timeout.状態.phase === 'error');
    assert.equal(stopped, 3); await timeout.終了();
  } finally { await panel.終了(); f.cleanup(); }
});
