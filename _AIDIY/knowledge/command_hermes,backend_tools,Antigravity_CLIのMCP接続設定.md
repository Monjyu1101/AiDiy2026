# Antigravity CLI の MCP 接続設定

> 文書: `command_hermes,backend_tools,Antigravity_CLIのMCP接続設定.md` | 実装: `backend_tools/_setup.py`, `backend_tools/_cleanup.py`

## このメモを使う場面

- Antigravity CLI (`agy`) の MCP 設定先や接続方式を確認するとき
- setup の生成内容や、旧 stdio 設定からの更新を検証するとき
- MCP の接続不良とツール実行の権限不足を切り分けるとき

## 設定先と接続方式

Antigravity CLI は `~/.gemini/config/mcp_config.json` をグローバル MCP 設定として読む。AiDiy の setup は `serverUrl` に Streamable HTTP の `/mcp` を指定する。

```json
{
  "mcpServers": {
    "aidiy_notification_sounds": {
      "serverUrl": "http://127.0.0.1:8095/aidiy_notification_sounds/mcp"
    }
  }
}
```

`backend_tools/_setup.py` の `configure_clients()` が、共通定義の `sse_url` の末尾を `/sse` から `/mcp` へ変換する。対象サーバーと除外対象は `MCP_MODULES` / `CODE_CLI_MCP_EXCLUDE` に従い、Codex と共通で `aidiy_image_generation` を除外する。Windows 限定の `aidiy_windows_control` は他 OS では登録しない。

設定生成自体に Python 仮想環境や `mcp_stdio.py` は不要。ツールを利用するときは `backend_tools` をポート 8095 で起動しておく。

## 旧設定の扱い

- 同名サーバーの `command` / `args` / `env` / `cwd` と旧形式の `type` / `url` / `httpUrl` を除去してから `serverUrl` を更新する。別サーバーやその他の設定項目は保持する。
- setup は旧設定先 `~/.gemini/antigravity-cli/mcp_config.json` へ書き込まない。旧ファイルを新設定先へ丸ごとコピーする処理も行わない。
- `backend_tools/_cleanup.py` は新旧両方の設定先から `aidiy_*` を解除し、他の MCP 登録を保持する。
- `mcp_stdio.py` 自体は、stdio 接続を選ぶクライアント向けの SSE ブリッジとして残る。

## 確認方法

```powershell
agy --version
agy mcp list
```

`agy mcp list` の `TYPE` が `http`、接続先が `http://127.0.0.1:8095/<名前>/mcp` であることを確認する。これは設定の読み込み確認なので、実接続は `agy` から対象 MCP ツールを呼び出して確かめる。

通知音で確認する場合は、`aidiy_notification_sounds.play_notification_sound` に `notification_type="完了", scene="plane"` を指定して 1 回呼び出す。CLI のツール結果と backend_tools のログを照合し、`status: ok` と再生記録を確認する。

非対話の `agy --print` は、確認が必要なツールを実行できずに終了する場合がある。これは HTTP の接続失敗とは分けて扱う。依頼された通知音だけを許可する場合は、権限設定 `~/.gemini/antigravity-cli/settings.json` の `permissions.allow` に `mcp(aidiy_notification_sounds/play_notification_sound)` を指定できる。テストのために追加した許可は検証後に取り除き、既存の権限設定は保持する。MCP 設定と権限設定ではディレクトリが異なる点に注意する。

## 公式仕様の参照先

- [MCP 設定](https://antigravity.google/docs/mcp/)
- [非対話モードと権限](https://antigravity.google/docs/cli/headless/)
- [権限ルール](https://antigravity.google/docs/permissions/)
