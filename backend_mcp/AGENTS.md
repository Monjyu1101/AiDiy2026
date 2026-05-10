# backend_mcp 実装概要

## 本書の目的

このファイルは `backend_mcp` の構成、提供 MCP、実装入口を示す概要ドキュメントです。
起動、依存関係、SSE URL、環境変数、運用手順は `.aidiy/knowledge` に移動しています。
AI エージェントは、本書に個別手順や一時的な作業メモを追記しないでください。
業務システム機能追加は `../docs/` の開発ガイドを優先し、コアシステム機能調整は `../.aidiy/knowledge/_index.md` を入口にします。

## HowTo 参照先

| 目的 | 参照先 |
|------|--------|
| 起動、stdio bridge、環境変数、ログ | [`../.aidiy/knowledge/backend_mcp,backend_server,運用手順.md`](../.aidiy/knowledge/backend_mcp,backend_server,運用手順.md) |
| MCP サーバー構成、新規 MCP 追加 | [`../.aidiy/knowledge/backend_mcp,構成.md`](../.aidiy/knowledge/backend_mcp,構成.md) |
| MCP の使い分け、AI エージェントからの利用 | [`../.aidiy/knowledge/backend_server,backend_mcp,MCP活用手順.md`](../.aidiy/knowledge/backend_server,backend_mcp,MCP活用手順.md) |
| Code CLI 側の MCP 設定 | [`../.aidiy/knowledge/backend_hermes,backend_mcp,CodeCLI_MCP設定.md`](../.aidiy/knowledge/backend_hermes,backend_mcp,CodeCLI_MCP設定.md) |

## 概要

`backend_mcp` はポート `8095` 上で 13 個の MCP サーバーを同居させる FastMCP アプリケーションです。
ブラウザ操作、デスクトップキャプチャ、DB確認、ログ確認、コードチェック、バックアップ確認、画像生成、音声認識/合成、OBS / ffmpeg 制御を AI エージェントから利用できるようにします。

## 提供 MCP

| MCP | 役割 |
|-----|------|
| `aidiy_chrome_devtools` | Chrome を CDP で操作するブラウザ自動化 |
| `aidiy_desktop_capture` | OS スクリーンショット取得 |
| `aidiy_sqlite` | AiDiy SQLite DB の read-only 中心クエリ |
| `aidiy_postgres` | 外部 PostgreSQL の read-only 中心クエリ |
| `aidiy_logs` | `backend_server` / `backend_mcp` のログ観測 |
| `aidiy_code_check` | Python 構文、ruff、TypeScript 型チェック |
| `aidiy_backup_check` | バックアップから変更前後ソースを抽出 |
| `aidiy_backup_save` | AiDiy ネイティブ差分バックアップを実行 |
| `aidiy_image_generation` | AI 画像生成（OpenAI gpt-image / DALL-E、Gemini、FreeAI） |
| `aidiy_speech_to_text` | 音声認識（speech_recognition、OpenAI Whisper） |
| `aidiy_text_to_speech` | テキスト音声合成（Edge / OpenAI / Gemini / FreeAI、MP3 出力） |
| `aidiy_obs_studio_control` | OBS Studio WebSocket 制御（配信、録画、シーン、ソース、音声） |
| `aidiy_ffmpeg_control` | ffmpeg / ffprobe / ffplay 実行（動画合成、字幕焼き込み、プレビュー再生） |

## ファイル構成

| パス | 役割 |
|------|------|
| `mcp_main.py` | FastAPI 上に 13 個の FastMCP を同居 |
| `mcp_stdio.py` | stdio <-> SSE bridge |
| `mcp_proc/chrome_manager.py` | Chrome プロセス管理 |
| `mcp_proc/chrome_devtools.py` | CDP client |
| `mcp_proc/desktop_capture.py` | スクリーンショット取得 |
| `mcp_proc/sqlite_query.py` | SQLite query |
| `mcp_proc/postgres_query.py` | PostgreSQL query |
| `mcp_proc/log_tailer.py` | ログ tail / error 抽出 |
| `mcp_proc/code_checker.py` | 構文 / 型チェック |
| `mcp_proc/backup_check.py` | 差分確認 |
| `mcp_proc/backup_save.py` | 差分バックアップ保存 |
| `mcp_proc/image_generation.py` | 画像生成（OpenAI / Gemini / FreeAI） |
| `mcp_proc/speech_to_text.py` | 音声認識（speech_recognition / Whisper） |
| `mcp_proc/text_to_speech.py` | テキスト音声合成（Edge / OpenAI / Gemini / FreeAI） |
| `mcp_proc/obs_studio_control.py` | OBS Studio WebSocket 制御 |
| `mcp_proc/ffmpeg_control.py` | ffmpeg / ffprobe / ffplay の薄いランナー |

## アーキテクチャ

MCP クライアントは SSE で `mcp_main.py` に接続します。
Codex など stdio クライアントは `mcp_stdio.py` を経由します。

Chrome DevTools は Node.js 版ではなく Python 実装の CDP client を使います。
Chrome は `ChromeManager` が単一 subprocess として管理し、必要時に `--remote-debugging-port=9222` で起動します。

アクセスは localhost 限定です。
SQLite / PostgreSQL は read-only 中心で扱い、書き込みが必要な場合もまずアプリ API で再現できないか確認します。

## 実装時の入口

- MCP を追加する場合は `mcp_main.py` と `mcp_proc/` を確認する。
- SSE / stdio の接続問題は `mcp_stdio.py` と `backendMCP運用手順.md` を確認する。
- AIコード側の MCP 設定は `backend_server/_config/AiDiy_mcp.json` と `CodeCLI_MCP設定.md` を確認する。
