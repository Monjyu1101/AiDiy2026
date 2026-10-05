# AiDiy (Code)

**AiDiy (Code)** は `aidiy_hermes` CLI を直接起動し、プロジェクトのコード調査・編集を支援する独立した VS Code 拡張です。同じチャット画面を使うスタンドアロンも提供します。

拡張 ID は `aidiy.aidiy-code`、配布ファイルは `dist/aidiy-code-0.1.0.vsix` です。拡張機能一覧の歯車から、この拡張を個別に無効化・解除できます。

拡張バージョンは当面 `0.1.0` に固定します。

実装構成と設計方針は [AGENTS.md](./AGENTS.md)、変更・検証手順は [`../_AIDIY/knowledge/frontend_vscode,VSCodeチャット拡張変更手順.md`](../_AIDIY/knowledge/frontend_vscode,VSCodeチャット拡張変更手順.md) を参照してください。

## 導入

1. セットアップ済みの `aidiy_hermes` を用意します。拡張モードを使う場合は VS Code **1.106 以降**も必要です。
2. AiDiy ルートの `python _setup.py` で、Hermes の次に表示される **フロントエンド(vscode)** を選びます。単体では `python frontend_vscode/_setup.py` を実行できます。
3. 単独画面は `aidiy_code` を実行します。拡張モードは VS Code でフォルダを開き、コマンドパレットから **AiDiy (Code): チャットを開く**を実行します。

セットアップは依存関係と Electron バイナリの事前導入、単独起動コマンドの作成と、VS Code CLI がある場合は VSIX を生成・配置します。`aidiy_code` のランチャーは `aidiy_hermes` と同じ `~/.local/bin` に配置します（Windows は `.cmd`）。このフォルダが PATH にない場合は追加してください。ランチャーだけを更新する場合は `python frontend_vscode/_setup.py --launchers-only` を使います。この作業コピーから配置した旧名 `aidiy_vscode` は解除します。手動で VSIX を配置する場合は、拡張機能画面の `…` → **VSIX からのインストール**で、`dist/aidiy-code-0.1.0.vsix` を選びます。解除と生成物削除は `python frontend_vscode/_cleanup.py`、またはルートの `python _cleanup.py` から実行できます。

既定では右側のセカンダリサイドバーに表示されます。VS Code の配置を変更している場合は、ビューの移動操作で配置を調整できます。

CLI は PATH と `~/.local/bin` から探索します。AiDiy の `_setup.py` が生成した Windows の `.cmd` に対応します。見つからない場合は、拡張の設定で **Cli Path** に `aidiy_hermes.cmd` または `cli_main.py` の絶対パスを指定してください。Python を直接指定する場合は **Python Path** を使用します（空欄では `cli_main.py` に隣接する `.venv`）。CLI 本体・Python・API 認証情報は VSIX に含めません。

## 操作

### チャット単独ウィンドウで使う

セットアップ後は、作業対象フォルダで次を実行します（Node.js とセットアップ済みの Hermes が必要です）。

```powershell
aidiy_code
```

別のフォルダを明示する場合は `aidiy_code "C:\work\my-project"` と指定できます。セットアップ前の試用や開発中は、作業対象フォルダから `node /path/to/AiDiy2026/frontend_vscode/aidiy_code/launch.mjs` を実行します。`launch-extension-dev.ps1` は Windows で VS Code 拡張の開発用ウィンドウを開くスクリプトです。

単独画面は Electron のフレームレスウィンドウで開き、起動時のカレントフォルダを作業対象にします。AiDiy ロゴのあるヘッダーをドラッグして移動でき、右上のボタンで最小化・最大化／復元・終了を操作できます。ウィンドウの端でサイズを変更できます。モデル選択・送信・進捗表示・停止・新規会話・会話履歴の選択と削除は VS Code 拡張と共通です。会話は単独サーバーのメモリに保持し、終了すると消えます。専用ウィンドウを閉じるとサーバーと実行中の CLI を停止します。VS Code の選択コード添付は拡張モードで利用してください。

既定ブラウザで開く場合は `aidiy_code --browser`（フォルダ指定も併用可能）を使います。Windows は Chrome / Edge のアプリウィンドウ、macOS / Linux は既定のブラウザで開きます。このモードはブラウザのウィンドウ枠を使用し、タブ／ウィンドウを閉じて60秒後にサーバーを停止します。Electron バイナリは `python frontend_vscode/_setup.py` で事前に取得・確認します。Avatar と共通のセットアップ処理で、同じバージョンの配置済みバイナリや `_cache/electron/` の保存済み ZIP を再利用します。未取得の場合だけ Python で GitHub から取得します。起動時にはダウンロードせず、未準備の場合はセットアップの再実行を案内します。`npm ci` だけではバイナリが取得されない場合があります。Electron は VSIX には含めません。

VS Code 拡張として試す場合は、次の手順を使います。

作業対象のフォルダで PowerShell を開き、`frontend_vscode/launch-extension-dev.ps1` を実行します。たとえば AiDiy2026 のルートからは次のコマンドです。

```powershell
.\frontend_vscode\launch-extension-dev.ps1
```

起動したフォルダがプロジェクトフォルダになります。VS Code の開発用ウィンドウが開くので、コマンドパレットの **AiDiy (Code): チャットを開く**で操作してください。実 CLI に接続するため、通常のチャットと同様に依頼を実行します。

試用時の VS Code 設定は `out/manual-profile` に保存します。通常の VS Code で同じフォルダを開いていても、試用ウィンドウで開けます。

### チャット操作

画面は会話と入力欄を中心とし、フォルダの追加・選択は VS Code 標準の操作だけを使います。「新規」「一覧」、モデル選択、履歴削除の確認、送信、停止は拡張モードと単独画面で同じチャットパネルから操作します。「設定」「選択コード」「実行ログ」「対話 CLI」は VS Code のビューの `…` メニューまたはコマンドパレットから操作できます。

- **送信**: 送信ボタンは空欄・空白だけの入力では白背景・青紫の枠・黒い紙ヒコーキで無効です。接続や入力の準備が整っていないときは灰色になります。送信できる文字を入力すると青紫になり、押すと送信します。入力欄の Enter は通常の改行です。Tab で送信ボタンへ移動し、そこで Enter を押すと送信します。日本語 IME の変換確定では送信しません。
- **停止**: 実行中の CLI と子プロセスを停止します。実行済みのファイル変更は残ります。
- **実行表示**: 実行中はヘッダー背景と上下のラインがシアンでゆっくり明滅し、終了・停止時に通常表示へ戻ります。OS の「動きを減らす」が有効な場合は明滅を抑えます。
- **新規**: 新しい会話に切り替えます。旧会話は履歴に残ります。
- **会話一覧**: 会話画面右上の「一覧」で、現在の作業フォルダの会話を最終更新日時の新しい順に表示します。日時と最初の依頼から会話を選択でき、各行の「削除」ではチャットパネル内に確認を表示します。実行中は切り替えと削除を行えません。「戻る」で今の会話に戻ります。
- **選択コード**: エディターで選択したコードを右クリックメニューから添付します。
- **プロバイダ／モデル**: 送信ボタン左の「モデル」ボタンをクリックし、チャットパネル内の選択画面でプロバイダ → モデルの順に選びます。候補は画面を開くたび取得します。外部 CLI の候補には AiDiy の `_config/AiDiy_code_*.json` を使います。「自動」は CLI の設定を使用します。選択内容はすぐに表示・保存され、次の送信に使われます。

初期値は `openai_oauth / gpt-6.1-sol` で、CLI にも両方を明示して渡します。モデルの最終選択は VS Code 全体で保存し、次に開いたときと新規会話で使います。履歴から会話を再開したときは、その会話で使っていたモデルに戻します。OpenAI OAuth は、拡張が動く環境の Codex CLI 認証ストア（`${CODEX_HOME:-~/.codex}/auth.json`）を使います。Codex CLI でログイン済みなら同じ認証を利用できます。
- `antigravity-cli` などの外部 CLI では「自動」に加え、設定 JSON にあるモデルを選べます。明示したモデルは CLI の `--model` に渡します。
- `xai-oauth / grok-4.6` もプロバイダ／モデル選択から指定できます。初回は「対話 CLI」を開き、`/model` で `xai-oauth` を選ぶか `hermes auth add xai-oauth` で認証してください。
- **実行ログ**: stdout / stderr の実行状況を出力パネルで確認します。
- **対話 CLI**: 認証、`/model` などの対話操作が必要な場合に利用します。

プロジェクトフォルダには、VS Code で開いている作業フォルダを自動で使います。複数フォルダのワークスペースでは、編集中のファイルが属するフォルダを優先し、該当がなければ先頭のフォルダを使います。会話開始後はそのフォルダを維持します。別フォルダで会話を始める場合は「新規」を使ってください。会話履歴は作業フォルダごとに表示し、会話ごとの表示履歴（最新60件、最大200万文字）と Hermes のセッションIDを VS Code のワークスペース内ストレージに保存します。

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

制御コードはストリームの状態遷移にだけ使い、Webview には表示しません。転送は Webview と拡張間のメッセージ通信で行い、拡張が CLI を直接起動します。AiDiy の常駐バックエンドへの WebSocket 接続は使用しません。

現行 Hermes の quiet モードは、処理ログを逐次出力し、回答本文を完成後に stdout へ出力します。そのため、実行状況はストリーム表示し、回答は完成後に Markdown で表示します。文字単位の回答ストリーミングには CLI 側の対応が必要です。

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
