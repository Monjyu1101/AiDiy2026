# Code CLIのMCP設定

## このメモを使う場面
- `claude` / `gemini` / `codex` をプロジェクトフォルダから起動したときに、特定の MCP を使わせたいとき
- CLI ごとに設定場所が違って混乱しやすいとき

## 結論
- `claude` は主にグローバル `C:\Users\admin\.claude.json` を使う
- `gemini` はプロジェクト直下の `.gemini/settings.json` を使う
- `codex` は `~/.codex/config.toml` を使い、`backend_mcp/mcp_stdio.py` を **stdio server** として登録する
- Codex の `url = ...` は **streamable HTTP** 用であり、`backend_mcp` の SSE エンドポイントは直接は扱えない
- `backend_mcp` を Codex から使うときは `mcp_stdio.py --sse-url http://localhost:8095/aidiy_chrome_devtools/sse` を挟む
- `_setup.py` の `backend_mcp` 向け MCP 設定書き込み前に、ルート `.gitignore` へ `.claude/` と `.gemini/` を自動追記してローカル CLI 設定を同期対象から外す

## 今回の関連ファイル
- `.mcp.json`
- `.gemini/settings.json`
- `.gitignore`
- `_setup.py`
- `scripts/cli_bat/_claude-code_AiDiy.bat`
- `scripts/cli_bat/_codex_cli_AiDiy.bat`
- `C:\Users\admin\.codex\config.toml`
- `backend_mcp/mcp_stdio.py`

## 注意点
- `scripts/cli_bat/_claude-code_AiDiy.bat` は `--mcp-config` を付けず、Claude のグローバル設定をそのまま使って起動する
- Windows の `scripts/cli_bat/*.bat` では `.cmd` を `start` で直接起動せず、`call "%USERPROFILE%\\AppData\\Roaming\\npm\\*.cmd"` で実行するほうが構文エラーを避けやすい
- Claude のグローバル `C:\Users\admin\.claude.json` に旧 `chrome-devtools` が残っていると、`claude mcp list` で失敗表示が出る。現行の `aidiy_chrome_devtools` に移行したら必要に応じて手動で整理する
- `claude mcp add -s project` は `.mcp.json` を作る
- `gemini mcp add -s project` は `.gemini/settings.json` を作る
- `codex mcp add` はユーザー設定 `~/.codex/config.toml` に追記される
- Codex の `url = ...` は **streamable HTTP** サーバー向けで、`backend_mcp` のような SSE 専用エンドポイントへ向けると初期化に失敗する
- Codex に `backend_mcp` を登録するときは、`command = "<backend_mcp の python>"` と `args = ["<repo>\\backend_mcp\\mcp_stdio.py", "--sse-url", "http://localhost:8095/aidiy_chrome_devtools/sse"]` の stdio bridge 形にする
- Windows では `codex.cmd -c "mcp_servers...='http://...'"` のような起動引数が、起動経路によって引用符崩れを起こすことがある
- `python _setup.py` は Codex 用に `~/.codex/config.toml` へ `mcp_stdio.py` の stdio 設定を書き込み、`python _cleanup.py` は同 table を削除する
- `.claude/` や `.gemini/` はローカル CLI が随時書き換えるため、プロジェクト配下に置く場合は ignore 前提で扱う
- Gemini CLI の `settings.json` は BOM 付き UTF-8 だと `Unexpected token '﻿'` で起動失敗する。JSON 内容が正しく見えても、先頭バイトが `EF BB BF` なら BOM なし UTF-8 で保存し直す
- `python _cleanup.py` は `aidiy_chrome_devtools` だけを `~/.claude.json` / `~/.gemini/settings.json` / `~/.copilot/mcp-config.json` / `~/.codex/config.toml` から自動解除できるようにしておくと、他担当者へ引き渡す前の後始末が揃う

## 最低限の確認方法
- `claude mcp list`
- `gemini mcp list`
- `codex mcp list`
- `python _setup.py` の `backend_mcp の mcp機能を使えるよう構成しますか？` で Claude / Gemini / Copilot / Codex 用設定を再生成できる
- `python _setup.py` 実行後にルート `.gitignore` に `.claude/` と `.gemini/` が存在する
