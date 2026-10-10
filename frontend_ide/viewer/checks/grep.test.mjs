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
