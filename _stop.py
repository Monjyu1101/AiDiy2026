"""開発環境停止スクリプト

バックエンド/フロントエンドをポート番号で停止します。

Usage:
    python _stop.py
    python _stop.py --backend=yes --frontend=no
    python _stop.py --backend=no --frontend=yes
"""

import argparse
import re
import subprocess
import sys
import time

# ============================================================
# プロジェクト設定
# ============================================================
BACKEND_CORE_PORT = 8091
BACKEND_APPS_PORT = 8092
FRONTEND_PORT = 8090
# ============================================================


def kill_process_on_port(port: int) -> bool:
    """指定ポートを使用しているプロセスを強制停止"""
    print(f"[ポート {port}] 使用中のプロセスを検索...")

    try:
        if sys.platform == "win32":
            # Windows: 複数PIDに対応し、終了後に解放確認
            def list_pids():
                result = subprocess.run(
                    ["netstat", "-ano", "-p", "tcp"],
                    capture_output=True,
                    text=True,
                    timeout=5
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

            killed = False
            for _ in range(8):
                pids = list_pids()
                if not pids:
                    if killed:
                        print(f"[ポート {port}] ポート解放を確認しました")
                    else:
                        print(f"[ポート {port}] 使用中のプロセスなし")
                    return killed

                for pid in pids:
                    print(f"[ポート {port}] プロセス検出: PID={pid}")
                    result = subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", pid],
                        capture_output=True,
                        text=True,
                        timeout=8
                    )
                    if result.returncode == 0:
                        print(f"[ポート {port}] プロセスを強制停止しました (PID={pid})")
                        killed = True
                    else:
                        detail = (result.stderr or result.stdout or "").strip()
                        print(f"[ポート {port}] 停止失敗 (PID={pid}): {detail}")
                time.sleep(0.5)

            remaining = list_pids()
            if remaining:
                print(f"[ポート {port}] 停止後もLISTEN中です: PID={','.join(remaining)}")
            return killed
        else:
            # Linux/Mac: 複数PIDに対応し、終了後に解放確認
            def list_pids():
                try:
                    result = subprocess.run(
                        ["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-t"],
                        capture_output=True,
                        text=True,
                        timeout=5
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
                        timeout=5
                    )
                    if result.returncode != 0:
                        return []
                    pids = set(re.findall(r"pid=(\d+)", result.stdout))
                    return sorted(pids, key=int)
                except FileNotFoundError:
                    return []

            killed = False
            for _ in range(8):
                pids = list_pids()
                if not pids:
                    if killed:
                        print(f"[ポート {port}] ポート解放を確認しました")
                    else:
                        print(f"[ポート {port}] 使用中のプロセスなし")
                    return killed

                for pid in pids:
                    print(f"[ポート {port}] プロセス検出: PID={pid}")
                    result = subprocess.run(
                        ["kill", "-9", pid],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        print(f"[ポート {port}] プロセスを強制停止しました (PID={pid})")
                        killed = True
                    else:
                        detail = (result.stderr or result.stdout or "").strip()
                        print(f"[ポート {port}] 停止失敗 (PID={pid}): {detail}")
                time.sleep(0.5)

            remaining = list_pids()
            if remaining:
                print(f"[ポート {port}] 停止後もLISTEN中です: PID={','.join(remaining)}")
            return killed

    except Exception as e:
        print(f"[ポート {port}] エラー: {e}")
        return False


def main():
    # パラメータなし: 両方停止（default="yes"）
    # パラメータあり: yes指定のみ停止（default="no"）
    has_params = len(sys.argv) > 1
    default_value = "no" if has_params else "yes"

    parser = argparse.ArgumentParser(description="開発環境を停止します")
    parser.add_argument("--backend", default=default_value, choices=["yes", "no"], help="バックエンド停止 (yes/no)")
    parser.add_argument("--frontend", default=default_value, choices=["yes", "no"], help="フロントエンド停止 (yes/no)")
    args = parser.parse_args()

    stop_backend = args.backend == "yes"
    stop_frontend = args.frontend == "yes"

    if not stop_backend and not stop_frontend:
        print("停止対象が指定されていません (backend/no, frontend/no)")
        sys.exit(0)

    print("=" * 60)
    print("開発環境を停止します...")
    print("=" * 60)

    if stop_frontend:
        kill_process_on_port(FRONTEND_PORT)
    if stop_backend:
        kill_process_on_port(BACKEND_CORE_PORT)
        kill_process_on_port(BACKEND_APPS_PORT)

    print("=" * 60)
    print("停止処理が完了しました")
    print("=" * 60)
    print("停止処理は正常終了しました。5秒後に終了します...")
    time.sleep(5)


if __name__ == "__main__":
    main()
