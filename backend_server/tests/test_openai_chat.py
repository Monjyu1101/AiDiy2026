import asyncio
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


class OpenAIChatTest(unittest.TestCase):
    def test_legacy_openai_oauth_chat_name_is_migrated(self):
        from conf.conf_json import conf_json

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "AiDiy_key.json"
            config_path.write_text(
                json.dumps({"CHAT_AI_NAME": "openai_oauth_chat"}),
                encoding="utf-8",
            )

            config = conf_json(str(config_path))

            self.assertEqual(config.CHAT_AI_NAME, "openai_oauth")
            saved = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["CHAT_AI_NAME"], "openai_oauth")

    def test_chat_manager_selects_shared_openai_module(self):
        from AIコア.AIチャット import Chat

        for ai_name in ("openai_chat", "openai_oauth"):
            with self.subTest(ai_name=ai_name):
                chat = Chat(AI_NAME=ai_name, AI_MODEL="gpt-5.6-sol")
                self.assertEqual(
                    chat.AIモジュール.__name__,
                    "AIコア.AIチャット_openai",
                )

    def test_openai_api_chat_uses_configured_api_key(self):
        from AIコア import AIチャット_openai as openai_module

        message = types.SimpleNamespace(content="API response", tool_calls=None)
        response = types.SimpleNamespace(
            choices=[types.SimpleNamespace(message=message)],
        )
        requests = []

        def create_completion(**kwargs):
            requests.append(kwargs)
            return response

        fake_client = types.SimpleNamespace(
            chat=types.SimpleNamespace(
                completions=types.SimpleNamespace(create=create_completion),
            ),
            close=lambda: None,
        )
        with patch.object(openai_module.openai, "OpenAI", return_value=fake_client) as factory:
            chat = openai_module.ChatAI(
                AI_NAME="openai_chat",
                AI_MODEL="gpt-5.6-sol",
                api_key="openai-api-key",
            )
            self.assertTrue(asyncio.run(chat.開始()))
            self.assertFalse(chat.oauth_mode)
            self.assertIs(chat.client._client, fake_client)
            self.assertEqual(asyncio.run(chat.実行("こんにちは")), "API response")
            self.assertNotIn("temperature", requests[0])
            factory.assert_called_once_with(
                api_key="openai-api-key",
                organization=None,
            )

    def test_openai_oauth_uses_hermes_codex_transport(self):
        from AIコア import AIチャット_openai as openai_module

        class FakeClient:
            def __init__(self):
                self.closed = False
                message = types.SimpleNamespace(content="OAuth response", tool_calls=None)
                response = types.SimpleNamespace(
                    choices=[types.SimpleNamespace(message=message)],
                )
                self.chat = types.SimpleNamespace(
                    completions=types.SimpleNamespace(create=lambda **kwargs: response),
                )

            def close(self):
                self.closed = True

        fake_client = FakeClient()
        calls = []
        auxiliary_module = types.ModuleType("agent.auxiliary_client")

        def fake_resolve_provider_client(**kwargs):
            calls.append(kwargs)
            return fake_client, kwargs["model"]

        auxiliary_module.resolve_provider_client = fake_resolve_provider_client

        with (
            patch.dict(sys.modules, {"agent.auxiliary_client": auxiliary_module}),
            patch.object(openai_module, "_prepare_hermes_imports"),
            patch.object(
                openai_module,
                "_oauth_access_token",
                return_value="oauth-token",
            ),
        ):
            chat = openai_module.ChatAI(
                AI_NAME="openai_oauth",
                AI_MODEL="gpt-5.6-sol",
            )
            self.assertTrue(asyncio.run(chat.開始()))
            self.assertTrue(chat.oauth_mode)
            self.assertEqual(
                calls,
                [
                    {
                        "provider": "openai-codex",
                        "model": "gpt-5.6-sol",
                        "api_mode": "codex_responses",
                    }
                ],
            )
            self.assertEqual(asyncio.run(chat.実行("こんにちは")), "OAuth response")
            self.assertIsInstance(chat._メッセージ履歴構築()[0]["content"], str)

            self.assertTrue(asyncio.run(chat.終了()))
            self.assertTrue(fake_client.closed)

    def test_openai_oauth_reports_aidiy_hermes_login(self):
        from AIコア import AIチャット_openai as openai_module

        with patch.object(
            openai_module,
            "_oauth_access_token",
            side_effect=RuntimeError("No Codex credentials stored"),
        ):
            chat = openai_module.ChatAI(
                AI_NAME="openai_oauth",
                AI_MODEL="gpt-5.6-sol",
            )
            self.assertFalse(asyncio.run(chat.開始()))
            self.assertIn("aidiy_hermes", chat.last_error)
            self.assertIn("openai_oauth", chat.last_error)


if __name__ == "__main__":
    unittest.main()
