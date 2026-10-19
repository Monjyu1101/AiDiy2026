import importlib
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend_server"))
sys.path.insert(0, str(ROOT / "backend_tools"))

from AIコア.AI応答 import 応答正規化, エラー応答, エラー応答判定
from tools_proc.chat_llm import ChatLLM
from tools_proc.code_agents import CodeAgents


class AIResponseErrors(unittest.IsolatedAsyncioTestCase):
    def test_final_response_contract(self):
        for value in (None, "", " \n", "!", "! 任意のエラー", " \n!利用上限", "（応答なし）"):
            with self.subTest(value=value):
                self.assertTrue(エラー応答判定(value))
                self.assertTrue(応答正規化(value).startswith("!"))
        self.assertEqual(エラー応答("認証に失敗"), "! 認証に失敗")
        self.assertEqual(エラー応答("! 認証に失敗"), "! 認証に失敗")
        self.assertEqual(エラー応答(), "!")
        self.assertFalse(エラー応答判定("おはよう！"))
        self.assertEqual(応答正規化("おはよう！"), "おはよう！")

    async def test_chat_providers_report_stopped_state_as_error(self):
        for provider in ("gemini", "openrt", "ollama", "local", "openai"):
            with self.subTest(provider=provider):
                module = importlib.import_module(f"AIコア.AIチャット_{provider}")
                instance = module.ChatAI(api_key="test-key")
                instance.is_alive = False
                reply = await instance.実行("おはよう")
                self.assertTrue(reply.startswith("!"), reply)
                self.assertIn("停止状態", reply)

    async def test_chat_api_exception_and_timeout_never_become_success(self):
        for provider in ("openrt", "ollama", "local", "openai"):
            for mode in ("exception", "timeout"):
                with self.subTest(provider=provider, mode=mode):
                    module = importlib.import_module(f"AIコア.AIチャット_{provider}")
                    ai = module.ChatAI(api_key="test-key")
                    ai.is_alive = True

                    def sync(**kwargs):
                        if mode == "exception":
                            raise RuntimeError("認証失敗")
                        kwargs["タイムアウトフラグ"].set()
                        return "途中の回答"

                    with patch.object(ai, "_同期実行", side_effect=sync):
                        result = await ai.実行("おはよう")
                    self.assertTrue(result.startswith("!"), result)
                    self.assertIn("認証失敗" if mode == "exception" else "タイムアウト", result)

    async def test_mcp_chat_plain_and_self_loop_classify_final_responses(self):
        for value in (None, "", " \n", "!", "! 任意の失敗", "おはよう！"):
            for loop in (False, True):
                with self.subTest(value=value, loop=loop):
                    ai = SimpleNamespace(実行=AsyncMock(return_value=value), 終了=AsyncMock())
                    service = object.__new__(ChatLLM)
                    service._sessions = {}
                    service._build_instance = AsyncMock(return_value=ai)
                    if loop:
                        result = await service._run_with_self_loop("おはよう", str(ROOT), "fake", "m", None, 1, 1, None)
                    else:
                        result = await service._run_plain("おはよう", str(ROOT), "fake", "m", None, "test", False, None, 1, None)
                    self.assertEqual(result["status"], "NG" if エラー応答判定(value) else "OK")
                    self.assertEqual(result["result"], 応答正規化(value))
                    ai.終了.assert_awaited_once()

    async def test_mcp_code_errors_skip_verification(self):
        for value in (None, "", "! 任意の失敗", "おはよう！"):
            with self.subTest(value=value):
                ai = SimpleNamespace(実行=AsyncMock(return_value=value), 終了=AsyncMock())
                agent = SimpleNamespace(_ensure_ai_instance=AsyncMock(return_value=ai),
                                        _バックアップ検証ループ=AsyncMock(return_value=False), 累積変更ファイル=[])
                service = CodeAgents()
                service.version_info = {}
                with patch.object(service, "_load_key_json", return_value={}), patch("AIコア.AIコード.CodeAgent", return_value=agent):
                    result = await service.run_async("おはよう", project_path=str(ROOT), ai_name="codex_cli", ai_model="same", self_check_loop=1)
                self.assertEqual(result["status"], "NG" if エラー応答判定(value) else "OK")
                self.assertEqual(result["result"], 応答正規化(value))
                self.assertEqual(agent._バックアップ検証ループ.await_count, 0 if エラー応答判定(value) else 1)
                ai.終了.assert_awaited_once()

    async def test_mcp_chat_exception_preserves_error_detail(self):
        service = object.__new__(ChatLLM)
        service._sessions = {}
        ai = SimpleNamespace(実行=AsyncMock(side_effect=RuntimeError("接続失敗")), 終了=AsyncMock())
        service._build_instance = AsyncMock(return_value=ai)
        result = await service._run_plain("おはよう", str(ROOT), "fake", "m", None, "test", False, None, 1, None)
        self.assertEqual(result["status"], "NG")
        self.assertEqual(result["result"], "! 接続失敗")

    async def test_websocket_chat_sends_error_marker_and_detail(self):
        from AIコア.AIチャット import Chat
        for reply, failure in (("", None), ("! 任意の失敗", None), (None, RuntimeError("接続失敗"))):
            with self.subTest(reply=reply, failure=failure):
                ai = SimpleNamespace(実行=AsyncMock(return_value=reply, side_effect=failure))
                chat = object.__new__(Chat)
                chat.セッションID, chat.チャンネル = "test", "chat"
                chat.AI_NAME, chat.AI_MODEL = "fake", "test"
                chat.初期化エラー = ""
                chat.保存関数 = None
                chat.接続 = SimpleNamespace(send_to_channel=AsyncMock())
                chat._ensure_ai_instance = AsyncMock(return_value=ai)
                await chat._AI実行と応答送信({"メッセージ内容": "おはよう"})
                packet = chat.接続.send_to_channel.call_args.args[1]
                self.assertEqual(packet["メッセージ識別"], "output_text")
                self.assertEqual(packet["メッセージ内容"], "! 接続失敗" if failure else 応答正規化(reply))

    async def test_completions_distinguishes_empty_errors_from_tool_calls(self):
        for reply, calls, expected in (("", [], "NG"), ("! 接続失敗", [], "NG"),
                                        ("", [{"id": "tool-1", "type": "function", "function": {"name": "test", "arguments": "{}"}}], "OK"),
                                        ("おはよう", [], "OK")):
            with self.subTest(reply=reply, calls=calls):
                ai = SimpleNamespace(実行=AsyncMock(return_value=reply), 終了=AsyncMock(), last_tool_calls=calls)
                service = object.__new__(ChatLLM)
                service.root = str(ROOT)
                service.version_info = {}
                service._build_instance = AsyncMock(return_value=ai)
                with patch.object(service, "_load_key_json", return_value={}):
                    result = await service.complete_async(messages=[{"role": "user", "content": "おはよう"}], ai_name="openai_chat", ai_model="test")
                self.assertEqual(result["status"], expected)
                self.assertEqual(result["content"], "" if calls else 応答正規化(reply))


if __name__ == "__main__":
    unittest.main()
