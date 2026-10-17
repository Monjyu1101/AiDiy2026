# backend_diag 実装概要

Node.js 標準モジュールの読み取り専用診断サーバーと Electron / Web 表示です。AIコアや DB が未設定でも起動できます。

- `起動/desktop.mjs` / `起動/electron-main.cjs`: 既存共有セットアップで用意した Electron を通常表示に使います。ブラウザ・Codespaces は Node.js のみです。
- `diag_main.mjs`: ループバック HTTP、起動単位の認証、ブラウザ起動。
- `モデル情報/models_info.mjs`: プロバイダ別モデル情報とchat / live / codeの合成JSON。取得モデルから `models` を生成し、API の詳細情報も保持。Grok / backend_local の固定候補と、Copilot導入済み・合成候補なし時の固定8モデルを管理。本体・クライアントは合成JSONを読み、`_config` 上のモデル設定ファイルには依存しません。
- `モデル情報/voices_info.mjs`: Gemini / FreeAI / OpenAIの固定音声候補。取得・認証状態にかかわらず3区分の `live_voices_info.json` を生成します。候補の存在は認証成功を意味しません。
- `診断/headless.mjs`: `--headless` の全診断と、画面の書込と共通の保存形式。画面・待受なしで最速実行し、`_AIDIY/aidiy_diag/*.json` へ成功時だけ保存します（現在は `install_info.json`）。
- `診断/catalog.json`: リポジトリの利用箇所から整理した外部プログラムの登録情報。
- `診断/probes.mjs`: 固定引数での存在・バージョン確認。任意コマンド API は設けません。
- `ui/src/`: Vue 3 SFC。認証・上部タブと、導入状況・モデル一覧・外部連携・設定モデルを同名の機能フォルダで分離します。複数画面の状態表示は `共通表示/状態バッジ.vue`、タイトルバーと Tools 接続は `ウィンドウ/` に集約します。
- `ui/build.mjs` / `static/`: ローカルの Vue を事前コンパイルした配布 UI。起動時はビルド・ダウンロード不要で、ソースとの一致を検証します。
- `モデル試行/audio_store.mjs`: Live が返した1秒以上の音声を専用一時領域に期限付きで保存し、認証付きの不透明IDで再生します。設定ファイル・モデル情報の保存とは分離します。
- `モデル試行/trials.mjs`: 明示操作専用の config 14役割・逐次会話試行。認証済み API から固定 loopback の MCP / Live アダプターへ接続し、同じ設定の結果だけを実行内で共有します。
- `モデル情報/public_models.mjs`: 起動時の匿名公開モデル取得と、起動中メモリだけのキャッシュ。個別キーの試験結果とは分離します。
- `モデル情報/bundled_models.mjs` / `モデル情報/openrouter_models/openrouter_models.zip`: 公開モデルを取得できない場合の同梱キャッシュ。一時フォルダへ展開して同じ絞り込みで使い、画面には「キャッシュ利用」と表示します。
- `モデル情報/key_status.mjs`: UI に返す固定スキーマの制限。設定値やキー値をブラウザへ返しません。
- `runtime/*.ts` / `runtime/*.mjs`: Node 標準モジュールの固定設定読取・HTTPS・キャンセルと、本体由来のモデル判定。TypeScript は既存 UI ビルドで事前変換し、実行時の Python・コンパイラ・venv 依存はありません。
- `checks/reference/`: 移植前の Python 実装から生成・凍結した合成ゴールデン。比較専用で本番実行から参照しません。
- `_setup.py` / `_cleanup.py`: この作業コピーのランチャー配置・解除。

インストール・設定ファイル変更・ログインは行いません。全テストは導入状況・モデル一覧・外部連携の確認と書込を順に行い、終わると導入状況タブへ切り替えます。会話生成を伴う config モデル試行は Tools 接続中の明示操作専用で、起動・headless・全テストには含めません。匿名の公開 OpenRouter 一覧だけを起動時に取得し、キーを使うモデル API と外部連携（Hugging Face / Discord）の読み取り専用の認証確認は、画面の明示操作（各行のテスト・一覧再取得・状況確認・全テスト）時だけ接続します。外部連携の結果は `_AIDIY/aidiy_diag/integration_info.json` へ保存し、headless では確認しません。API は起動時の認証が必須で、公開する静的ファイルに診断結果や認証キーを埋め込みません。

起動・検証・追加手順は [README.md](./README.md) を参照してください。
