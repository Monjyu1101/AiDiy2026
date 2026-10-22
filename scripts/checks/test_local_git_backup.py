import os
import importlib.util
import logging
import types
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.local_git_backup import commit_local_backup

@unittest.skipUnless(shutil.which("git"), "git required")
class LocalBackupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "日本語 space"
        self.root.mkdir()
        boundary=Path(self.tmp.name)
        original_lexists=os.path.lexists
        def fixture_lexists(path):
            return original_lexists(path) if Path(path).is_relative_to(boundary) else False
        original_run=subprocess.run
        def fixture_run(*args, **kwargs):
            kwargs["env"]=dict(kwargs.get("env",os.environ), GIT_CEILING_DIRECTORIES=str(boundary.parent))
            return original_run(*args, **kwargs)
        lexists_patch=patch("os.path.lexists",side_effect=fixture_lexists)
        run_patch=patch("subprocess.run",side_effect=fixture_run)
        lexists_patch.start();run_patch.start()
        self.addCleanup(lexists_patch.stop);self.addCleanup(run_patch.stop)
        self.meta = self.root / ".git_local"
        self.git("init", "--template=", "--separate-git-dir="+str(self.meta))
    def git(self, *args):
        env = {k:v for k,v in os.environ.items() if not k.upper().startswith("GIT_")}
        return subprocess.run(["git", "-C", str(self.root), *args], env=env, capture_output=True, text=True)
    def snapshot(self):
        return commit_local_backup(self.root, [p.relative_to(self.root).as_posix() for p in self.root.rglob("*") if p.is_file()])
    def test_missing_repo_created_and_first_backup_committed(self):
        # 既存fixtureの隣に、Git管理されていない別のプロジェクトを作る。
        plain=self.root.parent/"new project"
        plain.mkdir();(plain/"source.txt").write_text("source")
        self.assertEqual(commit_local_backup(plain,["source.txt"])[0],"created")
        self.assertTrue((plain/".git_local").is_dir())
        self.assertEqual(commit_local_backup(plain,["source.txt"])[0],"unchanged")
    def test_normal_repository_not_initialized_or_committed(self):
        plain=self.root.parent/"normal"
        plain.mkdir()
        subprocess.run(["git","-C",str(plain),"init"],capture_output=True,check=True)
        (plain/"source.txt").write_text("source")
        self.assertEqual(commit_local_backup(plain,["source.txt"])[0],"skipped")
        self.assertFalse((plain/".git_local").exists())
    def test_ancestor_repository_not_initialized(self):
        child=self.root/"nested"
        child.mkdir();(child/"source.txt").write_text("source")
        self.assertEqual(commit_local_backup(child,["source.txt"])[0],"skipped")
        self.assertFalse((child/".git_local").exists())
    def test_incomplete_metadata_not_reinitialized(self):
        plain=self.root.parent/"incomplete"
        plain.mkdir();(plain/".git_local").mkdir()
        (plain/".git_local"/"keep").write_text("keep")
        self.assertEqual(commit_local_backup(plain,[])[0],"skipped")
        self.assertFalse((plain/".git").exists())
        self.assertEqual((plain/".git_local"/"keep").read_text(),"keep")
    def test_new_modified_deleted_unchanged(self):
        path=self.root/"source.txt";path.write_text("one")
        self.assertEqual(self.snapshot()[0], "created")
        first=self.git("rev-parse","HEAD").stdout
        self.assertEqual(self.snapshot()[0], "unchanged")
        path.write_text("two");self.assertEqual(self.snapshot()[0], "created")
        self.assertNotEqual(self.git("rev-parse","HEAD").stdout,first)
        path.unlink();self.assertEqual(self.snapshot()[0], "created")
        self.assertEqual(self.git("ls-files").stdout, "")
        self.assertEqual(self.git("remote").stdout, "")
    def test_ignore_and_secret_exclusion_even_previously_tracked(self):
        (self.root/"source.txt").write_text("ok")
        self.snapshot()
        (self.root/".gitignore").write_text("source.txt\nprivate.txt\n")
        (self.root/"private.txt").write_text("private")
        (self.root/".env").write_text("secret")
        (self.root/"db.sqlite").write_text("db")
        self.assertEqual(self.snapshot()[0], "created")
        self.assertEqual(self.git("ls-files").stdout, "")
    def test_no_git_or_no_metadata_skips(self):
        with patch("scripts.local_git_backup.shutil.which",return_value=None):
            self.assertEqual(self.snapshot()[0], "skipped")

    def test_wrong_pointer_and_regular_repository_untouched(self):
        before=(self.meta/"HEAD").read_bytes()
        (self.root/".git").write_text("gitdir: ../other\n")
        self.assertEqual(self.snapshot()[0], "skipped")
        self.assertEqual((self.meta/"HEAD").read_bytes(),before)
    def test_invalid_metadata_errors(self):
        (self.meta/"HEAD").write_text("not git")
        self.assertEqual(self.snapshot()[0], "error")
    def test_wrong_config_worktree_rejected(self):
        self.git("config","core.worktree",str(self.root.parent))
        self.assertEqual(self.snapshot()[0], "error")
    def test_hooks_and_filters_not_executed(self):
        sentinel=self.root/"unexpected"
        hook=self.meta/"hooks"/"reference-transaction";hook.parent.mkdir(exist_ok=True)
        hook.write_text('#!/bin/sh\ntouch "'+str(sentinel)+'"\n');hook.chmod(0o755)
        self.git("config","filter.bad.clean",'touch "'+str(sentinel)+'"')
        (self.root/".gitattributes").write_text("*.txt filter=bad\n")
        (self.root/"source.txt").write_text("data")
        self.assertEqual(self.snapshot()[0],"created")
        self.assertFalse(sentinel.exists())
    def test_locked_index_preserved(self):
        (self.root/"source.txt").write_text("data")
        lock=self.meta/"index.lock";lock.write_text("user")
        self.assertEqual(self.snapshot()[0],"error")
        self.assertEqual(lock.read_text(),"user")
    def test_user_staged_changes_are_preserved(self):
        (self.root/"source.txt").write_text("user staged")
        self.git("add", "source.txt")
        before=(self.meta/"index").read_bytes()
        self.assertEqual(self.snapshot()[0], "error")
        self.assertEqual((self.meta/"index").read_bytes(), before)
        self.assertNotEqual(self.git("rev-parse", "--verify", "HEAD").returncode, 0)
    def test_actual_backup_triggers_history_even_without_copy_changes(self):
        spec=importlib.util.spec_from_file_location("backup_under_test",Path(__file__).resolve().parents[2]/"backend_server/AIコア/AIバックアップ.py")
        module=importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules,{"log_config":types.SimpleNamespace(get_logger=logging.getLogger)}):
            spec.loader.exec_module(module)
        path=self.root/"source.txt";path.write_text("before")
        context={"CODE_BASE_PATH":str(self.root)}
        self.assertIsNotNone(module.バックアップ実行(セッション設定=context, ログ出力=False))
        first=self.git("rev-parse","HEAD").stdout
        # 同一mtime内の変更は従来コピー差分には現れなくてもGitへ記録する。
        timestamp=path.stat().st_mtime
        path.write_text("after");os.utime(path,(timestamp,timestamp))
        self.assertIsNotNone(module.バックアップ実行(セッション設定=context, ログ出力=False))
        self.assertNotEqual(self.git("rev-parse","HEAD").stdout,first)
        self.assertEqual(self.git("ls-files").stdout,"source.txt\n")
    def test_identity_not_written_to_config(self):
        (self.root/"source.txt").write_text("data")
        before=(self.meta/"config").read_bytes()
        self.snapshot()
        self.assertEqual((self.meta/"config").read_bytes(),before)
        self.assertIn("AiDiy Local Backup",self.git("log","-1","--format=%an").stdout)

if __name__ == "__main__": unittest.main()
