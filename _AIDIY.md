# AiDiy について

## 本書について

このファイルは、AiDiy の概要だけを短く把握するためのメモです。

---

## プロジェクト概要

**AiDiy** は、**日本語を第一言語とするフルスタック業務システム開発テンプレート** です。

### 特徴

- 日本語ネイティブ設計
  - テーブル名、カラム名、API、JSON キー、Vue ファイル名が日本語中心
- フルスタック構成
  - バックエンド: FastAPI + SQLAlchemy + SQLite
  - フロントエンド Web: Vue 3 + Vite + TypeScript + Pinia
  - フロントエンド Avatar: Vue 3 + Vite + TypeScript + Electron
- マルチバックエンド
  - `core_main.py` : `8091`
  - `apps_main.py` : `8092`
  - `mcp_main.py` : `8095`（Chrome DevTools MCP — AIブラウザ自動操作）
- 実用サンプルを同梱
  - C系, M系, T系, V系, S系, A系, X系
- AI 統合
  - Claude / OpenAI / Gemini
  - WebSocket ベースの AI コア
  - 音声、画像、コード支援パネル
- マルチ Code CLI 対応
  - `claude_sdk`, `claude_cli`, `copilot_cli`, `codex_cli`, `gemini_cli`, `hermes_cli`
  - 複数のコードエージェントを同時並走（code1〜code4 パネル）
- AIブラウザ自動操作
  - `backend_mcp/mcp_main.py`（port 8095）が Chrome DevTools MCP を SSE で提供
  - `backend_server/_config/AiDiy_mcp.json` で MCP サーバーを定義
  - Claude Agent SDK（claude_sdk）が MCP 経由でブラウザ操作可能
- 自己改善機構
  - コードエージェントが修正完了後、`.aidiy/` フォルダへ知見を自動整理
  - 使うほど類似修正の精度が上がる「育つシステム」

---

## 実装メモ

- 起動は `python _start.py`
  - 起動時に backend(mcp) / backend(core,apps) / web / avatar を対話形式で選択
- Web フロント: `http://localhost:8090`
- MCP SSE: `http://localhost:8095/aidiy_chrome_devtools/sse`
- Avatar Web モード: `http://localhost:8099`
- SQLite DB: `backend_server/_data/AiDiy/database.db`
- 初期ログイン: `admin / ********`
- CRUD は原則 POST
- M商品構成 / T生産 は明細型パターン
- `frontend_avatar` は Electron では `localStorage`、Web では `sessionStorage`
- AI 名の規約
  - `CHAT_AI_NAME`: `*_chat`
  - `LIVE_AI_NAME`: `*_live`
  - `CODE_AI*_NAME`: `*_sdk` または `*_cli`

---

## 詳細

詳細は [AGENTS.md](./AGENTS.md) を参照してください。
