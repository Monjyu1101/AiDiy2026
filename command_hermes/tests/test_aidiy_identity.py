# -*- coding: utf-8 -*-
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1". See LICENSE for full terms.

from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock, patch

import command_hermes.cli_main  # AiDiy の layout shim を適用する。
from agent import prompt_builder, system_prompt
from hermes_cli import config, default_soul
from tools.skill_linter import _check_metadata_block


class AiDiyIdentityTest(unittest.TestCase):
    def test_default_identity_and_distributed_soul_agree(self):
        soul = Path(__file__).resolve().parents[1] / "SOUL.md"
        self.assertEqual(soul.read_text(encoding="utf-8").strip(), default_soul.DEFAULT_SOUL_MD)
        self.assertEqual(default_soul.DEFAULT_SOUL_MD, prompt_builder.DEFAULT_AGENT_IDENTITY)
        self.assertTrue(default_soul.DEFAULT_SOUL_MD.startswith(
            "You are AiDiy Hermes, built by Nous Research and enhanced by the AiDiy development team."
        ))
        self.assertIn("aidiy_hermes", default_soul.DEFAULT_SOUL_MD)

    def test_existing_unmodified_soul_is_upgraded_but_custom_persona_is_kept(self):
        upstream = default_soul._UPSTREAM_DEFAULT_SOUL_MD
        custom = upstream + "\n必ず日本語で答えてください。"
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            soul = home / "SOUL.md"
            previous = default_soul._PREVIOUS_AIDIY_SOUL_MD
            for original in (upstream, upstream.replace("—", "--"), "\ufeff" + upstream + "\r\n",
                             previous, previous.replace("—", "--")):
                soul.write_text(original, encoding="utf-8")
                config._ensure_default_soul_md(home)
                self.assertEqual(soul.read_text(encoding="utf-8"), default_soul.DEFAULT_SOUL_MD)
            soul.write_text(custom, encoding="utf-8")
            config._ensure_default_soul_md(home)
            self.assertEqual(soul.read_text(encoding="utf-8"), custom)

    def test_runtime_product_identity_is_present_with_or_without_custom_soul(self):
        for soul in (None, "私は案内役です。短く日本語で話します。"):
            with self.subTest(soul=soul), tempfile.TemporaryDirectory() as folder:
                agent = SimpleNamespace(
                    load_soul_identity=bool(soul), skip_context_files=True,
                    valid_tool_names=set(), model="test", provider="test", platform="",
                    _memory_store=None, _memory_manager=None, pass_session_id=False,
                    session_id=None, _environment_probe=False,
                    _plugin_system_prompt_sections_snapshot=(),
                )
                helpers = Mock()
                helpers.load_soul_md.return_value = soul
                helpers.build_environment_hints.return_value = ""
                with patch.object(system_prompt, "_ra", return_value=helpers), patch.object(
                    system_prompt, "_agent_home", return_value=Path(folder)
                ):
                    parts = system_prompt.build_system_prompt_parts(agent)
                self.assertIn(prompt_builder.AIDIY_RUNTIME_IDENTITY, parts["stable"])
                self.assertIn(soul or prompt_builder.DEFAULT_AGENT_IDENTITY, parts["stable"])
                self.assertIn("command_hermes/AGENTS.md", parts["stable"])
                self.assertNotIn("You run on Hermes Agent", parts["stable"])

    def test_help_uses_aidiy_docs_and_preserves_compatible_skill_id(self):
        guidance = prompt_builder.HERMES_AGENT_HELP_GUIDANCE
        self.assertIn("AiDiy_hermes", guidance)
        self.assertIn("skill_view(name='hermes-agent')", guidance)
        self.assertIn("_AIDIY/knowledge", guidance)
        self.assertNotIn("skill_view", prompt_builder.HERMES_AGENT_HELP_GUIDANCE_NO_SKILLS)

    def test_author_lint_accepts_aidiy_names_and_upstream_attribution(self):
        for author in ("Hermes Agent", "AiDiy Hermes", "AiDiy_hermes"):
            findings = _check_metadata_block({"author": author, "metadata": {"hermes": {"tags": []}}})
            self.assertFalse(any(item.rule == "author-caps" for item in findings))


if __name__ == "__main__":
    unittest.main()
