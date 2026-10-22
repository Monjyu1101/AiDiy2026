"""Diagの所有判定と、停止失敗時に削除へ進まないことを検証する。"""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


diag = load(ROOT / '_cleanup.py', 'diag_cleanup_test')
processes = diag._stop_helper
cleanup = load(ROOT.parent / '_cleanup.py', 'root_cleanup_test')


class DiagCleanupTests(unittest.TestCase):
    def owned(self, command, name='node.exe', executable=''):
        return processes.is_diag(dict(Name=name, CommandLine=command, ExecutablePath=executable), ROOT, True)

    def test_normal_and_preloaded_entrypoints(self):
        for entry in (ROOT / 'diag_main.mjs', ROOT / '起動/electron-main.cjs'):
            for prefix in ('', '--require "C:\\test dir\\probe.cjs" ', '--import=probe.mjs ', '-- '):
                self.assertTrue(self.owned(f'node.exe {prefix}"{entry}" --foreground'))

    def test_orphan_electron_children(self):
        exe = str(ROOT / 'node_modules/electron/dist/electron.exe')
        for kind in ('gpu-process', 'renderer', 'utility'):
            self.assertTrue(self.owned(f'"{exe}" --type={kind}', 'electron.exe'))
        self.assertTrue(self.owned('', 'electron.exe', exe))

    def test_other_checkout_and_argument_mentions_are_excluded(self):
        entry = ROOT / 'diag_main.mjs'
        for command in (f'node.exe other.js "{entry}"', f'node.exe --eval "run()" "{entry}"',
                        f'node.exe -erun() "{entry}"',
                        f'node.exe "{entry}.old"', f'node.exe "{ROOT}-other/diag_main.mjs"'):
            self.assertFalse(self.owned(command))
        self.assertFalse(self.owned(f'Code.exe "{entry}"', 'Code.exe'))
        self.assertFalse(self.owned(f'"{ROOT}-other/node_modules/electron/dist/electron.exe" --type=renderer', 'electron.exe'))

    def test_posix_entrypoint_with_spaces(self):
        root = (ROOT / 'space folder').resolve()
        self.assertTrue(processes.is_diag(dict(Name='node', CommandLine=f"node --require '/tmp/probe file.cjs' '{root.as_posix()}/diag_main.mjs'"), root, False))

    def test_macos_orphan_electron_children(self):
        distribution = ROOT / 'node_modules/electron/dist/Electron.app/Contents'
        targets = [('Electron', distribution / 'MacOS/Electron')]
        for suffix in ('', ' (GPU)', ' (Renderer)', ' (Plugin)'):
            name = f'Electron Helper{suffix}'
            targets.append((name, distribution / f'Frameworks/{name}.app/Contents/MacOS/{name}'))
        for name, executable in targets:
            with self.subTest(name=name):
                self.assertTrue(processes.is_diag(dict(Name=name, CommandLine='', ExecutablePath=str(executable)), ROOT, False))
                self.assertTrue(processes.is_diag(dict(Name=name, CommandLine=f'"{executable}" --type=renderer'), ROOT, False))

    def test_posix_case_normalization_does_not_expand_project_scope(self):
        name = 'Electron'
        for other_root in (Path(str(ROOT) + '-other'), ROOT.with_name(ROOT.name.upper())):
            executable = other_root / 'node_modules/electron/dist/Electron.app/Contents/MacOS/Electron'
            self.assertFalse(processes.is_diag(dict(Name=name, CommandLine='', ExecutablePath=str(executable)), ROOT, False))
            self.assertFalse(processes.is_diag(dict(Name=name, CommandLine=f'Electron "{other_root / "起動/electron-main.cjs"}"'), ROOT, False))
        self.assertTrue(processes.is_diag(dict(Name=name, CommandLine=f'Electron "{ROOT / "起動/electron-main.cjs"}"'), ROOT, False))
        self.assertFalse(processes.is_diag(dict(Name=name, CommandLine=f'Electron other.js "{ROOT / "起動/electron-main.cjs"}"'), ROOT, False))

    def test_stop_uses_tree_termination_and_checks_exit(self):
        record = dict(ProcessId=987654, ParentProcessId=0, Name='node.exe', CommandLine=f'node.exe "{ROOT / "diag_main.mjs"}"')
        common = processes.common
        with patch.object(common, 'list_processes', side_effect=[[record], [record], []]), \
                patch.object(common.sys, 'platform', 'win32'), \
                patch.object(common.subprocess, 'CREATE_NO_WINDOW', 0x08000000, create=True), \
                patch.object(common.subprocess, 'run') as run, patch('builtins.print'):
            self.assertTrue(processes.stop(ROOT))
        self.assertEqual(run.call_args.args[0], ['taskkill', '/F', '/T', '/PID', '987654'])
        self.assertEqual(run.call_args.kwargs['creationflags'], 0x08000000)

    def test_stop_failure_preserves_launcher(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(diag, '__file__', str(Path(folder) / '_cleanup.py')), \
                patch.object(diag, 'stop_processes', return_value=False), patch.object(diag, 'remove_launcher_path') as remove:
            self.assertFalse(diag.cleanup())
            remove.assert_not_called()

    def test_root_cleanup_requests_diag_stop_even_without_uninstall(self):
        with patch.object(cleanup, 'stop_all_services', side_effect=RuntimeError('stop failed')) as stop, \
                patch.object(cleanup, 'cleanup_backup') as delete, patch('builtins.print'):
            with self.assertRaisesRegex(RuntimeError, 'stop failed'):
                cleanup.execute_cleanup(ROOT.parent, {'diag': False})
        stop.assert_called_once_with({'diag': False}, keep_diag=False)
        delete.assert_not_called()

    def test_diag_stop_failure_is_reported_after_other_services_stop(self):
        module = Mock()
        module.stop_processes.return_value = False
        with patch.object(cleanup, '_load_folder_module', return_value=module), \
                patch.object(cleanup, '_load_folder_start_module', return_value=module), \
                patch.object(cleanup.time, 'sleep'), patch('builtins.print'):
            with self.assertRaisesRegex(RuntimeError, 'Diag'):
                cleanup.stop_all_services(keep_diag=False)
        module.kill_ports.assert_called()
        module.stop_tools_processes.assert_called_once()

    def test_normal_start_stop_preserves_diag(self):
        module = Mock()
        module.process_tree_pids.return_value = set()
        with patch.object(cleanup, '_load_folder_module', return_value=module), \
                patch.object(cleanup, '_load_folder_start_module', return_value=module), \
                patch.object(cleanup.time, 'sleep'), patch('builtins.print'):
            self.assertTrue(cleanup.stop_all_services(keep_code=True, keep_dev=True, keep_discord=True))
        module.stop_processes.assert_not_called()


if __name__ == '__main__':
    unittest.main()
