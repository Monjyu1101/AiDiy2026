# Hermes CLI TUI 調整手順

## このメモを使う場面
- `backend_hermes/cli_main.py` の TUI、起動バナー、slash command を調整する
- `/` 補完、`/new`、`/model`、spinner、色表示の挙動を確認する
- 旧 Hermes Agent 由来の機能を AiDiy Hermes に移植するか判断する

## 関連ファイル
- `backend_hermes/cli_main.py` — CLI/TUI エントリ
- `backend_hermes/hermes_cli/commands.py` — `COMMAND_REGISTRY` と補完
- `backend_hermes/_old_hermes-agent/cli.py` — 旧版参照元
- `backend_hermes/base/toolsets.py` — toolset 定義
- `backend_hermes/base/model_tools.py` — agent loop tool 定義
- `backend_hermes/tools/` — 各ツール実装
- `backend_hermes/AGENTS.md` — Hermes 実装方針

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

代表 provider:
- `ollama`: local または Ollama Cloud
- `openai`: `https://api.openai.com/v1`
- `openrt`: `https://openrouter.ai/api/v1`
- `gemini` / `freeai`: `https://generativelanguage.googleapis.com/v1beta/openai`
- `claude`: `https://api.anthropic.com`

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

- 共通モジュールは `backend_hermes/base/` に一本化する
- 旧版由来の `from hermes_constants import ...` や `from utils import ...` は `from base.hermes_constants import ...` / `from base.utils import ...` へ置換する
- `model_tools` を参照する箇所は `from base import model_tools` にする
- `requirements.txt` と `pyproject.toml` の dependencies を揃える
- `.venv` がない環境では、全 Python 構文確認と `tomllib` による `pyproject.toml` 検証を先に行う

## Windows / 非TTY の注意点

- Windows cp932 で落ちる文字は prompt symbol や説明文に入れない。必要なら `>>> ` へ fallback する
- 非TTY時は stdout/stderr を UTF-8 に reconfigure してから出す
- ANSI 色は `_supports_ansi_color()` のような判定に集約し、明確な対応端末だけ許可する
- `FORCE_COLOR=1` または `CLICOLOR_FORCE` がある場合だけ明示的に色を許可する
- `_build_tui()` は通常の Windows Terminal / cmd / PowerShell で実操作確認する。非コンソール環境では `NoConsoleScreenBufferError` になることがある

## spinner / status の要点

- spinner は command / 実行中に短周期で invalidate、idle では間隔を伸ばす
- 点字 spinner は出力可能な場合だけ使い、不可なら ASCII `| / - \` に fallback する
- tool 実行中は spinner 行へ `Step n/max: ツール実行中 <tool>` のように短く出す
- 完了ツール履歴は stderr へ `done Step n/max: <tool> (0.1s)` 形式で出し、stdout は会話本文用に残す

## 確認方法

```powershell
cd backend_hermes
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
