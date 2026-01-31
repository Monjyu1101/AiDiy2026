# -*- coding: utf-8 -*-

"""開発環境起動スクリプト

バックエンドサーバーとフロントエンド開発サーバーを同時起動します。

Usage:
    python start.py
    python start.py --backend=no --frontend=yes
    python start.py --backend=yes --frontend=no

Ctrl+Cで両方のサーバーを停止します。
"""

import argparse
import subprocess
import sys
import time
import webbrowser
import locale
import threading
from pathlib import Path

if sys.platform == "win32":
    import msvcrt
    import os

# 色付き出力用
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
    """ヘッダーメッセージを表示"""
    print(f"\n{Colors.HEADER}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{message}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'=' * 60}{Colors.ENDC}\n")


def print_success(message):
    """成功メッセージを表示"""
    print(f"{Colors.OKBLUE}[OK] {message}{Colors.ENDC}")


def print_error(message):
    """エラーメッセージを表示"""
    print(f"{Colors.FAIL}[NG] {message}{Colors.ENDC}")


def print_warning(message):
    """警告メッセージを表示"""
    print(f"{Colors.WARNING}[WARN] {message}{Colors.ENDC}")


def print_info(message):
    """情報メッセージを表示"""
    print(f"{Colors.OKGREEN}[INFO] {message}{Colors.ENDC}")



# ============================================================
# プロジェクト設定
# ============================================================
# バックエンド設定
BACKEND_PATH = "backend_server"           # バックエンドフォルダ名
BACKEND_CORE_PORT = 8091                  # coreサーバーポート番号
BACKEND_APPS_PORT = 8092                  # appsサーバーポート番号
BACKEND_CORE_APP = "main1:app"            # coreサーバーアプリケーションモジュール
BACKEND_APPS_APP = "main2:app"            # appsサーバーアプリケーションモジュール
BACKEND_ENV_CANDIDATES = [".venv", "venv"]  # venv フォルダ候補 (優先順)

# フロントエンド設定
FRONTEND_PATH = "frontend_server"    # フロントエンドフォルダパス
FRONTEND_PORT = 8090                 # フロントエンドポート番号
FRONTEND_COMMAND = "npm"             # パッケージマネージャ: "npm" or "pnpm" or "yarn"

# ============================================================

# プロジェクトルート
BASE_DIR = Path(__file__).parent

# バックエンド側のディレクトリ
SERVER_DIR = BASE_DIR / BACKEND_PATH
# フロントエンド側のディレクトリ
CLIENT_DIR = BASE_DIR / FRONTEND_PATH


def find_venv_python():
    """venv の python 実行ファイルを探す"""
    for env_name in BACKEND_ENV_CANDIDATES:
        if sys.platform == "win32":
            venv_python = SERVER_DIR / env_name / "Scripts" / "python.exe"
        else:
            venv_python = SERVER_DIR / env_name / "bin" / "python"
        if venv_python.exists():
            return venv_python
    return None


def get_backend_command(app_module: str, port: int):
    """バックエンド起動コマンドを取得 (venv優先、無ければuv)"""
    venv_python = find_venv_python()
    if venv_python:
        return [str(venv_python), "-m", "uvicorn", app_module,
                "--port", str(port)]

    return ["uv", "run", "uvicorn", app_module,
            "--port", str(port)]


def kill_process_on_port(port: int) -> bool:
    """指定ポートを使用しているプロセスを強制停止"""
    print_info(f"[ポート {port}] 使用中のプロセスを検索...")
    
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        pid = None
        for line in result.stdout.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    break
        
        if pid and pid != "0":
            print_info(f"[ポート {port}] プロセス検出: PID={pid}")
            subprocess.run(
                ["taskkill", "/F", "/PID", pid],
                capture_output=True,
                timeout=5
            )
            print_success(f"[ポート {port}] プロセスを強制停止しました")
            return True
        else:
            print_info(f"[ポート {port}] 使用中のプロセスなし")
            return False
            
    except Exception as e:
        print_error(f"[ポート {port}] エラー: {e}")
        return False


def start_backend(app_module: str, port: int, label: str):
    """バックエンドサーバーを起動"""
    print_info(f"作業ディレクトリ: {SERVER_DIR}")
    
    cmd = get_backend_command(app_module, port)
    print_info(f"コマンド: {' '.join(cmd)}")
    
    process = subprocess.Popen(
        cmd,
        cwd=str(SERVER_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # stderrをstdoutにマージ
        bufsize=0,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    )
    
    print_success(f"{label} 起動完了 (http://localhost:{port})")
    return process


def start_frontend():
    """フロントエンド開発サーバーを起動"""
    print_info(f"作業ディレクトリ: {CLIENT_DIR}")
    print_info(f"コマンド: {FRONTEND_COMMAND} run dev -- --port {FRONTEND_PORT}")
    
    cmd = f"{FRONTEND_COMMAND}.cmd" if sys.platform == "win32" else FRONTEND_COMMAND
    process = subprocess.Popen(
        [cmd, "run", "dev", "--", "--port", str(FRONTEND_PORT)],
        cwd=str(CLIENT_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # stderrをstdoutにマージ
        bufsize=0,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    )
    
    print_success(f"フロントエンド起動完了 (http://localhost:{FRONTEND_PORT})")
    return process


def open_browser(frontend_port):
    """ブラウザでフロントエンドを開く"""
    print_header("ブラウザを起動")
    try:
        webbrowser.open(f"http://localhost:{frontend_port}")
        print_success(f"ブラウザ起動完了 (http://localhost:{frontend_port})")
    except Exception as e:
        print_warning(f"ブラウザ起動エラー: {e}")


def stream_output_backend(name, stream, label, last_output_times):
    """バックエンドプロセスの出力をストリーム表示（CP932エンコーディング）"""
    if stream is None:
        return
    
    encoding = 'cp932' if sys.platform == "win32" else 'utf-8'

    try:
        while True:
            chunk = stream.read(1024)
            if not chunk:
                break

            if last_output_times is not None:
                last_output_times[name] = time.time()

            try:
                text = chunk.decode(encoding, errors="replace")
            except Exception:
                text = str(chunk)
            for line in text.splitlines(keepends=True):
                sys.stdout.write(f"{Colors.OKCYAN}[{name}]{Colors.ENDC} {line}")
            sys.stdout.flush()
    except Exception:
        pass


def stream_output_frontend(name, stream, label, last_output_times):
    """フロントエンドプロセスの出力をストリーム表示（UTF-8エンコーディング）"""
    if stream is None:
        return
    
    encoding = 'utf-8'

    try:
        while True:
            chunk = stream.read(1024)
            if not chunk:
                break

            if last_output_times is not None:
                last_output_times[name] = time.time()

            try:
                text = chunk.decode(encoding, errors="replace")
            except Exception:
                text = str(chunk)
            for line in text.splitlines(keepends=True):
                sys.stdout.write(f"{Colors.OKCYAN}[{name}]{Colors.ENDC} {line}")
            sys.stdout.flush()
    except Exception:
        pass


def wait_for_quiet(last_output_times, key, seconds=5, max_wait=60):
    """メッセージが途切れるまで待機（最終出力からN秒静か）"""
    start_time = time.time()
    while True:
        last_time = last_output_times.get(key)
        if last_time is None:
            if time.time() - start_time >= max_wait:
                print_warning(f"{key} からの出力がないままタイムアウト({max_wait}秒)")
                break
        else:
            if time.time() - last_time >= seconds:
                print_success(f"{key} が{seconds}秒間安定しました")
                break
        
        if time.time() - start_time >= max_wait:
            print_warning(f"{key} の出力が安定しないままタイムアウト({max_wait}秒)")
            break
        
        time.sleep(0.5)

def is_r_pressed():
    """r/Rが押されたかを判定（Windowsのみ）"""
    if sys.platform != "win32":
        return False
    if not msvcrt.kbhit():
        return False
    key = msvcrt.getch()
    if key in (b"\x00", b"\xe0"):  # 特殊キーのプレフィックス
        if msvcrt.kbhit():
            msvcrt.getch()
        return False
    return key in (b"r", b"R")

def stop_processes(processes):
    """起動中プロセスを停止"""
    for name, process in list(processes.items()):
        try:
            print_info(f"[{name}] プロセスを終了中...")
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                    capture_output=True,
                    timeout=5
                )
            else:
                process.terminate()

            try:
                process.wait(timeout=5)
                print_success(f"[{name}] 正常終了")
            except subprocess.TimeoutExpired:
                print_warning(f"[{name}] タイムアウト - 強制終了します")
                process.kill()
                process.wait()
                print_success(f"[{name}] 強制終了完了")
        except Exception as e:
            print_error(f"[{name}] 終了エラー: {e}")
        finally:
            processes.pop(name, None)


def main():
    # パラメータなし: 両方起動（default="yes"）
    # パラメータあり: yes指定のみ起動（default="no"）
    has_params = len(sys.argv) > 1
    default_value = "no" if has_params else "yes"

    parser = argparse.ArgumentParser(description="開発環境を起動します")
    parser.add_argument("--backend", default=default_value, choices=["yes", "no"], help="バックエンド起動 (yes/no)")
    parser.add_argument("--frontend", default=default_value, choices=["yes", "no"], help="フロントエンド起動 (yes/no)")
    args = parser.parse_args()
    start_backend_enabled = args.backend == "yes"
    start_frontend_enabled = args.frontend == "yes"

    if not start_backend_enabled and not start_frontend_enabled:
        print_warning("起動対象が指定されていません (backend=no, frontend=no)")
        sys.exit(0)

    def start_selected_services(processes, last_output_times, open_browser_enabled: bool = True):
        # 1) ポート確認と既存プロセスの停止
        print_info("既存プロセスの停止を確認中...")
        if start_frontend_enabled:
            kill_process_on_port(FRONTEND_PORT)
        if start_backend_enabled:
            kill_process_on_port(BACKEND_CORE_PORT)
            kill_process_on_port(BACKEND_APPS_PORT)
        time.sleep(1)

        # 2) バックエンドサーバー起動 & 待機
        if start_backend_enabled:
            print_header("バックエンド(core) 起動")
            core_process = start_backend(BACKEND_CORE_APP, BACKEND_CORE_PORT, "バックエンド(core)")
            if core_process:
                processes["バックエンド(core)"] = core_process
                thread_out = threading.Thread(
                    target=stream_output_backend,
                    args=("バックエンド(core)", core_process.stdout, "out", last_output_times),
                    daemon=True
                )
                thread_out.start()
                wait_for_quiet(last_output_times, "バックエンド(core)")

            print_header("バックエンド(apps) 起動")
            apps_process = start_backend(BACKEND_APPS_APP, BACKEND_APPS_PORT, "バックエンド(apps)")
            if apps_process:
                processes["バックエンド(apps)"] = apps_process
                thread_out = threading.Thread(
                    target=stream_output_backend,
                    args=("バックエンド(apps)", apps_process.stdout, "out", last_output_times),
                    daemon=True
                )
                thread_out.start()
                wait_for_quiet(last_output_times, "バックエンド(apps)")

        # 3) フロントエンド開発サーバー起動 & 待機
        if start_frontend_enabled:
            print_header("フロントエンド 起動")
            frontend_process = start_frontend()
            if frontend_process:
                processes["フロントエンド"] = frontend_process
                thread_out = threading.Thread(
                    target=stream_output_frontend,
                    args=("フロントエンド", frontend_process.stdout, "out", last_output_times),
                    daemon=True
                )
                thread_out.start()
                wait_for_quiet(last_output_times, "フロントエンド")

        # 4) ブラウザ起動
        if start_frontend_enabled and open_browser_enabled:
            open_browser(FRONTEND_PORT)

    while True:
        print_header("開発環境を起動します")
        processes = {}
        last_output_times = {}
        reboot_requested = False

        try:
            start_selected_services(processes, last_output_times, open_browser_enabled=True)

            print_header("起動完了")
            if start_backend_enabled:
                print_success(f"バックエンド(core) : http://localhost:{BACKEND_CORE_PORT}/docs")
                print_success(f"バックエンド(apps) : http://localhost:{BACKEND_APPS_PORT}/docs")
            if start_frontend_enabled:
                print_success(f"フロントエンド     : http://localhost:{FRONTEND_PORT}/")
            print_info("プロセス停止時は15秒後に自動再起動します")
            print_info("Ctrl+Cで停止します")

            # 監視・再起動ループ (Ctrl-C待ち)
            last_restart_attempt = {"バックエンド(core)": 0, "バックエンド(apps)": 0, "フロントエンド": 0}

            while True:
                current_time = time.time()

                for name in list(processes.keys()):
                    process = processes[name]
                    if process.poll() is not None:
                        exit_code = process.returncode
                        print_warning(f"{name} が終了しました (終了コード: {exit_code})")
                        del processes[name]

                if start_backend_enabled and "バックエンド(core)" not in processes:
                    if current_time - last_restart_attempt["バックエンド(core)"] >= 15:
                        print_info("[バックエンド(core)] 15秒後に再起動します...")
                        time.sleep(15)
                        print_info("[バックエンド(core)] 起動を試みます...")
                        new_process = start_backend(BACKEND_CORE_APP, BACKEND_CORE_PORT, "バックエンド(core)")
                        if new_process:
                            processes["バックエンド(core)"] = new_process
                            thread_out = threading.Thread(target=stream_output_backend, args=("バックエンド(core)", new_process.stdout, "out", last_output_times), daemon=True)
                            thread_out.start()
                            print_success("[バックエンド(core)] 起動成功")
                        else:
                            print_error("[バックエンド(core)] 起動失敗")
                        last_restart_attempt["バックエンド(core)"] = time.time()

                if start_backend_enabled and "バックエンド(apps)" not in processes:
                    if current_time - last_restart_attempt["バックエンド(apps)"] >= 15:
                        print_info("[バックエンド(apps)] 15秒後に再起動します...")
                        time.sleep(15)
                        print_info("[バックエンド(apps)] 起動を試みます...")
                        new_process = start_backend(BACKEND_APPS_APP, BACKEND_APPS_PORT, "バックエンド(apps)")
                        if new_process:
                            processes["バックエンド(apps)"] = new_process
                            thread_out = threading.Thread(target=stream_output_backend, args=("バックエンド(apps)", new_process.stdout, "out", last_output_times), daemon=True)
                            thread_out.start()
                            print_success("[バックエンド(apps)] 起動成功")
                        else:
                            print_error("[バックエンド(apps)] 起動失敗")
                        last_restart_attempt["バックエンド(apps)"] = time.time()

                if start_frontend_enabled and "フロントエンド" not in processes:
                    if current_time - last_restart_attempt["フロントエンド"] >= 15:
                        print_info("[フロントエンド] 15秒後に再起動します...")
                        time.sleep(15)
                        print_info("[フロントエンド] 起動を試みます...")
                        new_process = start_frontend()
                        if new_process:
                            processes["フロントエンド"] = new_process
                            thread_out = threading.Thread(target=stream_output_frontend, args=("フロントエンド", new_process.stdout, "out", last_output_times), daemon=True)
                            thread_out.start()
                            print_success("[フロントエンド] 起動成功")
                        else:
                            print_error("[フロントエンド] 起動失敗")
                        last_restart_attempt["フロントエンド"] = time.time()

                time.sleep(1)

        except KeyboardInterrupt:
            print_header("停止処理")
            print_info("Ctrl+C 検出 - サーバーを停止しています")
            stop_processes(processes)

            if sys.platform == "win32":
                print("\n\n")
                print(f"{Colors.FAIL}R を押すとリブートします (10秒以内){Colors.ENDC}")
                start_time = time.time()
                while time.time() - start_time < 10:
                    if is_r_pressed():
                        reboot_requested = True
                        break
                    time.sleep(0.05)

                if reboot_requested:
                    print_info("リブートを開始します")
            else:
                reboot_requested = False

        finally:
            stop_processes(processes)
            if reboot_requested:
                if sys.platform == "win32":
                    os.system("cls")
                continue

            print_header("停止完了")
            print_success("すべてのサーバーを停止しました")
            break


if __name__ == "__main__":
    main()
