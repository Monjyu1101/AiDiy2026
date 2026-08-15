# MCP 活用手順

> 文書: `backend_server,backend_tools,MCP活用手順.md` | 実装: `_config/AiDiy_mcp.json`, `backend_server/AIコア/AIコード_claude.py`

## このメモを使う場面
- Claude Agent SDK や Code CLI から MCP ツールを使う
- ブラウザ操作、DB 参照、ログ確認、コードチェック、バックアップ確認を MCP で行う
- `AiDiy_mcp.json` に MCP サーバーを追加する

## 関連ファイル
- `_config/AiDiy_mcp.json` — Claude Agent SDK に渡す MCP 接続定義
- `backend_server/AIコア/AIコード_claude.py` — Claude Agent SDK で MCP を使う処理
- `backend_tools/tools_main.py` — 19個の SSE MCP サーバー入口
- `backend_tools/mcp_stdio.py` — SSE を stdio client へ中継
- `backend_tools/tools_proc/` — 各 MCP のロジック

## MCP サーバー一覧

| サーバー名 | SSE URL | 主な用途 |
|-----------|---------|---------|
| `aidiy_chrome_devtools` | `http://127.0.0.1:8095/aidiy_chrome_devtools/sse` | ブラウザ操作、DOM取得、ナビゲーション。`session` パラメータ（省略時 `default`）で複数 Chrome を並行セッション管理でき、自動テストの並行実行が可能。使用後は `close_session` で破棄 |
| `aidiy_desktop_capture` | `http://127.0.0.1:8095/aidiy_desktop_capture/sse` | デスクトップのスクリーンショット、クリック、キー入力 |
| `aidiy_sqlite` | `http://127.0.0.1:8095/aidiy_sqlite/sse` | SQLite DB 参照、テーブル/件数確認 |
| `aidiy_postgres` | `http://127.0.0.1:8095/aidiy_postgres/sse` | PostgreSQL 参照、スキーマ/件数確認 |
| `aidiy_logs` | `http://127.0.0.1:8095/aidiy_logs/sse` | ログ tail、Traceback、ERROR 確認 |
| `aidiy_code_check` | `http://127.0.0.1:8095/aidiy_code_check/sse` | Python 構文、ruff、TypeScript 型チェック |
| `aidiy_backup` | `http://127.0.0.1:8095/aidiy_backup/sse` | 差分バックアップ保存 / 確認（HTTP は `save` / `check` に分岐） |
| `aidiy_image_generation` | `http://127.0.0.1:8095/aidiy_image_generation/sse` | AI 画像生成（`auto` は codex → antigravity → openai → freeai → gemini の順でフォールバック） |
| `aidiy_movie_generation` | `http://127.0.0.1:8095/aidiy_movie_generation/sse` | AI 動画生成（Google Gemini Veo、MP4 保存、base64 返却なし） |
| `aidiy_speech_to_text` | `http://127.0.0.1:8095/aidiy_speech_to_text/sse` | 音声認識（speech_recognition / Whisper） |
| `aidiy_text_to_speech` | `http://127.0.0.1:8095/aidiy_text_to_speech/sse` | テキスト音声合成（Edge / OpenAI / Gemini / FreeAI） |
| `aidiy_obs_studio_control` | `http://127.0.0.1:8095/aidiy_obs_studio_control/sse` | OBS Studio 制御（配信、録画、シーン、ソース、音声） |
| `aidiy_ffmpeg_control` | `http://127.0.0.1:8095/aidiy_ffmpeg_control/sse` | ffmpeg / ffprobe / ffplay 実行（動画合成、字幕焼き込み、プレビュー再生） |
| `aidiy_notification_sounds` | `http://127.0.0.1:8095/aidiy_notification_sounds/sse` | 通知音のローカル再生（scene 別の開始 / 終了 / 注意音、`tts` シーンは読み上げ合成） |
| `aidiy_code_agents` | `http://127.0.0.1:8095/aidiy_code_agents/sse` | AI コードエージェント実行（CodeAI CLI 経由） |
| `aidiy_chat_llms` | `http://127.0.0.1:8095/aidiy_chat_llms/sse` | AIチャット の ChatAI を MCP 化。OpenAI / Ollama 互換の `aidiy_chat_completions`（HTTP のみ）の実体 |
| `aidiy_task_agents` | `http://127.0.0.1:8095/aidiy_task_agents/sse` | backend_taskteam の Task API への AIタスク非同期投入、要求/明細状態取得 |
| `aidiy_team_agents` | `http://127.0.0.1:8095/aidiy_team_agents/sse` | backend_taskteam の Team API への AIチーム依頼投入、依頼/要員状態取得 |
| `aidiy_windows_control` | `http://127.0.0.1:8095/aidiy_windows_control/sse` | Windows デスクトップ操作制御（マウス/キーボード、ウィンドウ、プロセス、クリップボード、UI Automation） |

## AiDiy_mcp.json の形式

```json
{
  "mcpServers": {
    "aidiy_chrome_devtools": {
      "type": "sse",
      "url": "http://127.0.0.1:8095/aidiy_chrome_devtools/sse"
    },
    "aidiy_sqlite": {
      "type": "sse",
      "url": "http://127.0.0.1:8095/aidiy_sqlite/sse"
    }
  }
}
```

`type: "sse"` を明示する。環境依存の接続定義は `_config/` 配下で管理し、docs や code_samples へ実キーをコピーしない。

## ツール選択基準

| やりたいこと | 優先 MCP |
|-------------|----------|
| Web 画面の DOM、URL、クリック、スクリーンショット確認 | `aidiy_chrome_devtools` |
| 複数 Chrome でのシステムテスト自動実行・並行実行 | `aidiy_chrome_devtools`（`session` 指定。終了後 `close_session`） |
| Electron やブラウザ外を含む画面確認 | `aidiy_desktop_capture` |
| AiDiy SQLite のテーブル、件数、監査項目確認 | `aidiy_sqlite` |
| 外部 PostgreSQL のスキーマ、件数確認 | `aidiy_postgres` |
| サーバーログや Traceback 確認 | `aidiy_logs` |
| Python 構文、ruff、TypeScript 型チェック | `aidiy_code_check` |
| 差分バックアップ保存 / 確認 | `aidiy_backup` |
| AI 画像生成（プロンプト→ PNG） | `aidiy_image_generation` |
| AI 動画生成（テキスト/画像→ MP4、Gemini Veo） | `aidiy_movie_generation` |
| 音声→テキスト変換（Whisper など） | `aidiy_speech_to_text` |
| テキスト→音声変換（MP3 出力） | `aidiy_text_to_speech` |
| OBS Studio の配信、録画、シーン、ソース、音声制御 | `aidiy_obs_studio_control` |
| ffmpeg / ffprobe による動画合成・字幕焼き込み、ffplay でプレビュー再生 | `aidiy_ffmpeg_control` |
| 長時間処理の開始 / 終了 / 注意をローカル通知音で知らせる | `aidiy_notification_sounds` |
| AI コードエージェント実行（CodeAI CLI 経由） | `aidiy_code_agents` |
| AIチャット の ChatAI をツール／OpenAI 互換 API として呼ぶ | `aidiy_chat_llms` |
| AIタスクへ依頼を投入して非同期実行させる | `aidiy_task_agents` |
| AIチームの要員へ依頼を投入して非同期実行させる | `aidiy_team_agents` |
| マウス/キーボード操作、ウィンドウ制御、プロセス管理 | `aidiy_windows_control` |

SQLite / PostgreSQL は既定 read-only。書き込みが必要でも、まずアプリ API や既存初期化処理で再現できないか確認する。

`aidiy_task_agents.submit`の`task_id`は通常は指定不要で、省略時はbackend_taskteamが`TASK.mmdd.hhmmss`形式で自動採番する。呼出元のIDをAタスク要求まで引き継ぐ必要がある場合だけ指定する。

`aidiy_task_agents.submit`の`project_path` / `ai_name` / `ai_model`も通常は指定不要（null）。未指定時はbackend_taskteamがAIタスク_要求編集ダイアログの新規時と同じ条件、つまり利用者IDの更新最終レコードの値を引き継ぎ、レコードが無ければ規定値（`AiDiy_key.json`の`TASK_AI_NAME` / `TASK_AI_MODEL_do`）を使う。特定のプロジェクトやAIを狙う場合だけ明示指定する（`project_path`の空文字は「プロジェクト空欄」の明示指定として扱う）。

`aidiy_team_agents.submit`は`Aチーム依頼`を`状態=準備開始`で追加する。依頼IDはbackend_taskteamが`TR`＋8桁で自動採番するため指定できない。`member_id`（要員ID、既定`admin`）はAチーム要員の要員IDで、候補は`get_member_list`で確認する。`project_path` / `team_ai_name` / `team_ai_model` / `task_ai_name` / `task_ai_model`は通常は指定不要（null）で、未指定時はbackend_taskteamがAIチーム_依頼編集ダイアログの新規時と同じ条件、つまり要員IDの更新最終レコードの値を引き継ぎ、レコードが無ければ規定値（`AiDiy_key.json`の`CODE_BASE_PATH` / `TEAM_AI_*` / `TASK_AI_*`）を使う。登録後はbackend_taskteamの監視ループ（5秒間隔）が`aidiy_task_agents`へ投入するため、AIタスクを直接作る場合は`aidiy_task_agents`を使う。

## アクセスインターフェース（3種類）

各 MCP は同一ポート（8095）で 3 つのインターフェースを同時提供する。

| インターフェース | 説明 |
|----------------|------|
| **SSE（MCP標準）** | `GET /{mcp_name}/sse` + `POST /{mcp_name}/messages/` — Claude や公式 MCP SSE クライアント |
| **Streamable HTTP** | `POST\|DELETE /{mcp_name}/sse` および `/{mcp_name}/mcp` — Grok の `type=sse` は initialize を `/sse` へ POST する。同じ URL の GET は従来 SSE のまま |
| **stdio gateway** | `mcp_stdio.py --sse-url .../sse` — SSE を stdin/stdout に変換。Codex など stdio 専用 CLI が使う |
| **HTTP POST（FastAPI）** | `POST http://127.0.0.1:8095/{mcp_name}/{method_name}` — REST API として直接呼び出し可能。Swagger UI (`/docs`) で試行できる |

各 MCP の引数仕様 JSON: `GET http://127.0.0.1:8095/{mcp_name}/list`（`/{mcp_name}/docs` は存在しない。Swagger UI は本体の `http://127.0.0.1:8095/docs`）

## Python から利用する場合

SSE クライアントを使わなくても、`requests` で HTTP POST を直接呼べば MCP ツールと同じロジックを実行できる。
自動化スクリプト（`aidiy_automations/`）やバックエンドサーバーのルーターからも同様に利用できる。

```python
import requests

# SQLite テーブル一覧
res = requests.post("http://127.0.0.1:8095/aidiy_sqlite/list_tables", json={})
print(res.json())

# Python 構文チェック
res = requests.post("http://127.0.0.1:8095/aidiy_code_check/check_python_syntax",
                    json={"file_path": "backend_server/core_main.py", "venv_project": "backend_server"})
print(res.json())

# TTS でテキストを読み上げ（サーバー側ローカル再生）
res = requests.post("http://127.0.0.1:8095/aidiy_text_to_speech/synthesize",
                    json={"speech_text": "処理が完了しました", "play": True})
print(res.json())  # {"save_path": "temp/output/....mp3"}

# Chrome で URL を開く
res = requests.post("http://127.0.0.1:8095/aidiy_chrome_devtools/navigate",
                    json={"url": "http://127.0.0.1:8090"})
print(res.json())
```

ツール一覧は `GET http://127.0.0.1:8095/{mcp_name}/list` で確認できる（例: `http://127.0.0.1:8095/aidiy_sqlite/list`）。

## Claude Agent SDK から使う場合

- MCP 接続定義は `_config/AiDiy_mcp.json` に集約する
- `AIコード_claude.py` 側で `conf.models.mcp_servers` を Claude Agent SDK に渡す
- permission は実装側の方針に合わせる。ツール自動許可が必要な場合は `permission_mode` の設定箇所を確認する

## stdio クライアントから使う場合

Codex など SSE を直接扱えないクライアントは `backend_tools/mcp_stdio.py` を使う。

```powershell
backend_tools\.venv\Scripts\python.exe backend_tools\mcp_stdio.py --sse-url http://127.0.0.1:8095/aidiy_sqlite/sse
```

Codex の `url = ...` は streamable HTTP 用なので、AiDiy MCP の SSE URL を直接指定しない。

## 起動・再起動

- `_start.py` 経由なら `backend_tools/temp/reboot_tools.txt` 作成で再起動する
- 手動起動は `cd backend_tools && .venv/Scripts/python.exe -m uvicorn tools_main:app --reload --host 0.0.0.0 --port 8095`
- Docker 構成には `backend_tools` が含まれない。MCP 検証はローカルで別途起動する

## 不調時の切り分け

- 8095 が反応しない場合は `curl http://127.0.0.1:8095/` で本体起動を確認する
- SSE だけ確認する場合は `curl http://127.0.0.1:8095/aidiy_sqlite/sse` を使う
- Grok の handshake は `grok mcp doctor aidiy_sqlite` で確認する（`type=sse` は `/sse` へ initialize を POST する。405 なら `tools_main.py` の POST `/sse` 受け口を疑う）
- Chrome DevTools が不安定な場合は `curl http://127.0.0.1:9222/json` でデバッグポートを確認する
- PostgreSQL MCP だけ失敗する場合は、`psycopg` 未導入、DSN 未設定、外部 DB 接続不可を切り分ける
- `Transport closed` や timeout が続く場合は同じ MCP 呼び出しを繰り返さず、代替確認と未確認範囲を明示する

## バックアップ系 MCP の注意

- `backup_run` が長時間化する場合、編集前なら通常のファイル確認で続行してよい
- 編集後はバックアップ再試行だけに固執せず、リンク確認、BOM/依存確認、検索チェック、差分確認などで補完する
- バックアップ保存/確認系 MCP は自己検証の補助。ツール不調時も、対象ファイル、実行コマンド、検索結果で変更範囲を説明できる状態にする

## 確認方法

```powershell
curl http://127.0.0.1:8095/
curl http://127.0.0.1:8095/aidiy_sqlite/sse
curl http://127.0.0.1:9222/json
```

`/sse` が `text/event-stream` を返せば対象 MCP は起動している。
