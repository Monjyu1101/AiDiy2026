# AiDiy (Code)

**AiDiy (Code)** は `aidiy_live` と同じローカル AIコアに接続し、`AIコード.vue` と同じ Code CLI を選択して、プロジェクトのコード調査・編集を支援する独立した VS Code 拡張です。同じチャット画面を使うスタンドアロンも提供します。

拡張 ID は `aidiy.aidiy-code`、配布ファイルは `dist/aidiy-code-0.1.0.vsix` です。拡張機能一覧の歯車から、この拡張を個別に無効化・解除できます。

拡張バージョンは当面 `0.1.0` に固定します。

入力欄の「検証ループ」は0〜3回を選択できます（初期値1回）。0回はバックアップ・検証なし、1〜3回は指定回数を上限にバックアップと検証・修正を実行します。差分がなくなれば途中で終了します。単独起動版とVS Code拡張で共通です。

単独起動版 `aidiy_code` とVS Code拡張は未接続中も文字入力で送信でき、自動的に `aidiy_hermes` を直接実行します（検証0回固定）。接続済みと未接続の選択モデルは別々に保存し、接続状態に合わせて表示と実行モデルを切り替えます。`aidiy_code --offline` で直接起動することもできます。詳しくは [単独起動版README](./aidiy_code/README.md) を参照してください。

実装構成と設計方針は [AGENTS.md](./AGENTS.md)、変更・検証手順は [`../_AIDIY/knowledge/frontend_vscode,VSCodeチャット拡張変更手順.md`](../_AIDIY/knowledge/frontend_vscode,VSCodeチャット拡張変更手順.md) を参照してください。

## 導入

1. AiDiy の Core サーバーを起動し、使用する Code CLI の認証を用意します。拡張モードを使う場合は VS Code **1.106 以降**も必要です。
2. AiDiy ルートの `python _setup.py` で、Hermes の次に表示される **フロントエンド(vscode)** を選びます。単体では `python frontend_vscode/_setup.py` を実行できます。
3. 単独画面は `aidiy_code` を実行します。拡張モードは VS Code でフォルダを開き、コマンドパレットから **AiDiy (Code): チャットを開く**を実行します。

セットアップは依存関係と Electron バイナリの事前導入、単独起動コマンドの作成と、VS Code CLI がある場合は VSIX を生成・配置します。`aidiy_code` のランチャーは `aidiy_hermes` と同じ `~/.local/bin` に配置します（Windows は `.cmd`）。このフォルダが PATH にない場合は追加してください。ランチャーだけを更新する場合は `python frontend_vscode/_setup.py --launchers-only` を使います。この作業コピーから配置した旧名 `aidiy_vscode` は解除します。手動で VSIX を配置する場合は、拡張機能画面の `…` → **VSIX からのインストール**で、`dist/aidiy-code-0.1.0.vsix` を選びます。解除と生成物削除は `python frontend_vscode/_cleanup.py`、またはルートの `python _cleanup.py` から実行できます。

既定では右側のセカンダリサイドバーに表示されます。VS Code の配置を変更している場合は、ビューの移動操作で配置を調整できます。

未接続時の実行と「対話 CLI」の Hermes は PATH と `~/.local/bin` から探索します。AiDiy の `_setup.py` が生成した Windows の `.cmd` に対応します。見つからない場合は、拡張の設定で **Cli Path** に `aidiy_hermes.cmd` または `cli_main.py` の絶対パスを指定してください。Python を直接指定する場合は **Python Path** を使用します（空欄では `cli_main.py` に隣接する `.venv`）。CLI 本体・Python・API 認証情報は VSIX に含めません。

## 操作

### チャット単独ウィンドウで使う

セットアップ後は、作業対象フォルダで次を実行します（Node.js と起動済みの AIコアが必要です）。

```powershell
aidiy_code
```

別のフォルダを明示する場合は `aidiy_code "C:\work\my-project"` と指定できます。セットアップ前の試用や開発中は、作業対象フォルダから `node /path/to/AiDiy2026/frontend_vscode/aidiy_code/launch.mjs` を実行します。`launch-extension-dev.ps1` は Windows で VS Code 拡張の開発用ウィンドウを開くスクリプトです。

単独画面は Electron のフレームレスウィンドウで開き、起動時のカレントフォルダを作業対象にします。AiDiy ロゴのあるヘッダーをドラッグして移動でき、右上のボタンで最小化・最大化／復元・終了を操作できます。ウィンドウの端でサイズを変更できます。モデル選択・送信・進捗表示・停止・新規会話・会話履歴の選択と削除は VS Code 拡張と共通です。会話は単独サーバーのメモリに保持し、終了すると消えます。専用ウィンドウを閉じると実行中のコード処理へ停止要求を送り、接続と単独サーバーを終了します。VS Code の選択コード添付は拡張モードで利用してください。

既定ブラウザで開く場合は `aidiy_code --browser`（フォルダ指定も併用可能）を使います。Windows は Chrome / Edge のアプリウィンドウ、macOS / Linux は既定のブラウザで開きます。このモードはブラウザのウィンドウ枠を使用し、タブ／ウィンドウを閉じて60秒後（初回は120秒後、Codespaces では初回接続まで終了しない）にサーバーを停止します。GitHub Codespaces（`CODESPACES=true`）と画面のない Linux（`DISPLAY` / `WAYLAND_DISPLAY` なし）では、`--browser` を省略してもブラウザ版で開きます。ブラウザは VS Code / Codespaces が設定する `$BROWSER` を優先して手元の PC で開き、Codespaces ではポート転送先の URL（`https://<名前>-<ポート>.app.github.dev/…`）を使います。開けない場合は URL を表示します。判定と起動は `frontend_vscode/scripts/launch-project.mjs`、接続元の許可は `frontend_vscode/src/forwarded-origin.ts` で aidiy_code / aidiy_live / aidiy_discord 共通です。3本（aidiy_code / aidiy_live / aidiy_discord）の起動規則は `frontend_vscode/scripts/launch-project.mjs` の冒頭に一覧し、そこで共通化しています。Electron の専用ウィンドウを開けない場合（未セットアップ・起動失敗）は、理由を表示してブラウザ版に切り替えます。ブラウザ版のサーバーは、画面を閉じて60秒（初回は120秒、Codespaces では初回接続まで終了しない）で終了します。Electron バイナリは `python frontend_vscode/_setup.py` で事前に取得・確認します。Avatar と共通のセットアップ処理で、同じバージョンの配置済みバイナリや `_cache/electron/` の保存済み ZIP を再利用します。未取得の場合だけ Python で GitHub から取得します。起動時にはダウンロードせず、未準備の場合はセットアップの再実行を案内してブラウザ版で開きます。`npm ci` だけではバイナリが取得されない場合があります。Electron は VSIX には含めません。

VS Code 拡張として試す場合は、次の手順を使います。

作業対象のフォルダで PowerShell を開き、`frontend_vscode/launch-extension-dev.ps1` を実行します。たとえば AiDiy2026 のルートからは次のコマンドです。

```powershell
.\frontend_vscode\launch-extension-dev.ps1
```

起動したフォルダがプロジェクトフォルダになります。VS Code の開発用ウィンドウが開くので、コマンドパレットの **AiDiy (Code): チャットを開く**で操作してください。AIコアへ接続するため、通常のチャットと同様に依頼を実行します。

試用時の VS Code 設定は `out/manual-profile` に保存します。通常の VS Code で同じフォルダを開いていても、試用ウィンドウで開けます。

### チャット操作

画面は会話と入力欄を中心とし、フォルダの追加・選択は VS Code 標準の操作だけを使います。「新規」「一覧」、モデル選択、履歴削除の確認、送信、停止は拡張モードと単独画面で同じチャットパネルから操作します。「設定」「選択コード」「実行ログ」「対話 CLI」は VS Code のビューの `…` メニューまたはコマンドパレットから操作できます。

- **送信**: 送信ボタンは空欄・空白だけの入力では白背景・青紫の枠・黒い紙ヒコーキで無効です。接続や入力の準備が整っていないときは灰色になります。送信できる文字を入力すると青紫になり、押すと送信します。入力欄の Enter は通常の改行です。Tab で送信ボタンへ移動し、そこで Enter を押すと送信します。日本語 IME の変換確定では送信しません。
- **停止**: 実行中の CLI と子プロセスを停止します。実行済みのファイル変更は残ります。
- **自動接続**: プロジェクトバー右側に「自動接続」「新規」「一覧」を配置します。スイッチは右がON、左がOFFで、通常起動時は毎回ONです。OFFではAIコアへの接続と5秒ごとの再試行を停止し、ONへ戻すと接続します。OFF中の新規会話・履歴復帰でも接続を開始しません。実行中・モデル変更中は切り替えできません。
- **接続表示**: 自動接続ONでは未接続時は黒、接続済みはシアンのバーが4.5秒周期で明滅します。自動接続OFFでは赤いバーが同じ周期で明滅します。VS Code拡張ではタイトル行と接続状態の文字を表示しません。
- **新規**: 新しい会話に切り替えます。旧会話は履歴に残ります。
- **会話一覧**: 会話画面右上の「一覧」で、現在の作業フォルダの会話を最終更新日時の新しい順に表示します。日時と最初の依頼から会話を選択でき、各行の「削除」ではチャットパネル内に確認を表示します。実行中は切り替えと削除を行えません。「戻る」で今の会話に戻ります。
- **選択コード**: エディターで選択したコードを右クリックメニューから添付します。
- **コードAI／モデル**: 「モデル」から `aidiy_hermes`、`copilot_cli`、`codex_cli` 等を選び、各コードAIのモデルを選択します。候補は `AIコード.vue` と同じモデル情報APIから取得します。Hermes は `openai_oauth/gpt-6.1-sol`、Copilot は `gpt-6-sol` のように選択します。「自動」はAIコアの既定設定です。接続中の変更はセッションの設定だけに反映し、共通設定は保存しません。
- **接続状態**: 単独版はタイトル左側に `未接続` / `接続中` / `接続済み` を表示します。接続済みはモデル設定と入力・コード出力の初期化完了を示します。拡張・単独版とも、自動接続ONでは通信切断・接続失敗時も5秒ごとに再接続を試みます。未接続中はHermesで送信できます。接続復帰時のHermes実行は完了まで維持し、次の送信からAIコアを使います。単独版の `--offline` は自動接続OFFで起動します。この場合、ONへの切り替えは新しいオンライン会話を開始します。

未接続時のコードAIは `aidiy_hermes` 固定です。モデルは `auto`、`codex_cli/auto`、`copilot_cli/auto` と `_hermes_cli.bat` の `openai_oauth/` 付き選択値を使い、`~/.aidiy/aidiy_code_model_offline.json` に保存します。次回起動時もこの保存値を復元し、未保存なら `AiDiy_key.json` の `CODE_AIDIY_HERMES_MODEL`（候補外なら `auto`）を使います。オンライン用の保存値は変更しません。表示形式は両方とも `NAME - MODEL` です。

VS Codeで作業フォルダを開いていなくても、未接続用のモデルは選択・保存できます。送信には実行先のフォルダが必要です。「ファイル」→「フォルダーを開く」で作業対象を開くと、AIコアが未接続でも文字入力で送信が有効になります。

画面で確定したコードAIとモデルは `~/.aidiy/aidiy_code_model.json` へ保存し、拡張・単独画面で共用します。未保存ならAIコアの既定設定を使い、起動引数は保存値より優先します。`aidiy_code --provider aidiy_hermes --model openai_oauth/gpt-6.1-sol` または `aidiy_code --provider copilot_cli --model gpt-6-sol` のように起動できます。旧設定の `openai_oauth` と `gpt-6.1-sol` は Hermes の組み合わせモデルへ移行し、`copilot-cli` 等の旧名も読み替えます。新規会話は最後の手動選択を使い、履歴復帰はその会話のモデルとAIコアのセッションを使います。

接続先は Live と共通の解決処理で `127.0.0.1` と `_config/AiDiy_key.json` の `PORT_CORE`（未配置時8091）を使います。Core は拡張ホストまたは単独サーバーと同じ環境で起動してください。
- **実行ログ**: stdout / stderr の実行状況を出力パネルで確認します。
- **対話 CLI**: 認証、`/model` などの対話操作が必要な場合に利用します。

プロジェクトフォルダには、VS Code で開いている作業フォルダを自動で使います。複数フォルダのワークスペースでは、編集中のファイルが属するフォルダを優先し、該当がなければ先頭のフォルダを使います。会話開始後はそのフォルダを維持します。別フォルダで会話を始める場合は「新規」を使ってください。会話履歴は作業フォルダごとに表示し、会話ごとの表示履歴（最新60件、最大200万文字）と AIコアのセッションIDを VS Code のワークスペース内ストレージに保存します。

## ストリームの仕様

既存の `AIコード.vue` / `AIコード.py` / `AIコード_cli.py` と同じメッセージ形式を採用しています。

| 種類 | メッセージ識別 / 内容 |
|---|---|
| 要求 | `input_text`（アダプターは `input_request` も受理） |
| 停止 | `cancel_run` |
| 開始 | `output_stream` / `STX` (`0x02`) |
| 実行中 | stdout / stderr の各行を `output_stream` で逐次表示 |
| 終了 | `output_stream` / `ETX` (`0x03`) |
| 中断・異常 | `output_stream` / `CAN` (`0x18`) |
| 正式回答 | `output_text` |

制御コードは状態遷移にだけ使い、表示本文には含めません。AIコアへは `input` とコード出力 `1` の2本で接続し、両方の `init` とモデル設定の反映後に送信します。未接続時は同じ形式でHermesの出力を中継します。AIコアとHermesのセッションIDは別々に保持し、再接続で混在させません。

## 対応範囲

- Windows デスクトップ版 VS Code での利用を想定しています。Linux/macOS のプロセス起動分岐もありますが、実機検証対象は Windows です。
- Web 版 VS Code と仮想ワークスペースは対象外です。Remote SSH / WSL は未対応です。
- CLI のツール実行・承認設定に従います。拡張から `--yolo` を付けません。
- チャット入力はワンショットの要求文です。TUI のスラッシュコマンドや対話承認画面は「対話 CLI」で利用してください。
- 差分の適用ボタン、画像添付は初版には含みません。

## 開発・配布

```powershell
Set-Location frontend_vscode
npm ci
npm run check
npm test
npm run package
```

Windows の実 VS Code で登録・起動を確認する場合は、コンパイル後に `./scripts/test-extension-host.ps1 -Scenario Code` を実行します。専用の一時プロファイルで Code の登録・起動を確認します。

`dist/aidiy-code-0.1.0.vsix` が生成されます。共通セットアップで生成済み VSIX を配置する場合は、ルートから `python frontend_vscode/_setup.py --extensions-only` を実行します。セットアップは配置対象の VSIX の存在を確認し、拡張名が `aidiy-` で始まる既存拡張（`publisher.aidiy-*`）をすべて除去してから拡張を配置します。旧 `aidiy-vscode` も対象です。クリーンアップも同じ判定で除去し、解除を確認できない場合はランチャー・生成物の削除を中止します。生成物を削除する前に、この作業コピーの単独実行と専用ブラウザも強制終了し、終了を確認します。手動では各 VSIX を個別にインストールできます。`npm test` はモック CLI による検証で、AI API を呼びません。

Marketplace で公開する場合は、所有する publisher ID に `package.json` の `publisher` を合わせて公開します。初期値 `aidiy` はローカル配布用の識別子です。

仕様の参照: [Secondary Side Bar の拡張 API](https://code.visualstudio.com/updates/v1_106)、[Webview API](https://code.visualstudio.com/api/extension-guides/webview)、[VSIX の配布](https://code.visualstudio.com/api/working-with-extensions/publishing-extension)。

Codespaces のブラウザ版は、ポート転送やブラウザ認証を待てるよう、初回の画面接続までは自動終了しません。一度画面を開いた後は、最後の画面を閉じて約60秒で終了します。起動時は `$BROWSER`（VS Code のブラウザヘルパー）にトークン付き localhost URL を渡し、VS Code にポート転送と外部 URI の解決を任せます。転送先の URL を手で組み立ててヘルパーへ渡さないでください。手動では起動時に表示されるトークン付き URL を開きます。
