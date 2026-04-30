# backend_hermes 実装要点まとめ

## 本書の目的

このファイルは **backend_hermes（`aidiy_hermes` CLI 基盤）の実装詳細** を記載したドキュメントです。

**関連ドキュメント：**
- **[../AGENTS.md](../AGENTS.md)** - プロジェクト全体方針
- **[../CLAUDE.md](../CLAUDE.md)** - クイックコマンドと全体インデックス
- **[../backend_server/AGENTS.md](../backend_server/AGENTS.md)** - AI コードパネル側の統合実装

---

## 概要

`backend_hermes` は、AiDiy に統合された **on-demand のコードエージェント CLI** です。

- 常駐 HTTP サーバーではない
- 実行名は **`aidiy_hermes`**
- 手動で `cli_main.py` を起動しても使える
- `backend_server` の AI コードパネルでは `CODE_AI*_NAME = "aidiy_hermes"` として呼び出される

もともとの Hermes Agent の TUI / エージェントループをベースに、AiDiy 向けに次を追加・調整しています。

- Windows 前提の実行性
- AiDiy の `AiDiy_key.json` を使う provider / model 解決
- `backend_server` の CodeAI 連携
- 旧機能のうち必要な tool / slash command の再導入

---

## 現在の位置づけ

### プロジェクト内での役割

| 役割 | 内容 |
|---|---|
| 単体 CLI | `aidiy_hermes` / `python cli_main.py` として直接使う |
| AiDiy 統合 | `backend_server/AIコア/AIコード_cli.py` から subprocess で起動される |
| 常駐起動 | なし（`_start.py` の起動対象外） |
| セットアップ | `python _setup.py` の「バックエンド(hermes)」 |
| クリーンアップ | `python _cleanup.py` の「バックエンド(hermes)」 |

### 対応 provider

`cli_main.py` の `--provider` では次を扱います。

- API provider: `ollama`, `openai`, `openrt`, `gemini`, `freeai`, `claude`
- CLI bridge: `claude_cli`, `codex_cli`, `gemini_cli`, `copilot_cli`

既定 provider は `ollama` です。

---

## 技術スタック

| 項目 | 内容 |
|---|---|
| 言語 | Python 3.11+ |
| 依存管理 | `requirements.txt` |
| TUI | `prompt_toolkit` |
| 通信 | `requests`, `httpx`, `openai` 互換クライアント, Claude API 連携 |
| 実行方式 | 単体 CLI / subprocess 呼び出し |

---

## ディレクトリ構成

```text
backend_hermes/
├── cli_main.py       # CLI エントリポイント
├── requirements.txt  # 依存関係
├── README.md
├── AGENTS.md
├── NOTICE.md
├── base/             # 共通定数・utils・toolsets
├── core/             # AIAgent / prompt / display / retry
├── hermes_cli/       # slash command / TUI 補助 / 互換レイヤ
├── tools/            # file / terminal / web / media / planning / process
├── plugins/          # プラグイン拡張
├── skills/           # スキル資産
├── optional-skills/  # 任意スキル
├── environments/     # 実行環境補助
└── temp/             # 一時状態
```

---

## 重要ファイル

| ファイル | 役割 |
|---|---|
| `cli_main.py` | CLI オプション、TUI、provider/model picker、slash command 処理 |
| `core/run_agent.py` | エージェント会話ループとツール実行 |
| `base/toolsets.py` | 既定ツールセットの束ね方 |
| `tools/registry.py` | ツール登録の中心 |
| `hermes_cli/commands.py` | slash command 補完 |

---

## 起動方法

### 推奨

```bash
python _setup.py
```

`_setup.py` の「バックエンド(hermes)」は、次を順に行います。

1. `.venv` 作成
2. `uv pip install -r requirements.txt`
3. `uv tool install --force --editable .` を試行

3 が失敗しても、`cli_main.py` の直接実行は継続して使えます。

### 手動

```bash
cd backend_hermes
uv venv .venv
uv pip install -r requirements.txt
.venv/Scripts/python.exe cli_main.py --help
```

### 実行例

```bash
# 対話モード
aidiy_hermes

# 1ショット
aidiy_hermes -Q -z "このフォルダの構成を要約して"

# provider / model 指定
aidiy_hermes --provider openai -m gpt-5.2 -Q -z "TODO を整理して"
aidiy_hermes --provider ollama -m deepseek-v4-flash -Q -z "ファイル一覧を確認して"
```

---

## 主な CLI オプション

| オプション | 内容 |
|---|---|
| `-z`, `--oneshot` | 1ショット実行 |
| `-Q`, `--quiet` | 余計な表示を抑制 |
| `-m`, `--model` | モデル指定 |
| `--provider` | provider 指定 |
| `--list-tools` | 利用可能ツール一覧 |
| `--version` | バージョン表示 |
| `--no-tools` | ツール無効化 |

---

## AiDiy との連携

### backend_server 側の接続名

AiDiy 本体では `hermes_cli` ではなく **`aidiy_hermes`** を使います。

```json
{
  "CODE_AI1_NAME": "aidiy_hermes",
  "CODE_AIDIY_HERMES_MODEL": "auto"
}
```

### 連携箇所

- `backend_server/AIコア/AIコード_cli.py`
  - `aidiy_hermes` の実行ファイル探索
  - `--version` 実行
  - `aidiy_hermes -Q -z ...` 形式のコマンド構築
- `backend_server/conf/conf_json.py`
  - `CODE_AIDIY_HERMES_MODEL`
- `backend_server/conf/conf_model.py`
  - `get_code_models()["aidiy_hermes"]`
  - Ollama モデル一覧から動的生成
- `frontend_web` / `frontend_avatar` の AI 設定画面
  - code AI 選択肢として表示

### 注意

- `aidiy_hermes` は専用の `AiDiy_code_*.json` を持たず、モデル一覧は `conf_model.py` 側で動的に作る
- `_start.py` は `backend_hermes` を起動しない
- CodeAI 側は会話履歴を保持して再送するため、`aidiy_hermes` 自体に専用の `--continue` オプションを要求しない

---

## よく見る変更点

- TUI / slash command の調整 → `cli_main.py`, `hermes_cli/commands.py`
- ツール追加 / toolset 変更 → `tools/`, `base/toolsets.py`
- provider/model 解決 → `cli_main.py`
- AiDiy 本体連携 → `backend_server/AIコア/AIコード_cli.py`, `conf/conf_json.py`, `conf/conf_model.py`

---

## 参考コマンド

```bash
cd backend_hermes
.venv/Scripts/python.exe -m py_compile cli_main.py
.venv/Scripts/python.exe cli_main.py --version
.venv/Scripts/python.exe cli_main.py --help
.venv/Scripts/python.exe cli_main.py --list-tools
```
