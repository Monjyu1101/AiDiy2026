// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import test from 'node:test';
import assert from 'node:assert/strict';
import { access, readFile } from 'node:fs/promises';
const root = new URL('../', import.meta.url);

test('モジュール配置: 公開入口を維持し、内部処理は担当フォルダから読み込む', async () => {
  for (const entry of ['launch.mjs', 'server.mjs', 'desktop.cjs', '_setup.py', '_cleanup.py',
    'aidiy_term/launch.mjs', 'aidiy_code/launch.mjs', 'aidiy_live/launch.mjs', 'aidiy_ide/launch.mjs']) {
    await access(new URL(entry, root));
  }
  const modules = {
    'デスクトップ/desktop-process.mjs': 'spawnDesktop',
    'デスクトップ/project-profile.cjs': 'projectIdentity',
    'ファイル機能/ai-search.mjs': 'createAISearch',
    'ファイル機能/file-analysis.mjs': 'createFileAnalysis',
    'ファイル機能/file-history.mjs': 'createFileHistory',
    'aidiy_term/terminal.mjs': 'startTerminal',
    'viewer/markdown-preview.mjs': 'renderMarkdownDocument',
  };
  for (const [path, name] of Object.entries(modules)) {
    const module = await import(new URL(path, root));
    assert.equal(typeof (module[name] ?? module.default?.[name]), 'function', path);
    await assert.rejects(access(new URL(path.split('/').at(-1), root)), { code: 'ENOENT' });
  }
});

test('モジュール配置: Electron preload・端末worker・PowerShell補完を配置先から解決する', async () => {
  const desktop = await readFile(new URL('desktop.cjs', root), 'utf8');
  assert.match(desktop, /preload:join\(__dirname,'デスクトップ\/preload\.cjs'\)/);
  for (const path of ['デスクトップ/preload.cjs', 'aidiy_term/terminal-worker.mjs', 'aidiy_term/powershell-init.ps1']) {
    await access(new URL(path, root));
  }
  const terminal = await readFile(new URL('aidiy_term/terminal.mjs', root), 'utf8');
  assert.match(terminal, /new URL\('\.\/powershell-init\.ps1', import\.meta\.url\)/);
  const worker = await readFile(new URL('aidiy_term/terminal-process.mjs', root), 'utf8');
  assert.match(worker, /new URL\('\.\/terminal-worker\.mjs', import\.meta\.url\)/);
});
