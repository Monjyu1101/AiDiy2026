import { existsSync, readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { 起動解決, 会話引数, type 起動設定 } from '../../src/runner';
import { コード要求実行, type コードパケット } from '../../src/protocol';

export const オフラインモデル保存先 = (onlineFile: string) => onlineFile.replace(/\.json$/i, '') + '_offline.json';

export function Hermes既定モデル(...folders: string[]): string {
  const visited = new Set<string>();
  for (const folder of folders) {
    let current = resolve(folder);
    while (!visited.has(current)) {
      visited.add(current);
      const file = join(current, '_config', 'AiDiy_key.json');
      if (existsSync(file)) {
        let settings;
        try { settings = JSON.parse(readFileSync(file, 'utf8').replace(/^\uFEFF/, '')); }
        catch { throw new Error('共通設定 AiDiy_key.json を読み込めません。'); }
        const model = settings.CODE_AIDIY_HERMES_MODEL;
        return typeof model === 'string' && model.trim() ? model.trim() : 'auto';
      }
      const parent = dirname(current);
      if (parent === current) break;
      current = parent;
    }
  }
  return 'auto';
}

// AIコアもモデル情報APIも使わず、ローカルのHermesランチャーから候補を読む。
export function オフラインモデル候補(root: string) {
  const models = new Set<string>(['auto']);
  try {
    const bat = readFileSync(join(root, '..', 'scripts', 'cli_bat', '_hermes_cli.bat'), 'utf8');
    for (const match of bat.matchAll(/set "MODEL=([^"%\r\n]+)"/g)) models.add(match[1].includes('/') ? match[1] : `openai_oauth/${match[1]}`);
  } catch {
    // ランチャーを同梱しない配置でも、同じ固定候補を使う。
    for (const model of ['codex_cli/auto', 'copilot_cli/auto', 'openai_oauth/gpt-6-astra', 'openai_oauth/gpt-6.1-sol', 'openai_oauth/gpt-5.6-terra', 'openai_oauth/gpt-6-luna']) models.add(model);
  }
  return [...models].map(id => ({ id, label: id }));
}

export function オフライン実行(root: string, project: string, model: string, text: string,
  session: string | undefined, receive: (packet: コードパケット) => void,
  launch?: 起動設定) {
  // 設定済みのaidiy_hermesを優先し、未配置なら同梱のcommand_hermesを使う。
  if (!launch) {
    try { launch = 起動解決('aidiy_hermes', '', project); }
    catch { launch = 起動解決(join(root, '..', 'command_hermes', 'cli_main.py')); }
  }
  const cli = /^(codex_cli|copilot_cli)\/(.+)$/.exec(model);
  const args = cli ? 会話引数(cli[1].replace('_', '-'), cli[2], 999, session) : 会話引数('', model, 999, session);
  return コード要求実行({ セッションID: session || '', チャンネル: 'code1',
    メッセージ識別: 'input_text', メッセージ内容: text }, {
    起動: launch, 作業フォルダ: project, 引数: args, 制限時間: 1800000,
  }, receive, session);
}
