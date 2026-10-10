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

import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { homedir } from 'node:os';
import { basename, dirname, join } from 'node:path';
import { DiscordBot } from './bot';
import { 設定読込, 設定エラー, プロジェクトルート, type Discord設定 } from './config';
import { ライブ選択エラー, ライブモデル読込, ライブモデル保存, コードモデル読込, コードモデル保存, 起動解決, CLI実行 } from './vscode';
import { ライブ候補読込 } from './live-catalog';
import { 接続失敗案内, 接続エラー詳細, type 接続段階 } from './connection-error';

export const モデル保存先 = join(homedir(), '.aidiy', 'aidiy_discord_model.json');
export type 機能設定 = { live: boolean; code: boolean };
/** Code は現在 ON 固定（パネルでは操作不可）。切替できるようになっても接続制御はそのまま使える。 */
export const コード固定ON = true;
export function 機能設定読込(path: string): 機能設定 {
  let live = true;
  try { const data = JSON.parse(readFileSync(path, 'utf8')); if (typeof data?.live === 'boolean') live = data.live; } catch {}
  return { live, code: true };
}
export function 機能設定保存(value: unknown, path: string): 機能設定 {
  const live = (value as { live?: unknown } | null)?.live;
  if (typeof live !== 'boolean') throw new 設定エラー('Live の ON/OFF を指定してください。');
  const features = { live, code: コード固定ON ? true : (value as { code?: unknown }).code !== false };
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, JSON.stringify(features), 'utf8');
  return features;
}
export function 機能案内(features: 機能設定) {
  return features.live && features.code ? 'コード／音声会話' : features.live ? '音声会話' : features.code ? 'コード' : '機能なし';
}
export type パネル発言 = { who: string; text: string; role: 'user' | 'ai' };
export type パネル状態 = { phase: 'idle' | 'connecting' | 'connected' | 'reconnecting' | 'stopping' | 'error'; message: string; details?: string };
type Bot = Pick<DiscordBot, '起動' | '終了' | '表示' | 'メーター' | '音声'> & Partial<Pick<DiscordBot, 'モニター設定'>> & { client: { isReady(): boolean } };

// UI に渡すのは表示用モデル情報と状態だけ。トークンや接続 ID は worker 内に保持する。
export class Discordパネル {
  状態: パネル状態 = { phase: 'idle', message: '未接続 · 接続ボタンで接続します。' };
  private bot?: Bot;
  private cancel?: () => void;
  private stopping?: Promise<void>;
  private generation = 0;
  private closed = false;
  private preferred: Record<string, string>;
  private codePreferred?: { provider: string; model: string };
  private features: 機能設定;
  private catalogs = new Set<ReturnType<typeof CLI実行>>();
  発言?: (value: パネル発言) => void;
  音量?: (value: { kind: 'input' | 'output'; level: number; bins: number[] }) => void;
  音声?: (value: { kind: 'input' | 'output'; data: string; rate: number }) => void;
  constructor(private changed: (state: パネル状態) => void,
    private readConfig = 設定読込,
    private createBot: (config: Discord設定) => Bot = config => new DiscordBot(config),
    private preferenceFile = モデル保存先,
    private validateCLI = (config: Discord設定) => { 起動解決(config.cli, config.python, config.folder); },
    private timeoutMs = 40_000,
    private codePreferenceFile = join(dirname(preferenceFile), 'aidiy_discord_code_model.json'),
    private readCatalog = ライブ候補読込,
    private featureFile = join(dirname(preferenceFile), 'aidiy_discord_features.json')) {
    this.preferred = ライブモデル読込(preferenceFile) || {};
    this.codePreferred = コードモデル読込(codePreferenceFile);
    this.features = 機能設定読込(featureFile);
  }
  private 状態変更(phase: パネル状態['phase'], message: string, details?: string) {
    this.状態 = { phase, message, ...(details ? { details } : {}) }; this.changed(this.状態);
  }
  async 初期情報() {
    const config = this.readConfig();
    const settings = { ...config.liveModels, ...this.preferred };
    const { models, voices } = this.readCatalog();
    const notice = this.features.live ? ライブ選択エラー(settings, { models, voices }) : '';
    return { state: this.状態, features: this.features, settings, models, voices, notice, code: this.codePreferred || { provider: config.provider, model: config.model }, folder: { name: basename(config.folder) || config.folder, path: config.folder } };
  }
  async コード候補(provider: unknown) {
    if (this.closed || typeof provider !== 'string' || provider.length > 200) throw new Error();
    const config = this.readConfig(), cli = 起動解決(config.cli, config.python, config.folder);
    if (!cli.引数[0]?.endsWith('.py')) throw new Error();
    const job = CLI実行({ 起動: { 実行ファイル: cli.実行ファイル, 引数: [join(プロジェクトルート, 'frontend_ide/host/scripts/model-catalog.py'), cli.引数[0], provider] }, 作業フォルダ: config.folder, 本文: '', 引数: [], 制限時間: 30_000 });
    this.catalogs.add(job);
    try {
      const result = await job.完了;
      if (result.終了コード !== 0) throw new Error();
      return JSON.parse(result.回答) as { providers?: { id: string; label: string }[]; models?: { id: string; label: string }[] };
    } finally { this.catalogs.delete(job); }
  }
  コード選択保存(value: unknown) {
    if (this.closed || !['idle', 'error'].includes(this.状態.phase)) throw new Error('切断してからモデルを選択してください。');
    this.codePreferred = コードモデル保存(value, this.codePreferenceFile);
    return this.codePreferred;
  }
  機能選択保存(value: unknown) {
    if (this.closed || !['idle', 'error'].includes(this.状態.phase)) throw new Error('切断してから機能を選択してください。');
    this.features = 機能設定保存(value, this.featureFile);
    return this.features;
  }
  選択保存(value: unknown) {
    if (this.closed || !['idle', 'error'].includes(this.状態.phase)) throw new Error('切断してからモデルを選択してください。');
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
    let stage: 接続段階 = '設定読込';
    let token = '';
    const startedAt = Date.now();
    try {
      const config = this.readConfig(); token = config.token;
      // 接続制御: 無効な機能は確認も接続もしない。
      const features = this.features;
      if (!features.live && !features.code) throw new 設定エラー('Live と Code の両方が OFF です。どちらかを ON にしてください。');
      if (features.code) { stage = 'Hermes確認'; this.validateCLI(config); }
      if (features.live) {
        stage = 'モデル確認';
        const error = ライブ選択エラー({ ...config.liveModels, ...this.preferred }, this.readCatalog());
        if (error) throw new 設定エラー(error);
      }
      stage = 'Bot作成';
      const bot = this.createBot({ ...config, ...this.codePreferred, liveModels: { ...config.liveModels, ...this.preferred }, liveEnabled: features.live, codeEnabled: features.code });
      this.bot = bot;
      bot.音声 = (kind, pcm, rate) => { if (run === this.generation) this.音声?.({ kind, data: pcm.toString('base64'), rate }); };
      bot.メーター = (kind, level, bins) => { if (run === this.generation) this.音量?.({ kind, level, bins }); };
      bot.表示 = (who, text, role) => { if (run === this.generation) this.発言?.({ who: who.slice(0, 100), text: text.slice(0, 2000), role }); };
      const cancelled = new Promise<void>(resolve => { this.cancel = resolve; });
      const timeout = new Promise<never>((_, reject) => { timer = setTimeout(() => reject(new 設定エラー(`${stage}が${this.timeoutMs / 1000}秒以内に完了しませんでした。Discordへの通信状態を確認してください。`)), this.timeoutMs); });
      const connected = (async () => {
        stage = 'Discord接続';
        await bot.起動();
        if (run !== this.generation) return;
        // Gateway の login 完了後、サーバー・チャンネルの受信完了を待つ。
        stage = '準備完了待ち';
        if (!bot.client.isReady()) await new Promise<void>(resolve => {
          readyTimer = setInterval(() => { if (bot.client.isReady()) resolve(); }, 100);
        });
      })();
      await Promise.race([connected, cancelled, timeout]);
      if (run !== this.generation) return;
      if (!bot.client.isReady()) throw new Error();
      this.状態変更('connected', `接続中 · ${機能案内(this.features)}を利用できます。`);
    } catch (error) {
      if (run !== this.generation) return;
      const message = 接続失敗案内(error, stage);
      const details = 接続エラー詳細(error, stage, token, Date.now() - startedAt);
      console.error(`[Discord] 接続失敗: ${message}\n${details}`);
      await this.停止();
      if (!this.closed) this.状態変更('error', message, details);
    } finally {
      clearTimeout(timer);
      clearInterval(readyTimer);
      if (run === this.generation) this.cancel = undefined;
    }
  }
  /** 接続中の音声をパネルで聞くかどうか。新しい接続は常に OFF から始まる。 */
  モニター(value: unknown) {
    if (typeof value !== 'boolean') throw new Error();
    if (value && !this.features.live) throw new 設定エラー('Live が OFF のためモニターできません。');
    if (value && this.状態.phase !== 'connected' && this.状態.phase !== 'reconnecting') throw new 設定エラー('接続中だけモニターできます。');
    this.bot?.モニター設定?.(value);
    return value;
  }
  接続確認() {
    if (!this.bot || !['connected', 'reconnecting'].includes(this.状態.phase)) return;
    const ready = this.bot.client.isReady();
    if (ready && this.状態.phase !== 'connected') this.状態変更('connected', `接続中 · ${機能案内(this.features)}を利用できます。`);
    if (!ready && this.状態.phase !== 'reconnecting') this.状態変更('reconnecting', 'Discord への再接続を待っています…');
  }
  停止(): Promise<void> {
    if (this.stopping) return this.stopping;
    ++this.generation; this.cancel?.(); this.cancel = undefined;
    const bot = this.bot; this.bot = undefined;
    if (!bot) { this.状態変更('idle', '切断しました。接続すると再接続します。'); return Promise.resolve(); }
    this.状態変更('stopping', '会話を終了し、Discord から切断しています…');
    this.stopping = (async () => {
      try { await bot.終了(); this.状態変更('idle', '切断しました。接続すると再接続します。'); }
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
    const stopping = this.停止();
    for (const job of this.catalogs) job.停止();
    const results = await Promise.allSettled([stopping, ...[...this.catalogs].map(job => job.完了)]);
    if (results[0].status === 'rejected') throw results[0].reason;
  }
}
