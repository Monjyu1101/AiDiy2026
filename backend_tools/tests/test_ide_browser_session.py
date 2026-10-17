# -*- coding: utf-8 -*-
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
import json
import asyncio
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools_proc.chrome_sessions import ChromeSessionRegistry
from tools_proc.ide_browser_session import IDEBrowserManager, IDEBrowserClient

class IDEBrowserSessionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.registry = ChromeSessionRegistry(sessions_file=self.root / "sessions.json")
        self.manifests = self.root / "_ide_browser_sessions"
        self.manifests.mkdir()

    def register(self, token="12345678-1234-1234-1234-123456789abc"):
        entry = {"name": "aidiy_ide", "port": 30001, "pid": 123, "token": token}
        (self.manifests / "aidiy_ide.json").write_text(json.dumps(entry), encoding="utf-8")

    def test_missing_ide_never_launches_an_unrelated_chrome(self):
        with patch("tools_proc.chrome_sessions.ChromeManager") as chrome:
            with self.assertRaisesRegex(RuntimeError, "Browser"):
                self.registry.get("aidiy_ide")
            self.assertIsNone(self.registry.peek("aidiy_ide"))
            self.assertFalse(self.registry.close("aidiy_ide"))
            chrome.assert_not_called()

    def test_reconnect_and_close_only_owned_browser_panels(self):
        self.register()
        manager, client = self.registry.get("aidiy_ide")
        self.assertIsInstance(manager, IDEBrowserManager)
        self.assertIsInstance(client, IDEBrowserClient)
        self.assertIs(self.registry.peek("aidiy_ide")[1], client)
        with patch.object(manager, "close", return_value=True) as close:
            self.assertTrue(self.registry.close("aidiy_ide"))
            close.assert_called_once()
        self.assertTrue((self.manifests / "aidiy_ide.json").exists())
        self.register("87654321-1234-1234-1234-123456789abc")
        self.assertIsNot(self.registry.get("aidiy_ide")[1], client)

    def test_restart_discovers_manifest_without_persisting_tokens_in_chrome_table(self):
        self.register()
        other = ChromeSessionRegistry(sessions_file=self.root / "sessions.json")
        with patch.object(IDEBrowserManager, "is_running", return_value=True):
            entry = other.list()[0]
        self.assertEqual(entry["session"], "aidiy_ide")
        self.assertEqual(entry["owner"], "aidiy_ide")
        self.assertNotIn("token", entry)
        self.assertFalse((self.root / "sessions.json").exists())

    def test_external_client_prefixes_http_and_does_not_fall_back_to_raw_port(self):
        self.register()
        _, client = self.registry.get("aidiy_ide")
        with patch("tools_proc.chrome_devtools.CDPClient._http_get", return_value=[]) as request:
            client.list_tabs()
            request.assert_called_once_with("/12345678-1234-1234-1234-123456789abc/json", parse_json=True)

    def test_new_tab_uses_ide_only_and_rejects_browser_process_commands(self):
        self.register()
        _, client = self.registry.get("aidiy_ide")
        with patch.object(client, "_http_get", return_value={"id": "page-1"}) as request:
            result = asyncio.run(client.send_command(client.get_browser_ws_url(), "Target.createTarget", {"url": "https://example.com/"}))
            self.assertEqual(result, {"targetId": "page-1"})
            self.assertTrue(request.call_args.args[0].startswith("/json/new?url="))
        with self.assertRaisesRegex(RuntimeError, "公開していません"):
            asyncio.run(client.send_command(client.get_browser_ws_url(), "Browser.close"))

if __name__ == "__main__":
    unittest.main()
