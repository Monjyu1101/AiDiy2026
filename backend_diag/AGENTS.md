# backend_diag 実装概要

Node.js 標準モジュールの読み取り専用診断サーバーと Electron / Web 表示です。AIコアや DB が未設定でも起動できます。

- `起動/desktop.mjs` / `起動/electron-main.cjs`: 既存共有セットアップで用意した Electron を通常表示に使います。ブラウザ・Codespaces は Node.js のみです。
- `diag_main.mjs`: ループバック HTTP、起動単位の認証、ブラウザ起動。
- `モデル情報/models_info.mjs`: プロバイダ別モデル情報とchat / live / codeの合成JSON。取得モデルから `models` を生成し、API の詳細情報も保持。Grok / backend_local の固定候補と、Copilot導入済み・合成候補なし時の固定8モデルを管理。本体・クライアントは合成JSONを読み、`_config` 上のモデル設定ファイルには依存しません。
- `モデル情報/voices_info.mjs`: Gemini / FreeAI / OpenAIの固定音声候補。確認済みの有効キーに合わせて `live_voices_info.json` を生成します。
- `診断/headless.mjs`: `--headless` の全診断と、画面の書込と共通の保存形式。画面・待受なしで最速実行し、`_AIDIY/aidiy_diag/*.json` へ成功時だけ保存します（現在は `install_info.json`）。
- `診断/catalog.json`: リポジトリの利用箇所から整理した外部プログラムの登録情報。
- `診断/probes.mjs`: 固定引数での存在・バージョン確認。任意コマンド API は設けません。
- `ui/src/`: Vue 3 SFC。認証・上部タブ、インストール一覧、キー設定状況を分離します。
- `ui/build.mjs` / `static/`: ローカルの Vue を事前コンパイルした配布 UI。起動時はビルド・ダウンロード不要で、ソースとの一致を検証します。
- `モデル情報/public_models.mjs`: 起動時の匿名公開モデル取得と、起動中メモリだけのキャッシュ。個別キーの試験結果とは分離します。
- `モデル情報/bundled_models.mjs` / `モデル情報/openrouter_models/openrouter_models.zip`: 公開モデルを取得できない場合の同梱キャッシュ。一時フォルダへ展開して同じ絞り込みで使い、画面には「キャッシュ利用」と表示します。
- `モデル情報/key_status.mjs`: UI に返す固定スキーマの制限。設定値やキー値をブラウザへ返しません。
- `runtime/*.ts` / `runtime/*.mjs`: Node 標準モジュールの固定設定読取・HTTPS・キャンセルと、本体由来のモデル判定。TypeScript は既存 UI ビルドで事前変換し、実行時の Python・コンパイラ・venv 依存はありません。
- `checks/reference/`: 移植前の Python 実装から生成・凍結した合成ゴールデン。比較専用で本番実行から参照しません。
- `_setup.py` / `_cleanup.py`: この作業コピーのランチャー配置・解除。

インストール・設定ファイル変更・ログイン・文章生成・MCP/CLI 試行は診断に含めません。全テストはインストール確認のみです。匿名の公開 OpenRouter 一覧だけを起動時に取得し、キーを使うモデル API は個別テスト時だけ接続します。API は起動時の認証が必須で、公開する静的ファイルに診断結果や認証キーを埋め込みません。

起動・検証・追加手順は [README.md](./README.md) を参照してください。
