# Code CLI 追加手順

## このメモを使う場面
- `codex_cli` や `aidiy_hermes` のような Code CLI を追加する
- backend には追加したが設定 UI に出ない問題を避ける
- CLI 名、モデルキー、Code AI 6枠の関係を確認する

## 基本方針
- 新しい CLI は backend 実行処理、モデル定義、設定 JSON、frontend 設定 UI を一式で揃える
- `CODE_AI1_NAME`〜`CODE_AI6_NAME` は「どのスロットでどの CLI 種別を使うか」を表す
- `CODE_AI1_MODEL`〜`CODE_AI6_MODEL` は「そのスロットで使うモデル」を表す
- `CODE_<CLI名>_MODEL` のようなキーは CLI 種別ごとのデフォルトや候補管理に使う。スロットキーと混同しない
- Code AI パネルは現行 `code1`〜`code6`。新CLI追加だけならパネル数は増やさない

## 関連ファイル

### backend_server
- `backend_server/core_router/AIコア/AIコード_cli.py`
- `backend_server/core_router/AIコア/AIコード.py`
- `backend_server/conf/conf_model.py`
- `backend_server/conf/conf_json.py`
- `backend_server/_config/AiDiy_key.json`
- `backend_server/_config/AiDiy_code_<cli名>.json`（固定モデル一覧を持つ場合）

### frontend
- `frontend_web/src/components/AiDiy/dialog/AI設定再起動.vue`
- `frontend_avatar/src/dialog/AI設定再起動.vue`
- `frontend_avatar/src/AiDiy.vue`
- `frontend_avatar/src/components/AIコード.vue`

## 追加手順

1. `AIコード_cli.py` の `_コマンドパス取得()` に CLI 名を追加する
2. `バージョン確認()` に確認コマンドと timeout を追加する
3. `_コマンド構築()` に初回会話と継続会話のコマンド生成を追加する
4. OS 依存の起動条件やパス変換が必要なら同ファイル内で分岐する
5. `AIコード.py` の welcome 文言、候補一覧、未インストール案内を更新する
6. `conf_model.py` に `CODE_<CLI名>_MODELS` または動的生成ロジックを追加し、`get_code_models()` の返却対象へ入れる
7. 固定モデル一覧を持つ場合は `_config/AiDiy_code_<cli名>.json` を作り、最低でも `auto` を定義する
8. `conf_json.DEFAULT_CONFIG` と `AiDiy_key.json` に必要な `CODE_<CLI名>_MODEL` を追加する
9. frontend の `CODE_MODEL_KEYS` に CLI 名と保存キーの対応を追加する
10. 設定 UI で `availableModels.code_models` から新CLIが選べることを確認する

## Hermes 統合時の判断基準

- 公開名は frontend / backend / 設定 JSON で完全一致させる。現行値は `aidiy_hermes`
- CLI ごとに専用 `AiDiy_code_*.json` が必須とは限らない。`aidiy_hermes` のように既存モデル一覧を流用してもよい
- `_setup.py` / `_cleanup.py` に統合しても、常駐起動が不要な CLI は `_start.py` に追加しない
- `aidiy_hermes --version` は cold start や `code1`〜`code6` 同時接続で遅くなることがある。未インストール誤判定を避けるため、長めの timeout と結果キャッシュを検討する

## 注意点

- backend の `available_models.code_models` に出ない限り、frontend に項目を足しても選択できない
- frontend の設定 option は backend 返却値から生成し、CLI 名を固定直書きしない
- `code1`〜`code6` は WebSocket チャンネル/パネル名。CLI 名をチャンネル名として増やさない
- Windows で WSL 経由実行が必要な CLI は、作業ディレクトリとパス形式の差異を吸収する
- 設定変更は起動中サーバーへ自動反映されない。必要に応じて core server を再起動する

## 確認方法

- `AiDiy_key.json` に新CLI用の設定キーがある
- 固定モデル方式なら `_config/AiDiy_code_<cli名>.json` がある
- `/core/AIコア/モデル情報/取得` の `available_models.code_models` に新CLIが出る
- Web / Avatar の設定ダイアログで新CLIを選択できる
- バージョン確認、新規会話、継続会話のコマンドが組める
- `code1`〜`code6` のどのスロットに割り当てても WebSocket チャンネルは `code1`〜`code6` のまま動く

```powershell
backend_server\.venv\Scripts\python.exe -m py_compile backend_server\core_router\AIコア\AIコード_cli.py
backend_server\.venv\Scripts\python.exe -m py_compile backend_server\conf\conf_model.py
cd frontend_avatar
npm run type-check
cd ..\frontend_web
npm run type-check
```
