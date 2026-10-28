# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
"""接続専用Browserの登録試験。GUI依存だけを置換し、プロセスは起動しない。"""
import json
import logging
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'backend_tools'))
# この試験は画面キャプチャを使わない。未導入のscreeninfo/OS GUIを要求しない。
capture = types.ModuleType('tools_proc.desktop_capture')
capture.DesktopCapture = object
log = types.ModuleType('log_config')
log.get_logger = logging.getLogger
with patch.dict(sys.modules, {'tools_proc.desktop_capture': capture, 'log_config': log}):
    from tools_proc.ide_browser_session import is_ide_session, read_ide_session, IDEBrowserManager, IDEBrowserClient
    import tools_proc.chrome_sessions as sessions
    from tools_proc.chrome_sessions import ChromeSessionRegistry


class BrowserSessionsTest(unittest.TestCase):
    def test_names_and_manifest_validation(self):
        for name in ('aidiy_ide', 'aidiy_ide-2', 'aidiy_browser', 'aidiy_browser-2', 'aidiy_browser-100'):
            self.assertTrue(is_ide_session(name))
        for name in ('aidiy_browser-1', 'aidiy_browser-01', 'aidiy_browser/../../x', 'aidiy_browser_extra', 'default'):
            self.assertFalse(is_ide_session(name))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            entry = dict(name='aidiy_browser', port=12345, token='12345678-1234-1234-1234-123456789abc', pid=1)
            (root / 'aidiy_browser.json').write_text(json.dumps(entry))
            self.assertEqual(read_ide_session(root, 'aidiy_browser'), entry)
            entry['port'] = True
            (root / 'aidiy_browser.json').write_text(json.dumps(entry))
            self.assertIsNone(read_ide_session(root, 'aidiy_browser'))

    def test_registry_discovers_without_chrome_or_persistence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifests = root / '_ide_browser_sessions'
            manifests.mkdir()
            for name in ('aidiy_browser', 'aidiy_browser-2', 'aidiy_ide'):
                (manifests / (name + '.json')).write_text(json.dumps(dict(name=name, port=12345, token='12345678-1234-1234-1234-123456789abc', pid=1)))
            registry = ChromeSessionRegistry(sessions_file=root / '_chrome_sessions.json')
            with patch.object(sessions, 'ChromeManager', side_effect=AssertionError('Chrome must not start')), patch.object(IDEBrowserManager, 'is_running', return_value=True), patch.object(IDEBrowserManager, 'close', return_value=True):
                for name in ('aidiy_browser', 'aidiy_browser-2', 'aidiy_ide'):
                    manager, client = registry.get(name)
                    self.assertIsInstance(manager, IDEBrowserManager)
                    self.assertIsInstance(client, IDEBrowserClient)
                items = {item['session']: item for item in registry.list()}
                self.assertEqual(items['aidiy_browser']['owner'], 'aidiy_browser')
                self.assertEqual(items['aidiy_ide']['owner'], 'aidiy_ide')
                self.assertTrue(registry.close('aidiy_browser'))
                self.assertTrue(registry.delete('aidiy_browser-2'))
                self.assertTrue((manifests / 'aidiy_browser.json').exists())
                self.assertFalse(registry.sessions_file.exists())
                with self.assertRaises(RuntimeError):
                    registry.get('aidiy_browser-3')
                self.assertIsNone(registry.peek('aidiy_browser-3'))


if __name__ == '__main__':
    unittest.main()
