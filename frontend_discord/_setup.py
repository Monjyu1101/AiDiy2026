# -*- coding: utf-8 -*-
"""Discord フロントエンドの依存導入と、共通設定の不足キー補完。"""
import importlib.util
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


class Colors:
    HEADER = "\033[97m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"


def print_header(message):
    print(f"\n{Colors.HEADER}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{message}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'=' * 60}{Colors.ENDC}\n")


def print_success(message):
    print(f"{Colors.OKBLUE}[OK] {message}{Colors.ENDC}")


def print_error(message):
    print(f"{Colors.FAIL}[NG] {message}{Colors.ENDC}")


def print_info(message):
    print(f"{Colors.OKGREEN}[INFO] {message}{Colors.ENDC}")


def setup(choices=None) -> bool:
    del choices
    print_header("フロントエンド(Discord) セットアップ")
    print_info(f"作業ディレクトリ: {THIS_DIR}")
    print_info("対象: Discord Bot パネル / Electron / 共通設定の不足キー補完")
    npm = shutil.which("npm.cmd" if sys.platform == "win32" else "npm")
    if not npm:
        print_error("Node.js 22.12 以降と npm を導入してください。")
        return False
    try:
        env = {**os.environ, 'ELECTRON_SKIP_BINARY_DOWNLOAD': '1'}
        print_info(f"実行中: {npm} ci --no-fund --no-audit")
        subprocess.run([npm, "ci", "--no-fund", "--no-audit"], cwd=THIS_DIR, env=env, check=True)
        if not prepare_electron_binary(THIS_DIR, 'Discord'):
            return False
        install_launcher(THIS_DIR)
        # キーを独自に上書きせず、backend と同じ補完・原子的保存を使う。
        # conf パッケージの __init__ は requests 等の backend 依存を読むため、
        # 素の Python でも動く conf_json.py だけを直接読み込む。
        backend_dir = THIS_DIR.parent / "backend_server"
        sys.path.insert(0, str(backend_dir))
        spec = importlib.util.spec_from_file_location("_discord_conf_json", backend_dir / "conf" / "conf_json.py")
        conf_json_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(conf_json_mod)
        conf_json_mod.conf_json()
        print_success("共通設定の不足キーを補完しました。")
    except (OSError, ValueError, ImportError, subprocess.CalledProcessError):
        print_error("Discord の依存導入または共通設定の補完に失敗しました。")
        return False
    print_success("フロントエンド(Discord): aidiy_discord で起動できます。")
    return True


if __name__ == "__main__":
    sys.exit(0 if setup() else 1)
