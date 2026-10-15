# AiDiy 診断

外部プログラムの導入状態を、ソースに記載された利用箇所と一緒に確認します。診断サーバーは Node.js 18 以降の標準モジュールで動作します。通常は Electron ウィンドウで表示し、--browser / Codespaces / GUI のない環境では Web で表示します。AIコア / DB の起動は不要です。

診断本体の起動には Node.js が必要です。一覧は Python、uv、Node.js、npm、npx、Electron の順です。Python はバックエンドで使用します。Python が無くても配置済みランチャー・直接 Node 起動は使えます。全体セットアップは既存方式に合わせ Python を使用します。

## 起動

```sh
node backend_diag/diag_main.mjs --browser
# ランチャー配置後
aidiy_diag                  # 通常は Electron
aidiy_diag --browser        # 明示的なブラウザ起動
```

`python backend_diag/_setup.py` または全体の `python _setup.py` の最初の項目（既定 `[y]/n`、a=auto も対象）で `~/.local/bin` にランチャーを作成します。Windows は `aidiy_diag.cmd` です。リポジトリ直下の `./aidiy_diag` / `aidiy_diag.cmd` からも起動できます。

初期状態は未確認です。「診断を開始」で検出し、「再チェック」で更新します。左側でカテゴリを開閉、プログラム名・コマンドで検索、状態で絞り込み、項目を選ぶと右側でパス・バージョン・利用機能・参照ソースを表示します。

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
- GUI、内部ランチャー、安全な version 引数が確認できないものは存在確認のみです。Windows の `.cmd` / `.bat` / `.ps1` はシェル実行を避けて存在確認に限定します。
- PATH と登録済みの標準パス・プロジェクト内配置を検出対象とし、API キー・設定 JSON・環境変数の値は表示しません。個別設定による独自パスや venv 内のみにある実行ファイルは、PATH に載っていなければ検出されない場合があります。
- 判定は未確認・未検出・OK・NG・ERR の 5 種類です。OK に含める存在確認は起動試験ではありません。判定の定義は末尾の「状態インジケーター」を参照してください。
- Python / npm のライブラリ依存と外部プログラムは別です。この初期機能は外部プログラムを対象とします。

## 終了・解除

起動ターミナルで Ctrl+C を押して終了します。キーも失効します。`python backend_diag/_cleanup.py` または全体クリーンアップで、この作業コピーのランチャーだけを解除します。別コピーのランチャーは削除しません。全体起動 `python _start.py` では IDE グループの先頭に Diag の選択があります（既定 n）。選択時だけ Node の独立プロセスで起動し、全体起動の Ctrl+C・クリーンアップ要求では停止します。Diag を自動再起動する監視は行いません。単独ランチャーで起動した診断も、同じ作業コピーのクリーンアップで終了します。停止通知は `.stop-request` の短いランダム識別子のみで、PID・認証キー・診断結果は保存しません。

## 追加と検証

`catalog.json` に実際のソース参照を伴う項目を追加します。`version_args: null` は存在確認のみです。GUI 起動やネットワーク・モデル取得を伴うコマンドは version 検査に登録しないでください。API 経由で項目を追加・変更する機能はありません。

```sh
node --test backend_diag/tests/*.test.mjs backend_diag/tests/*.test.cjs
python -m unittest discover -s backend_diag/tests -v
node --check backend_diag/static/app.js
```

ブラウザ確認では、認証前拒否、診断開始・再チェック、カテゴリ開閉、検索、状態絞り込み、選択詳細、狭い画面、通常 URL とパス型プロキシを確認してください。診断結果や認証 URL を公開ログ・スクリーンショットに含めないでください。

## カタログの調査範囲

基準コミット `8adbdb484cafe31e145c4fe362897d2af1077eb1` の Git tree 全 4,950 ファイルから、対象ソース・設定・スクリプト・テンプレート・テスト・manifest/lockfile **3,333 件**を列挙し、全件の全文を静的走査しました。未取得・未読は 0 件。246 候補から今回の確認対象 **19 項目**を採用し、各項目の詳細に参照パスと行番号を表示します。コードの実行・インストール試験を行ったという意味ではありません。

通常の Markdown ガイド・skill 本文（README/AGENTS を除く）、画像・音声・モデル・Office/PDF、LaTeX 文書資産、ライセンス・非実行テキスト等は対象外です。実行可能な skill スクリプトやコード例は含めます。省略のある Python 教材 3 件は AST 解析できませんでしたが、全文テキストを走査済みです。全リポジトリの全バイトを検証したという主張ではありません。

- [coverage.json](./coverage.json): 件数、基準コミット、除外、制限、AST テキスト代替走査の記録。
- [reference/source-manifest.json](./reference/source-manifest.json): 対象 3,333 件のパスと元の Git blob SHA。
- [reference/source_scan.py](./reference/source_scan.py): 対象コードを実行しない標準ライブラリのみの走査スクリプト。基準コミットの作業コピーに対し `python backend_diag/reference/source_scan.py REPOSITORY OUTPUT_JSON COMMIT backend_diag/reference/source-manifest.json` で候補抽出を再現できます。抽出候補からカタログへの分類にはソース確認が必要です。

Python/Node のライブラリ、内部スクリプト、shell builtin、Git subcommand、モデル ID を外部実行ファイルと混同しません。19 項目すべてが必須ではなく、選択機能に応じて必要な項目を含みます。ユーザー設定の任意コマンドや動的生成、リモート・コンテナ・WSL・Android 側の導入状態は、ホストの PATH 確認だけでは保証できません。

## 今後の拡張（未実装）

現在の実装はインストール状況の診断までです。次段階は以下の順序を想定します。

1. AI モデルのキー設定状況と、API で利用可能なモデルの一覧を確認する。キー不要のサービスは区別し、キーの値は表示しない。
2. 設定済みで MCP が稼働している場合に、利用者が「試行」を押して MCP 経由で LLM に「おはよう」を送り、応答を確認する。
3. CLI についても、MCP 稼働時に利用者が「試行」を押して応答を確認する。

外部サービスへの送信・課金を伴い得る試行は、画面表示や通常診断から自動実行しません。送信先・対象モデル等を利用者が確認して実行する設計とします。この節は構想であり、キー設定・モデル取得・MCP 経由の試行機能はまだありません。

## インストール確認の表示分類

左の最上位は「インストール確認」で、その下に次の 19 項目を表示します。

- ベース（6）: Python、uv、Node.js、npm、npx、Electron。
- CLI群（7）: Claude Code、OpenAI Codex CLI、GitHub Copilot CLI、Antigravity CLI、Grok Build、OpenCode、Ollama。
- その他拡張（6）: ffmpeg、ffprobe、ffplay、Chrome、OBS Studio、VS Code。

Python、uv を先頭に表示します。CLI や拡張は利用する機能に応じて確認するもので、全 19 件が共通の起動必須条件ではありません。未検出は全体の故障判定ではありません。

### 今回の確認対象からの除外

旧静的調査の抽出候補 246 件から 227 件を除き、現在の確認対象を 19 件に絞っています。AiDiy 起動コマンド群、Hermes 本体・専用プラグイン・スキル・補助依存、macOS 音声再生（afplay）、GStreamer、Edge、Brave、OS 補助・シェル・開発・導入・配置用の補助ツール（Git / pip 等）は診断カタログに含めません。任意項目を再表示するチェックもありません。
実際のプログラムや機能を削除する変更ではありません。共通依存は非 Hermes の利用根拠で保持し、Hermes 専用の探索パスも除外します。
対象ソース・設定 3,333 件の調査履歴・マニフェストは保持します。調査範囲と今回の診断対象は異なり、除外内容は coverage.json の catalogSelection に記録しています。
将来のモデル設定・MCP 試行は別の最上位項目とする想定ですが、現時点では未実装です。

## 状態インジケーター

一覧・詳細・集計・絞り込み・凡例は同じ 5 種類で表示します。
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

Electron の認証 URL は標準入力の専用 pipe で渡し、引数・環境変数・ログへ出しません。renderer は sandbox / contextIsolation を有効、nodeIntegration を無効にします。非永続 session を使い、権限要求・別ウィンドウ・外部 navigation を拒否します。ウィンドウを閉じると診断サーバーも停止します。

実際の Electron GUI 起動はこの変更の検証環境では未確認です。テストでは共有セットアップ、同版再利用、起動分岐、URL受渡、Electron権限制限を mock / 一時ファイルで検証します。
