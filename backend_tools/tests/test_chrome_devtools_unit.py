# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

import asyncio
import json
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

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


class _FakeWebSocket:
    def __init__(self, fail_send: bool = False):
        self.sent: list[dict] = []
        self.responses: asyncio.Queue[str] = asyncio.Queue()
        self.closed = False
        self.fail_send = fail_send

    async def send(self, payload: str) -> None:
        if self.fail_send:
            raise OSError("closed")
        command = json.loads(payload)
        self.sent.append(command)
        await self.responses.put(json.dumps({
            "id": command["id"],
            "result": {"method": command["method"]},
        }))

    async def recv(self) -> str:
        return await self.responses.get()

    async def close(self) -> None:
        self.closed = True


class CDPClientConnectionTests(unittest.IsolatedAsyncioTestCase):
    async def test_send_command_disables_proxy_and_reuses_connection(self):
        ws = _FakeWebSocket()
        connect_mock = AsyncMock(return_value=ws)
        client = CDPClient()

        with patch("tools_proc.chrome_devtools.websockets.connect", connect_mock):
            first = await client.send_command(
                "ws://localhost:9222/devtools/page/abc",
                "Runtime.evaluate",
            )
            second = await client.send_command(
                "ws://localhost:9222/devtools/page/abc",
                "DOM.getDocument",
            )

        self.assertEqual(first, {"method": "Runtime.evaluate"})
        self.assertEqual(second, {"method": "DOM.getDocument"})
        self.assertEqual([item["id"] for item in ws.sent], [1, 2])
        connect_mock.assert_awaited_once_with(
            "ws://127.0.0.1:9222/devtools/page/abc",
            max_size=50 * 1024 * 1024,
            open_timeout=10,
            proxy=None,
        )

        await client.close_connections()
        self.assertTrue(ws.closed)

    async def test_send_failure_reconnects_once(self):
        stale_ws = _FakeWebSocket(fail_send=True)
        fresh_ws = _FakeWebSocket()
        connect_mock = AsyncMock(side_effect=[stale_ws, fresh_ws])
        client = CDPClient()

        with patch("tools_proc.chrome_devtools.websockets.connect", connect_mock):
            result = await client.send_command(
                "ws://127.0.0.1:9222/devtools/page/abc",
                "Runtime.evaluate",
            )

        self.assertEqual(result, {"method": "Runtime.evaluate"})
        self.assertTrue(stale_ws.closed)
        self.assertEqual(connect_mock.await_count, 2)
        await client.close_connections()


if __name__ == "__main__":
    unittest.main()
