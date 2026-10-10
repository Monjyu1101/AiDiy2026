# -*- coding: utf-8 -*-
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026

"""全体 setup / cleanup で IDE と Discord のランチャーを取り違えない。"""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]


def load(folder, name):
    spec = importlib.util.spec_from_file_location(f'test_{folder}_{name}', ROOT / folder / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LauncherTests(unittest.TestCase):
    def test_setup_and_cleanup_keep_commands_separate_in_both_orders(self):
        for order in [('frontend_ide/viewer', 'frontend_discord'), ('frontend_discord', 'frontend_ide/viewer')]:
            with self.subTest(order=order), tempfile.TemporaryDirectory() as temp:
                # 先に別フォルダの launcher が import 済みでも影響しない。
                cached = load(order[0], 'launcher')
                with patch.dict(sys.modules, {'launcher': cached}), patch.object(Path, 'home', return_value=Path(temp)), patch.object(sys, 'path', sys.path.copy()):
                    modules = {folder: load(folder, '_setup') for folder in order}
                    paths = {}
                    for folder, module in modules.items():
                        module.install_launcher(ROOT / folder)
                        paths[folder] = module._launcher.launcher_path()
                    self.assertNotEqual(*paths.values())
                    for folder, path in paths.items():
                        entry = ROOT / folder / ('panel/launch.mjs' if folder == 'frontend_discord' else 'launch.mjs')
                        self.assertIn(str(entry), path.read_text(encoding='utf-8'))
                    first, second = order
                    self.assertTrue(load(first, '_cleanup').remove_launcher(ROOT / first))
                    self.assertFalse(paths[first].exists())
                    self.assertTrue(paths[second].is_file())
                    self.assertTrue(load(second, '_cleanup').remove_launcher(ROOT / second))
                    self.assertFalse(paths[second].exists())

    def test_missing_entry_does_not_overwrite_registered_command(self):
        for folder in ('frontend_ide/viewer', 'frontend_discord'):
            with self.subTest(folder=folder), tempfile.TemporaryDirectory() as temp:
                launcher = load(folder, 'launcher')
                path = Path(temp) / 'command'
                path.write_text('existing command', encoding='utf-8')
                with patch.object(launcher, 'launcher_path', return_value=path):
                    with self.assertRaises(OSError):
                        launcher.install_launcher(Path(temp) / 'missing')
                self.assertEqual(path.read_text(encoding='utf-8'), 'existing command')


if __name__ == '__main__':
    unittest.main()
