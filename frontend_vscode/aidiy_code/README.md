# AiDiy (Code)

`aidiy_code` は、`aidiy_hermes` CLI を操作するコード用スタンドアロンです。表示名は **AiDiy (Code)** です。VS Code 拡張と共通の会話画面・CLI 実行層を使います。

セットアップ後は、作業対象のフォルダで `aidiy_code` を実行します。プロジェクトルートから直接起動する場合は `frontend_vscode/aidiy_code.cmd` を使えます。ブラウザモードは `aidiy_code --browser`、フォルダを明示する場合は `aidiy_code "C:\work\project"` です。

ルートの `vscode_code.bat` は Sonnet 5.5（Copilot CLI）、GPT-6 Astra／GPT-6.1 Sol／GPT-5.6 Terra／GPT-6 Luna（`openai_oauth`） の選択メニューを表示します。**未入力で Enter を押すと、Provider／モデルの起動引数を付けずに起動し、既定値とモデル選択は Code モジュールに任せます。** 番号を入力した場合は、対応する `--provider` / `--model` を渡します。追加の引数はそのまま転送します。起動後も画面の「モデル」から選択できます。`vscode_code.bat --browser` でブラウザ起動もできます。

直接指定する場合:

```powershell
aidiy_code --provider copilot_cli --model claude-sonnet-5.5
aidiy_code --provider openai_oauth --model gpt-6-astra --browser
```

`copilot_cli` は Hermes の `copilot-cli` として処理します。引数なしの `aidiy_code` は最後に画面で手動選択したモデル（`~/.aidiy/aidiy_code_model.json`、未保存なら既定値 `openai_oauth` / `gpt-6.1-sol`）で起動します。Provider だけ指定した場合は、保存済みと同じ Provider ならそのモデルを復元し、異なる場合はモデルを自動にします。モデルだけ指定した場合は既定の Provider を使います。起動引数だけでは保存済み選択を上書きしません。モデル指定は子プロセスにも起動引数で渡し、環境変数は使いません。

共通の利用・検証方法は [`../README.md`](../README.md) を参照してください。起動処理は `launch.mjs`、専用ウィンドウは `desktop.cjs`、単独サーバーは `src/server.ts` に分けています。
