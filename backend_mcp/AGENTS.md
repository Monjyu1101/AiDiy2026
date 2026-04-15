# backend_mcp 実装要点まとめ

## 本書の目的

このファイルは **backend_mcp（MCP サーバー）の実装詳細** を記載したドキュメントです。

**関連ドキュメント：**
- **[../CLAUDE.md](../CLAUDE.md)** - Claude Code向けインデックス（プロジェクト全体概要）
- **[../AGENTS.md](../AGENTS.md)** - プロジェクト全体方針
- **[../backend_server/AGENTS.md](../backend_server/AGENTS.md)** - バックエンド API 実装詳細

---

## 概要

`backend_mcp` は **Chrome DevTools MCP サーバー** です。

Claude Agent SDK（`claude_sdk`）がブラウザを操作するための MCP（Model Context Protocol）ブリッジとして機能します。
複数の AIコードエージェントが **同一の Chrome インスタンスを共有** できる設計になっています。
また、`mcp_stdio.py` により **Codex 向け stdio ブリッジ** も提供できます。

### 主な機能

- Chrome DevTools Protocol を MCP として SSE 経由で公開
- 複数クライアントが同一 Chrome を共有（subprocess は 1 つだけ）
- AIによるブラウザ自動操作（スクリーンショット・クリック・ナビゲーション・DOM取得等）

---

## ポート・エンドポイント

| 項目 | 値 |
|------|---|
| ポート | `8095` |
| SSE エンドポイント | `http://localhost:8095/aidiy_chrome_devtools/sse` |
| POST エンドポイント | `http://localhost:8095/aidiy_chrome_devtools/messages` |
| Chrome デバッグポート | `9222` |

アクセスは **localhost のみ許可**（127.0.0.1 / ::1）。外部からの接続は 403 で拒否。

---

## ファイル構成

```
backend_mcp/
├── mcp_main.py          # メインサーバー（FastAPI + SSE + subprocess管理）
├── mcp_stdio.py         # Codex 向け stdio <-> SSE ブリッジ
├── mcp_proc/
│   └── chrome_manager.py  # Chrome プロセス管理
├── log_config.py        # ログ設定（UTF-8 出力対応）
├── pyproject.toml       # Python 依存関係
├── package.json         # Node.js 依存関係（chrome-devtools-mcp）
└── node_modules/
    └── chrome-devtools-mcp/  # Chrome DevTools MCP 実装
```

---

## アーキテクチャ

```
Claude Agent SDK (claude_sdk)
    │
    │  MCP (SSE)
    ▼
mcp_main.py (port 8095)
    │
    │  subprocess (stdin/stdout)
    ▼
node chrome-devtools-mcp
    │
    │  Chrome DevTools Protocol (port 9222)
    ▼
Chrome ブラウザ
```

- Claude Agent SDK は `ClaudeAgentOptions.mcp_servers` に SSE エンドポイントを渡す
- `mcp_main.py` が Node.js の `chrome-devtools-mcp` を subprocess として起動・管理
- 複数の SSE クライアント（AIエージェント）が同じ subprocess を共有
- subprocess の stdout は全クライアントにブロードキャスト

Codex 用の経路:

```
Codex
    │
    │  MCP (stdio)
    ▼
mcp_stdio.py
    │
    │  MCP (SSE)
    ▼
mcp_main.py (port 8095)
```

---

## MCP 設定ファイル

`backend_server/_config/AiDiy_mcp.json` で定義：

```json
{
  "mcpServers": {
    "aidiy_chrome_devtools": {
      "type": "sse",
      "url": "http://localhost:8095/aidiy_chrome_devtools/sse"
    }
  }
}
```

- `conf/conf_model.py` の `_load_mcp_config()` が起動時に読み込む
- `AIコア/AIコード_claude.py` の `_load_mcp_servers()` も直接読み込む
- Claude Agent SDK へは `ClaudeAgentOptions(mcp_servers=..., permission_mode="bypassPermissions")` で渡す

---

## 起動方法

```bash
# _start.py 経由（推奨）
python _start.py   # 対話形式でバックエンド(mcp)を選択

# 手動起動
cd backend_mcp
.venv/Scripts/python.exe -m uvicorn mcp_main:app --host 0.0.0.0 --port 8095

# uv 経由
cd backend_mcp
uv run uvicorn mcp_main:app --host 0.0.0.0 --port 8095

# Codex 用 stdio ブリッジ
cd backend_mcp
.venv/Scripts/python.exe mcp_stdio.py --sse-url http://localhost:8095/aidiy_chrome_devtools/sse
```

---

## 依存関係セットアップ

```bash
# Python 依存関係
cd backend_mcp
uv sync

# Node.js 依存関係（chrome-devtools-mcp）
cd backend_mcp
npm install
```

---

## 環境変数

| 変数名 | デフォルト | 説明 |
|--------|-----------|------|
| `CHROME_DEBUG_PORT` | `9222` | Chrome デバッグポート |
| `MCP_PORT` | `8095` | MCP サーバーポート |
| `MCP_MOUNT_PATH` | `/aidiy_chrome_devtools` | SSE マウントパス |

---

## ログ

- ファイル: `backend_mcp/temp/logs/yyyymmdd.hh0000.mcp_main.log`
- コンソール出力は UTF-8 固定（Windows パイプ経由の文字化け対策済み）
- `log_config.py` の `StreamHandler` は `io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')` でラップ

---

## 注意事項

- `mcp_main.py` は Chrome が未起動の場合、最初の SSE 接続時に自動起動する
- Chrome は `ChromeManager` が管理（`mcp_proc/chrome_manager.py`）
- subprocess（chrome-devtools-mcp）が終了すると全 SSE クライアントに終了通知が送られる
- `permission_mode="bypassPermissions"` は AIコードエージェント（backend_server 側）の設定であり、MCP サーバー自体のアクセス制御はローカルホスト制限で行う
- `mcp_stdio.py` 自体は localhost 上の SSE サーバーへ接続するだけで、Chrome 管理は `mcp_main.py` 側に寄せる
