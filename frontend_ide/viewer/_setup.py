# -*- coding: utf-8 -*-
#
# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""AiDiy IDE（frontend_ide/viewer）の依存導入と aidiy_ide ランチャー登録。

ルートの `_setup.py` から呼ばれるほか、単独でも実行できる:
    python frontend_ide/viewer/_setup.py
コード表示の Monaco Editor と、Word / Excel / PowerPoint / PDF の表示ライブラリを自前で導入する。

公開 API:
    setup(choices: dict | None = None) -> bool
"""
import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))
# 全体処理で他フォルダの同名 launcher がキャッシュされても取り違えない。
_launcher_spec = importlib.util.spec_from_file_location('aidiy_frontend_dev_launcher', THIS_DIR / 'launcher.py')
_launcher = importlib.util.module_from_spec(_launcher_spec)
_launcher_spec.loader.exec_module(_launcher)
install_launcher = _launcher.install_launcher


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
    if not (choices and choices.get("ide")):
        print_header("IDE群(Code / Live / IDE) セットアップ")
    print_info(f"作業ディレクトリ: {THIS_DIR}")
    print_info("対象: Electron / コード・Office文書ビューア（Monaco / docx-preview / SheetJS / PptxViewJS / PDF.js）")
    npm = shutil.which("npm.cmd" if sys.platform == "win32" else "npm")
    if not npm:
        print_error("Node.js 22.13 以降と npm を導入してください。")
        return False
    # ロックファイルがあれば再現性のある npm ci、初回だけ npm install で作る。
    command = "ci" if (THIS_DIR / "package-lock.json").exists() else "install"
    try:
        print_info(f"実行中: {npm} {command} --no-fund --no-audit")
        env = dict(os.environ)
        browser_only = env.get('CODESPACES') == 'true' or (sys.platform.startswith('linux') and not env.get('DISPLAY') and not env.get('WAYLAND_DISPLAY'))
        if browser_only:
            env['ELECTRON_SKIP_BINARY_DOWNLOAD'] = '1'
            print_info("Web 起動環境のため Electron 本体のダウンロードは省略します。")
        subprocess.run([npm, command, "--include=dev", "--no-fund", "--no-audit"], cwd=THIS_DIR, env=env, check=True)
        vue = THIS_DIR.parent.parent / 'frontend_ide'
        if not (vue / 'node_modules' / 'vue').is_dir():
            subprocess.run([npm, 'ci', '--include=dev', '--no-fund', '--no-audit'], cwd=vue, check=True)
        subprocess.run([npm, 'run', 'build'], cwd=vue, check=True)
        install_launcher(THIS_DIR)
    except (OSError, subprocess.CalledProcessError):
        print_error("AiDiy IDE の依存導入またはランチャー登録に失敗しました。")
        return False
    if not (choices and choices.get("ide")):
        print_success("IDE群(Code / Live / IDE): aidiy_ide で起動できます。")
    return True


if __name__ == "__main__":
    sys.exit(0 if setup() else 1)
