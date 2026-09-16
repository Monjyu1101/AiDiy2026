# AiDiy for VS Code

`aidiy_hermes` CLI を、VS Code の右サイドバーにある専用チャットから操作する拡張機能です。

拡張バージョンは当面 `0.1.0` に固定します。

実装構成と設計方針は [AGENTS.md](./AGENTS.md)、変更・検証手順は [`../_AIDIY/knowledge/frontend_vscode,VSCodeチャット拡張変更手順.md`](../_AIDIY/knowledge/frontend_vscode,VSCodeチャット拡張変更手順.md) を参照してください。

## 導入

1. VS Code **1.106 以降**と、セットアップ済みの `aidiy_hermes` を用意します。
2. AiDiy ルートの `python _setup.py` で、Hermes の次に表示される **フロントエンド(VS Code)** を選びます。単体では `python frontend_vscode/_setup.py` を実行できます。
3. 作業フォルダを開き、コマンドパレットから **AiDiy: チャットを開く**を実行します。

セットアップは依存関係の導入、VSIX の生成、VS Code 拡張機能への配置まで実行します。手動で配置する場合は、拡張機能画面の `…` → **VSIX からのインストール**で `dist/aidiy-hermes-0.1.0.vsix` を選びます。解除と生成物削除は `python frontend_vscode/_cleanup.py`、またはルートの `python _cleanup.py` から実行できます。

既定では右側のセカンダリサイドバーに表示されます。VS Code の配置を変更している場合は、ビューの移動操作で配置を調整できます。

CLI は PATH と `~/.local/bin` から探索します。AiDiy の `_setup.py` が生成した Windows の `.cmd` に対応します。見つからない場合は、拡張の設定で **Cli Path** に `aidiy_hermes.cmd` または `cli_main.py` の絶対パスを指定してください。Python を直接指定する場合は **Python Path** を使用します（空欄では `cli_main.py` に隣接する `.venv`）。CLI 本体・Python・API 認証情報は VSIX に含めません。

## 操作

### インストール前に手元で試す

チャットだけの単独ウィンドウで試す場合は、作業対象フォルダで次を実行します（Node.js とセットアップ済みの Hermes が必要です）。

```powershell
.\frontend_vscode\start-standalone.ps1
```

Chrome / Edge のアプリウィンドウで開き、起動時のカレントフォルダを作業対象にします。実際の CLI に接続し、モデル選択・送信・進捗表示・停止・新規会話を利用できます。会話は単独サーバーのメモリに保持し、終了すると消えます。ウィンドウを閉じて60秒後にサーバーと実行中の CLI を停止します。VS Code の選択コード添付は拡張モードで利用してください。

VS Code 拡張として試す場合は、次の手順を使います。

作業対象のフォルダで PowerShell を開き、`frontend_vscode/start.ps1` を実行します。たとえば AiDiy2026 のルートからは次のコマンドです。

```powershell
.\frontend_vscode\start.ps1
```

起動したフォルダがプロジェクトフォルダになります。VS Code の開発用ウィンドウが開くので、コマンドパレットの **AiDiy: チャットを開く**で操作してください。実 CLI に接続するため、通常のチャットと同様に依頼を実行します。

試用時の VS Code 設定は `out/manual-profile` に保存します。通常の VS Code で同じフォルダを開いていても、試用ウィンドウで開けます。

### チャット操作

画面は会話と入力欄を中心とし、フォルダの追加・選択は VS Code 標準の操作だけを使います。「新規」「設定」は VS Code のビュータイトルバー、「選択コード」「実行ログ」「対話 CLI」はビューの `…` メニューまたはコマンドパレットから操作できます。

- **送信**: Enter。改行は Shift+Enter。日本語 IME の変換確定では送信しません。
- **停止**: 実行中の CLI と子プロセスを停止します。実行済みのファイル変更は残ります。
- **新規**: 新しい会話に切り替えます。旧会話の表示履歴は置き換えます。
- **選択コード**: エディターで選択したコードを右クリックメニューから添付します。
- **プロバイダ／モデル**: 送信ボタン左の表示をクリックし、プロバイダ → モデルの順に検索・選択します。Hermes の既存モデル選択処理から候補を取得します。「自動」は CLI の設定を使用します。選択内容はすぐに表示・保存され、次の送信に使われます。

初期値は `openai_oauth / gpt-5.6-sol` で、CLI にも両方を明示して渡します。選択済みのモデルと既存の会話は保持します。初期値での利用には OpenAI OAuth の認証が必要です。
- **実行ログ**: stdout / stderr の実行状況を出力パネルで確認します。
- **対話 CLI**: 認証、`/model` などの対話操作が必要な場合に利用します。

プロジェクトフォルダには、VS Code で開いている作業フォルダを自動で使います。複数フォルダのワークスペースでは、編集中のファイルが属するフォルダを優先し、該当がなければ先頭のフォルダを使います。会話開始後はそのフォルダを維持します。別フォルダで会話を始める場合は「新規」を使ってください。会話の表示履歴（最新60件、最大200万文字）と Hermes のセッションIDを VS Code のワークスペース内ストレージに保存します。

## ストリームの仕様

既存の `AIコード.vue` / `AIコード.py` / `AIコード_cli.py` と同じメッセージ形式を採用しています。

| 種類 | メッセージ識別 / 内容 |
|---|---|
| 要求 | `input_text`（アダプターは `input_request` も受理） |
| 停止 | `cancel_run` |
| 開始 | `output_stream` / `<<< 処理開始 >>>` |
| 実行中 | stdout / stderr の各行を `output_stream` で逐次表示 |
| 終了 | `output_stream` / `<<< 処理終了 >>>` |
| 中断・異常 | `output_stream` / `<<< 処理中断 >>>` または `!` |
| 正式回答 | `output_text` |

転送は Webview と拡張間のメッセージ通信で行い、拡張が CLI を直接起動します。AiDiy の常駐バックエンドへの WebSocket 接続は使用しません。

現行 Hermes の quiet モードは、処理ログを逐次出力し、回答本文を完成後に stdout へ出力します。そのため、実行状況はストリーム表示し、回答は完成後に Markdown で表示します。文字単位の回答ストリーミングには CLI 側の対応が必要です。

## 対応範囲

- Windows デスクトップ版 VS Code での利用を想定しています。Linux/macOS のプロセス起動分岐もありますが、実機検証対象は Windows です。
- Web 版 VS Code と仮想ワークスペースは対象外です。Remote SSH / WSL は未対応です。
- CLI のツール実行・承認設定に従います。拡張から `--yolo` を付けません。
- チャット入力はワンショットの要求文です。TUI のスラッシュコマンドや対話承認画面は「対話 CLI」で利用してください。
- 差分の適用ボタン、画像添付、複数会話の一覧・切り替えは初版には含みません。

## 開発・配布

```powershell
Set-Location frontend_vscode
npm ci
npm run check
npm test
npm run package
```

Windows の実 VS Code で登録・起動を確認する場合は、コンパイル後に `./scripts/test-extension-host.ps1` を実行します。専用の一時プロファイルを使います。画面単体の確認用 HTML は `node test/webview-preview.cjs` で `out/preview.html` に生成できます。

`dist/aidiy-hermes-0.1.0.vsix` が生成されます。`npm test` はモック CLI による通信・停止・メッセージ形式の検証で、AI API を呼びません。

Marketplace で公開する場合は、所有する publisher ID に `package.json` の `publisher` を合わせて公開します。初期値 `aidiy` はローカル配布用の識別子です。

仕様の参照: [Secondary Side Bar の拡張 API](https://code.visualstudio.com/updates/v1_106)、[Webview API](https://code.visualstudio.com/api/extension-guides/webview)、[VSIX の配布](https://code.visualstudio.com/api/working-with-extensions/publishing-extension)。
