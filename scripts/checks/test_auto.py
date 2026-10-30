"""単一batの静的構造・対象選択モデル・実Git契約試験。Windows CMDの実行試験ではない。"""
from pathlib import Path
import re
import shlex
import subprocess
import sys
import os
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
BAT = ROOT / "_auto.bat"
TEXT = BAT.read_bytes().decode("cp932").replace("\r\n", "\n")


class BatchStructureTests(unittest.TestCase):
    def test_cp932_crlf_no_bom_and_japanese_ui(self):
        data = BAT.read_bytes()
        self.assertEqual(data.decode('cp932').encode('cp932'), data)
        self.assertIn('aidiyセットアップと実行しますか？ [y]/n:', TEXT)
        self.assertIn('chcp 932 >nul', TEXT)
        self.assertNotIn('chcp 65001', TEXT)
        self.assertFalse(data.startswith(b"\xef\xbb\xbf"))
        self.assertNotIn(b"\n", data.replace(b"\r\n", b""))
        self.assertNotIn(b"\x1a", data)
        self.assertNotIn(b"\x00", data)

    def test_nonascii_source_is_only_ui_not_control_flow(self):
        for line in TEXT.splitlines():
            if not line.isascii():
                self.assertRegex(line, r'^(echo |set /p |if .+ echo )')

    def test_labels_and_calls_resolve(self):
        labels = re.findall(r"^:([a-z_]+)$", TEXT, re.M)
        self.assertEqual(len(labels), len(set(labels)))
        for label in re.findall(r"\bgoto\s+([a-z_]+)", TEXT, re.I):
            self.assertIn(label.lower(), labels)
        for label in re.findall(r"\bcall\s+:([a-z_]+)", TEXT, re.I):
            self.assertIn(label.lower(), labels)

    def test_single_file_no_companion_or_embedded_program(self):
        self.assertNotIn("_auto.py", TEXT)
        self.assertNotIn("runpy", TEXT)
        self.assertFalse((ROOT / "_auto.py").exists())
        self.assertFalse((ROOT / "_automatic.bat").exists())
        self.assertNotIn('_automatic.bat', TEXT)

    def test_original_locations_saved_before_control_transfer(self):
        transfer = TEXT.index('"%AIDIY_TEMP%\\_auto.bat" --_aidiy_temp')
        self.assertLess(TEXT.index('set "AIDIY_CWD=%CD%"'), transfer)
        self.assertLess(TEXT.index('set "AIDIY_SOURCE_DIR=%~dp0."'), transfer)
        self.assertNotRegex(TEXT, r"(?im)^\s*call\s+[^:]")
        self.assertIn("DisableDelayedExpansion", TEXT)

    def test_temp_directory_is_unique_and_atomic(self):
        self.assertIn('%RANDOM%-%RANDOM%-%RANDOM%', TEXT)
        self.assertIn('mkdir "%AIDIY_TEMP%"', TEXT)
        self.assertIn('if errorlevel 1 goto make_temp', TEXT)
        self.assertIn('if /i not "%~dp0"=="%AIDIY_TEMP%\\" goto temp_error', TEXT)

    def test_no_destructive_reset_clean_stash_or_mcp_deletion(self):
        self.assertNotRegex(TEXT.lower(), r"git\s+(reset|clean|stash)\b")
        self.assertNotIn('mcp.json', TEXT)
        self.assertNotIn('chatLanguageModels.json', TEXT)
        self.assertNotRegex(TEXT.lower(), r"\b(rd|rmdir|del)\s+/s\b")

    def test_git_redirect_environment_is_rejected_not_created(self):
        for name in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_COMMON_DIR', 'GIT_INDEX_FILE', 'GIT_OBJECT_DIRECTORY'):
            self.assertIn(f'if defined {name} goto failed', TEXT)
            self.assertNotIn(f'set "{name}=', TEXT)

    def test_origin_allowlist_never_expanded_as_command_text(self):
        self.assertNotIn('%ORIGIN_URL%', TEXT)
        validator = TEXT[TEXT.index('\n:validate_repository\n'):TEXT.index('\n:backup_local_state\n')]
        self.assertNotIn('findstr', validator.lower())
        self.assertNotIn('%%~zF', validator)
        self.assertIn('all(url.lower() in allowed for url in urls)', validator)
        self.assertIn('git remote get-url --all origin', TEXT)

    def test_repository_checks_report_each_guard_without_disclosing_origin(self):
        validator = TEXT[TEXT.index('\n:validate_repository\n'):TEXT.index('\n:backup_local_state\n')]
        for name in ('directory', 'files', 'root', 'origin', 'branch', 'gitdir', 'operation', 'unmerged'):
            self.assertIn(f'set "STAGE=repository_{name}"', validator)
        for line in validator.splitlines():
            if line.startswith('git '):
                self.assertIn('2>"%AIDIY_TEMP%\\validation.txt"', line)
        failed = validator[validator.index('\n:repository_failed\n'):]
        self.assertIn('REPOSITORY_CHECK_FAILED %STAGE%', failed)
        self.assertIn('type "%AIDIY_TEMP%\\validation.txt" >>"%LOG%"', failed)
        self.assertIn('exit /b 3', failed)
        self.assertNotIn('type "%AIDIY_TEMP%\\origin.txt"', TEXT)
        self.assertIn('if exist "%CONTROL%\\" goto control_ready', TEXT)
        main = TEXT[TEXT.index('\n:existing\n'):TEXT.index('\n:setup\n')]
        self.assertIn('call :validate_repository\nif errorlevel 1 goto failed', main)
        self.assertLess(main.index('call :validate_repository'), main.index('call :backup_local_state'))
        self.assertLess(main.index('call :validate_repository'), main.index('git fetch '))

    def test_git_failure_is_not_overwritten_by_following_python_probe(self):
        validator = TEXT[TEXT.index('\n:validate_repository\n'):TEXT.index('\n:repository_failed\n')]
        lines = validator.splitlines()
        for i, line in enumerate(lines):
            if line.startswith('git '):
                self.assertEqual(lines[i + 1], 'if errorlevel 1 goto repository_failed')
        self.assertIn(':repository_failed\nset "VALIDATION_RC=%ERRORLEVEL%"', TEXT)

    def test_clone_publish_uses_rename_not_move_into_existing_target(self):
        self.assertIn('ren "%STAGING%" "AiDiy2026"', TEXT)
        self.assertNotRegex(TEXT, r"(?im)^move\b")
        self.assertNotIn('rd "%STAGING%"', TEXT)

    def test_backup_is_required_before_fetch_and_setup(self):
        self.assertLess(TEXT.index('call :backup_local_state'), TEXT.index('git fetch '))
        self.assertIn('call :backup_local_state\nset "RC=%ERRORLEVEL%"\nif not "%RC%"=="0" goto failed', TEXT)
        self.assertNotIn('robocopy', TEXT.lower())
        self.assertIn('shutil.copytree(src,', TEXT)
        self.assertIn('if errorlevel 1 goto config_backup_failed', TEXT)
        failed = TEXT[TEXT.index('\n:config_backup_failed\n'):TEXT.index('\n:backup_file\n')]
        self.assertIn('type "%AIDIY_TEMP%\\backup.txt" >>"%LOG%"', failed)
        self.assertTrue(failed.rstrip().endswith('exit /b 1'))
        self.assertIn('git diff --cached --binary', TEXT)
        self.assertIn('call :backup_file', TEXT)

    def test_interactive_setup_start_and_error_propagation(self):
        block = TEXT[TEXT.index('\n:setup\n'):TEXT.index('\n:validate_repository\n')]
        for script in ('_setup.py', '_start.py'):
            self.assertIn(f'"%PYTHON%" -X utf8 -u {script}\nset "RC=%ERRORLEVEL%"', block)
        self.assertLess(block.index('_setup.py'), block.index('_start.py'))
        self.assertIn('if not "%RC%"=="0" goto failed', block)
        self.assertNotRegex(block, r"(?m)^.*(?:_setup|_start)\.py.*[<>|]")
        self.assertNotIn('再セットアップ', TEXT)
        self.assertNotIn('setup-state', TEXT)

    def test_setup_start_restore_codepage_after_saving_exit_status(self):
        for script in ('_setup.py', '_start.py'):
            start = TEXT.index(f'"%PYTHON%" -X utf8 -u {script}\n')
            lines = TEXT[start:].splitlines()
            self.assertEqual(lines[1], 'set "RC=%ERRORLEVEL%"')
            self.assertEqual(lines[3], 'chcp 932 >nul')
            self.assertTrue(lines[4].startswith('if errorlevel 1 '))
            self.assertIn('exit /b 2', lines[4])
            self.assertTrue(all(line.isascii() for line in lines[:5]))

    def test_cleanup_does_not_remove_unknown_files_or_original(self):
        cleanup = TEXT[TEXT.index(':clean_temp\n'):TEXT.index(':log_error\n')]
        self.assertNotIn('/s', cleanup.lower())
        self.assertNotIn('%AIDIY_SOURCE%', cleanup)
        self.assertIn('exit /b %RC%', cleanup)

    def test_cleanup_keeps_executing_batch_and_restores_caller_before_pause(self):
        cleanup = TEXT[TEXT.index('\n:finish\n'):TEXT.index('\n:log_error\n')]
        self.assertNotIn('del /q "%~f0"', cleanup)
        self.assertNotIn('rd "%AIDIY_TEMP%"', cleanup)
        self.assertIn('TEMP_COPY_RETAINED=', cleanup)
        self.assertIn('do if exist "%AIDIY_TEMP%\\%%F" del', cleanup)
        self.assertLess(cleanup.index('cd /d "%AIDIY_CWD%"'), cleanup.index(' pause'))
        self.assertTrue(cleanup.rstrip().endswith('pause\nexit /b %RC%'))
        self.assertNotRegex(cleanup, r'(?im)^endlocal\b')

    def test_required_checks_identify_failure_and_preserve_diagnostics(self):
        for name in ('git', 'python'):
            self.assertIn(f'set "STAGE=prerequisite_{name}"', TEXT)
        block = TEXT[TEXT.index('\n:prerequisite_failed\n'):TEXT.index('\n:validate_repository\n')]
        self.assertIn('REQUIRED_CHECK_FAILED %STAGE%', block)
        self.assertIn('type "%AIDIY_TEMP%\\probe.txt"', block)
        self.assertIn('set "RC=2"', block)
        self.assertIn('goto failed', block)

    def test_optional_tools_cannot_block_initial_setup(self):
        block = TEXT[TEXT.index('set "STAGE=check_node"'):TEXT.index('set "STAGE=git_environment"')]
        for name in ('node', 'npm', 'uv'):
            self.assertIn(f'set "STAGE=check_{name}"', block)
        self.assertEqual(block.count('set "CHECK_RC=%ERRORLEVEL%"'), 3)
        self.assertEqual(block.count('call :report_optional_check'), 3)
        self.assertNotIn('goto failed', block)
        self.assertNotIn('goto prerequisite_failed', block)
        report = TEXT[TEXT.index('\n:report_optional_check\n'):TEXT.index('\n:prerequisite_failed\n')]
        self.assertIn('exit /b 0', report)

    def test_npm_cmd_is_isolated_in_child_cmd_not_chained(self):
        self.assertIn('"%ComSpec%" /d /c npm --version', TEXT)
        self.assertNotRegex(TEXT, r'(?m)^npm(?:\.cmd)?\s')

    def test_python_path_encoding_matches_cp932_and_does_not_enforce_version(self):
        probes = [line for line in TEXT.splitlines() if 'sys.stdout.buffer.write' in line]
        self.assertEqual(len(probes), 2)
        for line in probes:
            self.assertIn('-X utf8 -c', line)
            self.assertIn("sys.executable.encode('cp932')", line)
            self.assertNotIn('sys.version_info', line)
            self.assertIn('2>"%AIDIY_TEMP%\\probe.txt"', line)
        self.assertIn('chcp 932 >nul\nif errorlevel 1 goto temp_error', TEXT)

    def test_actual_python_probe_returns_zero_and_cp932_japanese_path(self):
        line = next(line for line in TEXT.splitlines() if 'sys.stdout.buffer.write' in line)
        code = re.search(r'-c "([^"]+)"', line).group(1)
        compile(code, '<batch Python probe>', 'exec')
        with tempfile.TemporaryDirectory(prefix='python probe 日本語 ') as folder:
            executable = Path(folder) / 'python'
            executable.symlink_to(sys.executable)
            result = subprocess.run([str(executable), '-X', 'utf8', '-c', code],
                                    capture_output=True, env={**os.environ, 'PYTHONIOENCODING': 'ascii'})
            self.assertEqual(result.returncode, 0)
            self.assertEqual(Path(result.stdout.decode('cp932').strip()), executable)
            self.assertTrue(result.stderr.decode('ascii').startswith('Python '))

    def test_python_310_version_check_routes_only_to_warning(self):
        line = next(line for line in TEXT.splitlines() if 'sys.version_info >=' in line)
        code = re.search(r'-c "([^"]+)"', line).group(1)
        result = subprocess.run([sys.executable, '-c', 'import sys;sys.version_info=(3,10,11);' + code], capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn(line + '\nif errorlevel 1 call :python_version_warning', TEXT)
        warning = TEXT[TEXT.index('\n:python_version_warning\n'):TEXT.index('\n:convert_git_path_text\n')]
        self.assertIn('exit /b 0', warning)
        self.assertNotIn('goto failed', warning)

    def test_git_path_lists_are_converted_before_cmd_reads_them(self):
        for filename in ('gitdir.txt', 'untracked.txt'):
            marker = f'set "AIDIY_TEXT_FILE=%AIDIY_TEMP%\\{filename}"\ncall :convert_git_path_text\nif errorlevel 1 exit /b '
            self.assertIn(marker, TEXT)

    def test_git_path_conversion_preserves_japanese_and_rejects_loss(self):
        line = next(line for line in TEXT.splitlines() if "os.environ['AIDIY_TEXT_FILE']" in line)
        code = re.search(r'-c "([^"]+)"', line).group(1)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'paths.txt'
            for text, expected in [('C:/利用者/日本語 path!100%/file.txt\n', 0), ('emoji😀.txt\n', 1), ('wave〜.txt\n', 3)]:
                original = text.encode('utf-8')
                path.write_bytes(original)
                result = subprocess.run([sys.executable, '-X', 'utf8', '-c', code], capture_output=True,
                                        env={**os.environ, 'AIDIY_TEXT_FILE': str(path)})
                self.assertEqual(result.returncode, expected)
                if expected == 0:
                    self.assertEqual(path.read_bytes().decode('cp932'), text)
                else:
                    self.assertEqual(path.read_bytes(), original)


class RepositoryValidationTests(unittest.TestCase):
    """実batの短いPython検証を実行。CMD/FINDSTRの実行結果を模倣しない。"""
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='repo validation 日本語 & % ! ')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.gitdir = self.root / 'Git 管理'
        self.gitdir.mkdir()

    def run_guard(self, name):
        block = TEXT.split(f'set "STAGE=repository_{name}"', 1)[1]
        line = next(line for line in block.splitlines() if line.startswith('"%PYTHON%"'))
        code = re.search(r'-c "([^"]+)"', line).group(1)
        return subprocess.run([sys.executable, '-X', 'utf8', '-c', code],
                              cwd=self.root, capture_output=True,
                              env={**os.environ, 'AIDIY_TEMP': str(self.root),
                                   'AIDIY_GIT_DIR': str(self.gitdir)})

    def test_root_accepts_lf_crlf_and_empty_only(self):
        for raw, valid in [(b'\n', True), (b'\r\n', True), (b'', True),
                           (b'a\n', False), (b'a\r\n', False), (b' \n', False)]:
            with self.subTest(raw=raw):
                (self.root / 'prefix.txt').write_bytes(raw)
                self.assertEqual(self.run_guard('root').returncode == 0, valid)

    def test_origin_allowlist_accepts_git_lf_and_crlf(self):
        allowed = ['https://github.com/Monjyu1101/AiDiy2026.git',
                   'https://github.com/Monjyu1101/AiDiy2026',
                   'git@github.com:Monjyu1101/AiDiy2026.git',
                   'git@github.com:Monjyu1101/AiDiy2026']
        for newline in ('\n', '\r\n'):
            for url in allowed + [allowed[0].upper(), newline.join(allowed)]:
                with self.subTest(newline=newline, url=url):
                    (self.root / 'origin.txt').write_bytes((url + newline).encode())
                    self.assertEqual(self.run_guard('origin').returncode, 0)

    def test_origin_rejects_empty_other_mixed_and_command_text_privately(self):
        valid = 'https://github.com/Monjyu1101/AiDiy2026.git'
        secret = 'fixture-secret-token'
        for value in ['', '\n', valid + '/wrong\n', valid + '\nhttps://other.invalid/repo\n',
                      f'https://{secret}@github.com/Monjyu1101/AiDiy2026.git\n',
                      valid + '& echo injected\n', ' ' + valid + '\n']:
            with self.subTest(value=value):
                (self.root / 'origin.txt').write_bytes(value.encode())
                result = self.run_guard('origin')
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(b'Origin must be', result.stderr)
                self.assertNotIn(secret.encode(), result.stderr + result.stdout)
                self.assertNotIn(b'injected', result.stderr + result.stdout)

    def test_branch_accepts_only_main_with_normal_line_endings(self):
        for raw, valid in [(b'main\n', True), (b'main\r\n', True), (b'main', True),
                           (b'', False), (b'develop\n', False), (b'Main\n', False),
                           (b'main\nother\n', False), (b'main \n', False)]:
            with self.subTest(raw=raw):
                (self.root / 'branch.txt').write_bytes(raw)
                self.assertEqual(self.run_guard('branch').returncode == 0, valid)

    def test_files_guard_requires_real_setup_start_files_and_dotgit(self):
        self.assertNotEqual(self.run_guard('files').returncode, 0)
        (self.root / '.git').write_text('gitdir: fixture')
        (self.root / '_setup.py').write_text('# fixture')
        (self.root / '_start.py').mkdir()
        self.assertNotEqual(self.run_guard('files').returncode, 0)
        (self.root / '_start.py').rmdir()
        (self.root / '_start.py').write_text('# fixture')
        self.assertEqual(self.run_guard('files').returncode, 0)

    def test_gitdir_requires_one_existing_path_with_lf_or_crlf(self):
        for suffix in ('\n', '\r\n'):
            (self.root / 'gitdir.txt').write_bytes((str(self.gitdir) + suffix).encode())
            self.assertEqual(self.run_guard('gitdir').returncode, 0)
        for value in ['', str(self.root / 'absent') + '\n', str(self.gitdir) + '\nextra\n']:
            (self.root / 'gitdir.txt').write_bytes(value.encode())
            self.assertNotEqual(self.run_guard('gitdir').returncode, 0)

    def test_incomplete_operation_and_unmerged_index_are_rejected(self):
        self.assertEqual(self.run_guard('operation').returncode, 0)
        for name in ('MERGE_HEAD', 'CHERRY_PICK_HEAD', 'REVERT_HEAD', 'rebase-merge', 'rebase-apply'):
            marker = self.gitdir / name
            marker.write_text('fixture')
            result = self.run_guard('operation')
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(name.encode(), result.stderr)
            marker.unlink()
        (self.root / 'unmerged.txt').write_bytes(b'')
        self.assertEqual(self.run_guard('unmerged').returncode, 0)
        (self.root / 'unmerged.txt').write_bytes(b'100644 sha 1\tfile\n')
        self.assertNotEqual(self.run_guard('unmerged').returncode, 0)

    def test_all_inline_validators_support_python_310_syntax(self):
        import ast
        for line in TEXT.splitlines():
            if ' -c "' in line:
                code = re.search(r'-c "([^"]+)"', line).group(1)
                ast.parse(code, feature_version=(3, 10))


class ConfigurationBackupTests(unittest.TestCase):
    """bat内のPythonそのものを一時fixtureで実行。Windows CMD試験ではない。"""
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='backup 日本語 & % ! ')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.backup = self.root / '退避先 (copy)'
        self.backup.mkdir()
        line = next(line for line in TEXT.splitlines() if 'shutil.copytree(src,' in line)
        self.code = re.search(r'-c "([^"]+)"', line).group(1)
        compile(self.code, '<batch configuration backup>', 'exec')

    def run_backup(self, prefix=''):
        return subprocess.run([sys.executable, '-X', 'utf8', '-c', prefix + self.code],
                              cwd=self.root, capture_output=True,
                              env={**os.environ, 'BACKUP': str(self.backup)})

    def test_missing_configuration_is_success_without_copying_other_data(self):
        (self.root / '_data').mkdir()
        (self.root / '_data/private').write_bytes(b'do not copy')
        self.assertEqual(self.run_backup().returncode, 0)
        self.assertEqual(list(self.backup.iterdir()), [])

    def test_nested_binary_empty_and_read_only_files_are_preserved(self):
        config = self.root / '_config'
        nested = config / '日本語 空白 & % ! (nested)'
        nested.mkdir(parents=True)
        (nested / 'empty').mkdir()
        content = bytes(range(256))
        source = nested / 'configuration.bin'
        source.write_bytes(content)
        source.chmod(0o444)
        os.utime(source, (1700000000, 1700000000))
        result = self.run_backup()
        self.assertEqual(result.returncode, 0, result.stderr.decode('cp932'))
        copied = self.backup / source.relative_to(self.root)
        self.assertEqual(source.read_bytes(), content)
        self.assertEqual(copied.read_bytes(), content)
        self.assertEqual(copied.stat().st_mtime_ns, source.stat().st_mtime_ns)
        self.assertTrue((copied.parent / 'empty').is_dir())

    def test_existing_destination_is_not_merged_or_overwritten(self):
        (self.root / '_config').mkdir()
        (self.root / '_config/key.txt').write_text('original')
        (self.backup / '_config').mkdir()
        (self.backup / '_config/key.txt').write_text('previous backup')
        self.assertNotEqual(self.run_backup().returncode, 0)
        self.assertEqual((self.backup / '_config/key.txt').read_text(), 'previous backup')
        self.assertEqual((self.root / '_config/key.txt').read_text(), 'original')

    def test_root_nested_and_broken_links_fail_without_traversal(self):
        outside = self.root / 'outside'
        outside.mkdir()
        (outside / 'private').write_text('keep original')
        config = self.root / '_config'
        for kind in ('root', 'directory', 'file', 'broken'):
            with self.subTest(kind=kind):
                if kind == 'root':
                    link = config
                    target = outside
                else:
                    config.mkdir(exist_ok=True)
                    link = config / 'link'
                    target = outside if kind == 'directory' else outside / ('missing' if kind == 'broken' else 'private')
                try:
                    link.symlink_to(target, target_is_directory=kind in ('root', 'directory'))
                except OSError:
                    self.skipTest('symlink creation unavailable')
                try:
                    result = self.run_backup()
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(b'links/reparse points', result.stderr)
                    self.assertFalse((self.backup / '_config').exists())
                    self.assertEqual((outside / 'private').read_text(), 'keep original')
                finally:
                    link.unlink()

    def test_windows_reparse_attribute_is_rejected_without_requiring_new_python_api(self):
        (self.root / '_config/junction').mkdir(parents=True)
        prefix = "from unittest.mock import patch;from types import SimpleNamespace;from pathlib import Path;old=Path.lstat;fake=lambda p,*a,**k:SimpleNamespace(st_mode=old(p,*a,**k).st_mode,st_file_attributes=1024) if p.name=='junction' else old(p,*a,**k);patcher=patch.object(Path,'lstat',fake);patcher.start();"
        result = self.run_backup(prefix)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b'links/reparse points', result.stderr)
        self.assertFalse((self.backup / '_config').exists())
        self.assertNotIn('is_junction', self.code)

    def test_copy_failure_is_nonzero_and_does_not_remove_original_or_partial_backup(self):
        (self.root / '_config').mkdir()
        (self.root / '_config/key.txt').write_text('original')
        prefix = "from unittest.mock import patch;import shutil;patcher=patch.object(shutil,'copytree',side_effect=PermissionError('fixture copy failure'));patcher.start();"
        result = self.run_backup(prefix)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b'fixture copy failure', result.stderr)
        self.assertEqual((self.root / '_config/key.txt').read_text(), 'original')
        self.assertTrue(self.backup.is_dir())


class RoutingModelTests(unittest.TestCase):
    """実batの3本の選択文を読み、ディレクトリ有無だけmockする。"""
    def route(self, cwd_has=False, source_has=False):
        lines = [line for line in TEXT.splitlines() if 'set "TARGET=' in line]
        env = {'USERPROFILE': '利用者 home', 'AIDIY_CWD': '起動 cwd', 'AIDIY_SOURCE_DIR': 'script 配置'}
        exists = {'%AIDIY_CWD%': cwd_has, '%AIDIY_SOURCE_DIR%': source_has}
        target = None
        for line in lines:
            if line.startswith('if exist'):
                condition = re.search(r'"(%\w+%)\\backend_server\\"', line).group(1)
                if not exists[condition]:
                    continue
            value = re.search(r'set "TARGET=([^"]+)"', line).group(1)
            target = re.sub(r'%(\w+)%', lambda m: env[m.group(1)], value)
        return target

    def test_desktop_copy_uses_userprofile(self):
        self.assertEqual(self.route(), '利用者 home\\AiDiy2026')

    def test_shortcut_empty_working_directory_uses_source_repo(self):
        self.assertEqual(self.route(source_has=True), 'script 配置')

    def test_explicit_cwd_checkout_wins(self):
        self.assertEqual(self.route(cwd_has=True, source_has=True), '起動 cwd')

    def test_explicit_cwd_without_source_checkout(self):
        self.assertEqual(self.route(cwd_has=True), '起動 cwd')


class GitContractTests(unittest.TestCase):
    """batと同じGitコマンドをローカル一時repoへ実行。外部通信/実setup/GUIなし。"""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='AiDiy mock 日本語 ')
        self.base = Path(self.tmp.name)
        self.remote = self.base / 'remote.git'
        self.seed = self.base / 'seed'
        self.repo = self.base / '利用者 home' / 'AiDiy2026'
        self.git(self.base, 'init', '--bare', str(self.remote))
        self.git(self.base, 'init', '-b', 'main', str(self.seed))
        self.git(self.seed, 'config', 'user.name', 'Fixture')
        self.git(self.seed, 'config', 'user.email', 'fixture@example.invalid')
        (self.seed / 'local.txt').write_text('base\n')
        (self.seed / '.gitignore').write_text('_config/\n_data/\n')
        self.commit()
        self.git(self.seed, 'remote', 'add', 'origin', str(self.remote))
        self.git(self.seed, 'push', '-u', 'origin', 'main')
        self.repo.parent.mkdir()
        self.git(self.base, 'clone', '--branch', 'main', str(self.remote), str(self.repo))

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, repo, *args, check=True):
        return subprocess.run(['git', '-C', str(repo), *args], capture_output=True, check=check)

    def commit(self):
        self.git(self.seed, 'add', '.')
        self.git(self.seed, 'commit', '-m', 'fixture')

    def advance(self, name='remote.txt'):
        (self.seed / name).write_text('remote\n')
        self.commit()
        self.git(self.seed, 'push', 'origin', 'main')

    def update(self):
        self.git(self.repo, 'fetch', '--no-tags', 'origin', 'main')
        result = self.git(self.repo, 'merge-base', '--is-ancestor', 'HEAD', 'FETCH_HEAD', check=False)
        if result.returncode:
            return result
        merge = next(line for line in TEXT.splitlines() if line.startswith('git merge --'))
        return self.git(self.repo, *shlex.split(merge)[1:], check=False)

    def test_no_update_is_success(self):
        self.assertEqual(self.update().returncode, 0)

    def test_fast_forward_reaches_remote(self):
        self.advance()
        self.assertEqual(self.update().returncode, 0)
        self.assertEqual(self.git(self.repo, 'rev-parse', 'HEAD').stdout, self.git(self.seed, 'rev-parse', 'HEAD').stdout)

    def test_nonconflicting_unsaved_and_untracked_survive(self):
        (self.repo / 'local.txt').write_text('unsaved\n')
        (self.repo / '未追跡.txt').write_text('keep')
        self.advance()
        self.assertEqual(self.update().returncode, 0)
        self.assertEqual((self.repo / 'local.txt').read_text(), 'unsaved\n')
        self.assertEqual((self.repo / '未追跡.txt').read_text(), 'keep')

    def test_conflicting_unsaved_stops_without_autostash(self):
        self.git(self.repo, 'config', 'merge.autoStash', 'true')
        (self.repo / 'local.txt').write_text('unsaved\n')
        before = self.git(self.repo, 'rev-parse', 'HEAD').stdout
        self.advance('local.txt')
        self.assertNotEqual(self.update().returncode, 0)
        self.assertEqual(self.git(self.repo, 'rev-parse', 'HEAD').stdout, before)
        self.assertEqual((self.repo / 'local.txt').read_text(), 'unsaved\n')
        self.assertEqual(self.git(self.repo, 'stash', 'list').stdout, b'')

    def test_untracked_overlap_stops(self):
        (self.repo / 'remote.txt').write_text('local private')
        self.advance()
        self.assertNotEqual(self.update().returncode, 0)
        self.assertEqual((self.repo / 'remote.txt').read_text(), 'local private')

    def test_ignored_overlap_stops(self):
        for repo in (self.repo, self.seed):
            (repo / '_data').mkdir()
        (self.repo / '_data' / 'db').write_text('local private')
        (self.seed / '_data' / 'db').write_text('remote')
        self.git(self.seed, 'add', '--force', '_data/db')
        self.git(self.seed, 'commit', '-m', 'track data')
        self.git(self.seed, 'push', 'origin', 'main')
        self.assertNotEqual(self.update().returncode, 0)
        self.assertEqual((self.repo / '_data' / 'db').read_text(), 'local private')

    def test_local_commit_stops_without_reset(self):
        self.git(self.repo, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '--allow-empty', '-m', 'local')
        before = self.git(self.repo, 'rev-parse', 'HEAD').stdout
        self.assertNotEqual(self.update().returncode, 0)
        self.assertEqual(self.git(self.repo, 'rev-parse', 'HEAD').stdout, before)

    def test_binary_backup_command_contains_unsaved_work(self):
        (self.repo / 'local.txt').write_text('unsaved\n')
        line = next(line for line in TEXT.splitlines() if line.startswith('git diff --binary'))
        command = shlex.split(line.split('>')[0])[1:]
        self.assertIn(b'+unsaved', self.git(self.repo, *command).stdout)

    @unittest.skipUnless(os.name == 'nt', 'Windows CMD unavailable; no Windows execution claim')
    def test_real_cmd_repository_validator_success_and_failures(self):
        """Windowsでは実bat subroutineのみ実行。fetch/setup/startは含めない。"""
        for name in ('_setup.py', '_start.py'):
            (self.repo / name).write_text('# fixture', encoding='utf-8')
        temporary = self.base / '診断 temp'
        temporary.mkdir()
        log = temporary / 'validation.log'
        script = temporary / 'validator.bat'
        validator = TEXT[TEXT.index('\n:validate_repository\n'):TEXT.index('\n:control_failed\n')]
        conversion = TEXT[TEXT.index('\n:convert_git_path_text\n'):TEXT.index('\n:report_optional_check\n')]
        harness = ('@echo off\nsetlocal EnableExtensions DisableDelayedExpansion\n'
                   'chcp 932 >nul\ncall :validate_repository\nexit /b %ERRORLEVEL%\n')
        script.write_bytes((harness + validator + conversion).replace('\n', '\r\n').encode('cp932'))
        env = {**os.environ, 'TARGET': str(self.repo), 'AIDIY_TEMP': str(temporary),
               'PYTHON': sys.executable, 'LOG': str(log)}

        def run():
            return subprocess.run([os.environ['ComSpec'], '/d', '/c', str(script)],
                                  capture_output=True, env=env)

        self.git(self.repo, 'remote', 'set-url', 'origin', 'https://github.com/Monjyu1101/AiDiy2026.git')
        result = run()
        self.assertEqual(result.returncode, 0, result.stdout.decode('cp932', errors='replace'))
        self.git(self.repo, 'checkout', '-b', 'not-main')
        self.assertEqual(run().returncode, 3)
        self.assertIn('repository_branch', log.read_text(encoding='cp932'))
        self.git(self.repo, 'checkout', 'main')
        self.git(self.repo, 'remote', 'set-url', 'origin', 'https://other.invalid/wrong.git')
        self.assertEqual(run().returncode, 3)
        self.assertIn('repository_origin', log.read_text(encoding='cp932'))


if __name__ == '__main__':
    unittest.main()
