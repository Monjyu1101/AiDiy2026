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

**No Automated Tests:**
- No pytest or vitest configured
- Test manually via Swagger UI (`:8091/docs`, `:8092/docs`) and browser

---

## Quick Start

```bash
# Initial setup
python _setup.py

# Start all servers (frontend + backend)
python _start.py

# Stop all servers
python _stop.py

# Backend hot-reload (when code changes needed)
echo. > backend_server/temp/reboot_core.txt   # core_main
echo. > backend_server/temp/reboot_apps.txt   # apps_main

# Database reset
del backend_server\_data\AiDiy\database.db
python _start.py
```

## Access URLs

| Service | URL | Default Login |
|---------|-----|---------------|
| Frontend | http://localhost:8090 | `admin` / `********` |
| API Docs (Core) | http://localhost:8091/docs | |
| API Docs (Apps) | http://localhost:8092/docs | |

---

## Architecture Overview

```
AiDiy2026/
├── backend_server/          # FastAPI (Python 3.13) + SQLAlchemy + SQLite
│   ├── core_main.py            # Port 8091 - C系, A系
│   ├── apps_main.py            # Port 8092 - M系, T系, V系, S系
│   ├── core_models/, apps_models/  # SQLAlchemy ORM models
│   ├── core_crud/, apps_crud/      # Database operations
│   ├── core_router/, apps_router/  # API endpoints
│   ├── core_schema.py, apps_schema.py  # Pydantic models
│   ├── database.py         # SQLite config (shared by both servers)
│   ├── auth.py, deps.py    # JWT authentication
│   └── _data/AiDiy/database.db  # SQLite database
│
├── frontend_server/         # Vue 3 + Vite + TypeScript + Pinia
│   ├── src/
│   │   ├── components/     # Feature components by category
│   │   │   ├── C管理/      # C系 (Core) CRUD screens
│   │   │   ├── Mマスタ/    # M系 (Master) screens
│   │   │   ├── Tトラン/    # T系 (Transaction) screens
│   │   │   ├── Sスケジューラー/  # S系 (Scheduler) screens
│   │   │   ├── Vビュー/    # V系 (View) screens
│   │   │   ├── AIコア/    # AI interface
│   │   │   ├── Xテスト/    # Experimental features
│   │   │   └── _share/     # Shared components (qTubler, dialogs)
│   │   ├── stores/auth.ts  # Pinia auth store
│   │   ├── api/client.ts   # Axios with JWT interceptors
│   │   └── router/         # Vue Router (Japanese URLs)
│   └── vite.config.ts      # Proxy: /core→8091, /apps→8092
```

**Table Naming Convention:**
- `C` = Core/Common (C権限, C利用者, C採番)
- `M` = Master (M配車区分, M車両, M商品)
- `T` = Transaction (T配車, T商品入庫, T商品出庫, T商品棚卸)
- `V` = View endpoints (raw SQL, not DB views)
- `S` = Scheduler/Special (S配車_週表示, S配車_日表示)
- `A` = AI/Advanced (AIコア, A会話履歴)
- `X` = Experimental (Xテトリス, Xインベーダー, Xリバーシ)

---

## Key Implementation Patterns

### Backend Patterns

**Adding a new table (C系/A系 in core_main):**
1. Create model in `core_models/<テーブル名>.py`
2. Export in `core_models/__init__.py`
3. Add Pydantic schemas to `core_schema.py`
4. Create CRUD in `core_crud/<テーブル名>.py`
5. Create router in `core_router/<テーブル名>.py`
6. Register in `core_main.py` with `include_router`

**Authenticated endpoints:**
```python
from deps import get_db, get_現在利用者
from core_models import C利用者

@router.post("/一覧")
def list_items(db: Session = Depends(get_db), 現在利用者: C利用者 = Depends(get_現在利用者)):
    # 現在利用者 contains the JWT-authenticated user
```

**Audit fields (required on all tables):**
```python
from core_crud.utils import create_audit_fields, update_audit_fields

# Create
監査項目 = create_audit_fields(認証情報)
db.add(Model(..., **監査項目))

# Update
監査項目 = update_audit_fields(認証情報)
for key, value in 監査項目.items():
    setattr(record, key, value)
```

**V系 endpoints (raw SQL, NOT database VIEWs):**
```python
# V利用者/一覧 example
sql = """
SELECT C利用者.*, C権限.権限名
FROM C利用者
LEFT JOIN C権限 ON C利用者.権限ID = C権限.権限ID
"""
result = db.execute(text(sql))
items = [dict(row) for row in result]
```

### Frontend Patterns

**CRUD screen structure:**
```
components/<カテゴリ>/<テーブル名>/
├── <テーブル名>一覧.vue           # List page
├── <テーブル名>編集.vue           # Edit/Create page
└── components/
    └── <テーブル名>一覧テーブル.vue  # qTubler wrapper
```

**API calls:**
```typescript
import apiClient from '@/api/client'

// Automatically includes JWT token via interceptor
const response = await apiClient.post('/core/C利用者/一覧')
if (response.data.status === 'OK') {
  items.value = response.data.data.items
}
```

**qTubler usage:**
```vue
<template>
  <qTubler
    :columns="columns"
    :data="items"
    :pageSize="20"
    @row-dblclick="handleEdit"
  />
</template>

<script setup lang="ts">
import qTubler from '@/components/_share/qTubler.vue'
const columns = [
  { key: '利用者ID', label: '利用者ID', width: '150px', sortable: true },
  { key: '利用者名', label: '利用者名', width: '200px', sortable: true },
]
</script>
```

---

## Common Issues

| Issue | Solution |
|-------|----------|
| **Backend import error** | `cd backend_server && uv sync` |
| **Frontend module not found** | `cd frontend_server && npm install` |
| **Port conflicts** | `python _stop.py` then `python _start.py` |
| **Database locked** | Close SQLite browser/tools before starting servers |
| **401 Unauthorized** | JWT expired (60min) - re-login at `http://localhost:8090/ログイン` |
| **Code changes not reflected** | `echo. > backend_server/temp/reboot_core.txt` or restart with `--reload` |
| **Vue component shows as text** | Use `<component :is="日本語名" />` instead of `<日本語名 />` |

---

## Documentation Index

**Quick Reference:**
- [README.md](./README.md) - Setup, start/stop, troubleshooting
- [AGENTS.md](./AGENTS.md) - Project overview, development commands

**Implementation Details:**
- [backend_server/AGENTS.md](./backend_server/AGENTS.md) - Backend patterns, API design, database
- [frontend_server/AGENTS.md](./frontend_server/AGENTS.md) - Frontend architecture, routing, components

**HTML Documentation (docs/ folder):**
- [00_AiDiyシステムの歩き方](./docs/00_AiDiyシステムの歩き方/_index.html) - System overview, FAQ
- [01_バックエンド_M配車区分実装例](./docs/01_明日のために！その１_バックエンド_M配車区分実装例/_index.html) - Backend example
- [02_バックエンド_M配車区分テスト例](./docs/02_明日のために！その２_バックエンド_M配車区分テスト例/_index.html) - Testing guide
- [03_コーディングルール](./docs/03_コーディングルール/_index.html) - Coding standards, naming, best practices
- [04_フロントエンド画面追加例](./docs/04_フロントエンド画面追加例/_index.html) - Frontend CRUD screen guide
