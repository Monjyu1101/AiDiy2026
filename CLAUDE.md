# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> 実装詳細は次を参照してください。
> - [AGENTS.md](./AGENTS.md)
> - [backend_server/AGENTS.md](./backend_server/AGENTS.md)
> - [backend_mcp/AGENTS.md](./backend_mcp/AGENTS.md)
> - [frontend_web/AGENTS.md](./frontend_web/AGENTS.md)
> - [frontend_avatar/AGENTS.md](./frontend_avatar/AGENTS.md)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.13.3, FastAPI, SQLAlchemy, SQLite, uv |
| Backend MCP | Python 3.13.3, FastMCP (SSE×6), CDP, pyautogui, PIL, SQLite3, psycopg, subprocess |
| Frontend Web | Node.js 22, Vue 3, Vite, TypeScript, Pinia, Vue Router 4 |
| Frontend Avatar | Vue 3, Vite, TypeScript, Electron, Three.js, WebSocket |
| Auth | JWT (python-jose, HS256, 60分) |
| AI | Anthropic Claude, OpenAI, Google Gemini |
| AI Browser | Claude Agent SDK + MCP (aidiy_chrome_devtools / aidiy_desktop_capture / aidiy_sqlite / aidiy_postgres / aidiy_logs / aidiy_code_check via backend_mcp) |

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
- `AiDiy_mcp.json` — MCP サーバー設定（Claude Agent SDK に渡す `mcpServers` を定義）

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
cd backend_mcp && .venv/Scripts/python.exe -m uvicorn mcp_main:app --reload --host 0.0.0.0 --port 8095

# Frontend
cd frontend_web && npm run dev
cd frontend_web && npm run type-check

# Avatar
cd frontend_avatar && npm run dev
cd frontend_avatar && npm run type-check

# Backend dependency sync
cd backend_server && uv sync
cd backend_mcp && uv sync

# Cleanup
python _cleanup.py

# Backend reboot trigger when started via _start.py (Windows)
echo. > backend_server/temp/reboot_core.txt
echo. > backend_server/temp/reboot_apps.txt
echo. > backend_mcp/temp/reboot_mcp.txt

# DB reset (全データ削除・テーブル再作成・初期データ投入)
# 全サーバー停止後に実行すること
rm backend_server/_data/AiDiy/database.db
```

補足:

- `_start.py` は引数指定ではなく対話形式です。
- `_start.py` で起動したバックエンドは `--reload` なし。コード変更を即反映するには個別起動 or reboot 機構を使う。
- `_stop.py` は現在ありません。停止は `Ctrl+C` または手動のポート解放で行います（例: `netstat -ano | findstr :8091` → `taskkill /PID <pid> /F`。8092・8095 も同様）。
- `frontend_avatar` の `npm run build` は明示依頼時のみ実行します。

## Access URLs

| Service | URL |
|---------|-----|
| Frontend (Web) | http://localhost:8090 |
| Core API Docs | http://localhost:8091/docs |
| Apps API Docs | http://localhost:8092/docs |
| Backend MCP Chrome DevTools (SSE) | http://localhost:8095/aidiy_chrome_devtools/sse |
| Backend MCP Desktop Capture (SSE) | http://localhost:8095/aidiy_desktop_capture/sse |
| Backend MCP SQLite (SSE) | http://localhost:8095/aidiy_sqlite/sse |
| Backend MCP PostgreSQL (SSE) | http://localhost:8095/aidiy_postgres/sse |
| Backend MCP Logs (SSE) | http://localhost:8095/aidiy_logs/sse |
| Backend MCP Code Check (SSE) | http://localhost:8095/aidiy_code_check/sse |
| Backend MCP Backup Check (SSE) | http://localhost:8095/aidiy_backup_check/sse |
| Backend MCP Backup Save (SSE) | http://localhost:8095/aidiy_backup_save/sse |
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

### マルチサーバー構成

3つの独立したサーバーで構成される：

- **core_main.py** (8091): C系（権限・利用者・採番）、A系（AIコア・会話履歴）、WebSocket
- **apps_main.py** (8092): M系（マスタ）、T系（トランザクション）、V系（JOIN表示）、S系（スケジューラ）
- **mcp_main.py** (8095): MCP サーバー × 8 エンドポイント — Chrome DevTools (`/aidiy_chrome_devtools/sse`) / Desktop Capture (`/aidiy_desktop_capture/sse`) / SQLite (`/aidiy_sqlite/sse`) / PostgreSQL (`/aidiy_postgres/sse`) / Logs (`/aidiy_logs/sse`) / Code Check (`/aidiy_code_check/sse`)

core_main / apps_main は同じ SQLite DB を共有。Vite Proxy が `/core/*` → 8091、`/apps/*` → 8092 に自動振り分け。フロントのポートを変えたら `core_main.py` / `apps_main.py` の CORS 許可リストも更新すること。

### AIブラウザ自動操作（MCP連携）

- `backend_mcp/mcp_main.py` が 8 つの MCP サーバー（`aidiy_chrome_devtools` / `aidiy_desktop_capture` / `aidiy_sqlite` / `aidiy_postgres` / `aidiy_logs` / `aidiy_code_check` / `aidiy_backup_check` / `aidiy_backup_save`）を SSE で提供（ポート 8095）
- ブラウザ自動操作・画面キャプチャに加え、**AIエージェントの自己検証を支える DB クエリ（SQLite/PostgreSQL）・ログ観測・型チェック**を同居
- `backend_server/_config/AiDiy_mcp.json` に接続先 MCP サーバーを定義
- `AIコア/AIコード_claude.py`（Claude Agent SDK）が起動時に `AiDiy_mcp.json` を読み込み、`ClaudeAgentOptions.mcp_servers` に渡す
- `permission_mode="bypassPermissions"` により MCP ツール（スクリーンショット・クリック・ナビゲーション等）が自動許可で実行される
- Chrome は `backend_mcp` が必要に応じて自動起動（デバッグポート 9222）

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

### 設定管理（conf/ モジュール）

`backend_server/conf/` が全設定を一元管理する。サーバー起動時に `conf.__main__.Conf` がシングルトンとして生成され、各モジュールは `from conf import conf` でアクセスする：

```python
conf.json.claude_key_id      # AiDiy_key.json の値
conf.models.mcp_servers      # AiDiy_mcp.json の mcpServers
conf.path.exec_abs_path      # backend_server/ の絶対パス
```

- `conf_json.py` — `AiDiy_key.json` 読み書き。不足キーはデフォルト値で自動補完・保存。
- `conf_model.py` — `AiDiy_live_*.json` / `AiDiy_code_*.json` / `AiDiy_mcp.json` 読み込み。モデル一覧・MCPサーバー定義を保持。
- `conf_path.py` — 実行パス・外部プロジェクト検出（`_AIDIY.md` を持つフォルダを自動列挙）。

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

**UI 統一ルール（厳守）:**
- 数値入力欄: 非フォーカス時は3桁区切り表示、フォーカス時はカンマを外して全選択、フォーカスアウト時にカンマ再表示
- 日付欄・日時欄: センタリング表示に統一
- 固定幅入力欄: ラベル幅 `160px` と同一またはその倍数幅で揃える
- 単位付き入力欄: 「入力欄＋単位」合計幅でラベル幅 `160px` の倍数に揃える
- ID 選択欄: ラベルは業務名で表示し、選択肢は `ID : 名称` 形式で統一
- 検索欄: ラベル幅 `160px`、入力欄は `160px` または `320px` 基準

### 明細型マスタ/トランザクションパターン

ヘッダー行と明細行を**単一テーブルで管理**する設計パターン（`M商品構成`・`T生産` が実装例）。

- `明細SEQ=0` がヘッダー行、`明細SEQ≥1` が明細行
- `get_ヘッダ()` / `get_明細一覧()` で用途別に取得
- `create/update` は全明細を一括削除→再作成（楽観ロック不要）

---

### frontend_avatar（Electron / Web デュアルモード）

- `!!window.desktopApi` が `true` → Electron モード（`localStorage`、複数 BrowserWindow）
- `!!window.desktopApi` が `false` → Web モード（`sessionStorage`、単一タブ `/AiDiy?role=core`）
- Vue Router / Pinia は使用しない（frontend_web とは別設計）
- エントリーポイント: `src/AiDiy.vue`（`App.vue` は存在しない）— role に応じてコンポーネント切替
- Electron ウィンドウ role 一覧: `login`, `core`（アバター常駐）, `chat`, `file`, `image`, `code1`〜`code4`, `settings`
- ウィンドウは透明＋フレームレス基本（settings のみ不透明 760×700）
- 補助パネル間同期: BroadcastChannel `avatar-desktop-sync`

---

## .aidiy フォルダ（自己改善知見システム）

`.aidiy/` は**このプロジェクト専用の修正知見フォルダ**。コードエージェントが修正精度を高めるために使う。

**ファイル操作を伴う修正を行う前に必ず確認：**
1. `.aidiy/_index.md` — 知見インデックス（類似テーマがあれば参照）
2. `.aidiy/_最終変更.md` — 直近の修正要約（再修正依頼時の最優先参照先）
3. テーマ別メモ（例: `新たなCLI追加時の作業手順.md`、`CLIプロンプト正規化と履歴保持.md` など）

**修正・検証が完了したら：**
- 次回に再利用できる知見を `.aidiy/` 配下の該当テーマファイルへ追記（or 新規作成）
- `.aidiy/_index.md` のインデックスを更新
- 単なる作業ログではなく「次回の修正判断に使える情報」を残す
- アプリ本体の仕様変更はソースコードへ、知見整理は `.aidiy` へ（混在禁止）

---

## Common Issues

| 現象 | 原因 | 対処 |
|------|------|------|
| バックエンドのコード変更が反映されない | `_start.py` 起動は `--reload` なし | `echo. > backend_server/temp/reboot_core.txt` で再起動、または個別起動で `--reload` 付与 |
| M系マスタ一覧画面でエラー | フロントはV系エンドポイントを使用 | M系テーブル追加時はV系エンドポイントも必ず作成（`apps_router/V*.py`） |
| Vue コンポーネントがテキストとして表示 | 日本語タグ名は HTML 無効 | `<component :is="日本語コンポーネント名" />` を使う |
| `apps_crud/__init__.py` 登録漏れでエラー | 新規テーブル追加時に忘れやすい | 新規テーブル追加チェックリスト（上記）を必ず確認 |
| 初期データが更新されない | admin 未存在のときのみ投入 | DB 削除 → 再起動で再生成 |
| CORS エラー | フロント URL が許可リストにない | `core_main.py` / `apps_main.py` の CORS 許可リストを更新 |
| SQLite database is locked | DB ブラウザツールが開いている | SQLite Browser / DBeaver を閉じてから起動 |
| WebSocket 接続エラー（AIコア） | LiveAI 初期化タイミング問題 | `backend_server/AGENTS.md` の「AIコア Component System」参照 |
