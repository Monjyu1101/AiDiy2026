import asyncio
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock, patch

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from AIコア.AIコードモデル選択 import MODEL_CHOICES, select_model
from test_code_cli_output_routing import _load_code_ai_module, _親


def answer(model, **kwargs):
    return {"status": "OK", "data": {"answers": [{"type": "choice", "name": "code_model", "choice": model, **kwargs}]}}


class SelectorTests(unittest.IsolatedAsyncioTestCase):
    async def test_candidate_mapping_and_full_history(self):
        expected = {"codex_cli": ["gpt-6.1-sol", "gpt-5.6-terra", "gpt-6-luna", "gpt-6-astra"], "copilot_cli": ["gpt-6.1-sol", "gpt-5.6-terra", "gpt-6-luna", "gpt-6-astra"], "claude_cli": ["sonnet", "haiku", "fable"]}
        for provider, models in expected.items():
            for model in models:
                calls = []
                def handler(req):
                    calls.append(req.url.path)
                    if req.method == "GET":
                        return httpx.Response(200, json={"status": "OK", "data": {"available": True}})
                    body = json.loads(req.content)
                    self.assertEqual(json.loads(body["input"]), {"会話履歴": "履歴全文", "今回CLIへ送る内容": "依頼全文"})
                    self.assertEqual(body["model"], "auto")
                    self.assertEqual([c["value"] for c in body["questions"][0]["choices"]], models)
                    return httpx.Response(200, json=answer(model))
                with self.subTest(provider=provider, model=model):
                    self.assertEqual(await select_model(provider, "履歴全文", "依頼全文", transport=httpx.MockTransport(handler)), model)
                    self.assertEqual(len(calls), 2)

    async def test_unavailable_does_not_submit_history(self):
        def handler(req):
            self.assertEqual(req.method, "GET")
            return httpx.Response(200, json={"status": "NG", "data": {"available": False}})
        self.assertEqual(await select_model("codex_cli", "private history", "prompt", transport=httpx.MockTransport(handler)), "")

    async def test_failures_and_disallowed_models_fall_back(self):
        bad = [answer("unknown-model"), answer("fable"), answer("gpt-6-luna", type="refusal"), answer("gpt-6-luna", name="wrong"), {"status": "NG"}, {"status": "OK", "data": {"answers": []}}, {"status": "OK", "data": None}]
        for payload in bad:
            def handler(req):
                return httpx.Response(200, json={"status": "OK", "data": {"available": True}} if req.method == "GET" else payload)
            self.assertEqual(await select_model("codex_cli", "", "prompt", transport=httpx.MockTransport(handler)), "")
        for status in (401, 503):
            self.assertEqual(await select_model("codex_cli", "", "prompt", transport=httpx.MockTransport(lambda req: httpx.Response(status))), "")
        def timeout(req):
            raise httpx.ReadTimeout("test")
        self.assertEqual(await select_model("codex_cli", "", "prompt", transport=httpx.MockTransport(timeout)), "")

    async def test_cancel_propagates_and_other_cli_skips_http(self):
        def cancel(req):
            raise asyncio.CancelledError()
        with self.assertRaises(asyncio.CancelledError):
            await select_model("codex_cli", "", "prompt", transport=httpx.MockTransport(cancel))
        self.assertEqual(await select_model("grok_cli", "", "prompt", transport=httpx.MockTransport(cancel)), "")


class CodeAutoIntegrationTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = _load_code_ai_module()

    def instance(self, provider="codex_cli", model="auto"):
        parent = _親()
        code = self.module.CodeAI(親=parent, AI_NAME=provider, AI_MODEL=model)
        code._aidiy参照プロンプト取得 = lambda path: ""
        return code, parent

    async def run_code(self, code, text, **kwargs):
        with patch.dict(os.environ, {f"{code.code_ai.upper()}_CLI_PATH": "test_cli"}), redirect_stdout(io.StringIO()):
            return await code.実行(text, **kwargs)

    async def test_history_selection_is_per_turn_and_notification_precedes_stream(self):
        code, parent = self.instance()
        commands = []
        async def subprocess(**kwargs):
            commands.append(kwargs["command"])
            self.assertIn("選択モデル", parent.接続.messages[-1]["メッセージ内容"])
            await parent.接続.send_to_channel(1, {"メッセージ識別": "output_stream", "メッセージ内容": "CLI先頭"})
            return "前の回答"
        with patch("AIコア.AIコードモデル選択.select_model", new=AsyncMock(side_effect=["gpt-5.6-terra", "gpt-6.1-sol"])) as select, patch.object(code, "_subprocess実行", side_effect=subprocess), patch.object(code, "_履歴取得", wraps=code._履歴取得) as history:
            await self.run_code(code, "一つの設定を確認")
            self.assertEqual(history.call_count, 1)
            await self.run_code(code, "それを修正して")
            self.assertEqual(history.call_count, 2)
        self.assertEqual(select.call_args_list[0].args[1], "")
        self.assertIn("一つの設定を確認", select.call_args_list[1].args[1])
        self.assertIn("前の回答", select.call_args_list[1].args[1])
        self.assertIn("それを修正して", select.call_args_list[1].args[2])
        self.assertNotIn("それを修正して", select.call_args_list[1].args[1])
        self.assertEqual([c[c.index("--model") + 1] for c in commands], ["gpt-5.6-terra", "gpt-6.1-sol"])
        self.assertEqual(code.code_model, "auto")
        self.assertEqual(code.最終実行モデル, "gpt-6.1-sol")
        self.assertEqual([m["メッセージ内容"] for m in parent.接続.messages], ["[選択モデル: gpt-5.6-terra]\n", "CLI先頭", "[選択モデル: gpt-6.1-sol]\n", "CLI先頭"])

    async def test_failed_selection_notifies_before_cli_and_uses_fallback(self):
        fallback = {"codex_cli": "gpt-6.1-sol", "copilot_cli": "gpt-6.1-sol",
                    "claude_cli": "sonnet", "aidiy_hermes": "openai_oauth/gpt-6.1-sol"}
        for provider in (*MODEL_CHOICES, "antigravity_cli", "grok_cli", "opencode_cli", "aidiy_hermes", "claude_ollama", "codex_ollama"):
            code, parent = self.instance(provider)
            parent.モデル設定 = {"CHAT_OLLAMA_MODEL": "must-not-be-used"}
            async def run(**kwargs):
                if provider in fallback:
                    first = parent.接続.messages[0]
                    self.assertEqual(first["メッセージ識別"], "output_stream")
                    self.assertEqual(first["メッセージ内容"], f"[モデル選択失敗: {fallback[provider]} を使用します]\n")
                return "ok"
            process = AsyncMock(side_effect=run)
            with patch("AIコア.AIコードモデル選択.select_model", new=AsyncMock(return_value="")) as select, patch.object(code, "_subprocess実行", process), patch.object(code, "_antigravity実行", process):
                await self.run_code(code, "依頼")
            self.assertEqual(select.await_count, 1 if provider in MODEL_CHOICES or provider == "aidiy_hermes" else 0)
            command = process.call_args.kwargs["command"]
            if provider in fallback:
                self.assertEqual(command[command.index("--model") + 1], fallback[provider])
                self.assertEqual(code.最終実行モデル, fallback[provider])
                self.assertEqual(code.code_model, "auto")
            else:
                self.assertNotIn("--model", command)
                self.assertEqual(parent.接続.messages, [])

    async def test_explicit_and_same_skip_selection(self):
        for provider, model in (("codex_cli", "gpt-6-astra"), ("copilot_cli", "gpt-6-astra"), ("claude_cli", "fable"), ("claude_cli", "same"), ("aidiy_hermes", "openai_oauth/gpt-6-astra"), ("aidiy_hermes", "same")):
            code, parent = self.instance(provider, model)
            with patch("AIコア.AIコードモデル選択.select_model", new=AsyncMock()) as select, patch.object(code, "_subprocess実行", new=AsyncMock(return_value="ok")) as process:
                await self.run_code(code, "依頼")
            select.assert_not_awaited()
            command = process.call_args.kwargs["command"]
            if model != "same":
                self.assertEqual(command[command.index("--model") + 1], model)
            elif provider == "aidiy_hermes":
                self.assertEqual(command[command.index("--provider") + 1], "same")
                self.assertEqual(command[command.index("--model") + 1], "same")
            else:
                self.assertNotIn("--model", command)
            self.assertEqual(parent.接続.messages, [])

    async def test_hermes_uses_codex_selection_with_oauth_prefix_each_turn(self):
        code, parent = self.instance("aidiy_hermes")
        for choice in MODEL_CHOICES["codex_cli"]:
            model = choice["value"]
            with self.subTest(model=model), patch("AIコア.AIコードモデル選択.select_model", new=AsyncMock(return_value=model)) as select, patch.object(code, "_subprocess実行", new=AsyncMock(return_value="前の回答")) as process:
                await self.run_code(code, "今回の依頼")
            self.assertEqual(select.call_args.args[0], "codex_cli")
            command = process.call_args.kwargs["command"]
            expected = f"openai_oauth/{model}"
            self.assertEqual(command[command.index("--model") + 1], expected)
            self.assertEqual(select.call_args.args[2], process.call_args.kwargs["stdin_text"])
            self.assertEqual(code.最終実行モデル, expected)
            self.assertEqual(parent.接続.messages[-1]["メッセージ内容"], f"[選択モデル: {expected}]\n")
            self.assertEqual(code.code_model, "auto")
        self.assertIn("前の回答", select.call_args.args[1])

    async def test_new_conversation_drops_old_history(self):
        code, _ = self.instance()
        code.session_started = True
        code._履歴追加("旧会話", "user")
        with patch("AIコア.AIコードモデル選択.select_model", new=AsyncMock(return_value="gpt-6-luna")) as select, patch.object(code, "_subprocess実行", new=AsyncMock(return_value="ok")):
            await self.run_code(code, "おはよう", resume=False)
        self.assertNotIn("旧会話", select.call_args.args[1] + select.call_args.args[2])
        self.assertNotIn("旧会話", code._履歴取得())

    async def test_stop_during_selection_does_not_launch_cli(self):
        code, parent = self.instance()
        async def stop(*args):
            parent.強制停止フラグ = True
            return "gpt-6.1-sol"
        with patch("AIコア.AIコードモデル選択.select_model", side_effect=stop), patch.object(code, "_subprocess実行", new=AsyncMock()) as process:
            await self.run_code(code, "依頼")
        process.assert_not_awaited()
        self.assertEqual(parent.接続.messages, [])
