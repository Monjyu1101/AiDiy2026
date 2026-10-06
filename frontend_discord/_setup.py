# -*- coding: utf-8 -*-
"""Discord フロントエンドの依存導入と、共通設定の不足キー補完。"""
import shutil
import os
import subprocess
import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))
from launcher import install_launcher
sys.path.insert(0, str(THIS_DIR.parent / 'scripts'))
from setup_electron import prepare_electron_binary


def setup(choices=None) -> bool:
    del choices
    npm = shutil.which("npm.cmd" if sys.platform == "win32" else "npm")
    if not npm:
        print("[NG] Node.js 22.12 以降と npm を導入してください。")
        return False
    try:
        env = {**os.environ, 'ELECTRON_SKIP_BINARY_DOWNLOAD': '1'}
        subprocess.run([npm, "ci", "--no-fund", "--no-audit"], cwd=THIS_DIR, env=env, check=True)
        if not prepare_electron_binary(THIS_DIR, 'Discord'):
            return False
        install_launcher(THIS_DIR)
        # キーを独自に上書きせず、backend と同じ補完・原子的保存を使う。
        sys.path.insert(0, str(THIS_DIR.parent / "backend_server"))
        from conf.conf_json import conf_json
        conf_json()
    except (OSError, ValueError, subprocess.CalledProcessError):
        print("[NG] Discord の依存導入または共通設定の補完に失敗しました。")
        return False
    print("[OK] aidiy_discord または discord.bat でパネルを開き、開始ボタンで接続してください。")
    return True


if __name__ == "__main__":
    sys.exit(0 if setup() else 1)
