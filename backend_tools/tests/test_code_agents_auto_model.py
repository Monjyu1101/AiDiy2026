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

    def test_sdk_default_is_preserved(self):
        service = CodeAgents()
        service.version_info = {"codex_cli": {"ok": True}}
        with patch.object(service, "_load_key_json", return_value={"CODE_CLAUDE_SDK_MODEL": "sonnet"}):
            self.assertEqual(service._resolve_ai_params("claude_sdk", "auto"), ("claude_sdk", "sonnet"))

    def test_auto_and_same_choose_hermes_even_when_codex_is_available(self):
        service = CodeAgents()
        for versions in ({}, {"codex_cli": {"ok": True}}, {"aidiy_hermes": {"ok": False}, "codex_cli": {"ok": True}}):
            service.version_info = versions
            for name, model in (("auto", "auto"), ("auto", "same"), ("same", "same")):
                with self.subTest(versions=versions, name=name, model=model), patch.object(service, "_load_key_json", return_value={"CODE_AI1_NAME": "codex_cli"}):
                    self.assertEqual(service._resolve_ai_params(name, model), ("aidiy_hermes", model))

    def test_startup_checks_hermes_when_not_registered_in_code_panels(self):
        service = CodeAgents()
        with patch.object(service, "_setup_sys_path"), patch.object(service, "_load_key_json", return_value={"CODE_AI1_NAME": "codex_cli"}), patch.object(service, "_probe_ai_version", return_value={"ok": True}) as probe:
            versions = service._check_ai_versions()
        self.assertEqual(set(versions), {"codex_cli", "aidiy_hermes"})
        self.assertEqual({call.args[0] for call in probe.call_args_list}, {"codex_cli", "aidiy_hermes"})


class CodeAgentsUnavailableTests(unittest.IsolatedAsyncioTestCase):
    async def test_auto_and_same_report_unavailable_hermes_without_codex_fallback(self):
        service = CodeAgents()
        service.version_info = {"aidiy_hermes": {"ok": False, "version": "missing"}, "codex_cli": {"ok": True}}
        for name, model in (("auto", "auto"), ("auto", "same"), ("same", "same")):
            with self.subTest(name=name, model=model), patch.object(service, "_setup_sys_path"), patch.object(service, "_load_key_json", return_value={}):
                result = await service.run_async(prompt="質問", ai_name=name, ai_model=model)
            self.assertEqual(result["status"], "NG")
            self.assertEqual(result["ai_name"], "aidiy_hermes")
            self.assertEqual(result["ai_model"], model)
