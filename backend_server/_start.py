# -*- coding: utf-8 -*-

"""バックエンド(core,apps) 起動スクリプト

このフォルダ (backend_server) 単体の起動を行います。
ルートの `_start.py` から import して環境確認・起動関数を呼び出すことも、
このスクリプトを直接実行して core / apps を単体起動することもできます。

公開 API:
    CORE_PORT, APPS_PORT
    check_environment() -> (bool, str)
    start_core() -> subprocess.Popen
    start_apps() -> subprocess.Popen
    kill_ports()
"""

from __future__ import annotations

import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

if sys.platform == "win32":
    import msvcrt


class Colors:
    HEADER = "\033[97m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
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


def print_warning(message: str) -> None:
    print(f"{Colors.WARNING}[WARN] {message}{Colors.ENDC}")


def print_info(message: str) -> None:
    print(f"{Colors.OKGREEN}[INFO] {message}{Colors.ENDC}")


# ============================================================
# 設定
# ============================================================
THIS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = THIS_DIR
CORE_PORT = 8091
APPS_PORT = 8092
CORE_APP = "core_main:app"
APPS_APP = "apps_main:app"
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


def check_command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def get_backend_command(app_module: str, port: int) -> list[str]:
    backend_python = find_python_in_env(BACKEND_DIR, ENV_CANDIDATES)
    if backend_python is not None:
        return [str(backend_python), "-m", "uvicorn", app_module, "--host", "0.0.0.0", "--port", str(port)]
    return ["uv", "run", "uvicorn", app_module, "--host", "0.0.0.0", "--port", str(port)]


def check_environment() -> tuple[bool, str]:
    if not BACKEND_DIR.exists():
        return False, f"フォルダが見つかりません: {BACKEND_DIR}"
    if not (BACKEND_DIR / "pyproject.toml").exists():
        return False, f"pyproject.toml が見つかりません: {BACKEND_DIR / 'pyproject.toml'}"
    backend_python = find_python_in_env(BACKEND_DIR, ENV_CANDIDATES)
    if backend_python is not None:
        return True, str(backend_python)
    if check_command_exists("uv"):
        return True, "uv"
    return False, f"Python 仮想環境 ({' / '.join(ENV_CANDIDATES)}) または uv が見つかりません"


def launch_process(name: str, command: list[str], cwd: Path) -> subprocess.Popen[bytes]:
    print_info(f"[{name}] 作業ディレクトリ: {cwd}")
    print_info(f"[{name}] コマンド: {' '.join(command)}")
    if sys.platform == "win32":
        process = subprocess.Popen(
            command,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
    else:
        process = subprocess.Popen(
            command,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
            preexec_fn=os.setpgrp,
        )
    print_success(f"[{name}] 起動しました")
    return process


def start_core() -> subprocess.Popen[bytes]:
    return launch_process("バックエンド(core)", get_backend_command(CORE_APP, CORE_PORT), BACKEND_DIR)


def start_apps() -> subprocess.Popen[bytes]:
    return launch_process("バックエンド(apps)", get_backend_command(APPS_APP, APPS_PORT), BACKEND_DIR)


# ============================================================
# ポート整理
# ============================================================
def _listening_pids_windows(port: int) -> list[str]:
    result = subprocess.run(["netstat", "-ano", "-p", "tcp"], capture_output=True, text=True, timeout=5)
    if result.returncode != 0:
        return []
    pids = set()
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue
        local_address = parts[1]
        state = parts[3].upper()
        pid = parts[-1]
        local_port = local_address.rsplit(":", 1)[-1]
        if local_port != str(port):
            continue
        if state not in ("LISTENING", "待ち受け"):
            continue
        if pid.isdigit() and pid != "0":
            pids.add(pid)
    return sorted(pids, key=int)


def _listening_pids_linux(port: int) -> list[str]:
    try:
        result = subprocess.run(
            ["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-t"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode in (0, 1):
            pids = {pid.strip() for pid in result.stdout.splitlines() if pid.strip().isdigit()}
            return sorted(pids, key=int)
    except FileNotFoundError:
        pass
    try:
        result = subprocess.run(
            ["ss", "-ltnp", f"sport = :{port}"], capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            return []
        pids = set(re.findall(r"pid=(\d+)", result.stdout))
        return sorted(pids, key=int)
    except FileNotFoundError:
        return []


def kill_process_on_port(port: int) -> bool:
    print_info(f"[ポート {port}] 使用中プロセスを確認します")
    try:
        if sys.platform == "win32":
            finder = _listening_pids_windows
            killer = lambda pid: subprocess.run(["taskkill", "/F", "/T", "/PID", pid], capture_output=True, text=True, timeout=8)
        else:
            finder = _listening_pids_linux
            killer = lambda pid: subprocess.run(["kill", "-9", pid], capture_output=True, text=True, timeout=5)

        killed = False
        for _ in range(8):
            pids = finder(port)
            if not pids:
                if killed:
                    print_success(f"[ポート {port}] ポート解放を確認しました")
                else:
                    print_info(f"[ポート {port}] 使用中プロセスはありません")
                return killed
            for pid in pids:
                print_info(f"[ポート {port}] PID={pid} を停止します")
                result = killer(pid)
                if result.returncode == 0:
                    print_success(f"[ポート {port}] PID={pid} を停止しました")
                    killed = True
                else:
                    detail = (result.stderr or result.stdout or "").strip()
                    print_warning(f"[ポート {port}] PID={pid} の停止に失敗しました: {detail}")
            time.sleep(0.5)

        remaining = finder(port)
        if remaining:
            print_error(f"[ポート {port}] 停止後も使用中です: PID={','.join(remaining)}")
        return killed
    except Exception as exc:
        print_error(f"[ポート {port}] 確認時にエラーが発生しました: {exc}")
        return False


def kill_ports() -> None:
    kill_process_on_port(CORE_PORT)
    kill_process_on_port(APPS_PORT)


# ============================================================
# 単体実行用の簡易監視
# ============================================================
def _stream_output(name: str, stream) -> None:
    if stream is None:
        return
    try:
        while True:
            chunk = stream.read(1024)
            if not chunk:
                break
            text = chunk.decode("utf-8", errors="replace")
            for line in text.splitlines(keepends=True):
                sys.stdout.write(f"{Colors.OKCYAN}[{name}]{Colors.ENDC} {line}")
            sys.stdout.flush()
    except Exception:
        pass


def _stop(processes: dict[str, subprocess.Popen[bytes]]) -> None:
    for name, process in list(processes.items()):
        try:
            print_info(f"[{name}] 停止しています")
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True, timeout=5)
            else:
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    time.sleep(0.5)
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            print_success(f"[{name}] 停止しました")
        except Exception as exc:
            print_error(f"[{name}] 停止時にエラーが発生しました: {exc}")
        finally:
            processes.pop(name, None)


def main() -> None:
    print_header("バックエンド(core,apps) 起動")
    ok, detail = check_environment()
    if not ok:
        print_error(f"環境が準備されていません: {detail}")
        print_info("  対応例: uv sync")
        sys.exit(1)
    print_success(f"環境確認: OK ({detail})")

    kill_ports()
    time.sleep(1)

    processes: dict[str, subprocess.Popen[bytes]] = {}
    try:
        processes["バックエンド(core)"] = start_core()
        processes["バックエンド(apps)"] = start_apps()
        for name, proc in processes.items():
            threading.Thread(target=_stream_output, args=(name, proc.stdout), daemon=True).start()
        print_success(f"バックエンド(core): http://localhost:{CORE_PORT}/docs")
        print_success(f"バックエンド(apps): http://localhost:{APPS_PORT}/docs")
        print_info("Ctrl+C で停止します")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print_header("停止処理")
        _stop(processes)
        print_success("停止しました")


if __name__ == "__main__":
    main()
