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
- `_config/AiDiy_key.json` — AiDiy provider/モデル設定
- `_config/AiDiy_mcp.json` — AiDiy MCP サーバー定義

## Upstream からの調整点

この `command_hermes` は [Nous Research の hermes-agent](https://github.com/nousresearch/hermes-agent) **v0.21.0** (MIT License) を取り込み、AiDiy 用のレイヤを重ねたものです。
（2026-09-04 に v0.12.0 ベースから v0.21.0 ベースへ全面同期。旧ツリーは `command_hermes_0.12/` に退避。）

### レイアウトの読み替え（3点のみ）

| upstream | AiDiy |
|----------|-------|
| リポジトリ直下のモジュール群 | `base/` |
| `agent/` パッケージ | `core/` |
| `cli.py` | `cli_main.py` |

読み替えは `cli_main.py` 冒頭の **layout shim** が行います。`sys.path` へ `base/` と `command_hermes/` を追加し、
`sys.modules["agent"] = core` と `sys.modules["cli"] = cli_main` を登録します。
このため **upstream 由来コードの `from agent...` / `from cli import ...` は書き換え不要（書き換え禁止）** です。

`base/hermes_constants.py` だけは `_INSTALL_ROOT` / `_NODE_BOOTSTRAP_SCRIPT` を `parent.parent` に補正しています（`base/` に置いたため）。

### 同梱するもの / しないもの

同梱: `core/`（upstream `agent/`）、`base/`、`tools/`、`hermes_cli/`、`gateway/`、`tui_gateway/`、`cron/`、
`acp_adapter/`、`plugins/`、`providers/`、`skills/`、`optional-skills/`、`locales/`、`assets/`、`scripts/`、`native/`

非同梱: `ui-tui/`（Node/TS TUI）、`web/`、`website/`、`evals/`、`tests/`、`docker/`、`nix/`

0.12 系では `cron/`、`gateway/`、`tui_gateway/`、`acp_adapter/` を削除・スタブ化していましたが、
0.21 では upstream コードが相互に参照するため **そのまま同梱**しています（AiDiy では常駐させないだけ）。

### AiDiy レイヤ（upstream 追従時に再適用が必要）

| 対象 | 内容 |
|------|------|
| `cli_main.py` | layout shim / `_AIDIY_*` 設定ブロック（`AiDiy_key.json`、外部 CLI provider 定義）/ `_aidiy_*` メソッド群（`/model` ピッカー、モデル一覧取得、外部 CLI サブプロセス実行）/ `chat()` の CLI ディスパッチ / `_handle_model_switch` フック / `_AIDIY_RESPONSE_LABEL = "AiDiy,Hermes"` / `main()` 冒頭の MCP discovery / `cli_entry()` argparse エントリ |
| `tools/mcp_tool.py` | `_load_aidiy_mcp_servers()` と `_load_mcp_config()` へのマージ |
| `tools/daemon_pool.py` | Python 3.14 の `ThreadPoolExecutor` 内部変更対応 |
| `hermes_cli/main.py` | `_resolve_use_tui()` を常に False |
| `hermes_cli/_parser.py` | `--tui` / `--dev` のヘルプ文言 |
| `base/hermes_constants.py` | `_INSTALL_ROOT` / `_NODE_BOOTSTRAP_SCRIPT` の補正 |
| `pyproject.toml` | upstream core 依存 + anthropic / google-genai / fal-client / mcp / windows-curses |
| `aidiy_hermes_exec.bat`、`_setup.py`、`_start.py`、`_cleanup.py` | AiDiy 専用。upstream には対応物なし |

0.12 系にあった `*_win.py` / `*_linux.py` の platform selector 層は、upstream 0.21 が Windows ネイティブ対応を
本体に取り込んだため **廃止**しました。詳細は `command_hermes,Windows対応規則.md` を参照。

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

- upstream 由来コードの import は **書き換えない**。`from agent.xxx import ...` / `from hermes_constants import ...` / `from utils import ...` / `from cli import ...` はそのままで動く（`cli_main.py` の layout shim が `sys.path` と `sys.modules` を張るため）
- `from base.xxx import ...` / `from core.xxx import ...` は **書かない**。同じモジュールが二重ロードされ、モジュールレベルの状態が分裂する
- `cli_main.py` 以外を単体で import して試すときは、先に `sys.path` へ `base/` と `command_hermes/` を追加し、`sys.modules["agent"] = core` を張る
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
- AiDiy Code AI から呼ぶ 1ショットは `aidiy_hermes -Q -z "本文"` の順にする。`-Q`（quiet）は真偽フラグ、`-z`（oneshot）は本文を値に取る `nargs="?"` なので、本文は必ず `-z` の直後へ置く

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
cli = HermesCLI(model="deepseek-v4-flash", base_url="http://127.0.0.1:11434/v1")
print(cli.process_command("/q"))
cli.process_command("/model qwen3:latest")
print(cli.model)
cli.conversation_history.append({"role": "user", "content": "x"})
cli.process_command("/new")
print(len(cli.conversation_history), bool(cli.session_id))
'@ | .venv\Scripts\python.exe -
```

実操作では通常ターミナルで `python cli_main.py` を起動し、`/` 補完、Tab/上下キー、`/new`、`/model`、Ctrl+C、Ctrl+D、Ctrl+L を確認する。
