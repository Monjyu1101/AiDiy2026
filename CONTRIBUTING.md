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
  - `backend_mcp/AGENTS.md`
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

自動テストは未整備のため、手動テストで確認してください。

- API: http://localhost:8091/docs / http://localhost:8092/docs
- UI: http://localhost:8090
- MCP 連携変更時: `backend_mcp` の 8 SSE（`aidiy_chrome_devtools` / `aidiy_desktop_capture` / `aidiy_sqlite` / `aidiy_postgres` / `aidiy_logs` / `aidiy_code_check` / `aidiy_backup_check` / `aidiy_backup_save`、いずれも `http://localhost:8095/<name>/sse`）も確認

## セキュリティ

- APIキーなどの機密情報はコミットしないでください
- `backend_server/_config/AiDiy_key.json` は `.gitignore` で除外しています

## 相談

大きな変更や設計変更は、Issue で相談してから進めてください。
