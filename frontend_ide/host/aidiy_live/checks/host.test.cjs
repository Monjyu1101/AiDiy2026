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
const { EventEmitter } = require('node:events');
const { PassThrough } = require('node:stream');
const { LiveHost, backendUrl } = require('../../out/aidiy_live/host.cjs');

test('Live ホスト: 接続先・API 制限、3ソケット、破棄で全接続を閉じる', async () => {
  assert.throws(() => backendUrl('file:///private'));
  assert.throws(() => backendUrl('http://user:password@localhost:8091'));
  assert.throws(() => backendUrl('http://localhost:8091/core'));
  const originalSocket = global.WebSocket, originalFetch = global.fetch;
  const sockets = [], packets = [], requests = [];
  class Socket {
    readyState = 1; bufferedAmount = 0;
    constructor(url) { this.url = url; sockets.push(this); queueMicrotask(() => this.onopen?.()); }
    send(data) { this.sent = data; }
    close() { this.closed = true; this.onclose?.(); }
  }
  global.WebSocket = Socket;
  global.fetch = async (url, options) => { requests.push({ url, options }); return { ok: true, json: async () => ({ status: 'OK', data: { ok: true } }) }; };
  const host = new LiveHost('http://localhost:8091', packet => packets.push(packet), () => 'python', '/microphone.py');
  try {
    await host.receive({ type: 'api', id: 1, path: 'core/auth/ログイン', body: {} });
    assert.equal(requests.length, 0); assert.ok(packets.at(-1).error);
    await host.receive({ type: 'api', id: 2, path: 'core/AIコア/モデル情報/取得', body: { セッションID: 'session' } });
    assert.equal(requests.length, 1); assert.equal(JSON.parse(requests[0].options.body).セッションID, 'session');
    assert.equal(packets.at(-1).value.status, 'OK');
    for (const id of [3, 4, 5, 6]) await host.receive({ type: 'socket-open', id });
    assert.equal(sockets.length, 3); assert.ok(packets.some(packet => packet.type === 'socket-closed' && packet.id === 6));
    assert.equal(decodeURI(sockets[0].url.pathname), '/core/ws/AIコア');
    assert.equal(sockets[0].url.protocol, 'ws:');
    await host.receive({ type: 'socket-send', id: 3, data: 'audio-packet' });
    assert.equal(sockets[0].sent, 'audio-packet');
    sockets[0].onmessage({ data: '{"メッセージ識別":"output_audio"}' });
    assert.equal(packets.at(-1).type, 'socket-data');
    host.dispose(); assert.ok(sockets.every(socket => socket.closed));
    await host.receive({ type: 'socket-open', id: 7 }); assert.equal(sockets.length, 3);
  } finally { host.dispose(); global.WebSocket = originalSocket; global.fetch = originalFetch; }
});

test('Live ホスト: Windows PCM は前処理せず共通 Worklet へ渡し、停止でマイクを閉じる', { skip: process.platform !== 'win32' }, async () => {
  const childProcess = require('node:child_process'), original = childProcess.spawn;
  const child = new EventEmitter();
  child.stdout = new PassThrough(); child.stderr = new PassThrough(); child.stdin = new PassThrough(); child.exitCode = null;
  child.kill = () => { child.exitCode = 0; child.emit('exit', 0); };
  child.stdin.once('finish', () => queueMicrotask(() => child.kill()));
  childProcess.spawn = (python, args, options) => { assert.equal(python, 'python-test'); assert.equal(args.at(-1), '/microphone.py'); assert.equal(options.shell, false); return child; };
  const packets = [], host = new LiveHost('http://localhost:8091', packet => packets.push(packet), () => 'python-test', '/microphone.py');
  try {
    await host.receive({ type: 'mic-start', id: 1 });
    const pcm = Buffer.alloc(6144, 19); child.stdout.write(pcm.subarray(0, 100)); child.stdout.write(pcm.subarray(100));
    assert.equal(packets[0].type, 'reply'); assert.equal(packets[0].value.rate, 48000);
    assert.equal(packets[1].type, 'mic-data'); assert.deepEqual(Buffer.from(packets[1].data, 'base64'), pcm);
    await host.receive({ type: 'mic-stop', id: 1 });
    await new Promise(resolve => setImmediate(resolve)); assert.equal(child.exitCode, 0);
    const count = packets.length; child.stdout.write(pcm); assert.equal(packets.length, count);
  } finally { host.dispose(); child.kill(); childProcess.spawn = original; }
});
