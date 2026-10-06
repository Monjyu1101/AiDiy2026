import { createRequire } from 'node:module';

// frontend_vscode は CommonJS。日本語名の export を ESM の静的解析に依存させず読む。
// tsx の require フックでソースを直接共有し、VSIX / out の生成を不要にする。
const require = createRequire(import.meta.url);
export const { 起動解決, 会話引数, CLI実行 } = require('../../frontend_vscode/src/runner.ts') as typeof import('../../frontend_vscode/src/runner');
export const { コード要求実行 } = require('../../frontend_vscode/src/protocol.ts') as typeof import('../../frontend_vscode/src/protocol');
export const { LiveConnection, 入力レート, 音声入力, 音声操作 } = require('../../frontend_vscode/aidiy_live/src/protocol.ts') as typeof import('../../frontend_vscode/aidiy_live/src/protocol');
export const { ライブ選択エラー } = require('../../frontend_vscode/aidiy_live/src/model-catalog.ts') as typeof import('../../frontend_vscode/aidiy_live/src/model-catalog');
export const { LIVE_KEYS, ライブモデル読込, ライブモデル保存, コードモデル読込, コードモデル保存 } = require('../../frontend_vscode/src/model-preferences.ts') as typeof import('../../frontend_vscode/src/model-preferences');
