"""API・保存設定・キャッシュから旧 Sol が再表示されないことを確認する。"""

import time
import unittest
from unittest.mock import patch

import command_hermes.cli_main  # AiDiy の upstream 互換 import を準備する。
from hermes_cli import codex_models, models


class RetiredSolModelsTest(unittest.TestCase):
    def assert_current_sol(self, catalog):
        self.assertIn("gpt-6.1-sol", catalog)
        self.assertFalse(any("gpt-6-sol" in model for model in catalog))

    def test_live_codex_catalog_does_not_restore_retired_sol(self):
        with patch.object(codex_models, "_fetch_models_from_api", return_value=[
            "gpt-6-sol", "gpt-6-sol-900k", "gpt-6.1-sol",
        ]):
            catalog = codex_models.get_codex_model_ids(access_token="test-token")

        self.assert_current_sol(catalog)
        self.assertIn("gpt-6.1-sol-900k", catalog)

    def test_saved_codex_default_and_cache_do_not_restore_retired_sol(self):
        with (
            patch.object(codex_models, "_read_default_model", return_value="gpt-6-sol"),
            patch.object(codex_models, "_read_cache_models", return_value=["gpt-6-sol-pro"]),
        ):
            catalog = codex_models.get_codex_model_ids()

        self.assert_current_sol(catalog)
        self.assertIn("gpt-6-astra", catalog)
        self.assertIn("gpt-6-luna", catalog)

    def test_older_catalog_still_synthesizes_current_sol(self):
        catalog = codex_models._finalize_codex_models(["gpt-5.4"])

        self.assert_current_sol(catalog)

    def test_live_provider_catalog_filters_namespaced_retired_models(self):
        with patch.object(models, "_provider_model_ids", return_value=[
            "openai/gpt-6-sol-pro", "openai.gpt-6-sol", "gpt-6.1-sol",
        ]):
            catalog = models.provider_model_ids("openai")

        self.assert_current_sol(catalog)

    def test_fresh_disk_cache_filters_retired_models_without_refetch(self):
        entry = {
            "fp": "test-fingerprint", "at": time.time(),
            "models": ["gpt-6-sol", "gpt-6.1-sol"],
        }
        with (
            patch.object(models, "_load_provider_models_cache", return_value={"openai": entry}),
            patch.object(models, "_credential_fingerprint", return_value="test-fingerprint"),
            patch.object(models, "provider_model_ids", side_effect=AssertionError("再取得は不要")),
        ):
            catalog = models.cached_provider_model_ids("openai")

        self.assert_current_sol(catalog)


if __name__ == "__main__":
    unittest.main()
