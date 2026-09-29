"""Hermes と Codex CLI が同じ OAuth ストアを使うことを確認する。"""

import base64
from contextlib import contextmanager
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import command_hermes.cli_main  # noqa: F401  # Hermes の module alias を初期化
from hermes_cli import auth
from hermes_cli import auth_commands
from agent.credential_pool import load_pool


def _token(account: str, expires_at: int = 4102444800) -> str:
    payload = {
        "exp": expires_at,
        "https://api.openai.com/auth": {"chatgpt_account_id": account},
    }
    encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    return f"header.{encoded}.signature"


class SharedCodexAuthTest(unittest.TestCase):
    @contextmanager
    def _stores(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.dict(os.environ, {
                "CODEX_HOME": str(root / "codex"),
                "HERMES_HOME": str(root / "hermes"),
            }):
                yield root

    def test_existing_codex_login_is_visible_without_hermes_copy(self):
        with self._stores() as root:
            path = root / "codex" / "auth.json"
            path.parent.mkdir()
            path.write_text(json.dumps({
                "auth_mode": "chatgpt", "OPENAI_API_KEY": None,
                "tokens": {"access_token": _token("account-a"), "refresh_token": "refresh-a", "account_id": "account-a"},
                "last_refresh": "2026-01-01T00:00:00Z",
            }), encoding="utf-8")

            self.assertTrue(auth.get_codex_auth_status()["logged_in"])
            self.assertEqual(_token("account-a"), auth.resolve_codex_runtime_credentials()["api_key"])
            self.assertEqual(1, len(load_pool("openai-codex").entries()))
            self.assertFalse((root / "hermes" / "auth.json").exists())

    def test_hermes_login_and_refresh_update_codex_store(self):
        with self._stores() as root:
            path = root / "codex" / "auth.json"
            auth._save_codex_tokens({
                "access_token": _token("account-a"), "refresh_token": "refresh-a",
                "id_token": _token("account-a"),
            })
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["codex_extra"] = "preserve"
            path.write_text(json.dumps(payload), encoding="utf-8")

            with patch.object(auth, "refresh_codex_oauth_pure", return_value={
                "access_token": _token("account-a", 4102444801),
                "refresh_token": "refresh-b",
                "last_refresh": "2026-01-02T00:00:00Z",
            }):
                creds = auth.resolve_codex_runtime_credentials(force_refresh=True)

            stored = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(creds["api_key"], stored["tokens"]["access_token"])
            self.assertEqual("refresh-b", stored["tokens"]["refresh_token"])
            self.assertEqual("account-a", stored["tokens"]["account_id"])
            self.assertEqual("preserve", stored["codex_extra"])
            self.assertFalse((root / "hermes" / "auth.json").exists())

    def test_legacy_hermes_tokens_move_to_codex_store(self):
        with self._stores() as root:
            hermes_path = root / "hermes" / "auth.json"
            hermes_path.parent.mkdir()
            hermes_path.write_text(json.dumps({
                "version": 1,
                "providers": {"openai-codex": {"tokens": {
                    "access_token": _token("account-a"), "refresh_token": "refresh-a",
                }}},
                "credential_pool": {"openai-codex": [{"access_token": _token("account-a"), "refresh_token": "refresh-a"}]},
            }), encoding="utf-8")

            self.assertEqual(_token("account-a"), auth.resolve_codex_runtime_credentials()["api_key"])
            self.assertTrue((root / "codex" / "auth.json").exists())
            migrated = json.loads(hermes_path.read_text(encoding="utf-8"))
            self.assertNotIn("openai-codex", migrated["providers"])
            self.assertNotIn("openai-codex", migrated["credential_pool"])

    def test_logout_clears_shared_tokens(self):
        with self._stores() as root:
            auth._save_codex_tokens({
                "access_token": _token("account-a"), "refresh_token": "refresh-a",
            })
            self.assertTrue(auth._clear_codex_cli_tokens())
            stored = json.loads((root / "codex" / "auth.json").read_text(encoding="utf-8"))
            self.assertNotIn("tokens", stored)
            self.assertFalse(auth.get_codex_auth_status()["logged_in"])

    def test_auth_add_reuses_existing_codex_login(self):
        with self._stores() as root:
            auth._save_codex_tokens({
                "access_token": _token("account-a"), "refresh_token": "refresh-a",
            })
            with (
                patch.object(auth, "_codex_device_code_login") as login,
                patch.object(auth, "mark_provider_active_if_unset"),
                redirect_stdout(io.StringIO()) as output,
            ):
                auth_commands.auth_add_command(type("Args", (), {
                    "provider": "openai-codex", "auth_type": "oauth",
                })())
            login.assert_not_called()
            self.assertIn("existing shared Codex CLI OAuth login", output.getvalue())
            self.assertFalse((root / "hermes" / "auth.json").exists())

    def test_pool_refresh_uses_shared_store(self):
        with self._stores() as root:
            auth._save_codex_tokens({
                "access_token": _token("account-a"), "refresh_token": "refresh-a",
            })
            pool = load_pool("openai-codex")
            with patch.object(auth, "refresh_codex_oauth_pure", return_value={
                "access_token": _token("account-a", 4102444802),
                "refresh_token": "refresh-c",
                "last_refresh": "2026-01-03T00:00:00Z",
            }):
                refreshed = pool._refresh_entry(pool.entries()[0], force=True)

            self.assertIsNotNone(refreshed)
            stored = json.loads((root / "codex" / "auth.json").read_text(encoding="utf-8"))
            self.assertEqual("refresh-c", stored["tokens"]["refresh_token"])
            self.assertFalse((root / "hermes" / "auth.json").exists())


if __name__ == "__main__":
    unittest.main()
