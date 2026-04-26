# Code CLI 追加手順

## このメモを使う場面
- `codex_cli` のような code CLI を新規追加するとき
- backend だけ直しても UI に出ない問題を避けたいとき
- 追加対象 CLI の実行方法が OS 依存かどうかを整理したいとき

## 先に押さえる結論
- 新しい CLI 追加は、backend 実行ランタイム、モデル定義、設定JSON、frontend 設定UIを一式で揃える
- frontend 側だけ、または backend 側だけの片側修正では完成しない
- 起動中サーバーへは自動反映されないため、必要に応じて再起動を行う

## 変更が必要な場所

### 1. backend の CLI 実行処理
対象:
- `backend_server/AIコア/AIコード_cli.py`

対応内容:
- `_コマンドパス取得()` に新CLI名を追加する
- `バージョン確認()` に `--version` 相当の確認処理を追加する
- `_コマンド構築()` に新規会話・継続会話のコマンド生成を追加する
- OS依存の起動条件がある場合は分岐を追加する

### 2. CodeAgent 側の文言
対象:
- `backend_server/AIコア/AIコード.py`

対応内容:
- welcome 文言へ新CLI名を追加する
- 未インストール時の案内へ新CLI名を追加する
- 必要なら説明文や候補一覧も更新する

### 3. モデル定義
対象:
- `backend_server/conf/conf_model.py`

対応内容:
- `CODE_<CLI名>_MODELS` を追加する
- `_sync_local_model_configs()` に `AiDiy_code_<cli名>.json` を追加する
- `get_code_models()` の返却対象へ新CLIを追加する

### 4. 設定JSON
対象:
- `backend_server/conf/conf_json.py`
- `backend_server/_config/AiDiy_key.json`
- `backend_server/_config/AiDiy_code_<cli名>.json`

対応内容:
- `conf_json.DEFAULT_CONFIG` に `CODE_<CLI名>_MODEL` を追加する
- `AiDiy_key.json` に同じキーを追加する
- `AiDiy_code_<cli名>.json` を作成し、最低でも `auto` を定義する

### 5. frontend の設定UI
対象:
- `frontend_web/src/components/AiDiy/dialog/AI設定再起動.vue`
- `frontend_avatar/src/dialog/AI設定再起動.vue`

対応内容:
- `CODE_MODEL_KEYS` に新CLI用キーを追加する
- `availableModels.code_models` に新CLIが来たとき選択肢へ表示されることを確認する

### 6. frontend_avatar の表示・接続連動
対象:
- `frontend_avatar/src/AiDiy.vue`
- `frontend_avatar/src/components/AIコード.vue`
- `frontend_avatar/src/dialog/AI設定再起動.vue`

対応内容:
- `CODE_AI1_NAME`〜`CODE_AI4_NAME` は `PANEL_TITLES` の表示名にも使われるため、設定変更後に code1〜code4 のウィンドウタイトルが更新されるか確認する
- Web モードでは code1〜code4 は別ウィンドウではなくタブなので、`webTabs` と `PANEL_KEYS` は CLI 種別ではなくパネル数を表す。新CLI追加だけなら増やさない
- 各 `AIコード.vue` は `チャンネル`（code1〜code4）単位で WebSocket 接続する。CLI 名をチャンネル名として増やす設計にしない

## 実装時の注意点
- backend の `available_models.code_models` に出ない限り、frontend へ項目を足しても選択できない
- 設定JSONを追加しても、モデル定義や UI 側のキー追加が漏れると画面で扱えない
- `CODE_AI*_NAME` の値は `claude_sdk` / `codex_cli` のような AI 種別名。`CODE_AI*_MODEL` はそのスロットで使うモデル名。追加時にこの 2 つを取り違えない
- 設定 UI の選択肢は backend の `available_models.code_models` から作られるため、frontend に固定 option を直書きしない
- Windows で WSL 経由実行が必要な CLI は、作業ディレクトリとパス形式の差異を吸収する必要がある

## Hermes を追加したときの再利用知見
- `bash -i -c` は初期化で停止する場合があるため、`bash -lc` を優先する
- WSL 起動時に作業ディレクトリが自動で一致する前提にしない
- 絶対パスは `X:/...` ではなく `/mnt/x/...` へ変換して渡す
- Windows 上の AI へも、CLI 実行環境が WSL 側であることを明示する

## 最低限の確認項目
- AI設定再起動ダイアログで新CLIを選択できる
- frontend_avatar の Electron 設定ウィンドウと Web 設定モーダルの両方で新CLIを選択できる
- `AiDiy_key.json` に新CLI用キーがある
- `_config/AiDiy_code_<cli名>.json` がある
- バージョン確認が通る
- 新規会話コマンドが組める
- 継続会話コマンドが組める
- code1〜code4 のどのスロットに割り当てても、WebSocket チャンネルは `code1`〜`code4` のまま動く
- OS依存条件がある場合、その環境で実行確認できる

新しい CLI を追加したら、Hermes セクションと同じ観点（OS 依存の起動方法、パス変換、モデル選択の差異）をこのファイルの末尾に追記する。
