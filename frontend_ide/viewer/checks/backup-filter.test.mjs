// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, rm } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { scanTree } from '../server.mjs';

test('バックアップフィルターは_AIDIYのCode / IDE記録だけを除外し、knowledgeと同名ソースを残す', async t => {
  const root = await mkdtemp(join(tmpdir(), 'aidiy-backup-filter-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const excluded = ['_AIDIY/aidiy_code/histories/session.json', '_AIDIY/aidiy_ide/file_searches/search.json', 'nested/_AIDIY/aidiy_ide/file_analyses/analysis.json'];
  const included = ['_AIDIY/knowledge/example.md', 'frontend_ide/aidiy_code/source.py', '_AIDIY/aidiy_ide_extra/keep.md'];
  for (const path of [...excluded, ...included]) {
    const parts = path.split('/');
    await mkdir(join(root, ...parts.slice(0, -1)), { recursive: true });
    await writeFile(join(root, ...parts), '検証');
  }
  function paths(node, prefix = '') {
    return [...node.f.map(([name]) => prefix + name), ...node.d.flatMap(child => paths(child, `${prefix}${child.n}/`))];
  }
  const filtered = await scanTree(root, { filter: 'backup' });
  assert.equal(filtered.files, included.length);
  assert.deepEqual(paths(filtered.tree).sort(), included.sort());
  assert.deepEqual(filtered.tree.d.find(node => node.n === '_AIDIY').d.map(node => node.n).sort(), ['aidiy_ide_extra', 'knowledge']);
  assert.deepEqual(paths((await scanTree(root)).tree).sort(), [...excluded, ...included].sort());
  for (const folder of ['_AIDIY/aidiy_code', '_AIDIY/aidiy_ide']) assert.equal((await scanTree(join(root, folder), { filter: 'backup' })).files, 0);
});
