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
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_proc.chrome_manager import ChromeManager


class ChromeManagerLaunchOptionTests(unittest.TestCase):
    def test_default_launch_args_include_automation_banner(self):
        manager = ChromeManager(profile_dir="D:\\tmp\\chrome-profile")
        args = manager._build_launch_args("chrome.exe")
        self.assertIn("--enable-automation", args)

    def test_launch_args_can_hide_automation_banner(self):
        manager = ChromeManager(profile_dir="D:\\tmp\\chrome-profile")
        args = manager._build_launch_args("chrome.exe", show_automation_banner=False)
        self.assertNotIn("--enable-automation", args)

    def test_constructor_can_change_default_banner_setting(self):
        manager = ChromeManager(show_automation_banner=False)
        args = manager._build_launch_args("chrome.exe")
        self.assertNotIn("--enable-automation", args)

    def test_ensure_running_forwards_banner_override(self):
        manager = ChromeManager()
        with patch.object(manager, "is_running", return_value=False):
            with patch.object(manager, "launch", return_value="launched") as launch_mock:
                result = manager.ensure_running(show_automation_banner=False)
        self.assertEqual(result, "launched")
        launch_mock.assert_called_once_with(show_automation_banner=False)


if __name__ == "__main__":
    unittest.main()
