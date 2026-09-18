# -*- coding: utf-8 -*-

import importlib.util
import logging
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
CODE_AI_PATH = BACKEND_DIR / "AIコア" / "AIコード_cli.py"


def _load_code_ai_module():
    log_config_stub = types.ModuleType("log_config")
    log_config_stub.get_logger = logging.getLogger

    pil_stub = types.ModuleType("PIL")
    pil_stub.Image = object

    spec = importlib.util.spec_from_file_location(
        "code_cli_output_routing_test",
        CODE_AI_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"AIコード_cli を読み込めません: {CODE_AI_PATH}")
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"log_config": log_config_stub, "PIL": pil_stub}):
        spec.loader.exec_module(module)
    return module


class _接続:
    def __init__(self):
        self.messages = []

    async def send_to_channel(self, channel, message):
        self.messages.append(message)


class _親:
    def __init__(self):
        self.接続 = _接続()
        self.強制停止フラグ = False


class CodeCliOutputRoutingTest(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = _load_code_ai_module()

    def _code_ai(self, provider):
        parent = _親()
        code_ai = self.module.CodeAI(
            親=parent,
            セッションID="routing-test",
            チャンネル=1,
            AI_NAME=provider,
            AI_MODEL="auto",
        )
        return code_ai, parent

    @staticmethod
    def _stdout_stderr_command(stdout="STDOUT_FINAL", stderr="STDERR_PROGRESS"):
        script = (
            "import sys;"
            f"print({stderr!r},file=sys.stderr,flush=True);"
            f"print({stdout!r},flush=True)"
        )
        return [sys.executable, "-c", script]

    async def test_copilot_and_opencode_stream_only_stderr(self):
        for provider in ("copilot_cli", "opencode_cli"):
            with self.subTest(provider=provider):
                code_ai, parent = self._code_ai(provider)

                result = await code_ai._subprocess実行(
                    self._stdout_stderr_command(),
                    cwd=str(PROJECT_ROOT),
                    timeout=10,
                )

                streamed = [m["メッセージ内容"] for m in parent.接続.messages]
                self.assertEqual("STDOUT_FINAL", result)
                self.assertEqual(["STDERR_PROGRESS"], streamed)
                self.assertEqual("STDERR_PROGRESS", code_ai.last_stderr_output)

    async def test_copilot_and_opencode_do_not_use_stderr_as_final_answer(self):
        for provider in ("copilot_cli", "opencode_cli"):
            with self.subTest(provider=provider):
                code_ai, parent = self._code_ai(provider)

                result = await code_ai._subprocess実行(
                    self._stdout_stderr_command(stdout="", stderr="ERROR_ONLY"),
                    cwd=str(PROJECT_ROOT),
                    timeout=10,
                )

                streamed = [m["メッセージ内容"] for m in parent.接続.messages]
                self.assertEqual("（応答なし）", result)
                self.assertEqual(["ERROR_ONLY"], streamed)

    async def test_antigravity_streams_only_stderr(self):
        code_ai, parent = self._code_ai("antigravity_cli")

        result = await code_ai._antigravity実行(
            self._stdout_stderr_command(),
            cwd=str(PROJECT_ROOT),
            timeout=10,
        )

        streamed = [m["メッセージ内容"] for m in parent.接続.messages]
        self.assertEqual("STDOUT_FINAL", result)
        self.assertEqual(["STDERR_PROGRESS"], streamed)
        self.assertEqual("STDERR_PROGRESS", code_ai.last_stderr_output)

    async def test_codex_and_claude_keep_existing_stdout_stream_behavior(self):
        for provider in ("codex_cli", "claude_cli"):
            with self.subTest(provider=provider):
                code_ai, parent = self._code_ai(provider)

                result = await code_ai._subprocess実行(
                    self._stdout_stderr_command(),
                    cwd=str(PROJECT_ROOT),
                    timeout=10,
                )

                streamed = [m["メッセージ内容"] for m in parent.接続.messages]
                self.assertEqual("STDOUT_FINAL", result)
                self.assertCountEqual(["STDOUT_FINAL", "STDERR_PROGRESS"], streamed)


if __name__ == "__main__":
    unittest.main()
