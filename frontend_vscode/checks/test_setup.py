"""Avatar / VS Code 共通セットアップの再利用と取得回数を確認する。"""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import Mock, patch
import zipfile


ROOT = Path(__file__).resolve().parents[2]


def load_setup(name):
    spec = importlib.util.spec_from_file_location(name + '_setup', ROOT / name / '_setup.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


vscode = load_setup('frontend_vscode')
avatar = load_setup('frontend_avatar')
import setup_electron as common


class ElectronSetupTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name)
        self.cache = self.project / '_cache' / 'electron'
        self.enterContext(patch.object(common, 'CACHE_DIR', self.cache))
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))
        self.root = self.make_app('frontend_vscode')
        self.electron = self.root / 'node_modules' / 'electron'

    def make_app(self, name, version='44.5.1', parent=None):
        root = (parent or self.project) / name
        electron = root / 'node_modules' / 'electron'
        electron.mkdir(parents=True, exist_ok=True)
        (electron / 'package.json').write_text(json.dumps({'version': version}), encoding='utf-8')
        (root / 'package.json').write_text('{}', encoding='utf-8')
        return root

    def make_ready(self, root=None, version='44.5.1'):
        electron = (root or self.root) / 'node_modules' / 'electron'
        executable = common.electron_executable_name()
        binary = electron / 'dist' / executable
        binary.parent.mkdir(parents=True, exist_ok=True)
        binary.write_bytes(b'binary')
        (electron / 'dist' / 'version').write_text(version, encoding='utf-8')
        (electron / 'path.txt').write_text(executable, encoding='utf-8')

    def zip_bytes(self, version='44.5.1'):
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, 'w') as zipped:
            zipped.writestr(common.electron_executable_name(), b'binary')
            zipped.writestr('version', version)
        return archive.getvalue()

    def response(self, version='44.5.1'):
        data = self.zip_bytes(version)
        response = io.BytesIO(data)
        response.headers = {'Content-Length': str(len(data))}
        return response

    def test_both_frontends_use_the_same_setup_function(self):
        self.assertIs(vscode.setup_dependencies, common.setup_dependencies)
        self.assertIs(avatar.setup_dependencies, common.setup_dependencies)

    def test_existing_binary_requires_matching_version_and_path(self):
        self.make_ready()
        self.assertTrue(common.electron_binary_ready(self.root))
        (self.electron / 'dist' / 'version').write_text('44.5.0', encoding='utf-8')
        self.assertFalse(common.electron_binary_ready(self.root))
        (self.electron / 'dist' / 'version').write_text('44.5.1', encoding='utf-8')
        (self.electron / 'path.txt').unlink()
        self.assertFalse(common.electron_binary_ready(self.root))

    def test_prepared_binary_needs_no_network(self):
        self.make_ready()
        with patch.object(common.urllib.request, 'urlopen') as download:
            self.assertTrue(common.prepare_electron_binary(self.root, 'test'))
            download.assert_not_called()

    def test_missing_path_is_repaired_without_download(self):
        self.make_ready()
        (self.electron / 'path.txt').unlink()
        with patch.object(common.urllib.request, 'urlopen') as download:
            self.assertTrue(common.prepare_electron_binary(self.root, 'test'))
            download.assert_not_called()
        self.assertTrue(common.electron_binary_ready(self.root))

    def test_peer_binary_is_copied_without_network(self):
        peer = self.make_app('frontend_avatar')
        self.make_ready(peer)
        with patch.object(common.urllib.request, 'urlopen') as download:
            self.assertTrue(common.prepare_electron_binary(self.root, 'test'))
            download.assert_not_called()
        shutil.rmtree(peer / 'node_modules' / 'electron' / 'dist')
        self.assertTrue(common.electron_binary_ready(self.root))

    def test_different_peer_version_is_not_reused(self):
        peer = self.make_app('frontend_avatar', '44.5.0')
        self.make_ready(peer, '44.5.0')
        with patch.object(common.urllib.request, 'urlopen', return_value=self.response()) as download:
            self.assertTrue(common.prepare_electron_binary(self.root, 'test'))
            download.assert_called_once()
        self.assertTrue(common.electron_binary_ready(self.root))

    def test_download_is_shared_and_zip_survives_reinstall(self):
        with patch.object(common.urllib.request, 'urlopen', return_value=self.response()) as download:
            self.assertTrue(common.prepare_electron_binary(self.root, 'test'))
            peer = self.make_app('frontend_avatar')
            self.assertTrue(common.prepare_electron_binary(peer, 'test'))
            shutil.rmtree(self.electron / 'dist')
            (self.electron / 'path.txt').unlink()
            shutil.rmtree(peer / 'node_modules' / 'electron' / 'dist')
            self.assertTrue(common.prepare_electron_binary(self.root, 'test'))
            download.assert_called_once()
        self.assertEqual(len(list(self.cache.glob('*.zip'))), 1)

    def test_python_download_prepares_each_platform(self):
        for platform_name in ('win32', 'linux', 'darwin'):
            with self.subTest(platform=platform_name), patch.object(common.sys, 'platform', platform_name), patch.object(
                common.platform, 'machine', return_value='AMD64'
            ), patch.object(common.shutil, 'which', return_value=None):
                root = self.make_app('frontend_vscode', parent=self.project / platform_name)
                with patch.object(common.urllib.request, 'urlopen', return_value=self.response()) as download:
                    self.assertTrue(common.prepare_electron_binary(root, 'test'))
                    self.assertTrue(common.electron_binary_ready(root))
                    self.assertIn(f'electron-v44.5.1-{platform_name}-x64.zip', download.call_args.args[0])

    def test_corrupt_cached_zip_is_replaced(self):
        self.cache.mkdir(parents=True)
        with patch.object(common.sys, 'platform', 'win32'), patch.object(common.platform, 'machine', return_value='AMD64'):
            archive = self.cache / 'electron-v44.5.1-win32-x64.zip'
            archive.write_bytes(b'broken ZIP')
            with patch.object(common.urllib.request, 'urlopen', return_value=self.response()) as download:
                self.assertTrue(common.prepare_electron_binary(self.root, 'test'))
                download.assert_called_once()
            self.assertTrue(common._archive_ready(archive, '44.5.1'))

    def test_failed_download_is_not_retried_or_cached(self):
        with patch.object(common.urllib.request, 'urlopen', side_effect=OSError('offline')) as download:
            self.assertFalse(common.prepare_electron_binary(self.root, 'test'))
            download.assert_called_once()
            self.assertEqual(download.call_args.kwargs['timeout'], 30)
        self.assertEqual(list(self.cache.iterdir()), [])

    def test_incomplete_download_is_not_cached(self):
        response = self.response()
        response.headers['Content-Length'] = str(int(response.headers['Content-Length']) + 1)
        with patch.object(common.urllib.request, 'urlopen', return_value=response):
            self.assertFalse(common.prepare_electron_binary(self.root, 'test'))
        self.assertEqual(list(self.cache.iterdir()), [])

    def test_npm_skips_electron_download(self):
        self.make_ready()
        command = Mock(return_value=True)
        self.assertTrue(common.setup_dependencies(self.root, 'npm', 'test', command))
        self.assertEqual([call.args[0] for call in command.call_args_list], [['npm', 'install'], ['npm', 'update']])
        for call in command.call_args_list:
            self.assertEqual(call.kwargs['env']['ELECTRON_SKIP_BINARY_DOWNLOAD'], '1')

    def test_npm_recovery_rebuilds_before_compiling(self):
        self.make_ready()
        with patch.object(vscode, 'FRONTEND_VSCODE_DIR', self.root), patch.object(
            vscode, 'find_vscode_cli', return_value=None
        ), patch.object(vscode.shutil, 'which', return_value='npm'), patch.object(
            vscode, 'run_command', side_effect=[False, True, True, True, True]
        ) as command, patch.object(vscode, 'install_standalone_launcher', return_value=True):
            self.assertTrue(vscode.setup())
            self.assertEqual(
                [['npm', 'install'], ['npm', 'install', '--ignore-scripts'], ['npm', 'update'],
                 ['npm', 'rebuild'], ['npm', 'run', 'compile']],
                [call.args[0] for call in command.call_args_list],
            )

    def test_avatar_completes_with_shared_dependency_setup(self):
        peer = self.make_app('frontend_avatar')
        self.make_ready(peer)
        with patch.object(avatar, 'FRONTEND_AVATAR_DIR', peer), patch.object(
            avatar, 'check_npm_installed', return_value=True
        ), patch.object(avatar, 'run_command', return_value=True) as command:
            self.assertTrue(avatar.setup())
            self.assertEqual([call.args[0][1] for call in command.call_args_list], ['install', 'update'])

    def test_electron_failure_does_not_publish_launcher(self):
        with patch.object(vscode, 'FRONTEND_VSCODE_DIR', self.root), patch.object(
            vscode, 'find_vscode_cli', return_value=None
        ), patch.object(vscode.shutil, 'which', return_value='npm'), patch.object(
            vscode, 'run_command', return_value=True
        ), patch.object(common, 'prepare_electron_binary', return_value=False), patch.object(
            vscode, 'install_standalone_launcher'
        ) as launcher:
            self.assertFalse(vscode.setup())
            launcher.assert_not_called()

    def test_launcher_rename_installs_code_and_live_and_removes_owned_old_name(self):
        for platform_name in ('win32', 'linux'):
            with self.subTest(platform=platform_name):
                home = self.project / platform_name
                launchers = home / '.local' / 'bin'
                launchers.mkdir(parents=True)
                for name in ('aidiy_code', 'aidiy_live'):
                    script = self.root / name / 'launch.mjs'
                    script.parent.mkdir(exist_ok=True)
                    script.write_text('', encoding='utf-8')
                legacy = launchers / ('aidiy_vscode.cmd' if platform_name == 'win32' else 'aidiy_vscode')
                legacy.write_text(str(self.root / 'scripts' / 'launch-standalone.mjs'), encoding='utf-8')
                with patch.object(vscode, 'FRONTEND_VSCODE_DIR', self.root), patch.object(
                    vscode.Path, 'home', return_value=home
                ), patch.object(vscode.sys, 'platform', platform_name):
                    self.assertTrue(vscode.install_standalone_launcher())
                self.assertFalse(legacy.exists())
                for name in ('aidiy_code', 'aidiy_live'):
                    launcher = launchers / (f'{name}.cmd' if platform_name == 'win32' else name)
                    self.assertIn(str(self.root / name / 'launch.mjs'), launcher.read_text(encoding='utf-8'))
                    if platform_name == 'win32':
                        content = launcher.read_bytes()
                        self.assertTrue(content.startswith(b'@echo off\r\nchcp 65001 >nul\r\n'))
                        self.assertNotIn(b'\n', content.replace(b'\r\n', b''))

    def test_launcher_rename_preserves_other_checkout_old_name(self):
        home = self.project / 'other-home'
        launchers = home / '.local' / 'bin'
        launchers.mkdir(parents=True)
        for name in ('aidiy_code', 'aidiy_live'):
            script = self.root / name / 'launch.mjs'
            script.parent.mkdir(exist_ok=True)
            script.write_text('', encoding='utf-8')
        legacy = launchers / 'aidiy_vscode.cmd'
        legacy.write_text('node other-checkout/launch-standalone.mjs', encoding='utf-8')
        with patch.object(vscode, 'FRONTEND_VSCODE_DIR', self.root), patch.object(
            vscode.Path, 'home', return_value=home
        ), patch.object(vscode.sys, 'platform', 'win32'):
            self.assertTrue(vscode.install_standalone_launcher())
        self.assertEqual(legacy.read_text(encoding='utf-8'), 'node other-checkout/launch-standalone.mjs')

    def make_extension_packages(self):
        for folder, name in ((self.root, 'aidiy-code'), (self.root / 'aidiy_live', 'aidiy-live')):
            folder.mkdir(exist_ok=True)
            (folder / 'package.json').write_text(json.dumps({'publisher': 'aidiy', 'name': name, 'version': '0.1.0'}), encoding='utf-8')
            (self.root / 'dist').mkdir(exist_ok=True)
            (self.root / 'dist' / f'{name}-0.1.0.vsix').write_bytes(b'vsix')

    def test_aidiy_prefix_extensions_are_removed_before_both_are_installed(self):
        self.make_extension_packages()
        with patch.object(vscode, 'FRONTEND_VSCODE_DIR', self.root), patch.object(
            vscode, 'run_command', return_value=True
        ) as command, patch.object(vscode, 'get_installed_extensions', side_effect=[
            {'aidiy.aidiy-code', 'aidiy.aidiy-live', 'aidiy.aidiy-vscode', 'other.aidiy-old', 'other.tool'},
            {'other.tool'},
            {'aidiy.aidiy-code@0.1.0', 'aidiy.aidiy-live@0.1.0', 'other.tool'},
        ]):
            self.assertTrue(vscode.install_extensions('code'))
        calls = [call.args[0] for call in command.call_args_list]
        self.assertEqual([call[2] for call in calls[:4]], ['aidiy.aidiy-code', 'aidiy.aidiy-live', 'aidiy.aidiy-vscode', 'other.aidiy-old'])
        self.assertTrue(all(call[1] == '--uninstall-extension' for call in calls[:4]))
        self.assertIn('aidiy-code-0.1.0.vsix', calls[4][2])
        self.assertIn('aidiy-live-0.1.0.vsix', calls[5][2])

    def test_live_install_failure_is_reported_after_removal(self):
        self.make_extension_packages()
        with patch.object(vscode, 'FRONTEND_VSCODE_DIR', self.root), patch.object(
            vscode, 'run_command', side_effect=[True, False]
        ) as command, patch.object(vscode, 'get_installed_extensions', return_value=set()):
            self.assertFalse(vscode.install_extensions('code'))
        self.assertEqual(len(command.call_args_list), 2)

    def test_missing_live_in_installed_list_fails_verification(self):
        self.make_extension_packages()
        with patch.object(vscode, 'FRONTEND_VSCODE_DIR', self.root), patch.object(
            vscode, 'run_command', return_value=True
        ) as command, patch.object(vscode, 'get_installed_extensions', side_effect=[set(), {'aidiy.aidiy-code@0.1.0'}]):
            self.assertFalse(vscode.install_extensions('code'))
        self.assertEqual(len(command.call_args_list), 2)

    def test_missing_vsix_does_not_remove_existing_extensions(self):
        self.make_extension_packages()
        (self.root / 'dist' / 'aidiy-live-0.1.0.vsix').unlink()
        with patch.object(vscode, 'FRONTEND_VSCODE_DIR', self.root), patch.object(vscode, 'run_command') as command:
            self.assertFalse(vscode.install_extensions('code'))
        command.assert_not_called()

    def test_uninstall_failure_stops_setup_before_install(self):
        self.make_extension_packages()
        with patch.object(vscode, 'FRONTEND_VSCODE_DIR', self.root), patch.object(
            vscode, 'run_command', return_value=False
        ) as command, patch.object(vscode, 'get_installed_extensions', return_value={'aidiy.aidiy-code'}):
            self.assertFalse(vscode.install_extensions('code'))
        self.assertEqual([call.args[0] for call in command.call_args_list], [['code', '--uninstall-extension', 'aidiy.aidiy-code']])

    def test_remaining_aidiy_extension_stops_setup_before_install(self):
        self.make_extension_packages()
        with patch.object(vscode, 'FRONTEND_VSCODE_DIR', self.root), patch.object(
            vscode, 'run_command', return_value=True
        ) as command, patch.object(vscode, 'get_installed_extensions', return_value={'other.aidiy-old'}):
            self.assertFalse(vscode.install_extensions('code'))
        self.assertEqual([call.args[0] for call in command.call_args_list], [['code', '--uninstall-extension', 'other.aidiy-old']])


if __name__ == '__main__':
    unittest.main()
