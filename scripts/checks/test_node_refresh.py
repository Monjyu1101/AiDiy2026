# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026

"""git pull後の再配置を、インストール・設定変更・OS窓起動なしで検証する。"""
import contextlib
import importlib.util
import io
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


setup = load("node_refresh_root", "_setup.py")
common = load("node_refresh_electron", "scripts/_setup_electron.py")
host = load("node_refresh_host", "frontend_ide/host/_setup.py")


class NodeRefreshTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))
        self.enterContext(patch.object(setup, "AUTO_MODE", False))

    def test_existing_keys_and_new_key_are_case_insensitive(self):
        for key, expected in [(b"y", (True, False)), (b"n", (False, False)),
                              (b"a", (True, True)), (b"r", ("node", False))]:
            for value in (key, key.upper()):
                with self.subTest(key=value), patch.object(setup, "_read_single_key", return_value=value) as read:
                    self.assertEqual(setup.ask_start_mode("test"), expected)
                    self.assertIn(value, read.call_args.args[0])
                    self.assertEqual(read.call_args.args[1], b"n")

    def test_cancel_and_auto_keep_existing_choices(self):
        with patch.object(setup, "_read_single_key", return_value=b"n"), patch.object(setup, "ask_yes_no") as ask:
            self.assertIsNone(setup.collect_setup_choices())
            ask.assert_not_called()
        with patch.object(setup, "_read_single_key", return_value=b"a") as read:
            choices = setup.collect_setup_choices()
            read.assert_called_once()
            self.assertTrue(choices["common_python_upgrade"])
            self.assertTrue(choices["local"])
            self.assertEqual(choices["local_download"], "no")
            self.assertTrue(choices["mcp_config"])
            self.assertNotIn("node_refresh", choices)
        with patch.object(setup, "_read_single_key", return_value=b"y"), patch.object(setup, "ask_yes_no", return_value=False) as ask:
            choices = setup.collect_setup_choices()
            self.assertGreater(ask.call_count, 0)
            self.assertTrue(choices["diag"])
            self.assertFalse(choices["common"])
            self.assertFalse(setup.AUTO_MODE)

    def test_refresh_bypasses_full_setup_and_reports_failure_exit(self):
        for failures in ([], ["Web: ビルド"]):
            with self.subTest(failures=failures), contextlib.ExitStack() as stack:
                stack.enter_context(patch.object(setup, "_read_single_key", return_value=b"r"))
                refresh = stack.enter_context(patch.object(setup, "setup_node_refresh", return_value=failures))
                for name in ("ask_yes_no", "ensure_prerequisites", "setup_common_global_tools", "run_diag_headless", "_load_folder_module"):
                    stack.enter_context(patch.object(setup, name, side_effect=AssertionError("full setup forbidden")))
                if failures:
                    with self.assertRaises(SystemExit) as result:
                        setup.main()
                    self.assertEqual(result.exception.code, 1)
                else:
                    setup.main()
                refresh.assert_called_once()

    def fixture(self, *, desktop=True):
        self.enterContext(patch.object(setup, "get_node_version", return_value="v24"))
        self.enterContext(patch.object(setup, "get_npm_version", return_value="11"))
        self.enterContext(patch.object(setup, "npm_command", return_value="npm"))
        self.enterContext(patch.dict(os.environ, {"CODESPACES": "false" if desktop else "true", "ELECTRON_SKIP_BINARY_DOWNLOAD": "", "DISPLAY": ":fixture"}))
        prepare = self.enterContext(patch.object(common, "prepare_electron_binary", return_value=True))
        self.enterContext(patch.object(setup.importlib.util, "spec_from_file_location", return_value=SimpleNamespace(loader=SimpleNamespace(exec_module=lambda module: None))))
        self.enterContext(patch.object(setup.importlib.util, "module_from_spec", return_value=common))
        run = self.enterContext(patch.object(setup, "run_command", return_value=True))
        modules = {
            "backend_diag": SimpleNamespace(setup=Mock(return_value=True)),
            "frontend_avatar": SimpleNamespace(install_standalone_launcher=Mock(return_value=True)),
            "frontend_ide/host": SimpleNamespace(setup_assets=Mock(return_value=True)),
            "frontend_ide/viewer": SimpleNamespace(install_launcher=Mock(return_value=None)),
            "frontend_ide/aidiy_term": SimpleNamespace(setup=Mock(return_value=True)),
            # setup()やconf_jsonは用意しない。設定補完経路へ入れば失敗する。
            "frontend_channels": SimpleNamespace(install_launcher=Mock(return_value=None)),
        }
        self.enterContext(patch.object(setup, "_load_folder_module", side_effect=modules.__getitem__))
        return run, prepare, modules

    def test_refresh_syncs_all_dependencies_and_always_builds_then_reinstalls_launchers(self):
        run, prepare, modules = self.fixture()
        # 2回目（依存導入済み）もsource変更を反映するため全ビルドを呼ぶ。
        for _ in range(2):
            self.assertEqual(setup.setup_node_refresh(), [])
        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual(sum(command[1] == "install" for command in commands), 16)
        self.assertTrue(all(command[1] in ("install", "run") for command in commands))
        self.assertTrue(all("--include=dev" in command for command in commands if command[1] == "install"))
        builds = [(call.kwargs["cwd"].relative_to(ROOT).as_posix(), call.args[0][-1])
                  for call in run.call_args_list if call.args[0][1] == "run"]
        self.assertEqual(builds, [("backend_diag/ui", "build"), ("frontend_web", "build"),
                                 ("frontend_avatar", "build"), ("frontend_channels", "build:panel")] * 2)
        self.assertEqual(prepare.call_count, 10)
        modules["backend_diag"].setup.assert_called_with(desktop=False)
        self.assertEqual(modules["frontend_ide/host"].setup_assets.call_count, 2)
        modules["frontend_ide/host"].setup_assets.assert_called_with("npm")
        self.assertEqual(modules["frontend_channels"].install_launcher.call_count, 2)

    def test_browser_environment_skips_electron_binary_but_builds(self):
        run, prepare, _ = self.fixture(desktop=False)
        self.assertEqual(setup.setup_node_refresh(), [])
        prepare.assert_not_called()
        self.assertTrue(any(call.args[0][1] == "run" for call in run.call_args_list))

    def test_failure_stops_before_later_builds_and_launchers(self):
        run, _, modules = self.fixture()
        run.side_effect = lambda command, **kwargs: not (command[1] == "run" and kwargs["cwd"].name == "frontend_web")
        self.assertEqual(setup.setup_node_refresh(), ["Web: ビルド"])
        modules["frontend_avatar"].install_standalone_launcher.assert_not_called()
        modules["frontend_ide/host"].setup_assets.assert_not_called()

    def test_launcher_exception_is_not_reported_as_success(self):
        _, _, modules = self.fixture()
        modules["frontend_channels"].install_launcher.side_effect = OSError("fixture")
        self.assertEqual(setup.setup_node_refresh(), ["Discord: ランチャー"])

    def test_missing_node_stops_without_installation(self):
        with patch.object(setup, "get_node_version", return_value=None), patch.object(setup, "run_command") as run:
            self.assertEqual(setup.setup_node_refresh(), ["Node.js / npm の確認"])
            run.assert_not_called()

    def test_dependency_recovery_keeps_refresh_flags_and_rebuilds(self):
        run = Mock(side_effect=[False, True, True])
        with patch.object(common, "prepare_electron_binary", return_value=True), patch.object(common, "electron_binary_ready", return_value=True):
            self.assertTrue(common.setup_dependencies(ROOT, "npm", "fixture", run, update=False))
        self.assertEqual([call.args[0] for call in run.call_args_list], [
            ["npm", "install", "--include=dev", "--no-fund", "--no-audit"],
            ["npm", "install", "--include=dev", "--no-fund", "--no-audit", "--ignore-scripts"],
            ["npm", "rebuild"],
        ])

    def test_host_assets_use_existing_compile_or_package_and_stop_on_failure(self):
        for cli, success in [(None, True), ("code", True), (None, False)]:
            with self.subTest(cli=cli, success=success), patch.object(host, "find_vscode_cli", return_value=cli), patch.object(host, "run_command", return_value=success) as run, patch.object(host, "install_extensions", return_value=True) as extensions, patch.object(host, "install_standalone_launcher", return_value=True) as launcher, patch.object(host, "setup_dependencies", side_effect=AssertionError("dependencies already synced")):
                self.assertEqual(host.setup_assets("npm"), success)
                self.assertEqual(run.call_args.args[0], ["npm", "run", "package" if cli else "compile"])
                self.assertEqual(launcher.call_count, int(success))
                self.assertEqual(extensions.call_count, int(success and cli is not None))
        # 共通UIのビルドを省略しない既存compile経路を維持する。
        self.assertIn("../../scripts/build.mjs", (ROOT / "frontend_ide/host/scripts/build.mjs").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
