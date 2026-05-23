# Code CLI の MCP 設定

> 文書: `backend_hermes,backend_mcp,CodeCLI_MCP設定.md` | 実装: `backend_hermes/`, `backend_mcp/mcp_main.py`

## このメモを使う場面
- Claude / Gemini / Codex / Antigravity などの Code CLI から AiDiy MCP を使わせる
- CLI ごとの MCP 設定ファイルの場所を確認する
- `backend_mcp` の SSE MCP を stdio クライアントへ接続する

## 設定場所

| CLI | 主な設定場所 | 備考 |
|-----|-------------|------|
| Claude | `C:\Users\admin\.claude.json`、または project `.mcp.json` | `claude mcp add -s project` は `.mcp.json` を作る |
| Gemini | project `.gemini/settings.json` | BOM なし UTF-8 で保存する |
| Antigravity | `C:\Users\admin\.gemini\antigravity-cli\mcp_config.json` | `mcp_stdio.py` を経由した stdio server として登録する（Codexと同様） |
| Codex | `C:\Users\admin\.codex\config.toml` | `mcp_stdio.py` を stdio server として登録する |
| Copilot | `C:\Users\admin\.copilot\mcp-config.json` | `_setup.py` / `_cleanup.py` の対象 |
| OpenCode | `C:\Users\admin\.config\opencode\opencode.json` | 公式 docs では `mcp` キー配下。`.opencode/` は agents / commands / plugins などのディレクトリ用途 |

## 関連ファイル
- `.mcp.json`
- `.gemini/settings.json`
- `.gitignore`
- `_setup.py`
- `_cleanup.py`
- `scripts/cli_bat/_claude-code_AiDiy.bat`
- `scripts/cli_bat/_codex_cli_AiDiy.bat`
- `backend_mcp/mcp_stdio.py`
- `C:\Users\admin\.codex\config.toml`
- `C:\Users\admin\.gemini\antigravity-cli\mcp_config.json`

## Codex / Antigravity から stdio ブリッジを介して AiDiy MCP を使う設定

Codex や Antigravity CLI からは、AiDiy の SSE エンドポイントを直接扱わず、 `backend_mcp/mcp_stdio.py` ブリッジスクリプトを挟んで stdio サーバとして登録します。

### Codex の設定例 (config.toml)
```toml
[mcp_servers.aidiy_chrome_devtools]
command = "<repo>\\backend_mcp\\.venv\\Scripts\\python.exe"
args = [
  "<repo>\\backend_mcp\\mcp_stdio.py",
  "--sse-url",
  "http://localhost:8095/aidiy_chrome_devtools/sse",
]
```

### Antigravity の設定例 (mcp_config.json)
```json
{
  "mcpServers": {
    "aidiy_chrome_devtools": {
      "command": "<repo>\\\\backend_mcp\\\\.venv\\\\Scripts\\\\python.exe",
      "args": [
        "<repo>\\\\backend_mcp\\\\mcp_stdio.py",
        "--sse-url",
        "http://localhost:8095/aidiy_chrome_devtools/sse"
      ]
    }
  }
}
```

他の AiDiy MCP も同様に `--sse-url` の URL を `/aidiy_sqlite/sse` などの正しいマウントパスへ変えて登録します。

## セットアップ/クリーンアップの方針

- `python _setup.py` は必要に応じて Claude / Gemini / Copilot / OpenCode / Codex / Antigravity 用 MCP 設定を生成する
- `python _cleanup.py` は AiDiy が追加した MCP 設定を削除する
- `.claude/` と `.gemini/` は CLI がローカルで更新するため、project 配下に置く場合は `.gitignore` に入れる

## Windows の注意点

- `scripts/cli_bat/*.bat` では `.cmd` を `start` で直接起動せず、`call "%USERPROFILE%\\AppData\\Roaming\\npm\\*.cmd"` で実行する
- `codex.cmd -c "mcp_servers...='http://...'"` のような起動引数は引用符崩れが起きやすい。永続設定は `config.toml` を優先する
- Gemini の `settings.json` は BOM 付き UTF-8 だと `Unexpected token` で起動失敗する。先頭バイトが `EF BB BF` なら BOM なし UTF-8 で保存し直す

## 注意点

- Claude のグローバル設定に旧 `chrome-devtools` が残ると `claude mcp list` で失敗表示になる。現行は `aidiy_chrome_devtools`
- OpenCode の公式なグローバル設定は `~/.config/opencode/opencode.json`。`.opencode/` は project / home 配下で agents、commands、plugins などを置く用途
- `scripts/cli_bat/_claude-code_AiDiy.bat` は `--mcp-config` を付けず、グローバル設定を使う前提
- Codex や Antigravity から AiDiy MCP へつなぐ場合は、`backend_mcp` と対象 SSE サーバーが起動済みであることを先に確認する
- ローカル CLI 設定はユーザー環境依存なので、project の同期対象へ入れない

## 確認方法

```powershell
claude mcp list
gemini mcp list
codex mcp list
python _setup.py
python _cleanup.py
```

`_setup.py` 実行後は `.gitignore` に `.claude/` と `.gemini/` が含まれること、Codex/Antigravity 設定では `mcp_stdio.py --sse-url ...` 形式になっていることを確認する。
