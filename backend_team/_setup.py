# -*- coding: utf-8 -*-

"""バックエンド(team) セットアップスクリプト。"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
BACKEND_TEAM_ENV = ".venv"


class Colors:
    HEADER = "\033[97m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"


def print_header(message: str) -> None:
    print(f"\n{Colors.HEADER}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{message}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'=' * 60}{Colors.ENDC}\n")


def print_success(message: str) -> None:
    print(f"{Colors.OKBLUE}[OK] {message}{Colors.ENDC}")


def print_error(message: str) -> None:
    print(f"{Colors.FAIL}[NG] {message}{Colors.ENDC}")


def print_info(message: str) -> None:
    print(f"{Colors.OKGREEN}[INFO] {message}{Colors.ENDC}")


def run_command(command: list[str], cwd: Path) -> bool:
    try:
        print_info(f"実行中: {' '.join(command)}")
        subprocess.run(command, cwd=cwd, check=True, capture_output=False, text=True)
        return True
    except subprocess.CalledProcessError as exc:
        print_error(f"コマンド実行エラー: {exc}")
        return False
    except Exception as exc:
        print_error(f"予期しないエラー: {exc}")
        return False


def setup(choices: dict | None = None) -> bool:
    del choices
    label = "バックエンド(team)"
    print_header(f"{label} セットアップ")
    print_info(f"作業ディレクトリ: {THIS_DIR}")
    print_info("対象: AIチーム FastAPI (初期ポート 8094)")

    if not THIS_DIR.exists():
        print_error(f"{label}: フォルダが見つかりません: {THIS_DIR}")
        return False
    if shutil.which("uv") is None:
        print_error(f"{label}: uv がインストールされていません。")
        print_info("  PowerShell: irm https://astral.sh/uv/install.ps1 | iex")
        print_info("  または: pip install uv")
        return False
    if not (THIS_DIR / "pyproject.toml").exists():
        print_error(f"{label}: pyproject.toml が見つかりません。")
        return False

    venv_dir = THIS_DIR / BACKEND_TEAM_ENV
    if venv_dir.exists():
        print_success(f"{label}: 既存の仮想環境を検出しました: {venv_dir}")

    if not run_command(["uv", "sync", "--upgrade"], cwd=THIS_DIR):
        print_error(f"{label}: uv sync --upgrade に失敗しました。")
        return False

    print_success(f"{label}: 依存関係のセットアップが完了しました。")
    return True


def main() -> None:
    if not setup():
        sys.exit(1)


if __name__ == "__main__":
    main()
