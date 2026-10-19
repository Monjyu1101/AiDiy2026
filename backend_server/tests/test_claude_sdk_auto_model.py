import asyncio
from contextlib import redirect_stdout
import io
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from AIコア import AIコード_claude as sdk


class ClaudeSdkAutoModelTests(unittest.IsolatedAsyncioTestCase):
    def instance(self, model="auto"):
        parent = SimpleNamespace(強制停止フラグ=False, 接続=SimpleNamespace(send_to_channel=AsyncMock()))
        with patch.object(sdk, "_load_mcp_servers", return_value={}):
            code = sdk.CodeAI(親=parent, AI_NAME="claude_sdk", AI_MODEL=model)
        code._aidiy参照プロンプト取得 = lambda path: ""
        return code, parent

    async def run_code(self, code, text="今回の依頼", **kwargs):
        with redirect_stdout(io.StringIO()):
            return await code.実行(text, **kwargs)

    async def test_sdk_error_result_is_marked_even_without_an_exception(self):
        code, _ = self.instance("sonnet")

        async def query(*, prompt, options):
            yield SimpleNamespace(is_error=True, result="利用上限に達しました")

        with patch.object(sdk, "query", query):
            self.assertEqual(await self.run_code(code), "! 利用上限に達しました")

    async def test_each_turn_uses_cli_selector_history_and_sdk_model(self):
        code, parent = self.instance()
        calls = []

        async def query(*, prompt, options):
            calls.append((prompt, options))
            self.assertIn(options.model, parent.接続.send_to_channel.call_args.args[1]["メッセージ内容"])
            yield SimpleNamespace(session_id="sdk-session", result="前の回答")

        choices = ["haiku", "sonnet", "fable"]
        with patch("AIコア.AIコードモデル選択.select_model", new=AsyncMock(side_effect=choices)) as select, patch.object(sdk, "query", query):
            for model in choices:
                self.assertEqual(await self.run_code(code, f"依頼 {model}"), "前の回答")
                self.assertEqual(code.code_model, "auto")
                self.assertEqual(code.最終実行モデル, model)
        self.assertEqual([options.model for _, options in calls], choices)
        self.assertIsNone(calls[0][1].resume)
        self.assertEqual(calls[1][1].resume, "sdk-session")
        self.assertEqual(select.call_args_list[0].args[1], "")
        self.assertIn("依頼 haiku", select.call_args_list[1].args[1])
        self.assertIn("前の回答", select.call_args_list[1].args[1])
        self.assertNotIn("依頼 sonnet", select.call_args_list[1].args[1])
        for selected, (prompt, _) in zip(select.call_args_list, calls):
            self.assertEqual(selected.args[0], "claude_cli")
            self.assertEqual(selected.args[2], prompt)

    async def test_explicit_model_skips_selection_and_failure_notifies_before_sdk(self):
        for model, expected in (("sonnet", "sonnet"), ("fable", "fable"), ("same", None), ("auto", "sonnet")):
            with self.subTest(model=model):
                code, parent = self.instance(model)
                received = []

                async def query(*, prompt, options):
                    if model == "auto":
                        message = parent.接続.send_to_channel.call_args.args[1]
                        self.assertEqual(message["メッセージ識別"], "output_stream")
                        self.assertEqual(message["メッセージ内容"], "[モデル選択失敗: sonnet を使用します]\n")
                    received.append(options)
                    yield SimpleNamespace(session_id="sdk-session", result="ok")

                with patch("AIコア.AIコードモデル選択.select_model", new=AsyncMock(return_value="")) as select, patch.object(sdk, "query", query):
                    self.assertEqual(await self.run_code(code), "ok")
                self.assertEqual(received[0].model, expected)
                self.assertEqual(select.await_count, 1 if model == "auto" else 0)
                if model != "auto":
                    parent.接続.send_to_channel.assert_not_awaited()
                self.assertEqual(code.code_model, model)

    async def test_new_conversation_excludes_old_history_and_session(self):
        code, _ = self.instance()
        code.AIセッションID = "old-session"
        code._履歴追加("旧会話", "user")
        received = []

        async def query(*, prompt, options):
            received.append(options)
            yield SimpleNamespace(session_id="new-session", result="ok")

        with patch("AIコア.AIコードモデル選択.select_model", new=AsyncMock(return_value="haiku")) as select, patch.object(sdk, "query", query):
            await self.run_code(code, "こんにちは", resume=False)
        self.assertEqual(select.call_args.args[1], "")
        self.assertIsNone(received[0].resume)
        self.assertFalse(received[0].continue_conversation)
        self.assertNotIn("旧会話", code._履歴取得())

    async def test_stop_during_selection_prevents_sdk_call(self):
        code, parent = self.instance()

        async def stop(*args):
            parent.強制停止フラグ = True
            return "sonnet"

        with patch("AIコア.AIコードモデル選択.select_model", side_effect=stop), patch.object(sdk, "query") as query:
            self.assertEqual(await self.run_code(code), "!")
        query.assert_not_called()
        parent.接続.send_to_channel.assert_not_awaited()

    async def test_cancel_during_selection_propagates(self):
        code, _ = self.instance()
        with patch("AIコア.AIコードモデル選択.select_model", side_effect=asyncio.CancelledError), patch.object(sdk, "query") as query:
            with self.assertRaises(asyncio.CancelledError):
                await self.run_code(code)
        query.assert_not_called()
