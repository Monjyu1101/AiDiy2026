# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

## AI 設定ファイル

AIコアを動かすには `backend_server/_config/AiDiy_key.json` に API キーを記載する（初回は手動作成）。同フォルダに以下の設定ファイルが存在する：

- `AiDiy_key.json` — AI API キー（Anthropic/OpenAI/Gemini）
- `AiDiy_chat__context.json` / `AiDiy_live__context.json` / `AiDiy_code__context.json` — AIコアのシステムコンテキスト
- `AiDiy_live_gemini.json` / `AiDiy_live_openai.json` / `AiDiy_code_claude_*.json` など — ベンダー別設定

### AI モデル命名規則（重要）

`CHAT_AI_NAME` / `LIVE_AI_NAME` / `CODE_AI*_NAME` の値には末尾サフィックスが必須：

| キー | サフィックス | 例 |
|------|------------|-----|
| `CHAT_AI_NAME` | `_chat` で終わる | `gemini_chat`, `openai_chat`, `freeai_chat` |
| `LIVE_AI_NAME` | `_live` で終わる | `gemini_live`, `openai_live`, `freeai_live` |
| `CODE_AI1_NAME` 〜 `CODE_AI4_NAME` | `_sdk` または `_cli` で終わる | `claude_sdk`, `claude_cli`, `copilot_cli`, `codex_cli`, `gemini_cli`, `hermes_cli` |

比較は**完全一致のみ**（`startswith` 等の前方一致は使用禁止）。設定変更時は `backend_server/_config/AiDiy_*.json` と `frontend_avatar/src/api/config.ts` の `defaultModelSettings()` を合わせて更新する。

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
touch backend_server/temp/reboot_core.txt
touch backend_server/temp/reboot_apps.txt

# DB reset (全データ削除・テーブル再作成・初期データ投入)
# 全サーバー停止後に実行すること
rm backend_server/_data/AiDiy/database.db
```

補足:

- `_start.py` は引数指定ではなく対話形式です。
- `_start.py` で起動したバックエンドは `--reload` なし。コード変更を即反映するには個別起動 or reboot 機構を使う。
- `_stop.py` は現在ありません。停止は `Ctrl+C` または手動のポート解放で行います（`netstat -ano | findstr :8091` → `taskkill /PID <pid> /F`）。
- `frontend_avatar` の `npm run build` は明示依頼時のみ実行します。

## Access URLs

| Service | URL |
|---------|-----|
| Frontend (Web) | http://localhost:8090 |
| Core API Docs | http://localhost:8091/docs |
| Apps API Docs | http://localhost:8092/docs |
| Frontend (Avatar Web) | http://localhost:8099 |
| Frontend (Avatar Electron) | `npm run dev` で起動 |

**Default login:** `admin / ********`（他: `leader/secret`, `user/user`, `guest/guest`, `other/other`）

---

## Architecture Overview

### システム系統

| 系統 | 説明 | サーバー |
|------|------|---------|
| C系 | Core/Common（権限・利用者・採番） | core_main |
| A系 | AI/Advanced（AIコア・会話履歴・WebSocket） | core_main |
| M系 | Master（配車区分・車両・商品等） | apps_main |
| T系 | Transaction（配車・生産・在庫入出庫等） | apps_main |
| V系 | View（JOIN集計・生SQL） | apps_main |
| S系 | Scheduler/Special（週/日スケジュール表示） | apps_main |
| X系 | Experimental（ゲーム等・フロントのみ） | — |

### デュアルサーバー構成

2つの独立した FastAPI サーバーが同じ SQLite DB を共有する：

- **core_main.py** (8091): C系（権限・利用者・採番）、A系（AIコア・会話履歴）、WebSocket
- **apps_main.py** (8092): M系（マスタ）、T系（トランザクション）、V系（JOIN表示）、S系（スケジューラ）

Vite Proxy が `/core/*` → 8091、`/apps/*` → 8092 に自動振り分け。フロントのポートを変えたら `core_main.py` / `apps_main.py` の CORS 許可リストも更新すること。

DB ファイル: `backend_server/_data/AiDiy/database.db`

### API 設計の原則

- **全 CRUD は POST メソッド**（例外: `GET /` と `GET /core/サーバー状態`）
- **統一レスポンス形式:** `{"status": "OK"/"NG", "message": "...", "data": {...}}`
- **一覧系:** `{"items": [], "total": 100, "limit": 10000}`
- **V系エンドポイントは DB VIEW オブジェクト不使用** — 生 SQL（SELECT + LEFT JOIN）で実装

### 命名規約（全レイヤー共通）

日本語識別子を全レイヤーで使用：
- DB テーブル名: `C権限`, `M商品`, `T配車`
- カラム名: `利用者ID`, `配車日付`, `商品名`
- API エンドポイント: `/core/利用者/一覧`, `/apps/商品/作成`
- Vue コンポーネントファイル名: `C利用者一覧.vue`（ファイル名は日本語 OK）
- Vue コンポーネント **タグ名は ASCII のみ**：`<component :is="C利用者一覧 />` ← 正解、`<C利用者一覧 />` ← 無効

### カスタム ID 生成（C採番）

AUTOINCREMENT は使用しない。`C採番` テーブルが各テーブルの次 ID を管理する。新規レコード作成前に `/core/C採番/採番` API でトランザクション保護された ID を取得。

### 監査フィールド

全テーブルに自動付与：`登録日時`, `登録利用者ID`, `登録利用者名`, `登録端末ID`, `更新日時`, `更新利用者ID`, `更新利用者名`, `更新端末ID`。`core_crud/utils.py` / `apps_crud/utils.py` の `create_audit_fields()` / `update_audit_fields()` を使用。

### スキーマ変更（Alembic なし）

スキーマ変更時は既存 DB に手動適用が必要（適用しないとサーバー起動エラー）。`apps_crud/init.py` の `apply_schema_migrations()` に追記し起動時自動実行させる：

**カラム追加（ALTER TABLE ADD COLUMN）:**
```python
result = db.execute(text("PRAGMA table_info(テーブル名)")).fetchall()
existing_columns = [row[1] for row in result]
if "新カラム名" not in existing_columns:
    db.execute(text("ALTER TABLE テーブル名 ADD COLUMN 新カラム名 TEXT"))
    db.commit()
```

**カラム削除・型変更（テーブル再作成）:**
SQLite は `DROP COLUMN` / 型変更に非対応。新テーブルを作成しデータを移行後、旧テーブルをDROPしてリネームする。

**不要テーブル削除:**
```python
db.execute(text("DROP TABLE IF EXISTS 旧テーブル名"))
db.commit()
```

SQLite の `ALTER TABLE` はカラム追加・テーブル名変更・カラム名変更のみ対応。

### 新規テーブル追加チェックリスト（忘れやすい）

1. `apps_models/__init__.py` に Model import 追加（テーブル生成に必要）
2. **`apps_crud/__init__.py` に CRUD 関数の import と `__all__` 追加**（必須・最も忘れやすい）
3. `apps_main.py` に Router 登録
4. 初期データが必要なら `apps_crud/init.py` に初期化処理追加

### ドキュメントリソース

詳細な実装ガイドは `docs/開発ガイド/` フォルダに HTML 形式で整備されている。新規作成（API・テーブル・画面）後は該当章のチェック項目で自己検証すること：

| フォルダ | 内容 |
|---------|------|
| `docs/開発ガイド/11_コーディングルール/` | 命名規則・ベストプラクティス・レビューチェックリスト（**必読**）|
| `docs/開発ガイド/12_フロントエンド画面追加例/` | フロントエンド CRUD 画面追加手順 |
| `docs/開発ガイド/03_明日のために！その３_バックエンド開発/` | バックエンド API 実装手順 |
| `docs/開発ガイド/04_明日のために！その４_フロントエンド開発/` | フロントエンド実装手順 |

### フロントエンド (frontend_web)

- TypeScript strict mode 無効（`strictNullChecks: false`, `noImplicitAny: false`）
- JWT token は `localStorage` に保存、Axios interceptor で自動付与、401 で自動ログアウト
- qTubler: カスタムテーブルコンポーネント（`_share/qTublerFrame.vue`）— ソート・ページング・行選択付き（`qTubler.vue` は存在しない）
- CRUD 画面パターン: `<カテゴリ>/<テーブル名>/`一覧.vue + 編集.vue + `components/`一覧テーブル.vue
- 外部 UI フレームワーク不使用（Vuetify/Element Plus 等は使わない）— カスタム CSS + 独自コンポーネント
- 共通ダイアログ: `qAlert(message)`, `qConfirm(message)`, `qColorPicker(initialColor, title)` — Promise-based、App.vue でグローバル登録

### frontend_avatar（Electron / Web デュアルモード）

- `!!window.desktopApi` が `true` → Electron モード（`localStorage`、複数 BrowserWindow）
- `!!window.desktopApi` が `false` → Web モード（`sessionStorage`、単一タブ `/AiDiy?role=core`）
- Vue Router / Pinia は使用しない（frontend_web とは別設計）
- エントリーポイント: `src/AiDiy.vue`（`App.vue` は存在しない）— role に応じてコンポーネント切替
- Electron ウィンドウ role 一覧: `login`, `core`（アバター常駐）, `chat`, `file`, `image`, `code1`〜`code4`, `settings`
- ウィンドウは透明＋フレームレス基本（settings のみ不透明 760×700）
- 補助パネル間同期: BroadcastChannel `avatar-desktop-sync`
