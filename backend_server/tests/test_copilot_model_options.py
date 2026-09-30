import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "backend_server"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from conf.conf_model import conf_models


class CopilotModelOptionsTest(unittest.TestCase):
    def test_choices_match_bat_even_when_local_config_has_only_auto(self):
        bat = (ROOT / "scripts/cli_bat/_copilot_cli.bat").read_text(encoding="utf-8")
        bat_models = re.findall(
            r'^if "%MODEL_NUMBER%"=="\d+" set "MODEL=([^"]+)"',
            bat,
            flags=re.MULTILINE,
        )
        self.assertEqual(len(bat_models), 10)
        self.assertIn("claude-opus-5.5", bat_models)
        self.assertIn("claude-sonnet-5.5", bat_models)
        self.assertNotIn("gemini-3.7-flash", bat_models)

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "AiDiy_code_copilot_cli.json"
            config_path.write_text(
                '{"models": {"auto": "auto"}}', encoding="utf-8",
            )
            with patch.object(conf_models, "_config_dir_path", return_value=temp_dir):
                models = conf_models().get_code_models()["copilot_cli"]
            saved = json.loads(config_path.read_text(encoding="utf-8"))["models"]

        self.assertEqual(list(models), ["auto", *bat_models])
        self.assertEqual(saved, models)


if __name__ == "__main__":
    unittest.main()
