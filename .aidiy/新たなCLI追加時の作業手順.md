# 新たなCLI追加時の作業手順

このメモは、AiDiy2026 に新しい code CLI を追加する時の標準手順です。
`hermes_cli` 追加時の実装を元にしています。

## 対応が必要な場所

### 1. 実行ランタイムの追加
対象:
- `backend_server/AIコア/AIコード_cli.py`

実施内容:
- `_コマンドパス取得()` に新CLI名を追加
- `バージョン確認()` に新CLIの `--version` 実行方法を追加
- `_コマンド構築()` に以下を追加
  - 新規会話コマンド
  - 継続会話コマンド
  - 必要ならモデル指定
- Windows 固有事情がある場合は Windows 分岐を追加する

例: `hermes_cli`
- Windows: `wsl bash -i -c "hermes --version"`
- 新規: `hermes chat --yolo -Q -q "..."`
- 継続: `hermes chat --continue --yolo -Q -q "..."`

### 2. CodeAgent 側メッセージ対応
対象:
- `backend_server/AIコア/AIコード.py`

実施内容:
- welcome 文言に新CLI名を追加
- 未インストール時メッセージに新CLI名を追加
- 必要なら説明文も追加

### 3. モデル定義の追加
対象:
- `backend_server/conf/conf_model.py`

実施内容:
- `CODE_<CLI名>_MODELS` を追加
- `_sync_local_model_configs()` に `AiDiy_code_<cli名>.json` を追加
- `get_code_models()` に新CLIを追加

### 4. 設定JSONの追加
対象:
- `backend_server/conf/conf_json.py`
- `backend_server/_config/AiDiy_key.json`
- `backend_server/_config/AiDiy_code_<cli名>.json`

実施内容:
- `conf_json.DEFAULT_CONFIG` に `CODE_<CLI名>_MODEL` を追加
- `AiDiy_key.json` に同じキーを追加
- `AiDiy_code_<cli名>.json` を作成し、最低でも `auto` を定義

### 5. 設定UI対応
対象:
- `frontend_web/src/components/AiDiy/dialog/AI設定再起動.vue`
- `frontend_avatar/src/dialog/AI設定再起動.vue`

実施内容:
- `CODE_MODEL_KEYS` に新CLIのキーを追加
- `availableModels.code_models` に新CLIが来た時に表示・選択できることを確認

## 確認チェックリスト
- AI設定再起動ダイアログで新CLIが選べる
- `AiDiy_key.json` に新CLI用キーがある
- `_config/AiDiy_code_<cli名>.json` がある
- バージョン確認が通る
- 新規会話コマンドが組める
- 継続会話コマンドが組める
- Windows 固有条件があればその分岐が入っている

## 注意
- frontend 側だけ直しても選択肢は出ない
- backend 側の `available_models.code_models` に出るところまで揃って初めて UI に表示される
- 既に起動中の backend には変更が反映されないため、必要に応じて再起動が必要
