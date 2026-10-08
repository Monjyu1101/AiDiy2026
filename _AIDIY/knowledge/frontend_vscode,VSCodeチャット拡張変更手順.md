# VS Code チャット拡張変更手順

> 文書: `frontend_vscode,VSCodeチャット拡張変更手順.md` | 実装: `frontend_vscode/package.json`, `frontend_vscode/src/extension.ts`, `frontend_vscode/src/runner.ts`, `frontend_vscode/src/protocol.ts`, `frontend_vscode/src/webview.ts`, `frontend_vscode/aidiy_code/src/server.ts`, `frontend_vscode/aidiy_code/launch.mjs`, `frontend_vscode/src/model-preferences.ts`, `frontend_vscode/aidiy_live/`, `frontend_vscode/_setup.py`, `frontend_vscode/_cleanup.py`

## このメモを使う場面

- VS Code の AiDiy (Code) / AiDiy (Live) 拡張のビュー、コマンド、設定を変更する。
- `aidiy_hermes` の起動、停止、Provider / モデル選択を調整する。
- Live のライブ会話画面、音声入出力、AIコアへの接続を調整する。
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
| Code の接続・モデル候補 | `src/code-connection.ts` | `aidiy_live/local-backend.cjs`, AIコアのモデル情報API、`checks/code-connection.test.cjs`、`checks/code-extension.test.cjs` |
| 最終手動モデルの保存・復元 | `src/model-preferences.ts`, `src/extension.ts`, `aidiy_code/src/server.ts`, `aidiy_live/src/extension.ts`, `aidiy_live/src/server.ts`, `aidiy_live/src/bridge.ts`, `aidiy_live/src/view.ts` | Code / Live の画面・サーバー検証、両 README |
| 単独試用サーバー | `aidiy_code/src/server.ts`, `aidiy_code/bridge.js` | `checks/aidiy_code.test.cjs` |
| 単独ウィンドウ、タイトルバー | `aidiy_code/desktop.cjs`, `aidiy_code/preload.cjs`, `aidiy_code/launch.mjs` | `media/chat.html`, `media/chat.css`, `aidiy_code/theme.css` |
| bundle / VSIX | `scripts/build.mjs`, `scripts/package.mjs`, `package.json`, `aidiy_live/build.mjs`, `aidiy_live/package.json` | 両 `.vscodeignore`, `dist/THIRD_PARTY_NOTICES.txt` |
| Live 拡張、通信、マイク | `aidiy_live/src/extension.ts`, `src/host.ts`, `src/bridge.ts`, `microphone.py`（いずれも `aidiy_live/` 内） | `aidiy_live/checks/host.test.cjs`, `aidiy_live/checks/extension.test.cjs`, `aidiy_live/README.md` |
| Live 画面、音声、音量表示 | `aidiy_live/src/view.ts`, `src/audio.ts`, `src/visualizer.ts`, `src/protocol.ts`, `media/`（いずれも `aidiy_live/` 内） | `aidiy_live/checks/view.test.cjs`, `aidiy_live/checks/live.test.cjs` |
| Live 単独起動、中継、マイク許可 | `aidiy_live/launch.mjs`, `desktop.cjs`, `permissions.cjs`, `src/server.ts`（いずれも `aidiy_live/` 内） | `aidiy_live/checks/launcher.test.cjs`, `aidiy_live/checks/permissions.test.cjs`, `checks/desktop.test.cjs` |
| セットアップ、ランチャー、クリーンアップ | `_setup.py`, `_cleanup.py`, `scripts/vscode_extensions.py`, `scripts/standalone_processes.py`, ルートの `vscode_code.bat` / `vscode_live.bat` | `checks/test_setup.py`, `checks/test_extensions.py`, `checks/test_cleanup_processes.py` |

## 実装上の維持事項

- Code / Live は既存AIコアのWebSocketとモデル情報APIを使う。Code の接続は `src/code-connection.ts` が input → セッション設定API → 出力1 の順に行い、両init完了後にAIコアへ送信する。未接続中のCode送信はHermesの直接実行へ渡す。
- Code / Live は別々の拡張 ID・コマンド・設定・VSIX を維持し、`extensionDependencies` / `extensionPack` で相互依存させない。片方の非導入・無効化で他方が起動できることを確認する。
- Live の Windows マイクは Webview の権限に依存せず、拡張ホストの Python 標準ライブラリ補助で取り込む。音声処理と自動減衰はスタンドアロンと共有し、非表示・切断・無効化でマイクを終了する。
- CLI は `shell: false` で起動し、要求本文は標準入力で渡す。要求文をコマンドライン引数へ埋め込まない。
- 拡張側から `--yolo` を追加しない。
- `input_text` / `input_request` / `cancel_run` / `output_stream` / `output_text` の識別子と、開始 `STX`・終了 `ETX`・中断 `CAN` の1バイト制御値を既存 AIコード実装と揃える。制御値に改行を含めず、Webview にも表示しない。
- `.cmd` は AiDiy `_setup.py` が生成する `PY` / `CLI` 形式だけを解析し、任意の batch を実行しない。
- ワークスペース未信頼時、仮想ワークスペース、Web 版では CLI を実行しない。
- Webview では Markdown の HTML と外部画像を無効のまま維持し、外部リンクは `http` / `https` のみにする。
- `webview.ts` を変えた場合は VS Code 拡張モードと単独試用モードの両方を確認する。
- `src/runner.ts`、`src/protocol.ts`、`aidiy_live/src/protocol.ts`、`src/model-preferences.ts`、`scripts/model-catalog.py` を変えた場合は、これらを直接共有する `frontend_discord` で `npm run check` / `npm test` も実行する。詳細は [`frontend_discord,Discord接続変更手順.md`](./frontend_discord,Discord接続変更手順.md) を参照する。
- 初回は最初の状態通知を反映してから黒い画面からフェードインする。履歴復元時の保存済み回答にはタイプ表示を再適用せず、新しい回答だけを演出する。状態更新や会話切り替えではフェードインを繰り返さない。
- スタンドアロンの専用ウィンドウは中心を保ちながら初回だけ拡大する。拡大中は `opening` 通知で内容と初期画面の演出を止め、拡大後に最小サイズを戻して内容を表示する。ブラウザモードは CSS の拡大表示を使う。
- 専用ウィンドウの起動位置は、マウスポインターがある画面の作業領域を基準に Code を左上、Live を右上にする。端に約8pxの余白を設け、Live は拡大演出後の実際の幅で右端を合わせる。
- Live は `retainContextWhenHidden` で画面を保持し、タブ切り替えでは接続を閉じない。非表示中はマイクだけを停止し、heartbeat は拡張ホストで継続する。会話・接続通知を上限つきで保持して再表示時に反映し、非表示中の音声は再生しない。
- Live の input／0／audio の `connect` パケットに `CODE_BASE_PATH` と任意の `モデル設定`（Live の AI 名・モデル・音声）を含め、バックエンドの初期化前に反映する。接続後の設定 API による差し替えは行わない。接続中に別フォルダへ変わった場合は切断し、次回の接続に反映する。
- Live のモデル候補は `/core/AIコア/モデル情報/取得` を使う。起動時に空の `セッションID` で `AiDiy_key.json` に基づく既定設定と候補を取得し、接続前から AI 名・モデル・音声を表示する（セッションは作成しない）。起動引数の指定値を優先し、候補一覧にない設定値も選択肢へ補う。未接続の「選択する」はローカルの次回接続設定だけを更新し、接続中の「変更して再接続」は新しいセッションで3ソケットを接続し直す。画面の会話・入力は保持し、マイクは OFF に戻す。キャンセル後の再表示では確定済み設定から選択値を復元する。取得が遅れて接続や終了の後に応答した場合は、その既定値で現在設定を上書きしない。
- モデル選択の「専用ウィンドウで開く」は外し、VS Code のビュータイトル／コマンドパレットから実行する。確定操作は「選択する」または「変更して再接続」の1つにし、変更がある場合だけ有効にする。
- Code / Live の最終手動選択はユーザーのホームフォルダの `.aidiy/aidiy_code_model.json` / `.aidiy/aidiy_live_model.json` に分けて保存し、それぞれ VS Code 拡張・単独画面で共用する。保存は画面で確定したときだけ行い、起動引数・接続・新規会話・キャンセルでは上書きしない。モデル未指定なら保存済み選択を復元し、明示モデルは優先する。Provider のみ指定した場合は同じ Provider の保存値を復元し、異なる場合はその Provider の既定値（Code は `auto`）を使う。Code の自動選択（空の Provider / モデル）も復元する。Live は音声も保存するが、保存値の復元だけでは自動接続しない。未保存・破損時は既定設定を使い、保存失敗時は現在設定を変更せずエラーを表示する。JSON は一時ファイルへ書いて原子的に置換する。`AiDiy_key.json` と会話履歴はこの選択記録へ保存しない。
- Code の説明は `frontend_vscode/README.md`、Live の説明は `frontend_vscode/aidiy_live/README.md` に分ける。VSIX 作成時はそれぞれの `extension/readme.md` が各拡張だけを説明していることを確認する。
- Code / Live の起動画面は中央の文字を `--terminal`（緑 `#00ff00`）にし、3行のタイプ表示を12秒周期に揃える。各行の文字送りは周期の4〜16%、26〜38%、48〜60%（それぞれ1.44秒）とし、行間は1.2秒待機する。文字とカーソルの開始・終了位置を同時に変更し、Code の動きを減らす設定にも同じ周期を適用する。
- Code は新規会話で入力欄と保存済み下書きを空にし、`welcome-input-started` を引き継がず起動画面のターミナル演出を最初から再開する。同じ会話の状態通知では演出を再開せず、初回の下書き復元時は入力済みとして演出を停止する。VS Code / 単独画面の共通処理は `src/webview.ts` に置く。
- Live は手動切断・接続断で、会話欄を初期の案内（ターミナル演出を再開始）、入力欄を空へ戻す。確定したモデル・音声の表示とプロジェクト表示は保持する。接続中の「新しい会話」は会話欄と入力をクリアし、現在のモデル・音声・作業フォルダで新規セッションへ接続し直す。マイクとスピーカーの ON/OFF は保持する。未接続時は表示と入力だけをクリアする。未接続の「接続」は黒文字で背景を白〜水色（`--voice`）へ変化させ、接続済みの「切断」は白背景と黒文字で固定する（ホバー時も同じ）。
- Code / Live の新しいAI回答は、500ms後に文字送りを開始し、10msごとに `max(1, floor(文字数 / 50) + 1)` 文字を追加する。演出中は0.7秒周期でカーソルを点滅させ、完了後に外す。Live は次のメッセージを表示するときに前の回答を全文表示し、新規会話・切断・画面終了で演出タイマーを破棄する。`prefers-reduced-motion: reduce` では両方ともAI回答を全文表示する。
- Code / Live の手入力メッセージは白文字（`#fff`）で表示し、クリックで本文を入力欄へコピーしてフォーカスとカーソルを末尾へ移す。Live の `recognition_input` は灰色（`#e5e7eb`）、`recognition_output` は淡い緑（`#9ae6b4`）にし、同じクリック操作でコピーする。演出中・表示文字数の制限中でも元の全文をコピーし、この操作だけで送信は行わない。
- Live の文字表示には通常回答と音声認識に加え、コードエージェントの `output_request` を含める。旧バックエンドの `output_text: !` は送信エラーとして案内する。`aidiy_live/checks/view.test.cjs` で VS Code / 単独画面の両方を検証する。
- 送信ボタンは Code / Live とも未接続・入力不可時は灰色と白い紙ヒコーキ（`ws-disabled`）。接続済みの空欄・空白入力では白背景（`rgba(255, 255, 255, .95)`）、青紫の枠（`#667eea`）、黒い紙ヒコーキ。送信可能時は `frontend_web/src/components/AiDiy/compornents/AIコード.vue` と同じ青紫（`#667eea`）、ホバー時は `#5a6fd8` にする。紙ヒコーキ画像は `brightness(0)` で黒、`brightness(0) invert(1)` で白にする。空欄・空白だけでは無効にし、VS Code テーマで色を上書きしない。
- 入力欄の Enter は通常の改行。Tab で送信ボタンへ移動し、そこで Enter を押すと送信する。日本語 IME の変換確定では送信しない。
- Code / Live の入力欄は共通の `field-sizing: content` で改行・折り返しに合わせて上へ伸縮する。最小高さは 76px、上限は 220px と画面高さの 35% の小さい方にし、上限を超えた内容は入力欄内でスクロールする。下書き復元・会話からのコピー・送信後のクリアにも自動で反映する。
- Code / Live の会話末尾への追従は `src/scroll-follow.ts` を共用する。メッセージ追加・入力・送信受理・ストリーム枠の更新／開閉で即時と次の描画フレームに末尾へ移動し、`ResizeObserver` で会話領域の伸縮にも追従する。Code は会話履歴と進捗の両方を揃え、一覧から会話へ戻る際も末尾へ移す。確認は `checks/webview.test.cjs` と `aidiy_live/checks/view.test.cjs` で、入力直後・表示枠の開閉・描画後の高さ変更を検証する。
- Code の接続表示は Live と同じタイトル左側の配置・文字色・10px文字・5pxの丸印に揃える。未接続は灰色、接続済みは緑、オンライン実行中は水色とし、文字は `未接続` / `接続中` / `接続済み` とする。CodeConnectionの接続開始・成功・失敗通知を単独版と拡張の `接続中` / `接続済み` に反映し、5秒の再試行待ちは未接続とする。シアンバーは実行状態ではなく接続状態へ連動させ、AIコアの入力・コード出力ソケットの初期化とモデル設定完了後に表示し、切断時に消す。オフライン中もタイトル左側は `未接続` を表示し、専用のオフライン表示・モードボタンは設けない。入力欄下は「上段：Enter の操作説明」「下段：モデル選択とモデル名」の2段にし、右端の送信／停止ボタンは2段分の高さにする。両モードで共通の HTML / CSS を使う。
- 履歴削除の確認は `media/chat.html` のパネル内ダイアログで共通処理し、確認後に `deleteHistory` を送る。拡張ホストや単独画面のブリッジで別の確認ダイアログを出さない。
- 「新規」「一覧」、モデル選択、履歴削除、送信、停止は Webview 内の共通 UI を主操作にする。VS Code 固有のコマンドは外部からの呼び出しやエディター連携用に残す。
- 単独画面の上部はタイトルバー、実行状態バー、会話操作行の順に置く。VS Code 拡張では接続状態の文字を含むタイトル行を省略し、シアンバーを表示する。「今の会話／会話一覧」、フォルダ名、「新規」「一覧」は会話操作行にまとめる。単独ウィンドウのドラッグ領域はタイトルバーだけに指定し、会話操作行を含めない。
- Code / Live の上部シアンバーは Web の `frontend_web/src/components/_TopBar.vue` と同じ `abs(sin(2πt / 9))` の明滅に揃える。`media/chat.css` と `aidiy_live/media/style.css` の `cyan-bar-breathe` は、4.5秒の周期を2.5%刻みで標本化したRGB値を `linear` で補間する。`ease-in-out` に戻すとカーブが変わるため、通常表示・動きを減らす設定の両方で `linear` を維持する。
- Code の正式回答の緑はスタンドアロンと共通の `#00ff00` を `media/chat.css` で定義する。VS Code の明暗・高コントラストテーマでも、この色を上書きしない。
- Code の実行状況枠は CSS の `--stream`（シアン `#00ffff`）を基調にした枠線と薄い背景を使い、文字と点滅カーソルもシアンにする。Web / Avatar の `AIコード.vue` の `.stream-output .line-content` も同じ配色に揃える。Live の会話は `メッセージ識別` を行のクラスに残し、AIチャットパネルと同じく通常出力（`output_text`）は緑 `#00ff00`、コードエージェントの回答（`output_request`）はシアン `#00ffff`、音声出力認識は淡い緑で分ける。本文・文字送りカーソル・枠・背景はその種別の色を基調にし、文字送り完了後もクラスを保持する。
- 拡張機能一覧のアイコンは `package.json` 直下の `icon`、サイドバーのアイコンは `contributes.viewsContainers` の `icon` で指定する。両方とも `media/AiDiy.png`（`frontend_web/public/icons/AiDiy.png` と同じ画像）を使い、変更後は VSIX を再生成・再配置する。
- Live のマイク・スピーカーは `frontend_web/public/icons/microphone.png` / `speaker.png` を `aidiy_live/media/` にコピーし、CSS のマスクで赤／水色に表示する。画像追加時は Live の `.vscodeignore` と `src/server.ts` のリソース許可一覧へ含め、配布ディレクトリだけで読み込めることを確認する。
- Provider / モデル選択は VS Code 上部の Quick Pick ではなく、`media/chat.html` のチャットパネル内ダイアログで行う。候補は `chooseModel` / `modelCatalog` / `modelCatalogError`、確定値は `setModel` で Webview と実行層の間を受け渡す。
- Discord の直接CLI用 Provider と API モデルは `scripts/model-catalog.py` から Hermes の picker を再利用する。外部 CLI のモデルは `_config/AiDiy_code_*.json` を読み、設定がないか `auto` のみなら対応する `scripts/cli_bat` の `MODEL` 値を読む。`claude-code` は `AiDiy_code_claude_cli.json` に対応し、`claude_sdk` は Hermes の外部 CLI Provider には含まれない。
- Code は選択画面を開くたび `/core/AIコア/モデル情報/取得` の `available_models.code_models` を取得する。`aidiy_hermes` は `openai_oauth/gpt-6.1-sol` のような組み合わせID、`copilot_cli` はCLIのモデルIDをそのまま渡す。
- 外部 CLI Provider のモデルが `auto` の場合は `--model auto` を渡さず、各 CLI 自身の既定モデル選択へ任せる。明示モデルを選んだ場合は Hermes の外部 CLI 実行まで `--model <ID>` を渡す。
- `antigravity-cli` は Hermes の外部 CLI Provider 一覧から取得する。`xai-oauth` は API Provider のカタログ入口に含め、`grok-4.6` を Hermes の curated model 一覧から取得する。
- xAI OAuth の初回認証は静的なワンショット実行中ではなく、拡張の「対話 CLI」から `/model` で `xai-oauth` を選ぶか、`hermes auth add xai-oauth` を実行する。
- Code の履歴には `コアセッションID` を保存する。旧 `セッションID` はHermes用なのでAIコアへ渡さず、表示履歴だけ保持する。通信切断・初回失敗では約5秒後に再試行し、手動切断・画面破棄・サーバー終了ではタイマーと接続待ちを破棄する。

## セットアップと配置

VS Code の Code Webview では `<body class="vscode-host">` を拡張側で付け、`#title-bar` を非表示にする。Live は `view.ts` が同じクラスを付け、`aidiy_live/media/style.css` の `.vscode-host > header` を非表示にする。両方とも接続状態の文字を含むタイトル行を省略し、シアンバーとプロジェクト・会話操作行は表示する。単独版にはこのクラスを付けず、ウィンドウのタイトル行と操作を維持する。

プロジェクト全体ではルートから実行し、`command_hermes` の次に `frontend_vscode` を選ぶ。

```powershell
python _setup.py
```

拡張だけを処理する場合:

```powershell
python frontend_vscode/_setup.py
```

`frontend_vscode/_setup.py` は `npm install`、`npm update`、Electron の準備、`npm run package` による Code / Live の VSIX 生成、`code --install-extension --force` を順に実行し、最後に両拡張の ID とバージョンを再取得して配置を確認する。VS Code CLI が見つからない場合は単独画面だけをコンパイルする。最後に `~/.local/bin/aidiy_code.cmd`（Windows）または `~/.local/bin/aidiy_code`（macOS / Linux）を作り、`aidiy_code/launch.mjs` を絶対パスで呼び出す。`code` が PATH に無い場合は、稼働中の Codespaces / Dev Container / Remote SSH の Remote CLI と VS Code の標準配置先も探索する。単にファイルが存在するだけでなく、`--version` に成功した CLI だけを使う。

同時に `aidiy_live` のランチャーも作り、`aidiy_live/launch.mjs` を呼び出す。ランチャーだけの更新は `python frontend_vscode/_setup.py --launchers-only` を使う。この作業コピーから配置した旧名 `aidiy_vscode` は新しいランチャーの配置後に解除する。生成済み VSIX だけを配置する場合は `python frontend_vscode/_setup.py --extensions-only` を使う。通常セットアップと `--extensions-only` は両 VSIX の存在を確認してから、拡張名が `aidiy-` で始まる既存拡張（`publisher.aidiy-*`）をすべて除去し、除去を確認した後に Code / Live を配置する。旧 `aidiy-vscode` も同じ判定で対象になる。表示名は `AiDiy (Code)` / `AiDiy (Live)`、内部モジュール名・起動コマンドは `aidiy_code` / `aidiy_live` とする。拡張パッケージ名は `aidiy-code` / `aidiy-live`、拡張 ID は `aidiy.aidiy-code` / `aidiy.aidiy-live` とする。

片方だけを無効にする場合は VS Code の拡張一覧で対象の歯車から「無効にする」または「無効にする（ワークスペース）」を選択する。必要に応じてウィンドウを再読み込みする。

Electron は VSIX 生成・単独画面コンパイルより前に `scripts/setup_electron.py` の共通処理で準備する。配置済みの実行ファイル・`version`・`path.txt` を照合し、未配置なら Avatar の同じバージョンのバイナリ、`_cache/electron/` の共有 ZIP の順に再利用する。まだ取得されていない場合だけ Python で GitHub から取得する。npm の install / update / rebuild では Electron の自動取得をスキップし、同じ取得を繰り返さない。Electron を準備できない場合はセットアップを失敗扱いにする。詳細は [`共通,開発環境運用手順.md`](./共通,開発環境運用手順.md) の「Electron の共通セットアップ」を参照する。

単独画面は作業フォルダで `aidiy_code`、または `aidiy_code "C:\work\project"` のように明示して起動する。前者は起動時のカレントフォルダを使用する。`~/.local/bin` は Hermes のランチャーと共通なので PATH に含める。Windows の `.cmd` と macOS / Linux のシェルランチャーは、どちらも `aidiy_code/launch.mjs` を直接呼ぶ。`launch-extension-dev.ps1` は Windows で Code / Live の両方を `--extensionDevelopmentPath` に指定した VS Code 拡張の開発ホストを起動する。

配置は拡張機能ファイルを更新するだけで、VS Code 本体や AiDiy の常駐サービスを停止しない。すでに VS Code が起動している場合、変更の反映にはウィンドウ再読み込みが必要になる。

単独起動は Electron のフレームレスウィンドウを使う。ヘッダーのドラッグ領域から会話操作・ウィンドウ操作ボタンを除外し、最小化・最大化／復元・閉じるを preload の限定 API で扱う。Node integration は無効、context isolation と sandbox は有効にする。専用ウィンドウ終了時はサーバーと CLI を終了する。`aidiy_code --browser` では従来のブラウザモードを使い、接続が無くなって60秒後に終了する。Electron は開発・単独起動用依存で、VSIX に含めない。

`aidiy_code/launch.mjs` は Electron の取得処理を呼ばず、準備済みの実行ファイルを使う。未配置またはバージョン不一致の場合は `python frontend_vscode/_setup.py` の再実行を案内する。`npm ci` だけで Electron バイナリが取得されるとは限らないため、専用ウィンドウを使う環境ではセットアップを実行する。

専用ウィンドウはページ読み込み後に `show()` / `focus()` を呼び、`isVisible()` の確認後に起動完了ファイルへ `windowShown: true` を書く。ランチャーはその通知まで待ち、サーバーの準備だけで表示成功とは判断しない。Electron の起動では `windowsHide: false` とし、ブラウザモードの Node サーバーだけを非表示起動する。起動失敗・タイムアウト時は `out/aidiy_code/<起動ID>.stderr.log` の場所と末尾のエラーを表示する。

## 変更後の検証

`aidiy_code` 単独起動版とVS Code拡張は未接続中の送信を自動的にHermesへ渡す。拡張の `src/extension.ts` も `aidiy_code/src/offline.ts` の固定候補・既定値探索・実行処理を共用する。表示用のprovider/modelだけを接続状態で切り替え、会話内のオンラインモデルへオフライン選択を代入しない。通常起動は自動接続ONを既定とし、5秒ごとの再接続を継続する。プロジェクトバー右側の「自動接続」「新規」「一覧」のスイッチでOFFにすると接続・再試行を止め、新規・履歴復帰・ready通知でも再開しない。ONへ戻すと接続を再開し、OFFの選択は次回起動へ保存しない。実行中・モデル変更中の切り替えはUIとホスト側の両方で拒否する。バーはONの未接続で黒、接続済みで従来のシアン明滅、OFFで赤の明滅にする。復帰時も実行中のHermesジョブを維持する。AIコアとHermesのセッションID・保存モデルは分離し、次の送信からAIコアへ戻す。`executionMode` または `--offline` で明示したオフラインは自動接続OFFにし、再接続しない。この場合にスイッチをONへ戻すと新しいオンライン会話へ切り替え、HermesセッションIDをAIコアへ渡さない。明示オフラインの履歴復帰でもOFFへ切り替える。画面に専用のオフライン表示・モードボタンは設けない。`aidiy_code/src/offline.ts` は既存の `runner.ts` / `protocol.ts` を使ってHermesを直接実行し、AIコア・バックアップ・検証ループは呼ばない。コードAIは `aidiy_hermes` に限定し、モデルIDはオンラインのHermesと同じ形式を使う。オンライン用の `aidiy_code_model.json` はそのまま保持し、オフライン用を `aidiy_code_model_offline.json` に別保存する。両ファイルを拡張・単独版で共用し、未接続のモデル変更はオフライン用ファイルだけへ保存する。Hermesの再開IDは `HermesセッションID` に保持し、`コアセッションID` と混在させない。オフラインのコードAI欄は `aidiy_hermes` 固定・変更不可とし、モデル候補は `auto` と同梱の `_hermes_cli.bat` の選択値（`codex_cli/auto`、`copilot_cli/auto`、`openai_oauth/` 付きの4モデル）だけにする。既定値・保存値から候補を追加しない。候補外の保存値は共通設定の既定値へ戻し、既定値も候補外なら `auto` を使う。bat未配置でも同じ固定候補を使う。モデルAPIへの接続・モデルIDの手入力は不要。単独版の初期モデルは明示した起動引数、モード別の保存値、`_config/AiDiy_key.json` の `CODE_AIDIY_HERMES_MODEL` の順に優先し、共通設定が未配置・未指定の場合だけ `auto` を使う。既定値は配置先、作業フォルダの順で親へ探索し、AIコア接続前から表示する。候補外の起動引数・モデル変更要求は拒否する。

モード変更は実行中に拒否する。切り替え後は新規会話とし、一覧の各会話に実行モードを保持してAIコアのセッションIDをHermesへ渡さない。CLIジョブ終了前のモード変更・新規・モデル変更も拒否し、停止／サーバー終了では子プロセスを停止する。明示オフラインへオンライン接続の遅延通知を反映しない。自動オフラインでは再接続通知で実行中フラグを解除せず、停止を進行中のHermesジョブへ渡す。共通Webviewは `オフライン対応` が真の単独版・拡張で未接続時のHermes送信を許可し、オフライン中は検証0固定、オンライン復帰時は直前の検証回数へ戻す。

Code の検証ループ選択（0〜3回、初期値1回）は `media/chat.html` / `src/webview.ts` で扱い、送信パケットに `self_check_loop` を含める。単独版の `aidiy_code/src/server.ts` と拡張の `src/extension.ts` の両方でAIコアまで渡す。0回はバックアップ・検証を省略する。UI・HTTP中継・拡張中継の確認は `checks/webview.test.cjs`、`checks/aidiy_code.test.cjs`、`checks/code-extension.test.cjs` を使う。単独版は既存のbundleを使うため、変更後に `npm run compile` で生成物を更新する。

```powershell
Set-Location frontend_vscode
npm ci
npm run check
npm test
npm run live:test
npm run package
python -m unittest discover -s checks -p "test_*.py"
```

`npm run check` は Code / Live の型チェック、`npm test` は Code 側の Node.js テスト（`checks/*.test.cjs`。専用ウィンドウの起動は Live も含む）、`npm run live:test` は Live の Node.js テスト（`aidiy_live/checks/`）を実行する。Python テストはセットアップ・Electron 準備・拡張解除・クリーンアップ・モデル候補をモックで検証する。いずれも AI API や実バックエンドを呼ばない。Code のAIコア中継は模擬WebSocket/APIと実HTTP/SSEを組み合わせて検証する。

確認内容:

- TypeScript の型エラーがない。
- 日本語長文を stdin で渡せる。
- stdout の正式回答、stderr の進捗、Hermes セッション ID を分離できる。
- `copilot-cli`、`codex-cli`、`claude-code` が `-Q --oneshot-stdin` でも Hermes の API Provider 解決へ入らず、各 CLI を直接起動する。
- 非ゼロ終了、起動エラー、停止、タイムアウトを呼び出し元へ返せる。
- Windows の AiDiy `.cmd` をシェルなしで解決できる。
- packet が開始、進捗、終了または中断、正式回答の順になる。
- Code の両init前・切断中のHermes実行と検証0固定、オンライン／オフライン別のモデル保存・再起動後の復元、Hermes実行中の再接続と完了後のオンライン復帰、5秒間隔の再接続、自動接続OFFによる予約済み再試行の中止と新規・履歴復帰からの接続抑止、ONへの復帰と起動時ON、遅延イベント無視、モデルAPIのNG、破棄を確認する。接続済みで送信・停止・履歴復帰・CLI別モデル候補が動く。
- VS Code 側で旧 `workspaceState` の単一会話を履歴へ移行でき、作業フォルダごとに履歴が分かれる。最終選択モデルが再起動後と新規会話へ引き継がれる。
- `dist/aidiy-code-<version>.vsix` と `dist/aidiy-live-<version>.vsix` が生成され、それぞれのファイルだけを含む。
- Live のセッション・音声パケット・WebSocket 中継・モデル API・切断・Origin 拒否を模擬バックエンドで確認できる。VS Code / 単独画面の両方で会話表示と末尾追従が動き、単独画面では起動時のモデル指定で1回だけ自動接続する。拡張ではタブを切り替えても接続を保持し、非表示中はマイクを止める。

Windows の実 VS Code で拡張ホストまで確認するときは、依存導入と compile 後に次を使う。

```powershell
./scripts/test-extension-host.ps1
./scripts/test-extension-host.ps1 -Scenario Code
./scripts/test-extension-host.ps1 -Scenario Live
```

通常の VS Code プロファイルへ配置する確認は `_setup.py` を使う。試用ホストの `out/manual-profile` と混同しない。

Code / Live はどちらも `package.json` の `extensionKind` を `["workspace"]` とし、配置・解除の対象環境を揃える。Remote SSH / WSL / Codespaces では接続先の拡張ホストで動かす。旧版の Live の `["ui", "workspace"]` は接続元を優先するため、Windows 側に配置された Live を Linux の Remote CLI で解除できない。既存の接続元 Live は接続元の拡張機能一覧、または `code --uninstall-extension aidiy.aidiy-live` で一度解除する。`npm run package` で VSIX を再生成し、`python frontend_vscode/_setup.py --extensions-only` で接続先に配置して、Code / Live の両 ID が同じ拡張一覧にあることを確認する。Live の WinMM マイクは Windows の拡張ホスト用であり、Linux の拡張ホストでは単独ブラウザ版を使用する。Linux の cleanup は接続先で両 ID の解除と解除後の一覧を確認し、Live が残れば失敗にする。Remote CLI では接続元の旧 Live を確認できないことも表示する。

Code / Live の単独起動では、Electron の引数をエントリファイルだけにする。Chromium が追加のファイル引数を解釈して異常終了する場合があるため、起動設定は子プロセスの環境変数で渡す。Code は `AIDIY_CODE_PROJECT` / `AIDIY_CODE_READY` / `AIDIY_CODE_MODEL`、Live は `AIDIY_LIVE_BACKEND` / `AIDIY_LIVE_READY` / `AIDIY_LIVE_PROJECT` / `AIDIY_LIVE_MODELS` を使う。表示後の `windowShown: true` 通知は維持する。Code のブラウザ版は Node.js の引数で従来どおり渡す。

ルートの `vscode_code.bat` / `vscode_live.bat` は `scripts/cli_bat/_hermes_cli.bat` と同じ形式でモデルを選び、セットアップ済みの `aidiy_code` / `aidiy_live` コマンドを呼ぶ。`%USERPROFILE%\.local\bin\` の生成済み `.cmd` があれば使い、無ければ PATH 上の同名コマンドを呼ぶ。bat を別プロジェクトのルートへコピーすると、bat の配置先が作業フォルダになる。コピー先に `frontend_vscode` を置く必要はない。起動失敗時は `pause` し、終了コードを保持する。ダブルクリックで起動した場合も、閉じる前に表示されたエラーを確認できる。Electron が未配置なら AiDiy の配置先で `python frontend_vscode/_setup.py` を実行して準備する。ブラウザ版を確認する場合は、各 bat に `--browser` を付ける。bat 本体の案内とメニューは ASCII、改行は CRLF で保存する。Node.js の日本語出力とパス表示が文字化けしないよう、bat / `.cmd` の先頭では `chcp 65001 >nul` を実行する。生成済みランチャーだけを更新する場合は `python frontend_vscode/_setup.py --launchers-only` を使う。

Live の単独画面では起動設定の `モデル設定` にモデル名がある場合、または `--connect` が指定された場合、初期設定の読み込み後に1回だけ自動接続する。`--connect` は Electron の `AIDIY_LIVE_CONNECT` とブラウザ起動引数を通り、中継の画面設定 `自動接続` へ渡す。モデル未指定なら保存済み選択（未保存なら Core の既定設定）を使う。モデル未指定・Provider だけの指定で `--connect` が無い場合と、VS Code 拡張は手動で接続する。自動接続は音声再生の許可待ちで止めず、マイクは OFF にする。接続失敗・手動切断・画面終了の後には自動再試行しない。`aidiy_live/checks/view.test.cjs` で3種のモデル、接続失敗、音声再生の許可待ち、画面終了を検証する。

ルート `_start.py` の Code / Live は `frontend_vscode/_start.py` から同じコマンド入口を使う。Code は待機指定を付けず独立起動し、Live は `--foreground --connect` で起動する。手動で閉じた画面は自動再表示せず、全体起動の起動前整理・終了時は Code / Discord とその配下を継続し、Live を `scripts/standalone_processes.py` で照合して停止する。明示的な cleanup では Code / Discord も停止する。共通の Electron バイナリだけで判定して未選択の Code / Live を止めない。起動選択・既定値・コマンド引数・停止対象は `checks/test_start.py` と Discord の `checks/test_lifecycle.py` で外部接続なしに検証する。

Live のブラウザ版は通常の `--browser` と Electron 失敗時の自動切り替えでサーバーを分離し、CMD / PowerShell へ戻る。画面は localhost 中継の `presence`（SSE）へ接続し、最後の画面が閉じて約60秒後にサーバーを終了する。`--browser --foreground` は診断用、`--serve` は URL の表示と手動終了用としてターミナル上で実行する。`aidiy_live/checks/launcher.test.cjs` では、GUI が常駐してもランチャーが戻ることと、Electron 失敗時にもブラウザ中継が動いたまま戻ることを検証する。

## バージョン更新時

当面のバージョン番号は `0.1.0` に固定する。機能変更だけを理由に更新しない。将来、明示的に固定解除または改版する場合は次を同時に確認する。

- `package.json` と `aidiy_live/package.json` の `version`。
- `scripts/package.mjs` に固定している VSIX ファイル名（`-0.1.0.vsix`）。`_setup.py` は `package.json` の `version` から VSIX のパスを組み立てるため、両者を揃える。
- `README.md` と `aidiy_live/README.md` の手動配置用 VSIX ファイル名。
- `checks/test_setup.py` / `checks/test_extensions.py` のバージョンを含む期待値。

`scripts/build.mjs` は Webview の依存パッケージから `dist/THIRD_PARTY_NOTICES.txt` を再生成する。依存追加後は VSIX 内にライセンス文書が含まれることを確認する。

## クリーンアップ

```powershell
python frontend_vscode/_cleanup.py
```

ルートの `python _cleanup.py` でも、`command_hermes` の次に `frontend_vscode` を選択できる。拡張名が `aidiy-` で始まる配置済み拡張（`publisher.aidiy-*`）をすべて解除し、拡張一覧に対象が残っていないことを確認してから、`~/.local/bin` の Code / Live ランチャー（旧名 `aidiy_vscode` を含む）、`node_modules`、`dist`、`aidiy_live/dist`、`out`、`frontend_vscode` 直下の `*.vsix`、Python cache を削除する。セットアップとクリーンアップの対象判定・解除確認は `frontend_vscode/scripts/vscode_extensions.py` で共有する。解除が失敗した場合はランチャー・生成物を削除しない。

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
| 回答が出ない | VS Code 出力パネルの `AiDiy (Code)`、CLI の終了コード、認証が必要なら「対話 CLI」 |
| `Session not found` | 古い拡張では新しい会話を開始する。更新版では `--resume` を外して一度だけ自動再試行するため、実行ログと保存セッション ID を確認する |
| VSIX に変更が入らない | `npm run package` の prepublish、Code の `dist/extension.js` / `dist/webview.js`、Live の `aidiy_live/dist/extension.js` / `aidiy_live/dist/view.js`、`--force` 配置 |
| Live の専用ウィンドウでマイクが ON にならない | `aidiy_live/permissions.cjs` の origin 正規化と音声・メインフレーム制限。Windows のサウンド入力にデバイスがあるかを確認する。リモートデスクトップでは録音転送を有効にして再接続する。詳細は `aidiy_live/README.md` の「マイクを ON にできない場合」 |

## Live のローカル接続先

- 接続先の画面表示、`--backend`、`aidiyLive.backendUrl` は使わない。`aidiy_live/local-backend.cjs` がホストを `127.0.0.1` に固定し、AiDiy配置先から親へ、次に作業フォルダから親へ `_config/AiDiy_key.json` を探索して `PORT_CORE` を使う。設定ファイルが無い配布済み拡張では8091を使う。読込失敗・不正ポートは既定値で隠さずエラーにする。
- ランチャー・ブラウザ中継・拡張ホストで同じ解決処理を使う。ポート変更後はCoreとLiveを再起動する。モデル選択画面に接続先欄を再追加しない。
- `checks/launcher.test.cjs` で既定起動と共通ポート変更後の起動を確認する。単独起動の `launch.mjs` は `build-state.cjs` でソース・生成物のハッシュを照合し、不一致・生成物欠落・旧配置で記録がない場合に起動前に再生成する。HTMLだけ更新され、削除済み要素を参照する古いJavaScriptが残る状態を避ける。手動では `frontend_vscode` の `npm run live:compile` で更新できる。VS Code拡張はVSIXの更新も必要。
- 画面テストの `getElementById` は実HTMLにないIDへ `null` を返す。任意IDのモック要素を生成すると、HTMLとJavaScriptの不整合を見逃す。
- モデル情報APIへの通信失敗は、単独版・拡張とも実際の接続先と原因コードを表示する。`ECONNREFUSED` ならローカルCoreの起動・待受ポートを確認する。OpenAI側の障害と区別し、画面表示だけでAPIキーやモデルの問題と判断しない。

## Codespaces でブラウザ版が正常終了してしまう場合

- Code / Live / Discord は、通常のブラウザ版では初回120秒、最後の画面切断後60秒で終了する。Codespaces では転送登録・ブラウザ認証が遅れるため、`src/forwarded-origin.ts` の `接続元許可.初回待機時間` を未設定にし、初回接続まで自動終了しない。接続後の60秒の終了条件は維持する。
- `scripts/launch-project.mjs` はトークン付き localhost URL を `$BROWSER`（VS Code の `--openExternal`）へ渡す。転送先 URL を手で組み立てて直接渡すと、VS Code の localhost 転送・URI 解決を経由しない。localhost URL も端末へ表示し、自動転送を促す。転送先のルートではなく起動時のパスを含む URL を開く。再起動するとポートとパスが変わる。
- `[WARN] ... 終了コード: 0` は正常終了であり、ポート転送の障害とは限らない。待受プロセス、転送登録、トークン付きパスへの環境内応答、認証付き外部応答を照合する。
- `checks/browser-mode.test.cjs`、`aidiy_live/checks/live.test.cjs`、Discord の `checks/web-server.test.ts` で初回120秒以上待っても終了しないことと画面切断後の終了を確認する。
