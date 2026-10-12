from __future__ import annotations

import sys
import json
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


BACKEND_TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_TOOLS_DIR))

import tools_main  # noqa: E402


class PlatformRegistrationTests(unittest.TestCase):
    def test_windows_control_is_only_published_on_windows(self) -> None:
        windows = sys.platform == "win32"
        # 起動時の外部API呼び出しは別の実接続テストで検証する。
        availability = {"openai_decisions": {"ok": True, "model": "gpt-6-luna"}, "openai_oauth": {"ok": False, "model": "gpt-6-luna"}}
        with patch.object(tools_main.decisions, "availability", availability), patch.object(tools_main.decisions, "check_availability", new=AsyncMock(return_value={})) as startup_check, TestClient(tools_main.app) as client:
            startup_check.assert_awaited_once_with(timeout_sec=15)
            names = client.get("/").json()["mcps"]
            self.assertEqual(len(names), 20 if windows else 19)
            self.assertIn("aidiy_decisions_check", names)
            self.assertEqual("aidiy_windows_control" in names, windows)
            self.assertEqual(
                client.get("/aidiy_windows_control/ping").status_code,
                200 if windows else 404,
            )
            self.assertEqual(client.get("/aidiy_sqlite/ping").status_code, 200)
            self.assertEqual(client.get("/aidiy_decisions_check/ping").status_code, 200)
            names = {tool["name"] for tool in client.get("/aidiy_decisions_check/list").json()["tools"]}
            self.assertEqual(names, {"decisions_config", "decisions_check"})

            # 新規MCPのHTTP transportを実際にinitializeし、ツール呼出しまで確認する。
            headers = {"Host": "127.0.0.1:8095", "Accept": "application/json, text/event-stream"}
            endpoint = "/aidiy_decisions_check/mcp"
            response = client.post(endpoint, headers=headers, json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": tools_main.LATEST_PROTOCOL_VERSION, "capabilities": {}, "clientInfo": {"name": "decision-test", "version": "1"}}})
            self.assertEqual(response.status_code, 200, response.text)
            headers["Mcp-Session-Id"] = response.headers["mcp-session-id"]
            headers["MCP-Protocol-Version"] = tools_main.LATEST_PROTOCOL_VERSION
            response = client.post(endpoint, headers=headers, json={"jsonrpc": "2.0", "method": "notifications/initialized"})
            self.assertEqual(response.status_code, 202)
            meta = {"io.modelcontextprotocol/protocolVersion": tools_main.LATEST_PROTOCOL_VERSION, "io.modelcontextprotocol/clientCapabilities": {}}
            headers.update({"mcp-method": "tools/call", "mcp-name": "decisions_config"})
            response = client.post(endpoint, headers=headers, json={"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "decisions_config", "arguments": {}, "_meta": meta}})
            self.assertEqual(response.status_code, 200, response.text)
            messages = [json.loads(line[5:].strip()) for line in response.text.splitlines() if line.startswith("data:")]
            payload = messages[-1] if messages else response.json()
            self.assertFalse(payload["result"].get("isError"), payload)
            self.assertIn("openai_decisions", json.dumps(payload))

            # 全方式が無効なら実行は一覧から消え、MCP接続時に利用不可が伝わる。
            availability["openai_decisions"]["ok"] = False
            tools_main.tools_decisions.register_tools(tools_main.mcp_dj, tools_main.decisions)
            tools = client.get("/aidiy_decisions_check/list").json()["tools"]
            self.assertEqual([tool["name"] for tool in tools], ["decisions_config"])
            response = client.post(endpoint, headers={"Host": "127.0.0.1:8095", "Accept": "application/json, text/event-stream"}, json={"jsonrpc": "2.0", "id": 3, "method": "initialize", "params": {"protocolVersion": tools_main.LATEST_PROTOCOL_VERSION, "capabilities": {}, "clientInfo": {"name": "unavailable-test", "version": "1"}}})
            self.assertEqual(response.status_code, 200, response.text)
            messages = [json.loads(line[5:].strip()) for line in response.text.splitlines() if line.startswith("data:")]
            payload = messages[-1] if messages else response.json()
            self.assertIn("現在利用不可", payload["result"]["instructions"])


if __name__ == "__main__":
    unittest.main()
