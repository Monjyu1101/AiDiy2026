# 設定管理 (conf/)

> 文書: `backend_server,設定管理(conf).md` | 実装: `backend_server/conf/conf_json.py`, `backend_server/conf/conf_model.py`, `backend_server/conf/conf_path.py`

## このメモを使う場面

- `AiDiy_key.json` のキー構成やデフォルト値を変更するとき
- AI モデル一覧の取得ロジック（provider 別）を変更するとき
- 設定ファイルの保存先パスや外部プロジェクト探索を変更するとき
- 新しい設定キーを追加するとき

コードモデル一覧の `auto` / `same` は実行方法の選択肢なので合成JSONには含めません。`conf_models.get_code_models()` が画面用一覧の先頭に追加します。モデル一覧取得時には設定ファイルを変更せず、実モデルの表示名は合成JSONの値を維持します。

## アーキテクチャ

`backend_server/conf/` は 3 つのクラスで構成されます。

```
conf_path      → パス解決（実行パス、外部プロジェクト探索）
conf_json      → JSON 設定ファイル管理（ロード/保存/補完）
conf_models    → aidiy_diag のモデル・音声合成JSON読込、初期値補正、MCP設定読込
```

## conf_path — パス解決

```python
from conf.conf_path import conf_path
paths = conf_path()
paths.init()  # 起動時に1度だけ呼ぶ

paths.exec_abs_path      # backend_server/ の絶対パス
paths.exec_abs_root      # プロジェクトルート（1階層上）
paths.external_root_path # 外部プロジェクト（2階層上、エイリアスリンク用）
paths.config_path        # プロジェクトルートの _config/
paths.data_path          # プロジェクトルートの _data/
paths.database_path      # _data/AiDiy/database.db
paths.icons_path         # プロジェクトルートの _icons/
```

`init()` は `__file__` から実行パスを解決し、フォワードスラッシュの絶対パスに正規化します。ディレクトリには末尾 `/` を付け、DB ファイルの `database_path` には付けません。

共有ディレクトリの相対デフォルトは `backend_server/` 基準で、`../_config`、`../_data`、`../_data/AiDiy/database.db`、`../_icons` です。コードでは `DEFAULT_CONFIG_DIR`、`DEFAULT_DATA_DIR`、`DEFAULT_DATABASE_PATH`、`DEFAULT_ICONS_DIR` を参照し、同じパス文字列を個別に重複定義しないようにします。

`_discover_agents_projects()` は `external_root_path` の直下と、その1階層下で `_AIDIY.md` を持つフォルダを探索し、`{フォルダ名: 絶対パス}` の辞書を構築します。

## conf_json — JSON 設定管理

```python
from conf.conf_json import conf_json

config = conf_json()      # 既定: ../_config/AiDiy_key.json（backend_server/ 基準）
value = config.SOME_KEY   # __getattr__ でアクセス
config.SOME_KEY = "value" # __setattr__ → 即座に _save()
```

### 主要動作

| メソッド | 動作 |
|---------|------|
| `__getattr__` | `_config_data[SOME_KEY]` を返す。Ollama の `:cloud` 値もそのまま維持 |
| `__setattr__` | `set()` 経由で検証し、保存成功後にメモリへ反映（即時保存） |
| `_migrate_port_keys()` | 旧ポートキーを現行の `PORT_*` へ移行し、Task / Team を `PORT_TASKTEAM` に統合 |
| `_apply_default_keys()` | 不足キーをデフォルト値で補完。キー順序も `DEFAULT_CONFIG` に合わせる |
| `_save()` | 同じフォルダの一時ファイルへ書き、`os.replace()` で原子的に置換 |
| `get(key, default)` | dict 形式フォールバック |
| `update(dict)` | 複数キーを一括検証し、保存成功後にまとめて反映 |

既存の旧ポートキーは読み込み時に自動移行する。`TASK_BASE` と `TEAM_BASE` が異なる場合は `TASK_BASE` を優先する。現行キーと旧キーが同時にある場合は現行キーを優先する。ポート値は `1`～`65535` の文字列へ正規化し、不正な JSON や不正なポート値は元ファイルを上書きせず初期化を失敗させる。

### DEFAULT_CONFIG のキー構成

| カテゴリ | 主なキー |
|---------|---------|
| サービス / WebUI | `PORT_WEB`, `PORT_CORE`, `PORT_AVATAR`, `PORT_TASKTEAM`, `PORT_TOOLS`, `PORT_LOCAL`, `PORT_APPS`, `WEBUI_FIRST_PAGE` |
| Discord | `DISCORD_BOT_TOKEN`, `DISCORD_GUILD_ID`, `DISCORD_ALLOWED_USER_ID`, `DISCORD_TEXT_CHANNEL_ID`, `DISCORD_VOICE_CHANNEL_ID` の接続情報5項目。ID は単一文字列。旧 `*_IDS` の1件配列は自動移行。Live / Code は共通設定を使用（詳細は `frontend_channels/README.md`） |
| API Key | `gemini_key_id`, `freeai_key_id`, `claude_key_id`, `openai_key_id`, `copilot_key_id`, `openrt_key_id`, `ollama_key_id` |
| OpenAI/Azure | `openai_api_type`, `openai_organization`, `azure_endpoint`, `azure_version`, `azure_key_id` |
| Ollama | `ollama_host` |
| ChatAI | `CHAT_AI_NAME`, `CHAT_GEMINI_MODEL`, `CHAT_FREEAI_MODEL`, `CHAT_OPENRT_MODEL`, `CHAT_OPENAI_MODEL`, `CHAT_OLLAMA_MODEL`, `CHAT_LOCAL_MODEL` |
| DecisionAI | LIVE設定ブロックの直後に `DECISION_AI_NAME`, `DECISION_AI_MODEL`（初期値はともに `auto`）。方式別の予備設定は `DECISION_OPENAI_MODEL`, `DECISION_OAUTH_MODEL`, `DECISION_FREEAI_MODEL`, `DECISION_GEMINI_MODEL`（[AI判断](./backend_server,backend_tools,AI判断追加手順.md)） |
| LiveAI | `LIVE_AI_NAME`, `LIVE_GEMINI_MODEL/VOICE`, `LIVE_FREEAI_MODEL/VOICE`, `LIVE_OPENAI_MODEL/VOICE` |
| CodeAI | `CODE_BASE_PATH`, `CODE_AI1~6_NAME/MODEL`, `CODE_CLAUDE_SDK_MODEL`, `CODE_MAX_TURNS`, `CODE_PLAN`, `CODE_VERIFY` |
| TaskAI / TeamAI | `TASK_AI_NAME`, `TEAM_AI_NAME`, `TASK_AI_MODEL_plan/do/check`, `TEAM_AI_MODEL_plan/do/check`（各フェーズを別キーで保持） |

### `:cloud` サフィックスの扱い

`CHAT_OLLAMA_MODEL` または `OLLAMA_MODEL` の `:cloud` サフィックスは除去しない。ローカル Ollama daemon が cloud ルーティングを処理するため、設定ファイルと取得値を同じ値に保つ。

### 新しいキー追加手順

1. `conf_json.py` の `DEFAULT_CONFIG` にキーとデフォルト値を追加
2. `_normalize_ollama_cloud_model_value()` に特殊処理が必要なら追記
3. `_save()` で自動保存される

## conf_models — AI モデル一覧管理

```python
from conf.conf_model import conf_models
models = conf_models(conf=config)
models.fetch_all_models()  # 互換入口。合成ファイルの読込確認のみ
```

### モデル一覧の取得元

`_AIDIY/aidiy_diag/chat_models_info.json`、`live_models_info.json`、`code_models_info.json` だけを使います。各ファイルは `{区分名: {"models": {モデルID: 表示名}}}` 形式です。取得・絞り込み・重複統合・表示順は `aidiy_diag` が担当します。

### データフロー

1. ルート `_start.py` が必ず `aidiy_diag --headless` の完了を待ち、合成JSONを生成します。
2. `get_chat_models()`、`get_live_models()`、`get_code_models()` は呼出時に合成JSONを読み、モデル情報APIへ公開します。Coreから外部APIやモデル取得CLIは呼びません。
3. 新規セッションとモデル情報APIの共通初期値は `normalize_initial_settings()` で候補に合わせます。有効な既定値と `auto` / `same` は維持し、候補外の値は先頭の有効な候補に補正します。共通設定への書き戻しは行いません。
4. Code / Live はAPI経由、オフラインCodeとDiscordは同じ合成JSONを直接読みます。最後の手動選択は各クライアントの専用ファイルに保持します。

### ファイルがない・読み込めない場合

モデル候補は空になり、ログに `aidiy_diag --headless` の実行を案内します。旧 `_config` のモデル一覧・bat・固定モデルへのフォールバックはしません。修復後は次の一覧取得から反映します。読込・初期値・書込なしの確認は `python -m unittest discover -s tests -p test_diag_model_catalog.py` で行います。

### 音声とMCP

声は `_AIDIY/aidiy_diag/live_voices_info.json` の `{区分: {voices: {音声ID: 表示名}}}` を読みます。区分は `gemini_live` / `freeai_live` / `openai_live` です。固定定義は `backend_diag/モデル情報/voices_info.mjs` で管理し、キー確認成功・現在設定済みのプロバイダだけを出力します。Python側に音声定義や旧設定への代替読込はありません。MCPは従来の設定を読みます。`conf_models` は設定ファイルを作成・更新しません。

## 設定ファイル一覧

| ファイル | 管理対象 |
|---------|---------|
| `_config/AiDiy_key.json` | 全設定キー（conf_json 管理） |
| `_config/AiDiy_chat__context.json` | チャットコンテキスト |
| `_config/AiDiy_live__context.json` | ライブ音声コンテキスト |
| `_config/AiDiy_code__context.json` | コード AI コンテキスト |
| `_config/AiDiy_mcp.json` | MCP 設定 |
| `_AIDIY/aidiy_diag/*_models_info.json` | モデル詳細・合成一覧（aidiy_diagが生成） |
| `_AIDIY/aidiy_diag/live_voices_info.json` | 有効キーに対応した固定音声候補（aidiy_diagが生成） |
| `_config/AiDiy_live_gemini.json` / `AiDiy_live_openai.json` | 廃止済み。作成・参照・更新しない |
| `_config/AiDiy_code_*.json` / `AiDiy_chat_local.json` | 廃止済み。作成・参照・更新しない |

## 注意点

- **conf_json の即時保存**: `obj.key = value` で即座に JSON ファイルへ書き込まれる。バッチ更新は `update()` を使うこと
- **conf_models の生成元**: 合成JSONを先に `aidiy_diag --headless` で生成する。Core側の読込ではAPIキーを参照しない
- **conf_path の init**: `conf_path.init()` は `__file__` 基準でパスを再計算する。繰り返し呼んでも階層はズレず、外部プロジェクト一覧も再探索する
- **外部プロジェクト探索**: `_AIDIY.md` の有無で判定。新しい外部エージェントを追加したらこのファイルを配置する
