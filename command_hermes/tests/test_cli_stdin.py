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
