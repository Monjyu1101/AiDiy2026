# -*- coding: utf-8 -*-

import importlib
import logging
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import AsyncMock, Mock, patch


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))


class CodeVerificationTest(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        log_stub = types.ModuleType("log_config")
        log_stub.get_logger = logging.getLogger
        with patch.dict(sys.modules, {"log_config": log_stub}):
            cls.module = importlib.import_module("AIコア.AIコード")

    def setUp(self):
        with patch.object(self.module, "_load_or_create_code_context", return_value=""), patch.object(
            self.module.CodeAgent, "_select_ai_module", return_value=None
        ):
            self.agent = self.module.CodeAgent(
                セッションID="verification-test", チャンネル="1",
                接続=types.SimpleNamespace(
                    モデル設定={"CODE_SELF_CHECK_LOOP": 2}, send_to_channel=AsyncMock()
                ),
                保存関数=Mock(),
            )
        self.ai = types.SimpleNamespace(実行=AsyncMock(return_value="実行完了"))
        self.agent._ensure_ai_instance = AsyncMock(return_value=self.ai)
        self.agent._生成ファイル通知 = AsyncMock()
        self.agent._update_info送信 = AsyncMock()

    async def run_request(self, attributes, differences_remain=False):
        # 実バックアップや外部AIを実行せず、通常処理と検証ループを通す。
        difference = ("time", ["sample.py"], ["sample.py"], False, "backup/test")
        results = None if differences_remain else [
            difference, ("time", ["sample.py"], [], False, "backup/test"),
        ]
        with patch.object(self.module, "バックアップ実行", return_value=difference, side_effect=results) as backup, patch.object(
            self.module.asyncio, "sleep", new_callable=AsyncMock
        ):
            result = await self.agent._基本AI処理({
                "メッセージ識別": "input_text", "メッセージ内容": "変更依頼", **attributes,
            })
        self.assertEqual("実行完了", result)
        self.agent._生成ファイル通知.assert_awaited()
        return backup

    async def test_zero_skips_backup_and_verification_for_both_request_types(self):
        for request_type in ("input_text", "input_request"):
            with self.subTest(request_type=request_type):
                self.setUp()
                backup = await self.run_request({"メッセージ識別": request_type, "self_check_loop": 0})
                backup.assert_not_called()
                self.ai.実行.assert_awaited_once()
                self.agent._update_info送信.assert_not_awaited()

    async def test_omitted_and_invalid_keep_session_setting(self):
        for attributes in ({}, {"self_check_loop": None}, {"self_check_loop": "invalid"}):
            with self.subTest(attributes=attributes):
                self.setUp()
                backup = await self.run_request(attributes)
                self.assertEqual(2, backup.call_count)
                self.assertEqual(2, self.ai.実行.await_count)
                self.assertIn("【1回目の検証】", self.ai.実行.await_args.kwargs["要求テキスト"])
                self.agent._update_info送信.assert_awaited_once()

    async def test_omitted_respects_zero_loop_setting(self):
        self.agent.接続.モデル設定["CODE_SELF_CHECK_LOOP"] = 0
        backup = await self.run_request({})
        backup.assert_not_called()
        self.ai.実行.assert_awaited_once()

    async def test_zero_does_not_change_next_request_or_session_setting(self):
        await self.run_request({"self_check_loop": 0})
        backup = await self.run_request({})
        self.assertEqual(2, backup.call_count)
        self.assertEqual(2, self.agent.接続.モデル設定["CODE_SELF_CHECK_LOOP"])

    async def test_selected_count_overrides_session_and_limits_verification(self):
        for count in (1, 2, 3):
            for request_type in ("input_text", "input_request"):
                with self.subTest(count=count, request_type=request_type):
                    self.setUp()
                    self.agent.接続.モデル設定["CODE_SELF_CHECK_LOOP"] = 0
                    backup = await self.run_request({
                        "メッセージ識別": request_type, "self_check_loop": count,
                    }, differences_remain=True)
                    self.assertEqual(count, backup.call_count)
                    self.assertEqual(1 + count, self.ai.実行.await_count)
                    self.assertIn(f"【{count}回目の検証】", self.ai.実行.await_args.kwargs["要求テキスト"])
                    self.assertEqual(0, self.agent.接続.モデル設定["CODE_SELF_CHECK_LOOP"])

    async def test_selected_count_stops_when_no_differences_remain(self):
        backup = await self.run_request({"self_check_loop": 3})
        self.assertEqual(2, backup.call_count)
        self.assertEqual(2, self.ai.実行.await_count)

    async def test_request_count_is_limited_to_zero_through_three(self):
        for requested, expected in ((-1, 0), (4, 3)):
            with self.subTest(requested=requested):
                self.setUp()
                backup = await self.run_request({"self_check_loop": requested}, differences_remain=True)
                self.assertEqual(expected, backup.call_count)
                self.assertEqual(1 + expected, self.ai.実行.await_count)


if __name__ == "__main__":
    unittest.main()
