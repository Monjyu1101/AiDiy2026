"""OAuth の接続用情報と、製品名・著作者の本文を分けて保持する。"""

import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

# CLI を起動せず、AiDiy の upstream レイアウト読み替えだけを適用する。
_HERMES_ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(_HERMES_ROOT), str(_HERMES_ROOT / "base")]
import core

sys.modules.setdefault("agent", core)
from agent import anthropic_adapter, prompt_builder
from hermes_cli import default_soul


class AnthropicIdentityTest(unittest.TestCase):
    def test_fresh_identity_and_soul_templates_have_approved_attribution(self):
        identity = ("AiDiy Hermes, based on Hermes Agent by Nous Research and "
                    "enhanced by the AiDiy development team.")
        self.assertTrue(prompt_builder.DEFAULT_AGENT_IDENTITY.startswith("You are " + identity))
        self.assertEqual(default_soul.DEFAULT_SOUL_MD, prompt_builder.DEFAULT_AGENT_IDENTITY)
        self.assertEqual((_HERMES_ROOT / "SOUL.md").read_text(encoding="utf-8").strip(),
                         default_soul.DEFAULT_SOUL_MD)
        self.assertIn("based on Hermes Agent by Nous Research", prompt_builder.AIDIY_RUNTIME_IDENTITY)
        for relative in ("scripts/install.sh", "scripts/install.ps1", "hermes_cli/doctor.py"):
            with self.subTest(relative=relative):
                self.assertIn("You are " + identity,
                              (_HERMES_ROOT / relative).read_text(encoding="utf-8"))

    def build_payload(self, system, *, is_oauth=True, tools=None, tool_choice=None):
        return anthropic_adapter.build_anthropic_kwargs(
            model="claude-sonnet-4-6",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": "Who are you?"},
            ],
            tools=tools,
            max_tokens=200,
            reasoning_config=None,
            is_oauth=is_oauth,
            tool_choice=tool_choice,
        )

    def test_oauth_preserves_aidiy_identity_and_upstream_authorship(self):
        for identity in (
            prompt_builder.DEFAULT_AGENT_IDENTITY,
            prompt_builder.AIDIY_RUNTIME_IDENTITY,
            prompt_builder.HERMES_AGENT_HELP_GUIDANCE,
        ):
            with self.subTest(identity=identity):
                payload = self.build_payload(identity)
                self.assertEqual(payload["system"][0]["text"],
                                 anthropic_adapter._CLAUDE_CODE_SYSTEM_PREFIX)
                self.assertEqual(payload["system"][1]["text"], identity)
                self.assertNotIn("AiDiy Hermes, built by Anthropic", str(payload["system"]))

    def test_oauth_preserves_persona_memory_and_cached_block_metadata(self):
        persona = "I am a custom guide. Hermes Agent and Hermes agent are names in my notes."
        memory = "Nous Research publishes hermes-agent. Keep skill_view(name='hermes-agent')."
        blocks = [
            {"type": "text", "text": persona, "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": memory},
        ]
        original = copy.deepcopy(blocks)
        payload = self.build_payload(blocks)
        self.assertEqual(payload["system"][1:], original)
        self.assertEqual(blocks, original)
        self.assertEqual(payload["messages"][0]["content"], "Who are you?")

    def test_api_key_requests_keep_identity_without_oauth_prefix(self):
        identity = prompt_builder.DEFAULT_AGENT_IDENTITY
        payload = self.build_payload(identity, is_oauth=False)
        self.assertEqual(payload["system"], identity)

    def test_oauth_tool_names_and_prose_aliases_are_unchanged(self):
        tools = [{
            "type": "function",
            "function": {
                "name": "session_search",
                "description": "Use session_search with tools/session_search_tool.py.",
                "parameters": {"type": "object", "properties": {}},
            },
        }]
        original = copy.deepcopy(tools)
        payload = self.build_payload(
            "Use session_search. Keep tools/session_search_tool.py and hermes-agent.",
            tools=tools,
            tool_choice="session_search",
        )
        self.assertEqual(payload["tools"][0]["name"], "mcp__chat_history_lookup")
        self.assertEqual(payload["tool_choice"],
                         {"type": "tool", "name": "mcp__chat_history_lookup"})
        self.assertEqual(payload["system"][1]["text"],
                         "Use chat_history_lookup. Keep tools/session_search_tool.py and hermes-agent.")
        self.assertEqual(payload["tools"][0]["description"],
                         "Use chat_history_lookup with tools/session_search_tool.py.")
        self.assertEqual(tools, original)

    def test_api_key_client_discards_sdk_ambient_bearer(self):
        sdk = Mock()
        sdk.Anthropic.return_value.api_key = "sk-ant-api03-configured-test"
        sdk.Anthropic.return_value.auth_token = "ambient-claude-test-token"
        with patch.object(anthropic_adapter, "_get_anthropic_sdk", return_value=sdk), \
             patch.object(anthropic_adapter, "normalize_proxy_env_vars"):
            client = anthropic_adapter.build_anthropic_client("sk-ant-api03-configured-test")
        self.assertEqual("sk-ant-api03-configured-test", sdk.Anthropic.call_args.kwargs["api_key"])
        self.assertIsNone(client.auth_token)
        self.assertEqual("sk-ant-api03-configured-test", client.api_key)

    def test_oauth_authentication_metadata_is_unchanged(self):
        sdk = Mock()
        token = "sk-ant-oat-test-placeholder"
        with patch.object(anthropic_adapter, "_get_anthropic_sdk", return_value=sdk), \
             patch.object(anthropic_adapter, "_get_claude_code_version", return_value="2.1.74"), \
             patch.object(anthropic_adapter, "normalize_proxy_env_vars"):
            client = anthropic_adapter.build_anthropic_client(token)
        kwargs = sdk.Anthropic.call_args.kwargs
        self.assertEqual(kwargs["auth_token"], token)
        self.assertNotIn("api_key", kwargs)
        self.assertIsNone(client.api_key)
        self.assertEqual(kwargs["default_headers"]["user-agent"],
                         "claude-code/2.1.74 (external, cli)")
        self.assertEqual(kwargs["default_headers"]["x-app"], "cli")
        betas = kwargs["default_headers"]["anthropic-beta"].split(",")
        for beta in anthropic_adapter._OAUTH_ONLY_BETAS:
            self.assertIn(beta, betas)


if __name__ == "__main__":
    unittest.main()
