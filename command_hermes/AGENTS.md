# command_hermes 実装概要

## 本書の目的

このファイルは `command_hermes` の位置づけ、構成、実装入口を示す概要ドキュメントです。
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
| Provider 一覧と選択ロジック | [`../.aidiy/knowledge/command_hermes,Provider一覧と選択ロジック.md`](../.aidiy/knowledge/command_hermes,Provider一覧と選択ロジック.md) |
| Slash Command 一覧と追加手順 | [`../.aidiy/knowledge/command_hermes,Slash Command一覧.md`](../.aidiy/knowledge/command_hermes,Slash Command一覧.md) |

## 概要

`command_hermes` は AiDiy に統合された on-demand のコードエージェント CLI です。

- 常駐 HTTP サーバーではない。
- 実行名は `aidiy_hermes`。
- `_start.py` の常駐起動対象ではない。
- `_setup.py` / `_cleanup.py` の対象。
- `backend_server` の AI コードパネルでは `CODE_AI*_NAME = "aidiy_hermes"` として呼び出される。

## 技術スタック

| 項目 | 内容 |
|------|------|
| 言語 | Python |
| 依存管理 | `pyproject.toml` / `uv sync --upgrade` |
| TUI | `prompt_toolkit` |
| 通信 | `requests`、`httpx`、OpenAI 互換 client、Claude API 連携 |
| 実行方式 | 単体 CLI / subprocess 呼び出し |

## Windows ホストでの動作

Windows ネイティブ実行では、`terminal` は Git Bash があれば使い、無い場合は PowerShell へフォールバックします。`LocalEnvironment` は snapshot 用の login shell を作らず、コマンドごとに軽量なシェルプロセスを起動します。

`file_operations.py`、`file_tools.py`、`terminal_tool.py`、`process_registry.py` は platform selector として動作します。Windows では対応する `*_win.py`、非 Windows では `*_linux.py` のどちらか一方だけを import します。`*_linux.py` は upstream / original に近い実装を残し、Windows 差分は `*_win.py` 側へ寄せます。

ファイル操作は Windows では `WindowsFileOperations` が Python の `pathlib` / `subprocess` を使って直接処理します。`read_file`、`write_file`、`search_files`、`patch` は `wc`、`sed`、`find` などの POSIX コマンドへ依存しないようにしています。

## Provider 概要

`cli_main.py` の provider は API provider と CLI bridge の両方を扱います。31 の provider overlay と 50 以上のエイリアスがあり、`--provider` / config / 環境変数 / `auto` の優先順位で解決します。

詳細な一覧と選択ロジックは `.aidiy/knowledge/command_hermes,Provider一覧と選択ロジック.md` を参照してください。

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
