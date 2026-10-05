# VS Code チャット拡張変更手順

> 文書: `frontend_vscode,VSCodeチャット拡張変更手順.md` | 実装: `frontend_vscode/package.json`, `frontend_vscode/src/extension.ts`, `frontend_vscode/src/runner.ts`, `frontend_vscode/src/protocol.ts`, `frontend_vscode/src/webview.ts`, `frontend_vscode/aidiy_code/src/server.ts`, `frontend_vscode/aidiy_code/launch.mjs`

## このメモを使う場面

- VS Code の AiDiy チャット、コマンド、設定を変更する。
- `aidiy_hermes` の起動、停止、Provider / モデル選択を調整する。
- Webview と単独試用画面を変更する。
- VSIX を生成し、VS Code へ配置して確認する。
- 単独起動用の `aidiy_code` / `aidiy_live` コマンドを配置する。

## 変更箇所の選び方

| 変更内容 | 主なファイル | 同時に確認するもの |
|----------|--------------|--------------------|
| ビュー、コマンド、設定 | `package.json`, `src/extension.ts` | `README.md`, `media/chat.html` |
| CLI 探索、引数、標準入出力、停止 | `src/runner.ts` | `checks/runner.test.cjs` |
| AIコード互換 packet | `src/protocol.ts` | `backend_server/AIコア/AIコード.py`, `backend_server/AIコア/AIコード_cli.py` |
| チャット表示、入力 | `src/webview.ts`, `media/chat.html`, `media/chat.css` | `aidiy_code/bridge.js`, `checks/aidiy_code.test.cjs` |
| Provider / モデル候補 | `scripts/model-catalog.py` | `command_hermes` の picker / Provider 実装 |
| 単独試用サーバー | `aidiy_code/src/server.ts`, `aidiy_code/bridge.js` | `checks/aidiy_code.test.cjs` |
| 単独ウィンドウ、タイトルバー | `aidiy_code/desktop.cjs`, `aidiy_code/preload.cjs`, `aidiy_code/launch.mjs` | `media/chat.html`, `media/chat.css`, `aidiy_code/theme.css` |
| bundle / VSIX | `scripts/build.mjs`, `scripts/package.mjs`, `package.json`, `aidiy_live/build.mjs`, `aidiy_live/package.json` | 両 `.vscodeignore`, `dist/THIRD_PARTY_NOTICES.txt` |
| Live 拡張、通信、マイク | `aidiy_live/src/extension.ts`, `src/host.ts`, `src/bridge.ts`, `microphone.py`（いずれも `aidiy_live/` 内） | `aidiy_live/checks/host.test.cjs`, `aidiy_live/README.md` |

## 実装上の維持事項

- Code は常駐バックエンドを経由せず `aidiy_hermes` を直接起動する。Live は既存 AIコアの WebSocket とモデル情報 API を利用し、拡張専用の API を追加しない。
- Code / Live は別々の拡張 ID・コマンド・設定・VSIX を維持し、`extensionDependencies` / `extensionPack` で相互依存させない。片方の非導入・無効化で他方が起動できることを確認する。
- Live の Windows マイクは Webview の権限に依存せず、拡張ホストの Python 標準ライブラリ補助で取り込む。音声処理と自動減衰はスタンドアロンと共有し、非表示・切断・無効化でマイクを終了する。
- CLI は `shell: false` で起動し、要求本文は標準入力で渡す。要求文をコマンドライン引数へ埋め込まない。
- 拡張側から `--yolo` を追加しない。
- `input_text` / `input_request` / `cancel_run` / `output_stream` / `output_text` の識別子と、開始 `STX`・終了 `ETX`・中断 `CAN` の1バイト制御値を既存 AIコード実装と揃える。制御値に改行を含めず、Webview にも表示しない。
- `.cmd` は AiDiy `_setup.py` が生成する `PY` / `CLI` 形式だけを解析し、任意の batch を実行しない。
- ワークスペース未信頼時、仮想ワークスペース、Web 版では CLI を実行しない。
- Webview では Markdown の HTML と外部画像を無効のまま維持し、外部リンクは `http` / `https` のみにする。
- `webview.ts` を変えた場合は VS Code 拡張モードと単独試用モードの両方を確認する。
- 初回は最初の状態通知を反映してから黒い画面からフェードインする。履歴復元時の保存済み回答にはタイプ表示を再適用せず、新しい回答だけを演出する。状態更新や会話切り替えではフェードインを繰り返さない。
- スタンドアロンの専用ウィンドウは中心を保ちながら初回だけ拡大する。拡大中は `opening` 通知で内容と初期画面の演出を止め、拡大後に最小サイズを戻して内容を表示する。ブラウザモードは CSS の拡大表示を使う。
- 専用ウィンドウの起動位置は、マウスポインターがある画面の作業領域を基準に Code を左上、Live を右上にする。端に約8pxの余白を設け、Live は拡大演出後の実際の幅で右端を合わせる。
- Live は `retainContextWhenHidden` で画面を保持し、タブ切り替えでは接続を閉じない。非表示中はマイクだけを停止し、heartbeat は拡張ホストで継続する。会話・接続通知を上限つきで保持して再表示時に反映し、非表示中の音声は再生しない。
- Live の input／0／audio の `connect` パケットに `CODE_BASE_PATH` と任意の `モデル設定`（Live の AI 名・モデル・音声）を含め、バックエンドの初期化前に反映する。接続後の設定 API による差し替えは行わない。接続中に別フォルダへ変わった場合は切断し、次回の接続に反映する。
- Live のモデル候補は `/core/AIコア/モデル情報/取得` を使う。接続前は空の `セッションID` で既定設定と候補を取得でき、セッションは作成しない。未接続の「選択する」はローカルの次回接続設定だけを更新し、接続中の「変更して再接続」は新しいセッションで3ソケットを接続し直す。画面の会話・入力は保持し、マイクは OFF に戻す。キャンセル後の再表示では確定済み設定から選択値を復元する。
- モデル選択の「専用ウィンドウで開く」は外し、VS Code のビュータイトル／コマンドパレットから実行する。確定操作は「選択する」または「変更して再接続」の1つにし、変更がある場合だけ有効にする。
- Code の説明は `frontend_vscode/README.md`、Live の説明は `frontend_vscode/aidiy_live/README.md` に分ける。VSIX 作成時はそれぞれの `extension/readme.md` が各拡張だけを説明していることを確認する。
- Code は新規会話で入力欄と保存済み下書きを空にし、`welcome-input-started` を引き継がず起動画面のターミナル演出を最初から再開する。同じ会話の状態通知では演出を再開せず、初回の下書き復元時は入力済みとして演出を停止する。VS Code / 単独画面の共通処理は `src/webview.ts` に置く。
- Live は手動切断・接続断・「新しい会話」で、会話欄を初期の案内（ターミナル演出を再開始）、入力欄を空、モデル表示を初期ラベルへ戻す。接続先とプロジェクト表示は保持する。未接続の「接続」は黒文字で背景を白〜水色（`--voice`）へ変化させ、接続済みの「切断」は白背景と黒文字で固定する（ホバー時も同じ）。
- Code / Live の新しいAI回答は、500ms後に文字送りを開始し、10msごとに `max(1, floor(文字数 / 50) + 1)` 文字を追加する。演出中は0.7秒周期でカーソルを点滅させ、完了後に外す。Live は次のメッセージを表示するときに前の回答を全文表示し、新規会話・切断・画面終了で演出タイマーを破棄する。`prefers-reduced-motion: reduce` では両方ともAI回答を全文表示する。
- Code / Live の手入力メッセージは白文字（`#fff`）で表示し、クリックで本文を入力欄へコピーしてフォーカスとカーソルを末尾へ移す。Live の `recognition_input` / `recognition_output` は少し灰色（`#b8b8b8`）にし、同じクリック操作でコピーする。演出中・表示文字数の制限中でも元の全文をコピーし、この操作だけで送信は行わない。
- Live の文字表示には通常回答と音声認識に加え、コードエージェントの `output_request` を含める。旧バックエンドの `output_text: !` は送信エラーとして案内する。`aidiy_live/checks/view.test.cjs` で VS Code / 単独画面の両方を検証する。
- 送信ボタンは Code / Live とも未接続・入力不可時は灰色と白い紙ヒコーキ（`ws-disabled`）。接続済みの空欄・空白入力では白背景（`rgba(255, 255, 255, .95)`）、青紫の枠（`#667eea`）、黒い紙ヒコーキ。送信可能時は `frontend_web/src/components/AiDiy/compornents/AIコード.vue` と同じ青紫（`#667eea`）、ホバー時は `#5a6fd8` にする。紙ヒコーキ画像は `brightness(0)` で黒、`brightness(0) invert(1)` で白にする。空欄・空白だけでは無効にし、VS Code テーマで色を上書きしない。
- 入力欄の Enter は通常の改行。Tab で送信ボタンへ移動し、そこで Enter を押すと送信する。日本語 IME の変換確定では送信しない。
- 入力欄下の操作部は「上段：Enter の操作説明」「下段：左に状態、右にモデル選択とモデル名」のコンパクトな2段にし、右端の送信／停止ボタンは2段分の高さにする。両モードで共通の HTML / CSS を使う。
- 履歴削除の確認は `media/chat.html` のパネル内ダイアログで共通処理し、確認後に `deleteHistory` を送る。拡張ホストや単独画面のブリッジで別の確認ダイアログを出さない。
- 「新規」「一覧」、モデル選択、履歴削除、送信、停止は Webview 内の共通 UI を主操作にする。VS Code 固有のコマンドは外部からの呼び出しやエディター連携用に残す。
- 単独画面の上部はタイトルバー、実行状態バー、会話操作行の順に置く。VS Code 拡張ではアイコンと AiDiy のタイトル行を非表示にし、実行状態バーと会話操作行を表示する。「今の会話／会話一覧」、フォルダ名、「新規」「一覧」は会話操作行にまとめる。単独ウィンドウのドラッグ領域はタイトルバーだけに指定し、会話操作行を含めない。
- 回答・進捗の緑はスタンドアロンと共通の `#00ff00` を `media/chat.css` で定義する。VS Code の明暗・高コントラストテーマでも、この色を上書きしない。
- 拡張機能一覧のアイコンは `package.json` 直下の `icon`、サイドバーのアイコンは `contributes.viewsContainers` の `icon` で指定する。両方とも `media/AiDiy.png`（`frontend_web/public/icons/AiDiy.png` と同じ画像）を使い、変更後は VSIX を再生成・再配置する。
- Live のマイク・スピーカーは `frontend_web/public/icons/microphone.png` / `speaker.png` を `aidiy_live/media/` にコピーし、CSS のマスクで赤／水色に表示する。画像追加時は Live の `.vscodeignore` と `src/server.ts` のリソース許可一覧へ含め、配布ディレクトリだけで読み込めることを確認する。
- Provider / モデル選択は VS Code 上部の Quick Pick ではなく、`media/chat.html` のチャットパネル内ダイアログで行う。候補は `chooseModel` / `modelCatalog` / `modelCatalogError`、確定値は `setModel` で Webview と実行層の間を受け渡す。
- Provider と API モデルは `scripts/model-catalog.py` から Hermes の picker を再利用する。外部 CLI のモデルは `_config/AiDiy_code_*.json` を読み、設定がないか `auto` のみなら対応する `scripts/cli_bat` の `MODEL` 値を読む。`claude-code` は `AiDiy_code_claude_cli.json` に対応し、`claude_sdk` は Hermes の外部 CLI Provider には含まれない。
- モデル候補は provider ごとの固定キャッシュにせず、選択画面を開くたび CLI から取得する。特に `openai_oauth` は認証アカウントのライブ候補が変わり得る。
- 外部 CLI Provider のモデルが `auto` の場合は `--model auto` を渡さず、各 CLI 自身の既定モデル選択へ任せる。明示モデルを選んだ場合は Hermes の外部 CLI 実行まで `--model <ID>` を渡す。
- `antigravity-cli` は Hermes の外部 CLI Provider 一覧から取得する。`xai-oauth` は API Provider のカタログ入口に含め、`grok-4.6` を Hermes の curated model 一覧から取得する。
- xAI OAuth の初回認証は静的なワンショット実行中ではなく、拡張の「対話 CLI」から `/model` で `xai-oauth` を選ぶか、`hermes auth add xai-oauth` を実行する。
- VS Code の履歴に残る Hermes セッション ID が CLI 側で見つからない場合、同じ依頼を `--resume` なしで一度だけ再実行する。再実行が成功したら新しいセッション ID を保存する。以前の CLI セッションの文脈は復元されないため、必要な前提は依頼文に含める。

## セットアップと配置

プロジェクト全体ではルートから実行し、`command_hermes` の次に `frontend_vscode` を選ぶ。

```powershell
python _setup.py
```

拡張だけを処理する場合:

```powershell
python frontend_vscode/_setup.py
```

`frontend_vscode/_setup.py` は `npm install`、`npm update`、VSIX 生成、`code --install-extension --force` を順に実行し、最後に拡張 ID とバージョンを再取得して配置を確認する。VS Code CLI が見つからない場合は単独画面だけをコンパイルする。最後に `~/.local/bin/aidiy_code.cmd`（Windows）または `~/.local/bin/aidiy_code`（macOS / Linux）を作り、`aidiy_code/launch.mjs` を絶対パスで呼び出す。`code` が PATH に無い場合は、稼働中の Codespaces / Dev Container / Remote SSH の Remote CLI と VS Code の標準配置先も探索する。単にファイルが存在するだけでなく、`--version` に成功した CLI だけを使う。

同時に `aidiy_live` のランチャーも作り、`aidiy_live/launch.mjs` を呼び出す。ランチャーだけの更新は `python frontend_vscode/_setup.py --launchers-only` を使う。この作業コピーから配置した旧名 `aidiy_vscode` は新しいランチャーの配置後に解除する。生成済み VSIX だけを配置する場合は `python frontend_vscode/_setup.py --extensions-only` を使う。通常セットアップと `--extensions-only` は両 VSIX の存在を確認してから、拡張名が `aidiy-` で始まる既存拡張（`publisher.aidiy-*`）をすべて除去し、除去を確認した後に Code / Live を配置する。旧 `aidiy-vscode` も同じ判定で対象になる。表示名は `AiDiy (Code)` / `AiDiy (Live)`、内部モジュール名・起動コマンドは `aidiy_code` / `aidiy_live` とする。拡張パッケージ名は `aidiy-code` / `aidiy-live`、拡張 ID は `aidiy.aidiy-code` / `aidiy.aidiy-live` とする。

片方だけを無効にする場合は VS Code の拡張一覧で対象の歯車から「無効にする」または「無効にする（ワークスペース）」を選択する。必要に応じてウィンドウを再読み込みする。

Electron は VSIX 生成・単独画面コンパイルより前に `scripts/setup_electron.py` の共通処理で準備する。配置済みの実行ファイル・`version`・`path.txt` を照合し、未配置なら Avatar の同じバージョンのバイナリ、`_cache/electron/` の共有 ZIP の順に再利用する。まだ取得されていない場合だけ Python で GitHub から取得する。npm の install / update / rebuild では Electron の自動取得をスキップし、同じ取得を繰り返さない。Electron を準備できない場合はセットアップを失敗扱いにする。詳細は [`共通,開発環境運用手順.md`](./共通,開発環境運用手順.md) の「Electron の共通セットアップ」を参照する。

単独画面は作業フォルダで `aidiy_code`、または `aidiy_code "C:\work\project"` のように明示して起動する。前者は起動時のカレントフォルダを使用する。`~/.local/bin` は Hermes のランチャーと共通なので PATH に含める。Windows の `.cmd` と macOS / Linux のシェルランチャーは、どちらも `aidiy_code/launch.mjs` を直接呼ぶ。`launch-extension-dev.ps1` は Windows で VS Code 拡張の開発ホストを起動する。

配置は拡張機能ファイルを更新するだけで、VS Code 本体や AiDiy の常駐サービスを停止しない。すでに VS Code が起動している場合、変更の反映にはウィンドウ再読み込みが必要になる。

単独起動は Electron のフレームレスウィンドウを使う。ヘッダーのドラッグ領域から会話操作・ウィンドウ操作ボタンを除外し、最小化・最大化／復元・閉じるを preload の限定 API で扱う。Node integration は無効、context isolation と sandbox は有効にする。専用ウィンドウ終了時はサーバーと CLI を終了する。`aidiy_code --browser` では従来のブラウザモードを使い、接続が無くなって60秒後に終了する。Electron は開発・単独起動用依存で、VSIX に含めない。

`aidiy_code/launch.mjs` は Electron の取得処理を呼ばず、準備済みの実行ファイルを使う。未配置またはバージョン不一致の場合は `python frontend_vscode/_setup.py` の再実行を案内する。`npm ci` だけで Electron バイナリが取得されるとは限らないため、専用ウィンドウを使う環境ではセットアップを実行する。

専用ウィンドウはページ読み込み後に `show()` / `focus()` を呼び、`isVisible()` の確認後に起動完了ファイルへ `windowShown: true` を書く。ランチャーはその通知まで待ち、サーバーの準備だけで表示成功とは判断しない。Electron の起動では `windowsHide: false` とし、ブラウザモードの Node サーバーだけを非表示起動する。起動失敗・タイムアウト時は `out/aidiy_code/<起動ID>.stderr.log` の場所と末尾のエラーを表示する。

## 変更後の検証

```powershell
Set-Location frontend_vscode
npm ci
npm run check
npm test
npm run package
python -m unittest discover -s checks -p test_setup.py
```

確認内容:

- TypeScript の型エラーがない。
- 日本語長文を stdin で渡せる。
- stdout の正式回答、stderr の進捗、Hermes セッション ID を分離できる。
- `copilot-cli`、`codex-cli`、`claude-code` が `-Q --oneshot-stdin` でも Hermes の API Provider 解決へ入らず、各 CLI を直接起動する。
- 非ゼロ終了、起動エラー、停止、タイムアウトを呼び出し元へ返せる。
- Windows の AiDiy `.cmd` をシェルなしで解決できる。
- packet が開始、進捗、終了または中断、正式回答の順になる。
- 単独試用の接続制限、会話継続、新規会話、履歴の選択・削除、モデル変更、停止が動く。
- VS Code 側で旧 `workspaceState` の単一会話を履歴へ移行でき、作業フォルダごとに履歴が分かれる。最終選択モデルが再起動後と新規会話へ引き継がれる。
- `dist/aidiy-code-<version>.vsix` と `dist/aidiy-live-<version>.vsix` が生成され、それぞれのファイルだけを含む。

Windows の実 VS Code で拡張ホストまで確認するときは、依存導入と compile 後に次を使う。

```powershell
./scripts/test-extension-host.ps1
./scripts/test-extension-host.ps1 -Scenario Code
./scripts/test-extension-host.ps1 -Scenario Live
```

通常の VS Code プロファイルへ配置する確認は `_setup.py` を使う。試用ホストの `out/manual-profile` と混同しない。

Code / Live の単独起動では、Electron の引数をエントリファイルだけにする。Chromium が追加のファイル引数を解釈して異常終了する場合があるため、起動設定は子プロセスの環境変数で渡す。Code は `AIDIY_CODE_PROJECT` / `AIDIY_CODE_READY` / `AIDIY_CODE_MODEL`、Live は `AIDIY_LIVE_BACKEND` / `AIDIY_LIVE_READY` / `AIDIY_LIVE_PROJECT` / `AIDIY_LIVE_MODELS` を使う。表示後の `windowShown: true` 通知は維持する。Code のブラウザ版は Node.js の引数で従来どおり渡す。

ルートの `vscode_code.bat` / `vscode_live.bat` は起動失敗時に `pause` し、終了コードを保持する。ダブルクリックで起動した場合も、閉じる前に表示されたエラーを確認できる。Electron が未配置なら `python frontend_vscode/_setup.py` で準備する。ブラウザ版を確認する場合は、各 bat に `--browser` を付ける。bat は UTF-8、CRLF 改行で保存する。

Live のブラウザ版は通常の `--browser` と Electron 失敗時の自動切り替えでサーバーを分離し、CMD / PowerShell へ戻る。画面は localhost 中継の `presence`（SSE）へ接続し、最後の画面が閉じて約60秒後にサーバーを終了する。`--browser --foreground` は診断用、`--serve` は URL の表示と手動終了用としてターミナル上で実行する。`aidiy_live/checks/launcher.test.cjs` では、GUI が常駐してもランチャーが戻ることと、Electron 失敗時にもブラウザ中継が動いたまま戻ることを検証する。

## バージョン更新時

当面のバージョン番号は `0.1.0` に固定する。機能変更だけを理由に更新しない。将来、明示的に固定解除または改版する場合は次を同時に確認する。

- `package.json` の `version`。
- `package.json` の `package` script にある VSIX ファイル名。
- `README.md` の手動配置用 VSIX ファイル名。

`scripts/build.mjs` は Webview の依存パッケージから `dist/THIRD_PARTY_NOTICES.txt` を再生成する。依存追加後は VSIX 内にライセンス文書が含まれることを確認する。

## クリーンアップ

```powershell
python frontend_vscode/_cleanup.py
```

ルートの `python _cleanup.py` でも、`command_hermes` の次に `frontend_vscode` を選択できる。拡張名が `aidiy-` で始まる配置済み拡張（`publisher.aidiy-*`）をすべて解除し、拡張一覧に対象が残っていないことを確認してから、`~/.local/bin` の Code / Live ランチャー、`node_modules`、`dist`、`out`、Python cache を削除する。セットアップとクリーンアップの対象判定・解除確認は `frontend_vscode/scripts/vscode_extensions.py` で共有する。解除が失敗した場合はランチャー・生成物を削除しない。

cleanup は VS Code 本体を終了しない。起動中の拡張ホストには再読み込みまで旧コードが残る場合があるため、解除を画面へ反映するときだけ利用者が VS Code のウィンドウを再読み込みする。CLI が利用できない、解除後も拡張が残る、生成物を削除できない場合は失敗として終了する。

削除前に、この作業コピーの Code / Live 単独実行サーバー、Electron、専用 Chrome / Edge を強制終了する。ルートの cleanup では常駐サービス停止と同じ段階で実行し、フォルダ単独の cleanup でも生成物削除前に実行する。判定と終了確認は `frontend_vscode/scripts/standalone_processes.py` が担当する。専用ブラウザは `out/aidiy_code/browser-profile` / `out/aidiy_live/browser-profile` の完全一致で判定し、通常のブラウザは終了しない。`out` 内のキャッシュで WinError 32 が出る場合は、親サーバー終了後にも専用ブラウザが残っている可能性がある。終了確認後の一時的なファイル共有違反は短時間の再試行で吸収する。

## 問題の切り分け

| 症状 | 確認箇所 |
|------|----------|
| `code` が見つからず VSIX を配置できない | VS Code CLI の PATH、`frontend_vscode/_setup.py` の `find_vscode_cli()`。単独画面はセットアップ可能 |
| Electron が未配置 | `python frontend_vscode/_setup.py` を再実行する。Avatar の同じバージョン、共有 ZIP を優先して再利用する。`dist/version`・実行ファイル・`path.txt` の照合まで成功しているか確認する |
| 専用ウィンドウが表示されない | ターミナルに出る起動エラーと `out/aidiy_code/*.stderr.log` を確認する。`aidiy_code/desktop.cjs` の表示後通知と `aidiy_code/launch.mjs` の表示確認を両方使う |
| Hermes が見つからない | `aidiyHermes.cliPath`、`~/.local/bin`、`command_hermes/.venv` |
| Provider / モデルが空 | `scripts/model-catalog.py`、Hermes 設定、Cli Path が AiDiy CLI を指すか |
| 送信できない | ワークスペース信頼、フォルダが開かれているか、実行中状態 |
| 回答が出ない | VS Code 出力の `AiDiy`、CLI の終了コード、認証が必要なら「対話 CLI」 |
| `Session not found` | 古い拡張では新しい会話を開始する。更新版では `--resume` を外して一度だけ自動再試行するため、実行ログと保存セッション ID を確認する |
| VSIX に変更が入らない | `npm run package` の prepublish、`dist/extension.js` / `dist/webview.js`、`--force` 配置 |
| Live の専用ウィンドウでマイクが ON にならない | `aidiy_live/permissions.cjs` の origin 正規化と音声・メインフレーム制限。Windows のサウンド入力にデバイスがあるかを確認する。リモートデスクトップでは録音転送を有効にして再接続する。詳細は `aidiy_live/README.md` の「マイクを ON にできない場合」 |
