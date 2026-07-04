# Antigravity CLI の stdio 型 MCP 接続設定

> 文書: `command_hermes,backend_tools,Antigravity_CLIのstdio型MCP接続設定.md` | 実装: `_setup.py`, `_cleanup.py`

## このメモを使う場面

- Antigravity CLI (`agy`) において MCP 設定を変更・検証するとき
- `_setup.py` の MCP 接続方式（SSE vs stdio）を編集するとき
- 複数の接続パラメータ（`serverUrl` と `command`/`args`）の混在による動作競合を防ぎたいとき

## 接続方式の変更背景

従来の Antigravity CLI 向けの設定 (`~/.gemini/antigravity-cli/mcp_config.json`) は、他の JSON 系設定（Claude や Copilot など）と同様に、以下のような直接的な SSE 接続型でした。

```json
"aidiy_chrome_devtools": {
  "serverUrl": "http://localhost:8095/aidiy_chrome_devtools/sse"
}
```

しかし、Antigravity CLI において stdio 接続型を使用させたい場合、OpenAI Codex と同様にローカルで `backend_tools/mcp_stdio.py` ブリッジスクリプトを呼び出す stdio 接続スキーマへ切り替える必要があります。

## 設定方法と変更箇所

### 1. `_setup.py` での設定注入

`_setup.py` の `configure_backend_tools_clients` 関数内で、Antigravity 用の設定を以下の通り stdio 型で書き込むように変更します。

```python
    # 4) Antigravity (mcpServers - stdio型)
    antigravity_mcp = get_antigravity_mcp_config_path()
    print_info(f"[Antigravity] {antigravity_mcp}")

    python_path = find_python_in_env(backend_tools_DIR, backend_tools_ENV_CANDIDATES)
    script_path = backend_tools_DIR / "mcp_stdio.py"

    if python_path is None or not script_path.exists():
        print_error("Antigravity 設定用の Python 仮想環境または mcp_stdio.py が見つかりません。")
        all_ok = False
    else:
        # 古い serverUrl 設定などをクリアするために、いったん mcp_config.json の serverUrl キーを削除する
        try:
            if antigravity_mcp.exists():
                data = load_json_dict_file(antigravity_mcp)
                servers_dict = data.get("mcpServers", {})
                if isinstance(servers_dict, dict):
                    for sn, _ in servers:
                        if sn in servers_dict and isinstance(servers_dict[sn], dict):
                            servers_dict[sn].pop("serverUrl", None)
                    data["mcpServers"] = servers_dict
                    write_json_file(antigravity_mcp, data)
        except Exception as e:
            print_warning(f"Antigravity の旧 serverUrl 設定削除中にエラーが発生しました: {e}")

        antigravity_entries = []
        for sn, url in servers:
            config = {
                "command": str(python_path),
                "args": [
                    str(script_path),
                    "--sse-url",
                    url
                ]
            }
            antigravity_entries.append((sn, config))
        all_ok &= upsert_json_mcp_servers(antigravity_mcp, antigravity_entries)
```

### 2. クリーンアップへの影響 (`_cleanup.py`)

`_cleanup.py` では `remove_json_mcp_servers_by_prefix` 関数を使用してプレフィックス一致 (例: `aidiy_`) でサーバー名を削除するため、設定が stdio スキーマに変更された後も **コード修正なしで正常にクリーンアップ可能** です。

---

## 運用の注意点

> [!IMPORTANT]
> **旧設定キー (`serverUrl`) の競合防止**
> JSON 形式の MCP 設定ファイルを辞書マージ方式で更新する際、以前の `"serverUrl"` キーが残っていると、一部の CLI クライアントが stdio と SSE のどちらの接続方式を使用すべきか判断できず、接続エラーの原因になります。
> 新しい設定を `upsert_json_mcp_servers` する前に、必ず既存の該当サーバーエントリーから `serverUrl` キーを `pop` などで明示的に削除してください。

## 確認方法

設定ファイルが正しく stdio スキーマになっているかは、以下のファイルを開いて直接確認します。

- パス: `%USERPROFILE%\.gemini\antigravity-cli\mcp_config.json`
- 期待される記述例:
  ```json
  "aidiy_chrome_devtools": {
    "command": "D:\\OneDrive\\_sandbox\\AiDiy2026\\backend_tools\\.venv\\Scripts\\python.exe",
    "args": [
      "D:\\OneDrive\\_sandbox\\AiDiy2026\\backend_tools\\mcp_stdio.py",
      "--sse-url",
      "http://localhost:8095/aidiy_chrome_devtools/sse"
    ]
  }
  ```
