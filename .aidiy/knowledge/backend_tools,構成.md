# backend_tools 構成

> 文書: `backend_tools,構成.md` | 実装: `backend_tools/tools_main.py`, `backend_tools/mcp_stdio.py`

## このメモを使う場面
- `backend_tools` の入口、SSE サーバー、stdio bridge の役割を確認する
- MCP サーバーを追加、分割、修正する
- Codex など stdio クライアントから AiDiy MCP を使う経路を調査する

## 構成方針
- 常駐入口は `backend_tools/tools_main.py`
- Codex など stdio クライアント向けの SSE 変換入口は `backend_tools/mcp_stdio.py`
- 再利用ロジックは `backend_tools/tools_proc/` に置く
- `tools_main.py` からは `tools_proc.<module>` として import する
- `tools_main.py` は 18 本の `FastMCP` インスタンスを Starlette の `Mount` で合成し、`tools_main:app` として uvicorn に渡す

## 関連ファイル
- `backend_tools/tools_main.py`
- `backend_tools/mcp_stdio.py`
- `backend_tools/tools_proc/chrome_manager.py`
- `backend_tools/tools_proc/chrome_devtools.py`
- `backend_tools/tools_proc/sqlite_query.py`
- `backend_tools/tools_proc/postgres_query.py`
- `backend_tools/tools_proc/log_tailer.py`
- `backend_tools/tools_proc/code_checker.py`
- `backend_tools/tools_proc/backup.py`
- `backend_tools/tools_proc/image_generation.py`
- `backend_tools/tools_proc/movie_generation.py`
- `backend_tools/tools_proc/speech_to_text.py`
- `backend_tools/tools_proc/text_to_speech.py`
- `backend_tools/tools_proc/obs_studio_control.py`
- `backend_tools/tools_proc/ffmpeg_control.py`
- `backend_tools/tools_proc/code_agents.py`
- `backend_tools/tools_proc/windows_control.py`
- `backend_server/_config/AiDiy_mcp.json`
- `_start.py`

## アクセスインターフェース

各 MCP は **3 つのインターフェース**を同一ポート（8095）で同時提供する。

| トランスポート | アクセス方法 | 用途 |
|----------------|-------------|------|
| **SSE Transport** | `http://localhost:8095/{mcp_name}/sse` | AI エージェント・MCP クライアントが接続 |
| **Streamable HTTP Transport** | `POST http://localhost:8095/{mcp_name}/{method_name}` | Python / curl / 自動化スクリプトが直接呼び出し |
| **stdio gateway** | `mcp_stdio.py --sse-url .../sse` | Codex など stdio 専用の Code CLI が経由 |

MCP一覧: `GET http://localhost:8095/` — 全 MCP 名を返す。  
ツール一覧: `GET http://localhost:8095/{mcp_name}/list` — ツール名・説明・引数スキーマを JSON で返す。  
死活確認: `GET http://localhost:8095/{mcp_name}/ping` — `{"status":"ok"}` を返す。  
初期化: `POST http://localhost:8095/{mcp_name}/initialize` — capabilities を返す。

HTTP POST は SSE とまったく同じロジックを呼ぶ。AI エージェント経由でなくても Python スクリプトや `backend_tools/aidiy_automations/` から直接利用できる。

```python
import requests
# SQLite のテーブル一覧を取得する例
res = requests.post("http://localhost:8095/aidiy_sqlite/list_tables", json={})
print(res.json())

# TTS でテキストを読み上げる例（サーバー側ローカル再生）
res = requests.post("http://localhost:8095/aidiy_text_to_speech/synthesize",
                    json={"speech_text": "処理が完了しました", "play": True})
print(res.json())  # {"save_path": "..."}
```

## 提供 MCP

| MCP | 用途 | SSE URL |
|-----|------|---------|
| `aidiy_chrome_devtools` | Chrome CDP で画面検証 | `http://localhost:8095/aidiy_chrome_devtools/sse` |
| `aidiy_desktop_capture` | デスクトップ/ウィンドウのスクリーンショット | `http://localhost:8095/aidiy_desktop_capture/sse` |
| `aidiy_sqlite` | AiDiy SQLite DB の確認 | `http://localhost:8095/aidiy_sqlite/sse` |
| `aidiy_postgres` | 外部 PostgreSQL の確認 | `http://localhost:8095/aidiy_postgres/sse` |
| `aidiy_logs` | backend_server / backend_tools のログ確認 | `http://localhost:8095/aidiy_logs/sse` |
| `aidiy_code_check` | Python 構文、ruff、TypeScript 型チェック | `http://localhost:8095/aidiy_code_check/sse` |
| `aidiy_backup` | 差分バックアップ保存 / 確認。HTTP は `save` / `check` に分岐 | `http://localhost:8095/aidiy_backup/sse` |
| `aidiy_image_generation` | AI 画像生成（OpenAI / Gemini / FreeAI） | `http://localhost:8095/aidiy_image_generation/sse` |
| `aidiy_speech_to_text` | 音声認識（speech_recognition / Whisper） | `http://localhost:8095/aidiy_speech_to_text/sse` |
| `aidiy_text_to_speech` | テキスト音声合成（Edge / OpenAI / Gemini / FreeAI） | `http://localhost:8095/aidiy_text_to_speech/sse` |
| `aidiy_obs_studio_control` | OBS Studio WebSocket 制御 | `http://localhost:8095/aidiy_obs_studio_control/sse` |
| `aidiy_ffmpeg_control` | ffmpeg / ffprobe / ffplay 実行（動画合成、字幕焼き込み、プレビュー再生） | `http://localhost:8095/aidiy_ffmpeg_control/sse` |
| `aidiy_movie_generation` | AI 動画生成（Google Gemini Veo、MP4 保存、base64 返却なし） | `http://localhost:8095/aidiy_movie_generation/sse` |
| `aidiy_code_agents` | AI コードエージェント実行（CodeAI CLI 経由） | `http://localhost:8095/aidiy_code_agents/sse` |
| `aidiy_task_agents` | backend_task API への AIタスク非同期投入、要求/明細状態取得 | `http://localhost:8095/aidiy_task_agents/sse` |
| `aidiy_windows_control` | Windows デスクトップ操作制御（マウス/キーボード、ウィンドウ、プロセス、クリップボード、UI Automation） | `http://localhost:8095/aidiy_windows_control/sse` |

## 新規 MCP サーバー追加手順

### コード変更
1. `backend_tools/tools_proc/<サーバー名>.py` に処理を実装する（`<XxxError>` 例外クラスもセットで定義）
2. `backend_tools/tools_main.py` に以下を追加する
   - `from tools_proc.<サーバー名> import ...` の import
   - `MOUNT_<略号> = os.environ.get("MCP_<略号>_MOUNT_PATH", "/aidiy_<name>")`
   - インスタンス生成（例: `xx = ImageGeneration()`）
   - `mcp_<略号> = FastMCP("aidiy_<name>", host="0.0.0.0", port=MCP_PORT, sse_path=..., message_path=..., warn_on_duplicate_tools=False)`
   - `@mcp_<略号>.tool()` でツール登録
   - Starlette `routes` に `*mcp_<略号>.sse_app().routes` を追加
   - 起動ログに `logger.info(f"... SSE : http://localhost:{MCP_PORT}{MOUNT_<略号>}/sse")` を追加
3. `backend_server/_config/AiDiy_mcp.json` の `mcpServers` に `"aidiy_<name>": {"type": "sse", "url": "..."}` を追加する
4. stdio クライアントから使う場合は `mcp_stdio.py --sse-url http://localhost:8095/aidiy_<name>/sse` で中継できることを確認する

### ドキュメント更新（漏れやすいので必ず全部見る）
5. **本ファイル** (`backend_tools,構成.md`) の「提供 MCP」テーブルと「関連ファイル」リストに新規エントリを追加する
6. `backend_tools/AGENTS.md` の「提供 MCP」「ファイル構成」テーブル、概要文の「N 個の MCP サーバー」を更新する
7. ルート `AGENTS.md` の「ディレクトリ概要」と「MCP 概要」テーブル、「N つの MCP サーバー」を更新する
8. ルート `CLAUDE.md` の「**Backend MCP**: N 個の MCP サーバー」記載と内訳を更新する
9. `.aidiy/knowledge/backend_server,backend_tools,MCP活用手順.md` の「MCP サーバー一覧」「ツール選択基準」テーブル、`tools_main.py` の N 個記載を更新する
10. `.aidiy/knowledge/backend_tools,backend_server,運用手順.md` の「SSE エンドポイント」テーブルを更新する
11. `frontend_web/public/X自己紹介/index.html`（人間向け紹介ページ）の以下を更新する:
    - hero タグ行の `MCP Hub ×N` 表記
    - Feature Overview の `MCP Hub × N + Multi CLI` カード説明
    - Current Numbers の `data-count="N"` と stat-sub 内訳
    - Architecture Stack の `🔌 MCP サーバー (統合)` 説明と `SSE × N` バッジ
    - `<!-- 7. MCP Hub × N + Multi CLI -->` セクションのタイトル / サブタイトル / 各 architecture-item カード（新規 MCP 分を追加）
    - Self-Verification Loop の `MCP N サーバーの連携` 表記

### 確認
12. `backend_tools` 再起動後 `curl http://localhost:8095/aidiy_<name>/sse` が `text/event-stream` を返すか確認
13. Hermes / Claude CLI で `mcp list` 相当を実行し、新規サーバーが `ok` 表示になることを確認

## 再起動ウォッチャー

`tools_main.py` の `_setup_reboot_watcher()` が `backend_tools/temp/reboot_tools.txt` を監視する。ファイル検知後に削除して `os._exit(0)` し、`_start.py` が子プロセス終了を検知して再起動する。

手動で再起動したい場合:

```powershell
New-Item -ItemType File backend_tools\temp\reboot_tools.txt -Force
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

- `tools_main.py` は入口として残し、`tools_proc` へ入れない
- stdio と SSE の transport 変換は `mcp_stdio.py` に閉じ込める
- SQLite / PostgreSQL は既定 read-only。検証は SELECT / describe / count を優先する
- Chrome DevTools MCP は Python CDP 実装。Node.js 版 `chrome-devtools-mcp` 前提で復旧しない
- `aidiy_backup` の path 問題は、まず `backend_tools` 直下で `BackupSave().diff_scan()` を直接実行して root / backend_dir を確認する

## 確認方法

```powershell
cd backend_tools
.venv\Scripts\python.exe -c "import tools_main"
.venv\Scripts\python.exe mcp_stdio.py --help
curl http://localhost:8095/aidiy_sqlite/sse
curl http://localhost:9222/json
```

追加/移動後は `rg "chrome_manager|chrome_devtools" backend_tools` で旧 import が残っていないか確認する。
