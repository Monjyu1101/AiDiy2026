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
        models = self.make_models({"gpt-6-sol": {"作成日": "2026/09/01"}})

        with patch.dict(sys.modules, {"AIコア.AIチャット_openai": oauth_module}):
            chat_models = models.get_chat_models()

        self.assertEqual(chat_models["openai_chat"], chat_models["openai_oauth"])
        self.assertEqual(chat_models["openai_chat"], {"gpt-6-sol": "2026/09/01 - gpt-6-sol"})

    def test_oauth_list_is_shared_when_api_list_is_empty(self):
        oauth_module = types.ModuleType("AIコア.AIチャット_openai")
        oauth_module.get_openai_oauth_models = lambda: {"gpt-6-astra": "yyyy/mm/dd - gpt-6-astra"}
        models = self.make_models({})

        with patch.dict(sys.modules, {"AIコア.AIチャット_openai": oauth_module}):
            chat_models = models.get_chat_models()

        self.assertEqual(chat_models["openai_chat"], chat_models["openai_oauth"])
        self.assertEqual(chat_models["openai_chat"], {"gpt-6-astra": "yyyy/mm/dd - gpt-6-astra"})


if __name__ == "__main__":
    unittest.main()
