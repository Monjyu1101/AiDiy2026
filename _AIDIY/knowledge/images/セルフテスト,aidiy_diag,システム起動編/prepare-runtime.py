"""今回の実画面試験用。既存ロックの依存物と共有Electronだけを再配置する。"""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
TARGETS = {'avatar': ROOT / 'frontend_avatar', 'ide-host': ROOT / 'frontend_ide/host', 'discord': ROOT / 'frontend_channels', 'web': ROOT / 'frontend_web'}
spec = importlib.util.spec_from_file_location('aidiy_test_electron', ROOT / 'scripts/_setup_electron.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
target = TARGETS[sys.argv[1]]
assert target.resolve().is_relative_to(ROOT.resolve())
assert (target / 'node_modules').resolve().is_relative_to(ROOT.resolve())
log = Path(__file__).with_name('prepare-' + sys.argv[1] + '.log')
npm = shutil.which('npm.cmd' if sys.platform == 'win32' else 'npm')
env = {**os.environ, 'ELECTRON_SKIP_BINARY_DOWNLOAD': '1'}
with log.open('w', encoding='utf-8') as stream:
    result = subprocess.run([npm, 'ci', '--include=dev', '--no-audit', '--no-fund'], cwd=target, env=env, stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT)
    if result.returncode:
        raise SystemExit(result.returncode)
    def info(message):
        print(message, file=stream, flush=True)
    if sys.argv[1] != 'web' and not helper.prepare_electron_binary(target, sys.argv[1], info=info, error=info):
        raise SystemExit(1)
print(sys.argv[1] + ': runtime ready')
