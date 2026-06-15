# backend_hermes MCP サーバー起動

> 文書: `backend_hermes,MCP_サーバー起動.md` | 実装: `backend_hermes/base/mcp_serve.py`, `backend_hermes/hermes_cli/mcp_config.py`

## このメモを使う場面

- Claude Code / Gemini / Codex などのコードエージェントから Hermes の会話機能を使わせたい
- `hermes mcp serve` の動作・提供ツールを確認する
- Code CLI の MCP 設定に `hermes` を追加する

## 概要

`hermes mcp serve` を実行すると backend_hermes が **stdio MCP サーバー** として起動し、
コードエージェントがメッセージ送受信・会話管理ツールを直接呼び出せるようになる。

```
hermes mcp serve          # stdio サーバー起動
hermes mcp serve -v       # verbose ログあり（stderr に出力）
```

## 提供ツール一覧（10ツール）

| ツール名 | 概要 |
|---------|------|
| `conversations_list` | 全プラットフォームの会話一覧を返す（platform / search フィルタ対応） |
| `conversation_get` | session_key で会話の詳細情報を取得する |
| `messages_read` | 会話のメッセージ履歴を読み込む（最新 N 件） |
| `attachments_fetch` | メッセージから画像・ファイル等の添付を抽出する |
| `events_poll` | カーソル以降の新着イベントを返す（ポーリング） |
| `events_wait` | 次のイベントまでブロックする（ロングポール、最大 5 分） |
| `messages_send` | `platform:chat_id` 形式のターゲットへメッセージを送信する |
| `channels_list` | 送信可能なチャネル一覧を返す（messages_send の target 候補） |
| `permissions_list_open` | 未処理の承認リクエスト一覧を返す |
| `permissions_respond` | 承認リクエストに `allow-once/allow-always/deny` で応答する |

EventBridge がバックグラウンドで `sessions.json` と `state.db` を 200ms 間隔でポーリングし、
新着メッセージをメモリキュー（最大 1000 件）に積む。ファイルの mtime が変わらない間はポーリングをスキップするため低負荷。

## ディスパッチの流れ

```
hermes mcp serve
  └─ main.py: cmd_mcp(args) → mcp_config.mcp_command(args)
       └─ action == "serve"
            └─ mcp_serve.run_mcp_server()
                 ├─ EventBridge.start()   # バックグラウンドポーリング開始
                 ├─ create_mcp_server()   # FastMCP で 10 ツールを登録
                 └─ server.run_stdio_async()  # stdio トランスポートで待機
```

## Code CLI への登録方法

### Claude Code（グローバル設定）

```json
// C:\Users\admin\.claude.json の mcpServers に追加
{
  "mcpServers": {
    "hermes": {
      "command": "hermes",
      "args": ["mcp", "serve"]
    }
  }
}
```

または Claude Code の CLI で:

```powershell
claude mcp add hermes -- hermes mcp serve
```

### Claude Code（プロジェクト設定）

プロジェクトルートに `.mcp.json` を作成:

```json
{
  "mcpServers": {
    "hermes": {
      "command": "hermes",
      "args": ["mcp", "serve"]
    }
  }
}
```

### 他の Code CLI

| CLI | 設定場所 | 設定例 |
|-----|---------|--------|
| Gemini | `.gemini/settings.json` | `{"mcpServers": {"hermes": {"command": "hermes", "args": ["mcp", "serve"]}}}` |
| Codex | `~/.codex/config.toml` | `[mcp_servers.hermes]` / `command = "hermes"` / `args = ["mcp", "serve"]` |

## 確認方法

### CLI での確認

```powershell
# Claude Code の場合
claude mcp list
# → hermes が表示されること

# ツール一覧確認
claude mcp get hermes
```

### Python で直接テスト

```powershell
Set-Location backend_hermes
.venv\Scripts\python.exe -c "
from base.mcp_serve import create_mcp_server
srv = create_mcp_server()
tools = srv._tool_manager.list_tools()
print('Tools:', [t.name for t in tools])
"
```

## 注意点

- `mcp` パッケージが必要: `pip install 'mcp'`。インストールなしで起動しようとすると ImportError で停止する。
- `FastMCP` は `mcp.server.fastmcp` から import する（バージョンによって `mcp.server.fastmcp` → `fastmcp` にパスが変わることがある）。
- `hermes mcp serve` は stdio サーバーなので Code CLI が子プロセスとして起動する。プロセスが落ちると接続も切れる。
- `EventBridge` は `SessionDB` が起動時に利用可能でないとポーリングを無効化してメッセージイベントが届かなくなる。Hermes 本体が動いている状態で接続すること。
- `hermes mcp serve` は Hermes が **クライアントとして** AiDiy MCP に接続するフロー（`mcp_tool.py`）とは別の独立した機能。混同しないこと（→ SSE 接続は [`backend_hermes,backend_tools,MCP_SSE接続.md`](./backend_hermes,backend_tools,MCP_SSE接続.md) 参照）。
