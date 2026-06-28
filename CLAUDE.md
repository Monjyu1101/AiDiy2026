# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 本書の役割

このファイルは Claude Code が AiDiy を操作するための最小エントリです。
詳細な実装方針、アーキテクチャ、手順は [AGENTS.md](./AGENTS.md) と `.aidiy/knowledge/_index.md` を参照してください。

## システム概要

日本語識別子を前提としたフルスタック業務システム開発テンプレート。

- **Backend**: FastAPI + SQLAlchemy + SQLite（Python 3.13 以上、uv 管理、2 サーバー構成）
- **Backend Hermes**: `aidiy_hermes` コード支援 CLI（**常駐なし**、`_start.py` の起動対象外）
- **Backend MCP**: 15 個の MCP サーバー（Chrome, Desktop, SQLite, PostgreSQL, Logs, Code Check, Backup, Image Generation, Movie Generation, Speech-to-Text, Text-to-Speech, OBS Studio Control, FFmpeg Control, Code Agents, Chat LLM）— **SSE Transport** / **Streamable HTTP Transport** / **stdio gateway**（`mcp_stdio.py`）の 3 トランスポートを同一ポートで提供。ツール一覧は `GET http://localhost:8095/{mcp_name}/list`、Python からは `requests.post("http://localhost:8095/{mcp_name}/{method}")` で直接利用可能。加えて OpenAI / Ollama 互換の標準チャットインターフェース `POST http://localhost:8095/aidiy_chat_completions/v1/chat/completions`（HTTP のみ）を提供。
- **Backend Local**: `backend_local` ローカル LLM サーバー（ポート 8096）。HuggingFace の **Gemma** を `transformers` + `torch` でローカル推論し、**OpenAI 互換**の Chat Completions API（`POST http://localhost:8096/v1/chat/completions`、`stream` / `tools` 対応）として提供。モデルは `temp/models/<safe_name>` に配置し遅延ロード。設定は `backend_server/_config/AiDiy_key.json`（環境変数は使わない）。
- **Frontend Web**: Vue 3 + Vite + TypeScript（qTubler, Pinia, Vue Router）
- **Frontend Avatar**: Electron/Web デュアルモード AI Avatar（Three.js, VRM）

## 主要コマンド

### セットアップ（初回のみ）

```bash
python _setup.py            # 対話形式: .venv / node_modules / MCP 設定
```

### 起動

```bash
python _start.py            # 対話形式: 起動するサービスを選択
```

個別起動:

```bash
# Backend Core (C系, A系, 認証, AIコア) — ポート 8091
cd backend_server && .venv/Scripts/python -m uvicorn core_main:app --reload --host 0.0.0.0 --port 8091

# Backend Apps (M系, T系, V系, S系) — ポート 8092
cd backend_server && .venv/Scripts/python -m uvicorn apps_main:app --reload --host 0.0.0.0 --port 8092

# Backend MCP — ポート 8095
cd backend_tools && .venv/Scripts/python -m uvicorn tools_main:app --reload --host 0.0.0.0 --port 8095

# Backend Local (ローカル LLM, Gemma) — ポート 8096
cd backend_local && .venv/Scripts/python -m uvicorn local_main:app --reload --host 0.0.0.0 --port 8096

# Frontend Web — ポート 8090
cd frontend_web && npm run dev

# Frontend Avatar (Electron + Web) — ポート 8099
cd frontend_avatar && npm run dev

# Hermes CLI（常駐しない、必要時に手動起動）
cd backend_hermes && .venv/Scripts/python cli_main.py
```

### 型チェック・ビルド

`npm run build` は原則として日常的な確認では実行しません。配布物作成、ビルド成果物確認、利用者明示依頼など、実行理由が明確な場合だけ使ってください。

```bash
# Frontend Web
cd frontend_web && npm run type-check    # vue-tsc --noEmit
cd frontend_web && npm run build         # type-check + vite build

# Frontend Avatar
cd frontend_avatar && npm run type-check # vue-tsc + tsc (electron)
cd frontend_avatar && npm run build      # renderer + electron build
```

### 依存関係インストール

```bash
# Backend
cd backend_server && uv sync --upgrade
cd backend_tools && uv sync --upgrade
cd backend_hermes && uv sync --upgrade
cd backend_local && uv sync --upgrade

# Frontend
cd frontend_web && npm install
cd frontend_avatar && npm install
```

### クリーンアップ

```bash
python _cleanup.py          # 対話形式: .venv / node_modules / DB / キャッシュ削除
```

### コードチェック（MCP）

```bash
# backend_tools 起動後、Python 構文 / ruff / TypeScript 型チェックを MCP 経由で実行
# GET でツール一覧確認、POST でツール実行
curl http://localhost:8095/aidiy_code_check/list
curl -X POST http://localhost:8095/aidiy_code_check/check \
  -H "Content-Type: application/json" \
  -d '{"path": "backend_server/AIコア/AIコード_cli.py"}'
```

### 自動テスト

`aidiy_chrome_devtools`（MCP Chrome Tools）を使って E2E 自動テストを実行します。

```bash
# backend_tools が起動している状態で Chrome 操作 MCP ツールを使用
curl -X POST http://localhost:8095/aidiy_chrome_devtools/navigate \
  -H "Content-Type: application/json" \
  -d '{"url": "http://localhost:8090"}'
```

手動確認が必要な場合:
- API: http://localhost:8091/docs / http://localhost:8092/docs
- Web UI: http://localhost:8090
- Avatar Web: http://localhost:8099

## ポート一覧

| ポート | サービス |
|--------|----------|
| 8090 | Frontend Web (Vite) |
| 8091 | Backend Core (`core_main.py`) |
| 8092 | Backend Apps (`apps_main.py`) |
| 8095 | Backend MCP (`tools_main.py`) |
| 8096 | Backend Local (`local_main.py`) — OpenAI 互換 Gemma サーバー |
| 8099 | Frontend Avatar (Vite) |

**注意**: フロントエンドのポートを変える場合は `core_main.py` / `apps_main.py` の CORS 許可リストも合わせて更新してください。

## 主要 URL

- Web UI: http://localhost:8090
- Core API Swagger: http://localhost:8091/docs
- Apps API Swagger: http://localhost:8092/docs
- AI 画面: http://localhost:8090/AiDiy

## データベース

- DB ファイル: `backend_server/_data/AiDiy/database.db`
- Alembic は使わない。スキーマ変更の手順は `.aidiy/knowledge/backend_server,スキーマ変更手順.md` を参照。
- `create_all()` は新規テーブル作成には有効だが、**既存テーブルのカラム追加・削除・型変更には効かない**。
- 採番は `C採番` テーブルで管理（AUTOINCREMENT 非依存）。
- 全テーブルに監査フィールド必須（登録/更新: 日時、利用者ID、利用者名、端末ID）。

## テーブル命名規則

| 接頭辞 | 種別 | 担当サーバー |
|--------|------|-------------|
| C | Core / Common (`C権限`, `C利用者`, `C採番`) | core_main |
| A | AI / Advanced (`A会話履歴`, `AIコア`) | core_main |
| M | Master (`M商品`, `M取引先`) | apps_main |
| T | Transaction (`T配車`, `T生産`) | apps_main |
| V | View endpoint (生 SQL JOIN) | apps_main |
| S | Scheduler / Special | apps_main |
| X | Experimental (`Xテトリス`, `X世界の絶景`) | frontend_web |

## 日本語ファースト設計

全レイヤーで日本語識別子を使います:

| レイヤー | 例 |
|----------|-----|
| テーブル名 | `C権限`、`T配車`、`M商品構成` |
| カラム名 | `利用者ID`、`配車日付`、`商品名` |
| API パス | `/core/利用者/一覧`、`/apps/配車/検索` |
| JSON キー | `{"利用者名": "admin"}` |
| ファイル名 | `C利用者一覧.vue`、`T配車登録.vue` |
| Router path | `/C管理/C利用者/一覧` |
| Python 変数 | `利用者名`、`配車日付`、`商品名` |

システム用語（`request`、`query`、`items`、`total`、`limit`）や英字ライブラリ名はそのまま使用します。

## Backend 実装パターン（4層構造）

新規 M/T/C 機能は以下の 4 層で実装します:

| 層 | 配置先 | 役割 |
|----|--------|------|
| Model | `core_models/` or `apps_models/` | SQLAlchemy モデル（`C利用者Model`、`T配車Model`） |
| Schema | `core_schema/` or `apps_schema/` | Pydantic リクエスト/レスポンススキーマ |
| CRUD | `core_crud/` or `apps_crud/` | DB アクセスロジック |
| Router | `core_router/` or `apps_router/` | FastAPI エンドポイント + ルーティング |

- CRUD エンドポイントは POST 統一
- レスポンス形式: `{"status": "OK"/"NG", "message": "...", "data": {...}}`
- 認証は `deps.get_現在利用者` で dependency injection
- V系は Router 内の生 SQL JOIN（Model/CRUD 層は作らない）

### AI 名命名規約

| 設定キー | サフィックス規約 |
|----------|----------------|
| `CHAT_AI_NAME` | `_chat` で終わる |
| `LIVE_AI_NAME` | `_live` で終わる |
| `CODE_AI1_NAME`〜`CODE_AI6_NAME` | `_sdk` または `_cli`（例外: `aidiy_hermes`） |

比較は完全一致で行い、前方一致を使わない。MCP 設定は `backend_server/_config/AiDiy_mcp.json`。

## Frontend Web 実装パターン

### コンポーネント配置

| カテゴリ | 配置先 |
|----------|--------|
| C系管理画面 | `components/C管理/` |
| M系マスタ画面 | `components/Mマスタ/` |
| T系トランザクション画面 | `components/Tトラン/` |
| V系一覧画面 | `components/Vビュー/` |
| S系スケジュール画面 | `components/Sスケジュール/` |
| X系画面 | `components/Xその他/` |

### Vue テンプレートの制約

- `<template>` 内のコンポーネントタグは **ASCII のみ**。
- 日本語コンポーネントは `import` して `<component :is="コンポーネント名">` で扱う。
- UI framework / CSS framework は使わず、既存 CSS と共有コンポーネントへ合わせる。
- TypeScript strict mode は無効設定だが、既存型定義を使い不要な `any` の拡大は避ける。

### Router

| ファイル | 対象 |
|----------|------|
| `router/coreRouter.ts` | C系 / A系 |
| `router/appsRouter.ts` | M系 / T系 / V系 / S系 |
| `router/index.ts` | base route、ログイン |

### Vite Proxy

`/core/*` → `http://127.0.0.1:8091`、`/apps/*` → `http://127.0.0.1:8092` にプロキシ。WebSocket 対応済み。

### UI 補足

- qTubler（独自テーブル: `_share/qTublerFrame.vue`）が主要グリッド
- Vue Router + Pinia 使用
- 401 は Axios interceptor でログアウト処理へ自動誘導

## Frontend 共通（frontend_web / frontend_avatar）

両プロジェクトは以下の共通基盤を持ちます。詳細は `.aidiy/knowledge/_index.md` の「Frontend 共通」セクションを参照してください。

| 共通項目 | 説明 |
|----------|------|
| Axios API クライアント | Bearer token 付与、401 ハンドリング（認証延長ロジックは差異あり） |
| WebSocket クライアント (`AIWebSocket`) | 再接続ポリシー、メッセージディスパッチ、`createWebSocketUrl()` |
| Monaco Editor 設定 | Worker 構成、拡張子→言語マッピング (`モナコ言語推定()`) |
| qAlert / qConfirm / qColorPicker | シングルトンダイアログパターン |
| Vite proxy | `/core` → 8091、`/apps` → 8092（共に WebSocket 対応） |

**主要な差異:**
- **状態管理**: web は Pinia + Vue Router、avatar は BroadcastChannel + コンポーネント状態
- **認証 storage**: web は `localStorage`、avatar は `window.desktopApi ? localStorage : sessionStorage`
- **Electron 判定**: `!!window.desktopApi` が `true` なら Electron モード
- **tsconfig**: web は strict mode 無効、avatar は strict mode 有効
- **Electron**: avatar のみ（IPC、BrowserWindow、preload）
- **3D/VRM**: avatar のみ（Three.js、@pixiv/three-vrm）

## 初期ログイン情報

- `admin / ********`
- `leader / secret`
- `user / user`
- `guest / guest`
- `other / other`

## 参照すべきドキュメント

- [AGENTS.md](./AGENTS.md) — 全体アーキテクチャ・設計方針
- [`.aidiy/knowledge/_index.md`](./.aidiy/knowledge/_index.md) — 全 HowTo の入口（実装手順は必ずここを確認）
- `backend_server/AGENTS.md` — Backend 実装パターン
- `frontend_web/AGENTS.md` — Web UI 実装パターン
- `frontend_avatar/AGENTS.md` — Avatar / Electron 実装パターン
- `backend_tools/AGENTS.md` — MCP 実装パターン
- `backend_hermes/AGENTS.md` — Hermes CLI 実装パターン
- `backend_local/AGENTS.md` — ローカル LLM（OpenAI 互換 Gemma）実装パターン
- `docs/` — 開発ガイド (HTML)

### frontend 共通ナレッジ（新規）

- [共通APIクライアントパターン](.aidiy/knowledge/frontend_web,frontend_avatar,共通APIクライアントパターン.md) — Axios client / token / 401
- [共通WebSocketクライアント](.aidiy/knowledge/frontend_web,frontend_avatar,共通WebSocketクライアント.md) — AIWebSocket / 再接続 / パケット
- [共通ユーティリティ](.aidiy/knowledge/frontend_web,frontend_avatar,共通ユーティリティ.md) — Monaco / qAlert / 同期ルール
- [プロジェクト設定と依存関係](.aidiy/knowledge/frontend_web,frontend_avatar,プロジェクト設定と依存関係.md) — package.json / tsconfig / vite.config
