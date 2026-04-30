# HermesCLI TUI調整手順

## このメモを使う場面

- `backend_hermes/cli_main.py` の TUI 表示、起動バナー、スラッシュコマンドを調整したい
- 旧 Hermes Agent の TUI に近い操作感へ戻したい
- `/` 補完、`/new`、`/model` まわりの挙動を確認したい

## 関連ファイル

- `backend_hermes/cli_main.py` — AiDiy Hermes の CLI/TUI エントリポイント
- `backend_hermes/hermes_cli/commands.py` — `COMMAND_REGISTRY` と `SlashCommandCompleter`
- `backend_hermes/_old_hermes-agent/cli.py` — 旧 Hermes Agent の参照元
- `backend_hermes/tools/tts_tool.py` — AiDiy_key.json の OpenAI キーを使う軽量 TTS ツール
- `backend_hermes/tools/media_tools.py` — 画像生成と画像列からの簡易動画作成ツール
- `backend_hermes/tools/vision_tool.py` — OpenAI vision モデルを使う画像解析ツール
- `backend_hermes/tools/planning_tools.py` — `todo` と `clarify` の軽量復活
- `backend_hermes/tools/code_execution_tool.py` — 短い Python コード実行ツール
- `backend_hermes/tools/process_tool.py` — ローカルプロセス一覧/終了ツール
- `backend_hermes/base/toolsets.py` — `hermes-harness` に含めるツール定義
- `backend_hermes/AGENTS.md` — backend_hermes の実装方針

## 実装方針

- 旧版 `_old_hermes-agent/cli.py` を丸ごと戻すと `rich` / `fire` / `agent.*` / gateway / cron など未導入依存が復活するため、TUI の骨格だけをコピーし、AiDiy Hermes に不要な依存を削る
- `TextArea`、`FileHistory`、`SlashCommandCompleter`、`SlashCommandAutoSuggest`、Enter/Tab/上下キー/Alt+Enter/Ctrl+Enter の keybinding は旧版の流れに寄せる
- 実用コマンドとして `/new`、`/model`、`/help`、`/clear`、`/redraw`、`/history`、`/retry`、`/undo`、`/save`、`/copy`、`/tools`、`/toolsets`、`/config`、`/status`、`/exit` を `cli_main.py::process_command()` で処理する
- `/model` 引数なしは旧版準拠で provider picker を開く。1段目で provider、2段目で model を選択し、Enterで切替、Esc/Ctrl+Cでキャンセルする
- TUI 外で `/model` を呼んだ場合は provider 一覧と直接指定例を表示する
- `/model <model> --provider <provider>` と `/model <provider>:<model>` の直接切替も受け付ける
- 補完に出すコマンドは `HermesCLI._command_available()` で AiDiy Hermes 対応済みに絞る。旧 Hermes の cloud/gateway 専用コマンドは意図的に削る
- alias 解決は `resolve_command()` を使う
  - ただし `/q` は registry 上では `queue` alias と衝突しやすいため、CLI では終了ショートカットとして先に処理する
- `/model <name>` はセッション内だけの切替にし、`self.agent = None` で次ターンから新モデルを使わせる
- `/new` は会話履歴、セッションID、スピナー状態、エージェントインスタンスをリセットする
- `/model` のモデル一覧は OpenAI 互換 `/models` の `created` を見て、`YYYY/MM/DD - model` 表示にする。Ollama Cloud は 240 日以内に絞って新しい順に並べる
- `aidiy_key.json` の有効キーから provider を作る
  - `ollama`: ローカルまたは Ollama Cloud。Cloud は `:cloud` / `:clude` を外す
  - `openai`: `https://api.openai.com/v1`
  - `openrt`: `https://openrouter.ai/api/v1`
  - `gemini` / `freeai`: `https://generativelanguage.googleapis.com/v1beta/openai`
  - `claude`: `https://api.anthropic.com`、`core/run_agent.py` 側で Anthropic Messages 形式に変換して直接呼ぶ
- Windows の cp932 コンソールで行が落ちないよう、実行時表示は絵文字・罫線・点字スピナーに依存しない ASCII 寄りにする
- `/model` 実行ログを会話ログ側へ積むと、直後のモデル応答後に `[command] /model` が遅れて見えるため、TUI の Enter ハンドラでは slash command を out buffer に積まない
- エージェント実行中に slash command を入力した場合は、入力バッファを reset して残留実行を防ぐ

## 旧機能の復活方針

- Slack / Discord / Telegram など入出力チャンネル系は AiDiy Hermes では不要なので戻さない
- `hermes_cli/gateway.py` は旧 import 互換のためファイルだけ残し、常駐 gateway / setup / run は無効化スタブにする
- Yuanbao など gateway セッション前提ツールは登録名だけ残し、`check_fn` を False にして通常ツールセットからは出さない
- まず戻す対象は単体ツールとして完結するもの
  - `text_to_speech`: `openai_key_id` を使う OpenAI TTS
  - `image_generate`: `openai_key_id` を使う画像生成
  - `create_video_from_images`: ffmpeg で画像列から MP4 を作成
  - `vision_analyze`: `openai_key_id` を使うローカル画像解析
  - `todo`: `backend_hermes/temp/state/todo.json` に永続化する軽量 TODO
  - `clarify`: ユーザーへの確認質問を JSON として返し、モデルに質問文をそのまま出させる
  - `execute_code`: 一時ファイルで短い Python snippet を実行
  - `process`: ローカルプロセス一覧と PID kill
  - `browser_providers`: `browser_tool.py` の直接 import 前提なので `tools/browser_providers/` を旧版から移植する
- 旧版の巨大ツールを丸ごとコピーするより、`tools.registry.register()` に合わせた軽量ツールとして戻す方が依存破壊が少ない
- `base/model_tools.py` の `_AGENT_LOOP_TOOLS` に `todo` が残っていると registry dispatch されないため、軽量 `todo` を使う場合は除外する
- registry の正本は AiDiy 用の軽量実装へ寄せる
  - `todo` / `clarify`: `planning_tools.py`
  - `image_generate` / `create_video_from_images`: `media_tools.py`
  - `vision_analyze`: `vision_tool.py`
  - `process`: `process_tool.py`
- 旧版由来の `todo_tool.py` / `clarify_tool.py` / `image_generation_tool.py` / `vision_tools.py` / `process_registry.py` は、直接 import 用の関数・定数・補助クラスを残し、registry 自動登録はさせない
- registry 重複確認は、`tools/*.py` のトップレベル `registry.register(name=...)` を AST で集計する。重複が出た場合は、意図せず後勝ちで実装が変わっていないか確認する

## base import 統一

- 共通モジュールの実体は `backend_hermes/base/` に一本化する。ルート直下に `hermes_constants.py` / `utils.py` / `model_tools.py` などの再エクスポート shim を増やさない
- 旧版コピーの `hermes_cli/`・`tools/` に残りやすい `from hermes_constants import ...` や `from utils import ...` は、`from base.hermes_constants import ...` / `from base.utils import ...` へ置換する
- `model_tools` をモジュール名として参照する箇所は `from base import model_tools` にする。`import base.model_tools` だけにすると、後続の `model_tools.xxx` 参照が壊れる
- `pyproject.toml` の `py-modules` は `["cli_main", "hermes_state"]`。`base` は package として含める
- 確認は旧 import 検索、全 Python ファイルの `py_compile`、依存が入った環境での `cli_main.py --help` / `--list-tools` を行う

## 依存関係

- `requirements.txt` と `pyproject.toml` の dependencies は揃える
- 旧版由来の現行モジュールが直接 import するため、少なくとも `openai`、`pyyaml`、`prompt-toolkit`、`rich`、`requests`、`httpx[socks]`、`python-dotenv`、`pydantic`、`websockets`、`fal-client` を含める
- `.venv` がない環境では CLI 起動確認は依存不足で止まる。依存なしでできる検証として、`compile(source, path, "exec")` による全 Python 構文確認と `tomllib` による `pyproject.toml` 検証を行う

## Windows / process_registry 互換

- `tools/process_registry.py` は旧 `tools/environments/local.py` の `_find_shell` と `_sanitize_subprocess_env` を直接 import する
- AiDiy 版の `local.py` を簡略化する場合でも、この 2 関数と `_HERMES_PROVIDER_ENV_BLOCKLIST` は残す
- Windows の `_find_shell()` は Git Bash があれば優先し、なければ PowerShell、最後に `cmd.exe` へ fallback する
- `tools/delegate_tool.py` は `tools.terminal_tool.set_approval_callback` を import するため、簡易 terminal 実装でも thread-local の互換 API を残す

## `/` 補完メニュー

- `TextArea` には `SlashCommandCompleter`、`complete_while_typing=True`、`SlashCommandAutoSuggest` を付ける
- それだけで `/` 入力直後にメニューが開かない場合があるため、`KeyBindings` で `/` を捕捉し、行頭コマンドとしての `/` のときだけ `buffer.start_completion(select_first=False)` を呼ぶ
- 通常文や URL 内の `/` で補完が出ると邪魔なので、`buffer.document.text_before_cursor.strip() == "/"` の場合だけメニューを開く

## TUI旧版寄せの要点

- 旧版 Hermes の TUI は会話出力を TUI 内の出力ウィンドウに入れない。通常 stdout と `patch_stdout()` でスクロールバックへ流し、TUI は下部固定の入力・status・spinner だけを持つ
- `cli_main.py` に `out_buf` / `out_win` を入れるとスクロールバック、プロンプト追従、resize 時の見え方が旧版と大きく変わるため避ける
- root layout は旧版同様に `Window(height=0)` から始め、`model_picker`、`spinner`、`spacer`、`status_bar`、`input_rule_top`、`input_area`、`input_rule_bot`、`CompletionsMenu` の順を基本にする
- 下部固定入力欄の上下罫線は `input-rule`。スキン上書き後に再度 `#FFFFFF` を入れると、オレンジ系スキンが残らず白線を維持できる
- 入力後にスクロールバックへ残るユーザー入力は `_print_user_message()` で上下線に挟む。`process_loop()` 側で直接 `>>>` を出さず、この helper を通す
- スクロールバックへ出す `print()` には ANSI 色コードを直接入れない。AiDiy の Web 表示に流れると `?[32m` のような文字として見えるため、色は AiDiy 側のメッセージ種別表示に任せる
- モデル応答は `_print_cpu_output()` で `--- AiDiy ---` 表記にする。従来の `CPU OUTPUT` や `Hermes` 表記はユーザー向け表示として避ける
- `_print_cpu_output()` の AiDiy 出力は通常ターミナル（TTY）では緑にする。ただし AiDiy アプリ経由など非TTYでは ANSI を出さず、`?[32m` の混入を防ぐ
- Windows では `isatty()` が True でも AiDiy 側の擬似端末が ANSI を解釈しないことがある。色を出す判定は `_supports_ansi_color()` に集約し、`WT_SESSION` / `ANSICON` / `ConEmuANSI=ON` / `TERM_PROGRAM` / ANSI 系 `TERM` など明確な対応端末だけ許可する
- `show_banner()` や `_cprint()` から出る既存 ANSI も、未対応時は `_strip_ansi()` で除去してから出す。`FORCE_COLOR=1` または `CLICOLOR_FORCE` で明示的に色を許可できる
- スクロールバックの罫線は `─` を使う。Windows のパイプ出力では cp932 化で文字化けしやすいため、非TTY時は `_configure_pipe_encoding()` で stdout/stderr を UTF-8 に reconfigure してから出す
- 途中経過・待機表示は `_render_spinner_text()` の戻り値を `class:hint` で出す。`_build_tui_style_dict()` の最後に `hint=#00BFFF italic` を再適用し、シアン/青系を維持する
- `CompletionsMenu(max_height=12, scroll_offset=1)` は明示配置する。これがないと補完メニューの高さ・位置が旧版と揃いにくい
- `patch_stdout(raw=True)` ではなく旧版と同じ `patch_stdout()` を使う
- `mouse_support` は旧版と同じ `False`
- resize 時は `app._on_resize` をラップし、`renderer.output.erase_screen()`、`cursor_goto(0, 0)`、`renderer.reset(leave_alternate_screen=False)` を行う。tmux / cmux / SSH / Windows Terminal の ghost 行対策
- `Ctrl+C` は旧版同様に「入力があればクリア」「実行中は interrupt」「2秒以内の2回目は force exit」「空入力待機中は exit」
- `Ctrl+D` は文字があれば delete、空なら exit。`Ctrl+L` は出力バッファ削除ではなく full redraw
- 旧版 TUI 主要メソッドの有無をソース比較する場合は、少なくとも `_get_status_bar_snapshot`、`_get_tui_prompt_symbols`、`_get_tui_prompt_fragments`、`_build_tui_style_dict`、`_build_tui_layout_children`、`run`、`chat`、`process_command` を確認する
- slash command 判定は `text.startswith("/")` だけに戻さない。bracketed paste 制御文字や terminal response 混入対策として `_looks_like_slash_command()` 経由にする
- Windows cp932 出力環境では旧版の `❯` prompt symbol が `UnicodeEncodeError` になることがある。`_fits_output_encoding()` で出力可否を見て、出せない場合は `>>> ` へ fallback する
- 色合いを旧版へ寄せる場合は `_tui_style_base` の key 数と key 名を `ast` で比較する。2026-04-29 時点では旧版 / 新版とも 41 key、欠落 0 / 余分 0
- `_build_tui_style_dict()` は `dict(self._tui_style_base)` だけにしない。旧版同様に `hermes_cli.skin_engine.get_prompt_toolkit_style_overrides()` を重ね、実行中変更用に `_apply_tui_skin_style()` も残す
- slash command 実行中の点滅は、旧版同様 `int(time.monotonic() * 10)` で 10fps 相当にする。描画回数依存で index 加算すると、環境によって点滅速度がずれる
- 旧版スピナーは点字フレームだが、Windows cp932 では出力できない場合がある。`_spinner_frames()` で `_fits_output_encoding()` を見て、出せる場合は点字、出せない場合は ASCII `| / - \` に fallback する
- 通常 spinner text は旧版同様、`  text` / `  text  (0.1s)` の形にする。フレームを前置すると旧版より点滅感が強くなる
- 旧版のステップ進捗表示は、`core.run_agent.AIAgent` から `thinking_callback` / `step_callback` / `tool_progress_callback` へ通知し、`cli_main.py` 側で spinner 行へ反映する。表示形式は `Step 1/30: モデル呼び出し中`、ツール中は `Step 1/30: ツール実行中 read_file ...`
- `tool.completed` では `Step n/max: ツール完了 <tool>` を短く出し、次のモデル呼び出しで `Step n+1/max` に更新する。`_tool_start_time` は tool 実行中だけ有効にし、経過秒表示を旧版同様に維持する
- 完了したツール履歴は spinner の一時表示とは別に stderr へ `done Step n/max: <tool> (0.1s)` 形式で1行ずつ出す。stdout は会話本文用に残し、stderr は実行ログとして使う
- `spinner_loop` は command / spinner 表示中に `0.1s` で invalidate、idle では `0.2s` 待機にする。idle でも常時 repaint すると下部入力位置が動いて見えやすい
- 非コンソール環境では `_build_tui()` 直接生成が `prompt_toolkit.output.win32.NoConsoleScreenBufferError` になるため、TUI 実操作確認は通常の Windows Terminal / cmd / PowerShell で行う

## 起動ロゴ

- `show_banner()` は旧版の `build_welcome_banner()` をそのまま使うには依存が重いため、`cli_main.py` 内に軽量な ANSI ロゴを持つ
- ロゴには `AiDiy HERMES` とモデル名、endpoint を表示する
- Windows の `--help` や非UTF-8コンソールで落ちやすい文字は argparse の説明文に入れない。説明文は ASCII の `-` を使う

## バックアップ

- 旧版へ寄せる大きめの修正前に現行実装を手動退避した
  - `backup/manual/20260429_175108/backend_hermes_cli_main.py`
- MCP backup が `Transport closed` の場合は、手動バックアップを先に作ってから `apply_patch` で編集する

## 確認方法

PowerShell:

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
cli = HermesCLI(model='deepseek-v4-flash', base_url='http://localhost:11434/v1')
print(cli.process_command('/q'))
cli.process_command('/model qwen3:latest')
print(cli.model)
cli.conversation_history.append({'role': 'user', 'content': 'x'})
cli.process_command('/new')
print(len(cli.conversation_history), bool(cli.session_id))
'@ | .venv\Scripts\python.exe -
```

注意:
- `_build_tui()` は実 Windows コンソールがない実行環境では `prompt_toolkit.output.win32.NoConsoleScreenBufferError` になることがある
- TUI の実操作確認は通常のターミナルで `python cli_main.py` を起動して、`/` 入力、Tab/上下キー、`/new`、`/model` を確認する
