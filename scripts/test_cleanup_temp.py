"""一時フォルダの再帰削除と、プロジェクト外を削除しない境界を確認する。"""

import importlib.util
import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("aidiy_cleanup_temp_test", ROOT / "_cleanup.py")
cleanup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cleanup)


class CleanupTempTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.root = self.base / "project"
        self.root.mkdir()
        self.output = io.StringIO()
        stdout = patch("sys.stdout", self.output)
        stdout.start()
        self.addCleanup(stdout.stop)

    def make_file(self, relative, root=None):
        path = (root or self.root) / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("keep or remove", encoding="utf-8")
        return path

    def directory_link(self, link, target):
        if os.name == "nt":
            subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(link), str(target)],
                check=True, capture_output=True,
            )
        else:
            link.symlink_to(target, target_is_directory=True)

    def test_recursive_names_and_preserved_neighbors(self):
        removed = [self.make_file(name + "/sample.log") for name in (
            "temp", "_temp", ".temp", "a/temp", "a/.hidden/b/_temp", "b/c/.temp",
            "backend_tools/aidiy_automations/temp", "backup/old/temp", "node_modules/example/temp",
        )]
        kept = [self.make_file(name) for name in (
            "templates/example.py", "temp_data/data.txt", "tmp/sample.txt", "a/temp.txt",
            "file-parent/temp", ".git/objects/temp/sentinel", "_data/database.db",
        )]
        self.assertTrue(cleanup.cleanup_temp_directories(self.root))
        self.assertTrue(all(not path.exists() for path in removed))
        self.assertTrue(all(path.exists() for path in kept))
        self.assertTrue(self.root.is_dir())
        self.assertTrue(cleanup.cleanup_temp_directories(self.root))

    def test_nested_temp_is_deleted_once(self):
        self.make_file("temp/a/_temp/.temp/sample.log")
        self.assertEqual(cleanup.find_temp_directories(self.root), [self.root / "temp"])
        with patch.object(cleanup, "remove_directory", wraps=cleanup.remove_directory) as remove:
            self.assertTrue(cleanup.cleanup_temp_directories(self.root))
        self.assertEqual(remove.call_count, 1)

    def test_directory_links_are_not_followed(self):
        external = self.base / "external"
        sentinel = self.make_file("temp/sentinel.txt", external)
        self.directory_link(self.root / "linked", external)
        self.directory_link(self.root / ".temp", external)
        self.assertEqual(cleanup.find_temp_directories(self.root), [])
        self.assertTrue(cleanup.cleanup_temp_directories(self.root))
        self.assertTrue(sentinel.exists())

    def test_link_inside_temp_does_not_delete_its_target(self):
        external = self.base / "external"
        sentinel = self.make_file("sentinel.txt", external)
        (self.root / "temp").mkdir()
        self.directory_link(self.root / "temp/linked", external)
        self.assertTrue(cleanup.cleanup_temp_directories(self.root))
        self.assertFalse((self.root / "temp").exists())
        self.assertTrue(sentinel.exists())

    def test_deletion_rechecks_scope_and_links(self):
        external = self.base / "external"
        sentinel = self.make_file("sentinel.txt", external)
        alias = self.root / "temp"
        self.directory_link(alias, external)
        for unsafe in (external, self.root, alias):
            with self.subTest(path=unsafe), patch.object(cleanup, "find_temp_directories", return_value=[unsafe]):
                self.assertFalse(cleanup.cleanup_temp_directories(self.root))
            self.assertTrue(sentinel.exists())
            self.assertTrue(self.root.is_dir())

    def test_scan_failure_and_delete_failure_are_reported(self):
        self.make_file("temp/sample.log")
        with patch.object(cleanup.os, "walk", side_effect=PermissionError("cannot scan")):
            self.assertFalse(cleanup.cleanup_temp_directories(self.root))
        with patch.object(cleanup, "remove_directory", return_value=False):
            self.assertFalse(cleanup.cleanup_temp_directories(self.root))
        self.assertTrue((self.root / "temp/sample.log").exists())

    def run_root_cleanup(self, stop):
        choices = dict.fromkeys((
            "npm_uninstall", "backup", "local", "tools", "backend", "taskteam", "web",
            "avatar", "hermes", "vscode", "discord",
        ), False)
        with patch.object(cleanup, "stop_all_services", side_effect=stop), \
                patch.object(cleanup, "_remove_folder_import_cache"), \
                patch.object(cleanup, "_remove_root_python_caches"), \
                patch.object(cleanup.time, "sleep"):
            return cleanup.execute_cleanup(self.root, choices)

    def test_root_cleanup_runs_after_stop_even_when_folders_are_skipped(self):
        target = self.make_file("nested/.temp/sample.log")
        stops = []

        def stop(_choices):
            self.assertTrue(target.exists())
            stops.append(True)

        self.assertTrue(self.run_root_cleanup(stop))
        self.assertEqual(stops, [True])
        self.assertFalse(target.exists())

    def test_failed_stop_prevents_deletion(self):
        target = self.make_file("nested/temp/sample.log")
        with self.assertRaises(RuntimeError):
            self.run_root_cleanup(RuntimeError("cannot stop"))
        self.assertTrue(target.exists())

    def test_root_cleanup_propagates_temp_failure(self):
        with patch.object(cleanup, "cleanup_temp_directories", return_value=False):
            self.assertFalse(self.run_root_cleanup(lambda _choices: None))


if __name__ == "__main__":
    unittest.main()
