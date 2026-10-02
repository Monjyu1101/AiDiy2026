"""Electron の事前取得、npm 失敗時の復旧、セットアップ失敗を確認する。"""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile


SPEC = importlib.util.spec_from_file_location("vscode_setup", Path(__file__).resolve().parents[1] / "_setup.py")
setup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(setup)


class ElectronSetupTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.electron = self.root / "node_modules" / "electron"
        self.electron.mkdir(parents=True)
        (self.electron / "package.json").write_text(json.dumps({"version": "44.5.1"}), encoding="utf-8")
        (self.electron / "install.js").write_text("", encoding="utf-8")
        (self.root / "package.json").write_text("{}", encoding="utf-8")
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))

    def make_ready(self):
        executable = setup.electron_executable_name()
        binary = self.electron / "dist" / executable
        binary.parent.mkdir(parents=True, exist_ok=True)
        binary.write_bytes(b"binary")
        (self.electron / "dist" / "version").write_text("44.5.1", encoding="utf-8")
        (self.electron / "path.txt").write_text(executable, encoding="utf-8")

    def test_existing_binary_requires_matching_version_and_path(self):
        self.make_ready()
        self.assertTrue(setup.electron_binary_ready(self.root))
        (self.electron / "dist" / "version").write_text("44.5.0", encoding="utf-8")
        self.assertFalse(setup.electron_binary_ready(self.root))
        (self.electron / "dist" / "version").write_text("44.5.1", encoding="utf-8")
        (self.electron / "path.txt").unlink()
        self.assertFalse(setup.electron_binary_ready(self.root))

    def test_prepared_binary_needs_no_network_or_installer(self):
        self.make_ready()
        with patch.object(setup, "run_command") as command, patch.object(setup, "install_electron_binary") as download:
            self.assertTrue(setup.prepare_electron_binary(self.root, "test"))
            command.assert_not_called()
            download.assert_not_called()

    def test_installer_runs_even_after_successful_npm_without_postinstall(self):
        with patch.object(setup.shutil, "which", return_value="node"), patch.object(
            setup, "run_command", side_effect=lambda *args, **kwargs: self.make_ready() or True
        ), patch.object(setup, "install_electron_binary") as download:
            self.assertTrue(setup.prepare_electron_binary(self.root, "test"))
            download.assert_not_called()

    def test_failed_installer_falls_back_to_python_download(self):
        with patch.object(setup.shutil, "which", return_value="node"), patch.object(
            setup, "run_command", return_value=False
        ), patch.object(setup, "install_electron_binary", return_value=True) as download:
            self.assertTrue(setup.prepare_electron_binary(self.root, "test"))
            download.assert_called_once_with(self.root, "test")

    def test_python_download_prepares_each_platform(self):
        for platform_name, executable in (
            ("win32", "electron.exe"),
            ("linux", "electron"),
            ("darwin", "Electron.app/Contents/MacOS/Electron"),
        ):
            with self.subTest(platform=platform_name):
                archive = io.BytesIO()
                with zipfile.ZipFile(archive, "w") as zipped:
                    zipped.writestr(executable, b"binary")
                    zipped.writestr("version", "44.5.1")
                response = io.BytesIO(archive.getvalue())
                response.headers = {"Content-Length": str(len(archive.getvalue()))}
                with patch.object(setup.sys, "platform", platform_name), patch.object(
                    setup.platform, "machine", return_value="AMD64"
                ), patch.object(setup.shutil, "which", return_value=None), patch.object(
                    setup.urllib.request, "urlopen", return_value=response
                ) as download:
                    self.assertTrue(setup.install_electron_binary(self.root, "test"))
                    self.assertTrue(setup.electron_binary_ready(self.root))
                    self.assertIn(f"electron-v44.5.1-{platform_name}-x64.zip", download.call_args.args[0])

    def test_download_failure_is_reported_as_setup_failure(self):
        with patch.object(setup.urllib.request, "urlopen", side_effect=OSError("offline")):
            self.assertFalse(setup.install_electron_binary(self.root, "test"))

    def test_npm_recovery_rebuilds_before_compiling(self):
        self.make_ready()
        with patch.object(setup, "FRONTEND_VSCODE_DIR", self.root), patch.object(
            setup, "find_vscode_cli", return_value=None
        ), patch.object(setup.shutil, "which", return_value="npm"), patch.object(
            setup, "run_command", side_effect=[False, True, True, True, True]
        ) as command, patch.object(setup, "install_standalone_launcher", return_value=True):
            self.assertTrue(setup.setup())
            self.assertEqual(
                [["npm", "install"], ["npm", "install", "--ignore-scripts"], ["npm", "update"],
                 ["npm", "rebuild"], ["npm", "run", "compile"]],
                [call.args[0] for call in command.call_args_list],
            )

    def test_electron_failure_does_not_publish_launcher(self):
        with patch.object(setup, "FRONTEND_VSCODE_DIR", self.root), patch.object(
            setup, "find_vscode_cli", return_value=None
        ), patch.object(setup.shutil, "which", return_value="npm"), patch.object(
            setup, "run_command", return_value=True
        ), patch.object(setup, "prepare_electron_binary", return_value=False), patch.object(
            setup, "install_standalone_launcher"
        ) as launcher:
            self.assertFalse(setup.setup())
            launcher.assert_not_called()


if __name__ == "__main__":
    unittest.main()
