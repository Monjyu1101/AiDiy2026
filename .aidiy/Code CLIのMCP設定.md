# Code CLIのMCP設定

## このメモを使う場面
- `claude` / `gemini` / `codex` をプロジェクトフォルダから起動したときに、特定の MCP を使わせたいとき
- CLI ごとに設定場所が違って混乱しやすいとき

## 結論
- `claude` はプロジェクト直下の `.mcp.json` を使う
- `gemini` はプロジェクト直下の `.gemini/settings.json` を使う
- `codex` は `~/.codex/config.toml` または project スコープの `.codex/config.toml` を使えるが、`url = ...` は **streamable HTTP** 用であり、SSE エンドポイントを直接は扱えない
- `backend_mcp` は SSE エンドポイントを公開しているため、現状の Codex にはそのまま設定しない
- `_setup.py` の `backend_mcp` 向け MCP 設定書き込み前に、ルート `.gitignore` へ `.claude/` と `.gemini/` を自動追記してローカル CLI 設定を同期対象から外す

## 今回の関連ファイル
- `.mcp.json`
- `.gemini/settings.json`
- `.gitignore`
- `_setup.py`
- `scripts/cli_bat/_claude-code_AiDiy.bat`
- `scripts/cli_bat/_codex_cli_AiDiy.bat`
- `C:\Users\admin\.codex\config.toml`

## 注意点
- `claude mcp add -s project` は `.mcp.json` を作る
- `gemini mcp add -s project` は `.gemini/settings.json` を作る
- `codex mcp add` はユーザー設定 `~/.codex/config.toml` に追記される
- Codex の `url = ...` は **streamable HTTP** サーバー向けで、`backend_mcp` のような SSE 専用エンドポイントへ向けると初期化に失敗する
- Windows では `codex.cmd -c "mcp_servers...='http://...'"` のような起動引数が、起動経路によって引用符崩れを起こすことがある
- `backend_mcp` を Codex から使いたい場合は、SSE→stdio / streamable HTTP のアダプタを別途挟む必要がある
- `.claude/` や `.gemini/` はローカル CLI が随時書き換えるため、プロジェクト配下に置く場合は ignore 前提で扱う

## 最低限の確認方法
- `claude mcp list`
- `gemini mcp list`
- `codex mcp list`
- `python _setup.py` の `backend_mcp の mcp機能を使えるよう構成しますか？` で Claude / Gemini 用設定を再生成できる
- `python _setup.py` 実行後にルート `.gitignore` に `.claude/` と `.gemini/` が存在する
