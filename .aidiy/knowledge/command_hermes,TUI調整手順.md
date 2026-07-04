# Hermes CLI TUI 調整手順

> 文書: `command_hermes,TUI調整手順.md` | 実装: `command_hermes/cli_main.py`, `command_hermes/hermes_cli/commands.py`

## このメモを使う場面
- `command_hermes/cli_main.py` の TUI、起動バナー、slash command を調整する
- `/` 補完、`/new`、`/model`、spinner、色表示の挙動を確認する
- 旧 Hermes Agent 由来の機能を AiDiy Hermes に移植するか判断する
- upstream (Nous Research hermes-agent) からの調整点を確認する

## 関連ファイル
- `command_hermes/cli_main.py` — CLI/TUI エントリ
- `command_hermes/hermes_cli/commands.py` — `COMMAND_REGISTRY` と補完
- `command_hermes_old/cli_main.py` — 旧 AiDiy Hermes 実装の参照元
- `command_hermes/base/toolsets.py` — toolset 定義
- `command_hermes/base/model_tools.py` — agent loop tool 定義
- `command_hermes/tools/` — 各ツール実装
- `command_hermes/AGENTS.md` — Hermes 実装方針
- `backend_server/_config/AiDiy_key.json` — AiDiy provider/モデル設定
- `backend_server/_config/AiDiy_mcp.json` — AiDiy MCP サーバー定義

## Upstream からの調整点

この `command_hermes` は [Nous Research の hermes-agent](https://github.com/nousresearch/hermes-agent) v0.12.0 (MIT License) をフォークし、AiDiy 用に以下の調整を加えています。

オリジナルとの実差分は、6つのサブエージェントによる並行比較（`diff` + ファイル単位の調査）で確認済みです。

### 全体構造の変更

| 項目 | upstream | AiDiy |
|------|----------|-------|
| CLI エントリ | `cli.py` (12,275行) | `cli_main.py` (12,714行) — `argparse` + `cli_entry()` 追加 |
| パッケージ名 | `agent/` ディレクトリ | `core/` にリネーム。`sys.modules["agent"] = core` 互換alias |
| ルートスクリプト群 | 14ファイルがルート直置き | `base/` ディレクトリに移動（内容は同一） |
| 依存管理 | `pyproject.toml` (extras多数) | `pyproject.toml` (必要最小限の dependencies) |
| `run_agent.py` | ルート | `base/run_agent.py` (内容はupstreamと同一) |

### 削除されたディレクトリ/ファイル

| 対象 | 規模 | 理由 |
|------|------|------|
| `cron/` | Node.js フルプロジェクト | 定期実行はAiDiy不要 |
| `web/` | Vue 3 SPA (214KB lock) | AiDiy独自の `frontend_web` が別管理 |
| `website/` | Docusaurus サイト (777KB lock) | ドキュメントはプロジェクトルートの `docs/` で管理 |
| `ui-tui/` | Rust TUI (263KB) | Python `prompt_toolkit` TUIに置換 |
| `tui_gateway/` | TUI gateway | Python TUI化に伴い削除 |
| `acp_adapter/`, `acp_registry/` | ACP プロトコル (108KB) | 不要なプロトコルアダプタ |
| `gateway/` | 50+ファイル (全platform) | `__init__.py` + `session_context.py` のみの互換スタブに縮退 |
| `docs/`, `tests/`, `scripts/`, `packaging/`, `nix/`, `docker/` | 全ファイル | プロジェクトルートで一元管理 |
| `pyproject.toml`, `uv.lock` | ビルド設定 | `pyproject.toml` を AiDiy 用に維持。`uv.lock` は固定せず再生成対象 |
| `cli-config.yaml.example` | 55KBの設定例 | AiDiy_key.json方式のため不要 |
| `setup-hermes.sh`, `hermes` | シェルランチャ | Windows `.cmd` ラッパーで代替 |
| `cli.py` → `cli_main.py` | リネーム + 大幅改変 | AiDiy provider/oneshot 統合 |

### `cli_main.py` (upstream `cli.py`) の改変点

| 改変 | 説明 |
|------|------|
| `cli_entry()` 追加 (L12662) | `argparse` 駆動のconsole scriptエントリ。戻り値int |
| `_load_aidiy_hermes_defaults()` (L12609) | `AiDiy_key.json` から provider/model 既定値を動的読込 |
| `_resolve_aidiy_ollama_model()` (L12633) | 起動中のOllamaに `GET /api/tags` してモデル名解決 |
| `_aidiy_provider_slugs()` / `_handle_aidiy_model_command()` (L5655-5925) | `/model` コマンドをAiDiy provider pickerに置換 |
| 6 provider: ollama(local+cloud), openai, openrt, gemini/freeai, anthropic | すべて `AiDiy_key.json` で管理 |
| quiet/oneshot 出力分離 (L12485-12543) | 運用出力をstderrにredirect、stdout=正式回答に固定 |
| cron import fallback (L685-690) | `cron` 欠落時は `get_job` を None返却で代替 |

### `core/` 内の改変ファイル (upstream `agent/` 由来)

| ファイル | 変更内容 |
|---------|---------|
| `display.py` | 日本語待機メッセージ `_static_wait_message()` 追加。1ショット静的な spinner モード追加 |
| `curator.py` | `_strip_aux_credential()` / `_ReviewRuntimeBinding` 削除。初回実行ロジック簡略化 |
| `credential_pool.py` | `_get_env_prefer_dotenv()` 削除。env 読込を `get_env_value()` に統一 |
| `context_compressor.py` | `_summary_failure_cooldown_until` 削除。prune境界計算簡略化。タイムアウト条件から timeout を除外 |
| `prompt_builder.py` | Kanban プロンプト文言変更。`api_server` プラットフォーム用SYSTEM_PROMPT削除 |
| `error_classifier.py` | llama.cpp GBNF grammar fallback (`llama_cpp_grammar_pattern`) 削除。閾値判定簡略化 |
| `curator_backup.py` | **削除** |
| `think_scrubber.py` | **削除** |

### `tools/` 内の改変ファイル

| ファイル | 変更内容 |
|---------|---------|
| `mcp_tool.py` | **大規模改変**: `_is_sse()`, `_run_sse()`, `_load_aidiy_mcp_servers()` 追加。`get_mcp_servers_config()` にAiDiy_mcp.jsonマージ。keepalive削除。transport表示にSSE追加 |
| `vision_tools.py` | 動画解析ツールセクション全体 (lines 805-1167) 削除 |
| `file_operations.py` | ターミナルfence漏れ除去 (`_strip_terminal_fence_leaks()`) 削除。`lint` field削除 |
| `file_tools.py` | `redact_sensitive_text` 引数変更。シンタックスチェック説明削除。write validation簡略化 |
| `approval.py` | 危険パターンから `_SHELL_RC_FILES` / `_CREDENTIAL_FILES` 削除 |
| `delegate_tool.py` | heartbeat間隔短縮 (15→5, 40→20)。fallback chain継承削除。provider filter継承簡略化 |
| `schema_sanitizer.py` | llama.cpp 用 `strip_pattern_and_format()` リアクティブサニタイザ削除 |
| `cronjob_tools.py` | `no_agent` サポート削除。`custom` provider fallback削除 |
| `send_message_tool.py` | Feishu メディア添付サポート削除。QQ Bot 説明簡略化 |
| `skill_manager_tool.py` | pin guard を削除防止→全変更防止に強化 |
| `session_search_tool.py` | "auxiliary model" 参照を "Gemini Flash" / 汎用表現に置換 |
| `tts_tool.py` | MiniMax API v2 対応 (endpoint, voice_id, speed/vol/pitch) |
| `skill_provenance.py` | **削除** |

### `hermes_cli/` 内の改変

| ファイル | 変更内容 |
|---------|---------|
| `setup.py` | **削除** (プロジェクトルートの `_setup.py` に統一) |
| `main.py` | パス注入ブロック追加 (L86-103)。Node TUI→Python `cli_main` 呼び出しにルーティング変更 |
| `_parser.py` | `--dev` フラグのhelp文言をAiDiy用に変更 (「AiDiy Python TUI buildでは無効」) |

### 追加されたファイル (upstreamにないもの)

| ファイル | 目的 |
|---------|------|
| `NOTICE.md` | MITライセンス帰属表示 |
| `AGENTS.md` | AiDiy command_hermes 実装概要・HowTo参照マップ |
| `pyproject.toml` | 依存パッケージ一覧 |
| `AIDIY-HERMESロゴ.txt` | ASCII art ブランドロゴ |
| `tui画面出す.bat` | Windows TUI 起動バッチ |

### 変更なし (upstream と完全同一) のディレクトリ

以下のディレクトリは内容に変更がありません:
- `environments/` — 全ファイル同一 (benchmarks含む)
- `tools/browser_providers/` — 全ファイル同一
- `tools/environments/` — 全ファイル同一
- `skills/` — ディレクトリ構造同一 (26サブディレクトリ)
- `plugins/` — ディレクトリ構造同一 (13サブディレクトリ)
- `optional-skills/` — ディレクトリ構造同一
- `core/__init__.py`, `core/transports/` — 内容同一
- `core/prompt_caching.py`, `credential_sources.py`, `context_engine.py` など 30+ファイル — 内容同一
- `base/hermes_constants.py`, `utils.py`, `model_tools.py`, `toolsets.py`, `toolset_distributions.py`, `batch_runner.py` — ルート→base移動のみで内容同一
- `hermes_cli/banner.py` — 内容同一 (upstreamブランドのまま)

## TUI 調整方針

- 旧版を丸ごと戻さない。`rich` / `fire` / gateway / cron など不要依存が復活するため、必要な TUI 骨格だけ移す
- `TextArea`、`FileHistory`、`SlashCommandCompleter`、`SlashCommandAutoSuggest`、主要 keybinding を AiDiy Hermes に合わせて使う
- 会話出力は TUI 内の出力ウィンドウに入れず、通常 stdout と `patch_stdout()` でスクロールバックへ流す
- TUI は下部固定の入力、status、spinner、補完メニューを中心にする
- ANSI 色は対応端末でだけ出す。AiDiy アプリ経由や非TTYでは制御コードを出さない

## slash command

`process_command()` で扱う代表コマンド:

```text
/new
/model
/help
/clear
/redraw
/history
/retry
/undo
/save
/copy
/tools
/toolsets
/config
/status
/exit
```

実装上の注意:
- `/q` は alias 衝突を避けるため、終了ショートカットとして先に処理する
- `/model` 引数なしは provider picker を開く
- `/model <model> --provider <provider>` と `/model <provider>:<model>` を受け付ける
- `/model` はセッション内切替にし、必要に応じて `self.agent = None` で次ターンから新モデルを使わせる
- `/new` は会話履歴、sessionId、spinner 状態、agent instance をリセットする
- slash command は会話ログへ積まない。直後の応答後に `[command] /model` などが遅れて見える原因になる

## `/` 補完

- `TextArea` に `SlashCommandCompleter`、`complete_while_typing=True`、`SlashCommandAutoSuggest` を付ける
- `/` 入力直後に補完が開かない場合は KeyBindings で `/` を捕捉し、行頭コマンドのときだけ `buffer.start_completion(select_first=False)` を呼ぶ
- 通常文や URL 内の `/` で補完を出さない。`buffer.document.text_before_cursor.strip() == "/"` を条件にする

## モデル一覧と provider

- `AiDiy_key.json` の有効キーから provider を作る
- OpenAI 互換 `/models` の `created` が取れる場合は `YYYY/MM/DD - model` 表示にする
- Ollama Cloud は 240 日以内に絞って新しい順に並べる
- Ollama Cloud へ渡すモデル名は `:cloud` / 入力揺れの `:clude` を外す
- 上流 Hermes 側では `openai` が OpenRouter alias になる場合がある。AiDiy の `openai_key_id` を使うときは、`api.openai.com/v1` を明示した custom runtime として扱う
- `ollama` は `ollama_key_id` が有効なら Ollama Cloud、無効なら `ollama_host` の local `/v1` を使う
- `/model` 引数なしは provider -> model picker を開く。非TUIでは provider 一覧と使用例を出す
- `/model --provider openai` は provider の先頭モデルへ切り替える
- `/model gpt-5.2 --provider openai` と `/model openrt:anthropic/claude-sonnet-4.5` を受け付ける
- 切替後は `self.agent = None` と route signature reset により、次ターンで新 provider / model の agent を作り直す

代表 provider:
- `ollama`: local または Ollama Cloud
- `openai`: `https://api.openai.com/v1`
- `openrt`: `https://openrouter.ai/api/v1`
- `gemini` / `freeai`: `https://generativelanguage.googleapis.com/v1beta/openai`
- `anthropic`: `https://api.anthropic.com`

## 旧機能を戻す判断基準

戻す対象は単体ツールとして完結するものを優先する。

- `text_to_speech`
- `image_generate`
- `create_video_from_images`
- `vision_analyze`
- `todo`
- `clarify`
- `execute_code`
- `process`
- `browser_providers`

戻さない/スタブに寄せるもの:
- Slack / Discord / Telegram などチャンネル連携
- 常駐 gateway / setup / run
- gateway セッション前提ツール

旧版由来の巨大ツールを丸ごとコピーせず、`tools.registry.register()` に合わせた軽量実装へ寄せる。registry 重複は `tools/*.py` のトップレベル `registry.register(name=...)` を AST で集計して確認する。

## import と依存関係

- 共通モジュールは `command_hermes/base/` に一本化する
- 旧版由来の `from hermes_constants import ...` や `from utils import ...` は `from base.hermes_constants import ...` / `from base.utils import ...` へ置換する
- `model_tools` を参照する箇所は `from base import model_tools` にする
- 依存追加は `command_hermes/pyproject.toml` の dependencies へ追加する
- `.venv` がない環境では、全 Python 構文確認と `tomllib` による `pyproject.toml` 検証を先に行う
- console script ランチャは `_setup.py` が `~/.local/bin/aidiy_hermes.cmd` として生成する
- 依存追加後は `uv sync --upgrade` と `python ..\_setup.py` で同期・ランチャ再生成を行う
- provider SDK は `openai`、`anthropic`、`google-genai` を明示する

## Windows / 非TTY の注意点

- Windows cp932 で落ちる文字は prompt symbol や説明文に入れない。必要なら `>>> ` へ fallback する
- 非TTY時は stdout/stderr を UTF-8 に reconfigure してから出す
- ANSI 色は `_supports_ansi_color()` のような判定に集約し、明確な対応端末だけ許可する
- `FORCE_COLOR=1` または `CLICOLOR_FORCE` がある場合だけ明示的に色を許可する
- `_build_tui()` は通常の Windows Terminal / cmd / PowerShell で実操作確認する。非コンソール環境では `NoConsoleScreenBufferError` になることがある
- 非コンソール subprocess では `prompt_toolkit.print_formatted_text` が `NoConsoleScreenBufferError` になることがある。CLI 出力用の `_cprint()` は失敗時に通常 `print()` へ落とす
- AiDiy Code AI から呼ぶ 1ショットは `aidiy_hermes -z -Q "本文"` の順にする。`-z` は本文省略可にし、`-Q` の直後に本文を置けるようにする

## spinner / status の要点

- spinner は command / 実行中に短周期で invalidate、idle では間隔を伸ばす
- 点字 spinner は出力可能な場合だけ使い、不可なら ASCII `| / - \` に fallback する
- tool 実行中は spinner 行へ `Step n/max: ツール実行中 <tool>` のように短く出す
- 完了ツール履歴は stderr へ `done Step n/max: <tool> (0.1s)` 形式で出し、stdout は会話本文用に残す

## 確認方法

```powershell
cd command_hermes
.venv\Scripts\python.exe -m py_compile cli_main.py
.venv\Scripts\python.exe cli_main.py --version
.venv\Scripts\python.exe cli_main.py --help
.venv\Scripts\python.exe cli_main.py --list-tools
```

直接メソッド確認:

```powershell
@'
from cli_main import HermesCLI
cli = HermesCLI(model="deepseek-v4-flash", base_url="http://localhost:11434/v1")
print(cli.process_command("/q"))
cli.process_command("/model qwen3:latest")
print(cli.model)
cli.conversation_history.append({"role": "user", "content": "x"})
cli.process_command("/new")
print(len(cli.conversation_history), bool(cli.session_id))
'@ | .venv\Scripts\python.exe -
```

実操作では通常ターミナルで `python cli_main.py` を起動し、`/` 補完、Tab/上下キー、`/new`、`/model`、Ctrl+C、Ctrl+D、Ctrl+L を確認する。
