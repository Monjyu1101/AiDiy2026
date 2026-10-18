import json
from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock, patch

import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient
from mcp.server.mcpserver import MCPServer

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools_proc.decisions_check import Decision, DecisionError
from tools_proc.tools_decisions import check_startup, create_router, register_tools

REQUEST = {"model": "openai_decisions/gpt-6-luna", "input": "blue", "questions": [{"name": "blue", "type": "predicate", "instructions": "blue?"}]}


def service():
    instance = Decision(config={"openai_key_id": "test"}, transport=httpx.MockTransport(lambda req: httpx.Response(200, json={"answers": [{"name": "blue", "type": "predicate", "probability": 1}]})))
    instance.availability = {"openai_decisions": {"ok": True, "model": "gpt-6-luna"}, "openai_oauth": {"ok": False, "model": "gpt-6-luna", "reason": "認証なし"}}
    return instance


class DecisionHTTPTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        self.service = service()
        app.include_router(create_router(self.service))
        self.client = TestClient(app)

    def test_http_check(self):
        response = self.client.post("/aidiy_decisions_check/check", json=REQUEST)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["answers"][0]["probability"], 1)

    def test_invalid_input_and_provider(self):
        response = self.client.post("/aidiy_decisions_check/check", json=dict(REQUEST, questions=[]))
        self.assertEqual(response.status_code, 422)
        response = self.client.post("/aidiy_decisions_check/check", json=dict(REQUEST, model="unknown/m"))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["status"], "NG")

    def test_docs_and_config(self):
        self.assertEqual(self.client.get("/aidiy_decisions_check/docs").status_code, 200)
        self.assertEqual(self.client.get("/aidiy_decisions_check/config").status_code, 200)

    def test_unavailable_returns_status_and_blocks_execution(self):
        self.service.availability["openai_decisions"]["ok"] = False
        config = self.client.get("/aidiy_decisions_check/config").json()
        self.assertEqual(config["status"], "NG")
        self.assertIn("現在利用不可", config["message"])
        with patch.object(self.service, "実行", new=AsyncMock()) as execute:
            response = self.client.post("/aidiy_decisions_check/check", json=REQUEST)
        self.assertEqual(response.status_code, 503)
        execute.assert_not_awaited()


class DecisionMCPTests(unittest.IsolatedAsyncioTestCase):
    async def test_startup_pending_is_info_and_oauth_success_publishes_execution(self):
        instance = service()
        instance.availability = {}
        mcp = MCPServer("decision-startup")
        with self.assertLogs("tools_proc.tools_decisions", level="INFO") as pending:
            register_tools(mcp, instance)
        self.assertEqual(set(mcp._tool_manager._tools), {"decisions_config"})
        self.assertTrue(all(record.levelname == "INFO" for record in pending.records))
        self.assertIn("起動チェック待ち", "\n".join(pending.output))
        self.assertNotIn("実行ツールは非公開", "\n".join(pending.output))

        async def finish_check(timeout_sec):
            self.assertEqual(timeout_sec, 15)
            instance.availability = {
                "openai_decisions": {"ok": False, "model": "gpt-6-luna", "reason": "APIキーなし"},
                "openai_oauth": {"ok": True, "model": "gpt-6-luna", "reason": "おはよう → 挨拶 を確認"},
            }
            return instance.availability

        with patch.object(instance, "check_availability", side_effect=finish_check), self.assertLogs("tools_proc.tools_decisions", level="INFO") as completed:
            await check_startup(instance)
            register_tools(mcp, instance)
        self.assertIn("decisions_check", mcp._tool_manager._tools)
        self.assertIn("実行ツールを公開しました", "\n".join(completed.output))
        self.assertIn("openai_oauth/gpt-6-luna", "\n".join(completed.output))
        self.assertNotIn("実行ツールは非公開", "\n".join(completed.output))

    async def test_completed_failed_check_still_warns_and_hides_execution(self):
        instance = service()
        instance.availability["openai_decisions"]["ok"] = False
        mcp = MCPServer("decision-unavailable")
        with self.assertLogs("tools_proc.tools_decisions", level="WARNING") as failed:
            register_tools(mcp, instance)
        self.assertIn("実行ツールは非公開", "\n".join(failed.output))
        self.assertEqual(set(mcp._tool_manager._tools), {"decisions_config"})

    async def test_auto_uses_oauth_first_and_native_when_oauth_unavailable(self):
        for oauth_ok in (True, False):
            with self.subTest(oauth_ok=oauth_ok):
                instance = service()
                instance.availability["openai_oauth"]["ok"] = oauth_ok
                def handler(req):
                    self.assertEqual(json.loads(req.content)["model"], "gpt-6-luna")
                    answers = [{"type": "predicate", "name": "blue", "probability": 1}]
                    if oauth_ok:
                        self.assertIn("/codex/responses", str(req.url))
                        event = {"type": "response.completed", "response": {"status": "completed", "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps({"answers": answers})}]}]}}
                        return httpx.Response(200, content="data: " + json.dumps(event) + "\n\n")
                    self.assertIn("/v1/decisions", str(req.url))
                    return httpx.Response(200, json={"answers": answers})
                instance.transport = httpx.MockTransport(handler)
                mcp = MCPServer("decision-test")
                register_tools(mcp, instance)
                with patch("AIコア.AI判断_openai_jsonchat.oauth_headers", return_value={"Authorization": "Bearer test"}):
                    result = await mcp._tool_manager._tools["decisions_check"].fn(**dict(REQUEST, model="auto"))
                self.assertEqual(result["data"]["ai_name"], "openai_oauth" if oauth_ok else "openai_decisions")
                self.assertEqual(instance.get_config()["default_model"], result["data"]["model"])

    async def test_mcp_uses_file_defaults_and_explicit_model_wins(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "AiDiy_key.json"
            config = {"DECISION_AI_NAME": "openai_decisions", "DECISION_AI_MODEL": "configured-model", "openai_key_id": "test"}
            path.write_text(json.dumps(config), encoding="utf-8")
            models = []
            def handler(req):
                self.assertIn("/v1/decisions", str(req.url))
                models.append(json.loads(req.content)["model"])
                return httpx.Response(200, json={"answers": [{"name": "blue", "type": "predicate", "probability": 1}]})
            instance = Decision(config_path=path, transport=httpx.MockTransport(handler))
            instance.availability = {"openai_decisions": {"ok": True, "model": "configured-model"}, "openai_oauth": {"ok": True, "model": "configured-model"}}
            mcp = MCPServer("decision-config-test")
            register_tools(mcp, instance)
            tool = mcp._tool_manager._tools["decisions_check"]
            base = {key: value for key, value in REQUEST.items() if key != "model"}
            for params, expected in (({}, "configured-model"), ({"model": "auto"}, "configured-model"), ({"ai_model": "explicit-model"}, "explicit-model"), ({"model": "openai_decisions/explicit-model"}, "explicit-model")):
                result = await tool.fn(**base, **params)
                self.assertEqual(result["data"]["ai_model"], expected)
                self.assertEqual(models[-1], expected)
            shown = await mcp._tool_manager._tools["decisions_config"].fn()
            self.assertEqual(shown["configured_defaults"]["DECISION_AI_MODEL"], "configured-model")
            self.assertEqual(shown["default_model"], "openai_decisions/configured-model")

    async def test_mcp_schema_and_execution(self):
        mcp = MCPServer("aidiy_decisions_check", warn_on_duplicate_tools=False)
        register_tools(mcp, service())
        tools = mcp._tool_manager._tools
        self.assertIn("decisions_check", tools)
        self.assertIn("decisions_config", tools)
        self.assertIn("questions", tools["decisions_check"].parameters["required"])
        result = await tools["decisions_check"].fn(**REQUEST)
        self.assertEqual(result["status"], "OK")
        self.assertEqual(result["data"]["answers"][0]["probability"], 1)

    async def test_google_methods_are_exposed_and_execute_json_through_mcp(self):
        for name in ("freeai_chat", "gemini_chat"):
            def handler(req):
                self.assertIn("generativelanguage.googleapis.com", str(req.url))
                return httpx.Response(200, json={"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": json.dumps({"answers": [{"name": "blue", "type": "predicate", "probability": 1}]})}]}}]})
            instance = Decision(config={"DECISION_AI_NAME": name, "gemini_key_id": "fixture"}, transport=httpx.MockTransport(handler))
            instance.availability = {name: {"ok": True, "model": "gemini-flash-lite-latest"}}
            mcp = MCPServer("google-decision-test")
            register_tools(mcp, instance)
            result = await mcp._tool_manager._tools["decisions_check"].fn(**dict(REQUEST, model="auto"))
            self.assertEqual(result["data"]["ai_name"], name)
            config = await mcp._tool_manager._tools["decisions_config"].fn()
            self.assertEqual({item["ai_name"] for item in config["providers"]}, {"openai_oauth", "openai_decisions", "freeai_chat", "gemini_chat"})

    async def test_unavailable_hides_execution_and_keeps_diagnostics(self):
        instance = service()
        mcp = MCPServer("aidiy_decisions_check", warn_on_duplicate_tools=False)
        register_tools(mcp, instance)
        previous_tool = mcp._tool_manager._tools["decisions_check"]
        instance.availability["openai_decisions"]["ok"] = False
        register_tools(mcp, instance)
        self.assertEqual(set(mcp._tool_manager._tools), {"decisions_config"})
        self.assertIn("現在利用不可", mcp.instructions)
        result = await mcp._tool_manager._tools["decisions_config"].fn()
        self.assertFalse(result["available"])
        self.assertIn("認証なし", json.dumps(result, ensure_ascii=False))
        with patch.object(instance, "実行", new=AsyncMock()) as execute:
            with self.assertRaisesRegex(Exception, "現在利用不可"):
                await previous_tool.fn(**REQUEST)
        execute.assert_not_awaited()

    async def test_one_healthy_provider_restores_execution(self):
        instance = service()
        mcp = MCPServer("aidiy_decisions_check", warn_on_duplicate_tools=False)
        for healthy in ("openai_decisions", "openai_oauth"):
            for name, info in instance.availability.items():
                info["ok"] = name == healthy
            register_tools(mcp, instance)
            self.assertIn("decisions_check", mcp._tool_manager._tools)
            self.assertNotIn("現在利用不可", mcp.instructions)

    async def test_unchecked_and_broken_config_still_explain_unavailable(self):
        instance = service()
        instance.availability = {}
        mcp = MCPServer("aidiy_decisions_check", warn_on_duplicate_tools=False)
        register_tools(mcp, instance)
        self.assertNotIn("decisions_check", mcp._tool_manager._tools)
        with patch.object(instance, "get_config", side_effect=DecisionError("設定読込エラー")):
            result = await mcp._tool_manager._tools["decisions_config"].fn()
        self.assertEqual(result["status"], "NG")
        self.assertIn("現在利用不可", result["message"])
        self.assertEqual(result["config_error"], "設定読込エラー")


if __name__ == "__main__":
    unittest.main()
