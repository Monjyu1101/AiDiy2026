# -*- coding: utf-8 -*-

import importlib
import logging
import os
from pathlib import Path
import sys
import tempfile
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
        ), patch.object(
            self.module, "_バックアップ保存版パス確認", return_value="backup/test"
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

    async def test_shared_verification_saves_and_renames_inside_execution_project(self):
        native = importlib.import_module("AIコア.AIバックアップ")
        providers = ("copilot_cli", "codex_cli", "claude_cli", "claude_sdk",
                     "antigravity_cli", "grok_cli", "opencode_cli", "aidiy_hermes")
        for provider in providers:
            for incremental in (False, True):
                with self.subTest(provider=provider, incremental=incremental):
                    self.setUp()
                    with tempfile.TemporaryDirectory(prefix="aidiy verification ") as directory:
                        root = Path(directory) / "_global"
                        (root / "src").mkdir(parents=True)
                        (root / "_AIDIY/knowledge").mkdir(parents=True)
                        source = root / "src/main.py"
                        source.write_text("before", encoding="utf-8")
                        original_time = source.stat().st_mtime - 120
                        os.utime(source, (original_time, original_time))
                        knowledge = root / "_AIDIY/knowledge/example.md"
                        knowledge.write_text("再利用ナレッジ", encoding="utf-8")
                        os.utime(knowledge, (original_time, original_time))
                        settings = {"CODE_BASE_PATH": str(root)}
                        if incremental:
                            baseline = native.バックアップ実行(セッション設定=settings, ログ出力=False)
                            self.assertTrue(baseline[3])
                        source.write_text("after", encoding="utf-8")
                        changed_time = original_time + 60
                        os.utime(source, (changed_time, changed_time))
                        self.agent.AI_NAME = provider
                        self.agent.絶対パス = str(root)
                        # 古い設定が _AIDIY を向いていても、実際のCLI実行先を使う。
                        original_settings = {"CODE_BASE_PATH": str(root / "_AIDIY")}
                        self.agent.接続.モデル設定 = original_settings
                        self.agent.親 = types.SimpleNamespace(conf=types.SimpleNamespace(json=original_settings))
                        saved = []

                        async def verify(**kwargs):
                            prompt = kwargs["要求テキスト"]
                            self.assertEqual(kwargs["絶対パス"], str(root))
                            expected = {"src/main.py"} if incremental else {"src/main.py", "_AIDIY/knowledge/example.md"}
                            self.assertEqual(set(kwargs["変更ファイル一覧"]), expected)
                            self.assertIn(f"プロジェクトルート（差分ファイルの基準）: {root}", prompt)
                            self.assertIn("_AIDIY/backup へは保存・移動しない", prompt)
                            self.assertIn("親フォルダ内だけ", prompt)
                            self.assertIn("先頭の時刻と .all", prompt)
                            prefix = "バックアップ保存先（絶対パス）: "
                            target = Path(next(line[len(prefix):] for line in prompt.splitlines() if line.startswith(prefix)))
                            self.assertTrue(target.is_relative_to(root / "backup"))
                            self.assertEqual(target.name.endswith(".all"), not incremental)
                            self.assertEqual((target / "src/main.py").read_text(encoding="utf-8"), "after")
                            # AIのリネームを模擬し、保存場所と時刻接頭辞を維持する。
                            renamed = target.with_name(target.name + ".検証")
                            target.rename(renamed)
                            saved.append(renamed)
                            return "検証完了"

                        self.ai.実行 = AsyncMock(side_effect=verify)
                        with patch.object(self.module.asyncio, "sleep", new_callable=AsyncMock):
                            updated = await self.agent._バックアップ検証ループ(self.ai, 1)
                        self.assertTrue(updated)
                        self.ai.実行.assert_awaited_once()
                        self.assertEqual(len(saved), 1)
                        self.assertEqual(self.module._バックアップ保存版パス確認(str(saved[0]).removesuffix(".検証")), str(saved[0]))
                        self.assertFalse((root / "_AIDIY/backup").exists())
                        self.assertEqual(self.agent.接続.モデル設定, original_settings)
                        # リネーム後も日時判定が機能し、同じ差分を再保存しない。
                        repeated = native.バックアップ実行(セッション設定=settings, ログ出力=False)
                        self.assertEqual(repeated[2], [])

    async def test_verification_without_execution_path_uses_session_project(self):
        self.agent.絶対パス = ""
        self.agent.接続.モデル設定["CODE_BASE_PATH"] = str(BACKEND_DIR.parent)
        backup = await self.run_request({"self_check_loop": 1}, differences_remain=True)
        self.assertEqual(backup.call_args.kwargs["セッション設定"]["CODE_BASE_PATH"], str(BACKEND_DIR.parent))
        self.assertEqual(self.ai.実行.await_args.kwargs["絶対パス"], str(BACKEND_DIR.parent))

    async def test_verification_reports_backup_relocated_by_ai(self):
        native = importlib.import_module("AIコア.AIバックアップ")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "main.py").write_text("source", encoding="utf-8")
            self.agent.絶対パス = str(root)
            original = native.バックアップ実行
            saved = []

            def backup(**kwargs):
                result = original(**kwargs)
                saved.append(Path(result[4]))
                return result

            async def move_backup(**kwargs):
                destination = root / "_AIDIY/backup" / saved[0].parent.name / saved[0].name
                destination.parent.mkdir(parents=True)
                saved[0].rename(destination)
                return "検証完了"

            self.ai.実行 = AsyncMock(side_effect=move_backup)
            with patch.object(self.module, "バックアップ実行", side_effect=backup), patch.object(
                self.module.asyncio, "sleep", new_callable=AsyncMock
            ), self.assertLogs(self.module.logger, level="WARNING") as logs:
                await self.agent._バックアップ検証ループ(self.ai, 1)
            self.assertTrue(any("元の親フォルダ内に見つかりません" in line for line in logs.output))
            self.assertIsNone(self.module._バックアップ保存版パス確認(str(saved[0])))


if __name__ == "__main__":
    unittest.main()
