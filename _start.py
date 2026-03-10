# -*- coding: utf-8 -*-

"""開発環境起動スクリプト

バックエンド(core,apps)・フロントエンド(Web)・フロントエンド(Avatar)・
フロントエンド(GUI) の4系統を統一手順で起動します。

標準の起動順:
1. バックエンド(core,apps)
2. 落ち着き待機
3. フロントエンド(Avatar) を起動するか 5 秒確認
4. フロントエンド(GUI) を起動するか 5 秒確認
5. フロントエンド(Web)
6. 落ち着き待機
7. Web ページ表示
8. 自動再起動監視
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
import webbrowser
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


BACKEND_PATH = "backend_server"
BACKEND_CORE_PORT = 8091
BACKEND_APPS_PORT = 8092
BACKEND_CORE_APP = "core_main:app"
BACKEND_APPS_APP = "apps_main:app"
BACKEND_ENV_CANDIDATES = [".venv", "venv"]

FRONTEND_WEB_PATH = "frontend_web"
FRONTEND_WEB_PORT = 8090

FRONTEND_AVATAR_PATH = "frontend_avatar"
FRONTEND_AVATAR_PORT = 8099

FRONTEND_GUI_PATH = "frontend_gui"
FRONTEND_GUI_ENTRYPOINT = "main"
FRONTEND_GUI_ENV_CANDIDATES = [".venv", "venv"]

FRONTEND_COMMAND = "npm"
QUIET_WAIT_SECONDS = 15
QUIET_MAX_WAIT_SECONDS = 60
RESTART_WAIT_SECONDS = 15

BASE_DIR = Path(__file__).parent
BACKEND_DIR = BASE_DIR / BACKEND_PATH
FRONTEND_WEB_DIR = BASE_DIR / FRONTEND_WEB_PATH
FRONTEND_AVATAR_DIR = BASE_DIR / FRONTEND_AVATAR_PATH
FRONTEND_GUI_DIR = BASE_DIR / FRONTEND_GUI_PATH


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


def get_npm_command() -> str | None:
    candidates = [f"{FRONTEND_COMMAND}.cmd", FRONTEND_COMMAND] if sys.platform == "win32" else [FRONTEND_COMMAND]
    for candidate in candidates:
        try:
            subprocess.run([candidate, "--version"], capture_output=True, timeout=5, check=True)
            return candidate
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None


def get_backend_command(app_module: str, port: int) -> list[str]:
    backend_python = find_python_in_env(BACKEND_DIR, BACKEND_ENV_CANDIDATES)
    if backend_python is not None:
        return [str(backend_python), "-m", "uvicorn", app_module, "--host", "0.0.0.0", "--port", str(port)]
    return ["uv", "run", "uvicorn", app_module, "--host", "0.0.0.0", "--port", str(port)]


def get_gui_command() -> list[str]:
    gui_python = find_python_in_env(FRONTEND_GUI_DIR, FRONTEND_GUI_ENV_CANDIDATES)
    if gui_python is not None:
        return [str(gui_python), "-m", FRONTEND_GUI_ENTRYPOINT]
    return ["uv", "run", "python", "-m", FRONTEND_GUI_ENTRYPOINT]


def check_backend_environment() -> tuple[bool, str]:
    if not BACKEND_DIR.exists():
        return False, f"フォルダが見つかりません: {BACKEND_DIR}"
    if not (BACKEND_DIR / "pyproject.toml").exists():
        return False, f"pyproject.toml が見つかりません: {BACKEND_DIR / 'pyproject.toml'}"
    backend_python = find_python_in_env(BACKEND_DIR, BACKEND_ENV_CANDIDATES)
    if backend_python is not None:
        return True, str(backend_python)
    if check_command_exists("uv"):
        return True, "uv"
    return False, f"Python 仮想環境 ({' / '.join(BACKEND_ENV_CANDIDATES)}) または uv が見つかりません"


def check_npm_project_environment(project_dir: Path) -> tuple[bool, str]:
    package_json = project_dir / "package.json"
    if not project_dir.exists():
        return False, f"フォルダが見つかりません: {project_dir}"
    if not package_json.exists():
        return False, f"package.json が見つかりません: {package_json}"
    node_modules = project_dir / "node_modules"
    if not node_modules.exists() or not node_modules.is_dir():
        return False, f"node_modules が見つかりません: {node_modules}"
    try:
        if not any(node_modules.iterdir()):
            return False, f"node_modules が空です: {node_modules}"
    except Exception as exc:
        return False, f"node_modules の確認でエラー: {exc}"
    return True, str(node_modules)


def check_gui_environment() -> tuple[bool, str]:
    if not FRONTEND_GUI_DIR.exists():
        return False, f"フォルダが見つかりません: {FRONTEND_GUI_DIR}"
    if not (FRONTEND_GUI_DIR / "pyproject.toml").exists():
        return False, f"pyproject.toml が見つかりません: {FRONTEND_GUI_DIR / 'pyproject.toml'}"
    gui_python = find_python_in_env(FRONTEND_GUI_DIR, FRONTEND_GUI_ENV_CANDIDATES)
    if gui_python is not None:
        return True, str(gui_python)
    if check_command_exists("uv"):
        return True, "uv"
    return False, f"Python 仮想環境 ({' / '.join(FRONTEND_GUI_ENV_CANDIDATES)}) または uv が見つかりません"


def _listening_pids_windows(port: int) -> list[str]:
    result = subprocess.run(
        ["netstat", "-ano", "-p", "tcp"],
        capture_output=True,
        text=True,
        timeout=5,
    )
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
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode in (0, 1):
            pids = {pid.strip() for pid in result.stdout.splitlines() if pid.strip().isdigit()}
            return sorted(pids, key=int)
    except FileNotFoundError:
        pass

    try:
        result = subprocess.run(
            ["ss", "-ltnp", f"sport = :{port}"],
            capture_output=True,
            text=True,
            timeout=5,
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
            killer = lambda pid: subprocess.run(
                ["taskkill", "/F", "/T", "/PID", pid],
                capture_output=True,
                text=True,
                timeout=8,
            )
        else:
            finder = _listening_pids_linux
            killer = lambda pid: subprocess.run(
                ["kill", "-9", pid],
                capture_output=True,
                text=True,
                timeout=5,
            )

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


def start_backend_core() -> subprocess.Popen[bytes]:
    return launch_process("バックエンド(core)", get_backend_command(BACKEND_CORE_APP, BACKEND_CORE_PORT), BACKEND_DIR)


def start_backend_apps() -> subprocess.Popen[bytes]:
    return launch_process("バックエンド(apps)", get_backend_command(BACKEND_APPS_APP, BACKEND_APPS_PORT), BACKEND_DIR)


def start_frontend_web(npm_command: str) -> subprocess.Popen[bytes]:
    return launch_process(
        "フロントエンド(Web)",
        [npm_command, "run", "dev", "--", "--port", str(FRONTEND_WEB_PORT)],
        FRONTEND_WEB_DIR,
    )


def start_frontend_avatar(npm_command: str) -> subprocess.Popen[bytes]:
    return launch_process("フロントエンド(Avatar)", [npm_command, "run", "dev"], FRONTEND_AVATAR_DIR)


def start_frontend_gui() -> subprocess.Popen[bytes]:
    return launch_process("フロントエンド(GUI)", get_gui_command(), FRONTEND_GUI_DIR)


def stream_output(name: str, stream, last_output_times: dict[str, float]) -> None:
    if stream is None:
        return
    try:
        while True:
            chunk = stream.read(1024)
            if not chunk:
                break
            last_output_times[name] = time.time()
            text = chunk.decode("utf-8", errors="replace")
            for line in text.splitlines(keepends=True):
                sys.stdout.write(f"{Colors.OKCYAN}[{name}]{Colors.ENDC} {line}")
            sys.stdout.flush()
    except Exception:
        pass


def attach_output_thread(name: str, process: subprocess.Popen[bytes], last_output_times: dict[str, float]) -> None:
    last_output_times[name] = time.time()
    thread = threading.Thread(target=stream_output, args=(name, process.stdout, last_output_times), daemon=True)
    thread.start()


def wait_for_services_quiet(
    last_output_times: dict[str, float],
    names: list[str],
    seconds: int = QUIET_WAIT_SECONDS,
    max_wait: int = QUIET_MAX_WAIT_SECONDS,
    label: str | None = None,
) -> None:
    label_text = label or ", ".join(names)
    print_header(f"{label_text} 落ち着き待機")
    start_time = time.time()

    while True:
        now = time.time()
        quiet = True
        for name in names:
            last_time = last_output_times.get(name, start_time)
            if now - last_time < seconds:
                quiet = False
                break

        if quiet:
            print_success(f"{label_text} は {seconds} 秒間安定しました")
            return

        if now - start_time >= max_wait:
            print_warning(f"{label_text} は安定待機を {max_wait} 秒で打ち切りました")
            return

        time.sleep(0.5)


def clear_keyboard_buffer() -> None:
    if sys.platform != "win32":
        return
    while msvcrt.kbhit():
        key = msvcrt.getch()
        if key in (b"\x00", b"\xe0") and msvcrt.kbhit():
            msvcrt.getch()


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


def prompt_choice(question: str, default_yes: bool) -> bool:
    bracket = "[y]/n" if default_yes else "y/[n]"
    print(f"{Colors.FAIL}{question} {bracket}{Colors.ENDC}", end="  ", flush=True)

    if sys.platform == "win32":
        clear_keyboard_buffer()
        while True:
            if msvcrt.kbhit():
                key = msvcrt.getch()
                result = default_yes if key not in (b"y", b"Y", b"n", b"N") else key in (b"y", b"Y")
                print(key.decode("ascii", errors="replace"))
                return result
            time.sleep(0.05)

    v = input().strip().lower()
    if v in ("y", "n"):
        return v == "y"
    return default_yes


def collect_startup_choices() -> tuple[bool, bool, bool, bool]:
    print_header("起動条件の確認")
    backend_enabled = prompt_choice("バックエンド(core,apps) 起動しますか?", default_yes=True)
    web_enabled     = prompt_choice("フロントエンド(Web)      起動しますか?", default_yes=True)
    avatar_enabled  = prompt_choice("フロントエンド(Avatar)   起動しますか?", default_yes=False)
    gui_enabled     = prompt_choice("フロントエンド(GUI)      起動しますか?", default_yes=False)
    return backend_enabled, web_enabled, avatar_enabled, gui_enabled


def open_browser(port: int) -> None:
    print_header("ページ表示")
    url = f"http://localhost:{port}"
    try:
        webbrowser.open(url)
        print_success(f"ブラウザを開きました: {url}")
    except Exception as exc:
        print_warning(f"ブラウザを開けませんでした: {exc}")


def stop_processes(processes: dict[str, subprocess.Popen[bytes]]) -> None:
    for name, process in list(processes.items()):
        try:
            print_info(f"[{name}] 停止しています")
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                    capture_output=True,
                    timeout=5,
                )
            else:
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    time.sleep(0.5)
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass
                except PermissionError:
                    process.terminate()
                    time.sleep(0.5)
                    process.kill()

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



def validate_initial_environment(
    backend_enabled: bool,
    web_enabled: bool,
    avatar_enabled: bool,
    gui_enabled: bool,
) -> tuple[bool, str | None]:
    print_header("環境確認")
    has_error = False
    npm_command = get_npm_command()

    if backend_enabled:
        ok, detail = check_backend_environment()
        if ok:
            print_success(f"バックエンド(core,apps): OK ({detail})")
        else:
            print_error(f"バックエンド(core,apps): 未準備 ({detail})")
            print_info(f"  対応例: cd {BACKEND_PATH} && uv sync")
            has_error = True

    if web_enabled or avatar_enabled:
        if npm_command is None:
            print_error("npm コマンドが見つかりません (Node.js をインストールしてください)")
            has_error = True
        else:
            print_success(f"npm: OK ({npm_command})")

    if web_enabled:
        ok, detail = check_npm_project_environment(FRONTEND_WEB_DIR)
        if ok:
            print_success(f"フロントエンド(Web): OK")
        else:
            print_error(f"フロントエンド(Web): 未準備 ({detail})")
            print_info(f"  対応例: cd {FRONTEND_WEB_PATH} && {(npm_command or FRONTEND_COMMAND)} install")
            has_error = True

    if avatar_enabled:
        ok, detail = check_npm_project_environment(FRONTEND_AVATAR_DIR)
        if ok:
            print_success(f"フロントエンド(Avatar): OK")
        else:
            print_error(f"フロントエンド(Avatar): 未準備 ({detail})")
            print_info(f"  対応例: cd {FRONTEND_AVATAR_PATH} && {(npm_command or FRONTEND_COMMAND)} install")
            has_error = True

    if gui_enabled:
        ok, detail = check_gui_environment()
        if ok:
            print_success(f"フロントエンド(GUI): OK")
        else:
            print_error(f"フロントエンド(GUI): 未準備 ({detail})")
            print_info(f"  対応例: cd {FRONTEND_GUI_PATH} && uv sync")
            has_error = True

    return (not has_error), npm_command


def ensure_optional_service_ready(name: str, npm_command: str | None) -> bool:
    if name == "フロントエンド(Avatar)":
        if npm_command is None:
            print_warning(f"{name}: npm コマンドが見つからないため起動をスキップします")
            print_info("  対応例: Node.js をインストールしてください")
            return False
        ok, detail = check_npm_project_environment(FRONTEND_AVATAR_DIR)
        if ok:
            print_success(f"{name}: OK ({detail})")
            return True
        print_warning(f"{name}: 未準備のため起動をスキップします ({detail})")
        print_info(f"  対応例: cd {FRONTEND_AVATAR_PATH}")
        print_info(f"  対応例: {get_npm_command() or FRONTEND_COMMAND} install")
        return False

    ok, detail = check_gui_environment()
    if ok:
        print_success(f"{name}: OK ({detail})")
        return True
    print_warning(f"{name}: 未準備のため起動をスキップします ({detail})")
    print_info(f"  対応例: cd {FRONTEND_GUI_PATH}")
    print_info("  対応例: uv sync")
    return False


def start_service(
    name: str,
    processes: dict[str, subprocess.Popen[bytes]],
    last_output_times: dict[str, float],
    npm_command: str | None,
) -> bool:
    try:
        if name == "バックエンド(core)":
            process = start_backend_core()
        elif name == "バックエンド(apps)":
            process = start_backend_apps()
        elif name == "フロントエンド(Web)":
            if npm_command is None:
                print_error("フロントエンド(Web): npm コマンドが見つかりません")
                return False
            process = start_frontend_web(npm_command)
        elif name == "フロントエンド(Avatar)":
            if npm_command is None:
                print_error("フロントエンド(Avatar): npm コマンドが見つかりません")
                return False
            process = start_frontend_avatar(npm_command)
        elif name == "フロントエンド(GUI)":
            process = start_frontend_gui()
        else:
            print_error(f"未対応のサービスです: {name}")
            return False
    except Exception as exc:
        print_error(f"[{name}] 起動に失敗しました: {exc}")
        return False

    processes[name] = process
    attach_output_thread(name, process, last_output_times)
    return True


def maybe_kill_initial_ports(
    backend_enabled: bool,
    web_enabled: bool,
    avatar_enabled: bool,
) -> None:
    print_header("既存プロセス整理")
    if backend_enabled:
        kill_process_on_port(BACKEND_CORE_PORT)
        kill_process_on_port(BACKEND_APPS_PORT)
    if web_enabled:
        kill_process_on_port(FRONTEND_WEB_PORT)
    if avatar_enabled:
        kill_process_on_port(FRONTEND_AVATAR_PORT)
    time.sleep(1)


def start_initial_services(
    start_backend_enabled: bool,
    avatar_enabled: bool,
    gui_enabled: bool,
    web_enabled: bool,
    processes: dict[str, subprocess.Popen[bytes]],
    last_output_times: dict[str, float],
    npm_command: str | None,
) -> dict[str, bool]:
    selected_flags = {
        "バックエンド(core)": start_backend_enabled,
        "バックエンド(apps)": start_backend_enabled,
        "フロントエンド(Web)": web_enabled,
        "フロントエンド(Avatar)": False,
        "フロントエンド(GUI)": False,
    }

    maybe_kill_initial_ports(
        backend_enabled=start_backend_enabled,
        web_enabled=web_enabled,
        avatar_enabled=avatar_enabled,
    )

    if start_backend_enabled:
        print_header("バックエンド(core) 起動")
        start_service("バックエンド(core)", processes, last_output_times, npm_command)
        wait_for_services_quiet(last_output_times, ["バックエンド(core)"], label="バックエンド(core)")

        print_header("バックエンド(apps) 起動")
        start_service("バックエンド(apps)", processes, last_output_times, npm_command)
        wait_for_services_quiet(last_output_times, ["バックエンド(apps)"], label="バックエンド(apps)")

    if avatar_enabled and ensure_optional_service_ready("フロントエンド(Avatar)", npm_command):
        selected_flags["フロントエンド(Avatar)"] = True
        kill_process_on_port(FRONTEND_AVATAR_PORT)
        print_header("フロントエンド(Avatar) 起動")
        start_service("フロントエンド(Avatar)", processes, last_output_times, npm_command)
        wait_for_services_quiet(last_output_times, ["フロントエンド(Avatar)"], label="フロントエンド(Avatar)")

    if gui_enabled and ensure_optional_service_ready("フロントエンド(GUI)", npm_command):
        selected_flags["フロントエンド(GUI)"] = True
        print_header("フロントエンド(GUI) 起動")
        start_service("フロントエンド(GUI)", processes, last_output_times, npm_command)
        wait_for_services_quiet(last_output_times, ["フロントエンド(GUI)"], label="フロントエンド(GUI)")

    if web_enabled:
        print_header("フロントエンド(Web) 起動")
        if start_service("フロントエンド(Web)", processes, last_output_times, npm_command):
            wait_for_services_quiet(last_output_times, ["フロントエンド(Web)"], label="フロントエンド(Web)")
            open_browser(FRONTEND_WEB_PORT)

    return selected_flags


def monitor_and_restart(
    selected_services: dict[str, bool],
    processes: dict[str, subprocess.Popen[bytes]],
    last_output_times: dict[str, float],
    npm_command: str | None,
) -> None:
    print_header("自動再起動監視")
    print_info(f"監視対象: {', '.join(name for name, enabled in selected_services.items() if enabled) or 'なし'}")
    print_info(f"停止検出時は {RESTART_WAIT_SECONDS} 秒後に自動再起動します")
    print_info("Ctrl+C で停止します")

    process_crash_time: dict[str, float] = {}
    port_map = {
        "バックエンド(core)": BACKEND_CORE_PORT,
        "バックエンド(apps)": BACKEND_APPS_PORT,
        "フロントエンド(Web)": FRONTEND_WEB_PORT,
        "フロントエンド(Avatar)": FRONTEND_AVATAR_PORT,
    }

    while True:
        current_time = time.time()

        for name in list(processes.keys()):
            process = processes[name]
            if process.poll() is not None:
                print_warning(f"{name} が終了しました (終了コード: {process.returncode})")
                processes.pop(name, None)
                process_crash_time.setdefault(name, current_time)

        for name, enabled in selected_services.items():
            if not enabled or name in processes:
                continue

            crash_time = process_crash_time.get(name)
            if crash_time is None:
                process_crash_time[name] = current_time
                print_info(f"[{name}] {RESTART_WAIT_SECONDS} 秒後に再起動します")
                continue

            if current_time - crash_time < RESTART_WAIT_SECONDS:
                continue

            print_info(f"[{name}] 再起動を試みます")
            port = port_map.get(name)
            if port is not None:
                kill_process_on_port(port)
                time.sleep(1)

            if start_service(name, processes, last_output_times, npm_command):
                print_success(f"[{name}] 再起動しました")
                process_crash_time.pop(name, None)
            else:
                print_error(f"[{name}] 再起動に失敗しました。{RESTART_WAIT_SECONDS} 秒後に再試行します")
                process_crash_time[name] = current_time

        time.sleep(1)


def main() -> None:
    backend_enabled, web_enabled, avatar_enabled, gui_enabled = collect_startup_choices()

    is_ready, npm_command = validate_initial_environment(
        backend_enabled=backend_enabled,
        web_enabled=web_enabled,
        avatar_enabled=avatar_enabled,
        gui_enabled=gui_enabled,
    )
    if not is_ready:
        print()
        print_error("必要な環境が準備されていないため、起動を中止します")
        print_info("必要に応じて次を実行してください: python _setup.py")
        sys.exit(1)

    while True:
        print_header("開発環境起動")
        processes: dict[str, subprocess.Popen[bytes]] = {}
        last_output_times: dict[str, float] = {}
        reboot_requested = False

        try:
            selected_services = start_initial_services(
                start_backend_enabled=backend_enabled,
                avatar_enabled=avatar_enabled,
                gui_enabled=gui_enabled,
                web_enabled=web_enabled,
                processes=processes,
                last_output_times=last_output_times,
                npm_command=npm_command,
            )

            print_header("起動完了")
            if "バックエンド(core)" in processes:
                print_success(f"バックエンド(core): http://localhost:{BACKEND_CORE_PORT}/docs")
            if "バックエンド(apps)" in processes:
                print_success(f"バックエンド(apps): http://localhost:{BACKEND_APPS_PORT}/docs")
            if "フロントエンド(Web)" in processes:
                print_success(f"フロントエンド(Web): http://localhost:{FRONTEND_WEB_PORT}/")
            if "フロントエンド(Avatar)" in processes:
                print_success(f"フロントエンド(Avatar): renderer http://127.0.0.1:{FRONTEND_AVATAR_PORT}")
            if "フロントエンド(GUI)" in processes:
                print_success("フロントエンド(GUI): デスクトップアプリ起動中")

            monitor_and_restart(selected_services, processes, last_output_times, npm_command)

        except KeyboardInterrupt:
            print_header("停止処理")
            print_info("Ctrl+C を検出しました。起動中プロセスを停止します")
            stop_processes(processes)

            if sys.platform == "win32":
                clear_keyboard_buffer()
                print("\n\n")
                print(f"{Colors.FAIL}R を押すとリブートします (10秒以内){Colors.ENDC}")
                deadline = time.time() + 10
                while time.time() < deadline:
                    if is_r_pressed():
                        reboot_requested = True
                        print_info("リブートを開始します")
                        break
                    time.sleep(0.05)

        finally:
            stop_processes(processes)
            if reboot_requested:
                if sys.platform == "win32":
                    os.system("cls")
                continue

            print_header("停止完了")
            print_success("すべての対象サービスを停止しました")
            print_info("5秒後に終了します")
            time.sleep(5)
            break


if __name__ == "__main__":
    main()
