# -*- coding: utf-8 -*-
"""大量の対象ファイルでコピー前に中止し、境界未満は保存できることを確認する。"""

import importlib.util
import logging
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[2]


def _load_module(name, path):
    log_config = types.ModuleType("log_config")
    log_config.get_logger = logging.getLogger
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"log_config": log_config}):
        spec.loader.exec_module(module)
    return module


class BackupFileLimitTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = _load_module(
            "backup_file_limit_test", ROOT / "backend_server/AIコア/AIバックアップ.py"
        )
        cls.wrapper = _load_module(
            "backup_save_limit_test", ROOT / "backend_tools/tools_proc/backup.py"
        )

    def test_limit_cancels_full_and_incremental_backups_before_copy(self):
        for count in (50_000, 50_001):
            for previous in (None, (2.0, "1970-01-01 00:00:02")):
                with self.subTest(count=count, previous=previous):
                    with tempfile.TemporaryDirectory() as directory:
                        scanned = []

                        def file_names():
                            for index in range(count):
                                scanned.append(index)
                                yield f"file{index}.txt"

                        walk = [(directory, [], file_names())]
                        with (
                            patch.object(self.native.os, "walk", return_value=walk),
                            patch.object(self.native.os.path, "getmtime", return_value=1.0),
                            patch.object(self.native, "_バックアップ全体の最終日時取得", return_value=previous),
                            patch.object(self.native, "_ファイルコピー実行") as copy,
                            self.assertLogs(self.native.logger, level="ERROR") as logs,
                        ):
                            result = self.native.バックアップ実行(
                                セッション設定={"CODE_BASE_PATH": directory}, ログ出力=False
                            )
                        self.assertIsNone(result)
                        self.assertEqual(len(scanned), 50_000)
                        copy.assert_not_called()
                        self.assertFalse((Path(directory) / "backup").exists())
                        self.assertEqual(len(logs.output), 1)
                        self.assertIn("バックアップキャンセル", logs.output[0])
                        self.assertIn("50,000件以上", logs.output[0])
                        self.assertIn(directory, logs.output[0])

    def test_below_limit_keeps_full_and_incremental_backups(self):
        for previous in (None, (1.0, "1970-01-01 00:00:01")):
            with self.subTest(previous=previous):
                with tempfile.TemporaryDirectory() as directory:
                    names = (f"file{index}.txt" for index in range(49_999))
                    with (
                        patch.object(self.native.os, "walk", return_value=[(directory, [], names)]),
                        patch.object(self.native.os.path, "getmtime", return_value=2.0),
                        patch.object(self.native, "_バックアップ全体の最終日時取得", return_value=previous),
                        patch.object(self.native, "_ファイルコピー実行", return_value=True) as copy,
                    ):
                        result = self.native.バックアップ実行(
                            セッション設定={"CODE_BASE_PATH": directory}, ログ出力=False
                        )
                    self.assertEqual(len(result[1]), 49_999)
                    self.assertEqual(len(result[2]), 49_999)
                    self.assertEqual(result[3], previous is None)
                    copy.assert_called_once()

    def test_excluded_files_do_not_count_toward_limit(self):
        names = ["ignored.pyc", "ignored.log", "package-lock.json", "keep.txt"]
        with (
            patch.object(self.native.os, "walk", return_value=[("/project", [], names)]),
            patch.object(self.native.os.path, "getmtime", return_value=1.0),
        ):
            files = self.native._全ファイルスキャン("/project", 最大件数=2)
        self.assertEqual([item["パス"] for item in files], ["keep.txt"])

    def test_cancellation_is_reported_as_error_to_mcp_callers(self):
        saver = self.wrapper.BackupSave()
        saver._native = Mock()
        saver._native.バックアップ実行.return_value = None
        result = saver.run()
        self.assertFalse(result["ok"])
        self.assertIn("中止", result["error"])
        self.assertEqual(result["バックアップ件数"], 0)

    def test_common_log_reports_cancellation_instead_of_completion(self):
        caller = Mock()
        with patch.object(self.native, "バックアップ実行", return_value=None):
            result = self.native.バックアップ実行_共通ログ(呼出しロガー=caller)
        self.assertIsNone(result)
        messages = [call.args[0] for call in caller.info.call_args_list]
        self.assertTrue(any("バックアップ中止" in message for message in messages))
        self.assertFalse(any("バックアップ終了" in message for message in messages))


if __name__ == "__main__":
    unittest.main()
