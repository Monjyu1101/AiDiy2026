# -*- coding: utf-8 -*-

"""バックエンド(hermes) 起動スクリプト

Hermes は常駐サーバーではなく対話型 CLI (`cli_main.py`) です。
このスクリプトは仮想環境の Python で CLI を対話起動します。
ルートの `_start.py` は hermes を常駐管理しないため、この CLI は
必要時に単体で起動する想定です。

公開 API:
    check_environment() -> (bool, str)
    start() -> int   # CLI を対話起動し、終了コードを返す
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


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


def print_error(message: str) -> None:
    print(f"{Colors.FAIL}[NG] {message}{Colors.ENDC}")


def print_info(message: str) -> None:
    print(f"{Colors.OKGREEN}[INFO] {message}{Colors.ENDC}")


THIS_DIR = Path(__file__).resolve().parent
BACKEND_HERMES_DIR = THIS_DIR
CLI_SCRIPT = "cli_main.py"
ENV_CANDIDATES = [".venv", "venv"]


def find_python_in_env(base_dir: Path, env_candidates: list[str]) -> Path | None:
    for env_name in env_candidates:
        if sys.platform == "win32":
            python_path = base_dir / env_name / "Scripts" / "python.exe"
        else:
            python_path = base_dir / env_name / "bin" / "python"
        if python_path.exists():
            return python_path
    return None


def check_environment() -> tuple[bool, str]:
    if not BACKEND_HERMES_DIR.exists():
        return False, f"フォルダが見つかりません: {BACKEND_HERMES_DIR}"
    if not (BACKEND_HERMES_DIR / CLI_SCRIPT).exists():
        return False, f"{CLI_SCRIPT} が見つかりません: {BACKEND_HERMES_DIR / CLI_SCRIPT}"
    python_path = find_python_in_env(BACKEND_HERMES_DIR, ENV_CANDIDATES)
    if python_path is not None:
        return True, str(python_path)
    import shutil
    if shutil.which("uv") is not None:
        return True, "uv"
    return False, f"Python 仮想環境 ({' / '.join(ENV_CANDIDATES)}) または uv が見つかりません"


def start() -> int:
    """Hermes CLI を対話起動する。終了コードを返す。"""
    python_path = find_python_in_env(BACKEND_HERMES_DIR, ENV_CANDIDATES)
    if python_path is not None:
        command = [str(python_path), CLI_SCRIPT]
    else:
        command = ["uv", "run", "python", CLI_SCRIPT]
    print_info(f"[バックエンド(hermes)] 作業ディレクトリ: {BACKEND_HERMES_DIR}")
    print_info(f"[バックエンド(hermes)] コマンド: {' '.join(command)}")
    # 対話型 CLI のため stdio は継承する
    result = subprocess.run(command, cwd=str(BACKEND_HERMES_DIR))
    return result.returncode


def main() -> None:
    print_header("バックエンド(hermes) CLI 起動")
    ok, detail = check_environment()
    if not ok:
        print_error(f"環境が準備されていません: {detail}")
        print_info("  対応例: python _setup.py")
        sys.exit(1)
    print_success(f"環境確認: OK ({detail})")
    code = start()
    sys.exit(code)


if __name__ == "__main__":
    main()
