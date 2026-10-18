# AiDiy 診断

外部プログラムの導入状態を、ソースに記載された利用箇所と一緒に確認します。診断サーバー・インストール確認・キー設定・モデル確認は Node.js 18 以降の標準モジュールで動作します。診断の実行に Python は不要です。通常は Electron ウィンドウで表示し、--browser / Codespaces / GUI のない環境では Web で表示します。AIコア / DB の起動は不要です。

診断本体の起動には Node.js が必要です。一覧は Python、uv、Node.js、npm、npx、Electron の順です。Python はバックエンドで使用します。Python が無くても配置済みランチャー・直接 Node 起動は使えます。全体セットアップは既存方式に合わせ Python を使用します。

## フォルダ構成

ルート直下は公開起動入口とセットアップ・設定・案内だけにします。内部モジュールを追加するときは、担当する機能のフォルダへ置きます。

- `diag_main.mjs` / `aidiy_diag` / `aidiy_diag.cmd`: 外部から使う起動入口。
- `起動/`: Electron ウィンドウ・preload・起動監視・安全な診断ログ。
- `診断/`: インストール確認、MCP 状態、headless 実行、カタログと調査範囲。
- `モデル情報/`: キー確認、モデル・音声 JSON の合成、公開モデル一覧。`openrouter_models/` はこの機能専用の同梱キャッシュです。
- `runtime/`: モデル判定・通信の TypeScript と配布用 `.mjs`。
- `ui/` / `static/`: Vue ソース・ビルド設定と配布画面。
- `checks/` / `reference/`: 回帰テストとソース調査資料。

Electron の依存物は引き続き `backend_diag/node_modules/`、停止要求・安全ログも従来のルート直下に置きます。診断結果の保存先 `_AIDIY/aidiy_diag/` は変わりません。内部モジュールの移動時は import だけでなく、`import.meta.url` 基準のデータ・実行ファイル・リポジトリ位置とテスト fixture のコピー先も確認します。

画面の機能フォルダ・Vue パネル・状態管理・表示モジュールはタブ名に揃えます。共有のキー状態管理は `ui/src/キー設定共通/` を使います。

| タブ（左から） | 見出し | 主操作 | Vue 機能フォルダ |
|---|---|---|---|
| 導入状況 | 導入状況 | 状況確認 | `ui/src/導入状況/` |
| モデル一覧 | モデル一覧取得 | 一覧再取得 | `ui/src/モデル一覧/` |
| 外部連携 | 外部連携確認 | 状況確認（テストできる行を順次確認）・書込 | `ui/src/外部連携/` |
| 設定モデル | モデル動作確認 | 動作確認（全行を順次確認） | `ui/src/設定モデル/` |

外部連携は見出し行の「状況確認」（テストできる行を上から順に）と各行の「テスト」で、読み取り専用の認証確認を明示操作時だけ行います（下記「外部連携の認証確認」）。「書込」は直前の確認結果を `_AIDIY/aidiy_diag/integration_info.json` へ保存します。キー未設定・設定読込不可の行は確認せず、未実施と理由を表示します。設定モデルは見出し行の「再読込」と各行の「テスト」も使用できます。

右上ボタンの一括処理（各画面の状況確認・一覧再取得・動作確認）が終わると、一覧の1項目目を表示し、一覧・詳細を先頭までスクロールします。各行の「テスト」や中止では選択を維持します。タブ欄の「全テスト」は、導入状況（状況確認→書込）→モデル一覧（一覧再取得→書込）→外部連携（状況確認→書込）の順に実行し、実行中の画面へ表示タブを切り替え、終わったら導入状況タブへ切り替えます。外部連携の確認では、直前に読み直した設定を使い、モデル一覧の結果を消しません。API の `モデル試行`・`キー設定`・`診断`、タブ内部ID、保存JSON名は表示名とは別の互換識別子として維持します。

## 起動

```sh
node backend_diag/diag_main.mjs --browser
# ランチャー配置後
aidiy_diag                  # Electron 表示後、コマンドプロンプトへ戻る
aidiy_diag --browser        # ブラウザ起動・foreground
aidiy_diag --foreground     # Electron を foreground で起動（ログ・Ctrl+C）
aidiy_diag --wait           # --foreground と同じ
aidiy_diag --headless       # 画面を開かず全診断を最速で実行し、結果を保存
```

`--headless` は Electron・ブラウザ・HTTP 待受を使わず、全診断をコマンドラインで最速実行します（全項目を同時に確認し、結果は一覧順に表示）。全診断はインストール状況とモデル情報です。インストール状況は `_AIDIY/aidiy_diag/install_info.json`（状態・パス・バージョン・説明と集計）へ、モデル情報はテストできるプロバイダごとに `_AIDIY/aidiy_diag/<プロバイダ>_models_info.json` へ保存します。保存は一時ファイルからの置き換えで行い、例外・Ctrl+C・書込失敗など実行に失敗した場合は既存ファイルを更新しません。項目ごとの `未検出` / `ERR` などは診断結果として保存します。終了コードは成功 0、失敗 1、中断 130 です。`--headless` は他の引数と併用できません。

画面では「状況確認」で全項目が「確認中」で回り、確認が終わった項目から結果へ切り替わります（確認中は固定の `GET api/診断/進捗` で完了済みの結果だけを読みます。引数は受け付けません）。応答後は上から順に選択が追従し、最後に1項目目を表示します。確認が終わると「書込」が押せるようになり、このサーバーが直前に確認した結果を `--headless` と同じ形式で `_AIDIY/aidiy_diag/install_info.json` へ保存します（画面から値は送りません）。タブ欄の「全テスト」は、状況確認→書込のあと、一覧再取得→モデル情報の書込、外部連携の状況確認→書込まで続けて実行します。

### モデル情報ファイル（`<プロバイダ>_models_info.json`）

キー設定画面の「書込」（一覧再取得の後に押せます）・「全テスト」・`--headless` で、gemini / freeai / claude / openai / openai_oauth / grok / openrt / ollama / local のうちテストしたものを 1 ファイルずつ保存します。用途の分け方は本体の `get_chat_models` / `get_live_models` / `get_code_models` に合わせています。

保存形式は `形式: 2` です。選択候補は用途にかかわらず「区分名 → `{models}`」で取得できます。例: `chat.gemini_chat.models`、`code.claude_sdk.models`、`live.gemini_live.models`。区分名以下は各プログラムへそのまま渡せるよう `models` だけを持ちます。取得元などの説明や詳細情報はその外側に置きます。旧形式のファイルは次回の「書込」または `--headless` で置き換わります。

- `chat`: API から取得し本体と同じ条件で絞り込んだ一覧。`モデル` は作成日・トークン数・モダリティ付きの詳細配列として残します。選択候補は `gemini_chat` など本体の区分名をキーにした要素の `models` に置き、「モデルID: YYYY/MM/DD - モデルID」の一覧（作成日が無いものは `yyyy/mm/dd`、backend_local は固定候補の表示名）にします。詳細・選択候補とも作成日の新しい順です。Claude / Grok は本体に chat の選択区分がないため詳細だけを残し、CLI の選択候補は `code` に置きます。
- `live`（gemini / freeai / openai）: API で取得した live 対応モデル（Gemini は `bidiGenerateContent` 対応、OpenAI は `realtime`）から、`gemini_live` などの区分名をキーにした要素の `models` を直接生成します。Gemini / FreeAI はモデルIDに `native-audio` または `live` を含み、`transcribe` または `translate` を含むものを除外し、モデルIDの文字列降順で並べます。OpenAI は `whisper` または `translate` を含むものを除外し、作成日の新しい順です。表示名は「YYYY/MM/DD - モデルID」で、日付は API / OpenRouter の作成日 → モデル名の日付 → `yyyy/mm/dd` の順に採用します。設定ファイル由来のボイス・設定案・差分は保存しません。
- `code`: `claude_sdk` / `claude_cli` は Claude、`antigravity_cli` は Gemini、`codex_cli` は各ファイルの OpenAI API / OpenAI OAuth、`opencode_cli` は Ollama の取得モデルから `models` を生成します。`codex_cli` は `realtime` を含むモデルを除外し、同じ系列（`sol` / `luna` / `pro` など）は数値として比較した最新バージョンだけを残します。例: `gpt-6.1-sol` があれば `gpt-5.6-sol` は除外します。`-900k` などの別仕様は独立した系列として扱います。`aidiy_hermes` も OpenAI OAuth の取得モデルを使い、モデルIDに `openai_oauth/` を付けます。合成の `aidiy_hermes.models` には、導入済みCLIの `xx/auto`（CLI のモデルを維持して呼び出す選択肢）を追加します（下記）。Claude SDK / CLI はモデルIDから `haiku`・`sonnet`・`opus`・`fable` などの名前を抽出してキーに使い、同名は最新の1件へまとめます。表示名は「YYYY/MM/DD - バージョン付きモデルID」とし、最新バージョンを残します。`copilot_cli` は Claude / OpenAI / OpenAI OAuth のファイルに出力し、Claude は系列ごとの最新モデルをバージョン付きIDのキーで保存し、数字間の `-` を `.` に変換します（キー・表示名とも `claude-haiku-5.5` など）。OpenAI / OpenAI OAuth は `codex_cli` と同じ候補で保存します。詳細配列には元のモデルIDを保持します。作成日・並び順は chat と共通です。
- 固定候補は Grok（`grok_cli`）と backend_local（`local_chat`）だけです。aidiy_diag が管理し、本体は合成JSONから読みます。それ以外は取得に失敗した場合に候補を空にし、状態・説明・警告を残します。

Gemini / FreeAI はモデルIDに `lyria` を含むものを詳細・chat・live・code すべての出力対象から除外します。`antigravity_cli` もこの絞り込み後の候補から生成します。

モデル情報の生成・保存は `_config` 上のモデル設定ファイルに依存しません。API 接続用のキー・ログイン情報の読み取りは従来どおりです。保存するのは、このサーバーが直前に取得した結果と Grok / local の固定候補だけで、画面から値は送りません。

プロバイダ別ファイルへ `xx/auto` は挿入しません（旧表記 `xx/same` が残っていても合成時に除外します）。合成の `code_models_info.json` は導入済みCLIの区分だけを出力します（`claude_sdk` もClaude CLIの導入が必要）。`aidiy_hermes.models` だけは特別に、導入済みCLIの `xx/auto` をCopilot → Claude → Codex → Antigravity → Grok → OpenCodeの順で先頭へ追加し、その後に取得したモデルを並べます。導入判定はインストール診断と同じ探索先での実行ファイルの存在確認です。

音声候補は `live_voices_info.json` に `{gemini_live: {voices: {...}}, freeai_live: {voices: {...}}, openai_live: {voices: {...}}}` の形式で保存します。固定定義は `モデル情報/voices_info.mjs` で管理します。キーの確認成功と現在の設定状態に合わせて出力し、未設定・確認失敗のプロバイダは含めません。FreeAIの声はGeminiと同じ定義です。個別更新では他の有効な確認済み候補を保持し、キーが無効化された場合は除外します。

Copilot単独契約向けの例外として、Copilot CLIが導入済みで合成後の `copilot_cli.models` が空の場合だけ、指定のClaude / GPT固定8モデルを指定順・指定日付で補います。取得候補が1件でもあれば補わず、プロバイダ別ファイルへは固定8モデルを保存しません。

プロバイダ別ファイルの書込後に、同じ保存先の全プロバイダ別ファイルを読み、`chat_models_info.json` / `live_models_info.json` / `code_models_info.json` も生成します。chat / live の合成時は FreeAI を先頭に並べます。code は Claude / OpenAI 系を前、`antigravity_cli` を最後に並べます。合成ファイルのルートは `gemini_chat` / `gemini_live` / `codex_cli` などの区分名で、それぞれ `{models}` だけを持ちます。詳細配列や診断の説明はプロバイダ別ファイルに残します。同じ区分名・モデルIDはマージし、表示名が重複するときは日付の新しいものを優先します（実日付は `yyyy/mm/dd` より優先）。個別テスト後の書込でも、他プロバイダの保存済み候補を合成に含めます。

`python backend_diag/_setup.py` または全体の `python _setup.py` で `~/.local/bin` にランチャーを作成します。全体セットアップのDiagは `[y]` の表示だけで選択入力はありません。Windows は `aidiy_diag.cmd` です。`backend_diag/aidiy_diag` / `backend_diag/aidiy_diag.cmd` からも直接起動できます。

Electron の初回表示は Code / Live / Term / IDE / Discord と共通の `frontend_ide/host/scripts/window-opening.cjs` を使います。中央55%から750msで拡大し、描画を待ってから本画面を表示、内容を450msでフェード表示します。実ウィンドウを連続リサイズしないため、Windowsの未描画の白い縁を避けます。ブラウザ版・headlessには適用しません。`desktop-opening` 中は内容を隠し、演出完了後に起動済みを通知します。共通演出の仕様を変更する場合は6種類への影響を確認してください。`node --test backend_diag/checks/desktop.check.mjs` で読込・演出・表示通知の順序、演出中の終了・描画失敗と既存IPCの安全境界を確認できます。実OSでの拡大・DPI・最前面表示は別途目視確認が必要です。

上部は Term と同じ高さのタイトルバー・ウィンドウ操作・接続バーです。シアンの線は Tools の接続成功、黒は未接続を示します（Tools の確認は常に有効で、ON/OFF・再確認の操作はありません）。診断自体の接続とは別です。Tools は `_config/AiDiy_key.json` の `PORT_TOOLS`（省略時8095）に対して、固定 loopback の `/aidiy_code_agents/ping` だけを10秒間隔で確認します。キー・モデル・エージェントの実行は行いません。切断・画面破棄で確認を停止します。

「導入状況」「モデル一覧」「外部連携」「設定モデル」の Vue タブです。初期状態は未確認です。導入状況パネル右上の「状況確認」で検出・更新します。タブ欄右の「全テスト」は、導入状況・モデル一覧・外部連携をそれぞれ確認して書き込みます（前述）。左側でカテゴリを開閉し、項目を選ぶと右側でパス・バージョン・利用機能・参照ソースを表示します。

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

通常の Electron 起動は表示確認後にコマンドプロンプトへ戻ります。Electron 版のウィンドウは1つだけで、起動中にもう一度 `aidiy_diag` を実行すると、新しいウィンドウ・サーバーは作らず既存のウィンドウを前面に表示して終了コード 0 で戻ります（Electron の単一インスタンスロック。ブラウザ版・headless は対象外）。ウィンドウを閉じると HTTP・診断子プロセスも終了します。`--foreground` / `--wait`、`--browser` / `--no-open`、Codespaces・GUI のない環境では起動ターミナルの Ctrl+C で終了します。キーも失効します。`python backend_diag/_cleanup.py` または全体クリーンアップで、この作業コピーのランチャーだけを解除します。別コピーのランチャーは削除しません。全体起動 `python _start.py` では起動選択より先に必ず `aidiy_diag --headless` の完了を待ち、モデル合成JSONを生成します。DiagのGUI起動を選ぶ質問はなく、診断の実行・保存に失敗した場合はサービス起動を中止します。単独ランチャーで起動した診断も、同じ作業コピーのクリーンアップで終了します。停止通知は `.stop-request` の短いランダム識別子のみで、PID・認証キー・診断結果は保存しません。

## 追加と検証

`診断/catalog.json` に実際のソース参照を伴う項目を追加します。`version_args: null` は存在確認のみです。GUI 起動やネットワーク・モデル取得を伴うコマンドは version 検査に登録しないでください。API 経由で項目を追加・変更する機能はありません。

```sh
node --test backend_diag/checks/*.check.mjs backend_diag/checks/*.check.cjs
node --test backend_diag/ui/src/*/checks/*.check.cjs
node --check backend_diag/static/app.js
node backend_diag/ui/verify.mjs
```

回帰テストは Windows / POSIX の両方で通します。パス区切り、CRLF でのチェックアウト（ハッシュ照合は LF に正規化）、Windows の SIGTERM（シグナル終了として報告）、npm / npx の隣接 CLI 実行を前提にしないでください。

`checks/check_setup.py` は Python のまま残したセットアップ／起動／クリーンアップ（`_setup.py` / `_start.py` / `_cleanup.py`）の確認です。Python がある開発環境では任意で `python -m unittest backend_diag/checks/check_setup.py -v` を実行できます。

Playwright と Chromium が利用できる検証環境では `node backend_diag/checks/ui_browser.mjs` で、合成データのみの実ブラウザ回帰を実行できます。Playwright は依存に含めないため、実行ディレクトリか `backend_diag` で `npm i --no-save playwright-core` を行ってください。実キー読取・外部モデル API 呼出は行いません。必要なら `CHROMIUM_PATH` で既存ブラウザを指定します。

ブラウザ確認では、認証前拒否、診断開始・再チェック、カテゴリ開閉、選択詳細、狭い画面、通常 URL とパス型プロキシを確認してください。診断結果や認証 URL を公開ログ・スクリーンショットに含めないでください。

## カタログの調査範囲

基準コミット `8adbdb484cafe31e145c4fe362897d2af1077eb1` の Git tree 全 4,950 ファイルから、対象ソース・設定・スクリプト・テンプレート・テスト・manifest/lockfile **3,333 件**を列挙し、全件の全文を静的走査しました。未取得・未読は 0 件。246 候補から今回の確認対象 **19 項目**を採用し、各項目の詳細に参照パスと行番号を表示します。コードの実行・インストール試験を行ったという意味ではありません。

通常の Markdown ガイド・skill 本文（README/AGENTS を除く）、画像・音声・モデル・Office/PDF、LaTeX 文書資産、ライセンス・非実行テキスト等は対象外です。実行可能な skill スクリプトやコード例は含めます。省略のある Python 教材 3 件は AST 解析できませんでしたが、全文テキストを走査済みです。全リポジトリの全バイトを検証したという主張ではありません。

- [診断/coverage.json](./診断/coverage.json): 件数、基準コミット、除外、制限、AST テキスト代替走査の記録。
- [reference/source-manifest.json](./reference/source-manifest.json): 対象 3,333 件のパスと元の Git blob SHA。
- [reference/source_scan.ts](./reference/source_scan.ts): 対象コードを実行しない、依存パッケージなしの TypeScript 走査スクリプト。Python は字句解析で呼出し・for・代入・dict 単位に候補を抽出します（旧 Python AST 版と同じ候補を出すことを確認済み。構文エラーのファイルも走査します）。基準コミットの作業コピーに対し Node.js 22.18+ で `node backend_diag/reference/source_scan.ts REPOSITORY OUTPUT_JSON COMMIT backend_diag/reference/source-manifest.json` を実行すると候補抽出を再現できます。抽出候補からカタログへの分類にはソース確認が必要です。

Python/Node のライブラリ、内部スクリプト、shell builtin、Git subcommand、モデル ID を外部実行ファイルと混同しません。19 項目すべてが必須ではなく、選択機能に応じて必要な項目を含みます。ユーザー設定の任意コマンドや動的生成、リモート・コンテナ・WSL・Android 側の導入状態は、ホストの PATH 確認だけでは保証できません。

## キー設定状況とモデル一覧

「キー設定状況」は診断サーバーの TypeScript 実装から固定ファイル `_config/AiDiy_key.json` の既知キーだけを読み取り、設定済 / 未設定を表示します。設定 JSON の値、長さ、末尾、ハッシュはブラウザに返しません。ファイル未作成は未設定、JSON 不正や読込不可は確認不可です。既存 conf クラスの初期化・設定変更は行いません。

一覧は既存 config の固定キー順（Gemini、FreeAI、Claude、OpenAI、OpenAI OAuth、Grok（xAI）、OpenRouter、Ollama（ローカル）、ローカル（backend_local）、Hugging Face 読取・書込、Discord）です。Azure OpenAI と GitHub Copilot はモデル一覧の確認に対応しないため画面に表示しません（サーバーの登録とモデル名からのキー値秘匿の対象には残します）。表示対象外の設定項目は省き、JSON の任意の並べ替えには追従しません。左側でキーを選択し、右側で説明・テスト結果・モデル一覧を確認できます。キーの存在だけでは OK にしません。起動時には匿名の公開 OpenRouter 一覧だけを取得します。タブ移動・全テストから個別キーの API は呼びません。各行の「テスト」は明示操作時だけ固定プロバイダーのモデル一覧 API を読み取ります。会話生成は別の「設定モデル」で明示操作した場合だけです。

- キー試験の表示は未実施 / OK / NG。未設定・未対応の項目は未実施で、理由を表示します。OpenRouter の個別テストは設定キーを固定 GET `https://openrouter.ai/api/v1/key` で確認し、成功時だけ公開キャッシュから候補を表示します。公開 `/models` の応答だけでは認証成功にしません。キー未設定は未実施、認証・通信・応答形式の確認失敗は NG です。起動時・明示再取得の公開要求にはキーを送りません。
- OK はモデル一覧 API の応答確認であり、生成可能性・課金状態の保証ではありません。公開モデル一覧の場合はキー有効性の検証にもなりません。
- Gemini / FreeAI / Claude / OpenAI / OpenRouter / Ollama Cloud（外部連携は Hugging Face / Discord）の固定 HTTPS 宛先だけを使います。OpenAI OAuth は `~/.codex/auth.json`（`CODEX_HOME`）、Grok（xAI）は `~/.grok/auth.json` のログイン情報があれば API キーが無くても設定済とし、それぞれ `chatgpt.com/backend-api/codex/models`（本体と同じく非表示・廃止モデルを除き優先度順）と `cli-chat-proxy.grok.com/v1/models`（非表示を除き、作成日が分かるものは 240 日以内）からモデル一覧を取得します。ログイン情報は読むだけで、トークンの更新（ファイルの書換え）はしません。期限切れのときは各 CLI での再ログインを案内します。
- 絞り込み・並び順は本体（`backend_server/conf/conf_model.py` の取得関数と `get_chat_models`、OAuth は `command_hermes/hermes_cli/codex_models.py`）に合わせています。OpenAI / OpenRouter の表示一覧は旧 Sol（`gpt-6-sol` 系）を除き、補完用の公開一覧は除きません。OpenRouter の別名（`~provider/model`）も本体と同じく表示します。OpenAI OAuth は非表示・廃止を除いて優先度順に並べ、将来版と `-900k` 版を補完します。API で取れないときや空一覧の場合は、Copilot 既定の OpenAI 系4モデルで補完し、PASS（補完・実応答未検証）として表示します。OAuth 未設定時は補完しません。Grok は本体がもともと固定候補（`grok-4.7` / `grok-4.6`）を流し込む系統のため、API で取れない場合は固定候補を表示して PASS（黄）とし、取れなかった理由を説明に残します。backend_local も本体は API を使わず固定候補（`CHAT_LOCAL_MODELS`）を流し込む系統のため、aidiy_diag が持つ同じ固定候補を表示して PASS（黄）とします。Ollama は本体と同じくキーを使わず、ローカルの Ollama（`ollama list` と同じ一覧、新しい順）を `127.0.0.1:11434/api/tags` から読みます（プロセスは起動しません）。
- 「一覧再取得」は設定状況を読み直し、モデル一覧のテストできる行を上から順に取得します。取得中の行へ選択と右側のモデル一覧が追従し、終わると1項目目を表示します。Azure、Copilot、Hugging Face、Discord の個別テストは未対応です。
- キーは当該サービスへのモデル一覧要求（OpenRouter はキー確認 GET）にだけ使用し、任意 URL / 環境変数の base URL は採用しません。外部 HTTPS は既存の HTTP_PROXY / HTTPS_PROXY / NO_PROXY（小文字優先）に従い、TLS 検証を維持して CONNECT します。proxy 失敗時の直接接続への切替はしません。loopback は常に直接接続です。ALL_PROXY / SOCKS / OS proxy 自動読取は対象外です。詳細は [Node.js 外部 API 通信の注意点](../_AIDIY/knowledge/共通,Node.js外部API通信の注意点.md) を参照してください。リダイレクト禁止、要求ごとに期限・応答上限を設けます。モデル処理全体は 25 秒・同時2件、HTTPS 要求ごとは8秒・応答1 MiB、設定ファイルは128 KiB、表示モデルは500件上限です。終了・期限切れでは通信を中止し、Google のページ取得は最大20回です。表示の取得範囲・警告を確認してください。エラー本文やヘッダーは返しません。
- 外部連携の認証確認（見出し行の「状況確認」・各行の「テスト」・タブ欄の「全テスト」のときだけ。起動・タブ表示・一覧再取得・headless では実行しません）:
  - Hugging Face 読取・書込: 固定 GET `https://huggingface.co/api/whoami-v2`（Bearer）。トークンが有効なら OK。書込は権限が `write` なら OK、細粒度トークンで `*.write` 権限を含む場合は PASS（対象範囲は未確認）、それ以外は NG です。
  - Discord Bot: 固定 GET `https://discord.com/api/v10/users/@me`（`Bot` 認証）。Bot トークンとして認証できれば OK、Bot でなければ NG です。メッセージ送信・Gateway 接続はせず、Bot はオンラインになりません。
  - 表示するのは状態・固定の説明と、固定の文字種・64文字以内のユーザー名 / Bot 名・権限種別だけです。メール・組織・トークン名・応答本文は返しません。キー未設定は通信せず未実施です。結果はモデル情報の保存対象に含めません。
  - OK は認証と権限の確認で、個別のリポジトリ・チャンネルで実際に操作できることは保証しません。
- 外部連携の `integration_info.json` は `{形式:1, 種類:'外部連携', 保存日時, 件数, 集計, 項目:[{id, 名前, キー名, 設定済み, 状態, 説明, 確認日時}]}` です。登録した3行を常に保存し、確認していない行は未実施と理由を残します。キー値・応答本文は含みません。
- モデル一覧の「確認内容」は、テスト（OK / NG）後は「接続はテストで確認しました」と表示します。
- 設定状況を読み直す操作（一覧再取得・外部連携の状況確認）では前のテスト表示を消します。別のキーに変更した場合は再テストしてください。テスト結果はブラウザのメモリ内だけで、再起動・再読込後に引き継ぎません。

### 起動時の公開モデル取得

HTTP サーバーの起動後、匿名の公開 OpenRouter モデル一覧を一度だけ非同期で取得します。この操作は設定ファイルを読み取らず、Authorization も送りません。取得に失敗した場合も画面・インストール確認・他の個別テストは使えます。

パネル見出しに「公開モデル一覧取得:」として、ネットワーク取得は「OK」、同梱キャッシュは「キャッシュ利用」、ほかに「取得中」「失敗」「未取得」を 1 か所だけ表示し、個別キーの未実施 / OK / NG とは混ぜません。「再取得」ボタンはキャッシュ利用時だけその右に表示する明示操作で、同時要求は1回にまとめます。設定状況更新では公開キャッシュを消しません。

キャッシュは起動中の Node メモリだけに置き、再起動で破棄して再取得します。元の Python 判定を移植した処理で日付絞り込みした時点のスナップショットです。個別テストはこの整形済み公開情報を同じ Node プロセス内で参照し、OpenRouter を毎回再取得しません。時間が経った情報を更新したい場合は再取得してください。共通システムへの結果保存はありません。

OpenRouter の先行手動テストは要求しません。公開情報が取得中・失敗・未取得でも、他のモデル試験は補完なしの警告付きで実行できます。公開情報の取得成功はキーの認証成功を意味しません。

起動時に公開一覧を取得できない場合は、同梱の `モデル情報/openrouter_models/openrouter_models.zip`（OpenRouter `/api/v1/models` の応答を保存したもの）を一時フォルダ（`%TEMP%idiy_diag` / `$TMPDIR/aidiy_diag`）へ展開し、ネットワーク取得と同じ日付絞り込み・安全化を通して使います。展開は Node 標準の zlib だけで行い、外部コマンドは使いません。キー設定画面の見出しには「公開モデル一覧取得: OK」（ネットワーク取得、緑）または「キャッシュ利用」（同梱キャッシュ、黄）を表示します。同梱キャッシュは保存時点の一覧なので、新しいモデルは含まれません。

2026-10-15 の確認では OpenRouter の `/api/v1/models` はキーなしで応答しましたが、公式 API リファレンスには Authorization 必須の記載もあります。キーなし取得を将来も保証するものではありません。応答が失敗した場合は NG とし、キー自体の認証失敗とは断定しません。

## 診断単独の TypeScript モデル処理

`runtime/model_catalog.ts` は `backend_server/conf/conf_model.py` 由来のモデル日付判定・絞り込み・OpenRouter 情報補完を移植した診断専用実装です。本体ファイルを変更せず、Python モジュールの import・子プロセス起動・venv 探索を行いません。元実装の変更時は合成フィクスチャと対照更新します。

`runtime/model_probe.ts` は固定設定をサーバー内で読み、固定 HTTPS モデル API の GET を実行します。キー値を引数・環境変数・ブラウザへ渡さず、モデルの文字列に紛れた既知キーも抑止します。Conf クラス、設定保存、OAuth fallback は呼びません。`runtime/model_runner.ts` は処理期限・同時実行数・終了時キャンセルを管理します。エラー本文やキー値はログへ出しません。

TypeScript ソースは開発時に既存 UI の esbuild で Node.js 18 向け `.mjs` に事前変換し、配布物を同梱します。通常起動時は TypeScript 実行機能・コンパイラ・npm install・Python が不要です。全体のセットアップ／クリーンアップ用 Python と、インストール一覧の Python 検出は従来どおりです。

`checks/reference/model-golden.json` は、移植前の Python 実装から生成して凍結した合成ゴールデンです。Node テストはこれで日付境界・DST・UTCオフセット・補完・空キャッシュ・順序を照合します。移植前の Python 参照実装と再生成スクリプトは削除済みのため、ゴールデンは TypeScript 実装の出力で上書きしないでください。実キーや外部モデル API はテストに使いません。

モデル確認は選択したボタンを押したときだけです。補完用の公開キャッシュがないときは警告を表示し、元と同じ未補完時の判定へ進みます。公開情報だけでは実キーの有効性・生成・課金の可否を検証しません。起動時の匿名公開一覧を除く自動キー試験や共通結果保存は行いません。全テストはインストール確認だけです。

## Vue UI の配布と開発

画面から共有する状態表示は `共通表示/状態バッジ.vue` を使用します。タイトルバー・ウィンドウ操作・Tools 接続は既存の `ウィンドウ/` にまとめます。日本語の部品名は既存画面と同様に `<component :is="状態バッジ">` で描画します（日本語タグを直接書かない）。内部の部品名と import 名は日本語の機能名に揃え、API・保存JSON・Vue props・DOM属性の既存名は互換性のため維持します。新しい部品の追加前に、この共通部品と各機能フォルダを確認してください。

Vue 3 の SFC は `ui/src/` に分割しています。`App.vue` が認証・タブと共通 API、`導入状況/導入状況パネル.vue` がインストール一覧と詳細、`モデル一覧/モデル一覧パネル.vue` がモデルキーとモデル一覧、`外部連携/外部連携パネル.vue` が Hugging Face 読取・書込と Discord の設定状況を担当します。設定画面ごとの選択状態・表示・スタイル・テストを各機能フォルダへ内包し、`キー設定共通/` の設定取得・世代管理・公開キャッシュを共有します。外部連携は設定の有無のみ確認し、接続テストは未対応・未実施のままです。インストール専用の状態・診断実行は `導入状況状態.mjs`、選択・表示処理は `導入状況表示.mjs`、専用スタイルは `導入状況.css`、回帰チェックは同フォルダの `checks/`（`*.check.cjs`）に内包します。共通の `共通表示/状態バッジ.vue` とレイアウトは共有します。テンプレートはビルド時にコンパイルし、runtime compiler・CDN・unsafe-eval を使いません。

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

左の最上位は「状況確認」で、その下に次の 19 項目を表示します。

- ベース（6）: Python、uv、Node.js、npm、npx、Electron。
- CLI群（7）: Claude Code、OpenAI Codex CLI、GitHub Copilot CLI、Antigravity CLI、Grok Build、OpenCode、Ollama。
- その他拡張（6）: ffmpeg、ffprobe、ffplay、Chrome、OBS Studio、VS Code。

Python の検出では WindowsApps の Store エイリアスを除外します。実在する実行ファイル・仮想環境を優先し、必要に応じて `py.exe -3 --version` で確認します。エイリアスだけでは Python 導入済みとは判定しません。

Python、uv を先頭に表示します。CLI や拡張は利用する機能に応じて確認するもので、全 19 件が共通の起動必須条件ではありません。未検出は全体の故障判定ではありません。

### 今回の確認対象からの除外

旧静的調査の抽出候補 246 件から 227 件を除き、現在の確認対象を 19 件に絞っています。AiDiy 起動コマンド群、Hermes 本体・専用プラグイン・スキル・補助依存、macOS 音声再生（afplay）、GStreamer、Edge、Brave、OS 補助・シェル・開発・導入・配置用の補助ツール（Git / pip 等）は診断カタログに含めません。任意項目を再表示するチェックもありません。
実際のプログラムや機能を削除する変更ではありません。共通依存は非 Hermes の利用根拠で保持し、Hermes 専用の探索パスも除外します。
対象ソース・設定 3,333 件の調査履歴・マニフェストは保持します。調査範囲と今回の診断対象は異なり、除外内容は 診断/coverage.json の catalogSelection に記録しています。
モデル一覧と外部連携は上部の独立タブです。「設定モデル」は Tools 接続中だけ表示します。

## 状態インジケーター

項目一覧・詳細は同じ5種類の状態バッジで表示します。上部の状態凡例行・状態フィルター・検索欄は置きません。
- 未確認（黒）: 未実施。OS 対象外の場合も未確認とし、詳細に対象外の理由を表示します。
- 未検出（黄）: 登録した探索先に見つかりません。
- OK（緑）: 存在確認、または固定バージョンコマンドの正常終了。存在のみ・版未取得の場合は詳細で区別します。認証や実機能の動作保証ではありません。
- NG（赤）: バージョンコマンドの非ゼロ終了、または確認した最低バージョン要件の不足。検出対象とは別の仮想環境まで否定しません。
- ERR（赤）: 起動・探索例外、タイムアウト、出力上限等により確認できません。

確認中は進行メッセージを表示し、別の判定状態にはしません。色に加えて必ず状態名も表示します。モデル一覧・設定モデルの「未実施」は「未検出」と同じ黄色、「未確認」は黒系です。各画面は共通バッジの鮮やかな黄・緑・赤・青を使い、文字とのコントラスト比4.5:1以上を維持します。

## Electron と共通セットアップ

通常の `aidiy_diag` は Electron ウィンドウを開きます。`--browser`、`--no-open`、Codespaces、Linux の DISPLAY / WAYLAND_DISPLAY がない環境では Node.js の Web 版を使います。CI 環境も Web です。GUI 環境で Electron が未準備の場合は黙ってブラウザに切り替えず、セットアップまたは `--browser` を案内します。

全体 `_setup.py` は Git / Node.js の前提確認後、共通セットアップ（AI CLI 導入の待機を含む）→ Diag ランチャー配置・Electron準備 → local の順で実行します。共通や local が未選択ならその段階だけをスキップします。前提ツールの導入は auto 選択時も従来どおり確認付きです。単体 `python backend_diag/_setup.py` は Node.js / npm の準備後に使います。Codespaces / Linux GUI なしでは Electron 導入をスキップします。

Electron は既存 `scripts/_setup_electron.py` を使い、配置済み、他コンポーネントの同版 dist、`_cache/electron` の共有 ZIP の順で再利用し、不足時だけ取得します。Diag は既存 frontend と同じ `^44.7.0` の Electron パッケージを使います。同版 Diag dist も後段 frontend から再利用でき、専用の別キャッシュは作りません。起動時の npm install / ダウンロードはしません。

Electron の認証 URL は親子プロセス専用 IPC で渡し、引数・環境変数・ログへ出しません。Windows の Electron は標準入力が常に EOF になるため、標準入力は使いません。renderer は sandbox / contextIsolation を有効、nodeIntegration を無効にします。非永続 session を使い、権限要求・別ウィンドウ・外部 navigation を拒否します。ウィンドウを閉じると診断サーバーも停止します。

実際の Electron GUI 起動はこの変更の検証環境では未確認です。テストでは共有セットアップ、同版再利用、起動分岐、URL受渡、Electron権限制限を mock / 一時ファイルで検証します。

## 空候補の仮補完

- chat / live / code の合成 JSON は、モデルが0件のプロバイダ区分を含めません。CLI 絞り込み・Copilot 固定候補・Hermes 経路の合成後に判定します。chat の backend_local 固定4候補は維持します。
- OpenRouter は現在キー設定済み、かつ今回保持しているキー確認済み結果だけを合成します。保存済みの認証確認だけでは合成せず、設定再読込後は再テストが必要です。画面を開いたままキーを差し替えた場合も、サーバー内の確認結果と現在キーを比較して無効化します（キー・指紋は保存や画面送信をしません）。
- chat が空または local_chat のみなら、設定の CHAT_AI_NAME と対応するモデルを local より前に補完します。既存 local の候補・順序は保持し、同一候補は重複させません。local 以外が1件でもあれば補完しません。
- live 全体が空なら、設定の LIVE_AI_NAME と対応するモデルを補完します。設定不存在・空値・未対応プロバイダなら空のままです。code 全体が空なら従来どおり aidiy_hermes / auto を補います。config 自体は変更しません。
- config 補完と OAuth の4候補は「仮設定（未検証）」です。認証・CLI導入・生成可否を保証しません。OAuth 取得成功時は取得結果を優先し、4候補で補完できたときは PASS とします。認証確認は成功に変更しません。
- live_voices_info.json は FreeAI / Gemini / OpenAI の3区分を常時保存します。既存の音声定義・順序を使い、音声候補の存在は認証成功を意味しません。
- 認証方式の参照: [OpenRouter Get current API key](https://openrouter.ai/docs/api/api-reference/api-keys/get-current-key)。キー確認は GET のみです。別タブの config モデル試行は会話生成・課金が発生し得ます。
- `checks/node-only-startup.check.mjs` は隔離フォルダに設定ファイルを作らず、本物の `diag_main.mjs --headless` を実行します。HOME と PATH を隔離し、通信をオフライン mock にして同梱公開キャッシュを使い、local 4件・Liveモデル0件・Hermes auto 1件・音声3区分と、設定ファイル未作成の維持を確認します。

## 設定モデル（手動のみ）

Tools 接続中に専用タブで開始すると、`_config/AiDiy_key.json` の現在の CHAT / LIVE / CODE1〜6 / TASK plan・do・check / TEAM plan・do・check の15行へ、固定の「おはよう」を順番に送ります。設定ファイルは読み取りだけで、既存 conf クラスの初期化・補完保存は行いません。CODE2〜6 の NAME=auto は CODE1 の NAME と MODEL を継承します。モデルや音声だけを表示し、キーや作業パスは返しません。

見出し行の「再読込」で一覧を更新し、各項目の「テスト」でその1行だけ、または「動作確認」で全行を確認できます。同一設定の共有対象はサーバーが返し、その全行を同時に「テスト中」・結果へ更新します。個別テストでは設定版が同じ他の行のテキスト結果を残しますが、以前の音声は次の開始時に失効します。

- Chat は `chat_llms_run`、Code と Task / Team の選択モデルは `code_agents_run` を実際の MCP Streamable HTTP で呼びます。Task / Team の業務実行・投入は行いません。既存の通常 MCP 契約を使い、診断専用の CLI・認証・provider モードは追加しません。Code の権限は設定値を渡し、バックアップ検証ループは挨拶試行では実行しません。接続先 MCP の実際の利用可否と応答で結果を判定します。
- Live は Tools の非公開 `POST /internal/live_model_check` で固定メッセージに対する実際の応答を確認します。接続準備は最大20秒、準備完了後に10秒の安定待ちを挟み、固定テキストを送信して最大30秒応答を待ちます。終了処理の余裕を含め HTTP は75秒、1行は90秒、全実行は30分に制限します。音声セッションの接続成功だけを OK にしません。実際に返った PCM16・mono・24kHz の音声が1秒以上ある場合は保存・再生でき、テキストがなくても音声応答として OK にします。通常の有効なテキスト応答も引き続き OK です。音声が1秒未満の場合は保存しません。
- 返された音声は最大30秒・1,440,044バイトの WAV に限り、`_temp/aidiy-diag-audio-*` の専用一時フォルダへ保存します。フォルダは700、ファイルは600で作成し、外部指定パスを受け付けず、登録した通常ファイルだけを開きます。保存は最大16件・10分です。完了後は再生でき、次の開始・実行中の取消・設定変更・終了時に削除します。音声取得は認証付き同一 origin の GET `/api/モデル試行/音声/{音声ID}` のみで、画面へローカルパスやbase64は渡しません。画面は結果を受け取った時点で音声を取得して再生ボタンを表示し（保存期限後も同じ画面では再生可能）、再生ボタンを押して聴きます。自動再生はしません。
- 同じ実行内で transport・プロバイダ・モデル・音声と設定版が同じ行だけ結果を共有します。Chat と Live は共有しません。auto は動的選択のまま渡し、実行モデルが返らなければ未確認として表示します。
- 空応答・エラー・未設定・未対応は OK にしません。API キーの利用と料金が発生する場合があります。開始は利用者の明示操作だけで、起動・タブ表示・headless・既存「全テスト」から実行しません。
- 認証付き GET `/api/モデル試行` は表示情報だけ、POST `/api/モデル試行/開始` は一時実行を作成し、POST `/api/モデル試行/{実行ID}/{行ID}` は順序を確認して1行だけ実行します。いずれも利用者指定の本文・URL・プロンプトを受け付けません。DELETE `/api/モデル試行/{実行ID}`、画面切断、タイムアウトで中止し、MCP セッションを破棄します。設定変更時は結果を流用せず再開始します。
- 個別テストは POST `/api/モデル試行/開始/{行ID}` で1行の実行順を作成します。行IDは上記15役割のみ受け付け、全件と同じ認証・Tools接続・設定版・重複判定・中止処理を使います。
- MCP SDK は文字列戻り値を `structuredContent.result` に包むため、その中の JSON を解析して `status` と応答を判定します。オブジェクト形式の `structuredContent` と従来の `content[].text` にも対応します。外側の MCP 成功だけで会話を OK にしません。
- 実キーを使わない回帰確認: `node --test backend_diag/checks/model-trials.check.mjs backend_diag/checks/model-trial-audio.check.mjs`。15行、継承、重複、設定変更、MCP 初期化・SSE・セッション破棄、認証、切断、1秒の音声境界・認証再生・一時ファイル期限・symlink保護・保存中の取消を mock / 合成WAV で検証します。実モデル・CLI・音声の疎通は利用者環境での明示試行が必要です。
- 実 SDK 契約確認: Tools と同じ `mcp>=2,<3`・FastAPI・uvicorn を持つ Python を環境変数 `DIAG_TEST_PYTHON` に指定し、`node --test backend_diag/checks/model-trials-sdk.check.mjs` を実行します。実際の Chat / Code ツール登録と MCP SDK の初期化・セッション・SSE・文字列結果、実 Live 内部 HTTP ルートを一時 loopback サーバーで検証します。モデル実行と Live アダプターだけを合成し、キー・有料 API・稼働中の Tools は使いません。環境変数未指定時はこの契約テストをスキップします。
- 行別ボタンと配色は `node --test backend_diag/checks/status-badge.check.cjs backend_diag/ui/src/設定モデル/checks/設定モデル.check.cjs` で確認します。実ブラウザの任意確認は `node backend_diag/checks/model-trials-browser.mjs`。既存 Chrome / Edge（必要なら `CHROME_PATH`）を使い、合成データで1回だけの実行・共有表示・見出し配置・狭幅を確認し、`temp/diag-trial-browser/`（`DIAG_SCREENSHOT_DIR` で変更可）へ画像と結果を保存します。

## 判断用モデル一覧

`モデル情報/decisions_info.mjs` が `_AIDIY/aidiy_diag/decisions_models_info.json` を生成する。既存の `*_models_info.json` 命名を使用し、`desisions_model_info.json` は作成しない。スキーマは `{openai_oauth: {models: {モデルID: 表示名}}, openai_decisions: ..., freeai_chat: ..., gemini_chat: ...}`。表示名は `YYYY/MM/DD - ID`、取得日が不明なら `yyyy/mm/dd - ID`。認証付き一覧を取得できた方式だけを含める。

- 既存のキー確認と同じGET・ページング・proxy/TLS・制限時間・キャンセルを使い、追加の生成API試行は行わない。判断用の元一覧は公開補完前に分離する。OpenAIは既存の240日・廃止モデル除外、OAuthはAPIが返した表示対象IDのみ、GoogleはgenerateContent対応モデルから候補を作る。明らかな音声・画像・Live・埋込などの専用モデルを除く。JSON/Decisions対応の保証ではなく、実行可否はToolsの既存起動チェックで確認する。
- 公開OpenRouter一覧・同梱キャッシュ・OAuthの固定候補・将来版や900kの合成候補・設定モデルからの補完は行わない。認証の証跡は実行中のメモリだけに保持し、キー値や指紋をJSONへ保存しない。
- 書込時に現在のキー（OpenAIは組織も）またはOAuthトークン・アカウントが取得時と一致することを確認する。キー変更・削除、一覧取得失敗、旧JSONだけが残っている状態は候補にしない。個別確認後は同じDiag実行内で保持する他方式の有効な取得結果を使うが、再起動や設定再読込後は再確認が必要。
- FreeAI/Geminiは判断実行と同じ優先キーを使い、優先キー未設定時だけ他方の認証付き取得結果を代用する。キーが設定済みで認証に失敗した場合は代用しない。
- 空の方式は省略し、全方式が空なら `{}` を保存する。設定・autoの選択順・方式別既定値は書き換えない。生成確認済みの利用可能モデルとこの候補一覧を混同しない。
- headlessと画面のモデル書込は共通処理で生成し、保存先一覧にもファイル名を含める。Pythonの読込口は `conf_models.get_decisions_models()`。Web/Avatar設定画面もこの一覧を利用し、取得済み候補と設定保持値を区別して表示する。
- モック検証: `node --test backend_diag/checks/decisions-info.check.mjs`。4方式、認証変更、公開/固定/旧保存候補の排除、キー代用、失敗・空一覧、共通書込とheadlessの保存先を確認する。

### 判断系4方式の候補管理（2026-10-18）

autoの優先順は `openai_oauth` → `freeai_chat` → `openai_decisions` → `gemini_chat`。起動チェックに成功した方式だけを優先対象にする。

判断系の低コスト方針は `backend_diag/モデル情報/decisions_info.mjs` の `DECISION_MODEL_CANDIDATES` で書き出す候補を絞って管理する。現在はOpenAI両方式が `gpt-6-luna`、FreeAI/Geminiが `gemini-flash-lite-latest`。将来別モデルへ変更するときはこの候補配列を調整し、認証付き一覧を再取得・書き出しする。実行側や画面にモデル固定・恒久的な選択禁止は置かない。

[Google公式alias説明](https://developers.googleblog.com/en/continuing-to-bring-you-our-latest-models-with-an-improved-gemini-2-5-flash-and-flash-lite-release/) でIDを確認した。最新への追従はGoogle側のalias更新を利用し、番号を推測・並べ替えしてモデルを生成しない。[公式モデル一覧](https://ai.google.dev/gemini-api/docs/models) では現時点の安定版Flash-Liteは `gemini-3.5-flash-lite`。latestは安定版専用aliasではなくプレビュー等を指す場合もあるため、現在の解決先バージョンはこの実装で断定しない。

Diagは認証付きGET一覧に候補配列のIDそのものがある方式だけを掲載する。GoogleはgenerateContent対応を要求する。公開一覧・設定値・別バージョンから候補を捏造しない。未取得・認証なし・失敗・対象ID不在なら方式を省略し、全方式が空なら `{}`。モデル一覧は実行の許可リストではなく、設定画面の候補として扱う。

## OpenCode / Copilot のCode候補

`code_models_info.json` の `opencode_cli.models` は `copilot_cli.models` を共通元とし、OpenCode出力時だけClaude系を除外する。残るモデルのID・表示名・順序を揃える。合成したCopilot用モデルが空なら共通の `COPILOT_FALLBACK_MODELS` を使い、OpenCode側だけ同じClaude除外を適用する。Copilot側の取得候補・固定8候補は変更しない。OpenCodeの出力条件はOpenCode自身の導入検出であり、Copilotの導入や認証には依存しない。OpenCodeは独自認証を使う前提で、候補の補完を認証・生成成功へ昇格させない。Ollamaの取得モデルはChat用に維持するが、合成CodeのOpenCode候補は上記の共通定義を使う。

## 判断モデルの手動試行

設定モデル動作確認のLIVE直後に `DECISION / 挨拶の丁寧さ` を表示する。個別「テスト」と全体「動作確認」の両方で、既存MCP `/aidiy_decisions_check/mcp` の `decisions_check` を呼ぶ。HTTP `/check` への代替直結は行わない。Tools接続中の明示操作に限定し、headless・起動・全診断では実行しない。

`DECISION_AI_NAME` と方式別 `DECISION_OPENAI_MODEL` / `DECISION_OAUTH_MODEL` / `DECISION_GEMINI_MODEL` / `DECISION_FREEAI_MODEL` が不足時はauto。方式が明示されている試行行は対応する方式別値を使い、キー未存在時だけ旧 `DECISION_AI_MODEL` を参照する。方式autoの行はモデルもautoで送り、Toolsで方式とモデルを解決する。autoの方式順はOAuth → FreeAI → Decisions API → Gemini。結果には実効モデルを表示し、設定ファイルへは書き戻さない。

入力は「おはよう」、質問は挨拶としての丁寧さ、choice名は `politeness`、選択肢は `high / medium / low`。3値すべてを正常な選択として受け付け、特定値を正解とはしない。MCPのJSON内のstatus、回答名・型・選択値、3候補の確率分布・合計、confidenceを検証する。不正JSON・欠落・未知選択肢・通信エラーはNG。結果詳細に選択値と検証済みJSON、実際の実行モデルを表示する。

Chat/Live/Codeと判断結果は共有しない。MCPの初期化・セッション破棄、設定変更による結果破棄、既存のタイムアウトを共用する。判断の行期限を超えた場合はNGと理由を表示し、その全体実行を終了する。ユーザーによる中止は従来の中止表示を維持する。

検証は `checks/decision-trials.check.mjs`、既存モデル試行/API/音声/UIテスト、`DIAG_TEST_PYTHON` を指定する実MCP SDK fixtureで行う。fixtureの生成APIはMockTransportへ置換し、外部の生成サービスを使わない。Web/Avatarの設定画面とDiag試行UIは同じ候補と通常のモデル解決を使う。


## AIモデルの手動試行

「AIモデル」はChat / Live / Decision / Codeの4画面です。初期値はconfigのCHAT・LIVE・DECISION各設定とCODE1を使います。Decisionの方式autoはモデルもautoとしてTools側で解決します。入力の「おはよう」とDecisionのpoliteness / high・medium・lowは `モデル試行/defaults.mjs` を既存設定モデル試行と共用し、手動画面では自由に編集できます。

候補は `_AIDIY/aidiy_diag/{chat,live,decisions,code}_models_info.json` と `live_voices_info.json` の保存済み内容だけです。画面初期読込・再読込は認証付きローカルDiag APIを使い、外部モデル取得は行いません。プロバイダ変更は画面内で候補を連動し、一覧外の設定保持値を未確認として残します。候補の存在は認証・モデル利用成功の保証ではありません。選択や入力をconfigへ書き戻しません。

試行はTools接続中の明示操作だけです。既存 `モデル試行/trials.mjs` のMCP初期化・呼出し・セッション終了、逐次実行ロック、設定変更検知、期限、音声保存を共用します。Chatは `chat_llms_run`、Codeは `code_agents_run`、Decisionは `decisions_check` をHTTP MCPで呼び、Liveだけは既存 `/internal/live_model_check` へ明示した方式・モデル・音声・入力を渡します。Liveの接続後10秒待機とアダプター終了処理は共通です。空JSONの従来Live試行は従来のconfigと固定挨拶を使います。

AIモデルタブのタイトルバー「一括試行」は4画面の入力を開始時に固定し、Chat→Live→Decision→Codeを1実行として順に呼びます。NG・行タイムアウトでも次へ進みます。連打は抑止し、入力変更・実行中の画面移動・Tools切断で中止して古い結果を破棄します。全診断・headless・起動ではAI試行しません。設定モデルの15項目試行とAIモデルの4種試行は別の操作です。

Decisionは1問ずつpredicate / choice / scoreを選び、質問名・質問文と、必要な選択肢／段階（2〜32件、重複不可）を編集します。戻り値全体はJSONを読めればインデント付き、読めなければ元文字列を安全なテキストとして表示します。表示できることと回答スキーマの成功判定は別です。既知の秘密値は伏せます。

Liveの応答テキストと1秒以上のWAVを表示し、認証付き音声APIからBlobを取得してネイティブプレーヤーで再生します。自動再生しません。一括試行中はLiveの一時音声を保持し、完了後も再読込可能です。再試行・画面移動では再生を停止し、Object URLを解放します。短い音声・音声なし・取得失敗は明示し、音声だけを再読込できます。

検証は実AIを使わず、`checks/manual-models.check.mjs`、`ui/src/AIモデル/checks/manual-state.check.mjs`、`backend_tools/tests/test_live_model_check.py` を使います。`DIAG_TEST_PYTHON` をTools依存環境のPythonへ設定すると `checks/model-trials-sdk.check.mjs` が実MCP SDKと合成AIで経路を確認します。`checks/manual-models-browser.mjs` は既存Chrome/Edgeの隔離プロファイルで4画面・幅1280/720/390・合成音声再生・破棄・一括試行・非JSON表示を確認します。UI変更後は依頼に応じて `backend_diag/ui` のビルドと `node backend_diag/ui/verify.mjs` で配布物を同期します。
