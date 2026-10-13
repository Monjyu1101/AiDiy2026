# -*- coding: utf-8 -*-
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026

"""起動フォルダ・設定・MCPの指定によらず、保存と参照のルートが一致する。"""
import importlib.util
import logging
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


def load(name, path):
    log_config = types.ModuleType("log_config")
    log_config.get_logger = logging.getLogger
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"log_config": log_config}):
        spec.loader.exec_module(module)
    return module


class BackupProjectRootTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = load("backup_root_native", ROOT / "backend_server/AIコア/AIバックアップ.py")
        cls.wrapper = load("backup_root_wrapper", ROOT / "backend_tools/tools_proc/backup.py")

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        (self.root / "_AIDIY/knowledge").mkdir(parents=True)
        (self.root / "src").mkdir()
        (self.root / "src/main.py").write_text("print('初回')\n", encoding="utf-8")
        (self.root / "_AIDIY/knowledge/example.md").write_text("再利用ナレッジ\n", encoding="utf-8")
        native_loader = patch.object(self.wrapper, "_load_native_module", return_value=self.native)
        native_loader.start()
        self.addCleanup(native_loader.stop)

    def test_relative_config_and_session_paths_use_backend_directory_not_cwd(self):
        config = types.SimpleNamespace(json={"CODE_BASE_PATH": "../"})
        for cwd in (str(self.root), str(self.root / "_AIDIY")):
            with self.subTest(cwd=cwd), patch.object(os, "getcwd", return_value=cwd):
                result = self.native.バックアップ実行(
                    アプリ設定=config, backend_dir=str(self.root / "backend_server"), ログ出力=False
                )
                self.assertIsNotNone(result)
                self.assertEqual({item["パス"] for item in result[1]}, {"src/main.py", "_AIDIY/knowledge/example.md"})
                self.assertFalse((self.root / "_AIDIY/backup").exists())
        # セッション設定を優先し、相対パスも同じ基準で解決する。
        result = self.native.バックアップ実行(
            アプリ設定=types.SimpleNamespace(json={"CODE_BASE_PATH": "/missing"}),
            backend_dir=str(self.root / "backend_server"),
            セッション設定={"CODE_BASE_PATH": "../"}, ログ出力=False
        )
        self.assertIsNotNone(result)

    def test_save_scan_and_check_share_root_for_default_and_explicit_paths(self):
        with patch.object(self.wrapper, "_AIDIY_ROOT", str(self.root)):
            for selected in (None, str(self.root)):
                with self.subTest(selected=selected):
                    saver = self.wrapper.BackupSave(selected)
                    checker = self.wrapper.BackupCheck(selected)
                    self.assertEqual(saver.root, checker.root)
                    self.assertEqual(saver.root, str(self.root))
                    self.assertEqual(checker.backup_root, str(self.root / "backup"))
                    result = saver.run()
                    self.assertTrue(result["ok"])
                    if result["バックアップ先"]:
                        target = Path(result["バックアップ先"])
                        self.assertTrue(target.is_relative_to(self.root / "backup"))
                        self.assertEqual((target / "src/main.py").read_text(encoding="utf-8"), "print('初回')\n")
                    self.assertEqual(saver.diff_scan()["count"], 0)
                    self.assertEqual(checker.list_versions("src/main.py")["count"], 1)
                    self.assertFalse((self.root / "_AIDIY/backup").exists())

    def test_incremental_scan_and_save_use_root_relative_file_paths(self):
        saver = self.wrapper.BackupSave(str(self.root))
        saver.run()
        source = self.root / "src/main.py"
        changed = source.stat().st_mtime + 5
        source.write_text("print('更新')\n", encoding="utf-8")
        os.utime(source, (changed, changed))
        self.assertEqual(saver.diff_scan()["差分ファイル"], ["src/main.py"])
        scan = self.native.差分ファイル取得(
            アプリ設定=types.SimpleNamespace(json={"CODE_BASE_PATH": str(self.root / "_AIDIY")}),
            backend_dir=str(ROOT / "backend_server"),
            セッション設定={"CODE_BASE_PATH": str(self.root)},
        )
        self.assertEqual(scan[1], ["src/main.py"])
        result = saver.run()
        self.assertFalse(result["全件フラグ"])
        self.assertEqual(result["バックアップ件数"], 1)
        self.assertEqual((Path(result["バックアップ先"]) / "src/main.py").read_text(encoding="utf-8"), "print('更新')\n")

    def test_external_project_needs_no_backend_server_and_uses_installation_module(self):
        saver = self.wrapper.BackupSave(str(self.root))
        self.assertFalse((self.root / "backend_server").exists())
        self.assertEqual(saver.backend_dir, str(ROOT / "backend_server"))
        result = saver.run()
        self.assertTrue(result["ok"])
        self.assertTrue(Path(result["バックアップ先"]).is_relative_to(self.root / "backup"))

    def test_explicit_subfolder_remains_a_separate_backup_target(self):
        selected = self.root / "src"
        saver = self.wrapper.BackupSave(str(selected))
        checker = self.wrapper.BackupCheck(str(selected))
        self.assertEqual(saver.root, str(selected))
        self.assertEqual(checker.root, str(selected))
        self.assertTrue(saver.run()["ok"])
        self.assertEqual(checker.list_versions("main.py")["count"], 1)


if __name__ == "__main__":
    unittest.main()
