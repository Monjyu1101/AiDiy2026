# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""ChromeSessionRegistry のユニットテスト（Chrome は起動しない）"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools_proc.chrome_sessions import ChromeSessionRegistry


def _make_registry(tmp_dir: str) -> ChromeSessionRegistry:
    return ChromeSessionRegistry(
        default_port=9222,
        port_range=(9223, 9230),
        sessions_file=Path(tmp_dir) / "_chrome_sessions.json",
    )


class ChromeSessionRegistryTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        # ポート探索・Chrome 疎通は実ネットワークを使わない
        self._p1 = patch("tools_proc.chrome_sessions._port_is_free", return_value=True)
        self._p2 = patch.object(ChromeSessionRegistry, "_chrome_responding", return_value=False)
        self._p1.start()
        self._p2.start()

    def tearDown(self):
        self._p1.stop()
        self._p2.stop()
        self._tmp.cleanup()

    def test_default_session_keeps_legacy_port_and_profile(self):
        registry = _make_registry(self._tmp.name)
        manager, cdp = registry.get()
        self.assertEqual(manager.debug_port, 9222)
        self.assertEqual(cdp.port, 9222)
        self.assertTrue(manager.profile_dir.endswith("_chrome_profile"))

    def test_free_string_session_names_are_mapped_to_safe_keys(self):
        registry = _make_registry(self._tmp.name)
        for name in ("../evil", "M得意先", "con", "a/b\\c:d*e?f"):
            manager, _ = registry.get(name)
            # プロファイルディレクトリにセッション名が直接使われない（内部キー s0001 等）
            basename = Path(manager.profile_dir).name
            self.assertRegex(basename, r"^_chrome_profile_s\d{4}$")

    def test_each_session_gets_distinct_port(self):
        registry = _make_registry(self._tmp.name)
        m1, _ = registry.get("google")
        m2, _ = registry.get("yahoo")
        m3, _ = registry.get()
        ports = {m1.debug_port, m2.debug_port, m3.debug_port}
        self.assertEqual(len(ports), 3)

    def test_same_name_returns_same_instance(self):
        registry = _make_registry(self._tmp.name)
        self.assertIs(registry.get("google")[0], registry.get("google")[0])

    def test_mapping_persists_across_restart(self):
        registry = _make_registry(self._tmp.name)
        port_before = registry.get("M得意先")[0].debug_port
        # 別インスタンス（backend_tools 再起動相当）で同じ割り当てが復元される
        registry2 = _make_registry(self._tmp.name)
        self.assertEqual(registry2.get("M得意先")[0].debug_port, port_before)

    def test_headless_flag_is_stored_and_applied(self):
        registry = _make_registry(self._tmp.name)
        manager, _ = registry.get("テストA", headless=True)
        self.assertTrue(manager.headless)
        args = manager._build_launch_args("chrome.exe")
        self.assertIn("--headless=new", args)
        self.assertIn("--window-size=1920,1080", args)
        # headless=None（省略）では設定を変えない
        manager2, _ = registry.get("テストA")
        self.assertTrue(manager2.headless)

    def test_list_and_delete(self):
        registry = _make_registry(self._tmp.name)
        registry.get("google")
        registry.get("yahoo")
        names = {s["session"] for s in registry.list()}
        self.assertEqual(names, {"google", "yahoo"})
        self.assertTrue(registry.delete("google"))
        names = {s["session"] for s in registry.list()}
        self.assertEqual(names, {"yahoo"})
        self.assertFalse(registry.delete("google"))


if __name__ == "__main__":
    unittest.main()
