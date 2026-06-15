# backend_tools 運用手順

> 文書: `backend_tools,backend_server,運用手順.md` | 実装: `backend_tools/tools_main.py`, `backend_tools/mcp_stdio.py`

## このメモを使う場面

- `backend_tools` を起動する。
- MCP SSE エンドポイント、stdio bridge、環境変数を確認する。
- SQLite / PostgreSQL / Logs / Code Check / Backup 系 MCP の使い分けを確認する。

## 関連ファイル

- `backend_tools/tools_main.py`
- `backend_tools/mcp_stdio.py`
- `backend_tools/tools_proc/`
- `backend_server/_config/AiDiy_mcp.json`
- `backend_server/conf/conf_model.py`
- `backend_server/AIコア/AIコード_claude.py`

## 起動

通常は `_start.py` から backend_tools を選択する。

```powershell
python _start.py
```

手動起動:

```powershell
Set-Location backend_tools
.venv/Scripts/python.exe -m uvicorn tools_main:app --host 0.0.0.0 --port 8095
```

uv 経由:

```powershell
Set-Location backend_tools
uv run uvicorn tools_main:app --host 0.0.0.0 --port 8095
```

Codex など stdio クライアントから使う場合:

```powershell
Set-Location backend_tools
.venv/Scripts/python.exe mcp_stdio.py --sse-url http://localhost:8095/aidiy_chrome_devtools/sse
```

## 依存関係

```powershell
Set-Location backend_tools
uv sync
```

Node.js / `package.json` / `node_modules` は不要。

## アクセスインターフェース（3種類）

`backend_tools` は 1 ポート（8095）で 3 つのインターフェースを同時提供する。

| インターフェース | 説明 | 代表 URL / コマンド |
|----------------|------|-------------------|
| **SSE（MCP標準）** | AI エージェント・MCP クライアントが使う標準トランスポート | `http://localhost:8095/{mcp_name}/sse` |
| **stdio gateway** | `mcp_stdio.py` が SSE を stdin/stdout に変換。Codex 等の stdio 専用 CLI が使う | `mcp_stdio.py --sse-url .../sse` |
| **HTTP POST（FastAPI）** | REST API として直接呼び出せる。Swagger UI (`/docs`) で試行可能。Python から最も簡単に利用できる | `POST http://localhost:8095/{mcp_name}/{method_name}` |

各 MCP の引数仕様は `GET http://localhost:8095/{mcp_name}/docs` で JSON 取得できる。

### Python から利用する例

```python
import requests

# コードチェック
res = requests.post("http://localhost:8095/aidiy_code_check/check_python_ruff",
                    json={"file_path": "backend_server/core_main.py", "venv_project": "backend_server"})
print(res.json())

# バックアップ実行
res = requests.post("http://localhost:8095/aidiy_backup/save/run", json={})
print(res.json())
```

## SSE エンドポイント

| MCP | SSE |
|-----|-----|
| Chrome DevTools | `http://localhost:8095/aidiy_chrome_devtools/sse` |
| Desktop Capture | `http://localhost:8095/aidiy_desktop_capture/sse` |
| SQLite | `http://localhost:8095/aidiy_sqlite/sse` |
| PostgreSQL | `http://localhost:8095/aidiy_postgres/sse` |
| Logs | `http://localhost:8095/aidiy_logs/sse` |
| Code Check | `http://localhost:8095/aidiy_code_check/sse` |
| Backup | `http://localhost:8095/aidiy_backup/sse` |
| Image Generation | `http://localhost:8095/aidiy_image_generation/sse` |
| Speech-to-Text | `http://localhost:8095/aidiy_speech_to_text/sse` |
| Text-to-Speech | `http://localhost:8095/aidiy_text_to_speech/sse` |
| Movie Generation | `http://localhost:8095/aidiy_movie_generation/sse` |
| OBS Studio Control | `http://localhost:8095/aidiy_obs_studio_control/sse` |
| FFmpeg Control | `http://localhost:8095/aidiy_ffmpeg_control/sse` |
| Code Agents | `http://localhost:8095/aidiy_code_agents/sse` |

アクセスは localhost 限定。外部接続は 403。

## 環境変数

| 変数名 | 既定 | 用途 |
|--------|------|------|
| `CHROME_DEBUG_PORT` | `9222` | Chrome デバッグポート |
| `MCP_PORT` | `8095` | MCP サーバーポート |
| `CHROME_EXECUTABLE` | 未設定 | Chrome 実行ファイルの明示指定 |
| `AIDIY_PG_DSN` | 未設定 | PostgreSQL DSN |
| `AIDIY_PG_HOST` など | 未設定 | PostgreSQL 個別接続情報 |

mount path 系の環境変数を使う場合は `tools_main.py` の現行実装を確認する。

## OBS Studio 接続設定

`aidiy_obs_studio_control` の接続情報は `backend_server/_config/aidiy_obs_studio_control.json` で管理する。
ファイルが無ければ初回起動時にデフォルト値（`host=localhost`, `port=4455`, `password=aidiy4455`, `timeout=10`）が自動書き込まれる。
OBS Studio 側の `ツール → WebSocketサーバー設定` と一致させる。

## ffmpeg / ffprobe / ffplay 実行設定

`aidiy_ffmpeg_control` の実行ファイルパスと既定タイムアウトは `backend_server/_config/aidiy_ffmpeg_control.json` で管理する。
ファイルが無ければ初回起動時にデフォルト値（PATH 上の `ffmpeg` / `ffprobe` / `ffplay`、タイムアウト 600 秒）が自動書き込まれる。
PATH 上にない環境ではフルパスへ書き換える。MCP ツールは args_str 一本で各サブコマンドの引数を直接渡す薄いランナーで、ffplay 利用時は `-autoexit` と `-t <秒>` を付けて自然終了させること。

## Reboot

`backend_tools/temp/reboot_mcp.txt` を作成すると `tools_main.py` が自身を終了し、`_start.py` 起動中なら自動再起動される。

## ログ

- `backend_tools/temp/logs/yyyymmdd.hh0000.mcp_main.log`
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
