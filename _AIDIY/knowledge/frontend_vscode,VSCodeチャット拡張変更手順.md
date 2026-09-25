# VS Code チャット拡張変更手順

> 文書: `frontend_vscode,VSCodeチャット拡張変更手順.md` | 実装: `frontend_vscode/package.json`, `frontend_vscode/src/extension.ts`, `frontend_vscode/src/runner.ts`, `frontend_vscode/src/protocol.ts`, `frontend_vscode/src/webview.ts`, `frontend_vscode/src/standalone.ts`

## このメモを使う場面

- VS Code の AiDiy チャット、コマンド、設定を変更する。
- `aidiy_hermes` の起動、停止、Provider / モデル選択を調整する。
- Webview と単独試用画面を変更する。
- VSIX を生成し、VS Code へ配置して確認する。

## 変更箇所の選び方

| 変更内容 | 主なファイル | 同時に確認するもの |
|----------|--------------|--------------------|
| ビュー、コマンド、設定 | `package.json`, `src/extension.ts` | `README.md`, `media/chat.html` |
| CLI 探索、引数、標準入出力、停止 | `src/runner.ts` | `test/runner.test.cjs` |
| AIコード互換 packet | `src/protocol.ts` | `backend_server/AIコア/AIコード.py`, `backend_server/AIコア/AIコード_cli.py` |
| チャット表示、入力 | `src/webview.ts`, `media/chat.html`, `media/chat.css` | `standalone/bridge.js`, `test/standalone.test.cjs` |
| Provider / モデル候補 | `scripts/model-catalog.py` | `command_hermes` の picker / Provider 実装 |
| 単独試用サーバー | `src/standalone.ts`, `standalone/bridge.js` | `test/standalone.test.cjs` |
| bundle / VSIX | `scripts/build.mjs`, `package.json` | `.vscodeignore`, `dist/THIRD_PARTY_NOTICES.txt` |

## 実装上の維持事項

- 常駐バックエンドや AI コア WebSocket を経由せず、拡張プロセスから `aidiy_hermes` を直接起動する。
- CLI は `shell: false` で起動し、要求本文は標準入力で渡す。要求文をコマンドライン引数へ埋め込まない。
- 拡張側から `--yolo` を追加しない。
- `input_text` / `input_request` / `cancel_run` / `output_stream` / `output_text` の識別子と、開始 `STX`・終了 `ETX`・中断 `CAN` の1バイト制御値を既存 AIコード実装と揃える。制御値に改行を含めず、Webview にも表示しない。
- `.cmd` は AiDiy `_setup.py` が生成する `PY` / `CLI` 形式だけを解析し、任意の batch を実行しない。
- ワークスペース未信頼時、仮想ワークスペース、Web 版では CLI を実行しない。
- Webview では Markdown の HTML と外部画像を無効のまま維持し、外部リンクは `http` / `https` のみにする。
- `webview.ts` を変えた場合は VS Code 拡張モードと単独試用モードの両方を確認する。
- Provider / モデル選択は VS Code 上部の Quick Pick ではなく、`media/chat.html` のチャットパネル内ダイアログで行う。候補は `chooseModel` / `modelCatalog` / `modelCatalogError`、確定値は `setModel` で Webview と実行層の間を受け渡す。
- Hermes の Provider / モデル一覧を複製せず、`scripts/model-catalog.py` から既存 picker を再利用する。
- モデル候補は provider ごとの固定キャッシュにせず、選択画面を開くたび CLI から取得する。特に `openai_oauth` は認証アカウントのライブ候補が変わり得る。
- 外部 CLI Provider のモデルが `auto` の場合は `--model auto` を渡さず、Copilot / Codex / Claude CLI 自身の既定モデル選択へ任せる。
- `antigravity-cli` は Hermes の外部 CLI Provider 一覧から取得する。`xai-oauth` は API Provider のカタログ入口に含め、`grok-4.6` を Hermes の curated model 一覧から取得する。
- xAI OAuth の初回認証は静的なワンショット実行中ではなく、拡張の「対話 CLI」から `/model` で `xai-oauth` を選ぶか、`hermes auth add xai-oauth` を実行する。

## セットアップと配置

プロジェクト全体ではルートから実行し、`command_hermes` の次に `frontend_vscode` を選ぶ。

```powershell
python _setup.py
```

拡張だけを処理する場合:

```powershell
python frontend_vscode/_setup.py
```

`frontend_vscode/_setup.py` は `npm install`、`npm update`、VSIX 生成、`code --install-extension --force` を順に実行し、最後に拡張 ID とバージョンを再取得して配置を確認する。`code` が PATH に無い場合は、稼働中の Codespaces / Dev Container / Remote SSH の Remote CLI と VS Code の標準配置先も探索する。単にファイルが存在するだけでなく、`--version` に成功した CLI だけを使う。

配置は拡張機能ファイルを更新するだけで、VS Code 本体や AiDiy の常駐サービスを停止しない。すでに VS Code が起動している場合、変更の反映にはウィンドウ再読み込みが必要になる。

## 変更後の検証

```powershell
Set-Location frontend_vscode
npm ci
npm run check
npm test
npm run package
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
- `dist/aidiy-hermes-<version>.vsix` が生成される。

Windows の実 VS Code で拡張ホストまで確認するときは、依存導入と compile 後に次を使う。

```powershell
./scripts/test-extension-host.ps1
```

通常の VS Code プロファイルへ配置する確認は `_setup.py` を使う。試用ホストの `out/manual-profile` と混同しない。

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

ルートの `python _cleanup.py` でも、`command_hermes` の次に `frontend_vscode` を選択できる。配置済みの `aidiy.aidiy-hermes` を解除し、解除後に拡張一覧から消えたことを確認してから、`node_modules`、`dist`、`out`、Python cache を削除する。

cleanup は VS Code 本体を終了しない。起動中の拡張ホストには再読み込みまで旧コードが残る場合があるため、解除を画面へ反映するときだけ利用者が VS Code のウィンドウを再読み込みする。CLI が利用できない、解除後も拡張が残る、生成物を削除できない場合は失敗として終了する。

## 問題の切り分け

| 症状 | 確認箇所 |
|------|----------|
| `code` が見つからない | VS Code CLI の PATH、`frontend_vscode/_setup.py` の `find_vscode_cli()` |
| Hermes が見つからない | `aidiyHermes.cliPath`、`~/.local/bin`、`command_hermes/.venv` |
| Provider / モデルが空 | `scripts/model-catalog.py`、Hermes 設定、Cli Path が AiDiy CLI を指すか |
| 送信できない | ワークスペース信頼、フォルダが開かれているか、実行中状態 |
| 回答が出ない | VS Code 出力の `AiDiy`、CLI の終了コード、認証が必要なら「対話 CLI」 |
| VSIX に変更が入らない | `npm run package` の prepublish、`dist/extension.js` / `dist/webview.js`、`--force` 配置 |
