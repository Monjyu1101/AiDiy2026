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


class GrokModelOptionsTest(unittest.TestCase):
    def test_choices_and_config_match_bat(self):
        bat = (ROOT / "scripts/cli_bat/_grok_cli.bat").read_text(encoding="utf-8")
        bat_models = re.findall(
            r'^if "%MODEL_NUMBER%"=="\d+" set "MODEL=([^"]+)"',
            bat,
            flags=re.MULTILINE,
        )
        self.assertEqual(bat_models, ["grok-4.6", "grok-4.7"])

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "AiDiy_code_grok_cli.json"
            config_path.write_text(
                json.dumps({"models": {"auto": "auto", "grok-4.5": "old"}}),
                encoding="utf-8",
            )
            with patch.object(conf_models, "_config_dir_path", return_value=temp_dir):
                models = conf_models().get_code_models()["grok_cli"]

            saved = json.loads(config_path.read_text(encoding="utf-8"))["models"]

        self.assertEqual(list(models), ["auto", *bat_models])
        self.assertEqual(saved, models)


if __name__ == "__main__":
    unittest.main()
