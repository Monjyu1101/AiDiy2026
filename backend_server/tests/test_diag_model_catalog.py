"""診断の合成ファイルがAPI候補・セッション初期値へ反映されることを確認する。"""
import json
import ast
import asyncio
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from conf.conf_model import conf_models


class DiagModelCatalogTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.output = root / "_AIDIY" / "aidiy_diag"
        self.output.mkdir(parents=True)
        config = root / "_config"
        config.mkdir()
        patcher = patch.object(conf_models, "_config_dir_path", return_value=str(config))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.models = conf_models()

    def write(self, group, value):
        (self.output / f"{group}_models_info.json").write_text(json.dumps(value), encoding="utf-8")

    def test_catalogs_refresh_without_restarting_and_preserve_order(self):
        self.write("chat", {"freeai_chat": {"models": {"gemini-new": "new"}}})
        self.write("live", {"freeai_live": {"models": {"gemini-live-new": "new"}}, "gemini_live": {"models": {}}})
        self.write("code", {"claude_cli": {"models": {"haiku": "claude-haiku-5-5"}}, "copilot_cli": {"models": {"claude-haiku-5.5": "haiku"}}})
        self.assertEqual(self.models.get_chat_models(), {"freeai_chat": {"gemini-new": "new"}})
        self.assertEqual(list(self.models.get_live_models()), ["freeai_live", "gemini_live"])
        self.assertEqual(list(self.models.get_code_models()), ["claude_cli", "copilot_cli"])
        self.assertEqual(list(self.models.get_code_models()["claude_cli"]), ["auto", "same", "haiku"])
        self.assertNotIn("claude_ollama", self.models.get_code_models())
        self.assertEqual(self.models.get_live_voices(), {})
        self.write("code", {"codex_cli": {"models": {"gpt-new": "new"}}})
        self.assertEqual(list(self.models.get_code_models()), ["codex_cli"])

    def test_config_chat_precedes_local_in_api_catalog_and_initial_selection(self):
        self.write("chat", {
            "freeai_chat": {"models": {"configured": "仮設定（未検証） - configured"}},
            "local_chat": {"models": {"local-first": "first", "local-second": "second"}},
        })
        catalog = self.models.get_chat_models()
        # APIはこのdictをそのまま返し、画面のObject.keysもこの順序で選択肢を作る。
        self.assertEqual(list(catalog), ["freeai_chat", "local_chat"])
        self.assertEqual(list(catalog["local_chat"]), ["local-first", "local-second"])
        settings = self.models.normalize_initial_settings({"CHAT_AI_NAME": "removed"})
        self.assertEqual(settings["CHAT_AI_NAME"], "freeai_chat")
        self.assertEqual(settings["CHAT_FREEAI_MODEL"], "configured")
        self.assertEqual(self.models.normalize_initial_settings({"CHAT_AI_NAME": "local_chat"})["CHAT_AI_NAME"], "local_chat")

    def test_provider_ids_and_display_labels_are_used_without_rebuilding(self):
        # 選別・統合はdiagの責務。PythonではCLI用ID、バージョン表示、UTF-8を保持する。
        code = {
            "claude_sdk": {"haiku": "2026/10/07 - claude-haiku-5-5"},
            "claude_cli": {"haiku": "2026/10/07 - claude-haiku-5-5"},
            "copilot_cli": {"claude-haiku-5.5": "2026/10/07 - claude-haiku-5.5", "gpt-6.1-sol": "Sol"},
            "codex_cli": {"gpt-6.1-sol": "Sol"},
            "grok_cli": {"grok-4.7": "Grok"},
            "aidiy_hermes": {"claude_cli/same": "Claude", "copilot_cli/same": "Copilot", "codex_cli/same": "Codex", "openai_oauth/gpt-6.1-sol": "OAuth"},
            "opencode_cli": {"ollama/日本語モデル:cloud": "日本語モデル"},
            "antigravity_cli": {"gemini-new": "Gemini"},
        }
        self.write("code", {key: {"models": value} for key, value in code.items()})
        actual = self.models.get_code_models()
        self.assertEqual(list(actual), list(code))
        for provider, models in code.items():
            self.assertEqual({key: label for key, label in actual[provider].items() if key not in ("auto", "same")}, models)
        self.write("chat", {"openai_chat": {"models": {"api-only": "API"}}, "openai_oauth": {"models": {"oauth-only": "OAuth"}}})
        self.assertEqual(self.models.get_chat_models(), {"openai_chat": {"api-only": "API"}, "openai_oauth": {"oauth-only": "OAuth"}})

    def test_initial_values_use_candidates_without_modifying_input_or_controls(self):
        self.write("live", {"freeai_live": {"models": {"new-live": "new", "kept-live": "kept"}}})
        self.write("code", {"claude_cli": {"models": {"haiku": "Haiku"}}, "aidiy_hermes": {"models": {"claude_cli/same": "same"}}})
        settings = {"LIVE_AI_NAME": "removed", "LIVE_FREEAI_MODEL": "removed", "CODE_AI1_NAME": "removed", "CODE_AI1_MODEL": "removed", "CODE_AI2_NAME": "aidiy_hermes", "CODE_AI2_MODEL": "same", "CODE_CLAUDE_CLI_MODEL": "auto"}
        actual = self.models.normalize_initial_settings(settings)
        self.assertEqual(actual["LIVE_AI_NAME"], "freeai_live")
        self.assertEqual(actual["LIVE_FREEAI_MODEL"], "new-live")
        self.assertEqual(actual["CODE_AI1_NAME"], "claude_cli")
        self.assertEqual(actual["CODE_AI1_MODEL"], "haiku")
        self.assertEqual(actual["CODE_AI2_MODEL"], "same")
        self.assertEqual(actual["CODE_CLAUDE_CLI_MODEL"], "auto")
        self.assertEqual(settings["LIVE_AI_NAME"], "removed")
        self.assertEqual(self.models.normalize_initial_settings({"LIVE_AI_NAME": "freeai_live", "LIVE_FREEAI_MODEL": "kept-live"})["LIVE_FREEAI_MODEL"], "kept-live")

    def test_missing_invalid_and_empty_files(self):
        self.assertEqual(self.models.get_live_models(), {})
        self.write("live", {"bad": {"models": []}})
        self.assertEqual(self.models.get_live_models(), {})
        self.write("live", {})
        self.assertEqual(self.models.get_live_models(), {})

    def test_decisions_catalog_refreshes_without_synthetic_defaults_or_setting_changes(self):
        settings = {"DECISION_AI_NAME": "auto", "DECISION_AI_MODEL": "custom"}
        self.assertEqual(self.models.get_decisions_models(), {})
        self.write("decisions", {"freeai_chat": {"models": {"gemini-test": "取得済み"}}, "openai_oauth": {"models": {"gpt-test": "OAuth"}}})
        self.assertEqual(self.models.get_decisions_models(), {"freeai_chat": {"gemini-test": "取得済み"}, "openai_oauth": {"gpt-test": "OAuth"}})
        self.assertEqual(self.models.normalize_initial_settings(settings), settings)
        for value in ({}, {"bad": {"models": []}}, {"bad": {"models": {"model": False}}}):
            self.write("decisions", value)
            self.assertEqual(self.models.get_decisions_models(), {})
            self.assertEqual(self.models.normalize_initial_settings(settings), settings)

    def test_loading_never_creates_or_updates_model_configs_and_never_fetches(self):
        config = Path(self.temp.name) / "_config"
        old = config / "AiDiy_code_codex_cli.json"
        old.write_text('{"models":{"old":"kept"}}', encoding="utf-8")
        before = {file.name: file.read_bytes() for file in config.iterdir()}
        with patch("urllib.request.urlopen", side_effect=AssertionError("network")), patch("subprocess.run", side_effect=AssertionError("CLI")):
            models = conf_models()
            models.fetch_all_models()
            self.assertEqual(models.get_code_models(), {})
        self.assertEqual(before, {file.name: file.read_bytes() for file in config.iterdir()})

    def test_voice_catalog_refreshes_and_ignores_old_configs(self):
        old = Path(self.temp.name) / "_config" / "AiDiy_live_gemini.json"
        old.write_text('{"voices":{"old":"Old"}}', encoding="utf-8")
        file = self.output / "live_voices_info.json"
        self.assertEqual(self.models.get_live_voices(), {})
        file.write_text(json.dumps({"freeai_live": {"voices": {"Zephyr": "声1", "Kore": "声2"}}}), encoding="utf-8")
        self.assertEqual(self.models.get_live_voices(), {"freeai_live": {"Zephyr": "声1", "Kore": "声2"}})
        file.write_text('{}', encoding="utf-8")
        self.assertEqual(self.models.get_live_voices(), {})
        file.write_text('{"freeai_live":{"voices":[]}}', encoding="utf-8")
        self.assertEqual(self.models.get_live_voices(), {})

    def test_api_and_session_initial_values_share_the_same_catalog(self):
        self.write("chat", {"openai_chat": {"models": {"gpt-code": "code"}}, "openai_oauth": {"models": {"gpt-code-900k": "context"}}})
        self.write("live", {"freeai_live": {"models": {"new-live": "Live"}}})
        self.write("code", {"copilot_cli": {"models": {"claude-haiku-5.5": "Haiku"}}})
        root = Path(__file__).resolve().parents[1]
        scope = {"Optional": __import__('typing').Optional, "モデル設定正規化": lambda settings: dict(settings)}
        for file, function in [(root / "AIコア/AIセッション管理.py", "初期モデル設定生成"), (root / "core_router/AIコア.py", "モデル情報取得")]:
            tree = ast.parse(file.read_text(encoding="utf-8"))
            node = next(node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function)
            node.decorator_list = []
            scope.update({"Request": object, "モデル情報取得リクエスト": object})
            exec(compile(ast.Module(body=[node], type_ignores=[]), str(file), "exec"), scope)
        config = SimpleNamespace(models=self.models, json={"CHAT_AI_NAME": "openai_oauth", "CHAT_OPENAI_MODEL": "gpt-code-900k", "LIVE_FREEAI_MODEL": "removed", "CODE_AI1_NAME": "copilot_cli", "CODE_AI1_MODEL": "removed"})
        scope.update({"取得_コードベース選択肢": lambda config: {}, "_backend_local稼働中": lambda config: True})
        response = asyncio.run(scope["モデル情報取得"](SimpleNamespace(app=SimpleNamespace(conf=config)), SimpleNamespace(セッションID="")))
        self.assertEqual(response["status"], "OK")
        self.assertEqual(response["data"]["available_models"]["code_models"]["copilot_cli"]["claude-haiku-5.5"], "Haiku")
        settings = response["data"]["モデル設定"]
        self.assertEqual(settings["CHAT_OPENAI_MODEL"], "gpt-code-900k")
        self.assertEqual(settings["LIVE_FREEAI_MODEL"], "new-live")
        self.assertEqual(settings["CODE_AI1_MODEL"], "claude-haiku-5.5")
        self.assertEqual(config.json["LIVE_FREEAI_MODEL"], "removed")


if __name__ == "__main__":
    unittest.main()
