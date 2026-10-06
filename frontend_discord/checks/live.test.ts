import { test } from 'node:test';
import assert from 'node:assert/strict';
import { EventEmitter, once } from 'node:events';
import { PassThrough } from 'node:stream';
import { WebSocketServer, type WebSocket } from 'ws';
import OpusScript from 'opusscript';
import { VoiceConnectionStatus, type VoiceConnection, type AudioPlayer } from '@discordjs/voice';
import type { VoiceChannel } from 'discord.js';
import { Live接続 } from '../src/live';
import { config, userId, guildId, voiceId, waitFor } from './helpers';

async function fixture(rejectChannel = '') {
  const server = new WebSocketServer({ host: '127.0.0.1', port: 0 });
  await once(server, 'listening');
  const address = server.address(); assert.ok(address && typeof address !== 'string');
  const settings = config(); settings.coreUrl = `ws://127.0.0.1:${address.port}/core/ws/AIコア`;
  settings.liveModels = { LIVE_AI_NAME: 'openai_live' };
  const received: Record<string, any>[] = [];
  const sockets = new Map<string, WebSocket>();
  server.on('connection', socket => {
    let channel = '';
    socket.on('message', data => {
      const packet = JSON.parse(data.toString()); received.push({ ...packet, socket: channel });
      if (packet.type === 'connect') {
        channel = packet.ソケット番号; sockets.set(channel, socket);
        socket.send(JSON.stringify(channel === rejectChannel
          ? { メッセージ識別: 'error', メッセージ内容: 'テストで拒否' }
          : { メッセージ識別: 'init', セッションID: 'live-test-session', モデル設定: settings.liveModels }));
      }
    });
  });
  const speaking = Object.assign(new EventEmitter(), { users: new Map<string, number>() });
  const streams = new Map<string, PassThrough>();
  const voice = Object.assign(new EventEmitter(), {
    state: { status: VoiceConnectionStatus.Ready },
    receiver: { speaking, subscribe(user: string) { const stream = new PassThrough({ objectMode: true }); streams.set(user, stream); return stream; } },
    player: undefined as AudioPlayer | undefined,
    subscribe(player: AudioPlayer) { this.player = player; },
    destroy() { this.state.status = VoiceConnectionStatus.Destroyed; voice.emit(VoiceConnectionStatus.Destroyed); },
  });
  const members = new Map([[userId, { user: { bot: false }, id: userId }], ['unauthorized', { user: { bot: false }, id: 'unauthorized' }]]);
  const channel = { id: voiceId, guild: { id: guildId }, members } as unknown as VoiceChannel;
  const notices: string[] = []; let closed = 0;
  const connection = new Live接続(settings, channel, async text => { notices.push(text); }, () => { closed++; }, {
    join: () => voice as unknown as VoiceConnection,
    ready: async () => voice as unknown as VoiceConnection,
  });
  return { connection, received, sockets, speaking, streams, voice, notices, members, closed: () => closed,
    async cleanup() {
      connection.終了(); for (const socket of server.clients) socket.terminate();
      await new Promise<void>(resolve => server.close(() => resolve()));
    } };
}

test('Live実装がinput→0→audioのinitを待ち、許可話者のOpusと無音をAIコアへ送る', { timeout: 10000 }, async () => {
  const f = await fixture();
  const encoder = new OpusScript(48000, 2, OpusScript.Application.AUDIO);
  try {
    await f.connection.接続();
    await waitFor(() => f.received.some(packet => packet.メッセージ識別 === 'input_audio'));
    const connects = f.received.filter(packet => packet.type === 'connect');
    assert.deepEqual(connects.map(packet => packet.ソケット番号), ['input', '0', 'audio']);
    assert.equal(connects[0].セッションID, null);
    assert.equal(connects[1].セッションID, 'live-test-session');
    assert.equal(connects[2].モデル設定.LIVE_AI_NAME, 'openai_live');
    const silence = f.received.find(packet => packet.メッセージ識別 === 'input_audio')!;
    assert.equal(Buffer.from(silence.ファイル名, 'base64').length, 960);
    assert.equal(silence.socket, 'audio');
    f.speaking.emit('start', 'unauthorized'); assert.equal(f.streams.size, 0);
    f.speaking.emit('start', userId); assert.equal(f.streams.size, 1);
    const pcm = Buffer.alloc(3840);
    for (let i = 0; i < pcm.length / 2; i++) pcm.writeInt16LE(Math.round(Math.sin(i / 20) * 12000), i * 2);
    f.streams.get(userId)!.write(encoder.encode(pcm, 960));
    await waitFor(() => f.received.some(packet => packet.メッセージ識別 === 'input_audio' && Buffer.from(packet.ファイル名, 'base64').some(value => value !== 0)));
    f.connection.テキスト送信('こんにちは');
    await waitFor(() => f.received.some(packet => packet.メッセージ内容 === 'こんにちは'));
    const text = f.received.find(packet => packet.メッセージ内容 === 'こんにちは')!;
    assert.equal(text.送信モード, 'Live'); assert.equal(text.socket, 'input');
    f.connection.終了(); f.connection.終了();
    assert.equal(f.closed(), 1); assert.equal(f.voice.state.status, VoiceConnectionStatus.Destroyed);
    assert.equal(f.streams.get(userId)?.destroyed, true);
    await assert.rejects(f.connection.接続(), /開始済み/);
  } finally { encoder.delete(); await f.cleanup(); }
});

test('AI出力音声を再生し、cancel_audioで古いリソースを破棄、片側切断で全体を終了', { timeout: 10000 }, async () => {
  const f = await fixture();
  try {
    await f.connection.接続();
    const initial = f.voice.player!.state;
    assert.ok('resource' in initial);
    f.sockets.get('audio')!.send(JSON.stringify({ メッセージ識別: 'output_audio', メッセージ内容: 'audio/pcm;rate=24000', ファイル名: Buffer.alloc(960).toString('base64') }));
    await waitFor(() => initial.resource.playStream.readableLength > 0);
    f.sockets.get('audio')!.send(JSON.stringify({ メッセージ識別: 'cancel_audio' }));
    await waitFor(() => 'resource' in f.voice.player!.state && f.voice.player!.state.resource !== initial.resource);
    assert.equal(initial.resource.playStream.destroyed, true);
    f.sockets.get('0')!.close();
    await waitFor(() => f.closed() === 1);
    assert.equal(f.voice.state.status, VoiceConnectionStatus.Destroyed);
    await waitFor(() => f.notices.some(text => text.includes('接続が切れました')));
  } finally { await f.cleanup(); }
});

test('音声ソケットの接続拒否でも先に開いたソケットとDiscord接続を回収する', { timeout: 10000 }, async () => {
  const f = await fixture('audio');
  try {
    await assert.rejects(f.connection.接続());
    assert.equal(f.closed(), 1); assert.equal(f.voice.state.status, VoiceConnectionStatus.Destroyed);
    await waitFor(() => [...f.sockets.values()].every(socket => socket.readyState === 3));
  } finally { await f.cleanup(); }
});
