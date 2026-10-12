import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from mcp.server.mcpserver import MCPServer

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools_proc import tools_ffmpeg, tools_chat, tools_agents
from tools_proc.ffmpeg_control import FfmpegControl


def ffmpeg(working=()):
    service = object.__new__(FfmpegControl)
    service.version_info = {name: {"ok": name in working, "error": "missing"} for name in ("ffmpeg", "ffprobe", "ffplay")}
    service.ffmpeg_path, service.ffprobe_path, service.ffplay_path = "ffmpeg", "ffprobe", "ffplay"
    service.default_timeout_sec, service.default_play_timeout_sec = 60, 60
    return service


class AvailabilityMCPTests(unittest.IsolatedAsyncioTestCase):
    async def test_ffmpeg_unavailable_keeps_diagnostic(self):
        mcp = MCPServer("ffmpeg-test")
        tools_ffmpeg.register_tools(mcp, ffmpeg())
        self.assertEqual(set(mcp._tool_manager._tools), {"ffmpeg_versions"})
        self.assertIn("現在利用不可", mcp.instructions)
        result = json.loads(await mcp._tool_manager._tools["ffmpeg_versions"].fn())
        self.assertFalse(result["available"])
        self.assertEqual(result["status"], "NG")
        self.assertIn("checks", result)

    async def test_ffprobe_only_publishes_usable_functions(self):
        mcp = MCPServer("ffmpeg-test")
        tools_ffmpeg.register_tools(mcp, ffmpeg(("ffprobe",)))
        self.assertEqual(set(mcp._tool_manager._tools), {"ffmpeg_versions", "ffprobe_run", "get_media_duration"})
        self.assertIn("利用可能: ffprobe", mcp.instructions)
        self.assertTrue(json.loads(await mcp._tool_manager._tools["ffmpeg_versions"].fn())["available"])

    async def test_chat_and_code_keep_unavailable_diagnostic(self):
        for module, diagnostic in ((tools_chat, "chat_llms_config"), (tools_agents, "code_agents_config")):
            with self.subTest(module=module.__name__):
                service = Mock(version_info={"test": {"ok": False}})
                service.get_config.return_value = {"ai_versions": service.version_info}
                mcp = MCPServer("ai-test")
                module.register_tools(mcp, service)
                self.assertEqual(set(mcp._tool_manager._tools), {diagnostic})
                self.assertIn("現在利用不可", mcp.instructions)
                result = json.loads(await mcp._tool_manager._tools[diagnostic].fn())
                self.assertEqual(result["status"], "NG")
                self.assertFalse(result["available"])


class AvailabilityHTTPTests(unittest.TestCase):
    def test_missing_binary_returns_503_without_execution(self):
        service = ffmpeg(("ffprobe",))
        service.run_ffmpeg = AsyncMock()
        app = FastAPI()
        app.include_router(tools_ffmpeg.create_router(service))
        with TestClient(app) as client:
            self.assertTrue(client.post("/aidiy_ffmpeg_control/versions").json()["available"])
            for method in ("ffmpeg_run", "analyze_audio", "video_trimming", "ffplay_run"):
                response = client.post("/aidiy_ffmpeg_control/" + method, json={"args_str": "-version"})
                self.assertEqual(response.status_code, 503)
                self.assertIn("現在利用不可", response.json()["message"])
        service.run_ffmpeg.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
