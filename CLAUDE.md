# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
- core_main.py (port 8091): C系 (Core), A系 (AI) - `/core/*` endpoints
- apps_main.py (port 8092): M系 (Master), T系 (Transaction), V系 (View), S系 (Scheduler) - `/apps/*` endpoints
- BOTH servers must be running

**No Database VIEWs:**
- V系 endpoints use raw SQL queries with JOINs, NOT database VIEW objects

**権限ID is String Type:**
- Compare with `'1'`, `'2'`, NOT integers `1`, `2`

**Passwords are Plaintext:**
- `C利用者.パスワード` is stored as plaintext (bcrypt is installed but not used)
- `authenticate_C利用者` uses direct string comparison
- Do NOT assume hashing when modifying auth code

**AIコア WebSocket Packet Format:**
- All packets: `{セッションID, チャンネル, メッセージ識別, メッセージ内容}`
- `AIコア/AIバックアップ.py` の `全ファイルリスト` は `List[str]`（パスのみ、ファイル個別のmtimeは含まない）
- `コードベース絶対パス取得` は `CODE_BASE_PATH` 未設定時に `"../"` (backend_server の親) をデフォルトとして返す

**No Automated Tests:**
- No pytest or vitest configured
- Test manually via Swagger UI (`:8091/docs`, `:8092/docs`) and browser

**No Alembic Migrations:**
- Schema changes require `ALTER TABLE` in `init.py` for existing DBs (see Schema Changes section)
- Or full DB reset: stop servers → delete `database.db` → restart

---

## Quick Commands

```bash
# Initial setup
python _setup.py

# Start all servers (frontend + backend)
python _start.py

# Stop all servers
python _stop.py

# Backend with hot-reload (dev)
cd backend_server && .venv/Scripts/python.exe -m uvicorn core_main:app --reload --host 0.0.0.0 --port 8091
cd backend_server && .venv/Scripts/python.exe -m uvicorn apps_main:app --reload --host 0.0.0.0 --port 8092

# Frontend only
cd frontend_server && npm run dev

# Type checking (frontend)
cd frontend_server && npm run type-check

# Build (frontend)
cd frontend_server && npm run build

# Backend dependencies
cd backend_server && uv sync

# Frontend dependencies
cd frontend_server && npm install

# Trigger backend reload (without --reload flag) — Windows CMD syntax
echo. > backend_server/temp/reboot_core.txt   # core_main
echo. > backend_server/temp/reboot_apps.txt   # apps_main
# Unix equivalent: touch backend_server/temp/reboot_core.txt

# Database reset (delete and restart servers to recreate)
del backend_server\_data\AiDiy\database.db

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

---

## Architecture Overview

```
AiDiy2026/
├── backend_server/          # FastAPI (Python 3.13) + SQLAlchemy + SQLite
│   ├── core_main.py            # Port 8091 - Core/AI features (C系, A系)
│   ├── apps_main.py            # Port 8092 - App features (M系, T系, V系, S系)
│   ├── core_models/, apps_models/  # SQLAlchemy ORM models
│   ├── core_crud/, apps_crud/      # Database operations
│   ├── core_router/, apps_router/ # API endpoints
│   ├── core_schema.py, apps_schema.py  # Pydantic models
│   ├── database.py         # SQLite config (shared by both servers)
│   ├── auth.py, deps.py    # JWT authentication (HS256, 60min expiry)
│   ├── log_config.py       # Logging (daily files: temp/logs/yyyyMMdd.AiDiy.log)
│   ├── conf/               # ConfigManager singleton (reads _config/AiDiy_key.json)
│   ├── AIコア/             # AI integration modules (WebSocket, streaming, audio)
│   └── _data/AiDiy/database.db  # SQLite database (shared by both servers)
│
├── frontend_server/         # Vue 3 + Vite + TypeScript + Pinia
│   ├── src/
│   │   ├── components/     # Feature components by category
│   │   │   ├── C管理/      # C系 (Core) CRUD screens
│   │   │   ├── Mマスタ/    # M系 (Master) screens
│   │   │   ├── Tトラン/    # T系 (Transaction) screens
│   │   │   ├── Sスケジューラー/  # S系 (Scheduler) screens
│   │   │   ├── Vビュー/    # V系 (View) screens
│   │   │   ├── AIコア/    # AI interface (WebSocket, multi-panel)
│   │   │   ├── Xテスト/    # Experimental features
│   │   │   └── _share/     # Shared components (qTubler, dialogs)
│   │   ├── stores/auth.ts  # Pinia auth store (JWT in localStorage)
│   │   ├── api/client.ts   # Axios with JWT interceptors
│   │   ├── api/websocket.ts # WebSocket client (AIコア)
│   │   ├── types/          # TypeScript types (api.ts, entities.ts, qTubler.ts)
│   │   └── router/         # Vue Router (Japanese URLs)
│   └── vite.config.ts      # Proxy: /core→8091, /apps→8092, port 8090
```

**Table Naming Convention:**
- `C` = Core/Common (C権限, C利用者, C採番)
- `M` = Master (M配車区分, M車両, M商品)
- `T` = Transaction (T配車, T商品入庫, T商品出庫, T商品棚卸)
- `V` = View endpoints (raw SQL, not DB views)
- `S` = Scheduler/Special (S配車_週表示, S配車_日表示)
- `A` = AI/Advanced (AIコア, A会話履歴)
- `X` = Experimental/Test features

---

## Key Patterns

**Backend - Adding a new table (C系/A系 in core_main):**
1. Create model in `core_models/<テーブル名>.py`
2. Export in `core_models/__init__.py`
3. Add Pydantic schemas to `core_schema.py`
4. Create CRUD in `core_crud/<テーブル名>.py`
5. **Export in `core_crud/__init__.py` (easy to forget — causes AttributeError if missed)**
6. Create router in `core_router/<テーブル名>.py`
7. Register in `core_main.py` with `include_router` and `create_all`

**Backend - Adding a new table (M系/T系 in apps_main):**
- Same as above, but use `apps_models/`, `apps_crud/`, `apps_router/`, `apps_main.py`
- **Also create a V系 router** (`apps_router/V<テーブル名>.py`) — frontend list screens use V系 endpoints, not M系 directly
- Register both M系 and V系 routers in `apps_main.py`

**Backend - Schema changes (ALTER TABLE for existing DB):**
```python
# In apps_crud/init.py (or core_crud/init.py) — runs at startup
from sqlalchemy import text

def apply_schema_migrations(db: Session):
    result = db.execute(text("PRAGMA table_info(テーブル名)")).fetchall()
    existing_columns = [row[1] for row in result]
    if "新カラム名" not in existing_columns:
        db.execute(text("ALTER TABLE テーブル名 ADD COLUMN 新カラム名 TEXT"))
        db.commit()
```
SQLite only supports `ADD COLUMN` / `RENAME` via ALTER TABLE. Column deletion requires table recreation.

**Backend - Authenticated endpoints (dependency injection):**
```python
from deps import get_db, get_現在利用者
from core_models import C利用者

@router.post("/一覧")
def list_items(db: Session = Depends(get_db), 現在利用者: C利用者 = Depends(get_現在利用者)):
    pass
```

**Backend - Audit fields (required on all tables):**
```python
from core_crud.utils import create_audit_fields, update_audit_fields

# Create
認証情報 = {"利用者ID": 現在利用者.利用者ID, "利用者名": 現在利用者.利用者名}
監査項目 = create_audit_fields(認証情報)
db.add(Model(..., **監査項目))

# Update
監査項目 = update_audit_fields(認証情報)
for key, value in 監査項目.items():
    setattr(record, key, value)
```

**Backend - AI API keys:**
- Store in `backend_server/_config/AiDiy_key.json` (auto-created with defaults if missing)
- Keys: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`
- Access via `request.app.conf.json.get("KEY_NAME")`

**Backend - AIコア WebSocket messages (core_router/AIコア.py):**
- Request/response packets: `{セッションID, チャンネル, メッセージ識別, メッセージ内容}`
- File list packets: `files_backup` (backup file list) / `files_temp` (temp folder, 1h window)
- Each file entry: `{"パス": str, "更新日時": str}` — file list is `List[str]` in session, mtimes read on demand
- Session state: `セッション.全ファイルリスト` = `List[str]` paths, `セッション.バックアップベースパス` = backup dir, `セッション.ソース最終更新日時` = max mtime string

**Frontend - CRUD screen structure:**
```
components/<カテゴリ>/<テーブル名>/
├── <テーブル名>一覧.vue           # List page (calls V系 API)
├── <テーブル名>編集.vue           # Edit/Create page
└── components/
    └── <テーブル名>一覧テーブル.vue  # qTubler wrapper
```

**Frontend - API calls:**
```typescript
import apiClient from '@/api/client'
const response = await apiClient.post('/core/C利用者/一覧')
if (response.data.status === 'OK') {
  items.value = response.data.data.items
}
```

**Frontend - Dialogs:**
```typescript
import { qAlert, qConfirm } from '@/utils/qAlert'
await qAlert('保存しました')
const ok = await qConfirm('削除しますか？')
```

**Frontend - AIコア WebSocket client:**
```typescript
// src/api/websocket.ts — channel-based listener
出力WebSocket.value = new AIコアWebSocket(wsUrl, セッションID, 'file');
出力WebSocket.value.on('files_backup', ハンドラ関数);
出力WebSocket.value.on('files_temp', ハンドラ関数);
// Send: プロパティ.wsClient.send({セッションID, チャンネル, メッセージ識別, メッセージ内容})
```

**Frontend - TypeScript note:**
- Strict mode is **disabled** (`strict: false`) — intentional for development speed
- Type definitions in `src/types/` (api.ts, entities.ts, qTubler.ts, store.ts)

---

## Documentation Index

| Document | Purpose |
|----------|---------|
| [README.md](./README.md) | Setup, start/stop, cleanup |
| [AGENTS.md](./AGENTS.md) | Project overview, commands, common issues |
| [backend_server/AGENTS.md](./backend_server/AGENTS.md) | Backend implementation details |
| [frontend_server/AGENTS.md](./frontend_server/AGENTS.md) | Frontend implementation details |

**HTML Docs (docs/開発ガイド/ folder):**
| Folder | Purpose |
|--------|---------|
| [00_このプロジェクトの歩き方](./docs/開発ガイド/00_このプロジェクトの歩き方/_index.html) | System overview, FAQ |
| [01_環境構築ハンズオン](./docs/開発ガイド/01_明日のために！その１_環境構築ハンズオン/_index.html) | Environment setup |
| [02_設計](./docs/開発ガイド/02_明日のために！その２_設計/_index.html) | Design policy |
| [03_バックエンド開発](./docs/開発ガイド/03_明日のために！その３_バックエンド開発/_index.html) | Backend API implementation |
| [04_フロントエンド開発](./docs/開発ガイド/04_明日のために！その４_フロントエンド開発/_index.html) | Frontend CRUD screen guide |
| [11_コーディングルール](./docs/開発ガイド/11_コーディングルール/_index.html) | Coding rules, naming, best practices **(必読)** |
| [12_フロントエンド画面追加例](./docs/開発ガイド/12_フロントエンド画面追加例/_index.html) | Frontend screen addition example |
