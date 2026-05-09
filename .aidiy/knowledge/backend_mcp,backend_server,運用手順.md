# backend_mcp 運用手順

> 文書: `backend_mcp,backend_server,運用手順.md` | 実装: `backend_mcp/mcp_main.py`, `backend_mcp/mcp_stdio.py`

## このメモを使う場面

- `backend_mcp` を起動する。
- MCP SSE エンドポイント、stdio bridge、環境変数を確認する。
- SQLite / PostgreSQL / Logs / Code Check / Backup 系 MCP の使い分けを確認する。

## 関連ファイル

- `backend_mcp/mcp_main.py`
- `backend_mcp/mcp_stdio.py`
- `backend_mcp/mcp_proc/`
- `backend_server/_config/AiDiy_mcp.json`
- `backend_server/conf/conf_model.py`
- `backend_server/AIコア/AIコード_claude.py`

## 起動

通常は `_start.py` から backend_mcp を選択する。

```powershell
python _start.py
```

手動起動:

```powershell
Set-Location backend_mcp
.venv/Scripts/python.exe -m uvicorn mcp_main:app --host 0.0.0.0 --port 8095
```

uv 経由:

```powershell
Set-Location backend_mcp
uv run uvicorn mcp_main:app --host 0.0.0.0 --port 8095
```

Codex など stdio クライアントから使う場合:

```powershell
Set-Location backend_mcp
.venv/Scripts/python.exe mcp_stdio.py --sse-url http://localhost:8095/aidiy_chrome_devtools/sse
```

## 依存関係

```powershell
Set-Location backend_mcp
uv sync
```

Node.js / `package.json` / `node_modules` は不要。

## SSE エンドポイント

| MCP | SSE |
|-----|-----|
| Chrome DevTools | `http://localhost:8095/aidiy_chrome_devtools/sse` |
| Desktop Capture | `http://localhost:8095/aidiy_desktop_capture/sse` |
| SQLite | `http://localhost:8095/aidiy_sqlite/sse` |
| PostgreSQL | `http://localhost:8095/aidiy_postgres/sse` |
| Logs | `http://localhost:8095/aidiy_logs/sse` |
| Code Check | `http://localhost:8095/aidiy_code_check/sse` |
| Backup Check | `http://localhost:8095/aidiy_backup_check/sse` |
| Backup Save | `http://localhost:8095/aidiy_backup_save/sse` |
| Image Generation | `http://localhost:8095/aidiy_image_generation/sse` |
| Speech-to-Text | `http://localhost:8095/aidiy_speech_to_text/sse` |
| Text-to-Speech | `http://localhost:8095/aidiy_text_to_speech/sse` |

アクセスは localhost 限定。外部接続は 403。

## 環境変数

| 変数名 | 既定 | 用途 |
|--------|------|------|
| `CHROME_DEBUG_PORT` | `9222` | Chrome デバッグポート |
| `MCP_PORT` | `8095` | MCP サーバーポート |
| `CHROME_EXECUTABLE` | 未設定 | Chrome 実行ファイルの明示指定 |
| `AIDIY_PG_DSN` | 未設定 | PostgreSQL DSN |
| `AIDIY_PG_HOST` など | 未設定 | PostgreSQL 個別接続情報 |

mount path 系の環境変数を使う場合は `mcp_main.py` の現行実装を確認する。

## Reboot

`backend_mcp/temp/reboot_mcp.txt` を作成すると `mcp_main.py` が自身を終了し、`_start.py` 起動中なら自動再起動される。

## ログ

- `backend_mcp/temp/logs/yyyymmdd.hh0000.mcp_main.log`
- console 出力は UTF-8 固定。
- ログ確認自体は `aidiy_logs` MCP でも行える。

## 注意点

- Chrome は最初のツール呼び出し時に `_ensure_chrome()` が起動確認する。
- Chrome プロセスは `ChromeManager` が単一インスタンスで管理する。
- SQLite は `backend_server/_data/AiDiy/database.db` を対象にする。
- PostgreSQL は `psycopg[binary]` 未導入でもサーバー起動は継続し、PostgreSQL ツール呼び出し時にエラーを返す。
- Code Check は副作用なしの検査系のみを実行する。build や dev server 起動はしない。
- `permission_mode="bypassPermissions"` は backend_server 側の AIコードエージェント設定であり、MCP サーバー自身は localhost 制限で守る。

## 使い分け

MCP の選択基準は `MCP活用手順.md` を使う。
サーバー構成や新規 MCP 追加は `backendMCP構成.md` を使う。
