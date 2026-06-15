# MCP 活用手順

> 文書: `backend_server,backend_tools,MCP活用手順.md` | 実装: `backend_server/_config/AiDiy_mcp.json`, `backend_server/core_router/AIコア/AIコード_claude.py`

## このメモを使う場面
- Claude Agent SDK や Code CLI から MCP ツールを使う
- ブラウザ操作、DB 参照、ログ確認、コードチェック、バックアップ確認を MCP で行う
- `AiDiy_mcp.json` に MCP サーバーを追加する

## 関連ファイル
- `backend_server/_config/AiDiy_mcp.json` — Claude Agent SDK に渡す MCP 接続定義
- `backend_server/core_router/AIコア/AIコード_claude.py` — Claude Agent SDK で MCP を使う処理
- `backend_tools/tools_main.py` — 14個の SSE MCP サーバー入口
- `backend_tools/mcp_stdio.py` — SSE を stdio client へ中継
- `backend_tools/tools_proc/` — 各 MCP のロジック

## MCP サーバー一覧

| サーバー名 | SSE URL | 主な用途 |
|-----------|---------|---------|
| `aidiy_chrome_devtools` | `http://localhost:8095/aidiy_chrome_devtools/sse` | ブラウザ操作、DOM取得、ナビゲーション |
| `aidiy_desktop_capture` | `http://localhost:8095/aidiy_desktop_capture/sse` | デスクトップのスクリーンショット、クリック、キー入力 |
| `aidiy_sqlite` | `http://localhost:8095/aidiy_sqlite/sse` | SQLite DB 参照、テーブル/件数確認 |
| `aidiy_postgres` | `http://localhost:8095/aidiy_postgres/sse` | PostgreSQL 参照、スキーマ/件数確認 |
| `aidiy_logs` | `http://localhost:8095/aidiy_logs/sse` | ログ tail、Traceback、ERROR 確認 |
| `aidiy_code_check` | `http://localhost:8095/aidiy_code_check/sse` | Python 構文、ruff、TypeScript 型チェック |
| `aidiy_backup` | `http://localhost:8095/aidiy_backup/sse` | 差分バックアップ保存 / 確認（HTTP は `save` / `check` に分岐） |
| `aidiy_image_generation` | `http://localhost:8095/aidiy_image_generation/sse` | AI 画像生成（OpenAI / Gemini / FreeAI） |
| `aidiy_movie_generation` | `http://localhost:8095/aidiy_movie_generation/sse` | AI 動画生成（Google Gemini Veo、MP4 保存、base64 返却なし） |
| `aidiy_speech_to_text` | `http://localhost:8095/aidiy_speech_to_text/sse` | 音声認識（speech_recognition / Whisper） |
| `aidiy_text_to_speech` | `http://localhost:8095/aidiy_text_to_speech/sse` | テキスト音声合成（Edge / OpenAI / Gemini / FreeAI） |
| `aidiy_obs_studio_control` | `http://localhost:8095/aidiy_obs_studio_control/sse` | OBS Studio 制御（配信、録画、シーン、ソース、音声） |
| `aidiy_ffmpeg_control` | `http://localhost:8095/aidiy_ffmpeg_control/sse` | ffmpeg / ffprobe / ffplay 実行（動画合成、字幕焼き込み、プレビュー再生） |
| `aidiy_code_agents` | `http://localhost:8095/aidiy_code_agents/sse` | AI コードエージェント実行（CodeAI CLI 経由） |

## AiDiy_mcp.json の形式

```json
{
  "mcpServers": {
    "aidiy_chrome_devtools": {
      "type": "sse",
      "url": "http://localhost:8095/aidiy_chrome_devtools/sse"
    },
    "aidiy_sqlite": {
      "type": "sse",
      "url": "http://localhost:8095/aidiy_sqlite/sse"
    }
  }
}
```

`type: "sse"` を明示する。環境依存の接続定義は `backend_server/_config/` 配下で管理し、docs や code_samples へ実キーをコピーしない。

## ツール選択基準

| やりたいこと | 優先 MCP |
|-------------|----------|
| Web 画面の DOM、URL、クリック、スクリーンショット確認 | `aidiy_chrome_devtools` |
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
| AI コードエージェント実行（CodeAI CLI 経由） | `aidiy_code_agents` |

SQLite / PostgreSQL は既定 read-only。書き込みが必要でも、まずアプリ API や既存初期化処理で再現できないか確認する。

## アクセスインターフェース（3種類）

各 MCP は同一ポート（8095）で 3 つのインターフェースを同時提供する。

| インターフェース | 説明 |
|----------------|------|
| **SSE（MCP標準）** | `http://localhost:8095/{mcp_name}/sse` — AI エージェント・MCP クライアントが接続する標準トランスポート |
| **stdio gateway** | `mcp_stdio.py --sse-url .../sse` — SSE を stdin/stdout に変換。Codex など stdio 専用 CLI が使う |
| **HTTP POST（FastAPI）** | `POST http://localhost:8095/{mcp_name}/{method_name}` — REST API として直接呼び出し可能。Swagger UI (`/docs`) で試行できる |

各 MCP の引数仕様 JSON: `GET http://localhost:8095/{mcp_name}/docs`

## Python から利用する場合

SSE クライアントを使わなくても、`requests` で HTTP POST を直接呼べば MCP ツールと同じロジックを実行できる。
自動化スクリプト（`aidiy_automations/`）やバックエンドサーバーのルーターからも同様に利用できる。

```python
import requests

# SQLite テーブル一覧
res = requests.post("http://localhost:8095/aidiy_sqlite/list_tables", json={})
print(res.json())

# Python 構文チェック
res = requests.post("http://localhost:8095/aidiy_code_check/check_python_syntax",
                    json={"file_path": "backend_server/core_main.py", "venv_project": "backend_server"})
print(res.json())

# TTS でテキストを読み上げ（サーバー側ローカル再生）
res = requests.post("http://localhost:8095/aidiy_text_to_speech/synthesize",
                    json={"speech_text": "処理が完了しました", "play": True})
print(res.json())  # {"save_path": "temp/output/....mp3"}

# Chrome で URL を開く
res = requests.post("http://localhost:8095/aidiy_chrome_devtools/navigate",
                    json={"url": "http://localhost:8090"})
print(res.json())
```

ツール一覧は `GET http://localhost:8095/{mcp_name}/list` で確認できる（例: `http://localhost:8095/aidiy_sqlite/list`）。

## Claude Agent SDK から使う場合

- MCP 接続定義は `backend_server/_config/AiDiy_mcp.json` に集約する
- `AIコード_claude.py` 側で `conf.models.mcp_servers` を Claude Agent SDK に渡す
- permission は実装側の方針に合わせる。ツール自動許可が必要な場合は `permission_mode` の設定箇所を確認する

## stdio クライアントから使う場合

Codex など SSE を直接扱えないクライアントは `backend_tools/mcp_stdio.py` を使う。

```powershell
backend_tools\.venv\Scripts\python.exe backend_tools\mcp_stdio.py --sse-url http://localhost:8095/aidiy_sqlite/sse
```

Codex の `url = ...` は streamable HTTP 用なので、AiDiy MCP の SSE URL を直接指定しない。

## 起動・再起動

- `_start.py` 経由なら `backend_tools/temp/reboot_mcp.txt` 作成で再起動する
- 手動起動は `cd backend_tools && .venv/Scripts/python.exe -m uvicorn tools_main:app --reload --host 0.0.0.0 --port 8095`
- Docker 構成には `backend_tools` が含まれない。MCP 検証はローカルで別途起動する

## 不調時の切り分け

- 8095 が反応しない場合は `curl http://localhost:8095/` で本体起動を確認する
- SSE だけ確認する場合は `curl http://localhost:8095/aidiy_sqlite/sse` を使う
- Chrome DevTools が不安定な場合は `curl http://localhost:9222/json` でデバッグポートを確認する
- PostgreSQL MCP だけ失敗する場合は、`psycopg` 未導入、DSN 未設定、外部 DB 接続不可を切り分ける
- `Transport closed` や timeout が続く場合は同じ MCP 呼び出しを繰り返さず、代替確認と未確認範囲を明示する

## バックアップ系 MCP の注意

- `backup_run` が長時間化する場合、編集前なら通常のファイル確認で続行してよい
- 編集後はバックアップ再試行だけに固執せず、リンク確認、BOM/依存確認、検索チェック、差分確認などで補完する
- バックアップ保存/確認系 MCP は自己検証の補助。ツール不調時も、対象ファイル、実行コマンド、検索結果で変更範囲を説明できる状態にする

## 確認方法

```powershell
curl http://localhost:8095/
curl http://localhost:8095/aidiy_sqlite/sse
curl http://localhost:9222/json
```

`/sse` が `text/event-stream` を返せば対象 MCP は起動している。
