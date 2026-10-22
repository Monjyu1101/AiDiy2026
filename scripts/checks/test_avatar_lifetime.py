"""Avatarは全体終了でも停止し、Code/IDEは通常終了で継続する。実プロセスは停止しない。"""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]


def load(name):
    spec = importlib.util.spec_from_file_location('avatar_lifetime_' + name, ROOT / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AvatarLifetimeTest(unittest.TestCase):
    def test_setup_stops_only_live_and_avatar(self):
        setup = load('_setup')
        host, avatar = Mock(), Mock()
        with patch.object(setup, '_load_folder_module', side_effect=[host, avatar]) as loader:
            setup.stop_live_avatar()
        self.assertEqual([call.args for call in loader.call_args_list], [('frontend_ide/host', '_start.py'), ('frontend_avatar', '_start.py')])
        host.kill_ports.assert_called_once_with('live')
        avatar.kill_ports.assert_called_once_with()

    def test_normal_stop_closes_avatar_but_preserves_code_and_ide(self):
        start = load('_start')
        avatar = Mock()
        process = Mock()
        with patch.object(start, 'AVATAR', avatar), patch.object(start.subprocess, 'run') as run:
            start.stop_processes({'フロントエンド(Avatar)': process, 'フロントエンド(code)': Mock(), 'フロントエンド(IDE)': Mock()})
        run.assert_not_called()
        avatar.kill_ports.assert_called_once_with()

    def test_cleanup_stops_avatar_even_when_code_and_ide_are_preserved(self):
        cleanup = load('_cleanup')
        for keep in (True, False):
            calls = []
            def fake_module(folder):
                module = Mock()
                module.kill_ports.side_effect = lambda *args: calls.append(folder)
                module.process_tree_pids.return_value = set()
                return module
            with patch.object(cleanup, '_load_folder_start_module', side_effect=fake_module), \
                    patch.object(cleanup, '_load_folder_module', side_effect=fake_module), \
                    patch.object(cleanup.time, 'sleep'):
                cleanup.stop_all_services(keep_code=keep, keep_dev=keep, keep_discord=True)
            self.assertIn('frontend_avatar', calls)
            self.assertEqual('frontend_ide/viewer' in calls, not keep)


if __name__ == '__main__':
    unittest.main()
