import json
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "backend_server"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from conf.conf_model import conf_models


class HermesModelOptionsTest(unittest.TestCase):
    def test_cli_configs_and_defaults_match_bat_choices(self):
        with patch.object(conf_models, "_sync_local_model_configs"):
            models = conf_models()
        expected_gpt_models = ["gpt-6-astra", "gpt-6.1-sol", "gpt-6-sol", "gpt-5.6-terra", "gpt-6-luna"]
        for cli, defaults in (
            ("codex", models.CODE_CODEX_CLI_MODELS),
            ("copilot", models.CODE_COPILOT_CLI_MODELS),
        ):
            with self.subTest(cli=cli):
                bat = (ROOT / f"scripts/cli_bat/_{cli}_cli.bat").read_text(encoding="utf-8")
                choices = re.findall(r'^if "%MODEL_NUMBER%"=="(\d+)" set "MODEL=([^"]+)"', bat, re.MULTILINE)
                self.assertEqual([int(number) for number, _ in choices], list(range(1, len(choices) + 1)))
                bat_models = [model for _, model in choices]
                self.assertEqual(bat_models[:5], expected_gpt_models)
                config = json.loads((ROOT / f"_config/AiDiy_code_{cli}_cli.json").read_text(encoding="utf-8"))
                self.assertEqual(list(config["models"]), ["auto", *bat_models])
                self.assertEqual(list(defaults), ["auto", *bat_models])

    def test_choices_match_bat_with_oauth_provider(self):
        bat = (ROOT / "scripts/cli_bat/_hermes.bat").read_text(encoding="utf-8")
        bat_models = re.findall(
            r'^if "%MODEL_NUMBER%"=="\d+" set "MODEL=([^"]+)"',
            bat,
            flags=re.MULTILINE,
        )
        self.assertEqual(bat_models, ["gpt-6-astra", "gpt-6.1-sol", "gpt-6-sol", "gpt-5.6-terra", "gpt-6-luna"])

        models = conf_models._get_aidiy_hermes_models(object.__new__(conf_models))
        self.assertEqual(list(models), ["auto", *(f"openai_oauth/{model}" for model in bat_models)])


if __name__ == "__main__":
    unittest.main()
