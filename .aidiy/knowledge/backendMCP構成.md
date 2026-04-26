# backend_mcp 構成

## このメモを使う場面
- `backend_mcp` のファイル配置を整理するとき
- 入口ファイルとロジックファイルを分けたいとき

## 結論
- 入口は `backend_mcp/mcp_main.py` に置く
- Codex 向けの transport 変換入口は `backend_mcp/mcp_stdio.py` に分ける
- 再利用ロジックは `backend_mcp/mcp_proc/` にまとめる
- `mcp_main.py` からは `mcp_proc.<module>` で import する

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

## 提供 MCP と使い分け

| MCP | 用途 |
|-----|------|
| `aidiy_chrome_devtools` | Chrome を CDP で操作して画面検証する |
| `aidiy_desktop_capture` | デスクトップやウィンドウのスクリーンショットを取る |
| `aidiy_sqlite` | AiDiy SQLite DB のテーブル・件数・監査項目を確認する |
| `aidiy_postgres` | 外部 PostgreSQL を read-only 中心に確認する |
| `aidiy_logs` | backend_server / backend_mcp のログ tail とエラー抽出 |
| `aidiy_code_check` | Python 構文、ruff、TypeScript 型チェック |
| `aidiy_backup_check` | 差分バックアップから変更前後を確認する |
| `aidiy_backup_save` | AiDiy ネイティブの差分バックアップを実行する |

SSE URL は `http://localhost:8095/<MCP名>/sse`。Codex など stdio クライアントは `mcp_stdio.py --sse-url ...` でブリッジする。

## 注意点
- `mcp_main.py` は入口として残し、`mcp_proc` へ入れない
- stdio <-> SSE の transport 変換は `mcp_stdio.py` に閉じ込め、`mcp_main.py` の共有 Chrome 管理と混ぜない
- import パスを旧ファイル名のまま残すと起動時に `ModuleNotFoundError` になる
- `_start.py` の `(mcp)` ブラウザ起動ヘルパーも `from mcp_proc.chrome_manager import ChromeManager` に揃える
- 環境によっては `backend_mcp` の仮想環境に `mcp.server` などの依存が欠けていることがあるので、構成変更後は import 確認だけでなく実起動確認も必要
- MCP 設定は `backend_server/_config/AiDiy_mcp.json` で必要なサーバーだけ列挙してよい。使わない MCP を無理に有効化しない。
- SQLite / PostgreSQL は既定 read-only。検証では SELECT / describe / count を優先し、書き込みが必要な場合だけ明示的に許可する。
- `aidiy_postgres` は `psycopg` や DSN がない環境でも他 MCP の起動を妨げない。PostgreSQL ツール呼び出し時のエラーとして扱う。
- Chrome DevTools MCP は Node.js 版ではなく Python CDP 実装。`node_modules` や `package.json` 前提の復旧をしない。
- `mcp_stdio.py` で `ClientSession.call_tool()` へ `req.params.meta` を中継する場合、MCP SDK 1.27 系では `dict` ではなく `RequestParams.Meta` モデルが渡ることがある。`meta` は `model_dump(by_alias=True, exclude_none=True)` 相当で `dict` に正規化してから渡す。未対応だと `mcp.types.RequestParams.Meta() argument after ** must be a mapping, not Meta` が出て、`aidiy_backup_save` などのツール呼び出しがタイムアウトまたは `Transport closed` になる。
- `aidiy_backup_save` の path 確認は、まず `backend_mcp` 直下で `.\.venv\Scripts\python.exe -c "from mcp_proc.backup_save import BackupSave; print(BackupSave().diff_scan())"` を実行し、`root` がプロジェクトルート、`backend_dir` が `backend_server` を指しているかを見る。直接実行が速く成功し、MCP 経由だけ失敗する場合は path より `mcp_stdio.py` の中継処理を疑う。

## FastMCP インスタンスの定義パターン

`mcp_main.py` では 8 本の `FastMCP` インスタンスをひとつのファイルで定義し、Starlette の `Mount` で合成して `mcp_main:app` として uvicorn に渡す。

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "aidiy_chrome_devtools",
    host="0.0.0.0",
    port=MCP_PORT,               # 環境変数 MCP_PORT（デフォルト 8095）
    sse_path=f"{MOUNT}/sse",     # 環境変数 MCP_MOUNT_PATH（デフォルト /aidiy_chrome_devtools）
    message_path=f"{MOUNT}/messages/",
    warn_on_duplicate_tools=False,
)

@mcp.tool()
async def navigate(url: str, tab_id: Optional[str] = None) -> str:
    """指定URLへ移動する"""
    await _ensure_chrome()
    return await cdp.navigate(url, tab_id)
```

新しい MCP を追加する場合は、同ファイル内で `mcp_xx = FastMCP("aidiy_<name>", sse_path=f"{MOUNT_XX}/sse", ...)` を定義し、`@mcp_xx.tool()` でツールを登録してから Starlette の `Mount` ルートに追加する。

## 再起動ウォッチャーの仕組み

`mcp_main.py` の `_setup_reboot_watcher()` が起動時にデーモンスレッドを立ち上げる。

- `backend_mcp/temp/reboot_mcp.txt` を 1 秒ポーリングで監視
- ファイルを検知したら削除して `os._exit(0)` でプロセスを終了
- 外部から `echo. > backend_mcp/temp/reboot_mcp.txt` を置くだけで再起動できる
- `_start.py` が子プロセスの終了を検知して同コマンドで自動再起動する

## Chrome 自動起動の仕組み

`_ensure_chrome()` ヘルパーが、`@mcp.tool()` のある Chrome DevTools 系ツールの先頭から呼ばれる。

```python
async def _ensure_chrome():
    if not chrome.is_running():          # port 9222 への接続試行
        await asyncio.to_thread(chrome.ensure_running)  # Chrome を --remote-debugging-port で起動
```

- `ChromeManager` は `CHROME_EXECUTABLE` 環境変数でパスを上書き可能
- デバッグポートは `CHROME_DEBUG_PORT` 環境変数（デフォルト 9222）
- `_start.py` も起動時に `ChromeManager().ensure_running()` を先行起動として呼ぶ

## PostgreSQL の遅延初期化

`psycopg` 未導入や外部 DB 未設定の環境でも他の 7 MCP の起動を妨げないよう、起動時の `PgQuery()` 例外をキャッチして保存し、ツール呼び出し時だけ `_get_pg()` でエラーを返す。

```python
_pg_q: Optional[PgQuery] = None
try:
    _pg_q = PgQuery()
except PgQueryError as _e:
    _pg_init_error = str(_e)

def _get_pg() -> PgQuery:
    if _pg_q is None:
        raise ValueError(f"aidiy_postgres は初期化されていません: {_pg_init_error}")
    return _pg_q
```

## 新規 MCP サーバーを追加する手順

1. `backend_mcp/mcp_proc/<サーバー名>.py` にツール実装を追加する
2. `backend_mcp/mcp_main.py` に FastMCP アプリを追加し、`mcp_proc.<サーバー名>` を import する
3. `backend_server/_config/AiDiy_mcp.json` に `{ "type": "sse", "url": "http://localhost:8095/<サーバー名>/sse" }` を追加する
4. stdio クライアント（Codex 等）から使う場合は `backend_mcp/mcp_stdio.py` にも `--sse-url` オプションのエントリを確認する
5. `backend_mcp` を再起動して `curl http://localhost:8095/<サーバー名>/sse` で `text/event-stream` が返ることを確認する
6. `backend_mcp/AGENTS.md` の MCP サーバー一覧と、`MCP活用手順.md` のサーバー一覧にも追記する

## 最低限の確認方法
- `cd backend_mcp && .venv/Scripts/python.exe -c "import mcp_main"` で `mcp_main.py` を import できる
- `backend_mcp/.venv/Scripts/python.exe backend_mcp/mcp_stdio.py --help` が動く
- `rg "chrome_manager|chrome_devtools" backend_mcp` で旧 import が残っていない
- `http://localhost:8095/aidiy_sqlite/sse` が接続できる
- `aidiy_backup_save` 修正時は、`BackendMcpBridge.call_tool("backup_diff_scan", {}, RequestParams.Meta(...))` のように `Meta` オブジェクト付きで SSE 経由の呼び出しを確認する
