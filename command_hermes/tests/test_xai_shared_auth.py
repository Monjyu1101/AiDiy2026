"""Grok Build and Hermes use one xAI OAuth token store."""

import base64
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import command_hermes.hermes_main  # Install the AiDiy layout shim.
import core

sys.modules["agent"] = core

from hermes_cli import auth
from agent.credential_pool import load_pool


def _token(exp: int = 2_000_000_000) -> str:
    payload = base64.urlsafe_b64encode(
        json.dumps({"exp": exp, "sub": "test-user", "principal_type": "User"}).encode()
    ).decode().rstrip("=")
    return f"header.{payload}.signature"


class XaiSharedAuthTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = patch.dict(os.environ, {
            "GROK_HOME": str(self.root / "grok"),
            "HERMES_HOME": str(self.root / "hermes"),
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        self.global_store = patch.object(auth, "_global_auth_file_path", return_value=None)
        self.global_store.start()
        self.addCleanup(self.global_store.stop)

    def test_existing_grok_login_is_visible_without_hermes_copy(self):
        path = auth._grok_cli_auth_path()
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({
            auth._grok_auth_entry_key(): {
                "key": _token(), "refresh_token": "refresh-one",
                "auth_mode": "oidc", "oidc_issuer": auth.XAI_OAUTH_ISSUER,
                "oidc_client_id": auth.XAI_OAUTH_CLIENT_ID,
            },
        }), encoding="utf-8")

        creds = auth.resolve_xai_oauth_runtime_credentials(refresh_if_expiring=False)
        self.assertEqual(_token(), creds["api_key"])
        self.assertEqual("grok-cli-auth-store", creds["source"])
        self.assertEqual("grok-shared", load_pool("xai-oauth").entries()[0].id)
        self.assertFalse(auth._auth_file_path().exists())

    def test_hermes_login_writes_grok_schema_and_preserves_other_account(self):
        path = auth._grok_cli_auth_path()
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({"other-issuer::client": {"key": "other"}}), encoding="utf-8")

        auth._save_xai_oauth_tokens(
            {"access_token": _token(), "refresh_token": "refresh-two"},
            set_active=False,
        )
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual({"key": "other"}, payload["other-issuer::client"])
        entry = payload[auth._grok_auth_entry_key()]
        self.assertEqual(_token(), entry["key"])
        self.assertEqual("refresh-two", entry["refresh_token"])
        self.assertEqual("oidc", entry["auth_mode"])
        self.assertTrue(entry["expires_at"])
        self.assertFalse(auth._auth_file_path().exists())

    def test_legacy_hermes_login_migrates_once(self):
        path = auth._auth_file_path()
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({
            "version": 1,
            "providers": {"xai-oauth": {"tokens": {
                "access_token": _token(), "refresh_token": "old-refresh",
            }}},
            "credential_pool": {"xai-oauth": [
                {"id": "old-oauth", "auth_type": "oauth", "access_token": _token(),
                 "refresh_token": "old-refresh"},
                {"id": "api-key", "auth_type": "api_key", "access_token": "api-key-value"},
            ]},
        }), encoding="utf-8")

        state = auth._read_xai_oauth_tokens()
        self.assertEqual("old-refresh", state["tokens"]["refresh_token"])
        migrated = json.loads(path.read_text(encoding="utf-8"))
        self.assertNotIn("xai-oauth", migrated["providers"])
        self.assertEqual(["api-key"], [e["id"] for e in migrated["credential_pool"]["xai-oauth"]])
        self.assertEqual(
            {"grok-shared", "api-key"},
            {entry.id for entry in load_pool("xai-oauth").entries()},
        )
        self.assertTrue(auth._load_grok_cli_auth()[auth._grok_auth_entry_key()]["key"])


if __name__ == "__main__":
    unittest.main()
