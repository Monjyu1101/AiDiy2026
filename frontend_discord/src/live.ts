import { createAudioPlayer, createAudioResource, EndBehaviorType, entersState, joinVoiceChannel, NoSubscriberBehavior, StreamType, VoiceConnectionStatus, type AudioReceiveStream, type VoiceConnection } from '@discordjs/voice';
import type { VoiceChannel } from 'discord.js';
import WebSocket from 'ws';
import OpusScript from 'opusscript';
import type { LiveSocket, Packet } from '../../frontend_vscode/aidiy_live/src/protocol';
import { LiveConnection, 入力レート, 音声入力, 音声操作 } from './vscode';
import type { Discord設定 } from './config';
import { Discord音声出力, 音声入力ミキサー } from './audio';

const 音声トランスポート = {
  join: (channel: VoiceChannel) => joinVoiceChannel({ channelId: channel.id, guildId: channel.guild.id,
    adapterCreator: channel.guild.voiceAdapterCreator, selfDeaf: false, selfMute: false }),
  ready: (voice: VoiceConnection) => entersState(voice, VoiceConnectionStatus.Ready, 30000),
};

export class Live接続 {
  private core: InstanceType<typeof LiveConnection>;
  private voice?: VoiceConnection;
  private player = createAudioPlayer({ behaviors: { noSubscriber: NoSubscriberBehavior.Pause } });
  private output?: Discord音声出力;
  private mixer = new 音声入力ミキサー();
  private inputs = new Map<string, { stream: AudioReceiveStream; decoder: OpusScript }>();
  private sockets = new Set<WebSocket>();
  private heartbeat?: NodeJS.Timeout;
  private capture?: NodeJS.Timeout;
  private transcriptTimer?: NodeJS.Timeout;
  private transcript = '';
  private rate = 16000;
  private closed = false;
  private ready = false;
  private started = false;
  private notifyQueue = Promise.resolve();
  private pendingNotices = 0;
  constructor(private config: Discord設定, readonly channel: VoiceChannel, private notify: (text: string) => Promise<void>, private onClose: () => void,
    private transport = 音声トランスポート) {
    this.rate = 入力レート(config.liveModels.LIVE_AI_NAME || '');
    this.core = new LiveConnection(config.coreUrl, packet => this.受信(packet), () => this.失敗('AIコアとの接続が切れました。ボイスチャンネルに入り直してください。'), url => {
      const socket = new WebSocket(url, { handshakeTimeout: 15000, maxPayload: 8 * 1024 * 1024 });
      this.sockets.add(socket);
      socket.once('close', () => this.sockets.delete(socket));
      return socket as unknown as LiveSocket;
    });
    this.player.on('error', () => this.失敗('Discord の音声再生に失敗しました。'));
  }
  private 通知(text: string) {
    if (this.pendingNotices >= 8) return;
    this.pendingNotices++;
    this.notifyQueue = this.notifyQueue.then(() => this.notify(text)).catch(() => {
      console.error('[Discord] ライブ通知を送信できません。');
    }).finally(() => { this.pendingNotices--; });
  }
  private 失敗(text: string) {
    if (this.closed) return;
    this.終了(); this.通知(text);
  }
  private 再生開始() {
    this.player.stop(true);
    this.output?.destroy();
    if (this.closed) return;
    this.output = new Discord音声出力();
    this.output.on('error', () => this.失敗('AI 音声を再生できません。'));
    this.player.play(createAudioResource(this.output, { inputType: StreamType.Opus }));
  }
  private 受信(packet: Packet) {
    if (this.closed) return;
    if (packet.メッセージ識別 === 'init') {
      const settings = packet.モデル設定 as Record<string, unknown> | undefined;
      if (typeof settings?.LIVE_AI_NAME === 'string') this.rate = 入力レート(settings.LIVE_AI_NAME);
    } else if (packet.メッセージ識別 === 'cancel_audio') this.再生開始();
    else if (packet.メッセージ識別 === 'output_audio' && packet.ファイル名) {
      const mime = String(packet.メッセージ内容);
      const sampleRate = /rate=(\d+)/i.exec(mime)?.[1];
      if (!mime.startsWith('audio/pcm') || sampleRate && sampleRate !== '24000') {
        this.失敗('AIコアから対応外の音声形式を受信しました（24kHz PCM16 が必要です）。'); return;
      }
      try { this.output?.追加(Buffer.from(packet.ファイル名, 'base64')); }
      catch { this.失敗('AI 音声のサイズまたは形式が不正です。接続し直してください。'); }
    } else if (packet.メッセージ識別 === 'error') this.失敗('AIコアでライブ接続エラーが発生しました。バックエンドの設定・ログを確認してください。');
    else if (packet.チャンネル === '0' && ['output_text', 'output_request', 'recognition_output', 'output'].includes(packet.メッセージ識別 || '')) {
      const text = String(packet.メッセージ内容 || '').trim();
      if (text === '!') { this.失敗('LiveAI への送信に失敗しました。AIコアの接続設定を確認してください。'); return; }
      if (text) {
        this.transcript = (this.transcript + text + '\n').slice(-32000);
        if (!this.transcriptTimer) this.transcriptTimer = setTimeout(() => {
          const content = this.transcript; this.transcript = ''; this.transcriptTimer = undefined;
          if (!this.closed) this.通知(`【Live】\n${content}`);
        }, 1500);
      }
    }
  }
  async 接続() {
    if (this.started || this.closed) throw new Error('ライブ接続は開始済みです。');
    this.started = true;
    try {
      this.voice = this.transport.join(this.channel);
      this.voice.on('error', () => this.失敗('Discord のボイス接続でエラーが発生しました。'));
      this.voice.on(VoiceConnectionStatus.Disconnected, () => this.失敗('ボイス接続が切れました。ボイスチャンネルに入り直してください。'));
      this.voice.on(VoiceConnectionStatus.Destroyed, () => this.終了());
      await this.transport.ready(this.voice);
      if (this.closed) throw new Error('ライブ接続を中断しました。');
      this.voice.subscribe(this.player);
      this.再生開始();
      await this.core.connect({ codeBasePath: this.config.folder, modelSettings: this.config.liveModels });
      if (this.closed) throw new Error('ライブ接続を中断しました。');
      if (!this.core.send('input', 音声操作(true, true))) throw new Error('AIコアへ音声設定を送信できません。');
      this.ready = true;
      this.voice.receiver.speaking.on('start', this.話者開始);
      // 接続中から話していた人も取り込む。
      for (const user of this.voice.receiver.speaking.users.keys()) this.話者開始(user);
      this.capture = setInterval(() => {
        for (const user of this.inputs.keys()) if (!this.話者許可(user)) this.話者停止(user);
        if (!this.core.send('audio', 音声入力(this.mixer.フレーム(this.rate).toString('base64')))) {
          this.失敗('AIコアへの音声送信が滞留しました。ボイスチャンネルに入り直してください。');
        }
      }, 20);
      const alive = new WeakMap<WebSocket, boolean>();
      for (const socket of this.sockets) { alive.set(socket, true); socket.on('pong', () => alive.set(socket, true)); }
      this.heartbeat = setInterval(() => {
        for (const socket of this.sockets) {
          if (socket.readyState !== WebSocket.OPEN || !alive.get(socket)) { this.失敗('AIコアが応答しません。ボイスチャンネルに入り直してください。'); return; }
          alive.set(socket, false); socket.ping();
        }
      }, 20000);
    } catch (error) { this.終了(); throw error; }
  }
  private 話者許可(user: string): boolean {
    const member = this.channel.members.get(user);
    return !!member && !member.user.bot && user === this.config.userId;
  }
  private 話者開始 = (user: string) => {
    if (this.closed || !this.ready || !this.voice || this.inputs.has(user) || !this.話者許可(user)) return;
    try {
      const decoder = new OpusScript(48000, 2, OpusScript.Application.AUDIO);
      const stream = this.voice.receiver.subscribe(user, { end: { behavior: EndBehaviorType.AfterSilence, duration: 300 } });
      this.inputs.set(user, { stream, decoder });
      stream.on('data', (opus: Buffer) => {
        if (!this.話者許可(user)) { this.話者停止(user); return; }
        try { this.mixer.追加(user, decoder.decode(opus)); }
        catch { this.失敗('Discord の受信音声を復号できません。ボイスチャンネルに入り直してください。'); }
      });
      stream.on('error', () => this.失敗('Discord の音声受信に失敗しました。'));
      stream.once('close', () => { if (this.inputs.get(user)?.stream === stream) this.話者停止(user); });
    } catch { this.失敗('Discord の音声受信を開始できません。'); }
  };
  private 話者停止(user: string) {
    const input = this.inputs.get(user);
    if (!input) return;
    this.inputs.delete(user); this.mixer.削除(user); input.stream.destroy(); input.decoder.delete();
  }
  テキスト送信(text: string) {
    if (!this.ready || this.closed) throw new Error('ライブ接続の準備が完了していません。');
    if (!this.core.send('input', { チャンネル: '0', メッセージ識別: 'input_text', メッセージ内容: text, 送信モード: 'Live', 出力先チャンネル: '0' })) throw new Error('ライブに送信できません。');
  }
  終了() {
    if (this.closed) return;
    this.closed = true; this.ready = false;
    clearInterval(this.capture); clearInterval(this.heartbeat); clearTimeout(this.transcriptTimer);
    this.core.send('input', 音声操作(false, false)); this.core.disconnect();
    for (const socket of this.sockets) socket.terminate();
    this.sockets.clear();
    this.voice?.receiver.speaking.off('start', this.話者開始);
    for (const user of this.inputs.keys()) this.話者停止(user);
    this.player.stop(true); this.output?.destroy();
    if (this.voice && this.voice.state.status !== VoiceConnectionStatus.Destroyed) this.voice.destroy();
    this.onClose();
  }
}
