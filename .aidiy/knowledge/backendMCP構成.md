# backend_mcp 構成

## このメモを使う場面
- `backend_mcp` の入口、SSE サーバー、stdio bridge の役割を確認する
- MCP サーバーを追加、分割、修正する
- Codex など stdio クライアントから AiDiy MCP を使う経路を調査する

## 構成方針
- 常駐入口は `backend_mcp/mcp_main.py`
- Codex など stdio クライアント向けの SSE 変換入口は `backend_mcp/mcp_stdio.py`
- 再利用ロジックは `backend_mcp/mcp_proc/` に置く
- `mcp_main.py` からは `mcp_proc.<module>` として import する
- `mcp_main.py` は 8 本の `FastMCP` インスタンスを Starlette の `Mount` で合成し、`mcp_main:app` として uvicorn に渡す

## 関連ファイル
- `backend_mcp/mcp_main.py`
- `backend_mcp/mcp_stdio.py`
- `backend_mcp/mcp_proc/chrome_manager.py`
- `backend_mcp/mcp_proc/chrome_devtools.py`
- `backend_mcp/mcp_proc/sqlite_query.py`
- `backend_mcp/mcp_proc/postgres_query.py`
- `backend_mcp/mcp_proc/log_tailer.py`
- `backend_mcp/mcp_proc/code_checker.py`
- `backend_mcp/mcp_proc/backup_check.py`
- `backend_mcp/mcp_proc/backup_save.py`
- `backend_server/_config/AiDiy_mcp.json`
- `_start.py`

## 提供 MCP

| MCP | 用途 | SSE URL |
|-----|------|---------|
| `aidiy_chrome_devtools` | Chrome CDP で画面検証 | `http://localhost:8095/aidiy_chrome_devtools/sse` |
| `aidiy_desktop_capture` | デスクトップ/ウィンドウのスクリーンショット | `http://localhost:8095/aidiy_desktop_capture/sse` |
| `aidiy_sqlite` | AiDiy SQLite DB の確認 | `http://localhost:8095/aidiy_sqlite/sse` |
| `aidiy_postgres` | 外部 PostgreSQL の確認 | `http://localhost:8095/aidiy_postgres/sse` |
| `aidiy_logs` | backend_server / backend_mcp のログ確認 | `http://localhost:8095/aidiy_logs/sse` |
| `aidiy_code_check` | Python 構文、ruff、TypeScript 型チェック | `http://localhost:8095/aidiy_code_check/sse` |
| `aidiy_backup_check` | 差分バックアップ確認 | `http://localhost:8095/aidiy_backup_check/sse` |
| `aidiy_backup_save` | AiDiy 差分バックアップ実行 | `http://localhost:8095/aidiy_backup_save/sse` |

## 新規 MCP サーバー追加手順

1. `backend_mcp/mcp_proc/<サーバー名>.py` に処理を実装する
2. `backend_mcp/mcp_main.py` に `FastMCP("aidiy_<name>", ...)` を追加し、`@mcp_xxx.tool()` でツール登録する
3. Starlette の `Mount` に `/aidiy_<name>` を追加する
4. `backend_server/_config/AiDiy_mcp.json` に必要なサーバーだけ URL を追加する
5. stdio クライアントから使う場合は `mcp_stdio.py --sse-url http://localhost:8095/aidiy_<name>/sse` で中継できることを確認する
6. `backend_mcp/AGENTS.md` と `MCP活用手順.md` のサーバー一覧を更新する

## 再起動ウォッチャー

`mcp_main.py` の `_setup_reboot_watcher()` が `backend_mcp/temp/reboot_mcp.txt` を監視する。ファイル検知後に削除して `os._exit(0)` し、`_start.py` が子プロセス終了を検知して再起動する。

手動で再起動したい場合:

```powershell
New-Item -ItemType File backend_mcp\temp\reboot_mcp.txt -Force
```

## Chrome 自動起動

Chrome DevTools 系ツールは `_ensure_chrome()` で Chrome の起動状態を確認する。未起動なら `ChromeManager.ensure_running()` が `--remote-debugging-port` 付きで起動する。

- Chrome パス上書き: `CHROME_EXECUTABLE`
- デバッグポート: `CHROME_DEBUG_PORT`（既定 `9222`）
- `_start.py` も起動時に Chrome を先行起動する

## PostgreSQL の遅延初期化

`aidiy_postgres` は `psycopg` 未導入や DSN 未設定でも他 MCP の起動を妨げない。起動時の `PgQuery()` 例外を保存し、PostgreSQL ツール呼び出し時にだけ `_get_pg()` でエラー化する。

## stdio bridge の注意点

- Codex の `url = ...` は streamable HTTP 用。AiDiy の SSE エンドポイントは `mcp_stdio.py` を挟む
- `ClientSession.call_tool()` へ `req.params.meta` を中継する場合、MCP SDK 1.27 系では `RequestParams.Meta` モデルが渡ることがある。`model_dump(by_alias=True, exclude_none=True)` 相当で `dict` に正規化してから渡す
- 未対応だと `argument after ** must be a mapping, not Meta`、`Transport closed`、タイムアウトとして見えることがある

## 注意点

- `mcp_main.py` は入口として残し、`mcp_proc` へ入れない
- stdio と SSE の transport 変換は `mcp_stdio.py` に閉じ込める
- SQLite / PostgreSQL は既定 read-only。検証は SELECT / describe / count を優先する
- Chrome DevTools MCP は Python CDP 実装。Node.js 版 `chrome-devtools-mcp` 前提で復旧しない
- `aidiy_backup_save` の path 問題は、まず `backend_mcp` 直下で `BackupSave().diff_scan()` を直接実行して root / backend_dir を確認する

## 確認方法

```powershell
cd backend_mcp
.venv\Scripts\python.exe -c "import mcp_main"
.venv\Scripts\python.exe mcp_stdio.py --help
curl http://localhost:8095/aidiy_sqlite/sse
curl http://localhost:9222/json
```

追加/移動後は `rg "chrome_manager|chrome_devtools" backend_mcp` で旧 import が残っていないか確認する。
