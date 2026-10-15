# AiDiy 診断

外部プログラムの導入状態を、ソースに記載された利用箇所と一緒に確認します。診断サーバー・インストール確認・キー設定・モデル確認は Node.js 18 以降の標準モジュールで動作します。診断の実行に Python は不要です。通常は Electron ウィンドウで表示し、--browser / Codespaces / GUI のない環境では Web で表示します。AIコア / DB の起動は不要です。

診断本体の起動には Node.js が必要です。一覧は Python、uv、Node.js、npm、npx、Electron の順です。Python はバックエンドで使用します。Python が無くても配置済みランチャー・直接 Node 起動は使えます。全体セットアップは既存方式に合わせ Python を使用します。

## 起動

```sh
node backend_diag/diag_main.mjs --browser
# ランチャー配置後
aidiy_diag                  # Electron 表示後、コマンドプロンプトへ戻る
aidiy_diag --browser        # ブラウザ起動・foreground
aidiy_diag --foreground     # Electron を foreground で起動（ログ・Ctrl+C）
aidiy_diag --wait           # --foreground と同じ
```

`python backend_diag/_setup.py` または全体の `python _setup.py` の最初の項目（既定 `[y]/n`、a=auto も対象）で `~/.local/bin` にランチャーを作成します。Windows は `aidiy_diag.cmd` です。`backend_diag/aidiy_diag` / `backend_diag/aidiy_diag.cmd` からも直接起動できます。

上部は Term と同じ高さのタイトルバー・ウィンドウ操作・接続バーです。シアンの線は Tools の接続成功、黒は未接続、赤は確認OFFを示します。診断自体の接続とは別です。Tools は `_config/AiDiy_key.json` の `PORT_TOOLS`（省略時8095）に対して、固定 loopback の `/aidiy_code_agents/ping` だけを10秒間隔で確認します。キー・モデル・エージェントの実行は行いません。確認OFF・切断・画面破棄で確認を停止します。

「インストール」「モデルキー設定」「外部連携設定」の Vue タブです。初期状態は未確認です。インストール状況パネル右上の「インストール確認」で検出・更新します。右上の「全テスト」も現在はインストール確認だけを実行します。左側でカテゴリを開閉し、項目を選ぶと右側でパス・バージョン・利用機能・参照ソースを表示します。

## Codespaces / リモートブラウザ

```sh
node backend_diag/diag_main.mjs --browser --no-open --port 8097
```

ポート 8097 を **Private（非公開）** で転送してください。Codespaces の環境変数が揃っていれば HTTPS の転送 URL を表示します。その他の環境では転送画面の URL に、ターミナル表示 URL の `#token=...` を付けて開くか、画面に認証キー部分を入力してください。パス型プロキシでは `--base-path /proxy/8097/` を指定します。末尾の `/` を含む URL で開いてください。CSS・JS・API は同じパスを基準に読み込みます。

待受は常に `127.0.0.1`。既定ポートは自動割り当てです。ブラウザ側の PC ではなく、診断プロセスが動く Codespace / サーバーのプログラムを調べます。Electron API を使用しないため、ブラウザでも全機能を利用できます。

## 認証と安全範囲

- 起動ごとに一時認証キーを作成し、API は Bearer 認証を必須とします。認証 URL は他人に共有しないでください。
- キーはブラウザのメモリ内だけに保持し、URL fragment は読込直後に履歴から除去します。再読込時は認証 URL を開き直してください。認証キーをファイル・Storage・アクセスログには保存しません。
- 診断 API は引数・任意パス・任意コマンドを受け付けません。4 並列、各 5 秒、出力 16 KiB 上限です。結果には抽出したバージョン番号だけを表示し、生のコマンド出力は表示しません。
- 子プロセスには秘密を含み得る環境変数を渡さず、HOME・作業ディレクトリを一時領域に隔離します。POSIX ではプロセスグループ、Windows では直接起動したプロセスを停止します。Windows で子孫プロセスまでの停止は保証しません。固定の version 引数でも、PATH 上の実行ファイル自体の信頼性や全副作用を保証するサンドボックスではありません。信頼できる環境で使ってください。
- バージョン確認の NG / ERR は、サーバー側の標準エラーへ `[aidiy-diag:probe]` の JSON として出します。項目 ID・固定の version 引数・失敗分類・OS エラーコード・終了コード・シグナルだけを含め、生の子プロセス出力、フルパス、設定・環境変数・キー値は出しません。起動時の OS エラーコードは画面にも表示します。モデル API の通信エラー本文はログに出しません。
- 通常のデスクトップ起動では、NG / ERR と Electron 異常終了の安全な分類を `backend_diag/.desktop-errors.log` に保存します（書込み可能な場合、最大64 KiB、次の追記で容量超過分をリセット）。認証URL・キー・生stderrは保存しません。`aidiy_diag --foreground` では従来どおりターミナルの標準エラーも確認できます。
- GUI、内部ランチャー、安全な version 引数が確認できないものは存在確認のみです。Windows の `.cmd` / `.bat` / `.ps1` はシェル実行しません。npm / npx は既知の隣接 `node_modules/npm/bin/npm-cli.js` / `npx-cli.js` が確認できる場合だけ、Node から固定 `--version` で確認します。対応する実体がない shim は ERR とし、その他のラッパーは存在確認に限定します。
- PATH と登録済みの標準パス・プロジェクト内配置を検出対象とし、API キー・設定 JSON・環境変数の値は表示しません。個別設定による独自パスや venv 内のみにある実行ファイルは、PATH に載っていなければ検出されない場合があります。
- 判定は未確認・未検出・OK・NG・ERR の 5 種類です。OK に含める存在確認は起動試験ではありません。判定の定義は末尾の「状態インジケーター」を参照してください。
- Python / npm のライブラリ依存と外部プログラムは別です。この初期機能は外部プログラムを対象とします。

## 終了・解除

通常の Electron 起動は表示確認後にコマンドプロンプトへ戻ります。ウィンドウを閉じると HTTP・診断子プロセスも終了します。`--foreground` / `--wait`、`--browser` / `--no-open`、Codespaces・GUI のない環境では起動ターミナルの Ctrl+C で終了します。キーも失効します。`python backend_diag/_cleanup.py` または全体クリーンアップで、この作業コピーのランチャーだけを解除します。別コピーのランチャーは削除しません。全体起動 `python _start.py` では IDE グループの先頭に Diag の選択があります（既定 n）。選択時だけ Node の独立プロセスで起動し、全体起動の Ctrl+C・クリーンアップ要求では停止します。Diag を自動再起動する監視は行いません。単独ランチャーで起動した診断も、同じ作業コピーのクリーンアップで終了します。停止通知は `.stop-request` の短いランダム識別子のみで、PID・認証キー・診断結果は保存しません。

## 追加と検証

`catalog.json` に実際のソース参照を伴う項目を追加します。`version_args: null` は存在確認のみです。GUI 起動やネットワーク・モデル取得を伴うコマンドは version 検査に登録しないでください。API 経由で項目を追加・変更する機能はありません。

```sh
node --test backend_diag/tests/*.test.mjs backend_diag/tests/*.test.cjs
node --check backend_diag/static/app.js
node backend_diag/ui/verify.mjs
```

Python がある開発環境では任意で `python -m unittest discover -s backend_diag/tests -v` も実行できます。

Playwright と Chromium が利用できる検証環境では `python backend_diag/tests/ui_browser.py` で、合成データのみの実ブラウザ回帰を実行できます。実キー読取・外部モデル API 呼出は行いません。必要なら `CHROMIUM_PATH` で既存ブラウザを指定します。

ブラウザ確認では、認証前拒否、診断開始・再チェック、カテゴリ開閉、選択詳細、狭い画面、通常 URL とパス型プロキシを確認してください。診断結果や認証 URL を公開ログ・スクリーンショットに含めないでください。

## カタログの調査範囲

基準コミット `8adbdb484cafe31e145c4fe362897d2af1077eb1` の Git tree 全 4,950 ファイルから、対象ソース・設定・スクリプト・テンプレート・テスト・manifest/lockfile **3,333 件**を列挙し、全件の全文を静的走査しました。未取得・未読は 0 件。246 候補から今回の確認対象 **19 項目**を採用し、各項目の詳細に参照パスと行番号を表示します。コードの実行・インストール試験を行ったという意味ではありません。

通常の Markdown ガイド・skill 本文（README/AGENTS を除く）、画像・音声・モデル・Office/PDF、LaTeX 文書資産、ライセンス・非実行テキスト等は対象外です。実行可能な skill スクリプトやコード例は含めます。省略のある Python 教材 3 件は AST 解析できませんでしたが、全文テキストを走査済みです。全リポジトリの全バイトを検証したという主張ではありません。

- [coverage.json](./coverage.json): 件数、基準コミット、除外、制限、AST テキスト代替走査の記録。
- [reference/source-manifest.json](./reference/source-manifest.json): 対象 3,333 件のパスと元の Git blob SHA。
- [reference/source_scan.py](./reference/source_scan.py): 対象コードを実行しない標準ライブラリのみの走査スクリプト。基準コミットの作業コピーに対し `python backend_diag/reference/source_scan.py REPOSITORY OUTPUT_JSON COMMIT backend_diag/reference/source-manifest.json` で候補抽出を再現できます。抽出候補からカタログへの分類にはソース確認が必要です。

Python/Node のライブラリ、内部スクリプト、shell builtin、Git subcommand、モデル ID を外部実行ファイルと混同しません。19 項目すべてが必須ではなく、選択機能に応じて必要な項目を含みます。ユーザー設定の任意コマンドや動的生成、リモート・コンテナ・WSL・Android 側の導入状態は、ホストの PATH 確認だけでは保証できません。

## キー設定状況とモデル一覧

「キー設定状況」は診断サーバーの TypeScript 実装から固定ファイル `_config/AiDiy_key.json` の既知キーだけを読み取り、設定済 / 未設定を表示します。設定 JSON の値、長さ、末尾、ハッシュはブラウザに返しません。ファイル未作成は未設定、JSON 不正や読込不可は確認不可です。既存 conf クラスの初期化・設定変更は行いません。

一覧は既存 config の固定キー順（Gemini、FreeAI、Claude、OpenAI、Azure、Copilot、OpenRouter、Ollama、Hugging Face 読取・書込、Discord）です。表示対象外の設定項目は省き、JSON の任意の並べ替えには追従しません。左側でキーを選択し、右側で説明・テスト結果・モデル一覧を確認できます。キーの存在だけでは OK にしません。起動時には匿名の公開 OpenRouter 一覧だけを取得します。タブ移動・全テストから個別キーの API は呼びません。各行の「テスト」は明示操作時だけ固定プロバイダーのモデル一覧 API を読み取ります。生成リクエスト、MCP の挨拶、CLI 試行は未実装です。

- キー試験の表示は未実施 / OK / NG。未設定・未対応の項目は未実施で、理由を表示します。OpenRouter のテストボタンは取得済み公開キャッシュの表示だけで、個別取得やキー認証はしません。起動時・明示再取得の公開要求にもキーを送りません。キーの有効性は未確認のままです。
- OK はモデル一覧 API の応答確認であり、生成可能性・課金状態の保証ではありません。公開モデル一覧の場合はキー有効性の検証にもなりません。
- Gemini / FreeAI / Claude / OpenAI / OpenRouter / Ollama Cloud の固定 HTTPS 宛先だけを使います。Azure、Copilot、Hugging Face、Discord の個別テストは未対応です。
- キーは当該サービスへのモデル一覧要求にだけ使用し、任意 URL / proxy / 環境変数の base URL は採用しません。リダイレクト禁止、要求ごとに期限・応答上限を設けます。モデル処理全体は 25 秒・同時2件、HTTPS 要求ごとは8秒・応答1 MiB、設定ファイルは128 KiB、表示モデルは500件上限です。終了・期限切れでは通信を中止し、Google のページ取得は最大20回です。表示の取得範囲・警告を確認してください。エラー本文やヘッダーは返しません。
- 設定状況を更新すると前のテスト表示を消します。別のキーに変更した場合は再テストしてください。テスト結果はブラウザのメモリ内だけで、再起動・再読込後に引き継ぎません。

### 起動時の公開モデル取得

HTTP サーバーの起動後、匿名の公開 OpenRouter モデル一覧を一度だけ非同期で取得します。この操作は設定ファイルを読み取らず、Authorization も送りません。取得に失敗した場合も画面・インストール確認・他の個別テストは使えます。

テストボタン左に「公開モデル取得済」を成功時だけ表示します。「未取得」「取得中」「取得失敗」は区別し、個別キーの未実施 / OK / NG とは混ぜません。「公開モデルを再取得」は明示操作で、同時要求は1回にまとめます。設定状況更新では公開キャッシュを消しません。

キャッシュは起動中の Node メモリだけに置き、再起動で破棄して再取得します。元の Python 判定を移植した処理で日付絞り込みした時点のスナップショットです。個別テストはこの整形済み公開情報を同じ Node プロセス内で参照し、OpenRouter を毎回再取得しません。時間が経った情報を更新したい場合は再取得してください。共通システムへの結果保存はありません。

OpenRouter の先行手動テストは要求しません。公開情報が取得中・失敗・未取得でも、他のモデル試験は補完なしの警告付きで実行できます。公開情報の取得成功はキーの認証成功を意味しません。

2026-10-15 の確認では OpenRouter の `/api/v1/models` はキーなしで応答しましたが、公式 API リファレンスには Authorization 必須の記載もあります。キーなし取得を将来も保証するものではありません。応答が失敗した場合は NG とし、キー自体の認証失敗とは断定しません。

## 診断単独の TypeScript モデル処理

`runtime/model_catalog.ts` は `backend_server/conf/conf_model.py` 由来のモデル日付判定・絞り込み・OpenRouter 情報補完を移植した診断専用実装です。本体ファイルを変更せず、Python モジュールの import・子プロセス起動・venv 探索を行いません。元実装の変更時は合成フィクスチャと対照更新します。

`runtime/model_probe.ts` は固定設定をサーバー内で読み、固定 HTTPS モデル API の GET を実行します。キー値を引数・環境変数・ブラウザへ渡さず、モデルの文字列に紛れた既知キーも抑止します。Conf クラス、設定保存、OAuth fallback は呼びません。`runtime/model_runner.ts` は処理期限・同時実行数・終了時キャンセルを管理します。エラー本文やキー値はログへ出しません。

TypeScript ソースは開発時に既存 UI の esbuild で Node.js 18 向け `.mjs` に事前変換し、配布物を同梱します。通常起動時は TypeScript 実行機能・コンパイラ・npm install・Python が不要です。全体のセットアップ／クリーンアップ用 Python と、インストール一覧の Python 検出は従来どおりです。

移植前の2ファイルは比較専用の `tests/reference/` に保存しています。Node テストは保存済み合成ゴールデンで日付境界・DST・UTCオフセット・補完・空キャッシュ・順序を照合し、Python なしで実行できます。Python の参照テスト・ゴールデン再生成は開発時の任意確認です。実キーや外部モデル API はテストに使いません。

モデル確認は選択したボタンを押したときだけです。補完用の公開キャッシュがないときは警告を表示し、元と同じ未補完時の判定へ進みます。公開情報だけでは実キーの有効性・生成・課金の可否を検証しません。起動時の匿名公開一覧を除く自動キー試験や共通結果保存は行いません。全テストはインストール確認だけです。

## Vue UI の配布と開発

Vue 3 の SFC は `ui/src/` に分割しています。`App.vue` が認証・タブと共通 API、`インストール/インストールパネル.vue` がインストール一覧と詳細、`モデルキー設定/モデルキー設定パネル.vue` がモデルキーとモデル一覧、`外部連携設定/外部連携設定パネル.vue` が Hugging Face 読取・書込と Discord の設定状況を担当します。設定画面ごとの選択状態・表示・スタイル・テストを各機能フォルダへ内包し、`キー設定共通/` の設定取得・世代管理・公開キャッシュを共有します。外部連携は設定の有無のみ確認し、接続テストは未対応・未実施のままです。インストール専用の状態・診断実行は `インストール状態.mjs`、選択・表示処理は `インストール表示.mjs`、専用スタイルは `インストール.css`、回帰テストは同フォルダの `tests/` に内包します。共通の `StatusBadge.vue` とレイアウトは共有します。テンプレートはビルド時にコンパイルし、runtime compiler・CDN・unsafe-eval を使いません。

`static/` の事前ビルド成果物をリポジトリへ同梱するため、新規取得後も Node.js のみでブラウザ起動できます。Electron は従来の共有キャッシュを使います。通常起動は npm install・ビルド・依存ソフトウェアのダウンロードを行いません（公開モデル一覧は別途取得します）。ソースを変更すると起動前の SHA-256 マニフェスト照合で古い成果物を拒否します。

UI または runtime の TypeScript を変更した場合、配布物作成のため次を実行します。build は strict TypeScript 検査を先に実行します。開発用 lockfile は Electron の依存セットアップと独立です。

```sh
cd backend_diag/ui
npm ci
npm run build
npm run check
```

ソース・`runtime/*.mjs` と `static/app.js`、`static/style.css`、`static/index.html`、`static/build-manifest.json` を一緒にコミットしてください。ビルドは Vue のライセンスコメントを保持します。セットアップ後も変更を反映するには再ビルドが必要です。

## インストール確認の表示分類

左の最上位は「インストール確認」で、その下に次の 19 項目を表示します。

- ベース（6）: Python、uv、Node.js、npm、npx、Electron。
- CLI群（7）: Claude Code、OpenAI Codex CLI、GitHub Copilot CLI、Antigravity CLI、Grok Build、OpenCode、Ollama。
- その他拡張（6）: ffmpeg、ffprobe、ffplay、Chrome、OBS Studio、VS Code。

Python の検出では WindowsApps の Store エイリアスを除外します。実在する実行ファイル・仮想環境を優先し、必要に応じて `py.exe -3 --version` で確認します。エイリアスだけでは Python 導入済みとは判定しません。

Python、uv を先頭に表示します。CLI や拡張は利用する機能に応じて確認するもので、全 19 件が共通の起動必須条件ではありません。未検出は全体の故障判定ではありません。

### 今回の確認対象からの除外

旧静的調査の抽出候補 246 件から 227 件を除き、現在の確認対象を 19 件に絞っています。AiDiy 起動コマンド群、Hermes 本体・専用プラグイン・スキル・補助依存、macOS 音声再生（afplay）、GStreamer、Edge、Brave、OS 補助・シェル・開発・導入・配置用の補助ツール（Git / pip 等）は診断カタログに含めません。任意項目を再表示するチェックもありません。
実際のプログラムや機能を削除する変更ではありません。共通依存は非 Hermes の利用根拠で保持し、Hermes 専用の探索パスも除外します。
対象ソース・設定 3,333 件の調査履歴・マニフェストは保持します。調査範囲と今回の診断対象は異なり、除外内容は coverage.json の catalogSelection に記録しています。
モデルキー設定と外部連携設定は上部の独立タブです。MCP・CLI の試行は未実装です。

## 状態インジケーター

項目一覧・詳細は同じ5種類の状態バッジで表示します。上部の状態凡例行・状態フィルター・検索欄は置きません。
- 未確認（黒）: 未実施。OS 対象外の場合も未確認とし、詳細に対象外の理由を表示します。
- 未検出（黄）: 登録した探索先に見つかりません。
- OK（緑）: 存在確認、または固定バージョンコマンドの正常終了。存在のみ・版未取得の場合は詳細で区別します。認証や実機能の動作保証ではありません。
- NG（赤）: バージョンコマンドの非ゼロ終了、または確認した最低バージョン要件の不足。検出対象とは別の仮想環境まで否定しません。
- ERR（赤）: 起動・探索例外、タイムアウト、出力上限等により確認できません。

確認中は進行メッセージを表示し、別の判定状態にはしません。色に加えて必ず状態名も表示します。

## Electron と共通セットアップ

通常の `aidiy_diag` は Electron ウィンドウを開きます。`--browser`、`--no-open`、Codespaces、Linux の DISPLAY / WAYLAND_DISPLAY がない環境では Node.js の Web 版を使います。CI 環境も Web です。GUI 環境で Electron が未準備の場合は黙ってブラウザに切り替えず、セットアップまたは `--browser` を案内します。

全体 `_setup.py` は Diag ランチャーを最初に配置し、Git / Node.js の前提確認後に Diag の Electron を準備します。Node.js がないときもランチャー配置はできます。前提ツールの導入は従来どおり確認付きです。単体 `python backend_diag/_setup.py` は Node.js / npm の準備後に使います。Codespaces / Linux GUI なしでは Electron 導入をスキップします。

Electron は既存 `scripts/_setup_electron.py` を使い、配置済み、他コンポーネントの同版 dist、`_cache/electron` の共有 ZIP の順で再利用し、不足時だけ取得します。Diag は既存 frontend と同じ `^44.7.0` の Electron パッケージを使います。同版 Diag dist も後段 frontend から再利用でき、専用の別キャッシュは作りません。起動時の npm install / ダウンロードはしません。

Electron の認証 URL は親子プロセス専用 IPC で渡し、引数・環境変数・ログへ出しません。Windows の Electron は標準入力が常に EOF になるため、標準入力は使いません。renderer は sandbox / contextIsolation を有効、nodeIntegration を無効にします。非永続 session を使い、権限要求・別ウィンドウ・外部 navigation を拒否します。ウィンドウを閉じると診断サーバーも停止します。

実際の Electron GUI 起動はこの変更の検証環境では未確認です。テストでは共有セットアップ、同版再利用、起動分岐、URL受渡、Electron権限制限を mock / 一時ファイルで検証します。
