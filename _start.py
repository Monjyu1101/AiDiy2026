# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""開発環境起動スクリプト（まとめ役）

各フォルダの `_start.py` を import し、バックエンド(local/tools/core/apps/task)・
フロントエンド(Web/Avatar) を統一手順で起動します。各サービスの環境確認・
起動コマンドはフォルダ側に委譲し、このスクリプトは起動順序・出力集約・
ブラウザ表示・自動再起動監視・一括停止を一元管理します。

フォルダ別スクリプト:
- backend_local/_start.py    PORT / check_environment / start / kill_ports
- backend_tools/_start.py    PORT / check_environment / start / kill_ports
- backend_server/_start.py   CORE_PORT / APPS_PORT / check_environment / start_core / start_apps
- backend_task/_start.py     PORT / check_environment / start / kill_ports
- frontend_web/_start.py     PORT / check_environment / start / kill_ports
- frontend_avatar/_start.py  PORT / check_environment / start / kill_electron_processes

標準の起動順:
1. バックエンド(local)
2. バックエンド(tools)
3. バックエンド(core)
4. バックエンド(apps)
5. バックエンド(task)
6. フロントエンド(Web)
7. フロントエンド(Avatar)
8. ページ表示
9. 自動再起動監視
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
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


# ============================================================
# 設定
# ============================================================
BASE_DIR = Path(__file__).resolve().parent

FRONTEND_COMMAND = "npm"
QUIET_WAIT_SECONDS = 20
QUIET_MAX_WAIT_SECONDS = 60
RESTART_WAIT_SECONDS = 15
BACKEND_TOOLS_SHOW_AUTOMATION_BANNER = False

# フォルダ別 _start.py モジュール（_init_modules で設定）
LOCAL = TOOLS = SERVER = TASK = WEB = AVATAR = None


def _load_folder_module(folder: str):
    name = f"aidiy_{folder}_start"
    path = BASE_DIR / folder / "_start.py"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _init_modules() -> None:
    global LOCAL, TOOLS, SERVER, TASK, WEB, AVATAR
    LOCAL = _load_folder_module("backend_local")
    TOOLS = _load_folder_module("backend_tools")
    SERVER = _load_folder_module("backend_server")
    TASK = _load_folder_module("backend_task")
    WEB = _load_folder_module("frontend_web")
    AVATAR = _load_folder_module("frontend_avatar")


def get_npm_command() -> str | None:
    candidates = [f"{FRONTEND_COMMAND}.cmd", FRONTEND_COMMAND] if sys.platform == "win32" else [FRONTEND_COMMAND]
    for candidate in candidates:
        try:
            subprocess.run([candidate, "--version"], capture_output=True, timeout=5, check=True)
            return candidate
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None


# ============================================================
# ポート整理（監視・初期整理用）
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


# ============================================================
# 出力集約 / 安定待機
# ============================================================
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
    print_header(f"{label_text} 落ち着き待機 ({seconds}s)")
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


# ============================================================
# キー入力
# ============================================================
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


def collect_startup_choices() -> tuple[bool, bool, bool, bool, bool, bool]:
    print_header("起動条件の確認")
    local_enabled         = prompt_choice("バックエンド(local)     起動しますか?", default_yes=False)
    backend_tools_enabled = prompt_choice("バックエンド(tools)     起動しますか?", default_yes=True)
    backend_enabled       = prompt_choice("バックエンド(core,apps) 起動しますか?", default_yes=True)
    backend_task_enabled  = prompt_choice("バックエンド(task)      起動しますか?", default_yes=True)
    web_enabled           = prompt_choice("フロントエンド(Web)     起動しますか?", default_yes=True)
    avatar_enabled        = prompt_choice("フロントエンド(Avatar)  起動しますか?", default_yes=False)
    return local_enabled, backend_tools_enabled, backend_enabled, backend_task_enabled, web_enabled, avatar_enabled


# ============================================================
# ブラウザ表示
# ============================================================
def open_browser(port: int) -> None:
    print_header("ページ表示")
    url = f"http://localhost:{port}"
    try:
        webbrowser.open(url)
        print_success(f"ブラウザを開きました: {url}")
    except Exception as exc:
        print_warning(f"ブラウザを開けませんでした: {exc}")


def _tools_post(path: str, body: dict, timeout: int = 30) -> dict:
    """backend_tools の HTTP POST インターフェースを呼ぶ (urllib のみ使用)"""
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"http://localhost:{TOOLS.PORT}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def open_browser_via_tools(port: int) -> bool:
    print_header("ブラウザページ表示")
    url = f"http://localhost:{port}"
    try:
        _tools_post(
            "/aidiy_chrome_devtools/new_page",
            {"url": url, "show_automation_banner": BACKEND_TOOLS_SHOW_AUTOMATION_BANNER},
            timeout=60,
        )
        print_success(f"(tools) Chrome でページを開きました: {url}")
        return True
    except Exception as exc:
        print_warning(f"(tools) HTTP POST 経由でページを開けませんでした: {exc}")
        try:
            webbrowser.open(url)
        except Exception as exc2:
            print_warning(f"ブラウザを開けませんでした: {exc2}")
        return False


# ============================================================
# プロセス停止
# ============================================================
def stop_processes(processes: dict[str, subprocess.Popen[bytes]]) -> None:
    avatar_was_running = "フロントエンド(Avatar)" in processes
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

    # Avatar を起動していた場合は残留 Electron プロセスも終了する
    if avatar_was_running and AVATAR is not None:
        AVATAR.kill_electron_processes()


# ============================================================
# 環境確認 / サービス起動
# ============================================================
def validate_initial_environment(
    local_enabled: bool,
    backend_tools_enabled: bool,
    backend_enabled: bool,
    backend_task_enabled: bool,
    web_enabled: bool,
    avatar_enabled: bool,
) -> tuple[bool, str | None]:
    print_header("環境確認")
    has_error = False
    npm_command = get_npm_command()

    if local_enabled:
        ok, detail = LOCAL.check_environment()
        if ok:
            print_success(f"バックエンド(local): OK ({detail})")
        else:
            print_error(f"バックエンド(local): 未準備 ({detail})")
            print_info("  対応例: cd backend_local && uv sync --upgrade")
            has_error = True

    if backend_tools_enabled:
        ok, detail = TOOLS.check_environment()
        if ok:
            print_success(f"バックエンド(tools): OK ({detail})")
        else:
            print_error(f"バックエンド(tools): 未準備 ({detail})")
            print_info("  対応例: cd backend_tools && uv sync --upgrade")
            has_error = True

    if backend_enabled:
        ok, detail = SERVER.check_environment()
        if ok:
            print_success(f"バックエンド(core,apps): OK ({detail})")
        else:
            print_error(f"バックエンド(core,apps): 未準備 ({detail})")
            print_info("  対応例: cd backend_server && uv sync --upgrade")
            has_error = True

    if backend_task_enabled:
        ok, detail = TASK.check_environment()
        if ok:
            print_success(f"バックエンド(task): OK ({detail})")
        else:
            print_error(f"バックエンド(task): 未準備 ({detail})")
            print_info("  対応例: cd backend_task && uv sync --upgrade")
            has_error = True

    if web_enabled or avatar_enabled:
        if npm_command is None:
            print_error("npm コマンドが見つかりません (Node.js をインストールしてください)")
            has_error = True
        else:
            print_success(f"npm: OK ({npm_command})")

    if web_enabled:
        ok, detail = WEB.check_environment()
        if ok:
            print_success("フロントエンド(Web): OK")
        else:
            print_error(f"フロントエンド(Web): 未準備 ({detail})")
            print_info(f"  対応例: cd frontend_web && {(npm_command or FRONTEND_COMMAND)} install")
            has_error = True

    if avatar_enabled:
        ok, detail = AVATAR.check_environment()
        if ok:
            print_success("フロントエンド(Avatar): OK")
        else:
            print_error(f"フロントエンド(Avatar): 未準備 ({detail})")
            print_info(f"  対応例: cd frontend_avatar && {(npm_command or FRONTEND_COMMAND)} install")
            has_error = True

    return (not has_error), npm_command


def ensure_optional_service_ready(name: str, npm_command: str | None) -> bool:
    if npm_command is None:
        print_warning(f"{name}: npm コマンドが見つからないため起動をスキップします")
        print_info("  対応例: Node.js をインストールしてください")
        return False
    ok, detail = AVATAR.check_environment()
    if ok:
        print_success(f"{name}: OK ({detail})")
        return True
    print_warning(f"{name}: 未準備のため起動をスキップします ({detail})")
    print_info("  対応例: cd frontend_avatar")
    print_info(f"  対応例: {npm_command or FRONTEND_COMMAND} install")
    return False


def _port_for(name: str) -> int | None:
    return {
        "バックエンド(local)": LOCAL.PORT,
        "バックエンド(tools)": TOOLS.PORT,
        "バックエンド(core)": SERVER.CORE_PORT,
        "バックエンド(apps)": SERVER.APPS_PORT,
        "バックエンド(task)": TASK.PORT,
        "フロントエンド(Web)": WEB.PORT,
        "フロントエンド(Avatar)": AVATAR.PORT,
    }.get(name)


def start_service(
    name: str,
    processes: dict[str, subprocess.Popen[bytes]],
    last_output_times: dict[str, float],
    npm_command: str | None,
) -> bool:
    try:
        if name == "バックエンド(tools)":
            process = TOOLS.start()
        elif name == "バックエンド(local)":
            process = LOCAL.start()
        elif name == "バックエンド(task)":
            process = TASK.start()
        elif name == "バックエンド(core)":
            process = SERVER.start_core()
        elif name == "バックエンド(apps)":
            process = SERVER.start_apps()
        elif name == "フロントエンド(Web)":
            if npm_command is None:
                print_error("フロントエンド(Web): npm コマンドが見つかりません")
                return False
            process = WEB.start(npm_command)
        elif name == "フロントエンド(Avatar)":
            if npm_command is None:
                print_error("フロントエンド(Avatar): npm コマンドが見つかりません")
                return False
            process = AVATAR.start(npm_command)
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
    local_enabled: bool,
    backend_tools_enabled: bool,
    backend_enabled: bool,
    backend_task_enabled: bool,
    web_enabled: bool,
    avatar_enabled: bool,
) -> None:
    print_header("既存プロセス整理")
    if local_enabled:
        kill_process_on_port(LOCAL.PORT)
    if backend_tools_enabled:
        kill_process_on_port(TOOLS.PORT)
    if backend_enabled:
        kill_process_on_port(SERVER.CORE_PORT)
        kill_process_on_port(SERVER.APPS_PORT)
    if backend_task_enabled:
        kill_process_on_port(TASK.PORT)
    if web_enabled:
        kill_process_on_port(WEB.PORT)
    if avatar_enabled:
        kill_process_on_port(AVATAR.PORT)
        # electronmon が spawn した electron.exe は別プロセスグループで残留する場合があるため
        AVATAR.kill_electron_processes()
    time.sleep(1)


def start_initial_services(
    start_backend_local_enabled: bool,
    start_backend_tools_enabled: bool,
    start_backend_enabled: bool,
    start_backend_task_enabled: bool,
    avatar_enabled: bool,
    web_enabled: bool,
    processes: dict[str, subprocess.Popen[bytes]],
    last_output_times: dict[str, float],
    npm_command: str | None,
) -> dict[str, bool]:
    selected_flags = {
        "バックエンド(local)": start_backend_local_enabled,
        "バックエンド(tools)": start_backend_tools_enabled,
        "バックエンド(core)": start_backend_enabled,
        "バックエンド(apps)": start_backend_enabled,
        "バックエンド(task)": start_backend_task_enabled,
        "フロントエンド(Web)": web_enabled,
        "フロントエンド(Avatar)": False,
    }

    maybe_kill_initial_ports(
        local_enabled=start_backend_local_enabled,
        backend_tools_enabled=start_backend_tools_enabled,
        backend_enabled=start_backend_enabled,
        backend_task_enabled=start_backend_task_enabled,
        web_enabled=web_enabled,
        avatar_enabled=avatar_enabled,
    )

    if start_backend_local_enabled:
        print_header("バックエンド(local) 起動")
        start_service("バックエンド(local)", processes, last_output_times, npm_command)
        wait_for_services_quiet(last_output_times, ["バックエンド(local)"], label="バックエンド(local)")

    if start_backend_tools_enabled:
        print_header("バックエンド(tools) 起動")
        start_service("バックエンド(tools)", processes, last_output_times, npm_command)
        wait_for_services_quiet(last_output_times, ["バックエンド(tools)"], label="バックエンド(tools)")

    if start_backend_enabled:
        print_header("バックエンド(core) 起動")
        start_service("バックエンド(core)", processes, last_output_times, npm_command)
        wait_for_services_quiet(last_output_times, ["バックエンド(core)"], label="バックエンド(core)")

        print_header("バックエンド(apps) 起動")
        start_service("バックエンド(apps)", processes, last_output_times, npm_command)
        wait_for_services_quiet(last_output_times, ["バックエンド(apps)"], label="バックエンド(apps)")

    if start_backend_task_enabled:
        print_header("バックエンド(task) 起動")
        start_service("バックエンド(task)", processes, last_output_times, npm_command)
        wait_for_services_quiet(last_output_times, ["バックエンド(task)"], label="バックエンド(task)")

    if web_enabled:
        print_header("フロントエンド(Web) 起動")
        if start_service("フロントエンド(Web)", processes, last_output_times, npm_command):
            wait_for_services_quiet(last_output_times, ["フロントエンド(Web)"], label="フロントエンド(Web)")

    if avatar_enabled and ensure_optional_service_ready("フロントエンド(Avatar)", npm_command):
        selected_flags["フロントエンド(Avatar)"] = True
        kill_process_on_port(AVATAR.PORT)
        print_header("フロントエンド(Avatar) 起動")
        start_service("フロントエンド(Avatar)", processes, last_output_times, npm_command)
        wait_for_services_quiet(last_output_times, ["フロントエンド(Avatar)"], label="フロントエンド(Avatar)")

    if web_enabled and "フロントエンド(Web)" in processes:
        if not (start_backend_tools_enabled and "バックエンド(tools)" in processes and open_browser_via_tools(WEB.PORT)):
            open_browser(WEB.PORT)

    if avatar_enabled and "フロントエンド(Avatar)" in processes:
        if not (start_backend_tools_enabled and "バックエンド(tools)" in processes and open_browser_via_tools(AVATAR.PORT)):
            open_browser(AVATAR.PORT)

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
            port = _port_for(name)
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
    _init_modules()

    local_enabled, backend_tools_enabled, backend_enabled, backend_task_enabled, web_enabled, avatar_enabled = collect_startup_choices()

    is_ready, npm_command = validate_initial_environment(
        local_enabled=local_enabled,
        backend_tools_enabled=backend_tools_enabled,
        backend_enabled=backend_enabled,
        backend_task_enabled=backend_task_enabled,
        web_enabled=web_enabled,
        avatar_enabled=avatar_enabled,
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
                start_backend_local_enabled=local_enabled,
                start_backend_tools_enabled=backend_tools_enabled,
                start_backend_enabled=backend_enabled,
                start_backend_task_enabled=backend_task_enabled,
                avatar_enabled=avatar_enabled,
                web_enabled=web_enabled,
                processes=processes,
                last_output_times=last_output_times,
                npm_command=npm_command,
            )

            print_header("起動完了")
            if "バックエンド(local)" in processes:
                print_success(f"バックエンド(local): http://localhost:{LOCAL.PORT}/docs")
                print_info   (f"  OpenAI互換 (利用時にモデルロード): http://localhost:{LOCAL.PORT}/v1/chat/completions")
            if "バックエンド(tools)" in processes:
                print_success(f"バックエンド(tools) Swagger UI : http://localhost:{TOOLS.PORT}/docs")
                print_info   (f"  ツール一覧(例)            : http://localhost:{TOOLS.PORT}/aidiy_text_to_speech/list")
                print_info   (f"  利用可能 ツール 一覧      : http://localhost:{TOOLS.PORT}/")
            if "バックエンド(core)" in processes:
                print_success(f"バックエンド(core): http://localhost:{SERVER.CORE_PORT}/docs")
            if "バックエンド(apps)" in processes:
                print_success(f"バックエンド(apps): http://localhost:{SERVER.APPS_PORT}/docs")
            if "バックエンド(task)" in processes:
                print_success(f"バックエンド(task): http://localhost:{TASK.PORT}/docs")
            if "フロントエンド(Web)" in processes:
                print_success(f"フロントエンド(Web): http://localhost:{WEB.PORT}/")
            if "フロントエンド(Avatar)" in processes:
                print_success(f"フロントエンド(Avatar): renderer http://127.0.0.1:{AVATAR.PORT}")
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
