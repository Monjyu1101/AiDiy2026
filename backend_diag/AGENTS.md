# backend_diag 実装概要

Node.js 標準モジュールの読み取り専用診断サーバーと Electron / Web 表示です。AIコアや DB が未設定でも起動できます。

- `desktop.mjs` / `electron-main.cjs`: 既存共有セットアップで用意した Electron を通常表示に使います。ブラウザ・Codespaces は Node.js のみです。
- `diag_main.mjs`: ループバック HTTP、起動単位の認証、ブラウザ起動。
- `catalog.json`: リポジトリの利用箇所から整理した外部プログラムの登録情報。
- `probes.mjs`: 固定引数での存在・バージョン確認。任意コマンド API は設けません。
- `static/`: ビルド不要の Web UI。カテゴリ開閉・検索・状態絞り込み・詳細表示。
- `_setup.py` / `_cleanup.py`: この作業コピーのランチャー配置・解除。

インストール・設定ファイル変更・ログイン・外部 AI 接続は診断に含めません。API は起動時の認証が必須で、公開する静的ファイルに診断結果や認証キーを埋め込みません。

起動・検証・追加手順は [README.md](./README.md) を参照してください。
