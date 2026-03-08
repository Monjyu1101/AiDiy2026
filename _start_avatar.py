# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101
# -------------------------------------------------------------------------

"""frontend_avatar 専用起動スクリプト

独立したデスクトップアバターを起動するための最小ランチャーです。
既存の backend_server / frontend_server は起動しません。
"""

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    import msvcrt

# ============================================================
# プロジェクト設定
# ============================================================
AVATAR_PATH = "frontend_avatar"            # アバターフォルダ名
AVATAR_ENV_CANDIDATES = [".venv", "venv"] # Python環境候補
AVATAR_ENTRYPOINT_MODULE = "main"          # 起動対象モジュール
EXIT_WAIT_SECONDS = 5                      # 終了前待機秒数
REBOOT_WAIT_SECONDS = 10                   # リブート受付秒数

# ============================================================


class Colors:
    HEADER = '\033[97m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
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


BASE_DIR = Path(__file__).parent
AVATAR_DIR = BASE_DIR / AVATAR_PATH
CONTROL_C_EXIT_CODES = {130, -1073741510, 3221225786}


def find_avatar_python() -> Path | None:
    for env_name in AVATAR_ENV_CANDIDATES:
        if sys.platform == "win32":
            python_path = AVATAR_DIR / env_name / "Scripts" / "python.exe"
        else:
            python_path = AVATAR_DIR / env_name / "bin" / "python"
        if python_path.exists():
            return python_path
    return None


def check_uv_installed() -> bool:
    return shutil.which("uv") is not None


def check_environment() -> tuple[bool, str]:
    if not AVATAR_DIR.exists():
        return False, f"フォルダが見つかりません: {AVATAR_DIR}"

    pyproject_file = AVATAR_DIR / "pyproject.toml"
    if not pyproject_file.exists():
        return False, f"pyproject.toml が見つかりません: {pyproject_file}"

    avatar_python = find_avatar_python()
    if avatar_python is not None:
        return True, str(avatar_python)

    if not check_uv_installed():
        return False, "uv コマンドが見つかりません"

    return False, "仮想環境が見つかりません"


def build_command() -> list[str]:
    avatar_python = find_avatar_python()
    if avatar_python is not None:
        return [str(avatar_python), "-m", AVATAR_ENTRYPOINT_MODULE]
    return ["uv", "run", "python", "-m", AVATAR_ENTRYPOINT_MODULE]


def is_r_pressed() -> bool:
    if sys.platform != "win32":
        return False
    if not msvcrt.kbhit():
        return False
    key = msvcrt.getch()
    if key in (b"\x00", b"\xe0"):
        if msvcrt.kbhit():
            msvcrt.getch()
        return False
    return key in (b"r", b"R")


def clear_keyboard_buffer() -> None:
    if sys.platform != "win32":
        return
    while msvcrt.kbhit():
        key = msvcrt.getch()
        if key in (b"\x00", b"\xe0") and msvcrt.kbhit():
            msvcrt.getch()


def prompt_reboot() -> bool:
    if sys.platform != "win32":
        return False
    clear_keyboard_buffer()
    print("\n\n")
    print(f"{Colors.FAIL}R を押すとリブートします ({REBOOT_WAIT_SECONDS}秒以内){Colors.ENDC}")
    start_time = time.time()
    while time.time() - start_time < REBOOT_WAIT_SECONDS:
        if is_r_pressed():
            print_info("リブートを開始します")
            return True
        time.sleep(0.05)
    return False


def main():
    while True:
        print_header("frontend_avatar 起動")
        print_info(f"対象フォルダ: {AVATAR_DIR}")

        is_ready, detail = check_environment()
        if is_ready:
            print_success(f"Python 環境: OK ({detail})")
        else:
            print_warning(f"Python 環境: 未準備 ({detail})")
            print_info("セットアップ方法:")
            print_info("  cd frontend_avatar")
            print_info("  uv sync")
            sys.exit(1)

        command = build_command()
        print_info(f"起動コマンド: {' '.join(command)}")
        print_info("既存の backend_server / frontend_server は起動しません")

        reboot_requested = False
        process = None
        stopped_by_keyboard = False

        try:
            if sys.platform == "win32":
                process = subprocess.Popen(
                    command,
                    cwd=str(AVATAR_DIR),
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                )
            else:
                process = subprocess.Popen(
                    command,
                    cwd=str(AVATAR_DIR),
                )
            print_success("frontend_avatar を起動しました")
            while True:
                exit_code = process.poll()
                if exit_code is not None:
                    break
                time.sleep(0.2)

            if exit_code == 0:
                print_success("frontend_avatar は正常終了しました")
            elif exit_code in CONTROL_C_EXIT_CODES:
                print_warning(f"frontend_avatar は Ctrl+C により終了しました (終了コード: {exit_code})")
                reboot_requested = prompt_reboot()
            else:
                print_error(f"frontend_avatar が異常終了しました (終了コード: {exit_code})")
                log_dir = AVATAR_DIR / "temp" / "logs"
                if log_dir.exists():
                    print_info(f"実行ログ: {log_dir}")
                sys.exit(exit_code)
        except KeyboardInterrupt:
            stopped_by_keyboard = True
            print_warning("Ctrl+C を検出しました。frontend_avatar を終了します")
            try:
                if process is not None:
                    process.terminate()
                    process.wait(timeout=5)
            except Exception:
                pass
            reboot_requested = prompt_reboot()
        finally:
            if reboot_requested:
                if sys.platform == "win32":
                    os.system("cls")
                continue
            if stopped_by_keyboard:
                return
            print_info(f"{EXIT_WAIT_SECONDS}秒後に終了します...")
            time.sleep(EXIT_WAIT_SECONDS)
            return


if __name__ == "__main__":
    main()
