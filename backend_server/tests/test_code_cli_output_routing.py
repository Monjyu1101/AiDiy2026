# -*- coding: utf-8 -*-

import importlib.util
import asyncio
import inspect
import json
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

    async def test_opencode_streams_only_stderr(self):
        code_ai, parent = self._code_ai("opencode_cli")

        result = await code_ai._subprocess実行(
            self._stdout_stderr_command(),
            cwd=str(PROJECT_ROOT),
            timeout=10,
        )

        streamed = [m["メッセージ内容"] for m in parent.接続.messages]
        self.assertEqual("STDOUT_FINAL", result)
        self.assertEqual(["STDERR_PROGRESS"], streamed)
        self.assertEqual("STDERR_PROGRESS", code_ai.last_stderr_output)

    def test_copilot_command_uses_json_stream_for_new_and_continued_sessions(self):
        code_ai, _ = self._code_ai("copilot_cli")
        code_ai.code_model = "test-model"
        for first in (True, False):
            with self.subTest(first=first), patch.dict(os.environ, {"COPILOT_CLI_CLI_PATH": "copilot_test"}):
                command = code_ai._コマンド構築("質問", 初回=first, repo_path=str(PROJECT_ROOT))
            self.assertEqual("json", command[command.index("--output-format") + 1])
            self.assertEqual("on", command[command.index("--stream") + 1])
            self.assertEqual("test-model", command[command.index("--model") + 1])
            self.assertEqual(not first, "--continue" in command)
            self.assertEqual("質問", command[command.index("-p") + 1])

    @staticmethod
    def _jsonl_command(events):
        payload = "\n".join(json.dumps(event, ensure_ascii=False) for event in events)
        # UTF-8 の文字途中・JSON行途中で分割し、最後の行は改行なしで閉じる。
        script = (
            "import sys\n"
            f"payload={payload!r}.encode('utf-8')\n"
            "for start in range(0,len(payload),7):\n"
            "    sys.stdout.buffer.write(payload[start:start+7])\n"
            "    sys.stdout.buffer.flush()\n"
        )
        return [sys.executable, "-c", script]

    async def test_copilot_routes_json_progress_and_only_final_parent_answer(self):
        code_ai, parent = self._code_ai("copilot_cli")
        events = [
            {"type": "user.message", "data": {"content": "USER_INPUT"}},
            {"type": "assistant.reasoning_delta", "data": {"reasoningId": "r1", "deltaContent": "構成を"}},
            {"type": "assistant.reasoning_delta", "data": {"reasoningId": "r1", "deltaContent": "確認します。"}},
            {"type": "assistant.reasoning", "data": {"reasoningId": "r1", "content": "構成を確認します。"}},
            {"type": "assistant.message", "data": {"messageId": "m1", "content": "調査を進めます。", "toolRequests": [{"toolCallId": "t1"}]}},
            {"type": "tool.execution_start", "data": {"toolCallId": "t1", "toolName": "read", "arguments": {"path": "AGENTS.md"}}},
            {"type": "tool.execution_progress", "data": {"toolCallId": "t1", "progressMessage": "読取中"}},
            {"type": "tool.execution_complete", "data": {"toolCallId": "t1", "success": True, "result": {"content": "FILE_CONTENT"}}},
            {"type": "assistant.message_start", "data": {"messageId": "m2", "phase": "final_answer"}},
            {"type": "assistant.message_delta", "data": {"messageId": "m2", "deltaContent": "最終"}},
            {"type": "assistant.message_delta", "data": {"messageId": "m2", "deltaContent": "回答\n日本語"}},
            {"type": "assistant.message", "data": {"messageId": "m2", "content": "最終回答\n日本語", "toolRequests": [], "phase": "final_answer", "encryptedContent": "OPAQUE"}},
            {"type": "assistant.message", "agentId": "child", "data": {"messageId": "child", "content": "CHILD_ANSWER"}},
            {"type": "assistant.usage", "data": {"cost": 123}},
            {"type": "future.event", "data": {"content": "UNKNOWN"}},
            {"type": "result", "exitCode": 0, "usage": {"premiumRequests": 1}},
        ]
        result = await code_ai._subprocess実行(self._jsonl_command(events), cwd=str(PROJECT_ROOT), timeout=10)
        streamed = [m["メッセージ内容"] for m in parent.接続.messages]
        self.assertEqual("最終回答\n日本語", result)
        self.assertEqual(1, streamed.count("[Copilot thinking] 構成を確認します。"))
        self.assertIn("[Copilot] 調査を進めます。", streamed)
        self.assertIn("[Copilot tool] read 開始 AGENTS.md", streamed)
        self.assertIn("[Copilot tool] read 完了", streamed)
        self.assertIn("[Copilot tool] 読取中", streamed)
        for hidden in ("最終回答", "USER_INPUT", "FILE_CONTENT", "CHILD_ANSWER", "OPAQUE", "UNKNOWN", '"type"'):
            self.assertNotIn(hidden, "\n".join(streamed))

    async def test_copilot_thinking_is_streamed_before_process_exits(self):
        code_ai, parent = self._code_ai("copilot_cli")
        received = asyncio.Event()
        original = parent.接続.send_to_channel

        async def receive(channel, message):
            await original(channel, message)
            if message["メッセージ内容"].startswith("[Copilot thinking]"):
                received.set()

        parent.接続.send_to_channel = receive
        delta = json.dumps({"type": "assistant.reasoning_delta", "data": {"reasoningId": "r", "deltaContent": "あ" * 170}}, ensure_ascii=False)
        final = json.dumps({"type": "assistant.message", "data": {"messageId": "m", "content": "回答"}}, ensure_ascii=False)
        script = f"import time; print({delta!r},flush=True); time.sleep(0.8); print({final!r},flush=True)"
        task = asyncio.create_task(code_ai._subprocess実行([sys.executable, "-c", script], cwd=str(PROJECT_ROOT), timeout=10))
        try:
            await asyncio.wait_for(received.wait(), timeout=5)
            self.assertFalse(task.done())
            self.assertIsNone(code_ai.current_process.returncode)
            self.assertEqual("回答", await task)
        finally:
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        thinking = [m["メッセージ内容"].removeprefix("[Copilot thinking] ") for m in parent.接続.messages if m["メッセージ内容"].startswith("[Copilot thinking]")]
        self.assertEqual("あ" * 170, "".join(thinking))

    def test_copilot_handles_complete_reasoning_without_deltas_and_partial_answer(self):
        output = self.module._CopilotJSON出力()
        event = {"type": "assistant.reasoning", "data": {"reasoningId": "r", "content": "思考完了"}}
        self.assertEqual(["[Copilot thinking] 思考完了"], output.解析(json.dumps(event)))
        self.assertEqual([], output.解析(json.dumps(event)))
        output.解析(json.dumps({"type": "assistant.message_start", "data": {"messageId": "m"}}))
        for text in ("回答\n", "末尾"):
            output.解析(json.dumps({"type": "assistant.message_delta", "data": {"messageId": "m", "deltaContent": text}}))
        self.assertEqual("回答\n末尾", output.回答)

    def test_copilot_excludes_non_answer_phases_and_legacy_child_messages(self):
        output = self.module._CopilotJSON出力()
        for phase in ("commentary", "thinking", "analysis"):
            event = {"type": "assistant.message", "data": {"messageId": phase, "content": "進捗", "phase": phase}}
            self.assertEqual(["[Copilot] 進捗"], output.解析(json.dumps(event)))
        event = {"type": "assistant.message", "data": {"messageId": "child", "content": "子の回答", "parentToolCallId": "t"}}
        self.assertEqual([], output.解析(json.dumps(event)))
        self.assertEqual("", output.回答)

    async def test_copilot_json_errors_and_tool_failures_are_visible_without_becoming_answers(self):
        code_ai, parent = self._code_ai("copilot_cli")
        events = [
            {"type": "tool.execution_start", "data": {"toolCallId": "t", "toolName": "bash"}},
            {"type": "tool.shell_output", "data": {"toolCallId": "t", "text": "端末出力", "stream": "stderr"}},
            {"type": "tool.execution_complete", "data": {"toolCallId": "t", "success": False, "error": {"message": "ツールエラー"}}},
            {"type": "session.error", "data": {"message": "認証エラー"}},
        ]
        result = await code_ai._subprocess実行(self._jsonl_command(events), cwd=str(PROJECT_ROOT), timeout=10)
        self.assertEqual("Copilot実行エラー: 認証エラー", result)
        streamed = [m["メッセージ内容"] for m in parent.接続.messages]
        self.assertIn("[Copilot tool] 端末出力", streamed)
        self.assertIn("[Copilot tool] bash 失敗: ツールエラー", streamed)
        output = self.module._CopilotJSON出力()
        with self.assertLogs(level="WARNING"):
            self.assertEqual(["[Copilot] JSON出力を解析できませんでした。"], output.解析("{broken"))
        for line in ("[]", "null", '{"type":"assistant.message","data":null}'):
            self.assertEqual([], output.解析(line))
        self.assertEqual("", output.回答)

    async def test_copilot_process_failure_is_reported(self):
        code_ai, parent = self._code_ai("copilot_cli")
        command = [sys.executable, "-c", "import sys; print('起動エラー',file=sys.stderr); sys.exit(1)"]
        result = await code_ai._subprocess実行(command, cwd=str(PROJECT_ROOT), timeout=10)
        self.assertEqual("Copilot実行エラー: 起動エラー", result)
        self.assertEqual(["起動エラー"], [m["メッセージ内容"] for m in parent.接続.messages])

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
