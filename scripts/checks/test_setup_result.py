# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026

"""全体セットアップの終了結果を、インストール・通信・設定変更なしで検証する。"""
import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]


def load_setup():
    spec = importlib.util.spec_from_file_location("setup_result_test", ROOT / "_setup.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SetupResultTests(unittest.TestCase):
    @contextlib.contextmanager
    def execution(self, *, continue_on_error=True):
        module = load_setup()
        choices = dict.fromkeys((
            "common", "local", "mcp", "mcp_config", "backend", "taskteam",
            "web", "avatar", "hermes", "ide", "diag", "discord",
        ), True)
        choices.update(continue_on_error=continue_on_error, local_download="no")
        components = {}

        def component(folder):
            if folder not in components:
                components[folder] = Mock()
                for name in ("setup", "setup_desktop", "setup_dependencies", "configure_clients"):
                    getattr(components[folder], name).return_value = True
            return components[folder]

        # 遅延 import と同じ参照先を用意し、Git 初期化も遮断する。
        sys.path.insert(0, str(ROOT))
        try:
            from scripts import local_git_setup
            with contextlib.ExitStack() as stack:
                output = stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
                stack.enter_context(patch.object(module.sys, "argv", [str(ROOT / "_setup.py")]))
                stack.enter_context(patch.object(module, "collect_setup_choices", return_value=choices))
                for name in ("stop_setup_apps", "ensure_prerequisites", "remove_folder_import_caches"):
                    stack.enter_context(patch.object(module, name))
                stack.enter_context(patch.object(module.time, "sleep"))
                stack.enter_context(patch.object(module, "_load_folder_module", side_effect=component))
                stack.enter_context(patch.object(local_git_setup, "ensure_local_git", return_value=("skipped", "fixture")))
                stack.enter_context(patch.object(module, "setup_common_global_tools", return_value=[]))
                stack.enter_context(patch.object(module, "wait_global_cli_tools_install", return_value=[]))
                stack.enter_context(patch.object(module, "run_diag_headless", return_value=True))
                stack.enter_context(patch.object(module, "setup_node_refresh", return_value=[]))
                stack.enter_context(patch.object(module, "setup_launchers_only", return_value=[]))
                # モックの漏れがあれば、実行するのではなくテストを失敗させる。
                for name in ("run", "Popen"):
                    stack.enter_context(patch.object(module.subprocess, name, side_effect=AssertionError("process forbidden")))
                yield module, choices, component, output, local_git_setup
        finally:
            sys.path.remove(str(ROOT))

    def test_success_keeps_zero_exit_and_success_message(self):
        with self.execution() as (module, _, component, output, _git):
            self.assertIsNone(module.main())
            self.assertIn("セットアップは正常終了しました。", output.getvalue())
            component("frontend_channels").setup.assert_called_once()
            module.run_diag_headless.assert_called_once()

    def test_continue_runs_later_stages_but_returns_failure(self):
        for failure in ("Web", "共通", "Git", "Diag: aidiy_diag --headless"):
            with self.subTest(failure=failure), self.execution() as (module, _, component, output, git):
                if failure == "Web":
                    component("frontend_web").setup.return_value = False
                elif failure == "共通":
                    module.setup_common_global_tools.return_value = ["共通: Python"]
                elif failure == "Git":
                    git.ensure_local_git.return_value = ("error", "fixture Git error")
                else:
                    module.run_diag_headless.return_value = False
                with self.assertRaises(SystemExit) as caught:
                    module.main()
                self.assertEqual(caught.exception.code, 1)
                self.assertIn(failure, output.getvalue())
                self.assertIn("セットアップに失敗した項目があります。", output.getvalue())
                self.assertNotIn("セットアップは正常終了しました。", output.getvalue())
                component("frontend_channels").setup.assert_called_once()
                module.run_diag_headless.assert_called_once()

    def test_all_failed_stages_are_preserved_in_summary(self):
        with self.execution() as (module, _, component, output, _git):
            component("frontend_web").setup.return_value = False
            component("frontend_channels").setup.return_value = False
            module.run_diag_headless.return_value = False
            with self.assertRaises(SystemExit) as caught:
                module.main()
            self.assertEqual(caught.exception.code, 1)
            for label in ("  - Web", "  - Discord", "  - Diag: aidiy_diag --headless"):
                self.assertIn(label, output.getvalue())

    def test_fail_fast_stops_before_later_stage(self):
        with self.execution(continue_on_error=False) as (module, _, component, output, _git):
            component("frontend_web").setup.return_value = False
            with self.assertRaises(SystemExit) as caught:
                module.main()
            self.assertEqual(caught.exception.code, 1)
            component("frontend_avatar").setup.assert_not_called()
            module.run_diag_headless.assert_not_called()
            self.assertNotIn("セットアップは正常終了しました。", output.getvalue())

    def test_common_fail_fast_also_waits_for_already_started_cli(self):
        for failure in ("common", "cli"):
            with self.subTest(failure=failure), self.execution(continue_on_error=False) as (module, _, component, _output, _git):
                module.GLOBAL_CLI_INSTALL_PROCESSES = [object()]
                if failure == "common":
                    module.setup_common_global_tools.return_value = ["共通: Python"]
                else:
                    module.wait_global_cli_tools_install.return_value = ["fixture-cli"]
                with self.assertRaises(SystemExit) as caught:
                    module.main()
                self.assertEqual(caught.exception.code, 1)
                module.wait_global_cli_tools_install.assert_called_once()
                component("backend_diag").setup.assert_not_called()
                module.run_diag_headless.assert_not_called()

    def test_build_and_launcher_modes_keep_failure_exit(self):
        for mode in ("node_refresh", "launchers"):
            for failed in (False, True):
                with self.subTest(mode=mode, failed=failed), self.execution() as (module, choices, _component, output, _git):
                    errors = ["fixture failure"] if failed else []
                    if mode == "node_refresh":
                        choices["node_refresh"] = True
                        module.setup_node_refresh.return_value = errors
                    else:
                        module.sys.argv.append("--launchers-only")
                        module.setup_launchers_only.return_value = errors
                    if failed or mode == "launchers":
                        with self.assertRaises(SystemExit) as caught:
                            module.main()
                        self.assertEqual(caught.exception.code, int(failed))
                    else:
                        self.assertIsNone(module.main())
                    module.run_diag_headless.assert_not_called()
                    if failed:
                        self.assertIn("fixture failure", output.getvalue())
                        self.assertNotIn("セットアップは正常終了しました。", output.getvalue())


if __name__ == "__main__":
    unittest.main()
