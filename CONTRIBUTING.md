# Contributing

本プロジェクトへの貢献ありがとうございます。

## 前提

- 文字コードは UTF-8 固定
- 日本語の命名規約（テーブル/カラム/API/コンポーネント）を遵守
- ライセンス条件（`LICENSE`）を遵守（非商用利用のみ許可）
- 既存ドキュメントに従う
  - `AGENTS.md`
  - `docs/` フォルダ（コーディングルール、実装例など）
  - `backend_server/AGENTS.md`
  - `backend_tools/AGENTS.md`
  - `backend_local/AGENTS.md`
  - `backend_taskteam/AGENTS.md`
  - `command_hermes/AGENTS.md`
  - `frontend_web/AGENTS.md`
  - `frontend_avatar/AGENTS.md`

## ライセンス（重要）

- 本プロジェクトは非商用利用を前提とした公開ライセンスです
- 商用利用には、事前に全著作権者（諸作権者）の書面承諾が必要です

## 変更の流れ

1. 変更方針を決める（関連ドキュメントを確認）
2. 小さく変更し、動作確認する
3. README やドキュメントへの追記が必要なら同時に更新

## テスト

自動テストは `backend_server/tests/` の `unittest` だけです（設定管理まわり）。サーバー起動は不要です。

```powershell
cd backend_server
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

そのほかは手動テストで確認してください。

- API: http://127.0.0.1:8091/docs / http://127.0.0.1:8098/docs / http://127.0.0.1:8093/docs
- UI: http://127.0.0.1:8090
- 型チェック: `frontend_web` / `frontend_avatar` は `npm run type-check`（`npm run build` は明示依頼時のみ）
- MCP 連携変更時: `backend_tools` の 19 MCP サーバー（一覧は `GET http://127.0.0.1:8095/`、SSE は `http://127.0.0.1:8095/<mcp_name>/sse`）も確認

## セキュリティ

- APIキーなどの機密情報はコミットしないでください
- `_config/AiDiy_key.json` は `.gitignore` で除外しています

## 相談

大きな変更や設計変更は、Issue で相談してから進めてください。
