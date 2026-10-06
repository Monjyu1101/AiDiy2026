import { homedir } from 'node:os';
import { dirname, join } from 'node:path';
import { DiscordBot } from './bot';
import { 設定読込, 設定エラー, プロジェクトルート, type Discord設定 } from './config';
import { ライブ選択エラー, ライブモデル読込, ライブモデル保存, コードモデル読込, コードモデル保存, 起動解決, CLI実行 } from './vscode';
import { ライブ候補読込 } from './live-catalog';

export const モデル保存先 = join(homedir(), '.aidiy', 'aidiy_discord_model.json');
export type パネル状態 = { phase: 'idle' | 'connecting' | 'connected' | 'reconnecting' | 'stopping' | 'error'; message: string };
type Bot = Pick<DiscordBot, '起動' | '終了'> & { client: { isReady(): boolean } };

// UI に渡すのは表示用モデル情報と状態だけ。トークンや接続 ID は worker 内に保持する。
export class Discordパネル {
  状態: パネル状態 = { phase: 'idle', message: '未接続 · 開始ボタンで接続します。' };
  private bot?: Bot;
  private cancel?: () => void;
  private stopping?: Promise<void>;
  private generation = 0;
  private closed = false;
  private preferred: Record<string, string>;
  private codePreferred?: { provider: string; model: string };
  private catalogs = new Set<ReturnType<typeof CLI実行>>();
  constructor(private changed: (state: パネル状態) => void,
    private readConfig = 設定読込,
    private createBot: (config: Discord設定) => Bot = config => new DiscordBot(config),
    private preferenceFile = モデル保存先,
    private validateCLI = (config: Discord設定) => { 起動解決(config.cli, config.python, config.folder); },
    private timeoutMs = 40_000,
    private codePreferenceFile = join(dirname(preferenceFile), 'aidiy_discord_code_model.json'),
    private readCatalog = ライブ候補読込) {
    this.preferred = ライブモデル読込(preferenceFile) || {};
    this.codePreferred = コードモデル読込(codePreferenceFile);
  }
  private 状態変更(phase: パネル状態['phase'], message: string) {
    this.状態 = { phase, message }; this.changed(this.状態);
  }
  async 初期情報() {
    const config = this.readConfig();
    const settings = { ...config.liveModels, ...this.preferred };
    const { models, voices } = this.readCatalog();
    const notice = ライブ選択エラー(settings, { models, voices });
    return { state: this.状態, settings, models, voices, notice, code: this.codePreferred || { provider: config.provider, model: config.model } };
  }
  async コード候補(provider: unknown) {
    if (this.closed || typeof provider !== 'string' || provider.length > 200) throw new Error();
    const config = this.readConfig(), cli = 起動解決(config.cli, config.python, config.folder);
    if (!cli.引数[0]?.endsWith('.py')) throw new Error();
    const job = CLI実行({ 起動: { 実行ファイル: cli.実行ファイル, 引数: [join(プロジェクトルート, 'frontend_vscode/scripts/model-catalog.py'), cli.引数[0], provider] }, 作業フォルダ: config.folder, 本文: '', 引数: [], 制限時間: 30_000 });
    this.catalogs.add(job);
    try {
      const result = await job.完了;
      if (result.終了コード !== 0) throw new Error();
      return JSON.parse(result.回答) as { providers?: { id: string; label: string }[]; models?: { id: string; label: string }[] };
    } finally { this.catalogs.delete(job); }
  }
  コード選択保存(value: unknown) {
    if (this.closed || !['idle', 'error'].includes(this.状態.phase)) throw new Error('停止してからモデルを選択してください。');
    this.codePreferred = コードモデル保存(value, this.codePreferenceFile);
    return this.codePreferred;
  }
  選択保存(value: unknown) {
    if (this.closed || !['idle', 'error'].includes(this.状態.phase)) throw new Error('停止してからモデルを選択してください。');
    const error = ライブ選択エラー({ ...this.readConfig().liveModels, ...value as Record<string, string> }, this.readCatalog());
    if (error) throw new 設定エラー(error);
    this.preferred = ライブモデル保存(value, this.preferenceFile);
    return this.preferred;
  }
  async 開始() {
    if (this.closed || !['idle', 'error'].includes(this.状態.phase)) return;
    const run = ++this.generation;
    this.状態変更('connecting', 'Discord に接続しています…');
    let timer: ReturnType<typeof setTimeout> | undefined;
    let readyTimer: ReturnType<typeof setInterval> | undefined;
    try {
      const config = this.readConfig(); this.validateCLI(config);
      const error = ライブ選択エラー({ ...config.liveModels, ...this.preferred }, this.readCatalog());
      if (error) throw new 設定エラー(error);
      const bot = this.createBot({ ...config, ...this.codePreferred, liveModels: { ...config.liveModels, ...this.preferred } });
      this.bot = bot;
      const cancelled = new Promise<void>(resolve => { this.cancel = resolve; });
      const timeout = new Promise<never>((_, reject) => { timer = setTimeout(() => reject(new Error()), this.timeoutMs); });
      const connected = (async () => {
        await bot.起動();
        if (run !== this.generation) return;
        // Gateway の login 完了後、サーバー・チャンネルの受信完了を待つ。
        if (!bot.client.isReady()) await new Promise<void>(resolve => {
          readyTimer = setInterval(() => { if (bot.client.isReady()) resolve(); }, 100);
        });
      })();
      await Promise.race([connected, cancelled, timeout]);
      if (run !== this.generation) return;
      if (!bot.client.isReady()) throw new Error();
      this.状態変更('connected', '接続中 · コード／音声会話を利用できます。');
    } catch (error) {
      if (run !== this.generation) return;
      await this.停止();
      if (!this.closed) this.状態変更('error', error instanceof 設定エラー ? error.message : '接続できません。Bot 設定、通信、Hermes の導入を確認して再試行してください。');
    } finally {
      clearTimeout(timer);
      clearInterval(readyTimer);
      if (run === this.generation) this.cancel = undefined;
    }
  }
  接続確認() {
    if (!this.bot || !['connected', 'reconnecting'].includes(this.状態.phase)) return;
    const ready = this.bot.client.isReady();
    if (ready && this.状態.phase !== 'connected') this.状態変更('connected', '接続中 · コード／音声会話を利用できます。');
    if (!ready && this.状態.phase !== 'reconnecting') this.状態変更('reconnecting', 'Discord への再接続を待っています…');
  }
  停止(): Promise<void> {
    if (this.stopping) return this.stopping;
    ++this.generation; this.cancel?.(); this.cancel = undefined;
    const bot = this.bot; this.bot = undefined;
    if (!bot) { this.状態変更('idle', '停止しました。開始すると再接続します。'); return Promise.resolve(); }
    this.状態変更('stopping', '会話を終了し、Discord から切断しています…');
    this.stopping = (async () => {
      try { await bot.終了(); this.状態変更('idle', '停止しました。開始すると再接続します。'); }
      catch {
        this.closed = true;
        this.状態変更('error', '終了処理に失敗しました。パネルを閉じて開き直してください。');
        throw new Error('Discord の終了処理に失敗しました。');
      } finally { this.stopping = undefined; }
    })();
    return this.stopping;
  }
  async 終了() {
    this.closed = true;
    for (const job of this.catalogs) job.停止();
    await Promise.allSettled([...this.catalogs].map(job => job.完了));
    await this.停止();
  }
}
