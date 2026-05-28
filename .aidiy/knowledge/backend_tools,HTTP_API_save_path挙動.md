# backend_tools HTTP API の save_path 挙動

> 文書: `backend_tools,HTTP_API_save_path挙動.md` | 実装: `backend_tools/tools_main.py`

## このメモを使う場面

- `/aidiy_backup` `/tts` `/imageGen` `/movieGen` エンドポイントのレスポンス仕様を確認する
- save_path の有無でレスポンス内容が変わる仕様を再実装・修正するとき

## HTTP API 一覧

| エンドポイント | MCP サーバー | 出力形式 | 備考 |
|--------------|-------------|---------|------|
| `POST /aidiy_backup/save/scan` | aidiy_backup | JSON | 差分スキャンのみ |
| `POST /aidiy_backup/save/run` | aidiy_backup | JSON | 差分バックアップ実行 |
| `POST /aidiy_backup/check/{method}` | aidiy_backup | JSON | バックアップ内容確認。`info`, `before_after`, `versions`, `changed`, `diff_stats` |
| `POST /tts` | aidiy_text_to_speech | MP3 音声 | `speech_text` フィールド必須 |
| `POST /imageGen` | aidiy_image_generation | PNG 画像 | Gemini / OpenAI |
| `POST /movieGen` | aidiy_movie_generation | MP4 動画 | Gemini Veo、数分かかる |
| `POST /agents` | aidiy_code_agents | JSON | コードエージェント実行 |

## save_path の挙動まとめ

| `save_path` | 保存先 | レスポンスに含まれるもの |
|-------------|--------|--------------------------|
| 未指定 | `../temp/output/yyyymmdd.HHmmss.{ext}` へ自動保存 | base64 データ + save_path（自動生成パス） |
| 指定あり | 指定パスへ保存 | save_path のみ（base64 なし） |

- `/tts` の拡張子: `.mp3`
- `/imageGen` の拡張子: `.png`
- `/movieGen` の拡張子: `.mp4`（base64 返却なし、常に `save_path` のみ返す）
- `../temp/output/` は `backend_tools/tools_main.py` からの相対パス（= プロジェクトルートの `temp/output/`）

## TtsRequest フィールド仕様

- `speech_text` のみ（`text` フィールドは廃止済み）
- `save_path` 未指定でも常にファイルへ出力する
- `local_play=true` または `play=true` でサーバー側ローカル再生を試行する

## SSE エンドポイントのマウント方法

`app.mount()` でサブアプリとして使う場合、FastMCP の `sse_path` / `message_path` は
マウントポイント相対（`/sse`, `/messages/`）にし、`mount_path` で絶対パスを指定する必要がある。

```python
# NG: マウント後に 404 になる
mcp_ca = FastMCP("aidiy_code_agents", sse_path="/aidiy_code_agents/sse", message_path="/aidiy_code_agents/messages/")

# OK: mount_path で SseServerTransport にフルパスを伝え、sse_path/message_path は相対に
mcp_ca = FastMCP("aidiy_code_agents", mount_path="/aidiy_code_agents", sse_path="/sse", message_path="/messages/")
app.mount("/aidiy_code_agents", mcp_ca.sse_app())
```

理由: Starlette の `app.mount()` はリクエストパスからマウントプレフィックスを除去してサブアプリへ渡す。
`SseServerTransport` へ伝えるクライアント向け URL（`normalized_message_endpoint`）は `mount_path + message_path` で生成されるため、`mount_path` に正しい絶対パスを渡す必要がある。
