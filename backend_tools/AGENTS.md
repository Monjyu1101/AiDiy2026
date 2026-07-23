# backend_tools 実装概要

## 本書の目的

このファイルは `backend_tools` の構成、提供 MCP、実装入口を示す概要ドキュメントです。
起動、依存関係、SSE URL、環境変数、運用手順は `.aidiy/knowledge` に移動しています。
AI エージェントは、本書に個別手順や一時的な作業メモを追記しないでください。
業務システム機能追加は `../docs/` の開発ガイドを優先し、コアシステム機能調整は `../.aidiy/knowledge/_index.md` を入口にします。

## HowTo 参照先

| 目的 | 参照先 |
|------|--------|
| 起動、stdio bridge、環境変数、ログ | [`../.aidiy/knowledge/backend_tools,backend_server,運用手順.md`](../.aidiy/knowledge/backend_tools,backend_server,運用手順.md) |
| MCP サーバー構成、新規 MCP 追加 | [`../.aidiy/knowledge/backend_tools,構成.md`](../.aidiy/knowledge/backend_tools,構成.md) |
| MCP の使い分け、AI エージェントからの利用 | [`../.aidiy/knowledge/backend_server,backend_tools,MCP活用手順.md`](../.aidiy/knowledge/backend_server,backend_tools,MCP活用手順.md) |
| Code CLI 側の MCP 設定 | [`../.aidiy/knowledge/command_hermes,backend_tools,CodeCLI_MCP設定.md`](../.aidiy/knowledge/command_hermes,backend_tools,CodeCLI_MCP設定.md) |

## 概要

`backend_tools` はポート `8095` 上で 18 個の MCP サーバーを同居させる FastMCP アプリケーションです。
ブラウザ操作、デスクトップキャプチャ、DB確認、ログ確認、コードチェック、バックアップ確認、画像/動画生成、音声認識/合成、OBS / ffmpeg 制御、通知音再生、コードエージェント実行、チャット LLM 実行、AIタスク非同期投入、Windows デスクトップ操作制御を AI エージェントから利用できるようにします。
加えて OpenAI / Ollama 互換の標準チャットインターフェース `aidiy_chat_completions` を HTTP で提供します。

## 提供 MCP

| MCP | 役割 |
|-----|------|
| `aidiy_chrome_devtools` | Chrome を CDP で操作するブラウザ自動化（`session` パラメータで複数 Chrome の並行セッション管理。通常は省略= `default`。指定時は使用後に `close_session` で破棄） |
| `aidiy_desktop_capture` | OS スクリーンショット取得 |
| `aidiy_sqlite` | AiDiy SQLite DB の read-only 中心クエリ |
| `aidiy_postgres` | 外部 PostgreSQL の read-only 中心クエリ |
| `aidiy_logs` | `backend_server` / `backend_tools` のログ観測 |
| `aidiy_code_check` | Python 構文、ruff、TypeScript 型チェック |
| `aidiy_backup` | 差分バックアップ保存 / 確認（HTTP は `save` / `check` に分岐） |
| `aidiy_image_generation` | AI 画像生成（OpenAI gpt-image / DALL-E、Gemini、FreeAI、Codex CLI、Antigravity CLI） |
| `aidiy_movie_generation` | AI 動画生成（Google Gemini Veo、MP4 保存、base64 返却なし） |
| `aidiy_speech_to_text` | 音声認識（speech_recognition、OpenAI Whisper） |
| `aidiy_text_to_speech` | テキスト音声合成（Edge / OpenAI / Gemini / FreeAI、MP3 出力） |
| `aidiy_obs_studio_control` | OBS Studio WebSocket 制御（配信、録画、シーン、ソース、音声） |
| `aidiy_ffmpeg_control` | ffmpeg / ffprobe / ffplay 実行（動画合成、字幕焼き込み、プレビュー再生） |
| `aidiy_notification_sounds` | 通知音のローカル再生（scene 別の開始 / 終了 / 注意音、`tts` シーンは text_to_speech で読み上げ合成） |
| `aidiy_code_agents` | AI コードエージェント実行（CodeAI CLI 経由） |
| `aidiy_chat_llms` | AI チャット LLM 実行（AIチャット.py 系 ChatAI 経由 / `aidiy_code_agents` 互換 IF） |
| `aidiy_task_agents` | backend_task API への AIタスク非同期投入。`submit`の`task_id`は通常省略し、外部IDを引き継ぐ場合だけ指定 |
| `aidiy_windows_control` | Windows デスクトップ操作制御（マウス/キーボード、ウィンドウ、プロセス、クリップボード、UI Automation 要素操作） |

`aidiy_chat_llms` は SSE / Streamable HTTP / stdio の 3 トランスポートに対応します。
さらに `aidiy_chat_completions`（HTTP のみ）が OpenAI Chat Completions / Ollama 互換の標準チャットインターフェースを提供し、同じ ChatAI をバックエンドに使います。
OpenAI SDK / Ollama クライアントの `base_url` に `http://localhost:8095/aidiy_chat_completions/v1` を指定して利用できます。

| 標準チャット IF | エンドポイント |
|-----------------|----------------|
| チャット補完（OpenAI 標準） | `POST /aidiy_chat_completions/v1/chat/completions` |
| モデル一覧（ai_name 一覧） | `GET /aidiy_chat_completions/v1/models` |

## ファイル構成

| パス | 役割 |
|------|------|
| `tools_main.py` | FastAPI 上に 18 個の FastMCP を同居 |
| `mcp_stdio.py` | stdio <-> SSE bridge |
| `tests/` | MCP / HTTP API のテスト、動作確認スクリプト |
| `aidiy_automations/` | MCP / HTTP API を組み合わせる自動化スクリプト |
| `aidiy_automations/ビデオページ生成_紹介.py` | 一人アバター（AiDiy）による紹介・ガイド型ビデオ自動生成（version: "mcp"、short/long narration 形式） |
| `aidiy_automations/ビデオページ生成_解説.py` | 二人アバター（男女）の掛け合いによる解説・ニュース型ビデオ自動生成（version: "duo-v2"、dialogue 形式） |
| `tools_proc/chrome_manager.py` | Chrome プロセス管理 |
| `tools_proc/chrome_sessions.py` | Chrome セッションレジストリ（session 名 → ポート・プロファイルの辞書管理、`temp/_chrome_sessions.json` に永続化） |
| `tools_proc/chrome_devtools.py` | CDP client |
| `tools_proc/desktop_capture.py` | スクリーンショット取得 |
| `tools_proc/sqlite_query.py` | SQLite query |
| `tools_proc/postgres_query.py` | PostgreSQL query |
| `tools_proc/log_tailer.py` | ログ tail / error 抽出 |
| `tools_proc/code_checker.py` | 構文 / 型チェック |
| `tools_proc/backup.py` | 差分バックアップ保存 / 確認 |
| `tools_proc/image_generation.py` | 画像生成（OpenAI / Gemini / FreeAI / Codex CLI / Antigravity CLI） |
| `tools_proc/movie_generation.py` | 動画生成（Google Gemini Veo） |
| `tools_proc/speech_to_text.py` | 音声認識（speech_recognition / Whisper） |
| `tools_proc/text_to_speech.py` | テキスト音声合成（Edge / OpenAI / Gemini / FreeAI） |
| `tools_proc/obs_studio_control.py` | OBS Studio WebSocket 制御 |
| `tools_proc/ffmpeg_control.py` | ffmpeg / ffprobe / ffplay の薄いランナー |
| `tools_proc/code_agents.py` | CodeAI CLI ラッパー（コードエージェント実行） |
| `tools_proc/chat_llm.py` | ChatAI ラッパー（チャット LLM 実行 / OpenAI 互換 completions） |
| `tools_proc/tools_chat.py` | `aidiy_chat_llms` MCP 登録 + HTTP 2 系統ルート（独自 IF / OpenAI 互換 IF） |
| `tools_proc/task_agents.py` / `tools_proc/tools_task_agents.py` | backend_task API への AIタスク投入 |
| `tools_proc/windows_control.py` / `tools_proc/tools_windows_control.py` | Windows デスクトップ操作制御（マウス/キーボード/ウィンドウ/プロセス/クリップボード/UI Automation） |

## アーキテクチャ

### アクセストランスポート（3種類）

| トランスポート | エンドポイント / コマンド | 主な利用者 |
|----------------|--------------------------|-----------|
| **SSE Transport** | `http://localhost:8095/{mcp_name}/sse` | AI エージェント、Claude Code、MCP クライアント |
| **Streamable HTTP Transport** | `POST http://localhost:8095/{mcp_name}/{method_name}` | Python スクリプト、curl、自動化処理 |
| **stdio gateway** | `mcp_stdio.py --sse-url http://localhost:8095/{mcp_name}/sse` | Codex など stdio 専用の Code CLI |

MCP一覧は `GET http://localhost:8095/` で確認できます。  
各 MCP のツール一覧・引数仕様は `GET http://localhost:8095/{mcp_name}/list` が JSON で返します。  
死活確認は `GET http://localhost:8095/{mcp_name}/ping`、初期化情報は `POST http://localhost:8095/{mcp_name}/initialize` です。

Python から `requests` で直接呼び出す例:

```python
import requests
res = requests.post("http://localhost:8095/aidiy_sqlite/list_tables", json={})
print(res.json())
```

Chrome DevTools は Node.js 版ではなく Python 実装の CDP client を使います。
Chrome は `ChromeManager` が単一 subprocess として管理し、必要時に `--remote-debugging-port=9222` で起動します。

アクセスは localhost 限定です。
SQLite / PostgreSQL は read-only 中心で扱い、書き込みが必要な場合もまずアプリ API で再現できないか確認します。

## 実装時の入口

- MCP を追加する場合は `tools_main.py` と `tools_proc/` を確認する。
- MCP / HTTP API の検証コードは `tests/` に置く。
- 複数 MCP を組み合わせる自動化処理は `aidiy_automations/` に置く。
- `aidiy_automations/ビデオページ生成_紹介.py` と `aidiy_automations/ビデオページ生成_解説.py` は `localhost:8095/aidiy_text_to_speech/synthesize` の `play=true` を使い、進行案内を挟みながら実行する。
- 題材、生成先、テンプレート、開始ステップは `aidiy_automations/ビデオページ生成__設定.json`、`aidiy_automations/ビデオページ生成__状況.json`、CLI 引数で管理する。`__main__` に全体の流れを置き、詳細処理は `step_*` 関数へ分ける。
- 自動化ステップは `00` を初期確認、`01`〜`nn` を実行と検証、`99` を最終処理として並べる。
- `aidiy_automations/ビデオページ生成_紹介.py` と `aidiy_automations/ビデオページ生成_解説.py` は `01`〜`99` の各ステップ完了後に、Chrome DevTools CDP で `?auto=loop` のビデオ表示を再描写する。
- SSE / stdio の接続問題は `mcp_stdio.py` と `.aidiy/knowledge/backend_tools,backend_server,運用手順.md` を確認する。
- AIコード側の MCP 設定は `backend_server/_config/AiDiy_mcp.json` と `CodeCLI_MCP設定.md` を確認する。
