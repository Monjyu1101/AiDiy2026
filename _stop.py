"""開発環境停止スクリプト

バックエンド/フロントエンドをポート番号で停止します。

Usage:
    python _stop.py
    python _stop.py --backend=yes --frontend=no
    python _stop.py --backend=no --frontend=yes
"""

import argparse
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
            # Windows: netstat + taskkill
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
                print(f"[ポート {port}] プロセス検出: PID={pid}")
                subprocess.run(
                    ["taskkill", "/F", "/PID", pid],
                    capture_output=True,
                    timeout=5
                )
                print(f"[ポート {port}] プロセスを強制停止しました")
                return True
            else:
                print(f"[ポート {port}] 使用中のプロセスなし")
                return False
        else:
            # Linux/Mac: lsof + kill
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            pids = result.stdout.strip().split('\n')
            killed = False
            for pid in pids:
                if pid and pid.isdigit():
                    print(f"[ポート {port}] プロセス検出: PID={pid}")
                    subprocess.run(
                        ["kill", "-9", pid],
                        capture_output=True,
                        timeout=5
                    )
                    print(f"[ポート {port}] プロセスを強制停止しました (PID={pid})")
                    killed = True
            
            if not killed:
                print(f"[ポート {port}] 使用中のプロセスなし")
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
