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

import { AttachmentBuilder, ChannelType, Client, Events, GatewayIntentBits, PermissionFlagsBits, type Message, type SendableChannels, type VoiceChannel, type VoiceState } from 'discord.js';
import { Code接続 } from './code';
import { Live接続 } from './live';
import type { Discord設定 } from './config';
import { コマンド解析, メンション禁止, 会話キー, 利用許可, 本文分割 } from './commands';
import { Discord通信, Gateway戦略 } from './network';
import { ライブ接続エラー } from './connection-error';

export async function 回答送信(message: Message, text: string) {
  if (!message.channel.isSendable()) return;
  await チャンネル回答送信(message.channel, text);
}

async function チャンネル回答送信(channel: SendableChannels, text: string) {
  // 長いコード回答はファイルにまとめ、Discord の連投制限を避ける。
  if (text.length > 6000) {
    await channel.send({ content: '回答を添付しました。', files: [new AttachmentBuilder(Buffer.from(text, 'utf8'), { name: 'AiDiy回答.txt' })], allowedMentions: メンション禁止 });
    return;
  }
  for (const content of 本文分割(text)) await channel.send({ content, allowedMentions: メンション禁止 });
}

type Live実体 = Pick<Live接続, '接続' | '終了' | 'テキスト送信' | 'channel' | '表示' | 'メーター' | 'モニター送信'>;
type Live生成 = (config: Discord設定, channel: VoiceChannel, notify: (text: string) => Promise<void>, onClose: () => void) => Live実体;

export class DiscordBot {
  readonly client: Client;
  private code: Code接続;
  private live?: Live実体;
  private liveTextChannel = '';
  private closing = false;
  private shutdown?: Promise<void>;
  private connected = false;
  private voiceSync?: Promise<void>;
  private voiceDirty = false;
  private chatQueue = new Map<string, Promise<void>>();
  private chatCount = new Map<string, number>();
  private network?: Discord通信;
  // パネル下部に最後の発言を表示する。Discord への投稿とは独立している。
  表示?: (who: string, text: string, role: 'user' | 'ai') => void;
  メーター?: (kind: 'input' | 'output', level: number, bins: number[]) => void;
  /** パネルのモニター用。ON の間だけ Live の音声を渡す（接続直後は OFF）。 */
  音声?: (kind: 'input' | 'output', pcm: Buffer, rate: number) => void;
  private monitor = false;
  モニター設定(on: boolean) {
    this.monitor = on;
    if (this.live) this.live.モニター送信 = on ? (kind, pcm, rate) => this.音声?.(kind, pcm, rate) : undefined;
  }
  constructor(private config: Discord設定, client?: Client, code?: Code接続,
    private createLive: Live生成 = (...args) => new Live接続(...args)) {
    if (!client) this.network = new Discord通信();
    this.client = client ?? new Client({ intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages, GatewayIntentBits.MessageContent, GatewayIntentBits.GuildVoiceStates], allowedMentions: メンション禁止, rest: { agent: this.network!.rest }, ws: { buildStrategy: Gateway戦略 } });
    this.code = code ?? new Code接続(config);
    this.client.on(Events.ClientReady, () => {
      console.log(`[Discord] 接続しました。${this.codeEnabled ? '専用チャンネルに話しかけると返信します。' : ''}${this.liveEnabled ? '音声は入退室に合わせて接続します。' : ''}`);
      this.connected = true; void this.自動ライブ同期();
    });
    this.client.on(Events.ShardResume, () => { this.connected = true; void this.自動ライブ同期(); });
    this.client.on(Events.MessageCreate, message => { void this.メッセージ受信(message).catch(() => console.error('[Discord] メッセージ処理・返信に失敗しました。権限と接続状態を確認してください。')); });
    this.client.on(Events.Error, () => { if (!this.closing) console.error('[Discord] Gateway エラーが発生しました。接続設定を確認してください。'); });
    this.client.on(Events.ShardDisconnect, () => { this.connected = false; this.live?.終了(); });
    this.client.on(Events.VoiceStateUpdate, (oldState, state) => this.ボイス状態変更(oldState, state));
  }
  // 接続制御。省略時は ON（Code は現状パネルで ON 固定）。
  private get liveEnabled() { return this.config.liveEnabled !== false; }
  private get codeEnabled() { return this.config.codeEnabled !== false; }
  async メッセージ受信(message: Message) {
    if (this.closing || message.webhookId || !利用許可(this.config, message.guildId, message.channelId, message.author.id, message.author.bot)) return;
    const command = コマンド解析(message.content, this.config.prefix, this.client.user?.id ?? '');
    if (!command) return;
    const key = 会話キー(message.guildId!, message.channelId, message.author.id);
    const reply = (text: string) => message.reply({ content: text, allowedMentions: メンション禁止 }).then(() => {});
    try {
      if (!this.codeEnabled && ['stop', 'new', 'chat'].includes(command.name)) { if (command.name === 'chat') await reply('Code は OFF のため利用できません。'); return; }
      if (!this.liveEnabled && ['leave', 'live'].includes(command.name)) { await reply('Live は OFF のため利用できません。'); return; }
      switch (command.name) {
        case 'help':
          await reply([
            ...this.codeEnabled ? ['このチャンネルに、そのまま話しかけてください。AiDiy が返信します。'] : [],
            ...this.liveEnabled ? ['音声で話すときは専用のボイスチャンネルに参加してください。退出すると音声会話も終了します。'] : [],
          ].join('\n') || '利用できる機能がありません。'); return;
        case 'status': await reply(`Code: ${!this.codeEnabled ? 'OFF' : this.code.実行中(key) ? '実行中' : '待機中'} / Live: ${!this.liveEnabled ? 'OFF' : this.live ? '接続中' : '未接続'}`); return;
        case 'stop': {
          const running = this.code.実行中(key); this.code.停止(key);
          await reply(running ? '停止を要求しました。実行済みの変更は残ります。' : '実行中のコード要求はありません。'); return;
        }
        case 'new': this.code.リセット(key); await reply('新しいコード会話を開始します。'); return;
        case 'leave':
          if (this.live) {
            this.ライブ操作確認(message);
            this.live.終了();
          }
          await reply('ライブ接続を終了しました。'); return;
        case 'live':
          if (this.live) {
            this.ライブ操作確認(message);
            if (command.text) { this.live.テキスト送信(command.text); await reply('LiveAI に送信しました。'); }
            else await reply('ライブは接続中です。終了する場合は leave を使ってください。');
            return;
          }
          if (command.text) throw new Error('先に live でボイスチャンネルに接続してください。');
          await this.ライブ開始(message); return;
        case 'chat': {
          if (!command.text) return;
          await this.チャット受付(message, key, command.text);
          return;
        }
      }
    } catch (error) {
      if (!this.closing) {
        // Discord/API内部エラーのオブジェクトには認証情報が含まれ得るため出力しない。
        const text = error instanceof ライブ接続エラー || error instanceof Error && error.constructor === Error ? error.message : '処理に失敗しました。設定・権限・接続状態を確認してください。';
        await reply(text.slice(0, 1800));
      }
    }
  }
  private async チャット受付(message: Message, key: string, text: string) {
    const count = this.chatCount.get(key) || 0;
    if (count >= 10) throw new Error('返信待ちのメッセージが多いため、少し待ってから送ってください。');
    this.chatCount.set(key, count + 1);
    const previous = this.chatQueue.get(key) || Promise.resolve();
    this.表示?.(message.member?.displayName ?? message.author.displayName, text, 'user');
    const pending = previous.catch(() => {}).then(async () => {
      if (this.closing) return;
      const run = this.code.実行(key, text);
      const typing = () => { if ('sendTyping' in message.channel) void message.channel.sendTyping().catch(() => {}); };
      typing(); const timer = setInterval(typing, 8000);
      try {
        const answer = await run;
        if (this.closing) return;
        this.表示?.(this.client.user?.displayName ?? 'AiDiy', answer, 'ai');
        await 回答送信(message, answer);
      }
      finally { clearInterval(timer); }
    });
    this.chatQueue.set(key, pending);
    try { await pending; }
    finally {
      const remaining = (this.chatCount.get(key) || 1) - 1;
      if (remaining) this.chatCount.set(key, remaining); else this.chatCount.delete(key);
      if (this.chatQueue.get(key) === pending) this.chatQueue.delete(key);
    }
  }
  private 参加者あり(channel: VoiceChannel) {
    const member = channel.members.get(this.config.userId);
    return !!member && !member.user.bot;
  }
  private 希望ボイス(): VoiceChannel | undefined {
    const guild = this.client.guilds.cache.get(this.config.guildId);
    const channel = guild?.channels.cache.get(this.config.voiceChannelId);
    if (channel?.type === ChannelType.GuildVoice && this.参加者あり(channel)) return channel;
  }
  private ボイス状態変更(oldState: VoiceState, state: VoiceState) {
    if (this.closing || state.guild.id !== this.config.guildId) return;
    const live = this.live;
    if (live) {
      if (state.id === this.client.user?.id && state.channelId !== live.channel.id) { live.終了(); return; }
      // 接続準備中でも、最後の利用者が退出した時点で直ちに中断する。
      if (!this.参加者あり(live.channel)) live.終了();
    }
    if (state.id === this.config.userId && state.channelId !== oldState.channelId) void this.自動ライブ同期();
  }
  private 自動ライブ同期(): Promise<void> {
    if (!this.liveEnabled || !this.connected || this.closing) return Promise.resolve();
    this.voiceDirty = true;
    if (this.voiceSync) return this.voiceSync;
    this.voiceSync = this.自動ライブ処理().catch(() => {
      console.error('[Discord] 音声会話を開始できません。チャンネル設定と権限を確認してください。');
    }).finally(() => { this.voiceSync = undefined; });
    return this.voiceSync;
  }
  private async 自動ライブ処理() {
    while (this.voiceDirty && this.connected && !this.closing) {
      this.voiceDirty = false;
      if (this.live) continue;
      const channel = this.希望ボイス();
      if (!channel) continue;
      // 接続通知は設定した専用テキストチャンネルへ送る。字幕はパネル表示のみ。
      const textId = this.config.textChannelId;
      const textChannel = await this.client.channels.fetch(textId);
      if (!textChannel?.isSendable() || !('guildId' in textChannel) || textChannel.guildId !== this.config.guildId) throw new Error('音声会話の返信先がありません。');
      if (!this.connected || this.closing || this.live) return;
      if (this.希望ボイス()?.id !== channel.id) { this.voiceDirty = true; continue; }
      const notify = (text: string) => チャンネル回答送信(textChannel, text);
      try { await this.チャンネルライブ開始(channel, textId, notify); }
      catch (error) {
        if (!this.closing && this.connected && this.希望ボイス()?.id === channel.id) {
          const failure = error instanceof ライブ接続エラー ? error : new ライブ接続エラー(error, 'ボイス参加確認', this.config.token);
          console.error(`[Discord Live] ${failure.message}`);
          await notify(`${failure.message}\nボイスチャンネルに入り直すと再試行します。`);
        }
      }
    }
  }
  private ライブ操作確認(message: Message) {
    if (this.liveTextChannel !== message.channelId || message.member?.voice.channelId !== this.live?.channel.id) {
      throw new Error('開始時のテキストチャンネルから操作し、Bot と同じボイスチャンネルに参加してください。');
    }
  }
  private async ライブ開始(message: Message) {
    const channel = message.member?.voice.channel;
    if (!channel || channel.type !== ChannelType.GuildVoice) throw new Error('通常のボイスチャンネルに参加してから live を実行してください。');
    await this.チャンネルライブ開始(channel, message.channelId, text => 回答送信(message, text));
  }
  private async チャンネルライブ開始(channel: VoiceChannel, textId: string, notify: (text: string) => Promise<void>) {
    if (channel.id !== this.config.voiceChannelId) throw new Error('DISCORD_VOICE_CHANNEL_ID に設定したボイスチャンネルに参加してください。');
    if (channel.guild.id !== this.config.guildId || !this.参加者あり(channel)) throw new Error('設定したサーバー内で、利用者が参加中のボイスチャンネルに接続してください。');
    const me = channel.guild.members.me;
    if (!me || !channel.permissionsFor(me)?.has([PermissionFlagsBits.ViewChannel, PermissionFlagsBits.Connect, PermissionFlagsBits.Speak])) throw new Error('Bot にボイスチャンネルの表示・接続・発言権限が必要です。');
    let live: Live実体;
    live = this.createLive(this.config, channel, notify, () => {
      if (this.live === live) { this.live = undefined; this.liveTextChannel = ''; }
    });
    live.表示 = (who, text, role) => this.表示?.(who, text, role);
    live.メーター = (kind, level, bins) => this.メーター?.(kind, level, bins);
    if (this.monitor) live.モニター送信 = (kind, pcm, rate) => this.音声?.(kind, pcm, rate);
    // await 前に登録し、同時に live / leave が届いても接続を重複生成しない。
    this.live = live; this.liveTextChannel = textId;
    try {
      if (this.live !== live || this.closing) { live.終了(); return; }
      await live.接続();
      if (this.live === live && !this.closing) await notify('音声会話に接続しました。そのまま話しかけてください。');
    } catch (error) {
      live.終了();
      throw error instanceof ライブ接続エラー ? error : new ライブ接続エラー(error, 'Discordボイス接続', this.config.token);
    }
  }
  async 起動() {
    if (this.closing) throw new Error('Discord 接続は終了しています。');
    try { await this.client.login(this.config.token); }
    catch (error) { await this.終了().catch(() => {}); throw error; }
  }
  終了(): Promise<void> {
    if (this.shutdown) return this.shutdown;
    this.closing = true; this.connected = false;
    // REST応答やコード実行の完了待ちより先に音声・Gatewayを切断する。
    // 遅れて完了する受信処理は closing の判定で再接続・返信を抑止する。
    const cleanup = [() => this.live?.終了(), () => this.code.終了(), () => this.client.destroy(), () => this.network?.終了()];
    this.shutdown = Promise.allSettled(cleanup.map(stop => Promise.resolve().then(stop))).then(results => {
      if (results.some(result => result.status === 'rejected')) throw new Error('Discord 接続の終了処理に失敗しました。');
    });
    return this.shutdown;
  }
}
