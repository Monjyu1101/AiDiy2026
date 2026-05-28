# backend_hermes の MCP SSE 接続

> 文書: `backend_hermes,backend_tools,MCP_SSE接続.md` | 実装: `backend_hermes/tools/mcp_tool.py`, `backend_hermes/cli_main.py`

## このメモを使う場面

- `aidiy_hermes` TUI で MCP サーバーが `sse — failed` または `http — failed` と表示される
- バナーに MCP ツールが表示されない / AI が MCP ツールを使えない
- `mcp_tool.py` の SSE 関連メソッドを確認・修正する
- `backend_hermes` を新版へ更新した後に MCP 接続が壊れた

## 構成

`backend_hermes` は `AiDiy_mcp.json` を自動読み込みして SSE 接続する。

```
backend_server/_config/AiDiy_mcp.json  ← MCPサーバーURL一覧
  ↓ _load_aidiy_mcp_servers()
tools/mcp_tool.py
  ↓ discover_mcp_tools() → register_mcp_servers() → _connect_server()
  ↓ MCPServerTask.run() → _run_sse() ← SSE長期接続
  ↓ _register_server_tools() → registry.register()
base/toolsets.py: _get_plugin_toolset_names() → "mcp-aidiy_*" ツールセット
base/model_tools.py: get_tool_definitions() → AI へ送るツール定義
```

## 必須メソッド（mcp_tool.py）

`MCPServerTask` に以下がすべて揃っていること。バージョンアップで欠落しやすい。

### `_is_sse()` / `_is_http()`

```python
def _is_sse(self) -> bool:
    return "url" in self._config and str(self._config.get("type", "")).lower() == "sse"

def _is_http(self) -> bool:
    return "url" in self._config and not self._is_sse()
```

`AiDiy_mcp.json` の設定は `"type": "sse"` を持つので `_is_sse()` が True になる。

### `_run_sse()`

```python
async def _run_sse(self, config: dict):
    from mcp.client.sse import sse_client
    url = config["url"]
    headers = dict(config.get("headers") or {})
    sampling_kwargs = self._sampling.session_kwargs() if self._sampling else {}

    async with sse_client(url, headers=headers) as (read, write):
        async with ClientSession(read, write, **sampling_kwargs) as session:
            await session.initialize()
            self.session = session
            await self._discover_tools()
            self._ready.set()
            await self._shutdown_event.wait()
```

`self._ready.set()` は `await self._discover_tools()` の後でなければならない。

### `run()` のトランスポート分岐

```python
if self._is_sse():
    await self._run_sse(config)
elif self._is_http():
    await self._run_http(config)
else:
    await self._run_stdio(config)
```

## cli_main.py への discover_mcp_tools() 追加

`main()` の `cli.run()` 直前に必要（インタラクティブモードのみ）:

```python
# Run interactive mode
try:
    from tools.mcp_tool import discover_mcp_tools
    discover_mcp_tools()
except Exception:
    logger.debug("MCP tool discovery failed at CLI startup", exc_info=True)
cli.run()
```

`discover_mcp_tools()` は完了するまで block する（タイムアウト 120s）。
その後 `cli.run()` → `show_banner()` → `get_mcp_status()` で接続済みサーバーがバナーに表示される。

## AiDiy_mcp.json の確認

```
backend_server/_config/AiDiy_mcp.json
```

```json
{
  "mcpServers": {
    "aidiy_chrome_devtools": {
      "type": "sse",
      "url": "http://localhost:8095/aidiy_chrome_devtools/sse"
    },
    ...
  }
}
```

`"type": "sse"` が必須。なければ `_load_aidiy_mcp_servers()` が `entry.setdefault("type", "sse")` で補完する。

## 確認方法

### Python スクリプトで直接確認

```powershell
Set-Location backend_hermes
.venv\Scripts\python.exe -c "
from tools.mcp_tool import discover_mcp_tools, get_mcp_status
result = discover_mcp_tools()
print('Registered tools count:', len(result))
for s in get_mcp_status():
    print(s)
"
```

期待値: 全サーバーが `'connected': True`、合計 108 ツール。

### TUI で確認

```powershell
aidiy_hermes
```

バナーに `aidiy_chrome_devtools  sse — ok (50 tools)` のような行が並べば正常。

## 注意点

- `_run_sse()` が欠落していると SSE サーバーへ HTTP(StreamableHTTP) で接続しようとして失敗する。
  TUI のバナーが `http — failed` になったら `_run_sse()` の欠落を疑う。
- `_MCP_SSE_AVAILABLE` フラグ: `from mcp.client.sse import sse_client` が失敗した場合にフォールバックする。
  `mcp` パッケージのバージョンによって import パスが変わることがあるため確認する。
- `check_fn` は `server.session is not None` で評価する。
  SSE 接続が切れると `session` が None に戻り、ツール呼び出し時に「サーバー未接続」エラーになる。
- `.cmd` ファイルは ASCII エンコードで保存する。UTF-8 BOM 付きで保存すると `'・ｿ@echo'` エラーで起動失敗する。
