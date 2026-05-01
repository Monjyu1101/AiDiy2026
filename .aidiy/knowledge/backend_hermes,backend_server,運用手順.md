# backend_hermes 運用手順

> 文書: `backend_hermes,backend_server,運用手順.md` | 実装: `backend_hermes/cli_main.py`, `backend_server/core_router/AIコア/AIコード_hermes.py`

## このメモを使う場面

- `aidiy_hermes` を単体 CLI として起動する。
- AiDiy の Code AI から `aidiy_hermes` を呼ぶ経路を確認する。
- provider / model / slash command / TUI の変更後に確認する。

## 関連ファイル

- `backend_hermes/cli_main.py`
- `backend_hermes/core/run_agent.py`
- `backend_hermes/base/toolsets.py`
- `backend_hermes/tools/registry.py`
- `backend_hermes/hermes_cli/commands.py`
- `backend_server/AIコア/AIコード_cli.py`
- `backend_server/conf/conf_json.py`
- `backend_server/conf/conf_model.py`

## 位置づけ

- `backend_hermes` は常駐 HTTP サーバーではない。
- 実行名は `aidiy_hermes`。
- `_start.py` の常駐起動対象ではない。
- `_setup.py` と `_cleanup.py` の対象。
- AIコードパネルでは `CODE_AI*_NAME = "aidiy_hermes"` として使う。

## セットアップ

通常はプロジェクトルートで `_setup.py` を使う。

```powershell
python _setup.py
```

`_setup.py` の Hermes セットアップは、`backend_hermes/requirements.txt` を同期したうえで `uv tool install --force --refresh --editable .` により `aidiy_hermes` / `text-hermes` を再登録する。
`--refresh` を付けないと、editable install の古いメタデータが残り、追加した依存関係がグローバル tool 環境へ反映されないことがある。

手動で確認する場合:

```powershell
Set-Location backend_hermes
uv venv .venv
uv pip install -r requirements.txt
uv tool install --force --refresh --editable .
aidiy_hermes --version
```

`backend_hermes/setup.py` は `requirements.txt` を `install_requires` として読む。
provider SDK を追加したときは `requirements.txt`、`setup.py` 経由の metadata、`uv tool install --refresh` の3点を確認する。

主な provider 依存:

| 用途 | requirements |
|------|--------------|
| OpenAI / OpenAI互換 | `openai` |
| Claude | `anthropic` |
| Google Gemini / Google系 | `google-genai` |

## 実行例

```powershell
# 対話モード
aidiy_hermes

# 1ショット
aidiy_hermes -z -Q "このフォルダの構成を要約して"

# provider / model 指定
aidiy_hermes -z --provider openai -m gpt-5.2 -Q "TODO を整理して"
aidiy_hermes -z --provider ollama -m deepseek-v4-flash:cloud -Q "ファイル一覧を確認して"
```

AiDiy の Code AI 連携では、タイトルやバナーを出さないため `-z` を先に置き、クエリ直前に `-Q` を置く。
`-z` は本文省略可にしておき、`-z -Q "本文"` の形を 1ショットとして扱えるようにする。

ワンショット / quiet 実行の出力契約:

- stdout: 正式回答だけ。
- stderr: thinking、step、tool 進捗、警告、`session_id` などの処理ログ。
- ワンショットの stderr では spinner のフレームを連続出力しない。待機中は `[wait] AI応答待機` や `[wait] <tool/command>待機` のような静的1行にする。
- AiDiy 側で正式回答を取り込む場合は stdout を採用し、stderr はログ表示やデバッグ用に扱う。

## 主な CLI オプション

| オプション | 内容 |
|------------|------|
| `-z`, `--oneshot` | 1ショット実行 |
| `-Q`, `--quiet` | 余計な表示を抑制 |
| `-m`, `--model` | モデル指定 |
| `--provider` | provider 指定 |
| `--list-tools` | 利用可能ツール一覧 |
| `--version` | バージョン表示 |
| `--no-tools` | ツール無効化 |

## 対応 provider

- API provider: `ollama`, `openai`, `openrt`, `gemini`, `freeai`, `claude`
- CLI bridge: `claude_cli`, `codex_cli`, `gemini_cli`, `copilot_cli`

既定 provider は `ollama`。

## AiDiy 連携

設定例:

```json
{
  "CODE_AI1_NAME": "aidiy_hermes",
  "CODE_AIDIY_HERMES_MODEL": "auto"
}
```

連携箇所:

- `AIコード_cli.py`: 実行ファイル探索、`--version`、`aidiy_hermes -Q -z ...` のコマンド構築。
- `AIコード_cli.py`: `aidiy_hermes -z -Q ...`、モデル指定時は `aidiy_hermes -z --provider ollama --model <model> -Q ...` のコマンド構築。
- `conf_json.py`: `CODE_AIDIY_HERMES_MODEL`。
- `conf_model.py`: `get_code_models()["aidiy_hermes"]`。
- frontend の AI 設定画面: code AI 選択肢。

`aidiy_hermes` は専用の `AiDiy_code_*.json` を持たず、モデル一覧は `conf_model.py` 側で動的に作る。

## 変更時の確認

```powershell
Set-Location backend_hermes
.venv/Scripts/python.exe -m py_compile cli_main.py
.venv/Scripts/python.exe cli_main.py --version
.venv/Scripts/python.exe cli_main.py --help
.venv/Scripts/python.exe cli_main.py --list-tools
uv tool install --force --refresh --editable .
aidiy_hermes -z -Q "おはよう"
aidiy_hermes -z --provider ollama --model "deepseek-v4-flash:cloud" -Q "おはよう"
uv tool run --from aidiy-hermes python -c "import openai; import anthropic; import google.genai; print('provider sdks ok')"
```

TUI / slash command の詳細調整は `HermesCLI_TUI調整手順.md` を使う。
Code CLI としての追加・表示・ANSI 対策は `CodeCLI追加手順.md`、`CodeCLIプロンプト整形.md`、`CodeCLI表示ANSI制御コード対処.md` を使う。
