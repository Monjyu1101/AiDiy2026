# -*- coding: utf-8 -*-

"""バックエンド(team) 起動スクリプト。"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from team_proc.config import get_team_port

PORT = get_team_port()
APP = "team_main:app"


def _python_path() -> Path | None:
    path = THIS_DIR / ".venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    return path if path.exists() else None


def check_environment() -> tuple[bool, str]:
    python = _python_path()
    if python:
        return True, str(python)
    if shutil.which("uv"):
        return True, "uv"
    return False, "backend_team の .venv または uv が見つかりません"


def get_command() -> list[str]:
    python = _python_path()
    prefix = [str(python)] if python else ["uv", "run"]
    return prefix + ["-m", "uvicorn", APP, "--host", "0.0.0.0", "--port", str(PORT)]


def start() -> subprocess.Popen[bytes]:
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    return subprocess.Popen(
        get_command(),
        cwd=str(THIS_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=0,
        creationflags=creationflags,
    )


def kill_ports() -> None:
    """ルート _start.py がポート解放を担当するため、単体利用時は何もしない。"""


def main() -> None:
    ok, detail = check_environment()
    if not ok:
        raise SystemExit(detail)
    print(f"backend_team: http://localhost:{PORT}/docs")
    subprocess.run(get_command(), cwd=str(THIS_DIR), check=False)


if __name__ == "__main__":
    main()
