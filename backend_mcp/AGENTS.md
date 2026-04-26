# backend_mcp 実装要点まとめ

## 本書の目的

このファイルは **backend_mcp（MCP サーバー）の実装詳細** を記載したドキュメントです。

**関連ドキュメント：**
- **[../CLAUDE.md](../CLAUDE.md)** - Claude Code向けインデックス（プロジェクト全体概要）
- **[../AGENTS.md](../AGENTS.md)** - プロジェクト全体方針
- **[../backend_server/AGENTS.md](../backend_server/AGENTS.md)** - バックエンド API 実装詳細

---

## 概要

`backend_mcp` は **ポート `8095` 上で 8 つの MCP サーバーを同居させる FastMCP アプリケーション** です。
ブラウザ自動操作・デスクトップキャプチャに加え、**AIエージェントの自己検証を支える開発効率系 MCP** を提供します。

| MCP サーバー | マウントパス | 役割 |
|------------|------------|------|
| `aidiy_chrome_devtools` | `/aidiy_chrome_devtools` | Chrome を CDP で直接操作するブラウザ自動化 |
| `aidiy_desktop_capture` | `/aidiy_desktop_capture` | OS のスクリーンショット取得（全画面・領域・ウィンドウ指定） |
| `aidiy_sqlite`          | `/aidiy_sqlite`          | AiDiy SQLite DB に対する読み取り中心のクエリ（スキーマ確認・件数・監査） |
| `aidiy_postgres`        | `/aidiy_postgres`        | 外部 PostgreSQL に対する read-only 中心クエリ（DSN は環境変数 or 引数） |
| `aidiy_logs`            | `/aidiy_logs`            | `backend_server` / `backend_mcp` のログ tail・エラー抽出 |
| `aidiy_code_check`      | `/aidiy_code_check`      | Python 構文 / ruff / TypeScript 型チェックを subprocess 実行 |
| `aidiy_backup_check`    | `/aidiy_backup_check`    | バックアップフォルダから変更前/変更後ソースを抽出（差分検証用） |
| `aidiy_backup_save`     | `/aidiy_backup_save`     | AiDiy ネイティブの差分バックアップを実行（`バックアップ実行` を動的ロードして流用） |

Chrome 側は `chrome-devtools-mcp`（Node.js 実装）を廃止し、**Python MCP SDK + 自前の CDP クライアント** で直接実装しています。Node.js 依存は不要です。

Claude Agent SDK（`claude_sdk`）やその他 MCP クライアントが、これらを SSE 経由で利用します。
また、`mcp_stdio.py` により **Codex など stdio クライアント向けのブリッジ** も提供します。

### 主な機能

- **Chrome DevTools Protocol を MCP として SSE 公開**（navigate / click / screenshot / DOM取得 等）
- **デスクトップキャプチャを MCP として SSE 公開**（全画面・領域指定・ウィンドウ指定・マルチモニター対応）
- **SQLite クエリを MCP として公開**（read-only が既定・テーブル一覧・describe・count・audit_summary・任意 SELECT）
- **PostgreSQL クエリを MCP として公開**（read-only トランザクション既定・DB/スキーマ/テーブル探索・describe・任意 SELECT）
- **ログ tail を MCP として公開**（末尾 N 行・grep・ERROR 抽出）
- **コードチェックを MCP として公開**（py_compile / ruff / TypeScript type-check）
- **バックアップ確認を MCP として公開**（変更前/変更後ソース抽出・差分検証）
- **バックアップ保存を MCP として公開**（AiDiy ネイティブ差分バックアップ実行）
- 複数クライアントが同一 Chrome インスタンスを共有（`ChromeManager` が単一 subprocess を管理）
- localhost 限定アクセス（外部接続は 403）

---

## ポート・エンドポイント

| MCP | SSE | POST |
|---|---|---|
| Chrome DevTools | `http://localhost:8095/aidiy_chrome_devtools/sse` | `.../aidiy_chrome_devtools/messages/` |
| Desktop Capture | `http://localhost:8095/aidiy_desktop_capture/sse` | `.../aidiy_desktop_capture/messages/` |
| SQLite          | `http://localhost:8095/aidiy_sqlite/sse`          | `.../aidiy_sqlite/messages/` |
| PostgreSQL      | `http://localhost:8095/aidiy_postgres/sse`        | `.../aidiy_postgres/messages/` |
| Logs            | `http://localhost:8095/aidiy_logs/sse`            | `.../aidiy_logs/messages/` |
| Code Check      | `http://localhost:8095/aidiy_code_check/sse`      | `.../aidiy_code_check/messages/` |
| Backup Check    | `http://localhost:8095/aidiy_backup_check/sse`    | `.../aidiy_backup_check/messages/` |
| Backup Save     | `http://localhost:8095/aidiy_backup_save/sse`     | `.../aidiy_backup_save/messages/` |
| Chrome デバッグポート | `9222` | — |

アクセスは **localhost のみ許可**（127.0.0.1 / ::1）。外部からの接続は 403 で拒否。

---

## ファイル構成

```
backend_mcp/
├── mcp_main.py                    # メイン（FastAPI 上に 8 つの FastMCP を同居）
├── mcp_stdio.py                   # stdio <-> SSE ブリッジ（Codex 向け）
├── mcp_test_chrome.py             # Chrome DevTools MCP 動作確認
├── mcp_test_ss.py                 # Desktop Capture MCP 動作確認
├── mcp_proc/
│   ├── chrome_manager.py          # Chrome プロセス起動・監視
│   ├── chrome_devtools.py         # CDP クライアント（Python 実装）
│   ├── desktop_capture.py         # スクリーンショット取得（pyautogui / PIL）
│   ├── sqlite_query.py            # SQLite DB クエリ（read-only 既定）
│   ├── postgres_query.py          # PostgreSQL クエリ（psycopg 3・read-only 既定）
│   ├── log_tailer.py              # ログ tail・エラー抽出
│   ├── code_checker.py            # 構文/型チェックの subprocess ラッパ
│   ├── backup_check.py            # 変更前/変更後ソース抽出
│   └── backup_save.py             # AiDiy 差分バックアップ実行
├── log_config.py                  # ログ設定（UTF-8 出力対応）
├── pyproject.toml                 # Python 依存関係（uv 管理）
└── uv.lock
```

Node.js / `package.json` / `node_modules` は使用しません（旧構成では使用していたが廃止済み）。

---

## アーキテクチャ

```
MCP クライアント (Claude Agent SDK / Claude CLI / Gemini / Codex 等)
    │
    │  MCP (SSE)           ← Codex は mcp_stdio.py 経由の stdio
    ▼
mcp_main.py (port 8095)
    ├── FastMCP "aidiy_chrome_devtools"  → mcp_proc/chrome_devtools.py (CDPClient)
    │                                        └─ mcp_proc/chrome_manager.py が Chrome を自動起動
    ├── FastMCP "aidiy_desktop_capture"  → mcp_proc/desktop_capture.py (pyautogui / PIL)
    ├── FastMCP "aidiy_sqlite"           → mcp_proc/sqlite_query.py   (backend_server/_data/AiDiy/database.db)
    ├── FastMCP "aidiy_postgres"         → mcp_proc/postgres_query.py (psycopg 3・DSN は環境変数 or 引数)
    ├── FastMCP "aidiy_logs"             → mcp_proc/log_tailer.py     (backend_server/temp/logs, backend_mcp/temp/logs)
    ├── FastMCP "aidiy_code_check"       → mcp_proc/code_checker.py   (py_compile / ruff / npm run type-check)
    ├── FastMCP "aidiy_backup_check"     → mcp_proc/backup_check.py   (変更前/変更後ソース抽出)
    └── FastMCP "aidiy_backup_save"      → mcp_proc/backup_save.py    (差分バックアップ実行)
```

- `mcp_main.py` が 8 つの `FastMCP` インスタンスを生成し、Starlette で同一ポートにマウント
- Chrome 側は `ChromeManager` が `--remote-debugging-port=9222` で subprocess 起動を管理し、最初の SSE 接続時に自動起動
- SQLite クエリは**既定で読み取り専用接続**（`file:...?mode=ro`）。書き込みは `allow_write=True` を明示したときのみ、かつ単一ステートメントに限定
- PostgreSQL クエリも**既定で read-only トランザクション**（`default_transaction_read_only=on`）＋ `statement_timeout=15s`。書き込みは `allow_write=True` を明示したときのみ
- ログ tail は末尾最大 2000 行・正規表現 grep 可。ERROR/Traceback 抽出は前後 2 行の文脈付きで返す
- Code Check は `python -m py_compile` / `python -m ruff check` / `npm run type-check` を timeout 付きで実行

Codex 用の経路:

```
Codex
    │  MCP (stdio)
    ▼
mcp_stdio.py  --sse-url http://localhost:8095/<server>/sse
    │  MCP (SSE)
    ▼
mcp_main.py (port 8095)
```

---

## MCP 設定ファイル

`backend_server/_config/AiDiy_mcp.json` で定義（用途に応じて必要なものだけ列挙してよい）：

```json
{
  "mcpServers": {
    "aidiy_chrome_devtools": {
      "type": "sse",
      "url": "http://localhost:8095/aidiy_chrome_devtools/sse"
    },
    "aidiy_desktop_capture": {
      "type": "sse",
      "url": "http://localhost:8095/aidiy_desktop_capture/sse"
    },
    "aidiy_sqlite": {
      "type": "sse",
      "url": "http://localhost:8095/aidiy_sqlite/sse"
    },
    "aidiy_postgres": {
      "type": "sse",
      "url": "http://localhost:8095/aidiy_postgres/sse"
    },
    "aidiy_logs": {
      "type": "sse",
      "url": "http://localhost:8095/aidiy_logs/sse"
    },
    "aidiy_code_check": {
      "type": "sse",
      "url": "http://localhost:8095/aidiy_code_check/sse"
    },
    "aidiy_backup_check": {
      "type": "sse",
      "url": "http://localhost:8095/aidiy_backup_check/sse"
    },
    "aidiy_backup_save": {
      "type": "sse",
      "url": "http://localhost:8095/aidiy_backup_save/sse"
    }
  }
}
```

- `conf/conf_model.py` の `_load_mcp_config()` が起動時に読み込む
- `AIコア/AIコード_claude.py` の `_load_mcp_servers()` も直接読み込む
- Claude Agent SDK へは `ClaudeAgentOptions(mcp_servers=..., permission_mode="bypassPermissions")` で渡す

---

## 提供ツール一覧

### aidiy_sqlite（自己検証用 SQLite アクセス）

| ツール | 概要 |
|---|---|
| `sqlite_list_tables()` | 全テーブル・VIEW 一覧 |
| `sqlite_describe_table(table_name)` | 列・FK・索引・件数 |
| `sqlite_count(table_name, where=None)` | 件数（`;` を含む where は拒否） |
| `sqlite_query(sql, params=None, max_rows=200, allow_write=False)` | 任意 SQL（既定は read-only） |
| `sqlite_audit_summary(table_name, limit=5)` | 監査フィールドに基づく直近更新 |

### aidiy_postgres（外部 PostgreSQL へのクエリ）

| ツール | 概要 |
|---|---|
| `postgres_server_info(dsn=None)` | バージョン・現在 DB・ユーザー・host/port |
| `postgres_list_databases(dsn=None)` | テンプレート以外の DB 一覧 |
| `postgres_list_schemas(dsn=None)` | ユーザースキーマ一覧（システム系は除外） |
| `postgres_list_tables(schema='public', dsn=None)` | テーブル・VIEW 一覧 |
| `postgres_describe_table(table, schema='public', dsn=None)` | 列・PK・FK・件数 |
| `postgres_count(table, schema='public', where=None, dsn=None)` | 件数 |
| `postgres_query(sql, params=None, max_rows=200, allow_write=False, dsn=None)` | 任意 SQL（既定 read-only） |

接続先は次の優先順で決定:

1. 各呼び出しの `dsn` 引数
2. 環境変数 `AIDIY_PG_DSN`
3. 環境変数 `AIDIY_PG_HOST` / `AIDIY_PG_PORT` / `AIDIY_PG_USER` / `AIDIY_PG_PASSWORD` / `AIDIY_PG_DATABASE` から組み立て

`psycopg` 未導入環境でもサーバー自体は起動する（他 MCP はそのまま使える）。`aidiy_postgres` のツール呼び出し時だけ `uv sync` を促すエラーが返る。

### aidiy_logs（ログ観測）

| ツール | 概要 |
|---|---|
| `logs_list()` | 監視対象ログファイル一覧 |
| `logs_tail(server='server'/'mcp', lines=100, grep=None)` | 末尾 N 行 |
| `logs_recent_errors(server='server'/'mcp', lines=500)` | ERROR/Traceback 抽出＋前後 2 行 |

### aidiy_code_check（構文・型チェック）

| ツール | 概要 |
|---|---|
| `check_list_targets()` | チェック可能な venv / TS プロジェクト |
| `check_python_syntax(file_path, venv_project='backend_server')` | `python -m py_compile` |
| `check_python_ruff(path='backend_server')` | `python -m ruff check` |
| `check_typescript(project='frontend_web')` | `npm run type-check` |

### aidiy_backup_check（バックアップ差分確認）

| ツール | 概要 |
|---|---|
| `backup_info()` | バックアップルートと検出状況 |
| `backup_get_before_after(path, version=None)` | 指定ファイルの変更前/変更後ソースを取得 |
| `backup_list_versions(path)` | 指定ファイルのバックアップ版一覧 |
| `backup_find_changed(from_ts: str, to_ts: Optional[str] = None)` | 指定期間のバックアップに含まれる変更ファイル一覧 |
| `backup_diff_stats(path=None)` | 差分行数などの概要 |

### aidiy_backup_save（バックアップ保存）

| ツール | 概要 |
|---|---|
| `backup_run()` | AiDiy ネイティブの差分バックアップを実行 |
| `backup_diff_scan()` | 保存前の差分スキャン結果を取得 |

Chrome DevTools / Desktop Capture のツールは従来通り（`mcp_test_chrome.py` / `mcp_test_ss.py` で確認可能）。

---

## 起動方法

```bash
# _start.py 経由（推奨）
python _start.py   # 対話形式で バックエンド(mcp) を選択

# 手動起動
cd backend_mcp
.venv/Scripts/python.exe -m uvicorn mcp_main:app --host 0.0.0.0 --port 8095

# uv 経由
cd backend_mcp
uv run uvicorn mcp_main:app --host 0.0.0.0 --port 8095

# Codex 用 stdio ブリッジ（例: Chrome DevTools 側に接続）
cd backend_mcp
.venv/Scripts/python.exe mcp_stdio.py --sse-url http://localhost:8095/aidiy_chrome_devtools/sse
```

---

## 依存関係セットアップ

```bash
# Python 依存関係のみ
cd backend_mcp
uv sync
```

Node.js 側のセットアップは不要です。

---

## 環境変数

| 変数名 | デフォルト | 説明 |
|--------|-----------|------|
| `CHROME_DEBUG_PORT` | `9222` | Chrome デバッグポート |
| `MCP_PORT` | `8095` | MCP サーバーポート |
| `MCP_MOUNT_PATH`    | `/aidiy_chrome_devtools` | Chrome DevTools SSE マウントパス |
| `MCP_DC_MOUNT_PATH` | `/aidiy_desktop_capture` | Desktop Capture SSE マウントパス |
| `MCP_SQ_MOUNT_PATH` | `/aidiy_sqlite`          | SQLite SSE マウントパス |
| `MCP_PG_MOUNT_PATH` | `/aidiy_postgres`        | PostgreSQL SSE マウントパス |
| `MCP_LG_MOUNT_PATH` | `/aidiy_logs`            | Logs SSE マウントパス |
| `MCP_CC_MOUNT_PATH` | `/aidiy_code_check`      | Code Check SSE マウントパス |
| `MCP_BC_MOUNT_PATH` | `/aidiy_backup_check`    | Backup Check SSE マウントパス |
| `MCP_BS_MOUNT_PATH` | `/aidiy_backup_save`     | Backup Save SSE マウントパス |
| `AIDIY_PG_DSN` | （未設定） | PostgreSQL DSN を 1 本で渡す（例: `postgresql://user:pw@host:5432/db`） |
| `AIDIY_PG_HOST` / `AIDIY_PG_PORT` / `AIDIY_PG_USER` / `AIDIY_PG_PASSWORD` / `AIDIY_PG_DATABASE` | （未設定） | DSN が無いとき個別指定 |
| `CHROME_EXECUTABLE` | （未設定） | Chrome 実行ファイルの絶対パス（自動検出失敗時の明示指定） |

---

## Reboot 機構

`temp/reboot_mcp.txt` を作成すると `mcp_main.py` が自身を終了（`_start.py` が自動再起動）。

---

## ログ

- ファイル: `backend_mcp/temp/logs/yyyymmdd.hh0000.mcp_main.log`
- コンソール出力は UTF-8 固定（Windows パイプ経由の文字化け対策済み）
- `log_config.py` の `StreamHandler` は `io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')` でラップ

---

## 注意事項

- `mcp_main.py` は Chrome 未起動の場合、最初のツール呼び出し時に `_ensure_chrome()` が自動起動する
- Chrome プロセスは `ChromeManager`（`mcp_proc/chrome_manager.py`）が単一インスタンスで管理
- `permission_mode="bypassPermissions"` は AIコードエージェント（backend_server 側）の設定であり、MCP サーバー自身のアクセス制御は localhost 制限で行う
- `mcp_stdio.py` 自体は localhost の SSE サーバーへ接続するだけで、Chrome 管理は `mcp_main.py` 側に寄せる
- Desktop Capture はマルチモニターを扱うが、Windows 以外ではウィンドウタイトル指定キャプチャが制限される
- SQLite ツールは `backend_server/_data/AiDiy/database.db` を対象に固定。DB ファイル不在時はエラーを返す
- PostgreSQL は `psycopg[binary]` を使用。未導入時はサーバー起動は継続し、ツール呼び出し時に初めてエラーを返す（`uv sync` 推奨）
- Code Check は副作用なしの検査系のみを実行（ビルドや dev server の起動は行わない）
