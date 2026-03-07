# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **詳細ドキュメント方針**: CLAUDE.md はクイックリファレンスのみ。実装詳細・追加手順・アーキテクチャ詳細は以下を参照。
> - [AGENTS.md](./AGENTS.md) — プロジェクト全体方針・共通問題
> - [backend_server/AGENTS.md](./backend_server/AGENTS.md) — バックエンド実装詳細
> - [frontend_server/AGENTS.md](./frontend_server/AGENTS.md) — フロントエンド実装詳細

---

## Critical Constraints (MUST READ)

**Japanese-First Implementation:**
- Table names, column names, API endpoints, JSON keys, Vue components are ALL in Japanese
- System/framework terms remain English: `request`, `router`, `items`, `total`
- All files MUST be UTF-8 encoded

**Vue Component Tag Constraint:**
- Japanese component tags are INVALID in HTML: `<C利用者一覧 />` will NOT work
- Use dynamic component syntax: `<component :is="C利用者一覧" />`
- File names can be Japanese: `C利用者一覧.vue` is OK

**API Design:**
- ALL CRUD operations use POST method (no GET/PUT/DELETE for data)
- Unified response: `{"status": "OK"/"NG", "message": "...", "data": {...}}`
- List responses: `{"items": [], "total": N, "limit": 10000}`

**Dual Server Architecture:**
- core_main.py (port 8091): C系 (Core), A系 (AI) — `/core/*` endpoints
- apps_main.py (port 8092): M系 (Master), T系 (Transaction), V系 (View), S系 (Scheduler) — `/apps/*` endpoints
- BOTH servers must be running

**No Database VIEWs:**
- V系 endpoints use raw SQL queries with JOINs, NOT database VIEW objects

**権限ID is String Type:**
- Compare with `'1'`, `'2'`, NOT integers `1`, `2`

**Passwords are Plaintext:**
- `C利用者.パスワード` is stored as plaintext (bcrypt is installed but not used)
- Do NOT assume hashing when modifying auth code

**AI名 命名規則:**
- `CHAT_AI_NAME` の値は `_chat` サフィックス必須: `gemini_chat` / `freeai_chat` / `openrt_chat`
- `LIVE_AI_NAME` の値は `_live` サフィックス必須: `gemini_live` / `freeai_live` / `openai_live`
- 比較は厳格に完全一致（`startswith` 不使用）

**AIコア WebSocket Packet Format:**
- All packets: `{セッションID, チャンネル, メッセージ識別, メッセージ内容}`
- `全ファイルリスト` は `List[str]`（パスのみ）、mtimes は都度読取
- `files_save` 受信時はバックアップ再実行後にセッションの `全ファイルリスト` を更新（返信なし）
- `コードベース絶対パス取得` は `CODE_BASE_PATH` 未設定時に `"../"` をデフォルトとして返す

**ファイル書き込み改行:**
- 通常ファイル: UTF-8 + LF (`newline="\n"`) — Windows 自動変換を抑止
- `.bat` / `.cmd`: Shift-JIS + CRLF (`newline="\r\n"`)

**No Automated Tests:**
- Test manually via Swagger UI (`:8091/docs`, `:8092/docs`) and browser

**No Alembic Migrations:**
- Schema changes: `ALTER TABLE` in `init.py` for existing DBs, or full DB reset

---

## Quick Commands

```bash
# Start all servers
python _start.py

# Stop all servers
python _stop.py

# Trigger backend reload (Unix: touch)
touch backend_server/temp/reboot_core.txt   # core_main
touch backend_server/temp/reboot_apps.txt   # apps_main

# Backend with hot-reload (dev)
cd backend_server && .venv/Scripts/python.exe -m uvicorn core_main:app --reload --host 0.0.0.0 --port 8091
cd backend_server && .venv/Scripts/python.exe -m uvicorn apps_main:app --reload --host 0.0.0.0 --port 8092

# Frontend only
cd frontend_server && npm run dev

# Type checking / build (frontend)
cd frontend_server && npm run type-check
cd frontend_server && npm run build

# Dependencies
cd backend_server && uv sync
cd frontend_server && npm install

# Database reset
del backend_server\_data\AiDiy\database.db   # then restart servers

# Inspect database
sqlite3 backend_server/_data/AiDiy/database.db ".tables"
sqlite3 backend_server/_data/AiDiy/database.db "PRAGMA table_info(テーブル名);"
```

## Access URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:8090 |
| API Docs (Core) | http://localhost:8091/docs |
| API Docs (Apps) | http://localhost:8092/docs |

**Default login:** `admin` / `********` (also: `leader`/`secret`, `user`/`user`, `guest`/`guest`)
