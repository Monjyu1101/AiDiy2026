# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101
# -------------------------------------------------------------------------

"""frontend_avatar 専用セットアップスクリプト

独立したデスクトップアバターの起動に必要な最小セットアップだけを行います。
backend_server / frontend_server / npm / DB / グローバルツールは対象外です。
"""

import shutil
import subprocess
import sys
import time
from pathlib import Path

# ============================================================
# プロジェクト設定
# ============================================================
AVATAR_PATH = "frontend_avatar"            # アバターフォルダ名
AVATAR_ENV_CANDIDATES = [".venv", "venv"] # Python環境候補
AVATAR_SETUP_COMMAND = ["uv", "sync"]     # セットアップコマンド

# ============================================================


class Colors:
    HEADER = '\033[97m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(message):
    print(f"\n{Colors.HEADER}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{message}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'=' * 60}{Colors.ENDC}\n")


def print_success(message):
    print(f"{Colors.OKBLUE}[OK] {message}{Colors.ENDC}")


def print_error(message):
    print(f"{Colors.FAIL}[NG] {message}{Colors.ENDC}")


def print_warning(message):
    print(f"{Colors.WARNING}[WARN] {message}{Colors.ENDC}")


def print_info(message):
    print(f"{Colors.OKGREEN}[INFO] {message}{Colors.ENDC}")


BASE_DIR = Path(__file__).resolve().parent
AVATAR_DIR = BASE_DIR / AVATAR_PATH
AUTO_MODE = False


def ask_start_mode(prompt, default="n"):
    if default.lower() == "y":
        prompt_text = f"\n{prompt} ([y]/n/a=auto): "
    else:
        prompt_text = f"\n{prompt} (y/[n]/a=auto): "

    while True:
        answer = input(prompt_text).strip().lower()
        if answer == "":
            answer = default.lower()
        if answer in ["y", "yes"]:
            return True, False
        if answer in ["n", "no"]:
            return False, False
        if answer in ["a", "auto"]:
            return True, True
        print_warning("'y' または 'n' または 'a'(auto) で答えてください。")


def ask_yes_no(prompt, default="y"):
    global AUTO_MODE

    if AUTO_MODE:
        print_info(f"[AUTO] {prompt} -> {'Yes' if default.lower() == 'y' else 'No'} (default)")
        return default.lower() == "y"

    prompt_text = f"\n{prompt} ([y]/n): " if default.lower() == "y" else f"\n{prompt} (y/[n]): "
    while True:
        answer = input(prompt_text).strip().lower()
        if answer == "":
            answer = default.lower()
        if answer in ["y", "yes"]:
            return True
        if answer in ["n", "no"]:
            return False
        print_warning("'y' または 'n' で答えてください。")


def check_uv_installed() -> bool:
    return shutil.which("uv") is not None


def run_command(command, cwd: Path) -> bool:
    try:
        print_info(f"実行中: {' '.join(str(part) for part in command)}")
        subprocess.run(
            command,
            cwd=str(cwd),
            check=True,
            capture_output=False,
            text=True,
        )
        return True
    except subprocess.CalledProcessError as exc:
        print_error(f"コマンド実行エラー: {exc}")
        return False
    except Exception as exc:
        print_error(f"予期しないエラー: {exc}")
        return False



def setup_avatar_environment() -> bool:
    print_header("frontend_avatar セットアップ")
    print_info(f"作業ディレクトリ: {AVATAR_DIR}")

    if not AVATAR_DIR.exists():
        print_error(f"フォルダが見つかりません: {AVATAR_DIR}")
        return False

    pyproject_file = AVATAR_DIR / "pyproject.toml"
    if not pyproject_file.exists():
        print_error(f"pyproject.toml が見つかりません: {pyproject_file}")
        return False

    if not check_uv_installed():
        print_error("uv がインストールされていません。")
        print_info("uv をインストールしてください:")
        print_info("  PowerShell: irm https://astral.sh/uv/install.ps1 | iex")
        print_info("  または: pip install uv")
        return False

    existing_envs = [env_name for env_name in AVATAR_ENV_CANDIDATES if (AVATAR_DIR / env_name).exists()]
    if existing_envs:
        print_success(f"既存の仮想環境を検出しました: {', '.join(existing_envs)}")

    if not ask_yes_no("frontend_avatar のローカル環境をセットアップしますか?", default="y"):
        print_warning("セットアップをキャンセルしました。")
        return False

    if run_command(AVATAR_SETUP_COMMAND, cwd=AVATAR_DIR):
        print_success("frontend_avatar のセットアップが完了しました。")
        return True

    print_error("frontend_avatar のセットアップに失敗しました。")
    return False


def main():
    global AUTO_MODE

    print_header("frontend_avatar 専用セットアップ")
    print(f"{Colors.BOLD}このスクリプトは frontend_avatar の起動に必要な最小セットアップのみを実行します。{Colors.ENDC}")
    print()

    run_setup, AUTO_MODE = ask_start_mode("セットアップを実行しますか?", default="y")
    if not run_setup:
        print_warning("セットアップをキャンセルしました。")
        sys.exit(0)

    if AUTO_MODE:
        print_info("AUTOモードで実行します。以降の質問はデフォルト値で自動回答します。")

    if not setup_avatar_environment():
        sys.exit(1)

    print()
    print_header("セットアップ完了")
    print_success("frontend_avatar のセットアップが完了しました。")
    print_info("起動方法:")
    print_info("  python _start_avatar.py")
    print_info("または:")
    print_info("  cd frontend_avatar")
    print_info("  uv run python main.py")
    print_info("5秒後に終了します...")
    time.sleep(5)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_warning("セットアップが中断されました。")
        sys.exit(130)
    except Exception as exc:
        print_error(f"予期しないエラーが発生しました: {exc}")
        sys.exit(1)
