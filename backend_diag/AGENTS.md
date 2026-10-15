# backend_diag 実装概要

Node.js 標準モジュールの読み取り専用診断サーバーと Electron / Web 表示です。AIコアや DB が未設定でも起動できます。

- `desktop.mjs` / `electron-main.cjs`: 既存共有セットアップで用意した Electron を通常表示に使います。ブラウザ・Codespaces は Node.js のみです。
- `diag_main.mjs`: ループバック HTTP、起動単位の認証、ブラウザ起動。
- `catalog.json`: リポジトリの利用箇所から整理した外部プログラムの登録情報。
- `probes.mjs`: 固定引数での存在・バージョン確認。任意コマンド API は設けません。
- `ui/src/`: Vue 3 SFC。認証・上部タブ、インストール一覧、キー設定状況を分離します。
- `ui/build.mjs` / `static/`: ローカルの Vue を事前コンパイルした配布 UI。起動時はビルド・ダウンロード不要で、ソースとの一致を検証します。
- `public_models.mjs`: 起動時の匿名公開モデル取得と、起動中メモリだけのキャッシュ。個別キーの試験結果とは分離します。
- `key_status.mjs`: 固定 Python bridge の起動・期限・終了管理。設定ファイルやキー値を Node に読み込みません。
- `model_probe.py` / `model_catalog_copy.py`: Python 標準ライブラリの単独診断と、本体からコピーしたモデル判定。本体への import・venv 依存はありません。
- `_setup.py` / `_cleanup.py`: この作業コピーのランチャー配置・解除。

インストール・設定ファイル変更・ログイン・文章生成・MCP/CLI 試行は診断に含めません。全テストはインストール確認のみです。匿名の公開 OpenRouter 一覧だけを起動時に取得し、キーを使うモデル API は個別テスト時だけ接続します。API は起動時の認証が必須で、公開する静的ファイルに診断結果や認証キーを埋め込みません。

起動・検証・追加手順は [README.md](./README.md) を参照してください。
