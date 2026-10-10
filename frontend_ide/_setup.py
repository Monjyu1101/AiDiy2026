# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026

"""IDE群(Code / Live / IDE)の依存・拡張・ランチャーをまとめて準備する。"""
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent

def prepare():
    npm = shutil.which('npm.cmd' if sys.platform == 'win32' else 'npm')
    if not npm:
        return False
    try:
        subprocess.run([npm, 'ci', '--include=dev', '--no-fund', '--no-audit'], cwd=ROOT, check=True)
        return True
    except (OSError, subprocess.CalledProcessError):
        return False

def setup(choices=None):
    if choices is not None and choices.get("ide") is False:
        return True
    print("\n" + "=" * 60)
    print("IDE群(Code / Live / IDE) セットアップ")
    print("=" * 60 + "\n")
    child_choices = {**(choices or {}), "ide": True}
    # hostからprepareだけを呼ぶため再帰しない。
    for name in ('frontend_ide/host', 'frontend_ide/viewer'):
        spec = importlib.util.spec_from_file_location('ide_setup_' + name.replace('/', '_'), ROOT.parent / name / '_setup.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if not module.setup(child_choices):
            return False
    print("IDE群(Code / Live / IDE) セットアップ完了")
    print("Code 起動: aidiy_code")
    print("Live 起動: aidiy_live")
    print("IDE  起動: aidiy_ide")
    return True

if __name__ == '__main__':
    sys.exit(0 if setup() else 1)
