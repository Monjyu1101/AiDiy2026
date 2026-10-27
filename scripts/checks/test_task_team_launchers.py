"""Task / Team の PATH 登録と停止対象を一時環境だけで確認する。"""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[2]
def load(path):
    spec = importlib.util.spec_from_file_location('test_task_team_' + path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
class Launchers(unittest.TestCase):
    def test_path_launchers_windows_and_posix(self):
        launcher = load(ROOT / 'frontend_ide/viewer/launcher.py')
        for platform in ('win32', 'linux', 'darwin'):
            for kind in ('task', 'team'):
                with self.subTest(platform=platform, kind=kind), tempfile.TemporaryDirectory() as home:
                    with patch.object(Path, 'home', return_value=Path(home)), patch.object(launcher.sys, 'platform', platform), patch.object(launcher.shutil, 'which', return_value='/usr/bin/node'), patch.object(launcher, 'ensure_launcher_path', return_value=True):
                        launcher.install_launcher(ROOT / 'frontend_ide' / ('aidiy_' + kind), kind)
                        path=launcher.launcher_path(kind)
                        self.assertIn('aidiy_' + kind, path.read_text())
                        self.assertNotIn('aidiy_avatar', path.read_text())
                        if platform != 'win32': self.assertTrue(path.stat().st_mode & 0o111)
    def test_process_scope_keeps_other_apps_safe(self):
        start=load(ROOT / 'frontend_ide/viewer/_start.py')
        scope=load(ROOT / 'scripts/_setup_processes.py')
        for kind in ('task', 'team'):
            proc={'Name':'node','CommandLine':f'node {ROOT}/frontend_ide/launch.mjs --app {kind}'}
            self.assertTrue(start.is_dev_process(proc, ROOT / 'frontend_ide/viewer', False, kind))
            self.assertFalse(start.is_dev_process(proc, ROOT / 'frontend_ide/viewer', False, 'ide'))
            self.assertEqual(scope.process_role(proc, ROOT, False), kind)
        self.assertEqual(scope.KEEP, frozenset(('code','ide','frontend_channels')))
if __name__ == '__main__': unittest.main()
