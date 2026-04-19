# このプロジェクトの歩き方

このガイドは、**現在の AiDiy2026 実装** を前提に、最初に何を読めばよいかを整理するための案内です。

古いテンプレート由来の PostgreSQL / Alembic / `base_server` 前提ではなく、**FastAPI + SQLite + Vue 3 + Electron** の現行構成に合わせています。

---

## 1. まず押さえること

- バックエンドは **3 サーバー**
  - `core_main.py` : `8091`
  - `apps_main.py` : `8092`
  - `mcp_main.py` : `8095`
- Web フロントは `frontend_web`、ポート `8090`
- Avatar フロントは `frontend_avatar`、ポート `8099`
- DB は **SQLite**
  - `backend_server/_data/AiDiy/database.db`
- スキーマ変更は **Alembic なし**
  - モデル更新
  - 既存 DB には `ALTER TABLE` などを `init.py` で適用
- 画面や API は日本語命名が基本

---

## 2. リポジトリ構成

```text
AiDiy2026/
├── AGENTS.md
├── README.md
├── _setup.py
├── _start.py
├── _cleanup.py
├── backend_mcp/
│   ├── mcp_main.py
│   ├── mcp_proc/
│   └── AGENTS.md
├── backend_server/
│   ├── core_main.py
│   ├── apps_main.py
│   ├── core_router/
│   ├── apps_router/
│   ├── core_models/
│   ├── apps_models/
│   ├── core_schema/
│   ├── apps_schema/
│   ├── core_crud/
│   ├── apps_crud/
│   ├── AIコア/
│   └── AGENTS.md
├── frontend_web/
│   ├── src/
│   │   ├── router/
│   │   ├── stores/
│   │   ├── api/
│   │   └── components/
│   └── AGENTS.md
├── frontend_avatar/
│   ├── electron/
│   ├── src/
│   ├── public/
│   └── AGENTS.md
└── docs/
```

---

## 3. 最短で動かす

### セットアップ

```powershell
python _setup.py
```

### 起動

```powershell
python _start.py
```

`_start.py` は**対話形式**です。起動時に以下を選択します。

- バックエンド(mcp)
- バックエンド(core/apps)
- フロントエンド(Web)
- フロントエンド(Avatar)

### 個別起動

```powershell
# backend mcp
cd backend_mcp
.venv/Scripts/python.exe -m uvicorn mcp_main:app --reload --host 0.0.0.0 --port 8095

# backend core
cd backend_server
.venv/Scripts/python.exe -m uvicorn core_main:app --reload --host 0.0.0.0 --port 8091

# backend apps
cd backend_server
.venv/Scripts/python.exe -m uvicorn apps_main:app --reload --host 0.0.0.0 --port 8092

# frontend web
cd frontend_web
npm run dev

# frontend avatar
cd frontend_avatar
npm run dev
```

---

## 4. アクセス URL

| 用途 | URL |
|------|-----|
| Web フロント | http://localhost:8090 |
| Core API Docs | http://localhost:8091/docs |
| Apps API Docs | http://localhost:8092/docs |
| Backend MCP Chrome DevTools (SSE) | http://localhost:8095/aidiy_chrome_devtools/sse |
| Backend MCP Desktop Capture (SSE) | http://localhost:8095/aidiy_desktop_capture/sse |
| Backend MCP SQLite (SSE)          | http://localhost:8095/aidiy_sqlite/sse |
| Backend MCP PostgreSQL (SSE)      | http://localhost:8095/aidiy_postgres/sse |
| Backend MCP Logs (SSE)            | http://localhost:8095/aidiy_logs/sse |
| Backend MCP Code Check (SSE)      | http://localhost:8095/aidiy_code_check/sse |
| Avatar Web モード | http://localhost:8099 |

初期ユーザー:

- `admin / ********`
- `leader / secret`
- `user / user`
- `guest / guest`
- `other / other`

---

## 5. バックエンドの見方

### 役割分担

- `core_router/`
  - 認証、C系、A系、files、AIコア
- `apps_router/`
  - M系、T系、V系、S系
- `core_models/`, `apps_models/`
  - SQLAlchemy モデル
- `core_schema/`, `apps_schema/`
  - Pydantic スキーマ
- `core_crud/`, `apps_crud/`
  - DB 操作と初期化処理

### 大事な前提

- CRUD は原則 POST
- V 系は DB VIEW ではなく生 SQL
- `apps_crud/__init__.py` 追加漏れに注意
- M 系一覧は通常 V 系エンドポイントを使う
- パスワードは現状平文比較
- Claude のブラウザ自動操作は `backend_mcp` と `backend_server/_config/AiDiy_mcp.json` を併用する

---

## 6. フロントエンド Web の見方

- ルーター: `frontend_web/src/router/`
- 認証: `frontend_web/src/stores/auth.ts`
- API: `frontend_web/src/api/client.ts`
- AI 画面ルート: `/AiDiy`
- 一覧画面は `qTublerFrame` ベース

主要カテゴリ:

- `C管理`
- `Mマスタ`
- `Tトラン`
- `Sスケジュール`
- `Vビュー`
- `Xその他`

---

## 7. フロントエンド Avatar の見方

- Electron メイン: `frontend_avatar/electron/main.ts`
- preload: `frontend_avatar/electron/preload.ts`
- renderer エントリ: `frontend_avatar/src/AiDiy.vue`

動作モード:

- Electron
  - `localStorage`
  - 複数ウィンドウ
- Web
  - `sessionStorage`
  - `http://localhost:8099`
  - 単一タブ + 左右分割

---

## 8. 変更反映と再起動

`_start.py` で起動したバックエンドは `--reload` なしです。

### 推奨方法

```powershell
echo. > backend_server/temp/reboot_core.txt
echo. > backend_server/temp/reboot_apps.txt
```

または個別に `uvicorn --reload` で起動します。

---

## 9. テスト方針

現状、**自動テストは整備されていません**。基本は手動確認です。

- API: Swagger UI
- Web UI: ブラウザ
- Avatar: Electron / Web の両モード確認

実装追加後は最低でも以下を確認します。

1. 一覧取得
2. 取得
3. 登録
4. 変更
5. 削除または無効化
6. ルーティング
7. 初期データや採番の連動

---

## 10. まず読む順番

1. [README.md](../../README.md)
2. [AGENTS.md](../../AGENTS.md)
3. [backend_server/AGENTS.md](../../backend_server/AGENTS.md)
4. [backend_mcp/AGENTS.md](../../backend_mcp/AGENTS.md)
5. [frontend_web/AGENTS.md](../../frontend_web/AGENTS.md)
6. [frontend_avatar/AGENTS.md](../../frontend_avatar/AGENTS.md)

---

## 11. docs 配下の補助資料

- `00_このプロジェクトの歩き方/`
  - 全体像と導入
- `01_明日のために！その１_環境構築ハンズオン/`
  - セットアップと起動
- `02_明日のために！その２_設計/`
  - 設計サンプル
- `03_明日のために！その３_バックエンド開発/`
  - API 実装の流れ
- `04_明日のために！その４_フロントエンド開発/`
  - 画面実装の流れ
- `11_コーディングルール/`
  - 必読
- `12_フロントエンド画面追加例/`
  - CRUD 追加例

---

## 12. 迷ったとき

- 古いテンプレート由来の `PostgreSQL`, `Alembic`, `base_server`, `base_client` 記述は現行実装には当てはまりません。
- 実装事実を優先してください。
- 迷ったらまず `AGENTS.md` と各サブ `AGENTS.md` を見てください。
