import { test } from 'node:test';
import assert from 'node:assert/strict';
import { once } from 'node:events';
import { readFileSync } from 'node:fs';
import WebSocket from 'ws';
import { パネルWeb起動, ブラウザ用HTML } from '../src/web-server';
import type { パネルサービス } from '../src/panel-service';

// panel-service の代わりに、要求と通知の中継だけを確認する模擬サービス。
function fakeService() {
  const calls: unknown[][] = [];
  let send: ((data: Record<string, unknown> & { type: string }) => void) | undefined;
  let stopped = 0;
  const factory = ((callback: typeof send) => {
    send = callback;
    return { panel: {}, 要求: async (action: unknown, value: unknown) => { calls.push([action, value]); return action === 'bad' ? { error: '拒否' } : { result: { action, value } }; }, 終了: async () => { stopped++; } };
  }) as unknown as typeof パネルサービス;
  return { factory, calls, emit: (data: Record<string, unknown> & { type: string }) => send!(data), stopped: () => stopped };
}

test('ブラウザ版の画面は Electron 版と同じ index.html に WebSocket 用の橋渡しだけを加える', () => {
  const html = ブラウザ用HTML(readFileSync(new URL('../panel/index.html', import.meta.url), 'utf8'));
  assert.match(html, /connect-src 'self'/);
  assert.doesNotMatch(html, /connect-src 'none'/);
  assert.ok(html.indexOf('web-bridge.js') < html.indexOf('visualizer.js') && html.indexOf('visualizer.js') < html.indexOf('view.js'));
  assert.throws(() => ブラウザ用HTML('<html></html>'));
});

test('ブラウザ版サーバー: 許可した接続元の要求だけを中継し、通知を配信して、画面が閉じたら終了する', { timeout: 10000 }, async () => {
  const service = fakeService();
  const codespaces = process.env.CODESPACES;
  delete process.env.CODESPACES; // Codespaces ではポート転送先の URL になるため。
  const app = await パネルWeb起動({ service: service.factory, idleMs: 50 });
  if (codespaces !== undefined) process.env.CODESPACES = codespaces;
  try {
    const origin = new URL(app.url).origin;
    assert.equal(app.publicUrl, app.url, 'Codespaces 以外ではローカルURLを開く');
    assert.equal((await fetch(app.url)).status, 200);
    assert.equal((await fetch(new URL('style.css', app.url))).status, 200);
    assert.equal((await fetch(app.url, { headers: { origin: 'https://evil.example' } })).status, 403);
    assert.equal((await fetch(new URL('/wrong/', app.url))).status, 404);
    assert.equal((await fetch(new URL('../src/config.ts', app.url))).status, 404);

    const wsUrl = new URL('ws', app.url); wsUrl.protocol = 'ws:';
    const rejected = new WebSocket(wsUrl, { origin: 'https://evil.example' });
    await assert.rejects(once(rejected, 'open'));

    const socket = new WebSocket(wsUrl, { origin });
    await once(socket, 'open');
    const next = () => once(socket, 'message').then(([data]) => JSON.parse(String(data)));
    socket.send(JSON.stringify({ id: 1, action: 'select', value: { a: 1 } }));
    assert.deepEqual(await next(), { id: 1, result: { action: 'select', value: { a: 1 } } });
    socket.send(JSON.stringify({ id: 2, action: 'bad' }));
    assert.deepEqual(await next(), { id: 2, error: '拒否' });
    service.emit({ type: 'activity', activity: { who: 'AiDiy', text: 'こんにちは', role: 'ai' } });
    assert.deepEqual(await next(), { type: 'activity', activity: { who: 'AiDiy', text: 'こんにちは', role: 'ai' } });
    socket.send('not json'); socket.send(JSON.stringify({ action: 'start' }));
    socket.send(JSON.stringify({ id: 3, action: 'initial' }));
    assert.equal((await next()).id, 3, 'id のない要求・不正な JSON は無視する');
    assert.deepEqual(service.calls.map(([action]) => action), ['select', 'bad', 'initial']);

    socket.close();
    await app.closed;
    assert.equal(service.stopped(), 1, '画面が閉じたら猶予の後に Bot も終了する');
  } finally { await app.close(); }
});

test('ブラウザ版サーバー: 一度も画面が開かれなければ猶予の後に終了する', { timeout: 10000 }, async () => {
  const service = fakeService();
  const app = await パネルWeb起動({ service: service.factory, firstIdleMs: 30 });
  await app.closed;
  assert.equal(service.stopped(), 1);
});

test('Codespaces は初回画面接続を120秒以上待っても終了しない', async t => {
  const service = fakeService();
  const env = { CODESPACES: 'true', CODESPACE_NAME: 'aidiy-test', GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN: 'app.github.dev' };
  const saved = { ...process.env };
  Object.assign(process.env, env);
  t.mock.timers.enable({ apis: ['setTimeout'] });
  let app;
  try { app = await パネルWeb起動({ service: service.factory }); }
  finally {
    for (const key of Object.keys(env)) {
      if (key in saved) process.env[key] = saved[key];
      else delete process.env[key];
    }
  }
  try {
    t.mock.timers.tick(120_001);
    t.mock.timers.reset();
    assert.equal(service.stopped(), 0);
    assert.equal((await fetch(app.url)).status, 200);
  } finally { await app.close(); }
  assert.equal(service.stopped(), 1);
});
