# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""プロジェクトクリーンアップスクリプト（まとめ役）

各フォルダの `_cleanup.py` を import し、不要なキャッシュ・ビルド成果物・
仮想環境などを対話的に一括削除します。クリーンアップを実行する場合は、削除開始前に
全常駐サービスを各フォルダの `_start.py` が公開する `kill_ports()` で停止します。ルート固有の
処理（ルート temp / backup フォルダの削除、グローバル npm ツールの
アンインストール）のみこのスクリプトが直接担当し、フォルダ固有の処理は
各フォルダの `_cleanup.py` に委譲します。

フォルダ別スクリプト:
- backend_local/_cleanup.py    cleanup(choices)
- backend_tools/_cleanup.py    cleanup(choices)（グローバル MCP 設定も解除）
- backend_server/_cleanup.py   cleanup(choices)
- backend_taskteam/_cleanup.py cleanup(choices)
- frontend_web/_cleanup.py     cleanup(choices)
- frontend_avatar/_cleanup.py  cleanup(choices)
- command_hermes/_cleanup.py   cleanup(choices)（ランチャー/PATH も解除）

Usage:
    python _cleanup.py
"""

import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

if sys.platform == "win32":
    import msvcrt

# ============================================================
# プロジェクト設定
# ============================================================
BASE_DIR = Path(__file__).resolve().parent

BACKEND_PATH = "backend_server"
BACKEND_ENV_LIST = [".venv", "venv"]
BACKEND_TASKTEAM_PATH = "backend_taskteam"
BACKEND_TASKTEAM_ENV_LIST = [".venv", "venv"]
BACKEND_TOOLS_PATH = "backend_tools"
BACKEND_TOOLS_ENV_LIST = [".venv", "venv"]
BACKEND_LOCAL_PATH = "backend_local"
BACKEND_LOCAL_ENV_LIST = [".venv", "venv"]
BACKEND_HERMES_PATH = "command_hermes"
BACKEND_HERMES_ENV_LIST = [".venv", "venv"]

BACKUP_PATH = "backup"
ROOT_TEMP_PATH = "temp"
CLEANUP_STOP_REQUEST_PATH = BASE_DIR / ".cleanup_stop_request.json"

DATABASE_TYPE = "sqlite"
SQLITE_DB_REL_PATH = Path("_data/AiDiy/database.db")

AUTO_MODE = False

NPM_PACKAGES = [
    "@anthropic-ai/claude-code",
    "@github/copilot",
    "@openai/codex",
    "opencode-ai",
]


class Colors:
    HEADER = '\033[97m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(message):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")


def print_success(message):
    print(f"{Colors.OKBLUE}[OK] {message}{Colors.ENDC}")


def print_info(message):
    print(f"{Colors.OKGREEN}[INFO] {message}{Colors.ENDC}")


def print_warning(message):
    print(f"{Colors.WARNING}[WARN] {message}{Colors.ENDC}")


def print_error(message):
    print(f"{Colors.FAIL}[NG] {message}{Colors.ENDC}")


def _load_folder_module(folder: str):
    name = f"aidiy_{folder}_cleanup"
    path = BASE_DIR / folder / "_cleanup.py"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_folder_start_module(folder: str):
    """選択対象の既存プロセス停止に使う `_start.py` を読み込む。"""
    name = f"aidiy_{folder}_start_for_cleanup"
    path = BASE_DIR / folder / "_start.py"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _remove_folder_import_cache(folder: str) -> None:
    """`_start.py` / `_cleanup.py` の import で生成された `__pycache__` を消す。

    各フォルダの `cleanup()` は自分自身が import された後に走るため、
    ローダーが書き出したバイトコードが残る場合がある。呼び出し後に掃除する。
    """
    pycache_dir = BASE_DIR / folder / "__pycache__"
    if not pycache_dir.is_dir():
        return
    try:
        shutil.rmtree(pycache_dir, onerror=handle_remove_readonly)
        print_success(f"__pycache__ ({folder}) を削除しました: {pycache_dir}")
    except Exception as e:
        print_warning(f"__pycache__ ({folder}) の削除に失敗しました: {e}")


def _remove_root_python_caches() -> None:
    """ルート直下と `scripts/` の `__pycache__` を消す（フォルダ別の担当外）。"""
    targets = [BASE_DIR / "__pycache__"]
    for relative_path in ROOT_CACHE_SCAN_PATHS:
        scan_dir = BASE_DIR / relative_path
        if scan_dir.is_dir():
            targets.extend(sorted(scan_dir.rglob("__pycache__")))
    for pycache_dir in targets:
        if not pycache_dir.is_dir():
            continue
        remove_directory(pycache_dir, "__pycache__ (ルート)")


def _run_folder_cleanup(folder: str, choices: dict) -> None:
    """フォルダ別 `cleanup()` を実行し、import で残ったキャッシュを片付ける。"""
    try:
        _load_folder_module(folder).cleanup(choices)
    finally:
        _remove_folder_import_cache(folder)


SERVICE_CLEANUP_TARGETS = (
    ("local", "backend_local", "バックエンド(local)", ("バックエンド(local)",)),
    ("tools", "backend_tools", "バックエンド(tools)", ("バックエンド(tools)",)),
    (
        "backend",
        "backend_server",
        "バックエンド(core,apps)",
        ("バックエンド(core)", "バックエンド(apps)"),
    ),
    (
        "taskteam",
        "backend_taskteam",
        "バックエンド(task,team)",
        ("バックエンド(task,team)",),
    ),
    ("web", "frontend_web", "フロントエンド(Web)", ("フロントエンド(Web)",)),
    (
        "avatar",
        "frontend_avatar",
        "フロントエンド(Avatar)",
        ("フロントエンド(Avatar)",),
    ),
)

# `_start.py` / `_cleanup.py` を import するフォルダ（= `__pycache__` が生成される）。
IMPORT_CACHE_FOLDERS = tuple(
    folder for _choice_key, folder, _description, _service_names in SERVICE_CLEANUP_TARGETS
) + (BACKEND_HERMES_PATH,)

# フォルダ別 `_cleanup.py` の担当外になる、ルート側の Python キャッシュ。
ROOT_CACHE_SCAN_PATHS = ("scripts",)


@contextmanager
def cleanup_stop_request(choices: dict):
    """ルート `_start.py` に、全常駐サービスの自動再起動停止を通知する。"""
    _ = choices  # 呼び出し側との互換性を維持する。停止対象は常に全サービス。
    services = [
        service_name
        for _choice_key, _folder, _description, service_names in SERVICE_CLEANUP_TARGETS
        for service_name in service_names
    ]
    payload = {
        "owner_pid": os.getpid(),
        "services": services,
        "created_at": time.time(),
    }
    temporary_path = CLEANUP_STOP_REQUEST_PATH.with_suffix(
        f"{CLEANUP_STOP_REQUEST_PATH.suffix}.{os.getpid()}.tmp",
    )
    try:
        temporary_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        os.replace(temporary_path, CLEANUP_STOP_REQUEST_PATH)
    finally:
        temporary_path.unlink(missing_ok=True)
    try:
        yield
    finally:
        try:
            current = json.loads(CLEANUP_STOP_REQUEST_PATH.read_text(encoding="utf-8"))
            if current.get("owner_pid") == os.getpid():
                CLEANUP_STOP_REQUEST_PATH.unlink(missing_ok=True)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            pass


def stop_all_services(choices: dict) -> None:
    """全常駐サービスの待受プロセスを、ファイル削除前に停止する。"""
    _ = choices  # 呼び出し側との互換性を維持する。停止対象は常に全サービス。
    print_header("クリーンアップ前の既存プロセス整理")
    for _choice_key, folder, description, _service_names in SERVICE_CLEANUP_TARGETS:
        print_info(f"{description} の既存プロセスを停止します")
        _load_folder_start_module(folder).kill_ports()

    # `_start.py` の起動前整理と同様に、OS側のポート解放を短時間待つ。
    time.sleep(1)


# 以前の内部名を参照するテスト・補助コードとの互換性を保つ。
stop_selected_services = stop_all_services


# ============================================================
# 対話入力
# ============================================================
def _clear_keyboard_buffer() -> None:
    if sys.platform != "win32":
        return
    while msvcrt.kbhit():
        key = msvcrt.getch()
        if key in (b"\x00", b"\xe0") and msvcrt.kbhit():
            msvcrt.getch()


def _read_single_key(valid: tuple[bytes, ...], default_key: bytes) -> bytes:
    if sys.platform == "win32":
        _clear_keyboard_buffer()
        while True:
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key in (b"\x00", b"\xe0"):
                    if msvcrt.kbhit():
                        msvcrt.getch()
                    continue
                if key in (b"\r", b"\n"):
                    print(default_key.decode("ascii"))
                    return default_key
                if key in valid:
                    print(key.decode("ascii", errors="replace"))
                    return key
            time.sleep(0.05)

    response = input().strip().lower()
    if response == "":
        return default_key
    first = response[0:1].encode("ascii", errors="replace")
    if first in valid:
        return first
    return default_key


def ask_yes_no(prompt, default="n"):
    global AUTO_MODE
    if AUTO_MODE:
        print_info(f"[AUTO] {prompt} -> {'Yes' if default.lower() == 'y' else 'No'} (default)")
        return default.lower() == "y"

    bracket = "[y]/n" if default.lower() == "y" else "y/[n]"
    print(f"\n{prompt} ({bracket}): ", end="", flush=True)
    default_key = b"y" if default.lower() == "y" else b"n"
    key = _read_single_key((b"y", b"Y", b"n", b"N"), default_key)
    return key in (b"y", b"Y")


def ask_start_mode(prompt, default="n"):
    bracket = "[y]/n/a=auto" if default.lower() == "y" else "y/[n]/a=auto"
    print(f"\n{prompt} ({bracket}): ", end="", flush=True)
    default_key = b"y" if default.lower() == "y" else b"n"
    key = _read_single_key((b"y", b"Y", b"n", b"N", b"a", b"A"), default_key)
    if key in (b"a", b"A"):
        return True, True
    if key in (b"y", b"Y"):
        return True, False
    return False, False


# ============================================================
# ルート固有の削除処理
# ============================================================
def handle_remove_readonly(func, path, exc_info):
    del exc_info
    os.chmod(path, stat.S_IWRITE)
    func(path)


def remove_directory(path: Path, description: str) -> bool:
    if path.exists() and path.is_dir():
        try:
            shutil.rmtree(path, onerror=handle_remove_readonly)
            print_success(f"{description} を削除しました: {path}")
            return True
        except Exception as e:
            print_error(f"{description} の削除に失敗しました: {path}")
            print_error(f"  理由: {e}")
            print_warning("  ヒント: 管理者権限で実行するか、手動で削除してください")
            return False
    return False


def cleanup_backup(base_dir: Path, choices: dict):
    backup_dir = base_dir / BACKUP_PATH
    if not backup_dir.exists():
        return
    print_header("backup フォルダのクリーンアップ")
    if choices.get("backup") is True:
        remove_directory(backup_dir, "backup")
    elif choices.get("backup") is False:
        print_info("backup フォルダはそのまま残します")


def uninstall_global_npm_tools():
    print_header("グローバルnpmツールのアンインストール")

    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"

    uninstalled_count = 0
    for i, package in enumerate(NPM_PACKAGES, 1):
        cmd = [npm_cmd, "uninstall", "-g", package]
        print_info(f"実行中: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, check=True, capture_output=False, text=True)
            print_success(f"  [{i}/{len(NPM_PACKAGES)}] {package} をアンインストールしました")
            uninstalled_count += 1
        except subprocess.CalledProcessError as e:
            print_error(f"  [{i}/{len(NPM_PACKAGES)}] {package} のアンインストールに失敗しました: {e}")
        except FileNotFoundError:
            print_error(f"  {npm_cmd} が見つかりません。Node.jsがインストールされているか確認してください")
            break

    if uninstalled_count > 0:
        print_success(f"グローバルnpmツールのアンインストール完了 ({uninstalled_count}個削除)")
    else:
        print_info("アンインストール対象はありませんでした")


# ============================================================
# 選択収集
# ============================================================
def collect_cleanup_choices(base_dir: Path) -> dict | None:
    """全ての y/n を最初にまとめて聞く。キャンセル時は None を返す。"""
    global AUTO_MODE

    run_cleanup, AUTO_MODE = ask_start_mode("クリーンアップを実行しますか？", default="n")
    if not run_cleanup:
        return None

    if AUTO_MODE:
        print_info("AUTOモードで実行します。以降の質問はデフォルト値で自動回答します。")

    print_header("クリーンアップ内容の選択")
    print_info("最初に実行項目をまとめて選択してください。処理はまとめて一括実行されます。")
    print_info("常駐サービスが起動中の場合は、削除開始前にすべて停止します。")

    choices: dict = {
        "npm_uninstall":  False,
        "backup":         None,
        "tools":            False,
        "tools_envs":       {},
        "tools_node_modules": None,
        "tools_temp":       None,
        "backend":        False,
        "backend_envs":   {},
        "backend_logs":   None,
        "backend_temp":   None,
        "backend_sqlite": None,
        "taskteam":       False,
        "taskteam_envs":  {},
        "taskteam_temp":  None,
        "local":          False,
        "local_envs":     {},
        "local_temp":     None,
        "web":            False,
        "avatar":         False,
        "hermes":         False,
        "hermes_envs":    {},
        "hermes_temp":    None,
    }

    choices["npm_uninstall"] = ask_yes_no(
        "グローバルnpmツール(AI CLIツール)をアンインストールしますか？", default="n",
    )

    if (base_dir / BACKUP_PATH).exists():
        choices["backup"] = ask_yes_no("backup フォルダを削除しますか？", default="y")

    choices["local"] = ask_yes_no("バックエンド(local) をクリーンアップしますか？", default="y")
    if choices["local"]:
        backend_local_dir = base_dir / BACKEND_LOCAL_PATH
        if backend_local_dir.exists():
            for env_name in BACKEND_LOCAL_ENV_LIST:
                if (backend_local_dir / env_name).exists():
                    choices["local_envs"][env_name] = ask_yes_no(
                        f"  {BACKEND_LOCAL_PATH}/{env_name} を削除しますか？", default="y",
                    )
            if (backend_local_dir / "temp").exists():
                choices["local_temp"] = ask_yes_no(
                    f"  {BACKEND_LOCAL_PATH}/temp フォルダ(ダウンロード済みモデル含む)を削除しますか？", default="y",
                )

    choices["tools"] = ask_yes_no("バックエンド(tools) をクリーンアップしますか？", default="y")
    if choices["tools"]:
        backend_tools_dir = base_dir / BACKEND_TOOLS_PATH
        if backend_tools_dir.exists():
            for env_name in BACKEND_TOOLS_ENV_LIST:
                if (backend_tools_dir / env_name).exists():
                    choices["tools_envs"][env_name] = ask_yes_no(
                        f"  {BACKEND_TOOLS_PATH}/{env_name} を削除しますか？", default="y",
                    )
            if (backend_tools_dir / "node_modules").exists():
                choices["tools_node_modules"] = ask_yes_no(
                    f"  {BACKEND_TOOLS_PATH}/node_modules を削除しますか？", default="y",
                )
            if (backend_tools_dir / "temp").exists():
                choices["tools_temp"] = ask_yes_no(
                    f"  {BACKEND_TOOLS_PATH}/temp フォルダを削除しますか？", default="y",
                )

    choices["backend"] = ask_yes_no("バックエンド(core,apps)をクリーンアップしますか？", default="y")
    if choices["backend"]:
        backend_dir = base_dir / BACKEND_PATH
        if backend_dir.exists():
            for env_name in BACKEND_ENV_LIST:
                if (backend_dir / env_name).exists():
                    choices["backend_envs"][env_name] = ask_yes_no(
                        f"  {BACKEND_PATH}/{env_name} を削除しますか？", default="y",
                    )
            if (backend_dir / "temp").exists():
                choices["backend_temp"] = ask_yes_no(
                    f"  {BACKEND_PATH}/temp フォルダを削除しますか？", default="y",
                )
            if (
                DATABASE_TYPE.lower() == "sqlite"
                and (base_dir / SQLITE_DB_REL_PATH).exists()
            ):
                choices["backend_sqlite"] = ask_yes_no("  SQLite データベースを削除しますか？", default="n")

    choices["taskteam"] = ask_yes_no("バックエンド(task,team)をクリーンアップしますか？", default="y")
    if choices["taskteam"]:
        taskteam_dir = base_dir / BACKEND_TASKTEAM_PATH
        if taskteam_dir.exists():
            for env_name in BACKEND_TASKTEAM_ENV_LIST:
                if (taskteam_dir / env_name).exists():
                    choices["taskteam_envs"][env_name] = ask_yes_no(
                        f"  {BACKEND_TASKTEAM_PATH}/{env_name} を削除しますか？", default="y",
                    )
            if (taskteam_dir / "temp").exists():
                choices["taskteam_temp"] = ask_yes_no(
                    f"  {BACKEND_TASKTEAM_PATH}/temp フォルダを削除しますか？", default="y",
                )

    choices["web"] = ask_yes_no("フロントエンド(Web)をクリーンアップしますか？", default="y")
    choices["avatar"] = ask_yes_no("フロントエンド(Avatar)をクリーンアップしますか？", default="y")

    choices["hermes"] = ask_yes_no("コマンド(hermes)をクリーンアップしますか？", default="y")
    if choices["hermes"]:
        hermes_dir = base_dir / BACKEND_HERMES_PATH
        if hermes_dir.exists():
            for env_name in BACKEND_HERMES_ENV_LIST:
                if (hermes_dir / env_name).exists():
                    choices["hermes_envs"][env_name] = ask_yes_no(
                        f"  {BACKEND_HERMES_PATH}/{env_name} を削除しますか？", default="y",
                    )
            if (hermes_dir / "temp").exists():
                choices["hermes_temp"] = ask_yes_no(
                    f"  {BACKEND_HERMES_PATH}/temp フォルダを削除しますか？", default="y",
                )

    return choices


# ============================================================
# メイン
# ============================================================
def execute_cleanup(base_dir: Path, choices: dict) -> None:
    """選択済みの処理を、プロセス停止から順番に実行する。"""
    print_header("一括実行開始")

    stop_all_services(choices)

    if choices["npm_uninstall"]:
        uninstall_global_npm_tools()
    else:
        print_info("グローバルnpmツールのアンインストールをスキップしました")

    print()
    root_temp_dir = base_dir / ROOT_TEMP_PATH
    if root_temp_dir.exists():
        print_header("ルート temp フォルダのクリーンアップ")
        remove_directory(root_temp_dir, "ルート temp")

    print()
    cleanup_backup(base_dir, choices)

    print()
    if choices["local"]:
        _run_folder_cleanup("backend_local", choices)
    else:
        print_info("バックエンド(local) のクリーンアップをスキップしました")

    print()
    if choices["tools"]:
        _run_folder_cleanup("backend_tools", choices)
    else:
        print_info("バックエンド(tools) のクリーンアップをスキップしました")

    print()
    if choices["backend"]:
        _run_folder_cleanup("backend_server", choices)
    else:
        print_info("バックエンド(core,apps)のクリーンアップをスキップしました")

    print()
    if choices["taskteam"]:
        _run_folder_cleanup("backend_taskteam", choices)
    else:
        print_info("バックエンド(task,team)のクリーンアップをスキップしました")

    print()
    if choices["web"]:
        _run_folder_cleanup("frontend_web", choices)
    else:
        print_info("フロントエンド(Web)のクリーンアップをスキップしました")

    print()
    if choices["avatar"]:
        _run_folder_cleanup("frontend_avatar", choices)
    else:
        print_info("フロントエンド(Avatar)のクリーンアップをスキップしました")

    print()
    if choices["hermes"]:
        _run_folder_cleanup("command_hermes", choices)
    else:
        print_info("コマンド(hermes) のクリーンアップをスキップしました")

    print()
    # スキップしたフォルダにも `_start.py` の import キャッシュが残るため、最後に掃う。
    for folder in IMPORT_CACHE_FOLDERS:
        _remove_folder_import_cache(folder)
    _remove_root_python_caches()

    print()
    print_header("クリーンアップ完了")
    print_success("プロジェクトのクリーンアップが完了しました")
    print_info("他の担当者にプロジェクトを渡す準備ができました")
    print()
    print_info("クリーンアップは正常終了しました。5秒後に終了します...")
    time.sleep(5)


def main():
    print_header("プロジェクト クリーンアップ")

    base_dir = BASE_DIR
    print_info(f"プロジェクトディレクトリ: {base_dir}")
    print_info("クリーンアップ対象:")
    print_info("  1. ルート temp フォルダ")
    print_info("  2. ルート backup フォルダ")
    print_info("  3. バックエンド(local)")
    print_info("  4. バックエンド(tools)")
    print_info("  5. バックエンド(core,apps)")
    print_info("  6. バックエンド(task,team)")
    print_info("  7. フロントエンド(Web)")
    print_info("  8. フロントエンド(Avatar)")
    print_info("  9. コマンド(hermes)")
    print()

    choices = collect_cleanup_choices(base_dir)
    if choices is None:
        print_info("クリーンアップをキャンセルしました")
        return

    with cleanup_stop_request(choices):
        execute_cleanup(base_dir, choices)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_warning("クリーンアップが中断されました")
        sys.exit(1)
    except Exception as e:
        print_error(f"予期しないエラーが発生しました: {e}")
        sys.exit(1)
