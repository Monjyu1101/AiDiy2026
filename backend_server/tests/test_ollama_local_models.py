from pathlib import Path
import subprocess
import sys
import time
import unittest
from unittest.mock import patch


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from conf.conf_model import conf_models


class OllamaLocalModelsTest(unittest.TestCase):
    def make_models(self):
        models = object.__new__(conf_models)
        models.ollama_models = {"previous": "previous"}
        return models

    def test_reads_utf8_model_names_from_command_output(self):
        def run(command, **kwargs):
            self.assertEqual(command, ["ollama", "list"])
            kwargs["stdout"].write("NAME ID SIZE MODIFIED\n日本語モデル:latest abc 1GB now\n".encode("utf-8"))
            return subprocess.CompletedProcess(command, 0)

        models = self.make_models()
        with patch("subprocess.run", side_effect=run):
            result = models.get_ollama_models()
        self.assertEqual(list(result), ["日本語モデル:latest"])
        self.assertEqual(models.ollama_models, result)

    def test_timeout_returns_while_descendant_keeps_output_handles_open(self):
        # 実子プロセスが起動した孫プロセスに出力を継承させる。
        # PIPEだと親終了後も孫の終了まで待つが、一時ファイルなら待たない。
        child_code = (
            "import os, subprocess, sys, time; "
            "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(4)'], "
            "stdout=sys.stdout, stderr=sys.stderr, "
            "creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0); "
            "time.sleep(4)"
        )
        real_run = subprocess.run

        def run(command, **kwargs):
            kwargs["timeout"] = 0.5
            return real_run([sys.executable, "-c", child_code], **kwargs)

        models = self.make_models()
        started = time.monotonic()
        with patch("subprocess.run", side_effect=run):
            self.assertEqual(models.get_ollama_models(), {})
        self.assertLess(time.monotonic() - started, 2)
        self.assertEqual(models.ollama_models, {})


if __name__ == "__main__":
    unittest.main()
