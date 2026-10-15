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
aidiy_diag --headless       # 画面を開かず全診断を最速で実行し、結果を保存
```

`--headless` は Electron・ブラウザ・HTTP 待受を使わず、全診断をコマンドラインで最速実行します（全項目を同時に確認し、結果は一覧順に表示）。全診断はインストール状況とモデル情報です。インストール状況は `_AIDIY/aidiy_diag/install_info.json`（状態・パス・バージョン・説明と集計）へ、モデル情報はテストできるプロバイダごとに `_AIDIY/aidiy_diag/<プロバイダ>_models_info.json` へ保存します。保存は一時ファイルからの置き換えで行い、例外・Ctrl+C・書込失敗など実行に失敗した場合は既存ファイルを更新しません。項目ごとの `未検出` / `ERR` などは診断結果として保存します。終了コードは成功 0、失敗 1、中断 130 です。`--headless` は他の引数と併用できません。

画面では「インストール確認」で全項目が「確認中」で回り、上から順に結果へ切り替わります。確認が終わると「書込」が押せるようになり、このサーバーが直前に確認した結果を `--headless` と同じ形式で `_AIDIY/aidiy_diag/install_info.json` へ保存します（画面から値は送りません）。タブ欄の「全テスト」は、インストール確認→書込のあと、最新モデル取得→モデル情報の書込まで続けて実行します。

### モデル情報ファイル（`<プロバイダ>_models_info.json`）

キー設定画面の「書込」（最新モデル取得の後に押せます）・「全テスト」・`--headless` で、gemini / freeai / claude / openai / openai_oauth / grok / openrt / ollama / local のうちテストしたものを 1 ファイルずつ保存します。用途の分け方は本体の `get_chat_models` / `get_live_models` / `get_code_models` に合わせています。

保存形式は `形式: 2` です。選択候補は用途にかかわらず「区分名 → `{models}`」で取得できます。例: `chat.gemini_chat.models`、`code.claude_sdk.models`、`live.gemini_live.models`。区分名以下は各プログラムへそのまま渡せるよう `models` だけを持ちます。取得元などの説明や詳細情報はその外側に置きます。旧形式のファイルは次回の「書込」または `--headless` で置き換わります。

- `chat`: API から取得し本体と同じ条件で絞り込んだ一覧。`モデル` は作成日・トークン数・モダリティ付きの詳細配列として残します。選択候補は `gemini_chat` など本体の区分名をキーにした要素の `models` に置き、「モデルID: YYYY/MM/DD - モデルID」の一覧（作成日が無いものは `yyyy/mm/dd`、backend_local は固定候補の表示名）にします。詳細・選択候補とも作成日の新しい順です。Claude / Grok は本体に chat の選択区分がないため詳細だけを残し、CLI の選択候補は `code` に置きます。
- `live`（gemini / freeai / openai）: API で取得した live 対応モデル（Gemini は `bidiGenerateContent` 対応、OpenAI は `realtime`）から、`gemini_live` などの区分名をキーにした要素の `models` を直接生成します。Gemini / FreeAI はモデルIDに `native-audio` または `live` を含み、`transcribe` または `translate` を含むものを除外し、モデルIDの文字列降順で並べます。OpenAI は `whisper` または `translate` を含むものを除外し、作成日の新しい順です。表示名は「YYYY/MM/DD - モデルID」で、日付は API / OpenRouter の作成日 → モデル名の日付 → `yyyy/mm/dd` の順に採用します。設定ファイル由来のボイス・設定案・差分は保存しません。
- `code`: `claude_sdk` / `claude_cli` は Claude、`antigravity_cli` は Gemini、`codex_cli` は各ファイルの OpenAI API / OpenAI OAuth、`opencode_cli` は Ollama の取得モデルから `models` を生成します。`codex_cli` は `realtime` を含むモデルを除外し、同じ系列（`sol` / `luna` / `pro` など）は数値として比較した最新バージョンだけを残します。例: `gpt-6.1-sol` があれば `gpt-5.6-sol` は除外します。`-900k` などの別仕様は独立した系列として扱います。`aidiy_hermes` も OpenAI OAuth の取得モデルを使い、モデルIDに `openai_oauth/` を付けます。合成の `aidiy_hermes.models` には、導入済みCLIの `xx/auto`（CLI のモデルを維持して呼び出す選択肢）を追加します（下記）。Claude SDK / CLI はモデルIDから `haiku`・`sonnet`・`opus`・`fable` などの名前を抽出してキーに使い、同名は最新の1件へまとめます。表示名は「YYYY/MM/DD - バージョン付きモデルID」とし、最新バージョンを残します。`copilot_cli` は Claude / OpenAI / OpenAI OAuth のファイルに出力し、Claude は系列ごとの最新モデルをバージョン付きIDのキーで保存し、数字間の `-` を `.` に変換します（キー・表示名とも `claude-haiku-5.5` など）。OpenAI / OpenAI OAuth は `codex_cli` と同じ候補で保存します。詳細配列には元のモデルIDを保持します。作成日・並び順は chat と共通です。
- 固定候補は Grok（`grok_cli`）と backend_local（`local_chat`）だけです。aidiy_diag が管理し、本体は合成JSONから読みます。それ以外は取得に失敗した場合に候補を空にし、状態・説明・警告を残します。

Gemini / FreeAI はモデルIDに `lyria` を含むものを詳細・chat・live・code すべての出力対象から除外します。`antigravity_cli` もこの絞り込み後の候補から生成します。

モデル情報の生成・保存は `_config` 上のモデル設定ファイルに依存しません。API 接続用のキー・ログイン情報の読み取りは従来どおりです。保存するのは、このサーバーが直前に取得した結果と Grok / local の固定候補だけで、画面から値は送りません。

プロバイダ別ファイルへ `xx/auto` は挿入しません（旧表記 `xx/same` が残っていても合成時に除外します）。合成の `code_models_info.json` は導入済みCLIの区分だけを出力します（`claude_sdk` もClaude CLIの導入が必要）。`aidiy_hermes.models` だけは特別に、導入済みCLIの `xx/auto` をCopilot → Claude → Codex → Antigravity → Grok → OpenCodeの順で先頭へ追加し、その後に取得したモデルを並べます。導入判定はインストール診断と同じ探索先での実行ファイルの存在確認です。

音声候補は `live_voices_info.json` に `{gemini_live: {voices: {...}}, freeai_live: {voices: {...}}, openai_live: {voices: {...}}}` の形式で保存します。固定定義は `voices_info.mjs` で管理します。キーの確認成功と現在の設定状態に合わせて出力し、未設定・確認失敗のプロバイダは含めません。FreeAIの声はGeminiと同じ定義です。個別更新では他の有効な確認済み候補を保持し、キーが無効化された場合は除外します。

Copilot単独契約向けの例外として、Copilot CLIが導入済みで合成後の `copilot_cli.models` が空の場合だけ、指定のClaude / GPT固定8モデルを指定順・指定日付で補います。取得候補が1件でもあれば補わず、プロバイダ別ファイルへは固定8モデルを保存しません。

プロバイダ別ファイルの書込後に、同じ保存先の全プロバイダ別ファイルを読み、`chat_models_info.json` / `live_models_info.json` / `code_models_info.json` も生成します。chat / live の合成時は FreeAI を先頭に並べます。code は Claude / OpenAI 系を前、`antigravity_cli` を最後に並べます。合成ファイルのルートは `gemini_chat` / `gemini_live` / `codex_cli` などの区分名で、それぞれ `{models}` だけを持ちます。詳細配列や診断の説明はプロバイダ別ファイルに残します。同じ区分名・モデルIDはマージし、表示名が重複するときは日付の新しいものを優先します（実日付は `yyyy/mm/dd` より優先）。個別テスト後の書込でも、他プロバイダの保存済み候補を合成に含めます。

`python backend_diag/_setup.py` または全体の `python _setup.py` で `~/.local/bin` にランチャーを作成します。全体セットアップのDiagは `[y]` の表示だけで選択入力はありません。Windows は `aidiy_diag.cmd` です。`backend_diag/aidiy_diag` / `backend_diag/aidiy_diag.cmd` からも直接起動できます。

上部は Term と同じ高さのタイトルバー・ウィンドウ操作・接続バーです。シアンの線は Tools の接続成功、黒は未接続を示します（Tools の確認は常に有効で、ON/OFF・再確認の操作はありません）。診断自体の接続とは別です。Tools は `_config/AiDiy_key.json` の `PORT_TOOLS`（省略時8095）に対して、固定 loopback の `/aidiy_code_agents/ping` だけを10秒間隔で確認します。キー・モデル・エージェントの実行は行いません。切断・画面破棄で確認を停止します。

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

通常の Electron 起動は表示確認後にコマンドプロンプトへ戻ります。ウィンドウを閉じると HTTP・診断子プロセスも終了します。`--foreground` / `--wait`、`--browser` / `--no-open`、Codespaces・GUI のない環境では起動ターミナルの Ctrl+C で終了します。キーも失効します。`python backend_diag/_cleanup.py` または全体クリーンアップで、この作業コピーのランチャーだけを解除します。別コピーのランチャーは削除しません。全体起動 `python _start.py` では起動選択より先に必ず `aidiy_diag --headless` の完了を待ち、モデル合成JSONを生成します。DiagのGUI起動を選ぶ質問はなく、診断の実行・保存に失敗した場合はサービス起動を中止します。単独ランチャーで起動した診断も、同じ作業コピーのクリーンアップで終了します。停止通知は `.stop-request` の短いランダム識別子のみで、PID・認証キー・診断結果は保存しません。

## 追加と検証

`catalog.json` に実際のソース参照を伴う項目を追加します。`version_args: null` は存在確認のみです。GUI 起動やネットワーク・モデル取得を伴うコマンドは version 検査に登録しないでください。API 経由で項目を追加・変更する機能はありません。

```sh
node --test backend_diag/checks/*.check.mjs backend_diag/checks/*.check.cjs
node --check backend_diag/static/app.js
node backend_diag/ui/verify.mjs
```

`checks/check_setup.py` は Python のまま残したセットアップ／起動／クリーンアップ（`_setup.py` / `_start.py` / `_cleanup.py`）の確認です。Python がある開発環境では任意で `python -m unittest backend_diag/checks/check_setup.py -v` を実行できます。

Playwright と Chromium が利用できる検証環境では `node backend_diag/checks/ui_browser.mjs` で、合成データのみの実ブラウザ回帰を実行できます。Playwright は依存に含めないため、実行ディレクトリか `backend_diag` で `npm i --no-save playwright-core` を行ってください。実キー読取・外部モデル API 呼出は行いません。必要なら `CHROMIUM_PATH` で既存ブラウザを指定します。

ブラウザ確認では、認証前拒否、診断開始・再チェック、カテゴリ開閉、選択詳細、狭い画面、通常 URL とパス型プロキシを確認してください。診断結果や認証 URL を公開ログ・スクリーンショットに含めないでください。

## カタログの調査範囲

基準コミット `8adbdb484cafe31e145c4fe362897d2af1077eb1` の Git tree 全 4,950 ファイルから、対象ソース・設定・スクリプト・テンプレート・テスト・manifest/lockfile **3,333 件**を列挙し、全件の全文を静的走査しました。未取得・未読は 0 件。246 候補から今回の確認対象 **19 項目**を採用し、各項目の詳細に参照パスと行番号を表示します。コードの実行・インストール試験を行ったという意味ではありません。

通常の Markdown ガイド・skill 本文（README/AGENTS を除く）、画像・音声・モデル・Office/PDF、LaTeX 文書資産、ライセンス・非実行テキスト等は対象外です。実行可能な skill スクリプトやコード例は含めます。省略のある Python 教材 3 件は AST 解析できませんでしたが、全文テキストを走査済みです。全リポジトリの全バイトを検証したという主張ではありません。

- [coverage.json](./coverage.json): 件数、基準コミット、除外、制限、AST テキスト代替走査の記録。
- [reference/source-manifest.json](./reference/source-manifest.json): 対象 3,333 件のパスと元の Git blob SHA。
- [reference/source_scan.ts](./reference/source_scan.ts): 対象コードを実行しない、依存パッケージなしの TypeScript 走査スクリプト。Python は字句解析で呼出し・for・代入・dict 単位に候補を抽出します（旧 Python AST 版と同じ候補を出すことを確認済み。構文エラーのファイルも走査します）。基準コミットの作業コピーに対し Node.js 22.18+ で `node backend_diag/reference/source_scan.ts REPOSITORY OUTPUT_JSON COMMIT backend_diag/reference/source-manifest.json` を実行すると候補抽出を再現できます。抽出候補からカタログへの分類にはソース確認が必要です。

Python/Node のライブラリ、内部スクリプト、shell builtin、Git subcommand、モデル ID を外部実行ファイルと混同しません。19 項目すべてが必須ではなく、選択機能に応じて必要な項目を含みます。ユーザー設定の任意コマンドや動的生成、リモート・コンテナ・WSL・Android 側の導入状態は、ホストの PATH 確認だけでは保証できません。

## キー設定状況とモデル一覧

「キー設定状況」は診断サーバーの TypeScript 実装から固定ファイル `_config/AiDiy_key.json` の既知キーだけを読み取り、設定済 / 未設定を表示します。設定 JSON の値、長さ、末尾、ハッシュはブラウザに返しません。ファイル未作成は未設定、JSON 不正や読込不可は確認不可です。既存 conf クラスの初期化・設定変更は行いません。

一覧は既存 config の固定キー順（Gemini、FreeAI、Claude、OpenAI、OpenAI OAuth、Grok（xAI）、OpenRouter、Ollama（ローカル）、ローカル（backend_local）、Hugging Face 読取・書込、Discord）です。Azure OpenAI と GitHub Copilot はモデル一覧の確認に対応しないため画面に表示しません（サーバーの登録とモデル名からのキー値秘匿の対象には残します）。表示対象外の設定項目は省き、JSON の任意の並べ替えには追従しません。左側でキーを選択し、右側で説明・テスト結果・モデル一覧を確認できます。キーの存在だけでは OK にしません。起動時には匿名の公開 OpenRouter 一覧だけを取得します。タブ移動・全テストから個別キーの API は呼びません。各行の「テスト」は明示操作時だけ固定プロバイダーのモデル一覧 API を読み取ります。生成リクエスト、MCP の挨拶、CLI 試行は未実装です。

- キー試験の表示は未実施 / OK / NG。未設定・未対応の項目は未実施で、理由を表示します。OpenRouter のテストボタンは取得済み公開キャッシュの表示だけで、個別取得やキー認証はしません。起動時・明示再取得の公開要求にもキーを送りません。キーの有効性は未確認のままです。
- OK はモデル一覧 API の応答確認であり、生成可能性・課金状態の保証ではありません。公開モデル一覧の場合はキー有効性の検証にもなりません。
- Gemini / FreeAI / Claude / OpenAI / OpenRouter / Ollama Cloud の固定 HTTPS 宛先だけを使います。OpenAI OAuth は `~/.codex/auth.json`（`CODEX_HOME`）、Grok（xAI）は `~/.grok/auth.json` のログイン情報があれば API キーが無くても設定済とし、それぞれ `chatgpt.com/backend-api/codex/models`（本体と同じく非表示・廃止モデルを除き優先度順）と `cli-chat-proxy.grok.com/v1/models`（非表示を除き、作成日が分かるものは 240 日以内）からモデル一覧を取得します。ログイン情報は読むだけで、トークンの更新（ファイルの書換え）はしません。期限切れのときは各 CLI での再ログインを案内します。
- 絞り込み・並び順は本体（`backend_server/conf/conf_model.py` の取得関数と `get_chat_models`、OAuth は `command_hermes/hermes_cli/codex_models.py`）に合わせています。OpenAI / OpenRouter の表示一覧は旧 Sol（`gpt-6-sol` 系）を除き、補完用の公開一覧は除きません。OpenRouter の別名（`~provider/model`）も本体と同じく表示します。OpenAI OAuth は非表示・廃止を除いて優先度順に並べ、将来版と `-900k` 版を補完します。API で取れないときは本体と同じ代替候補（`~/.codex/config.toml` の model → `models_cache.json` → 既定値）を NG の結果と併せて表示します。Grok は本体がもともと固定候補（`grok-4.7` / `grok-4.6`）を流し込む系統のため、API で取れない場合は固定候補を表示して PASS（黄）とし、取れなかった理由を説明に残します。backend_local も本体は API を使わず固定候補（`CHAT_LOCAL_MODELS`）を流し込む系統のため、aidiy_diag が持つ同じ固定候補を表示して PASS（黄）とします。Ollama は本体と同じくキーを使わず、ローカルの Ollama（`ollama list` と同じ一覧、新しい順）を `127.0.0.1:11434/api/tags` から読みます（プロセスは起動しません）。
- 「最新モデル取得」は設定状況を読み直し、モデルキー設定のテストできる行を上から順に取得します。取得中の行へ選択と右側のモデル一覧が追従します。Azure、Copilot、Hugging Face、Discord の個別テストは未対応です。
- キーは当該サービスへのモデル一覧要求にだけ使用し、任意 URL / proxy / 環境変数の base URL は採用しません。リダイレクト禁止、要求ごとに期限・応答上限を設けます。モデル処理全体は 25 秒・同時2件、HTTPS 要求ごとは8秒・応答1 MiB、設定ファイルは128 KiB、表示モデルは500件上限です。終了・期限切れでは通信を中止し、Google のページ取得は最大20回です。表示の取得範囲・警告を確認してください。エラー本文やヘッダーは返しません。
- 設定状況を更新すると前のテスト表示を消します。別のキーに変更した場合は再テストしてください。テスト結果はブラウザのメモリ内だけで、再起動・再読込後に引き継ぎません。

### 起動時の公開モデル取得

HTTP サーバーの起動後、匿名の公開 OpenRouter モデル一覧を一度だけ非同期で取得します。この操作は設定ファイルを読み取らず、Authorization も送りません。取得に失敗した場合も画面・インストール確認・他の個別テストは使えます。

パネル見出しに「公開モデル一覧取得:」として、ネットワーク取得は「OK」、同梱キャッシュは「キャッシュ利用」、ほかに「取得中」「失敗」「未取得」を 1 か所だけ表示し、個別キーの未実施 / OK / NG とは混ぜません。「再取得」ボタンはキャッシュ利用時だけその右に表示する明示操作で、同時要求は1回にまとめます。設定状況更新では公開キャッシュを消しません。

キャッシュは起動中の Node メモリだけに置き、再起動で破棄して再取得します。元の Python 判定を移植した処理で日付絞り込みした時点のスナップショットです。個別テストはこの整形済み公開情報を同じ Node プロセス内で参照し、OpenRouter を毎回再取得しません。時間が経った情報を更新したい場合は再取得してください。共通システムへの結果保存はありません。

OpenRouter の先行手動テストは要求しません。公開情報が取得中・失敗・未取得でも、他のモデル試験は補完なしの警告付きで実行できます。公開情報の取得成功はキーの認証成功を意味しません。

起動時に公開一覧を取得できない場合は、同梱の `openrouter_models/openrouter_models.zip`（OpenRouter `/api/v1/models` の応答を保存したもの）を一時フォルダ（`%TEMP%idiy_diag` / `$TMPDIR/aidiy_diag`）へ展開し、ネットワーク取得と同じ日付絞り込み・安全化を通して使います。展開は Node 標準の zlib だけで行い、外部コマンドは使いません。キー設定画面の見出しには「公開モデル一覧取得: OK」（ネットワーク取得、緑）または「キャッシュ利用」（同梱キャッシュ、黄）を表示します。同梱キャッシュは保存時点の一覧なので、新しいモデルは含まれません。

2026-10-15 の確認では OpenRouter の `/api/v1/models` はキーなしで応答しましたが、公式 API リファレンスには Authorization 必須の記載もあります。キーなし取得を将来も保証するものではありません。応答が失敗した場合は NG とし、キー自体の認証失敗とは断定しません。

## 診断単独の TypeScript モデル処理

`runtime/model_catalog.ts` は `backend_server/conf/conf_model.py` 由来のモデル日付判定・絞り込み・OpenRouter 情報補完を移植した診断専用実装です。本体ファイルを変更せず、Python モジュールの import・子プロセス起動・venv 探索を行いません。元実装の変更時は合成フィクスチャと対照更新します。

`runtime/model_probe.ts` は固定設定をサーバー内で読み、固定 HTTPS モデル API の GET を実行します。キー値を引数・環境変数・ブラウザへ渡さず、モデルの文字列に紛れた既知キーも抑止します。Conf クラス、設定保存、OAuth fallback は呼びません。`runtime/model_runner.ts` は処理期限・同時実行数・終了時キャンセルを管理します。エラー本文やキー値はログへ出しません。

TypeScript ソースは開発時に既存 UI の esbuild で Node.js 18 向け `.mjs` に事前変換し、配布物を同梱します。通常起動時は TypeScript 実行機能・コンパイラ・npm install・Python が不要です。全体のセットアップ／クリーンアップ用 Python と、インストール一覧の Python 検出は従来どおりです。

`checks/reference/model-golden.json` は、移植前の Python 実装から生成して凍結した合成ゴールデンです。Node テストはこれで日付境界・DST・UTCオフセット・補完・空キャッシュ・順序を照合します。移植前の Python 参照実装と再生成スクリプトは削除済みのため、ゴールデンは TypeScript 実装の出力で上書きしないでください。実キーや外部モデル API はテストに使いません。

モデル確認は選択したボタンを押したときだけです。補完用の公開キャッシュがないときは警告を表示し、元と同じ未補完時の判定へ進みます。公開情報だけでは実キーの有効性・生成・課金の可否を検証しません。起動時の匿名公開一覧を除く自動キー試験や共通結果保存は行いません。全テストはインストール確認だけです。

## Vue UI の配布と開発

Vue 3 の SFC は `ui/src/` に分割しています。`App.vue` が認証・タブと共通 API、`インストール/インストールパネル.vue` がインストール一覧と詳細、`モデルキー設定/モデルキー設定パネル.vue` がモデルキーとモデル一覧、`外部連携設定/外部連携設定パネル.vue` が Hugging Face 読取・書込と Discord の設定状況を担当します。設定画面ごとの選択状態・表示・スタイル・テストを各機能フォルダへ内包し、`キー設定共通/` の設定取得・世代管理・公開キャッシュを共有します。外部連携は設定の有無のみ確認し、接続テストは未対応・未実施のままです。インストール専用の状態・診断実行は `インストール状態.mjs`、選択・表示処理は `インストール表示.mjs`、専用スタイルは `インストール.css`、回帰チェックは同フォルダの `checks/`（`*.check.cjs`）に内包します。共通の `StatusBadge.vue` とレイアウトは共有します。テンプレートはビルド時にコンパイルし、runtime compiler・CDN・unsafe-eval を使いません。

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
