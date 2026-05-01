# backend_hermes 実装概要

## 本書の目的

このファイルは `backend_hermes` の位置づけ、構成、実装入口を示す概要ドキュメントです。
起動方法、CLI オプション、確認コマンドなどの HowTo は `.aidiy/knowledge` に移動しています。
AI エージェントは、本書に個別手順や一時的な作業メモを追記しないでください。
業務システム機能追加は `../docs/` の開発ガイドを優先し、コアシステム機能調整は `../.aidiy/knowledge/_index.md` を入口にします。

## HowTo 参照先

| 目的 | 参照先 |
|------|--------|
| `aidiy_hermes` の起動、provider、CLI 確認 | [`../.aidiy/knowledge/backendHermes運用手順.md`](../.aidiy/knowledge/backendHermes運用手順.md) |
| TUI、slash command、補完、spinner の調整 | [`../.aidiy/knowledge/HermesCLI_TUI調整手順.md`](../.aidiy/knowledge/HermesCLI_TUI調整手順.md) |
| Code CLI として AiDiy に追加・調整する | [`../.aidiy/knowledge/CodeCLI追加手順.md`](../.aidiy/knowledge/CodeCLI追加手順.md) |
| Code CLI のプロンプト整形 | [`../.aidiy/knowledge/CodeCLIプロンプト整形.md`](../.aidiy/knowledge/CodeCLIプロンプト整形.md) |
| CLI 出力の ANSI 制御コード対処 | [`../.aidiy/knowledge/CodeCLI表示ANSI制御コード対処.md`](../.aidiy/knowledge/CodeCLI表示ANSI制御コード対処.md) |

## 概要

`backend_hermes` は AiDiy に統合された on-demand のコードエージェント CLI です。

- 常駐 HTTP サーバーではない。
- 実行名は `aidiy_hermes`。
- `_start.py` の常駐起動対象ではない。
- `_setup.py` / `_cleanup.py` の対象。
- `backend_server` の AI コードパネルでは `CODE_AI*_NAME = "aidiy_hermes"` として呼び出される。

## 技術スタック

| 項目 | 内容 |
|------|------|
| 言語 | Python |
| 依存管理 | `requirements.txt` |
| TUI | `prompt_toolkit` |
| 通信 | `requests`、`httpx`、OpenAI 互換 client、Claude API 連携 |
| 実行方式 | 単体 CLI / subprocess 呼び出し |

## Provider 概要

`cli_main.py` の provider は、API provider と CLI bridge の両方を扱います。

| 種別 | 値 |
|------|----|
| API provider | `ollama`、`openai`、`openrt`、`gemini`、`freeai`、`claude` |
| CLI bridge | `claude_cli`、`codex_cli`、`gemini_cli`、`copilot_cli` |

既定 provider は `ollama` です。

## ディレクトリ構成

| パス | 役割 |
|------|------|
| `cli_main.py` | CLI エントリ、provider/model picker、slash command 処理 |
| `core/` | agent loop、prompt、display、retry |
| `base/` | 共通定数、utils、toolsets |
| `hermes_cli/` | slash command、TUI 補助、互換レイヤ |
| `tools/` | file / terminal / web / media / planning / process |
| `plugins/` | plugin 拡張 |
| `skills/`、`optional-skills/` | skill 資産 |
| `environments/` | 実行環境補助 |
| `temp/` | 一時状態 |

## AiDiy 連携

`aidiy_hermes` は `backend_server/AIコア/AIコード_cli.py` から subprocess で起動されます。
モデル設定は `CODE_AIDIY_HERMES_MODEL` を使い、モデル一覧は `backend_server/conf/conf_model.py` 側で動的生成します。

主な連携箇所:

- `backend_server/AIコア/AIコード_cli.py`
- `backend_server/conf/conf_json.py`
- `backend_server/conf/conf_model.py`
- `frontend_web` / `frontend_avatar` の AI 設定画面

## 変更時の入口

- TUI と slash command は `cli_main.py` と `hermes_cli/commands.py` を起点に確認する。
- tool 追加や toolset 変更は `tools/` と `base/toolsets.py` を確認する。
- AiDiy 本体連携は `backend_server/AIコア/AIコード_cli.py`、`conf_json.py`、`conf_model.py` を確認する。
