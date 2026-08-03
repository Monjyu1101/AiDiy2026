# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

import asyncio
import os
import sys
import threading
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools_proc.tools_chrome import register_tools


class _FakeMCP:
    def tool(self):
        def decorator(func):
            return func
        return decorator


class _FakeChromeManager:
    def __init__(self):
        self.ensure_thread_id: int | None = None
        self.ensure_count = 0
        self.active_count = 0
        self.max_active_count = 0
        self._lock = threading.Lock()

    def ensure_running(self, show_automation_banner=None):
        self.ensure_thread_id = threading.get_ident()
        with self._lock:
            self.ensure_count += 1
            self.active_count += 1
            self.max_active_count = max(self.max_active_count, self.active_count)
        time.sleep(0.02)
        with self._lock:
            self.active_count -= 1
        return "already_running"


class _FakeRegistry:
    def __init__(self):
        self.manager = _FakeChromeManager()
        self.cdp = object()
        self.get_thread_id: int | None = None

    def get(self, session="default", headless=None):
        self.get_thread_id = threading.get_ident()
        time.sleep(0.02)
        return self.manager, self.cdp


class ChromeEnsureTests(unittest.IsolatedAsyncioTestCase):
    async def test_registry_and_health_check_run_outside_event_loop(self):
        registry = _FakeRegistry()
        ensure_chrome = register_tools(_FakeMCP(), registry)
        event_loop_thread = threading.get_ident()

        cdp = await ensure_chrome(session="test")

        self.assertIs(cdp, registry.cdp)
        self.assertNotEqual(registry.get_thread_id, event_loop_thread)
        self.assertNotEqual(registry.manager.ensure_thread_id, event_loop_thread)
        self.assertEqual(registry.manager.ensure_count, 1)

    async def test_same_session_startup_is_serialized(self):
        registry = _FakeRegistry()
        ensure_chrome = register_tools(_FakeMCP(), registry)

        await asyncio.gather(
            ensure_chrome(session="same"),
            ensure_chrome(session="same"),
        )

        self.assertEqual(registry.manager.ensure_count, 2)
        self.assertEqual(registry.manager.max_active_count, 1)


if __name__ == "__main__":
    unittest.main()
