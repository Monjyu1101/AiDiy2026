# -*- coding: utf-8 -*-

"""バックエンド(team) クリーンアップスクリプト。"""

from __future__ import annotations

import os
import shutil
import stat
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent


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
