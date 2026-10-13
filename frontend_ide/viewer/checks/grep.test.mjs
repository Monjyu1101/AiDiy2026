// -*- coding: utf-8 -*-
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026

import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, rm, symlink } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { grepFiles, startServer } from '../server.mjs';
import { createCoreConnection } from '../core-connection.mjs';

test('grep は内容の部分一致で検索し、除外フォルダ・バイナリ・巨大ファイル・外部リンクを読まない', async () => {
  const temp = await mkdtemp(join(tmpdir(), 'aidiy-grep-'));
  const root = join(temp, 'project');
  await mkdir(root);
  try {
    for (const dir of ['src', 'node_modules', 'backup']) await mkdir(join(root, dir));
    await writeFile(join(root, 'src', '日本語.txt'), 'AiDiy 日本語 (a+b)');
    await writeFile(join(root, 'data.csv'), '名前,値\nAiDiy,1');
    await writeFile(join(root, 'AiDiy.txt'), '名前だけ一致');
    await writeFile(join(root, 'binary.bin'), Buffer.from([0, 65, 105, 68, 105, 121]));
    await writeFile(join(root, 'large.txt'), 'AiDiy'.repeat(300000));
    await writeFile(join(root, 'node_modules', 'hidden.txt'), 'AiDiy');
    await writeFile(join(root, 'backup', 'hidden.txt'), 'AiDiy');
    const outside = join(temp, 'outside');
    await mkdir(outside); await writeFile(join(outside, 'hidden.txt'), 'AiDiy');
    await symlink(outside, join(root, 'linked'), process.platform === 'win32' ? 'junction' : 'dir');
    const result = await grepFiles(root, 'aidiy');
    assert.deepEqual(result.paths.sort(), ['data.csv', 'src/日本語.txt']);
    assert.equal(result.truncated, false);
    assert.deepEqual((await grepFiles(root, 'aidiy', { caseSensitive: true })).paths, []);
    assert.deepEqual((await grepFiles(root, '(a+b)')).paths, ['src/日本語.txt']);
    assert.deepEqual((await grepFiles(root, '日本語')).paths, ['src/日本語.txt']);
    await assert.rejects(grepFiles(root, ''));
    assert.deepEqual((await grepFiles(root, 'AiDiy', { signal: AbortSignal.abort() })).paths, []);
  } finally { await rm(temp, { recursive: true, force: true }); }
});

test('grep API は利用開始前を拒否し、オフライン開始後だけ検索できる', async () => {
  const temp = await mkdtemp(join(tmpdir(), 'aidiy-grep-api-'));
  const connection = createCoreConnection(temp);
  const app = await startServer(temp, 0, { connection });
  try {
    await writeFile(join(temp, 'sample.txt'), '検索対象');
    assert.equal((await fetch(app.url + 'api/grep?q=test')).status, 503);
    connection.offline();
    const response = await fetch(app.url + 'api/grep?q=' + encodeURIComponent('検索対象'));
    assert.equal(response.status, 200);
    assert.deepEqual((await response.json()).paths, ['sample.txt']);
    assert.equal((await fetch(app.url + 'api/grep?q=')).status, 400);
    assert.equal((await fetch(app.url + 'api/grep?q=test', { method: 'POST' })).status, 405);
  } finally {
    app.server.closeAllConnections();
    await new Promise(done => app.server.close(done));
    await rm(temp, { recursive: true, force: true });
  }
});

test('grepは日本語・CRLF・UTF-16の行と桁、繰り返し一致、短い抜粋を返す', async t => {
  const root = await mkdtemp(join(tmpdir(), 'aidiy-grep-lines-')); t.after(() => rm(root, { recursive: true, force: true }));
  await writeFile(join(root, '日本語.txt'), '最初\r\n😀日本語 日本語\r\n最後 日本語\n');
  const data = await grepFiles(root, '日本語');
  assert.deepEqual(data.matches.map(({ line, column, length }) => ({ line, column, length })), [
    { line: 2, column: 3, length: 3 }, { line: 2, column: 7, length: 3 }, { line: 3, column: 4, length: 3 },
  ]);
  assert.equal(data.matchCount, 3); assert.equal(data.matchedFiles, 1);
  assert.equal(data.matches[0].snippet, '😀日本語 日本語');
  assert.ok(data.matches.every(match => !match.snippet.includes('\r') && match.mtime > 0 && match.size > 0));
  await writeFile(join(root, 'long.txt'), 'あ'.repeat(400) + '日本語' + 'い'.repeat(400));
  const long = (await grepFiles(root, '日本語')).matches.find(match => match.path === 'long.txt');
  assert.equal(long.column, 401); assert.equal(long.snippetColumn, 321); assert.equal(long.snippetTruncated, true); assert.ok(long.snippet.length <= 240);
});

test('Shift_JISと大文字小文字の長さ変換でも元ファイルの位置を返す', async t => {
  const root = await mkdtemp(join(tmpdir(), 'aidiy-grep-encoding-')); t.after(() => rm(root, { recursive: true, force: true }));
  // Shift_JIS の「日本語」。UTF-8としては不正なので既存のフォールバックを使う。
  await writeFile(join(root, 'sample.bat'), Buffer.from([0x41, 0x0d, 0x0a, 0x93, 0xfa, 0x96, 0x7b, 0x8c, 0xea]));
  const japanese = await grepFiles(root, '日本語');
  assert.equal(japanese.matches[0].line, 2); assert.equal(japanese.matches[0].column, 1); assert.equal(japanese.matches[0].length, 3);
  await writeFile(join(root, 'unicode.txt'), 'İx\nİx');
  assert.deepEqual((await grepFiles(root, 'x')).matches.map(({ line, column }) => [line, column]), [[1, 2], [2, 2]]);
  assert.equal((await grepFiles(root, 'i')).matches[0].length, 1);
});

test('grepの一致・読み取り件数・総バイト・時間・走査の打切りを報告する', async t => {
  const root = await mkdtemp(join(tmpdir(), 'aidiy-grep-caps-')); t.after(() => rm(root, { recursive: true, force: true }));
  for (const name of ['a.txt', 'b.txt', 'c.txt']) await writeFile(join(root, name), 'xx');
  const matches = await grepFiles(root, 'x', { limits: { maxMatches: 3 } });
  assert.equal(matches.matchCount, 3); assert.equal(matches.truncationReason, 'matches');
  const files = await grepFiles(root, 'x', { limits: { maxFiles: 1 } });
  assert.equal(files.scannedFiles, 1); assert.equal(files.checked, 1); assert.equal(files.truncationReason, 'files'); assert.equal(files.matches.length, 2);
  const bytes = await grepFiles(root, 'x', { limits: { maxBytes: 3 } });
  assert.equal(bytes.bytes, 2); assert.equal(bytes.truncationReason, 'bytes'); assert.equal(bytes.matches.length, 2);
  const time = await grepFiles(root, 'x', { limits: { timeMs: 0 } });
  assert.equal(time.truncationReason, 'time'); assert.equal(time.checked, 0);
  const scan = await grepFiles(root, 'x', { limits: { scan: { maxEntries: 1 } } });
  assert.equal(scan.truncationReason, 'entries'); assert.equal(scan.scan.entries, 1);
  const cancelled = await grepFiles(root, 'x', { signal: AbortSignal.abort() });
  assert.equal(cancelled.truncationReason, 'cancelled'); assert.deepEqual(cancelled.paths, []);
});

test('共有スナップショットを使い、更新内容を再読込し削除済み候補を安全に除外する', async t => {
  const { createScanPool } = await import('../file-scan.mjs');
  const root = await mkdtemp(join(tmpdir(), 'aidiy-grep-stale-')); t.after(() => rm(root, { recursive: true, force: true }));
  await writeFile(join(root, 'changed.txt'), 'old'); await writeFile(join(root, 'deleted.txt'), 'old');
  const pool = createScanPool(root); t.after(() => pool.close());
  const snapshot = await pool.get();
  await writeFile(join(root, 'changed.txt'), 'new\n新しい内容'); await rm(join(root, 'deleted.txt'));
  const next = await grepFiles(root, '新しい', { pool });
  assert.deepEqual(next.paths, ['changed.txt']); assert.equal(next.matches[0].line, 2); assert.equal(next.skipped, 1);
  assert.equal(next.scan.scannedAt, snapshot.scannedAt);
  await writeFile(join(root, 'new.txt'), '新しい');
  assert.deepEqual((await grepFiles(root, '新しい', { pool, fresh: true })).paths, ['changed.txt', 'new.txt']);
});
