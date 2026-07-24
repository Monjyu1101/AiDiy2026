# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""バックエンド(team) クリーンアップスクリプト。"""

from __future__ import annotations

import os
import shutil
import stat
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    import msvcrt


THIS_DIR = Path(__file__).resolve().parent
AUTO_MODE = False


class Colors:
    HEADER = "\033[97m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"


def print_header(message: str) -> None:
    print(f"\n{Colors.HEADER}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{message}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'=' * 60}{Colors.ENDC}\n")


def print_success(message: str) -> None:
    print(f"{Colors.OKBLUE}[OK] {message}{Colors.ENDC}")


def print_info(message: str) -> None:
    print(f"{Colors.OKGREEN}[INFO] {message}{Colors.ENDC}")


def print_warning(message: str) -> None:
    print(f"{Colors.WARNING}[WARN] {message}{Colors.ENDC}")


def print_error(message: str) -> None:
    print(f"{Colors.FAIL}[NG] {message}{Colors.ENDC}")


def _clear_keyboard_buffer() -> None:
    if sys.platform != "win32":
        return
    while msvcrt.kbhit():
        key = msvcrt.getch()
        if key in (b"\x00", b"\xe0") and msvcrt.kbhit():
            msvcrt.getch()


def _read_single_key(valid: tuple[bytes, ...], default_key: bytes) -> bytes:
    if sys.platform == "win32":
        _clear_keyboard_buffer()
        while True:
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key in (b"\x00", b"\xe0"):
                    if msvcrt.kbhit():
                        msvcrt.getch()
                    continue
                if key in (b"\r", b"\n"):
                    print(default_key.decode("ascii"))
                    return default_key
                if key in valid:
                    print(key.decode("ascii", errors="replace"))
                    return key
            time.sleep(0.05)

    response = input().strip().lower()
    if response == "":
        return default_key
    first = response[0:1].encode("ascii", errors="replace")
    if first in valid:
        return first
    return default_key


def ask_yes_no(prompt: str, default: str = "n") -> bool:
    if AUTO_MODE:
        print_info(f"[AUTO] {prompt} -> {'Yes' if default.lower() == 'y' else 'No'} (default)")
        return default.lower() == "y"
    bracket = "[y]/n" if default.lower() == "y" else "y/[n]"
    print(f"\n{prompt} ({bracket}): ", end="", flush=True)
    default_key = b"y" if default.lower() == "y" else b"n"
    key = _read_single_key((b"y", b"Y", b"n", b"N"), default_key)
    return key in (b"y", b"Y")


def ask_start_mode(prompt: str, default: str = "n") -> tuple[bool, bool]:
    bracket = "[y]/n/a=auto" if default.lower() == "y" else "y/[n]/a=auto"
    print(f"\n{prompt} ({bracket}): ", end="", flush=True)
    default_key = b"y" if default.lower() == "y" else b"n"
    key = _read_single_key((b"y", b"Y", b"n", b"N", b"a", b"A"), default_key)
    if key in (b"a", b"A"):
        return True, True
    if key in (b"y", b"Y"):
        return True, False
    return False, False


def handle_remove_readonly(func, path, exc_info) -> None:
    del exc_info
    os.chmod(path, stat.S_IWRITE)
    func(path)


def remove_directory(path: Path, description: str) -> bool:
    if not path.exists() or not path.is_dir():
        return False
    try:
        shutil.rmtree(path, onerror=handle_remove_readonly)
        print_success(f"{description} を削除しました: {path}")
        return True
    except Exception as exc:
        print_error(f"{description} の削除に失敗しました: {path}")
        print_error(f"  理由: {exc}")
        return False


def cleanup_common_python_caches(target_dir: Path, label: str) -> int:
    deleted_count = 0
    print_info(f"{label}: __pycache__ フォルダを検索中...")
    for path in target_dir.rglob("__pycache__"):
        if remove_directory(path, f"__pycache__ ({label})"):
            deleted_count += 1
    print_info(f"{label}: .pytest_cache フォルダを検索中...")
    for path in target_dir.rglob(".pytest_cache"):
        if remove_directory(path, f".pytest_cache ({label})"):
            deleted_count += 1
    return deleted_count


def cleanup(choices: dict) -> None:
    label = "バックエンド(team)"
    print_header(f"{label} のクリーンアップ")

    if not THIS_DIR.exists():
        print_warning(f"{label} のフォルダが見つかりません")
        return

    deleted_count = cleanup_common_python_caches(THIS_DIR, label)

    env_dir = THIS_DIR / ".venv"
    if env_dir.exists():
        if choices.get("team_env") is True:
            if remove_directory(env_dir, f".venv ({label})"):
                deleted_count += 1
        elif choices.get("team_env") is False:
            print_info("  .venv はそのまま残します")

    temp_dir = THIS_DIR / "temp"
    if temp_dir.exists():
        if choices.get("team_temp") is True:
            if remove_directory(temp_dir, f"temp ({label})"):
                deleted_count += 1
        elif choices.get("team_temp") is False:
            print_info("  temp はそのまま残します")

    if deleted_count > 0:
        print_success(f"{label} のクリーンアップ完了 ({deleted_count}個削除)")
    else:
        print_info(f"{label}: 削除対象はありませんでした")


def collect_choices() -> dict:
    choices: dict = {"team_env": None, "team_temp": None}
    if THIS_DIR.exists():
        if (THIS_DIR / ".venv").exists():
            choices["team_env"] = ask_yes_no("  .venv を削除しますか？", default="y")
        if (THIS_DIR / "temp").exists():
            choices["team_temp"] = ask_yes_no("  temp フォルダを削除しますか？", default="y")
    return choices


def main() -> None:
    global AUTO_MODE
    print_header("バックエンド(team) クリーンアップ")
    run_cleanup, AUTO_MODE = ask_start_mode("クリーンアップを実行しますか？", default="n")
    if not run_cleanup:
        print_info("クリーンアップをキャンセルしました")
        return
    if AUTO_MODE:
        print_info("AUTOモードで実行します。以降の質問はデフォルト値で自動回答します。")
    cleanup(collect_choices())
    print_success("クリーンアップが完了しました")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_warning("クリーンアップが中断されました")
        sys.exit(1)
