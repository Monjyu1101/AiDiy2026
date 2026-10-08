"""アバターの二重起動が既存プロセスを停止しないことを確認する。"""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "_start.py"
spec = importlib.util.spec_from_file_location("avatar_start_test", SCRIPT)
start = importlib.util.module_from_spec(spec)
spec.loader.exec_module(start)


class AvatarStartTest(unittest.TestCase):
    def test_other_process_is_rejected_and_exit_releases_lock(self):
        with tempfile.TemporaryDirectory(prefix="avatar start ") as folder:
            path = Path(folder) / "avatar.lock"
            code = (
                "import importlib.util; from pathlib import Path; "
                f"spec=importlib.util.spec_from_file_location('avatar_start', {str(SCRIPT)!r}); "
                "module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); "
                f"ctx=module.avatar_start_lock(Path({str(path)!r})); "
                "print(ctx.__enter__(), flush=True); ctx.__exit__(None,None,None)"
            )
            with start.avatar_start_lock(path) as owned:
                self.assertTrue(owned)
                result = subprocess.run([sys.executable, "-X", "utf8", "-c", code], capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), "False")
            with start.avatar_start_lock(path) as owned:
                self.assertTrue(owned)

    def test_existing_renderer_is_preserved(self):
        with patch.object(start.socket, "create_connection"), patch.object(start, "kill_ports") as stop, patch.object(start, "start") as launch:
            start._main()
            stop.assert_not_called()
            launch.assert_not_called()

    def test_duplicate_does_not_check_environment_or_cleanup(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "avatar.lock"
            real_lock = start.avatar_start_lock
            with real_lock(path), patch.object(start, "avatar_start_lock", side_effect=lambda: real_lock(path)), patch.object(
                start, "_main"
            ) as launch, patch.object(start.sys, "argv", ["aidiy_avatar"]):
                start.main()
                launch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
