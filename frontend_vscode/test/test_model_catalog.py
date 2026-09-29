"""VS Code 拡張の外部 CLI モデル候補取得を確認する。"""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "model-catalog.py"
SPEC = importlib.util.spec_from_file_location("model_catalog", SCRIPT)
catalog = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(catalog)


class ModelCatalogTest(unittest.TestCase):
    def test_json_models_take_priority_over_bat(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config_dir = root / "_config"
            config_dir.mkdir()
            (config_dir / "AiDiy_code_codex_cli.json").write_text(
                json.dumps({"models": {"auto": "自動", "gpt-6-sol": "GPT 6 Sol"}}),
                encoding="utf-8",
            )
            models = catalog._cli_models(root, "codex-cli")

        self.assertEqual(
            [{"label": "自動", "id": "auto"}, {"label": "GPT 6 Sol", "id": "gpt-6-sol"}],
            models,
        )

    def test_auto_only_json_falls_back_to_bat(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config_dir = root / "_config"
            config_dir.mkdir()
            (config_dir / "AiDiy_code_grok_cli.json").write_text(
                json.dumps({"models": {"auto": "自動"}}), encoding="utf-8"
            )
            bat_dir = root / "scripts" / "cli_bat"
            bat_dir.mkdir(parents=True)
            (bat_dir / "_grok_cli.bat").write_text(
                'if "%MODEL_NUMBER%"=="1" set "MODEL=grok-4.7"\n', encoding="utf-8"
            )
            models = catalog._cli_models(root, "grok-cli")

        self.assertEqual(
            [{"label": "auto", "id": "auto"}, {"label": "grok-4.7", "id": "grok-4.7"}],
            models,
        )


if __name__ == "__main__":
    unittest.main()
