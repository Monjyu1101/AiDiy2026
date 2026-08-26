# -*- coding: utf-8 -*-

import importlib.util
import json
import logging
from pathlib import Path
import sys
import types as stdlib_types
import unittest
from unittest.mock import patch

from google.genai import types


BACKEND_DIR = Path(__file__).resolve().parents[1]
GEMINI_CHAT_PATH = BACKEND_DIR / "AIコア" / "AIチャット_gemini.py"


def _load_gemini_chat_module():
    log_config_stub = stdlib_types.ModuleType("log_config")
    log_config_stub.get_logger = logging.getLogger

    spec = importlib.util.spec_from_file_location(
        "gemini_thought_signature_test",
        GEMINI_CHAT_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Gemini チャットを読み込めません: {GEMINI_CHAT_PATH}")
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"log_config": log_config_stub}):
        spec.loader.exec_module(module)
    return module


class GeminiThoughtSignatureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = _load_gemini_chat_module()
        cls.chat_ai = cls.module.ChatAI.__new__(cls.module.ChatAI)

    def test_function_call_signature_survives_openai_message_round_trip(self):
        raw_signature = b"\x00gemini-thought-signature\xff"
        source_part = types.Part(
            function_call=types.FunctionCall(
                id="gemini-call-1",
                name="default_api:aidiy_notification_sounds__play_notification_sound",
                args={"scene": "start"},
            ),
            thought_signature=raw_signature,
        )

        tool_call = self.chat_ai._function_call_part_to_tool_call(
            source_part,
            "fallback-call-id",
        )

        self.assertEqual("gemini-call-1", tool_call["id"])
        self.assertIn("thought_signature", tool_call)
        json.dumps(tool_call)

        _, contents = self.chat_ai._messages_to_gemini_contents([
            {"role": "user", "content": "開始音を鳴らして"},
            {"role": "assistant", "content": None, "tool_calls": [tool_call]},
            {"role": "tool", "tool_call_id": "gemini-call-1", "content": '{"ok": true}'},
        ])

        restored_part = contents[1].parts[0]
        self.assertEqual(raw_signature, restored_part.thought_signature)
        self.assertEqual(source_part.function_call.name, restored_part.function_call.name)
        self.assertEqual(source_part.function_call.args, restored_part.function_call.args)
        self.assertEqual(
            source_part.function_call.name,
            contents[2].parts[0].function_response.name,
        )

    def test_unsigned_tool_call_remains_supported(self):
        _, contents = self.chat_ai._messages_to_gemini_contents([
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": "call-legacy",
                    "type": "function",
                    "function": {"name": "legacy_tool", "arguments": "{}"},
                }],
            },
        ])

        self.assertIsNone(contents[0].parts[0].thought_signature)
        self.assertEqual("legacy_tool", contents[0].parts[0].function_call.name)

    def test_invalid_signature_is_ignored_without_breaking_history(self):
        _, contents = self.chat_ai._messages_to_gemini_contents([
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": "call-invalid",
                    "type": "function",
                    "thought_signature": "not valid base64!",
                    "function": {"name": "safe_tool", "arguments": "{}"},
                }],
            },
        ])

        self.assertIsNone(contents[0].parts[0].thought_signature)
        self.assertEqual("safe_tool", contents[0].parts[0].function_call.name)


if __name__ == "__main__":
    unittest.main()
