# backend_tools aidiy_automations

`backend_tools` の MCP / HTTP API を組み合わせて実行する自動化スクリプトを置くフォルダです。

## 置くもの

- 動画生成、音声生成、画像生成などを連続実行する自動化
- `localhost:8095` の HTTP API を利用するジョブ
- AiDiy プロジェクト内の素材作成や確認作業を自動化するスクリプト

## 方針

- MCP サーバー本体の機能は `../tools_proc/` に実装します。
- ここには、複数の MCP 機能を組み合わせる「利用側」の処理を置きます。
- 長時間実行、外部サービス利用、ファイル大量生成を伴う場合は、冒頭に入力、出力、再実行条件を書きます。

## ビデオページ生成_紹介.py / ビデオページ生成_解説.py

AiDiy の自動化ソリューションとして、Xビデオ素材生成を 8 ステップで実行します。

主な設定は環境変数で指定できます。

- `AIDIY_VIDEO_GEN_FOLDER_NAME`: 出力フォルダ名。
- `AIDIY_VIDEO_GEN_TOPIC`: 題材、動画テーマ。
- `AIDIY_VIDEO_GEN_BASE_DIR`: 生成先ルートフォルダ。
- `AIDIY_VIDEO_GEN_TEMPLATE_DIR`: コピー元テンプレート。
- `AIDIY_VIDEO_GEN_START_STEP`: 再開するステップ番号（`00`, `01`〜`07`, `99`）。
- `AIDIY_VIDEO_GEN_STOP_STEP`: 検証時に停止するステップ番号（1ステップずつ実行するときに使う）。
- `AIDIY_VIDEO_GEN_TTS`: `0` で音声案内を無効化。
- `AIDIY_VIDEO_GEN_BROWSER`: `0` で Chrome 再描写を無効化。
- `AIDIY_VIDEO_GEN_FRONTEND_URL`: 表示に使う frontend_web のベース URL。

`__main__` では、設定読み込み、流れの表示、CodeAgents 初期化、各ステップ実行の順に大枠を追える構成にしています。

ステップ番号は他の自動化にも流用しやすいように、以下の規則にしています。

- `00`: 最初に確認すること（設定、API、テンプレート、AI 利用可否）。
- `01`〜`nn`: 各ステップの実行と検証。
- `99`: 最後の処理、完了判定、完了ファイル作成。

`01`〜`99` の各ステップ完了後は、`aidiy_chrome_devtools` と同じ CDP 実装で
`<frontend>/Xビデオ/<フォルダ名>/index.html?auto=loop` を表示し直します。
