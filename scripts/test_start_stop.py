"""ルート `_start.py` の Ctrl+C 時の全停止（`_cleanup.stop_all_services` と同じ手順）を確認する。"""
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("aidiy_start_stop_test", ROOT / "_start.py")
start = importlib.util.module_from_spec(spec)
spec.loader.exec_module(start)


class StopAllTasksTest(unittest.TestCase):
    def run_with_cleanup(self, source: str) -> tuple[Path, str]:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        folder = Path(temporary.name)
        (folder / "_cleanup.py").write_text(source, encoding="utf-8")
        output = io.StringIO()
        with patch.object(start, "BASE_DIR", folder), patch("sys.stdout", output):
            start.stop_all_tasks()
        return folder, output.getvalue()

    def test_ctrl_c_uses_the_same_stop_as_cleanup(self):
        folder, _ = self.run_with_cleanup(
            "from pathlib import Path\n"
            "def stop_all_services(choices):\n"
            "    Path(__file__).with_name('called.txt').write_text(repr(choices), encoding='utf-8')\n"
        )
        self.assertEqual((folder / "called.txt").read_text(encoding="utf-8"), "{}")

    def test_stop_failure_is_reported_without_raising(self):
        _, output = self.run_with_cleanup(
            "def stop_all_services(choices):\n"
            "    raise RuntimeError('Code / Live の単独実行を終了できません')\n"
        )
        self.assertIn("一部のタスクを停止できませんでした", output)
        self.assertIn("Code / Live の単独実行を終了できません", output)


if __name__ == "__main__":
    unittest.main()
