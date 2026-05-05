# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 本書の役割

このファイルは Claude Code が AiDiy を操作するための最小エントリです。
詳細な実装方針、アーキテクチャ、手順は [AGENTS.md](./AGENTS.md) と `.aidiy/knowledge/_index.md` を参照してください。

## システム概要

日本語識別子を前提としたフルスタック業務システム開発テンプレート。

- **Backend**: FastAPI + SQLAlchemy + SQLite（2 サーバー構成）
- **Backend Hermes**: `aidiy_hermes` コード支援 CLI（常駐なし）
- **Backend MCP**: 8 つの MCP サーバー（Chrome / Desktop / SQLite / PostgreSQL / Logs / Code Check / Backup Check / Backup Save）
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
cd backend_mcp && .venv/Scripts/python -m uvicorn mcp_main:app --reload --host 0.0.0.0 --port 8095

# Frontend Web — ポート 8090
cd frontend_web && npm run dev

# Frontend Avatar (Electron + Web) — ポート 8099
cd frontend_avatar && npm run dev

# Hermes CLI
cd backend_hermes && .venv/Scripts/python cli_main.py
```

### 型チェック・ビルド

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
cd backend_server && uv sync
cd backend_mcp && uv sync
cd backend_hermes && uv sync

# Frontend
cd frontend_web && npm install
cd frontend_avatar && npm install
```

### クリーンアップ

```bash
python _cleanup.py          # 対話形式: .venv / node_modules / DB / キャッシュ削除
```

### 自動テスト

自動テストは未整備です。手動テストで確認します:
- API: http://localhost:8091/docs / http://localhost:8092/docs
- Web UI: http://localhost:8090
- Avatar Web: http://localhost:8099

## ポート一覧

| ポート | サービス |
|--------|----------|
| 8090 | Frontend Web (Vite) |
| 8091 | Backend Core (`core_main.py`) |
| 8092 | Backend Apps (`apps_main.py`) |
| 8095 | Backend MCP (`mcp_main.py`) |
| 8099 | Frontend Avatar (Vite) |

## 主要 URL

- Web UI: http://localhost:8090
- Core API Swagger: http://localhost:8091/docs
- Apps API Swagger: http://localhost:8092/docs
- AI 画面: http://localhost:8090/AiDiy

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

## 初期ログイン情報

- `admin / ********`
- `leader / secret`
- `user / user`
- `guest / guest`
- `other / other`

## 参照すべきドキュメント

- [AGENTS.md](./AGENTS.md) — 全体アーキテクチャ・設計方針
- [`.aidiy/knowledge/_index.md`](./.aidiy/knowledge/_index.md) — 全 HowTo の入口
- `backend_server/AGENTS.md` — Backend 実装パターン
- `frontend_web/AGENTS.md` — Web UI 実装パターン
- `docs/` — 開発ガイド (HTML)
