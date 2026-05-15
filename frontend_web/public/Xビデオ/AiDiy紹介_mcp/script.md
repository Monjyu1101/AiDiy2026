# AiDiy MCP Hub 紹介 — ナレーション台本

> 合計: 110.0 秒 / 8 シーン
> 音声ファイル出力先: `audio/scene_XXX.mp3`
> 画像ファイル出力先: `images/scene_XXX.png`

---

## scene_000 (0.0 - 12.0 sec) INTRODUCTION

この動画では、AiDiy の MCP Hub を紹介します。ポート 8095 に 13 個の MCP サーバーが同居し、ブラウザ操作、DB 確認、ログ観測、コードチェック、バックアップ、メディア生成、OBS・ffmpeg 制御まで、AI エージェントからひとつの SSE エンドポイントで使えます。

---

## scene_001 (12.0 - 26.0 sec) ARCHITECTURE

backend_mcp は FastAPI と Starlette の上に 13 個の FastMCP インスタンスを Mount 合成し、ポート 8095 で uvicorn 起動します。クライアントは SSE で直接接続するか、stdio クライアントは mcp_stdio.py を介して変換します。再起動は temp/reboot_mcp.txt ウォッチャーで制御されます。

---

## scene_002 (26.0 - 41.0 sec) 13 SERVERS

13 の MCP サーバーを役割で分類します。ブラウザ系が chrome_devtools と desktop_capture。DB 系が sqlite と postgres。観測系が logs と code_check。バックアップ系が backup_check と backup_save。メディア系が image_generation、speech_to_text、text_to_speech。制作系が obs_studio_control と ffmpeg_control です。

---

## scene_003 (41.0 - 55.0 sec) BROWSER & DESKTOP

aidiy_chrome_devtools は Node.js 版の MCP ではなく、Python で実装した CDP クライアントです。ChromeManager が Chrome を --remote-debugging-port=9222 で単一 subprocess として管理し、必要なときだけ自動起動します。desktop_capture は OS レベルのスクリーンショットを取得します。

---

## scene_004 (55.0 - 69.0 sec) DB / OBSERVE / CHECK

aidiy_sqlite は AiDiy の SQLite DB を read-only 中心で参照します。aidiy_postgres は psycopg を使い、DSN が未設定でも他の MCP を妨げない遅延初期化を採用しています。aidiy_logs は backend_server と backend_mcp のログを tail し、Traceback や ERROR を抽出します。aidiy_code_check は Python 構文チェック、ruff、TypeScript の型チェックをまとめて実行します。

---

## scene_005 (69.0 - 83.0 sec) BACKUP & MEDIA

aidiy_backup_check は差分バックアップから変更前後のソースを抽出します。aidiy_backup_save は AiDiy ネイティブの差分バックアップを実行します。aidiy_image_generation は OpenAI gpt-image、DALL-E、Gemini、FreeAI に対応。aidiy_speech_to_text は speech_recognition と OpenAI Whisper で音声認識。aidiy_text_to_speech は Edge、OpenAI、Gemini、FreeAI で MP3 音声を合成します。

---

## scene_006 (83.0 - 97.0 sec) PRODUCTION

aidiy_obs_studio_control は OBS Studio の WebSocket を使い、配信の開始・停止、録画、シーン切り替え、ソース制御、音声調整を MCP ツールとして公開します。aidiy_ffmpeg_control は ffmpeg、ffprobe、ffplay の薄いランナーで、動画合成、字幕焼き込み、プレビュー再生を実行します。

---

## scene_999 (97.0 - 110.0 sec) CLOSING

ご視聴ありがとうございました。AiDiy の MCP Hub はポート 8095 に 13 個のサーバーを集約し、ブラウザ操作、DB 確認、ログ観測、コードチェック、バックアップ、メディア生成、OBS・ffmpeg 制御を AI エージェントから一括で使えます。SSE で接続するか、stdio bridge を経由して Claude Code CLI や Codex からも利用できます。
