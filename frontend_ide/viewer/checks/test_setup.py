# -*- coding: utf-8 -*-
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026

"""IDE の Windows セットアップが共通 Electron 資産を再利用することを確認する。"""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('viewer_setup_test', ROOT / 'frontend_ide/viewer/_setup.py')
viewer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(viewer)
import _setup_electron as common


class ViewerSetupTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name)
        self.target = self.project / 'frontend_ide/viewer'
        self.electron = self.target / 'node_modules/electron'
        self.electron.mkdir(parents=True)
        (self.electron / 'package.json').write_text(json.dumps({'version': '44.7.0'}), encoding='utf-8')
        (self.target / 'package-lock.json').write_text('{}', encoding='utf-8')
        for name in ('vue', '@xterm/xterm', '@xterm/addon-fit', 'node-pty', 'ws'):
            (self.target.parent / 'node_modules' / name).mkdir(parents=True)
        self.cache = self.project / '_cache/electron'
        self.enterContext(patch.object(viewer, 'THIS_DIR', self.target))
        self.enterContext(patch.object(common, 'CACHE_DIR', self.cache))
        self.enterContext(patch.object(viewer.sys, 'platform', 'win32'))
        self.enterContext(patch.dict(os.environ, {}, clear=True))
        self.enterContext(patch.object(viewer.shutil, 'which', return_value='npm.cmd'))
        self.run = self.enterContext(patch.object(viewer.subprocess, 'run'))
        self.launcher = self.enterContext(patch.object(viewer, 'install_launcher'))
        self.download = self.enterContext(patch.object(common.urllib.request, 'urlopen', side_effect=OSError('network unavailable')))
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))

    def assert_installed(self):
        self.assertTrue(viewer.setup())
        npm = self.run.call_args_list[0]
        self.assertEqual(npm.args[0][1], 'ci')
        self.assertEqual(npm.kwargs['env']['ELECTRON_SKIP_BINARY_DOWNLOAD'], '1')
        self.assertEqual(self.run.call_args_list[-1].args[0], ['npm.cmd', 'run', 'build'])
        self.launcher.assert_called_once_with(self.target)
        self.download.assert_not_called()
        self.assertTrue(common.electron_binary_ready(self.target))

    def test_windows_reuses_host_binary_without_node_or_python_download(self):
        dist = self.project / 'frontend_ide/host/node_modules/electron/dist'
        dist.mkdir(parents=True)
        (dist / 'electron.exe').write_bytes(b'binary')
        (dist / 'version').write_text('44.7.0', encoding='utf-8')
        self.assert_installed()
        self.assertEqual((self.electron / 'dist/electron.exe').read_bytes(), b'binary')

    def test_windows_reuses_cached_zip_without_network(self):
        self.cache.mkdir(parents=True)
        with patch.object(common.platform, 'machine', return_value='AMD64'):
            with zipfile.ZipFile(self.cache / 'electron-v44.7.0-win32-x64.zip', 'w') as archive:
                archive.writestr('electron.exe', b'binary')
                archive.writestr('version', '44.7.0')
            self.assert_installed()

    def test_binary_failure_stops_before_build_and_launcher(self):
        with patch.object(viewer, 'prepare_electron_binary', return_value=False):
            self.assertFalse(viewer.setup())
        self.assertEqual(self.run.call_count, 1)
        self.launcher.assert_not_called()

    def test_web_and_explicit_skip_do_not_prepare_binary(self):
        for env in ({'CODESPACES': 'true'}, {'ELECTRON_SKIP_BINARY_DOWNLOAD': '1'}):
            with self.subTest(env=env), patch.dict(os.environ, env, clear=True), patch.object(viewer, 'prepare_electron_binary') as prepare:
                self.assertTrue(viewer.setup())
                self.assertEqual(self.run.call_args_list[-2].kwargs['env']['ELECTRON_SKIP_BINARY_DOWNLOAD'], '1')
                prepare.assert_not_called()
        self.download.assert_not_called()

    def test_npm_failure_stops_before_binary_and_launcher(self):
        self.run.side_effect = subprocess.CalledProcessError(1, 'npm ci')
        with patch.object(viewer, 'prepare_electron_binary') as prepare:
            self.assertFalse(viewer.setup())
            prepare.assert_not_called()
        self.launcher.assert_not_called()


if __name__ == '__main__':
    unittest.main()
