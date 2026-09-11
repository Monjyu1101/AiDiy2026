# -*- coding: utf-8 -*-

from contextlib import redirect_stderr
import io
import unittest
from unittest.mock import patch

import command_hermes.cli_main as cli_main


class CliStdinTest(unittest.TestCase):
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
