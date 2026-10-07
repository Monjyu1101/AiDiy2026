# -*- coding: utf-8 -*-

import importlib.util
import logging
from pathlib import Path
import sys
import tempfile
import types as stdlib_types
import unittest
from unittest.mock import Mock, patch

from google.genai import types


CHAT_PATH = Path(__file__).resolve().parents[1] / "AIコア" / "AIチャット_gemini.py"


def load_chat_module():
    log_config_stub = stdlib_types.ModuleType("log_config")
    log_config_stub.get_logger = logging.getLogger
    spec = importlib.util.spec_from_file_location("gemini_image_test", CHAT_PATH)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"log_config": log_config_stub}):
        spec.loader.exec_module(module)
    return module


class GeminiImageGenerationTest(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.ChatAI = load_chat_module().ChatAI

    async def test_image_model_skips_tools_and_saves_image(self):
        image_bytes = b"test image bytes"
        response = types.GenerateContentResponse(candidates=[types.Candidate(
            content=types.Content(role="model", parts=[
                types.Part.from_text(text="猫の画像です。"),
                types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
            ]),
        )])
        generate = Mock(return_value=response)
        tools_stub = stdlib_types.ModuleType("AI内部ツール")
        tools_stub.MCPツールブリッジ = Mock(side_effect=AssertionError("画像モデルに tools を渡した"))

        with tempfile.TemporaryDirectory() as temp_dir:
            chat = self.ChatAI(
                AI_NAME="gemini_chat", AI_MODEL="gemini-3.1-flash-image",
                api_key="test-key", 絶対パス=temp_dir,
            )
            chat.is_alive = True
            chat.client = stdlib_types.SimpleNamespace(
                models=stdlib_types.SimpleNamespace(generate_content=generate),
            )
            with patch.dict(sys.modules, {
                "AI内部ツール": tools_stub,
                "AIコア.AI内部ツール": tools_stub,
            }):
                result = await chat.実行("かわいい猫の画像を作って", 自己ループ=True)

            self.assertIn("猫の画像です。", result)
            self.assertEqual(1, len(chat.last_output_files))
            self.assertEqual(image_bytes, Path(chat.last_output_files[0]).read_bytes())

        config = generate.call_args.kwargs["config"]
        self.assertEqual(["TEXT", "IMAGE"], config.response_modalities)
        self.assertIsNone(config.response_mime_type)
        tools_stub.MCPツールブリッジ.assert_not_called()

    def test_nano_banana_is_treated_as_image_model(self):
        for model, expected in (
            ("gemini-nano-banana-2.1", True),
            ("gemini-3.1-flash-lite-image", True),
            ("gemini-3-pro-image", True),
            ("gemini-3.8-flash", False),
        ):
            chat = self.ChatAI(AI_NAME="gemini_chat", AI_MODEL=model, api_key="test-key")
            self.assertEqual(expected, chat._画像生成モデル(), model)

    async def test_api_error_is_returned_to_chat(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            chat = self.ChatAI(
                AI_NAME="gemini_chat", AI_MODEL="gemini-3.1-flash-image",
                api_key="test-key", 絶対パス=temp_dir,
            )
            chat.is_alive = True
            chat.client = stdlib_types.SimpleNamespace(models=stdlib_types.SimpleNamespace(
                generate_content=Mock(side_effect=RuntimeError("API failure")),
            ))
            with self.assertLogs(level="ERROR"):
                result = await chat.実行("かわいい猫の画像を作って", 自己ループ=True)

        self.assertIn("API failure", result)


if __name__ == "__main__":
    unittest.main()
