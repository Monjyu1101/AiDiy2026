# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools_proc.chrome_devtools import CDPClient, _normalize_loopback_ws_url


class CDPClientLoopbackTests(unittest.TestCase):
    def test_default_host_is_ipv4_loopback(self):
        self.assertEqual(CDPClient().host, "127.0.0.1")

    def test_http_get_uses_no_proxy_opener(self):
        response = MagicMock()
        response.read.return_value = b'{"Browser":"Chrome"}'
        response.__enter__.return_value = response
        with patch("tools_proc.chrome_devtools._NO_PROXY_OPENER.open", return_value=response) as open_mock:
            result = CDPClient(port=9333).get_version()
        self.assertEqual(result, {"Browser": "Chrome"})
        open_mock.assert_called_once_with("http://127.0.0.1:9333/json/version", timeout=5)

    def test_chrome_localhost_websocket_url_is_normalized(self):
        url = "ws://localhost:9222/devtools/page/abc"
        self.assertEqual(
            _normalize_loopback_ws_url(url),
            "ws://127.0.0.1:9222/devtools/page/abc",
        )

    def test_non_loopback_websocket_url_is_unchanged(self):
        url = "ws://192.0.2.10:9222/devtools/page/abc"
        self.assertEqual(_normalize_loopback_ws_url(url), url)


if __name__ == "__main__":
    unittest.main()
