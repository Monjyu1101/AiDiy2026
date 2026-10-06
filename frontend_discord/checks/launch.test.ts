import { test } from 'node:test';
import assert from 'node:assert/strict';
import { cpSync, existsSync, mkdirSync, mkdtempSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { プロジェクトルート } from '../src/config';
import { defaults } from './helpers';

test('単独起動・自動接続は無効なトークンを Electron 起動前に検出し、終了コード1で止まる', () => {
  // 実際のキーには触れず、起動コードと設定検証を一時作業コピーで実行する。
  // Electron は配置しないため、検証を飛ばす退行もエラーメッセージの違いで検出できる。
  const root = mkdtempSync(join(tmpdir(), 'aidiy-discord-preflight-'));
  const source = join(プロジェクトルート, 'frontend_discord'), frontend = join(root, 'frontend_discord');
  try {
    mkdirSync(join(frontend, 'panel'), { recursive: true });
    mkdirSync(join(root, '_config'));
    cpSync(join(source, 'src'), join(frontend, 'src'), { recursive: true });
    cpSync(join(source, 'panel/launch.mjs'), join(frontend, 'panel/launch.mjs'));
    writeFileSync(join(frontend, 'package.json'), '{"type":"module"}');
    for (const name of ['tsx', 'discord.js', '@discordjs/voice', 'opusscript', 'ws']) {
      const target = join(frontend, 'node_modules', name);
      mkdirSync(dirname(target), { recursive: true });
      symlinkSync(join(source, 'node_modules', name), target, 'junction');
    }
    symlinkSync(join(プロジェクトルート, 'frontend_vscode'), join(root, 'frontend_vscode'), 'junction');
    for (const args of [[], ['--connect'], ['--wait', '--connect']]) {
      for (const token of ['', '<', '<secret-placeholder>', '>']) {
        writeFileSync(join(root, '_config/AiDiy_key.json'), JSON.stringify({ ...defaults, DISCORD_BOT_TOKEN: token }));
        const result = spawnSync(process.execPath, [join(frontend, 'panel/launch.mjs'), ...args], { cwd: tmpdir(), encoding: 'utf8', timeout: 15_000, windowsHide: true });
        assert.equal(result.status, 1, result.stderr);
        assert.match(result.stderr, /DISCORD_BOT_TOKEN/);
        assert.doesNotMatch(result.stderr, /secret-placeholder|Electron|パネルの準備/);
        assert.equal(existsSync(join(frontend, 'out')), false, 'Electron 起動用のログも作らない');
      }
    }
  } finally { rmSync(root, { recursive: true, force: true }); }
});
