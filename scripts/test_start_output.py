# -*- coding: utf-8 -*-
"""起動ログのUTF-8分割、行境界、複数サービスの出力を検証する。"""
import importlib.util
import io
from pathlib import Path
import threading
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("aidiy_start_output_test", ROOT / "_start.py")
start = importlib.util.module_from_spec(spec)
spec.loader.exec_module(start)


class FragmentedStream(io.BytesIO):
    def read(self, size=-1):
        return super().read(min(size, 1))


class StartOutputTest(unittest.TestCase):
    def capture(self, stream):
        output = io.StringIO()
        times = {}
        with patch.object(start.sys, "stdout", output):
            start.stream_output("core", stream, times)
        return output.getvalue(), times

    def test_japanese_split_at_every_byte_keeps_one_prefix_per_line(self):
        text = "セッションID=確認\r\n次のログ\n"
        output, times = self.capture(FragmentedStream(text.encode("utf-8")))
        prefix = f"{start.Colors.OKCYAN}[core]{start.Colors.ENDC} "
        self.assertEqual(output, prefix + "セッションID=確認\n" + prefix + "次のログ\n")
        self.assertIn("core", times)

    def test_1024_byte_boundary_and_final_line_without_newline(self):
        text = "x" * 1023 + "日本語\n末尾"
        output, _ = self.capture(io.BytesIO(text.encode("utf-8")))
        prefix = f"{start.Colors.OKCYAN}[core]{start.Colors.ENDC} "
        self.assertEqual(output, prefix + "x" * 1023 + "日本語\n" + prefix + "末尾\n")

    def test_services_with_partial_lines_keep_separate_output(self):
        barrier = threading.Barrier(2)

        class PausedStream(io.BytesIO):
            def read(self, size=-1):
                chunk = super().read(min(size, 2))
                if chunk:
                    barrier.wait(timeout=5)
                return chunk

        output = io.StringIO()
        with patch.object(start.sys, "stdout", output):
            threads = [threading.Thread(target=start.stream_output,
                       args=(name, PausedStream("日本\n".encode("utf-8")), {}))
                       for name in ("core", "tools")]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=10)
                self.assertFalse(thread.is_alive())
        self.assertCountEqual(output.getvalue().splitlines(), [
            f"{start.Colors.OKCYAN}[{name}]{start.Colors.ENDC} 日本" for name in ("core", "tools")
        ])


if __name__ == "__main__":
    unittest.main()
