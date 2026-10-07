const { test } = require('node:test');
const assert = require('node:assert/strict');
const { mkdtempSync, rmSync } = require('node:fs');
const { join } = require('node:path');
const { tmpdir } = require('node:os');
const { pathToFileURL } = require('node:url');
const { 接続元許可, 転送オリジン } = require('../out/forwarded-origin.cjs');

const codespace = { CODESPACES: 'true', CODESPACE_NAME: 'aidiy-test', GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN: 'app.github.dev' };

test('ブラウザ版の起動判断: Codespaces と画面のない Linux だけ自動でブラウザ版にする', async () => {
  const { ブラウザ自動判定 } = await import(pathToFileURL(join(__dirname, '../scripts/launch-project.mjs')).href);
  assert.equal(ブラウザ自動判定({ CODESPACES: 'true' }, 'win32'), true);
  assert.equal(ブラウザ自動判定({}, 'linux'), true);
  assert.equal(ブラウザ自動判定({ DISPLAY: ':0' }, 'linux'), false);
  assert.equal(ブラウザ自動判定({ WAYLAND_DISPLAY: 'wayland-0' }, 'linux'), false);
  assert.equal(ブラウザ自動判定({}, 'win32'), false);
  assert.equal(ブラウザ自動判定({}, 'darwin'), false);
});

test('接続元の許可: 通常は 127.0.0.1 だけ、Codespaces ではポート転送先も許可する', () => {
  const local = new 接続元許可(8123, {});
  assert.equal(local.公開URL('/t/'), 'http://127.0.0.1:8123/t/');
  assert.ok(local.host('127.0.0.1:8123') && local.origin('http://127.0.0.1:8123'));
  for (const value of ['localhost:8123', 'aidiy-test-8123.app.github.dev', 'evil.example']) assert.equal(local.host(value), false);
  assert.equal(local.origin('https://aidiy-test-8123.app.github.dev'), false);
  assert.equal(local.origin(undefined), false);

  const forwarded = new 接続元許可(8123, codespace);
  assert.equal(forwarded.公開URL('/t/'), 'https://aidiy-test-8123.app.github.dev/t/');
  for (const origin of ['http://127.0.0.1:8123', 'https://aidiy-test-8123.app.github.dev', 'http://localhost:8123']) assert.ok(forwarded.origin(origin), origin);
  for (const origin of ['https://aidiy-test-9999.app.github.dev', 'https://evil.example', 'http://aidiy-test-8123.app.github.dev']) assert.equal(forwarded.origin(origin), false, origin);
  // 必要な変数が欠けている・不正な文字を含む場合は転送先を許可しない。
  assert.equal(転送オリジン(8123, { ...codespace, CODESPACE_NAME: '' }), undefined);
  assert.equal(転送オリジン(8123, { ...codespace, GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN: 'evil.example/x' }), undefined);
});

test('Code ブラウザ版: Codespaces の転送元からの操作だけを受け付け、公開URLを返す', async () => {
  const saved = { ...process.env };
  Object.assign(process.env, codespace);
  const preferences = mkdtempSync(join(tmpdir(), 'aidiy-browser-mode-'));
  const { 単独起動 } = require('../out/aidiy_code/server.cjs');
  const app = await 単独起動(process.cwd(), undefined, {}, join(preferences, 'model.json'));
  try {
    const port = new URL(app.url).port, path = new URL(app.url).pathname;
    assert.equal(app.publicUrl, `https://aidiy-test-${port}.app.github.dev${path}`);
    const get = headers => fetch(app.url, { headers }).then(response => response.status);
    // fetch は Host を変更できないため、Origin で転送元の許可・拒否を確認する。
    assert.equal(await get({ origin: `https://aidiy-test-${port}.app.github.dev` }), 200);
    assert.equal(await get({ origin: 'https://evil.example' }), 403);
  } finally {
    await app.close();
    for (const key of Object.keys(codespace)) if (!(key in saved)) delete process.env[key];
    rmSync(preferences, { recursive: true, force: true });
  }
});
