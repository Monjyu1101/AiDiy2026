"""単一batの静的構造・対象選択モデル・実Git契約試験。Windows CMDの実行試験ではない。"""
from pathlib import Path
import re
import shlex
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
BAT = ROOT / "_automatic.bat"
TEXT = BAT.read_bytes().decode("utf-8").replace("\r\n", "\n")


class BatchStructureTests(unittest.TestCase):
    def test_utf8_crlf_no_bom(self):
        data = BAT.read_bytes()
        self.assertFalse(data.startswith(b"\xef\xbb\xbf"))
        self.assertNotIn(b"\n", data.replace(b"\r\n", b""))

    def test_labels_and_calls_resolve(self):
        labels = re.findall(r"^:([a-z_]+)$", TEXT, re.M)
        self.assertEqual(len(labels), len(set(labels)))
        for label in re.findall(r"\bgoto\s+([a-z_]+)", TEXT, re.I):
            self.assertIn(label.lower(), labels)
        for label in re.findall(r"\bcall\s+:([a-z_]+)", TEXT, re.I):
            self.assertIn(label.lower(), labels)

    def test_single_file_no_companion_or_embedded_program(self):
        self.assertNotIn("_automatic.py", TEXT)
        self.assertNotIn("runpy", TEXT)
        self.assertFalse((ROOT / "_automatic.py").exists())

    def test_original_locations_saved_before_control_transfer(self):
        transfer = TEXT.index('"%AIDIY_TEMP%\\_automatic.bat" --_aidiy_temp')
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
        self.assertIn('findstr /i /l /x /v /g:', TEXT)
        self.assertIn('git remote get-url --all origin', TEXT)

    def test_clone_publish_uses_rename_not_move_into_existing_target(self):
        self.assertIn('ren "%STAGING%" "AiDiy2026"', TEXT)
        self.assertNotRegex(TEXT, r"(?im)^move\b")
        self.assertNotIn('rd "%STAGING%"', TEXT)

    def test_backup_is_required_before_fetch_and_setup(self):
        self.assertLess(TEXT.index('call :backup_local_state'), TEXT.index('git fetch '))
        self.assertIn('call :backup_local_state\nset "RC=%ERRORLEVEL%"\nif not "%RC%"=="0" goto failed', TEXT)
        self.assertIn('robocopy "_config"', TEXT)
        self.assertIn('git diff --cached --binary', TEXT)
        self.assertIn('call :backup_file', TEXT)

    def test_interactive_setup_start_and_error_propagation(self):
        block = TEXT[TEXT.index('\n:setup\n'):TEXT.index('\n:validate_repository\n')]
        for script in ('_setup.py', '_start.py'):
            self.assertIn(f'"%PYTHON%" -u {script}\nset "RC=%ERRORLEVEL%"', block)
        self.assertLess(block.index('_setup.py'), block.index('_start.py'))
        self.assertIn('if not "%RC%"=="0" goto failed', block)
        self.assertNotRegex(block, r"(?m)^.*(?:_setup|_start)\.py.*[<>|]")
        self.assertNotIn('再セットアップ', TEXT)
        self.assertNotIn('setup-state', TEXT)

    def test_cleanup_does_not_remove_unknown_files_or_original(self):
        cleanup = TEXT[TEXT.index(':clean_temp\n'):TEXT.index(':log_error\n')]
        self.assertNotIn('/s', cleanup.lower())
        self.assertNotIn('%AIDIY_SOURCE%', cleanup)
        self.assertIn('exit /b %RC%', cleanup)


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


if __name__ == '__main__':
    unittest.main()
