import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools_proc.code_agents import CodeAgents


class CodeAgentsAutoModelTests(unittest.TestCase):
    def test_cli_auto_reaches_code_ai_without_config_override(self):
        service = CodeAgents()
        for provider in ("codex_cli", "claude_cli", "copilot_cli", "grok_cli", "aidiy_hermes"):
            with self.subTest(provider=provider), patch.object(service, "_load_key_json", return_value={f"CODE_{provider.upper()}_MODEL": "explicit-config-model"}):
                self.assertEqual(service._resolve_ai_params(provider, "auto"), (provider, "auto"))
                self.assertEqual(service._resolve_ai_params(provider, "same"), (provider, "same"))
                self.assertEqual(service._resolve_ai_params(provider, "explicit"), (provider, "explicit"))

    def test_sdk_default_and_auto_provider_are_preserved(self):
        service = CodeAgents()
        service.version_info = {"codex_cli": {"ok": True}}
        with patch.object(service, "_load_key_json", return_value={"CODE_CLAUDE_SDK_MODEL": "sonnet"}):
            self.assertEqual(service._resolve_ai_params("claude_sdk", "auto"), ("claude_sdk", "sonnet"))
            self.assertEqual(service._resolve_ai_params("auto", "auto"), ("codex_cli", "auto"))
