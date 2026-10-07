import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from conf.conf_model import conf_models


class OpenAIModelOptionsTest(unittest.TestCase):
    def make_models(self, api_models):
        models = object.__new__(conf_models)
        models.google_models = {}
        models.openrt_models = {}
        models.openai_models = api_models
        models.ollama_models = {}
        models.CHAT_LOCAL_MODELS = {}
        return models

    def test_api_list_is_shared_without_fetching_oauth_models(self):
        oauth_module = types.ModuleType("AIコア.AIチャット_openai")
        oauth_module.get_openai_oauth_models = lambda: self.fail("OAuth への取得は不要")
        models = self.make_models({"gpt-6.1-sol": {"作成日": "2026/09/01"}})

        with patch.dict(sys.modules, {"AIコア.AIチャット_openai": oauth_module}):
            chat_models = models.get_chat_models()

        self.assertEqual(chat_models["openai_chat"], chat_models["openai_oauth"])
        self.assertEqual(chat_models["openai_chat"], {"gpt-6.1-sol": "2026/09/01 - gpt-6.1-sol"})

    def test_oauth_list_is_shared_when_api_list_is_empty(self):
        oauth_module = types.ModuleType("AIコア.AIチャット_openai")
        oauth_module.get_openai_oauth_models = lambda: {"gpt-6-astra": "yyyy/mm/dd - gpt-6-astra"}
        models = self.make_models({})

        with patch.dict(sys.modules, {"AIコア.AIチャット_openai": oauth_module}):
            chat_models = models.get_chat_models()

        self.assertEqual(chat_models["openai_chat"], chat_models["openai_oauth"])
        self.assertEqual(chat_models["openai_chat"], {"gpt-6-astra": "yyyy/mm/dd - gpt-6-astra"})

    def test_api_and_openrouter_catalogs_exclude_retired_sol_variants(self):
        models = self.make_models({
            model: {"作成日": "2026/09/01"}
            for model in ("gpt-6-sol", "gpt-6-sol-pro", "gpt-6.1-sol")
        })
        models.openrt_models = {
            "openai/gpt-6-sol": {},
            "openai/gpt-6.1-sol": {},
        }

        chat_models = models.get_chat_models()

        self.assertEqual(list(chat_models["openai_chat"]), ["gpt-6.1-sol"])
        self.assertEqual(list(chat_models["openrt_chat"]), ["openai/gpt-6.1-sol"])

    def test_oauth_catalog_excludes_retired_sol_from_cache(self):
        oauth_module = types.ModuleType("AIコア.AIチャット_openai")
        oauth_module.get_openai_oauth_models = lambda: {
            "gpt-6-sol-900k": "旧モデル",
            "gpt-6.1-sol": "新モデル",
        }

        with patch.dict(sys.modules, {"AIコア.AIチャット_openai": oauth_module}):
            chat_models = self.make_models({}).get_chat_models()

        self.assertEqual(chat_models["openai_oauth"], {"gpt-6.1-sol": "新モデル"})

    def test_retired_only_oauth_catalog_uses_current_fallback(self):
        oauth_module = types.ModuleType("AIコア.AIチャット_openai")
        oauth_module.get_openai_oauth_models = lambda: {"gpt-6-sol": "旧モデル"}

        with patch.dict(sys.modules, {"AIコア.AIチャット_openai": oauth_module}):
            chat_models = self.make_models({}).get_chat_models()

        self.assertIn("gpt-6.1-sol", chat_models["openai_oauth"])
        self.assertNotIn("gpt-6-sol", chat_models["openai_oauth"])

    def test_fallback_uses_current_sol_when_discovery_fails(self):
        oauth_module = types.ModuleType("AIコア.AIチャット_openai")
        def fail_discovery():
            raise RuntimeError("offline")
        oauth_module.get_openai_oauth_models = fail_discovery
        models = self.make_models({})

        with patch.dict(sys.modules, {"AIコア.AIチャット_openai": oauth_module}):
            chat_models = models.get_chat_models()

        self.assertEqual(list(chat_models["openai_chat"]), ["gpt-6-astra", "gpt-6.1-sol", "gpt-5.6-terra", "gpt-6-luna"])
        self.assertEqual(chat_models["openai_chat"], chat_models["openai_oauth"])


if __name__ == "__main__":
    unittest.main()
