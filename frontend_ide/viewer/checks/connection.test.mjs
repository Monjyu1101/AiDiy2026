// -*- coding: utf-8 -*-
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026

import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { fileURLToPath } from 'node:url';
import { createCoreConnection } from '../core-connection.mjs';
import { startServer } from '../server.mjs';

const project = fileURLToPath(new URL('../web/', import.meta.url));
const valid = { status: 'OK', data: { available_models: {}, モデル設定: {} } };
test('手動開始後はコア停止でも作業を維持し、復帰時に同じセッションで再接続する', async () => {
  let healthy = true, calls = 0;
  const backend = createServer((req, res) => {
    calls++;
    assert.equal(decodeURI(req.url), '/core/AIコア/モデル情報/取得');
    assert.equal(req.method, 'POST');
    req.resume(); res.writeHead(healthy ? 200 : 503, { 'content-type': 'application/json' });
    res.end(JSON.stringify(healthy ? valid : { status: 'NG' }));
  });
  await new Promise(done => backend.listen(0, '127.0.0.1', done));
  const connection = createCoreConnection(project, { target: `http://127.0.0.1:${backend.address().port}` });
  const app = await startServer(project, 0, { connection });
  const get = path => fetch(app.url + path);
  const post = path => fetch(app.url + 'api/connection/' + path, { method: 'POST' });
  try {
    assert.equal(calls, 0); // 起動だけでは接続を作らない
    assert.equal((await get('api/connection').then(r => r.json())).connected, false);
    for (const path of ['api/galaxy', 'api/file?path=app.js', 'api/raw?path=a.png', 'api/document?path=a.pdf']) assert.equal((await get(path)).status, 503);
    assert.equal((await get('connection.js')).status, 200);
    assert.equal((await get('licenses.html')).status, 200);
    assert.equal((await post('connect').then(r => r.json())).connected, true);
    assert.equal((await get('api/galaxy')).status, 200);
    assert.equal((await get('api/file?path=app.js')).status, 200);
    const startedAt = connection.state().startedAt;
    healthy = false;
    await connection.check();
    assert.equal(connection.state().connected, false);
    assert.equal((await get('api/file?path=app.js')).status, 200);
    assert.equal(connection.state().mode, 'online');
    assert.equal(connection.state().wanted, true);
    assert.equal(connection.state().active, true);
    assert.equal(connection.state().startedAt, startedAt);
    healthy = true;
    const failedCalls = calls;
    await connection.check();
    assert.ok(calls > failedCalls);
    assert.equal(connection.state().active, true);
    assert.equal(connection.state().connected, true);
    assert.equal(connection.state().startedAt, startedAt);
    assert.equal((await post('connect').then(r => r.json())).connected, true);
    assert.equal((await post('disconnect').then(r => r.json())).connected, false);
    const previous = calls;
    await connection.check();
    assert.equal(calls, previous); // 明示切断後は自動接続しない
    assert.equal((await get('api/galaxy')).status, 503);
    healthy = false;
    const offline = await post('offline').then(r => r.json());
    assert.equal(offline.mode, 'offline');
    assert.equal(offline.active, true);
    assert.equal(offline.connected, false);
    await connection.check();
    assert.equal(calls, previous); // オフラインではコアを呼ばない
    assert.equal((await get('api/galaxy')).status, 200);
    assert.equal((await get('api/file?path=app.js')).status, 200);
    assert.equal((await get('api/connection/offline')).status, 405);
    await post('disconnect');
    assert.equal((await get('api/galaxy')).status, 503);
  } finally {
    app.server.closeAllConnections(); backend.closeAllConnections();
    await Promise.all([new Promise(done => app.server.close(done)), new Promise(done => backend.close(done))]);
  }
});

test('接続処理中に切断した場合、遅れて届いた成功で再接続しない', async () => {
  let release;
  const connection = createCoreConnection(project, { target: 'http://127.0.0.1:8091', fetcher: () => new Promise(done => { release = done; }) });
  const pending = connection.connect();
  connection.disconnect();
  release({ ok: true, json: async () => valid });
  await pending;
  assert.equal(connection.state().connected, false);
  assert.equal(connection.state().wanted, false);
  connection.close();
});

test('AiDiy の応答形式でないサーバーをオンラインと表示しない', async () => {
  const connection = createCoreConnection(project, { target: 'http://127.0.0.1:8091', fetcher: async () => ({ ok: true, json: async () => ({ status: 'OK' }) }) });
  try { const state=await connection.connect();assert.equal(state.connected, false);assert.equal(state.active,false);assert.equal(state.wanted,false);assert.equal(state.startedAt,null); }
  finally { connection.close(); }
});

test('接続確認中のオフライン切り替えを遅い応答で上書きしない', async () => {
  let release;
  const connection = createCoreConnection(project, { target: 'http://127.0.0.1:8091', fetcher: () => new Promise(done => { release = done; }) });
  try {
    const pending = connection.connect();
    connection.offline();
    release({ ok: true, json: async () => valid });
    await pending;
    assert.equal(connection.state().mode, 'offline');
    assert.equal(connection.state().active, true);
    assert.equal(connection.state().connected, false);
    assert.equal(connection.state().connecting, false);
  } finally { connection.close(); }
});

test('起動の起点は接続成立時刻で、稼働確認では変わらず次回利用で更新する', async t => {
  let now = 1000;
  t.mock.method(Date, 'now', () => now);
  const connection = createCoreConnection(project, { target: 'http://127.0.0.1:8091', fetcher: async () => ({ ok: true, json: async () => valid }) });
  try {
    assert.equal(connection.state().startedAt, null);
    now = 2000;
    assert.equal((await connection.connect()).startedAt, 2000);
    now = 3000;
    assert.equal((await connection.check()).startedAt, 2000);
    assert.equal(connection.disconnect().startedAt, null);
    now = 4000;
    assert.equal(connection.offline().startedAt, 4000);
    now = 5000;
    assert.equal((await connection.check()).startedAt, 4000);
    assert.equal((await connection.connect()).startedAt, 5000);
  } finally { connection.close(); }
});
