# AiDiy Hermes

**`aidiy_hermes` は AiDiy に統合されたコードエージェント CLI** です。

- 実装場所: `backend_hermes/`
- 実行名: `aidiy_hermes`
- 種別: on-demand CLI（常駐サーバーではない）
- AiDiy 連携名: `CODE_AI*_NAME = "aidiy_hermes"`

## できること

- 対話 TUI モード
- 1ショット実行
- provider / model 切り替え
- ファイル操作 / ターミナル実行 / Web / planning / media / process 系ツールの利用

## セットアップ

### 推奨

```bash
python _setup.py
```

`_setup.py` の「バックエンド(hermes)」は、`.venv` 作成、依存インストール、`aidiy_hermes` のグローバル登録試行まで行います。

### 手動

```bash
cd backend_hermes
uv venv .venv
uv pip install -r requirements.txt
.venv/Scripts/python.exe cli_main.py --help
```

## 起動例

```bash
# 対話モード
aidiy_hermes

# 1ショット
aidiy_hermes -Q -z "このフォルダの構成を要約して"

# provider / model 指定
aidiy_hermes --provider openai -m gpt-5.2 -Q -z "TODO を整理して"
aidiy_hermes --provider ollama -m deepseek-v4-flash -Q -z "ファイル一覧を確認して"
```

## 主なオプション

| オプション | 内容 |
|---|---|
| `-z`, `--oneshot` | 1ショット実行 |
| `-Q`, `--quiet` | 余計な表示を抑制 |
| `-m`, `--model` | モデル指定 |
| `--provider` | provider 指定 |
| `--list-tools` | 利用可能ツール一覧 |
| `--version` | バージョン表示 |

## 対応 provider

- `ollama`
- `openai`
- `openrt`
- `gemini`
- `freeai`
- `claude`
- `claude_cli`
- `codex_cli`
- `gemini_cli`
- `copilot_cli`

## AiDiy との連携

`backend_server/_config/AiDiy_key.json` では、たとえば次のように設定します。

```json
{
  "CODE_AI1_NAME": "aidiy_hermes",
  "CODE_AIDIY_HERMES_MODEL": "auto"
}
```

- 起動コマンドは `backend_server/AIコア/AIコード_cli.py` が組み立てる
- モデル一覧は `backend_server/conf/conf_model.py` が Ollama モデル一覧から動的生成する
- `frontend_web` / `frontend_avatar` の AI 設定画面から選択できる

## 注意

- `_start.py` は `backend_hermes` を起動しません
- `aidiy_hermes` は専用の `AiDiy_code_*.json` を持ちません
- 詳細は [AGENTS.md](./AGENTS.md) を参照してください
