# -*- coding: utf-8 -*-
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1". See LICENSE.
"""一時プロジェクトだけで .backup_local の保存・参照・除外を検証する。"""

import importlib.util
import logging
import os
from pathlib import Path
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


backup = load_module("backup_local_tools_under_test", ROOT / "backend_tools/tools_proc/backup.py")
folder_status = load_module("backup_local_folders_under_test", ROOT / "backend_server/core_router/フォルダ状態.py")


class BackupLocalTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="aidiy-backup-local-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.saver = backup.BackupSave(str(self.root))
        # アプリのログ初期化とローカル Git 記録は実行せず、保存・走査・コピーは実装を使う。
        logging_stub = ModuleType("log_config")
        logging_stub.get_logger = logging.getLogger
        with patch.dict(sys.modules, {"log_config": logging_stub}):
            self.native = self.saver._get_native()
        git_record = patch.object(self.native, "_ローカルGit記録")
        git_record.start()
        self.addCleanup(git_record.stop)
        self.checker = backup.BackupCheck(str(self.root))

    def write(self, relative, content="fixture\n", mtime=1_800_000_000):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="")
        os.utime(path, (mtime, mtime))
        return path

    def test_first_save_uses_new_store_and_keeps_ordinary_backup_sources(self):
        self.write("main.txt", "first\n")
        self.write("backup/ordinary.txt")
        self.write("src/backup/nested.txt")
        # 旧名の日時フォルダを保存履歴として使わない。ここでは合成した通常ソースとして扱う。
        old_file = self.write("backup/20990101/000000.all/main.txt", "ordinary old-name fixture\n")

        result = self.saver.run()

        self.assertTrue(result["ok"])
        self.assertTrue(result["全件フラグ"])
        target = Path(result["バックアップ先"])
        self.assertTrue(target.is_relative_to(self.root / ".backup_local"))
        self.assertTrue(target.name.endswith(".all"))
        self.assertEqual(result["全件数"], 4)
        self.assertEqual((target / "main.txt").read_text(encoding="utf-8"), "first\n")
        self.assertTrue((target / "backup/ordinary.txt").is_file())
        self.assertTrue((target / "src/backup/nested.txt").is_file())
        self.assertEqual(old_file.read_text(encoding="utf-8"), "ordinary old-name fixture\n")
        self.assertFalse((self.root / ".git_local").exists())

    def test_second_save_and_mcp_queries_share_new_store(self):
        self.write("main.txt", "first\n")
        first = self.saver.run()
        self.assertTrue(first["ok"])
        self.assertEqual(self.saver.diff_scan()["count"], 0)
        self.assertTrue(self.saver.run()["差分なし"])

        self.write("main.txt", "second\n", mtime=1_800_000_010)
        scan = self.saver.diff_scan()
        self.assertEqual(scan["差分ファイル"], ["main.txt"])
        before = self.checker.get_before_after("main.txt")
        self.assertEqual(before["before"]["content"], "first\n")
        self.assertEqual(before["before"]["source"], "backup")
        self.assertEqual(before["after"]["content"], "second\n")

        second = self.saver.run()
        self.assertTrue(second["ok"])
        self.assertFalse(second["全件フラグ"])
        self.assertEqual(second["バックアップ件数"], 1)
        self.assertTrue(Path(second["バックアップ先"]).is_relative_to(self.root / ".backup_local"))
        self.assertFalse(Path(second["バックアップ先"]).name.endswith(".all"))
        self.assertEqual(self.saver.diff_scan()["count"], 0)
        self.assertEqual(self.checker.list_versions("main.txt")["count"], 2)
        changed = self.checker.find_changed("20000101_000000")
        self.assertEqual([item["path"] for item in changed["items"]], ["main.txt"])

    def test_old_store_is_not_a_reader_or_diff_fallback(self):
        self.write("main.txt", "current\n")
        self.write("backup/20990101/000000.all/main.txt", "not history\n")
        info = self.checker.backup_root_path()
        self.assertEqual(info["backup_root"], (self.root / ".backup_local").as_posix())
        self.assertFalse(info["exists"])
        self.assertIsNone(self.checker.get_before_after("main.txt")["before"])
        self.assertEqual(self.checker.list_versions("main.txt")["count"], 0)
        self.assertEqual(self.checker.find_changed("20000101_000000")["count"], 0)
        self.assertEqual(self.saver.diff_scan()["最終バックアップ日時"], "")
        self.assertFalse((self.root / ".backup_local").exists())

    def test_project_named_backup_is_not_excluded(self):
        self.write("backup/project/main.txt")
        project = self.root / "backup/project"
        saver = backup.BackupSave(str(project))
        saver._native = self.native
        result = saver.run()
        self.assertTrue(result["ok"])
        self.assertEqual(result["バックアップ件数"], 1)
        self.assertTrue(Path(result["バックアップ先"]).is_relative_to(project / ".backup_local"))

    def test_scanners_exclude_new_store_but_not_ordinary_backup(self):
        expected = {"main.txt", "backup/ordinary.txt", "src/backup/nested.txt"}
        for name in expected:
            self.write(name)
        self.write(".backup_local/20990101/000000.all/private.txt")
        self.write("src/.backup_local/private.txt")
        native = self.native._全ファイルスキャン(str(self.root))
        status = folder_status.状態走査(self.root)
        self.assertEqual({entry["パス"] for entry in native}, expected)
        self.assertEqual({entry["パス"] for entry in status["ファイル一覧"]}, expected)
        self.assertFalse(status["不完全"])
        self.assertIn(".backup_local", folder_status.規則["backupDirectories"])
        self.assertNotIn("backup", folder_status.規則["backupDirectories"])
        with self.assertRaises(ValueError):
            folder_status.状態走査(self.root, ".backup_local")

    def test_exclusion_is_relative_to_selected_project(self):
        for ancestor in ("temp", "log", "_AIDIY/aidiy_code"):
            with self.subTest(ancestor=ancestor):
                project = self.root / ancestor / "project"
                self.write(f"{ancestor}/project/main.txt")
                self.write(f"{ancestor}/project/temp/ignored.txt")
                self.write(f"{ancestor}/project/_AIDIY/aidiy_code/ignored.md")
                scanned = self.native._全ファイルスキャン(str(project))
                self.assertEqual({item["パス"] for item in scanned}, {"main.txt"})


if __name__ == "__main__":
    unittest.main()
