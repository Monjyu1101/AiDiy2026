# backend_hermes 運用手順

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

手動で確認する場合:

```powershell
Set-Location backend_hermes
uv venv .venv
uv pip install -r requirements.txt
.venv/Scripts/python.exe cli_main.py --help
```

## 実行例

```powershell
# 対話モード
aidiy_hermes

# 1ショット
aidiy_hermes -Q -z "このフォルダの構成を要約して"

# provider / model 指定
aidiy_hermes --provider openai -m gpt-5.2 -Q -z "TODO を整理して"
aidiy_hermes --provider ollama -m deepseek-v4-flash -Q -z "ファイル一覧を確認して"
```

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
```

TUI / slash command の詳細調整は `HermesCLI_TUI調整手順.md` を使う。
Code CLI としての追加・表示・ANSI 対策は `CodeCLI追加手順.md`、`CodeCLIプロンプト整形.md`、`CodeCLI表示ANSI制御コード対処.md` を使う。
