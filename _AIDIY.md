# AiDiy

## 本書の役割

このファイルは、AI エージェントが AiDiy の入口だけを短く把握するための最小メモです。
ここに手順、詳細仕様、個別の実装メモを追記しないでください。

詳しい情報は [AGENTS.md](./AGENTS.md) を参照してください。

## システム概要

AiDiy は、日本語を第一言語とするフルスタック業務システム開発テンプレートです。

- Backend: FastAPI + SQLAlchemy + SQLite。
- Command Hermes: `aidiy_hermes` コード支援 CLI（常駐なし）。
- Backend MCP: 16 個の MCP サーバー（Chrome / Desktop / SQLite / PostgreSQL / Logs / Code Check / Backup / Image Generation / Movie Generation / Speech-to-Text / Text-to-Speech / OBS Studio Control / FFmpeg Control / Notification Sounds / Code Agents / Chat LLM）。
- Backend Local: OpenAI 互換の Gemma ローカル推論サーバー（ポート 8094）。
- Backend Task: AIタスク実行 + 定期タスクサーバー（ポート 8093）。
- Frontend Web: Vue 3 + Vite + TypeScript。
- Frontend Avatar: Electron / Web デュアルモードの AI Avatar UI。
- AI コア: チャット、音声、画像、ファイル、code1〜code6 のコード支援パネル。
- AIタスク: 要求を AI が明細へ分解し Code CLI で自動実行する画面と実行基盤。

業務システム機能追加の手順は `docs/` を参照してください。
コアシステム機能調整の手順は [`.aidiy/knowledge/_index.md`](./.aidiy/knowledge/_index.md) を参照してください。

詳細な概要、サブシステム構成、文書インデックスは [AGENTS.md](./AGENTS.md) を参照してください。
