# -*- coding: utf-8 -*-

import importlib.util
import inspect
import logging
import os
from pathlib import Path
import sys
import time
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

    def test_default_idle_timeout_is_900_seconds(self):
        self.assertEqual(900, inspect.signature(self.module.CodeAI.実行).parameters["タイムアウト秒数"].default)

    def test_antigravity_has_no_separate_fixed_deadline(self):
        code_ai, _ = self._code_ai("antigravity_cli")
        with patch.dict(os.environ, {"ANTIGRAVITY_CLI_CLI_PATH": sys.executable}):
            command = code_ai._コマンド構築("test", 初回=True)
        self.assertEqual("0", command[command.index("--print-timeout") + 1])

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

    async def test_partial_output_keeps_cli_running(self):
        for provider, method in (("opencode_cli", "_subprocess実行"), ("antigravity_cli", "_antigravity実行")):
            for source in ("stdout", "stderr"):
                with self.subTest(provider=provider, source=source):
                    code_ai, parent = self._code_ai(provider)
                    script = (
                        "import sys,time\n"
                        f"out=sys.{source}.buffer\n"
                        "for _ in range(3):\n"
                        "    out.write(b'tick')\n"
                        "    out.flush()\n"
                        "    time.sleep(0.55)\n"
                    )
                    if source == "stderr":
                        script += "print('answer',flush=True)\n"
                    result = await getattr(code_ai, method)(
                        [sys.executable, "-c", script],
                        cwd=str(PROJECT_ROOT),
                        timeout=1,
                    )
                    self.assertNotIn("タイムアウト", result)
                    self.assertEqual("answer" if source == "stderr" else "tickticktick", result)
                    if source == "stderr":
                        self.assertEqual("tickticktick", code_ai.last_stderr_output)
                        self.assertEqual(["tickticktick"], [m["メッセージ内容"] for m in parent.接続.messages])

    async def test_timeout_starts_after_last_received_chunk(self):
        script = (
            "import sys,time\n"
            "sys.stdout.close()\n"
            "sys.stderr.write('tick')\n"
            "sys.stderr.flush()\n"
            "time.sleep(0.6)\n"
            "sys.stderr.write('tick')\n"
            "sys.stderr.flush()\n"
            "time.sleep(60)\n"
        )
        for provider, method in (("opencode_cli", "_subprocess実行"), ("antigravity_cli", "_antigravity実行")):
            with self.subTest(provider=provider):
                code_ai, _ = self._code_ai(provider)
                start = time.monotonic()
                result = await getattr(code_ai, method)(
                    [sys.executable, "-c", script],
                    cwd=str(PROJECT_ROOT),
                    timeout=1,
                )
                self.assertEqual("処理タイムアウト(1秒)が発生しました。", result)
                self.assertGreaterEqual(time.monotonic() - start, 1.5)


if __name__ == "__main__":
    unittest.main()
