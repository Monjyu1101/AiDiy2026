# backend_tools tests

`backend_tools` のテスト、動作確認スクリプト、手元検証用コードを置くフォルダです。

## 置くもの

- MCP 実装の単体確認スクリプト
- HTTP API の疎通確認スクリプト
- 外部サービスやローカルツールを使う検証コード

## 方針

- 本体実装は `../tools_proc/` と `../tools_main.py` に置きます。
- 一時的な実験コードは、再利用できる検証に整理してから置きます。
- テスト実行に外部 API キー、Chrome、OBS、ffmpeg などが必要な場合は、先頭コメントや README に前提条件を書きます。

## スモークテスト

backend_tools 起動後、まず以下を確認します。

```powershell
cd backend_tools
.venv\Scripts\python.exe tests\test_mcp_smoke.py
.venv\Scripts\python.exe tests\test_post_api_smoke.py
```

- `test_mcp_smoke.py`: 15 MCP の SSE 接続、`list_tools`、各 MCP につき最低 1 メソッドの呼び出し（重い生成系は prompt 省略のバリデーションエラー経路）を確認します。
- `test_post_api_smoke.py`: 15 MCP + `aidiy_chat_completions` の HTTP docs / POST API を確認します。画像生成、動画生成、AI agent 実行などの重い外部処理は実行しません。
