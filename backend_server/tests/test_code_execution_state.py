import asyncio
import importlib
import logging
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class CodeExecutionStateTest(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        log = types.ModuleType("log_config")
        log.get_logger = logging.getLogger
        with patch.dict(sys.modules, {"log_config": log}):
            cls.module = importlib.import_module("AIコア.AIコード")

    def setUp(self):
        self.packets = []

        async def send(channel, packet):
            self.packets.append(packet)

        with patch.object(self.module, "_load_or_create_code_context", return_value=""), patch.object(
            self.module.CodeAgent, "_select_ai_module", return_value=None
        ):
            self.agent = self.module.CodeAgent(
                セッションID="execution-state", チャンネル="1",
                接続=types.SimpleNamespace(send_to_channel=send),
            )
        self.ai = types.SimpleNamespace(強制終了=AsyncMock(), 開始=AsyncMock())
        self.agent.AIインスタンス = self.ai
        self.agent._ensure_ai_instance = AsyncMock(return_value=self.ai)

    def completed(self):
        return [p for p in self.packets if p["メッセージ識別"] == "output_end"]

    async def test_response_does_not_finish_request_before_verification_and_knowledge(self):
        verified, knowledge = asyncio.Event(), asyncio.Event()
        in_verification, in_knowledge = asyncio.Event(), asyncio.Event()

        async def basic(data):
            await self.agent.接続.send_to_channel("1", {"メッセージ識別":"output_text", "メッセージ内容":"回答"})
            in_verification.set()
            await verified.wait()
            return "回答"

        async def improve(**kwargs):
            in_knowledge.set()
            await knowledge.wait()

        self.agent._基本AI処理 = basic
        self.agent._自己改善書き込み実行 = improve
        task = asyncio.create_task(self.agent._実行状態つき要求処理({"メッセージ識別":"input_text"}))
        try:
            await asyncio.wait_for(in_verification.wait(), 1)
            self.assertTrue(self.packets[0]["実行中"])
            self.assertFalse(self.completed())
            verified.set()
            await asyncio.wait_for(in_knowledge.wait(), 1)
            self.assertFalse(self.completed())
            knowledge.set()
            await asyncio.wait_for(task, 1)
            self.assertEqual([False], [p["実行中"] for p in self.completed()])
        finally:
            verified.set(); knowledge.set()
            await task

    async def test_cancel_knowledge_waits_for_ai_restart_before_completion(self):
        started, restart = asyncio.Event(), asyncio.Event()
        self.agent._基本AI処理 = AsyncMock(return_value="回答")

        async def improve(**kwargs):
            started.set()
            await asyncio.Event().wait()

        async def resume():
            await restart.wait()

        self.agent._自己改善書き込み実行 = improve
        self.ai.開始.side_effect = resume
        task = asyncio.create_task(self.agent._実行状態つき要求処理({"メッセージ識別":"input_text"}))
        await asyncio.wait_for(started.wait(), 1)
        stop = asyncio.create_task(self.agent.強制停止())
        try:
            for _ in range(20):
                await asyncio.sleep(0)
            self.ai.開始.assert_awaited_once()
            self.assertFalse(self.completed())
            self.assertFalse(task.done())
            restart.set()
            self.assertTrue(await asyncio.wait_for(stop, 1))
            await asyncio.wait_for(task, 1)
            self.assertEqual([False], [p["実行中"] for p in self.completed()])
        finally:
            restart.set()
            await stop; await task

    async def test_task_finishing_during_force_exit_does_not_lose_task_reference(self):
        started, finish, exiting, exit_done = (asyncio.Event() for _ in range(4))

        async def basic(data):
            started.set()
            await finish.wait()
            return "回答"

        async def force_exit():
            exiting.set()
            await exit_done.wait()

        self.agent._基本AI処理 = basic
        self.agent._自己改善書き込み実行 = AsyncMock()
        self.ai.強制終了.side_effect = force_exit
        task = asyncio.create_task(self.agent._処理_input_text({"メッセージ内容":"依頼"}))
        await asyncio.wait_for(started.wait(), 1)
        stop = asyncio.create_task(self.agent.強制停止())
        try:
            await asyncio.wait_for(exiting.wait(), 1)
            finish.set()
            await asyncio.wait_for(task, 1)
            self.assertIsNone(self.agent.現在タスク)
            exit_done.set()
            self.assertTrue(await asyncio.wait_for(stop, 1))
            self.ai.開始.assert_awaited_once()
        finally:
            finish.set(); exit_done.set()
            await task; await stop

    async def test_worker_supports_opt_in_for_both_request_types(self):
        self.agent._処理_input_text = AsyncMock()
        self.agent._処理_input_request = AsyncMock()
        self.agent.is_alive = True
        worker = asyncio.create_task(self.agent._コード処理ワーカー())
        try:
            for kind in ("input_text", "input_request"):
                await self.agent.コード要求({"メッセージ識別":kind, "実行状態通知":True})
            await asyncio.wait_for(self.agent.コード処理Ｑ.join(), 1)
            self.assertEqual(2, len(self.completed()))
            self.agent._処理_input_text.assert_awaited_once()
            self.agent._処理_input_request.assert_awaited_once()
        finally:
            worker.cancel()
            await worker


if __name__ == "__main__":
    unittest.main()
