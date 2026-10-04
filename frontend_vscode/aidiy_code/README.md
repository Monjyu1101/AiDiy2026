# AiDiy (Code)

`aidiy_code` は、`aidiy_hermes` CLI を操作するコード用スタンドアロンです。表示名は **AiDiy (Code)** です。VS Code 拡張と共通の会話画面・CLI 実行層を使います。

セットアップ後は、作業対象のフォルダで `aidiy_code` を実行します。プロジェクトルートから直接起動する場合は `frontend_vscode/aidiy_code.cmd` を使えます。ブラウザモードは `aidiy_code --browser`、フォルダを明示する場合は `aidiy_code "C:\work\project"` です。

共通の利用・検証方法は [`../README.md`](../README.md) を参照してください。起動処理は `launch.mjs`、専用ウィンドウは `desktop.cjs`、単独サーバーは `src/server.ts` に分けています。
