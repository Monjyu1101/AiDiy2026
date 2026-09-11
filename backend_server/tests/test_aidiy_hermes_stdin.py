# -*- coding: utf-8 -*-

import asyncio
from contextlib import redirect_stdout
import hashlib
import io
import importlib.util
import logging
import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import AsyncMock, patch


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
CODE_AI_PATH = BACKEND_DIR / "AIコア" / "AIコード_cli.py"


def _load_code_ai_module():
    log_config_stub = types.ModuleType("log_config")
    log_config_stub.get_logger = logging.getLogger

    pil_stub = types.ModuleType("PIL")
    pil_stub.Image = object

    spec = importlib.util.spec_from_file_location(
        "aidiy_hermes_stdin_test",
        CODE_AI_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"AIコード_cli を読み込めません: {CODE_AI_PATH}")
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"log_config": log_config_stub, "PIL": pil_stub}):
        spec.loader.exec_module(module)
    return module


class AidiyHermesCommandTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = _load_code_ai_module()

    def test_long_prompt_is_not_in_hermes_command(self):
        long_prompt = "長文プロンプト" * 10_000

        for model in ("auto", "local_chat"):
            with self.subTest(model=model):
                code_ai = self.module.CodeAI(
                    AI_NAME="aidiy_hermes",
                    AI_MODEL=model,
                )
                with patch.dict(
                    os.environ,
                    {"AIDIY_HERMES_CLI_PATH": "aidiy_hermes_test"},
                ):
                    command = code_ai._コマンド構築(long_prompt, 初回=True)

                self.assertIn("--oneshot-stdin", command)
                self.assertNotIn("-z", command)
                self.assertTrue(all(long_prompt not in arg for arg in command))
                self.assertLess(sum(len(arg) for arg in command), 1_000)


class AidiyHermesSubprocessTest(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = _load_code_ai_module()

    def setUp(self):
        self.code_ai = self.module.CodeAI(
            AI_NAME="aidiy_hermes",
            AI_MODEL="auto",
        )

    async def asyncTearDown(self):
        if self.code_ai.current_process is not None:
            await self.code_ai.強制終了()

    async def test_large_japanese_prompt_reaches_child_as_utf8(self):
        prompt = ("日本語入力\n" * 10_000) + "終端"
        prompt_bytes = prompt.encode("utf-8")
        expected = f"{len(prompt_bytes)}:{hashlib.sha256(prompt_bytes).hexdigest()}"
        script = (
            "import hashlib,sys;"
            "data=sys.stdin.buffer.read();"
            "print(f'{len(data)}:{hashlib.sha256(data).hexdigest()}')"
        )

        result = await self.code_ai._subprocess実行(
            [sys.executable, "-c", script],
            cwd=str(PROJECT_ROOT),
            timeout=10,
            stdin_text=prompt,
        )

        self.assertEqual(expected, result)
        self.assertIsNone(self.code_ai.current_process)

    async def test_execute_passes_complete_prompt_to_hermes_stdin(self):
        subprocess_mock = AsyncMock(return_value="応答")

        with (
            patch.object(self.code_ai, "_subprocess実行", subprocess_mock),
            redirect_stdout(io.StringIO()),
        ):
            result = await self.code_ai.実行(
                "stdin 経路の確認",
                resume=False,
                絶対パス=str(PROJECT_ROOT),
            )

        call_kwargs = subprocess_mock.call_args.kwargs
        self.assertEqual("応答", result)
        self.assertIn("stdin 経路の確認", call_kwargs["stdin_text"])
        self.assertIn("--oneshot-stdin", call_kwargs["command"])
        self.assertTrue(
            all(call_kwargs["stdin_text"] not in arg for arg in call_kwargs["command"])
        )

    async def test_large_bidirectional_pipes_do_not_deadlock(self):
        prompt = "入" * 1_200_000
        prompt_bytes = prompt.encode("utf-8")
        expected_marker = f"stdin={len(prompt_bytes)}:{hashlib.sha256(prompt_bytes).hexdigest()}"
        script = (
            "import hashlib,sys;"
            "sys.stdout.buffer.write(b'O'*(3*1024*1024)+b'\\n');"
            "sys.stdout.buffer.flush();"
            "data=sys.stdin.buffer.read();"
            "print(f'stdin={len(data)}:{hashlib.sha256(data).hexdigest()}')"
        )

        result = await asyncio.wait_for(
            self.code_ai._subprocess実行(
                [sys.executable, "-c", script],
                cwd=str(PROJECT_ROOT),
                timeout=20,
                stdin_text=prompt,
            ),
            timeout=30,
        )

        self.assertIn(expected_marker, result)
        self.assertGreater(len(result), 3 * 1024 * 1024)
        self.assertIsNone(self.code_ai.current_process)

    async def test_child_that_does_not_read_stdin_is_killed_on_timeout(self):
        prompt = "停止" * 1_500_000
        self.code_ai.last_stderr_output = "stale-stderr"

        result = await asyncio.wait_for(
            self.code_ai._subprocess実行(
                [
                    sys.executable,
                    "-c",
                    (
                        "import sys,time;"
                        "print('timeout-stderr',file=sys.stderr,flush=True);"
                        "time.sleep(60)"
                    ),
                ],
                cwd=str(PROJECT_ROOT),
                timeout=1,
                stdin_text=prompt,
            ),
            timeout=8,
        )

        self.assertEqual("処理タイムアウト(1秒)が発生しました。", result)
        self.assertEqual("timeout-stderr", self.code_ai.last_stderr_output)
        self.assertIsNone(self.code_ai.current_process)


if __name__ == "__main__":
    unittest.main()
