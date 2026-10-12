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


class CodexModelOptionsTest(unittest.TestCase):
    def test_all_cli_catalogs_include_same(self):
        with tempfile.TemporaryDirectory() as temp_dir, patch.object(conf_models, "_config_dir_path", return_value=temp_dir):
            config = conf_models()
            config.ollama_models = {"test-model": "test-model"}
            models = config.get_code_models()
            for path in Path(temp_dir).glob("AiDiy_code*.json"):
                saved = json.loads(path.read_text(encoding="utf-8"))["models"]
                self.assertNotIn("auto", saved)
                self.assertNotIn("same", saved)
        for provider in ("claude_sdk", "codex_cli", "claude_cli", "copilot_cli", "antigravity_cli", "grok_cli", "opencode_cli", "aidiy_hermes", "claude_ollama", "codex_ollama"):
            with self.subTest(provider=provider):
                self.assertEqual(models[provider]["auto"], "auto (自動判定)")
                self.assertEqual(models[provider]["same"], "same (変更なし)")
                self.assertEqual(list(models[provider])[:2], ["auto", "same"])

    def test_choices_and_config_match_bat(self):
        bat = (ROOT / "scripts/cli_bat/_codex_cli.bat").read_text(encoding="utf-8")
        bat_models = re.findall(
            r'^if "%MODEL_NUMBER%"=="\d+" set "MODEL=([^"]+)"',
            bat,
            flags=re.MULTILINE,
        )
        self.assertEqual(bat_models, ["gpt-6-astra", "gpt-6.1-sol", "gpt-5.6-terra", "gpt-6-luna"])

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "AiDiy_code_codex_cli.json"
            config_path.write_text(
                json.dumps({"models": {"auto": "auto", "gpt-5.6-sol": "old"}}),
                encoding="utf-8",
            )
            with patch.object(conf_models, "_config_dir_path", return_value=temp_dir):
                models = conf_models().get_code_models()["codex_cli"]

            saved = json.loads(config_path.read_text(encoding="utf-8"))["models"]

        self.assertEqual(list(models), ["auto", "same", *bat_models])
        self.assertEqual(models["same"], "same (変更なし)")
        self.assertEqual(models["auto"], "auto (自動判定)")
        self.assertEqual(saved, {key: value for key, value in models.items() if key not in ("auto", "same")})

    def test_display_labels_do_not_depend_on_saved_aliases(self):
        with tempfile.TemporaryDirectory() as temp_dir, patch.object(conf_models, "_config_dir_path", return_value=temp_dir):
            path = Path(temp_dir) / "AiDiy_code_claude_sdk.json"
            path.write_text(json.dumps({"models": {"sonnet": "Sonnet", "auto": "yyyy/mm/dd auto", "same": "same"}}), encoding="utf-8")
            config = conf_models()
            models = config.get_code_models()["claude_sdk"]
            self.assertEqual(list(models), ["auto", "same", "sonnet"])
            self.assertEqual(models["auto"], "auto (自動判定)")
            self.assertEqual(models["same"], "same (変更なし)")
            self.assertEqual(models["sonnet"], "Sonnet")
            self.assertEqual(config.CODE_CLAUDE_SDK_MODELS["auto"], "yyyy/mm/dd auto")


if __name__ == "__main__":
    unittest.main()
