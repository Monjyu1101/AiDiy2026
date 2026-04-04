# CLAUDE.md

This file provides a quick index for working in this repository.

> 実装詳細は次を参照してください。
> - [AGENTS.md](./AGENTS.md)
> - [backend_server/AGENTS.md](./backend_server/AGENTS.md)
> - [frontend_web/AGENTS.md](./frontend_web/AGENTS.md)
> - [frontend_avatar/AGENTS.md](./frontend_avatar/AGENTS.md)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.13.3, FastAPI, SQLAlchemy, SQLite, uv |
| Frontend Web | Node.js 22, Vue 3, Vite, TypeScript, Pinia, Vue Router 4 |
| Frontend Avatar | Vue 3, Vite, TypeScript, Electron, Three.js, WebSocket |
| Auth | JWT (python-jose, HS256, 60分) |
| AI | Anthropic Claude, OpenAI, Google Gemini |

## Critical Constraints

- Japanese-first implementation
- All files must be UTF-8
- CRUD APIs are POST-based
- V系は DB VIEW ではなく生 SQL
- Passwords are plaintext today
- No Alembic migrations
- `frontend_avatar` は Electron / Web デュアルモード
- Web 版 AI 画面ルートは `/AiDiy`

## Quick Commands

```bash
# Initial setup
python _setup.py

# Start services (interactive prompt)
python _start.py

# Backend hot reload (manual)
cd backend_server && .venv/Scripts/python.exe -m uvicorn core_main:app --reload --host 0.0.0.0 --port 8091
cd backend_server && .venv/Scripts/python.exe -m uvicorn apps_main:app --reload --host 0.0.0.0 --port 8092

# Frontend
cd frontend_web && npm run dev
cd frontend_web && npm run type-check

# Avatar
cd frontend_avatar && npm run dev
cd frontend_avatar && npm run type-check

# Backend dependency sync
cd backend_server && uv sync

# Cleanup
python _cleanup.py

# Backend reboot trigger when started via _start.py
echo. > backend_server/temp/reboot_core.txt
echo. > backend_server/temp/reboot_apps.txt
```

補足:

- `_start.py` は引数指定ではなく対話形式です。
- `_stop.py` は現在ありません。停止は `Ctrl+C` または手動のポート解放で行います。
- `frontend_avatar` の `npm run build` は明示依頼時のみ実行します。

## Access URLs

| Service | URL |
|---------|-----|
| Frontend (Web) | http://localhost:8090 |
| Core API Docs | http://localhost:8091/docs |
| Apps API Docs | http://localhost:8092/docs |
| Frontend (Avatar Web) | http://localhost:8099/AiDiy |
| Frontend (Avatar Electron) | `npm run dev` で起動 |

**Default login:** `admin / ********`
