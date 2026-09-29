import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "backend_server"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from conf.conf_model import conf_models


class HermesModelOptionsTest(unittest.TestCase):
    def test_choices_match_bat_with_oauth_provider(self):
        bat = (ROOT / "scripts/cli_bat/_hermes.bat").read_text(encoding="utf-8")
        bat_models = re.findall(
            r'^if "%MODEL_NUMBER%"=="\d+" set "MODEL=([^"]+)"',
            bat,
            flags=re.MULTILINE,
        )
        self.assertEqual(bat_models, ["gpt-6-astra", "gpt-6.1-sol", "gpt-5.6-terra", "gpt-6-luna"])

        models = conf_models._get_aidiy_hermes_models(object.__new__(conf_models))
        self.assertEqual(list(models), ["auto", *(f"openai_oauth/{model}" for model in bat_models)])


if __name__ == "__main__":
    unittest.main()
