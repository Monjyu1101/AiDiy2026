# 設定管理 (conf/)

> 文書: `backend_server,設定管理(conf).md` | 実装: `backend_server/conf/conf_json.py`, `backend_server/conf/conf_model.py`, `backend_server/conf/conf_path.py`

## このメモを使う場面

- `AiDiy_key.json` のキー構成やデフォルト値を変更するとき
- AI モデル一覧の取得ロジック（provider 別）を変更するとき
- 設定ファイルの保存先パスや外部プロジェクト探索を変更するとき
- 新しい設定キーを追加するとき

## アーキテクチャ

`backend_server/conf/` は 3 つのクラスで構成されます。

```
conf_path      → パス解決（実行パス、外部プロジェクト探索）
conf_json      → JSON 設定ファイル管理（ロード/保存/補完）
conf_models    → AI モデル一覧管理（provider API 取得/キャッシュ）
```

## conf_path — パス解決

```python
from conf.conf_path import conf_path
conf_path.init()  # 起動時に1度だけ呼ぶ

conf_path.exec_abs_path      # backend_server/ の絶対パス
conf_path.exec_abs_root      # プロジェクトルート（1階層上）
conf_path.external_root_path # 外部プロジェクト（2階層上、エイリアスリンク用）
```

`init()` は `__file__` から実行パスを解決し、末尾 `/` 付きの絶対パス（フォワードスラッシュ）に正規化します。

`_discover_agents_projects()` は `external_root_path` 以下で `_AIDIY.md` を持つフォルダを探索し、`{フォルダ名: 絶対パス}` の辞書を構築します。

## conf_json — JSON 設定管理

```python
from conf.conf_json import conf_json

config = conf_json(filepath="backend_server/_config/AiDiy_key.json")
value = config.SOME_KEY   # __getattr__ でアクセス
config.SOME_KEY = "value" # __setattr__ → 即座に _save()
```

### 主要動作

| メソッド | 動作 |
|---------|------|
| `__getattr__` | `_config_data[SOME_KEY]` を返す。`:cloud` サフィックスを自動除去 |
| `__setattr__` | `_config_data` に書き込んだ後 `_save()` を呼ぶ（即時保存） |
| `_apply_default_keys()` | `DEFAULT_CONFIG` に無いキーをデフォルト値で補完。キー順序も DEFAULT_CONFIG に合わせる |
| `_save()` | JSON をファイルに書き出し |
| `get(key, default)` | dict 形式フォールバック |
| `update(dict)` | 複数キーを一括更新 |

### DEFAULT_CONFIG のキー構成

| カテゴリ | 主なキー |
|---------|---------|
| サービス / WebUI | `WEB_BASE`, `CORE_BASE`, `AVATAR_BASE`, `TASK_BASE`, `TEAM_BASE`, `LOCAL_BASE`, `TOOLS_BASE`, `APPS_BASE`, `WEBUI_FIRST_PAGE` |
| API Key | `gemini_key_id`, `freeai_key_id`, `claude_key_id`, `openai_key_id`, `copilot_key_id`, `openrt_key_id`, `ollama_key_id` |
| OpenAI/Azure | `openai_api_type`, `openai_organization`, `azure_endpoint`, `azure_version`, `azure_key_id` |
| Ollama | `ollama_host` |
| ChatAI | `CHAT_AI_NAME`, `CHAT_GEMINI_MODEL`, `CHAT_FREEAI_MODEL`, `CHAT_OPENRT_MODEL`, `CHAT_OLLAMA_MODEL` |
| LiveAI | `LIVE_AI_NAME`, `LIVE_GEMINI_MODEL/VOICE`, `LIVE_FREEAI_MODEL/VOICE`, `LIVE_OPENAI_MODEL/VOICE` |
| CodeAI | `CODE_BASE_PATH`, `CODE_AI1~6_NAME/MODEL`, `CODE_CLAUDE_SDK_MODEL`, `CODE_MAX_TURNS`, `CODE_PLAN`, `CODE_VERIFY` |

### `:cloud` サフィックス自動除去

`CHAT_OLLAMA_MODEL` または `OLLAMA_MODEL` の値に `:cloud` が含まれる場合、`ollama_key_id` が有効（プレースホルダーでない）なら `:cloud` を除去して返します。これにより設定ファイルの値は変えずに、Ollama Cloud とローカル Ollama を切り替えられます。

### 新しいキー追加手順

1. `conf_json.py` の `DEFAULT_CONFIG` にキーとデフォルト値を追加
2. `_normalize_ollama_cloud_model_value()` に特殊処理が必要なら追記
3. `_save()` で自動保存される

## conf_models — AI モデル一覧管理

```python
from conf.conf_model import conf_models
models = conf_models(conf=config)
models.fetch_all_models()  # 起動時に1度呼ぶ
```

### モデル一覧の取得元

| プロバイダ | 取得方法 | 保存ファイル |
|-----------|---------|-------------|
| Google Gemini | SDK `genai.list_models()` | `AiDiy_live_gemini.json` など |
| OpenAI | SDK | `AiDiy_live_openai.json` など |
| Anthropic Claude | SDK | `AiDiy_code_claude_sdk.json` など |
| OpenRouter | REST API | モデルメタデータを補充 |
| Ollama | `ollama list` CLI / Ollama Cloud REST API | ローカルモデル一覧 |

### データフロー

1. `_sync_local_model_configs()` で JSON ファイル群を読み込み/作成
2. `fetch_all_models()` で全 provider のモデルリストを取得
3. 各 provider のモデルは recency フィルタ（3〜12ヶ月）と OpenRouter データのクロスリファレンスで拡充
4. `get_chat_models()`, `get_live_models()`, `get_live_voices()`, `get_code_models()` で UI に公開

### ハードコードドデフォルト

`fetch_all_models()` 未実行の場合のフォールバックとして、主要な live-AI モデル/音声と code-AI モデルのハードコードド辞書が用意されています。

## 設定ファイル一覧

| ファイル | 管理対象 |
|---------|---------|
| `_config/AiDiy_key.json` | 全設定キー（conf_json 管理） |
| `_config/AiDiy_chat__context.json` | チャットコンテキスト |
| `_config/AiDiy_live__context.json` | ライブ音声コンテキスト |
| `_config/AiDiy_code__context.json` | コード AI コンテキスト |
| `_config/AiDiy_mcp.json` | MCP 設定 |
| `_config/AiDiy_live_*.json` | 各プロバイダの live-AI モデル/音声一覧 |
| `_config/AiDiy_code_*.json` | 各プロバイダの code-AI モデル一覧 |

## 注意点

- **conf_json の即時保存**: `obj.key = value` で即座に JSON ファイルへ書き込まれる。バッチ更新は `update()` を使うこと
- **conf_models の起動順序**: `conf_json` が先に初期化されている必要がある（API キー参照のため）
- **conf_path の init**: `conf_path.init()` は起動時に1度だけ呼ぶ。複数回呼ぶとパスがズレる
- **外部プロジェクト探索**: `_AIDIY.md` の有無で判定。新しい外部エージェントを追加したらこのファイルを配置する
