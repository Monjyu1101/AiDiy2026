# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

REPO_DIR = Path(__file__).resolve().parents[2]
BACKEND_SERVER_DIR = REPO_DIR / "backend_server"
sys.path.insert(0, str(BACKEND_SERVER_DIR))


def _load_module():
    path = BACKEND_SERVER_DIR / "AIコア" / "AI内部ツール.py"
    spec = importlib.util.spec_from_file_location("test_ai_internal_tools_target", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class MCPBridgeLoopbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = _load_module()

    def test_default_url_uses_ipv4_loopback(self):
        bridge = self.module.MCPツールブリッジ()
        self.assertEqual(bridge.base_url, "http://127.0.0.1:8095")

    def test_list_mcps_uses_dedicated_no_proxy_opener(self):
        bridge = self.module.MCPツールブリッジ()
        response = MagicMock()
        response.read.return_value = json.dumps({"mcps": ["aidiy_sqlite"]}).encode()
        response.__enter__.return_value = response
        bridge._http_opener = MagicMock()
        bridge._http_opener.open.return_value = response

        self.assertEqual(bridge.list_mcps(), ["aidiy_sqlite"])
        bridge._http_opener.open.assert_called_once_with(
            "http://127.0.0.1:8095/", timeout=10,
        )


if __name__ == "__main__":
    unittest.main()
