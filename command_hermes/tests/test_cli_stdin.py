# -*- coding: utf-8 -*-

from contextlib import redirect_stderr, redirect_stdout
import io
import unittest
from unittest.mock import patch

import command_hermes.cli_main as cli_main


class CliStdinTest(unittest.TestCase):
    def test_gemini_cli_is_not_an_external_cli_provider(self):
        self.assertIs(cli_main.provider_entry_is_cli("gemini-cli"), False)
        self.assertNotIn("gemini-cli", cli_main.HermesCLI._aidiy_provider_slugs())
        self.assertEqual([], cli_main._aidiy_cli_build_command("gemini-cli", "質問", True))

    def test_multiline_stdin_is_passed_to_main_unchanged(self):
        prompt = "1行目\n2行目\n"

        with (
            patch.object(cli_main.sys, "stdin", io.StringIO(prompt)),
            patch.object(cli_main, "_load_aidiy_hermes_defaults", return_value={}),
            patch.object(cli_main, "main") as main_mock,
        ):
            result = cli_main.cli_entry(["--oneshot-stdin"])

        self.assertEqual(0, result)
        self.assertEqual(prompt, main_mock.call_args.kwargs["query"])

    def test_oneshot_stdin_enables_quiet_and_oneshot(self):
        with (
            patch.object(cli_main.sys, "stdin", io.StringIO("質問")),
            patch.object(cli_main, "_load_aidiy_hermes_defaults", return_value={}),
            patch.object(cli_main, "main") as main_mock,
        ):
            result = cli_main.cli_entry(["--oneshot-stdin"])

        self.assertEqual(0, result)
        self.assertIs(main_mock.call_args.kwargs["quiet"], True)
        self.assertIs(main_mock.call_args.kwargs["oneshot"], True)

    def test_omitted_model_keeps_native_auto_resolution(self):
        with (
            patch.object(cli_main.sys, "stdin", io.StringIO("質問")),
            patch.object(cli_main, "_load_aidiy_hermes_defaults") as defaults_mock,
            patch.object(cli_main, "_load_aidiy_hermes_provider_defaults") as provider_defaults_mock,
            patch.object(cli_main, "main") as main_mock,
        ):
            result = cli_main.cli_entry(["--oneshot-stdin"])

        self.assertEqual(0, result)
        defaults_mock.assert_not_called()
        provider_defaults_mock.assert_not_called()
        self.assertIsNone(main_mock.call_args.kwargs["model"])
        self.assertIsNone(main_mock.call_args.kwargs["provider"])

    def test_explicit_model_keeps_aidiy_model_routing(self):
        defaults = {
            "provider": "custom",
            "base_url": "https://example.invalid/v1",
            "api_key": "test-key",
            "model": "gemini-explicit",
        }
        with (
            patch.object(cli_main.sys, "stdin", io.StringIO("質問")),
            patch.object(cli_main, "_load_aidiy_hermes_defaults", return_value=defaults) as defaults_mock,
            patch.object(cli_main, "main") as main_mock,
        ):
            result = cli_main.cli_entry([
                "--oneshot-stdin",
                "--model",
                "freeai/gemini-explicit",
            ])

        self.assertEqual(0, result)
        defaults_mock.assert_called_once_with("freeai/gemini-explicit")
        self.assertEqual("gemini-explicit", main_mock.call_args.kwargs["model"])
        self.assertEqual("custom", main_mock.call_args.kwargs["provider"])

    def test_xai_oauth_model_value_routes_to_xai_runtime(self):
        with patch.object(cli_main, "_xai_oauth_is_authenticated", return_value=True):
            defaults = cli_main._load_aidiy_hermes_defaults("xai-oauth/grok-4.6")

        self.assertEqual("xai-oauth", defaults["provider"])
        self.assertEqual("grok-4.6", defaults["model"])

    def test_explicit_xai_oauth_provider_uses_grok_46(self):
        with (
            patch.object(cli_main.sys, "stdin", io.StringIO("質問")),
            patch.object(cli_main, "main") as main_mock,
        ):
            result = cli_main.cli_entry([
                "--oneshot-stdin",
                "--provider",
                "xai-oauth",
                "--model",
                "grok-4.6",
            ])

        self.assertEqual(0, result)
        self.assertEqual("xai-oauth", main_mock.call_args.kwargs["provider"])
        self.assertEqual("grok-4.6", main_mock.call_args.kwargs["model"])

    def test_xai_oauth_picker_entry_includes_grok_46(self):
        cli = cli_main.HermesCLI.__new__(cli_main.HermesCLI)
        cli._aidiy_config = {}

        entry = cli._get_aidiy_provider_entry("xai-oauth", include_models=True)

        self.assertIsNotNone(entry)
        self.assertEqual("xai-oauth", entry["runtime_provider"])
        self.assertEqual("codex_responses", entry["api_mode"])
        self.assertEqual("grok-4.6", entry["default_model"])
        self.assertIn(("grok-4.6", "grok-4.6"), entry["models"])

    def test_grok_oauth_alias_is_not_kept(self):
        from hermes_cli.auth_commands import _normalize_provider
        from hermes_cli.models import normalize_provider as normalize_model_provider
        from hermes_cli.providers import normalize_provider

        for normalizer in (normalize_provider, normalize_model_provider, _normalize_provider):
            with self.subTest(normalizer=normalizer.__module__):
                self.assertEqual("xai-oauth", normalizer("xai-oauth"))
                self.assertEqual("grok-oauth", normalizer("grok-oauth"))

    def test_xai_oauth_picker_selection_uses_runtime_auth(self):
        cli = cli_main.HermesCLI.__new__(cli_main.HermesCLI)
        cli._aidiy_provider_slug = None
        cli._aidiy_config = {}
        cli.provider = "custom"
        cli.requested_provider = "custom"
        cli.model = "old-model"
        cli.api_mode = "chat_completions"
        cli.base_url = "https://example.invalid/v1"
        cli.api_key = "old-key"
        cli._explicit_base_url = cli.base_url
        cli._explicit_api_key = cli.api_key
        cli.agent = None
        cli._active_agent_route_signature = None
        cli._ensure_xai_oauth_auth = unittest.mock.Mock(return_value=False)
        entry = cli._get_aidiy_provider_entry("xai-oauth")

        with patch.object(cli_main, "_cprint"):
            cli._apply_aidiy_provider_model(entry, "grok-4.6")

        self.assertEqual("xai-oauth", cli.provider)
        self.assertEqual("grok-4.6", cli.model)
        self.assertEqual("codex_responses", cli.api_mode)
        self.assertEqual("", cli.base_url)
        self.assertEqual("", cli.api_key)
        cli._ensure_xai_oauth_auth.assert_called_once_with()

    def test_external_cli_auto_uses_provider_without_model_override(self):
        for provider in ("copilot-cli", "codex-cli", "claude-code", "antigravity-cli"):
            with self.subTest(provider=provider):
                with (
                    patch.object(cli_main.sys, "stdin", io.StringIO("質問")),
                    patch.object(cli_main, "_load_aidiy_hermes_provider_defaults") as defaults_mock,
                    patch.object(cli_main, "main") as main_mock,
                ):
                    result = cli_main.cli_entry([
                        "--oneshot-stdin",
                        "--provider",
                        provider,
                        "--model",
                        "auto",
                    ])

                self.assertEqual(0, result)
                defaults_mock.assert_not_called()
                self.assertEqual(provider, main_mock.call_args.kwargs["provider"])
                self.assertIsNone(main_mock.call_args.kwargs["model"])

    def test_external_cli_provider_is_configured_and_resume_is_preserved(self):
        class FakeCli:
            def __init__(self, slug):
                self.slug = slug
                self.applied = None
                self._aidiy_cli_session_started = {}

            def _get_aidiy_provider_entry(self, provider, include_models=False):
                self.test_case.assertEqual(self.slug, provider)
                self.test_case.assertIs(include_models, False)
                return {"slug": provider, "is_cli": True}

            def _apply_aidiy_provider_model(self, entry, model):
                self.applied = (entry, model)

        for provider in ("copilot-cli", "codex-cli", "claude-code", "antigravity-cli"):
            with self.subTest(provider=provider):
                fake = FakeCli(provider)
                fake.test_case = self
                configured = cli_main._configure_aidiy_cli_provider(
                    fake,
                    provider,
                    resumed=True,
                )
                self.assertIs(configured, True)
                self.assertEqual(({"slug": provider, "is_cli": True}, "auto"), fake.applied)
                self.assertIs(fake._aidiy_cli_session_started[provider], True)

    def test_external_cli_quiet_keeps_final_answer_on_stdout(self):
        class FakeCli:
            session_id = "external-session"

            def _dispatch_aidiy_cli_subprocess(self, query, images=None, quiet_output=False):
                self.call = (query, images, quiet_output)
                self._aidiy_cli_last_exit_code = 0
                print("外部CLI進捗")
                return "正式回答"

        fake = FakeCli()
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = cli_main._run_aidiy_cli_quiet(fake, "質問", ["image.png"])

        self.assertEqual(0, exit_code)
        self.assertEqual(("質問", ["image.png"], True), fake.call)
        self.assertEqual("正式回答\n", stdout.getvalue())
        self.assertIn("外部CLI進捗", stderr.getvalue())
        self.assertIn("[done] AI応答完了", stderr.getvalue())
        self.assertIn("session_id: external-session", stderr.getvalue())

    def test_main_quiet_routes_external_provider_without_agent_initialization(self):
        class FakeCli:
            session_id = "main-external-session"
            _aidiy_provider_slug = None
            _aidiy_cli_session_started = {}

            def _get_aidiy_provider_entry(self, provider, include_models=False):
                return {"slug": provider, "is_cli": True}

            def _apply_aidiy_provider_model(self, entry, model):
                self._aidiy_provider_slug = entry["slug"]
                self._aidiy_cli_session_started = {}

            def _claim_active_session(self, source, stderr=False):
                return True

            def _dispatch_aidiy_cli_subprocess(self, query, images=None, quiet_output=False):
                self._aidiy_cli_last_exit_code = 0
                return "統合回答"

        fake = FakeCli()
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            patch.object(cli_main, "HermesCLI", return_value=fake),
            patch.object(cli_main, "_parse_skills_argument", return_value=[]),
            patch.object(cli_main, "_collect_query_images", return_value=("質問", [])),
            patch.object(cli_main, "_finalize_single_query"),
            patch.object(cli_main.atexit, "register"),
            patch("tools.skills_sync.sync_skills"),
            patch("tools.mcp_tool.discover_mcp_tools"),
            patch("agent.coding_context.coding_selection", return_value=[]),
            patch("signal.signal"),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
            self.assertRaises(SystemExit) as raised,
        ):
            cli_main.main(
                query="質問",
                oneshot=True,
                quiet=True,
                provider="copilot-cli",
            )

        self.assertEqual(0, raised.exception.code)
        self.assertEqual("統合回答\n", stdout.getvalue())
        self.assertIn("session_id: main-external-session", stderr.getvalue())

    def test_external_cli_commands_leave_model_selection_to_each_cli(self):
        with patch.object(cli_main, "_aidiy_cli_code_permissions", return_value="none"):
            commands = {
                provider: cli_main._aidiy_cli_build_command(
                    provider,
                    "質問",
                    True,
                    "/repo",
                )
                for provider in ("copilot-cli", "codex-cli", "claude-code", "antigravity-cli")
            }

        for provider, command in commands.items():
            with self.subTest(provider=provider):
                self.assertNotIn("--model", command)
                self.assertNotIn("auto", command)
        self.assertEqual(
            ["copilot", "--silent", "--add-dir", "/repo", "-p", "質問"],
            commands["copilot-cli"],
        )
        self.assertIn(
            "--continue",
            cli_main._aidiy_cli_build_command("copilot-cli", "続き", False, "/repo"),
        )
        self.assertEqual(
            ["codex", "exec", "--skip-git-repo-check", "--dangerously-bypass-approvals-and-sandbox", "質問"],
            commands["codex-cli"],
        )
        self.assertEqual(["claude", "--add-dir", "/repo", "-p", "質問"], commands["claude-code"])
        self.assertIn(
            "--continue",
            cli_main._aidiy_cli_build_command("claude-code", "続き", False, "/repo"),
        )
        self.assertEqual(
            ["agy", "--add-dir", "/repo", "--print-timeout", "20m", "-p", "質問"],
            commands["antigravity-cli"],
        )
        with patch.object(cli_main, "_aidiy_cli_code_permissions", return_value="auto"):
            self.assertEqual(
                ["agy", "--dangerously-skip-permissions", "--add-dir", "/repo",
                 "--print-timeout", "20m", "-p", "続き", "-c"],
                cli_main._aidiy_cli_build_command("antigravity-cli", "続き", False, "/repo"),
            )

    def test_antigravity_cli_prefers_windows_local_install(self):
        expected = cli_main.os.path.join(
            r"C:\Users\tester", "AppData", "Local", "agy", "bin", "agy.exe"
        )
        with (
            patch.object(cli_main.os, "name", "nt"),
            patch.dict(cli_main.os.environ, {"USERPROFILE": r"C:\Users\tester"}),
            patch.object(cli_main.os.path, "isfile", side_effect=lambda path: path == expected),
        ):
            self.assertEqual(expected, cli_main._aidiy_cli_command_path("antigravity-cli"))

    def test_antigravity_cli_detaches_from_windows_console(self):
        class FakeProcess:
            stdout = io.StringIO("回答\n")
            stderr = io.StringIO("")
            returncode = 0

            def poll(self):
                return self.returncode

            def wait(self):
                return self.returncode

            def kill(self):
                self.returncode = -9

        class FakeCli:
            _aidiy_provider_slug = "antigravity-cli"
            conversation_history = []

        with (
            patch.object(cli_main.os, "name", "nt"),
            patch.object(
                cli_main,
                "_aidiy_cli_build_command",
                return_value=["agy.exe", "-p", "質問"],
            ),
            patch("subprocess.DETACHED_PROCESS", 8, create=True),
            patch("subprocess.Popen", return_value=FakeProcess()) as popen_mock,
            redirect_stdout(io.StringIO()),
        ):
            result = cli_main.HermesCLI._dispatch_aidiy_cli_subprocess(
                FakeCli(), "質問", quiet_output=True
            )

        self.assertEqual("回答", result)
        self.assertEqual(8, popen_mock.call_args.kwargs["creationflags"])

    def test_blank_stdin_returns_two_without_calling_main(self):
        stderr = io.StringIO()

        with (
            patch.object(cli_main.sys, "stdin", io.StringIO(" \n\t")),
            patch.object(cli_main, "main") as main_mock,
            redirect_stderr(stderr),
        ):
            result = cli_main.cli_entry(["--oneshot-stdin"])

        self.assertEqual(2, result)
        main_mock.assert_not_called()
        self.assertIn("requires non-empty UTF-8 input", stderr.getvalue())

    def test_existing_oneshot_argument_remains_supported(self):
        with (
            patch.object(cli_main, "_load_aidiy_hermes_defaults", return_value={}),
            patch.object(cli_main, "main") as main_mock,
        ):
            result = cli_main.cli_entry(["-Q", "-z", "手動実行"])

        self.assertEqual(0, result)
        self.assertEqual("手動実行", main_mock.call_args.kwargs["query"])
        self.assertIs(main_mock.call_args.kwargs["oneshot"], True)


if __name__ == "__main__":
    unittest.main()
