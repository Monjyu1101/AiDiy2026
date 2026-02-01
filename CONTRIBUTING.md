# Contributing

本プロジェクトへの貢献ありがとうございます。

## 前提

- 文字コードは UTF-8 固定
- 日本語の命名規約（テーブル/カラム/API/コンポーネント）を遵守
- 既存ドキュメントに従う
  - `AGENTS.md`
  - `docs/` フォルダ（コーディングルール、実装例など）
  - `backend_server/AGENTS.md`
  - `frontend_server/AGENTS.md`

## 変更の流れ

1. 変更方針を決める（関連ドキュメントを確認）
2. 小さく変更し、動作確認する
3. README やドキュメントへの追記が必要なら同時に更新

## テスト

自動テストは未整備のため、手動テストで確認してください。

- API: http://localhost:8091/docs / http://localhost:8092/docs
- UI: http://localhost:8090

## セキュリティ

- APIキーなどの機密情報はコミットしないでください
- `backend_server/_config/RiKi_AiDiy_key.json` は `.gitignore` で除外しています

## 相談

大きな変更や設計変更は、Issue で相談してから進めてください。
