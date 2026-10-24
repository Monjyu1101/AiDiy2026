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

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { cp, mkdtemp, readFile, writeFile, symlink, rm } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('..', import.meta.url));

test('依存更新後は実ビルドで manifest を揃え、ソースと配布物の改変検出を保つ', async () => {
  const folder = await mkdtemp(join(tmpdir(), 'aidiy-discord-manifest-'));
  try {
    for (const entry of ['package.json', 'package-lock.json', 'scripts', 'panel']) {
      await cp(join(root, entry), join(folder, entry), { recursive: true });
    }
    await symlink(join(root, 'node_modules'), join(folder, 'node_modules'), process.platform === 'win32' ? 'junction' : 'dir');
    const run = (script: string) => spawnSync(process.execPath, [join(folder, 'scripts', script)], { cwd: folder, encoding: 'utf8' });
    assert.equal(run('verify-panel.mjs').status, 0);
    const lockPath = join(folder, 'package-lock.json');
    const lock = JSON.parse(await readFile(lockPath, 'utf8'));
    lock.packages['node_modules/electron'].version += '-setup-fixture';
    await writeFile(lockPath, JSON.stringify(lock, null, 2) + '\n');
    assert.equal(run('verify-panel.mjs').status, 1, 'lock の更新だけでは古い manifest を承認しない');
    const built = run('build-panel.mjs');
    assert.equal(built.status, 0, built.stderr);
    assert.equal(run('verify-panel.mjs').status, 0);
    // 配布物と元ソースのどちらの変更も、再ビルド前には拒否する。
    for (const entry of ['panel/view.js', 'panel/画面/接続パネル.vue']) {
      const path = join(folder, entry);
      const original = await readFile(path, 'utf8');
      await writeFile(path, original + '\n// changed fixture\n');
      assert.equal(run('verify-panel.mjs').status, 1, entry);
      await writeFile(path, original);
      assert.equal(run('verify-panel.mjs').status, 0);
    }
  } finally {
    await rm(folder, { recursive: true, force: true });
  }
});
