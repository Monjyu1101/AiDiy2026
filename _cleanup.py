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
仮想環境などを対話的に一括削除します。ルート固有の処理（ルート temp /
backup フォルダの削除、グローバル npm ツールのアンインストール）のみ
このスクリプトが直接担当し、フォルダ固有の処理は各フォルダの
`_cleanup.py` に委譲します。

フォルダ別スクリプト:
- backend_local/_cleanup.py    cleanup(choices)
- backend_tools/_cleanup.py    cleanup(choices)（グローバル MCP 設定も解除）
- backend_server/_cleanup.py   cleanup(choices)
- backend_task/_cleanup.py     cleanup(choices)
- backend_team/_cleanup.py     cleanup(choices)
- frontend_web/_cleanup.py     cleanup(choices)
- frontend_avatar/_cleanup.py  cleanup(choices)
- command_hermes/_cleanup.py   cleanup(choices)（ランチャー/PATH も解除）

Usage:
    python _cleanup.py
"""

import importlib.util
import os
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    import msvcrt

# ============================================================
# プロジェクト設定
# ============================================================
BASE_DIR = Path(__file__).resolve().parent

BACKEND_PATH = "backend_server"
BACKEND_ENV_LIST = [".venv", "venv"]
BACKEND_TASK_PATH = "backend_task"
BACKEND_TASK_ENV_LIST = [".venv", "venv"]
BACKEND_TEAM_PATH = "backend_team"
BACKEND_TOOLS_PATH = "backend_tools"
BACKEND_TOOLS_ENV_LIST = [".venv", "venv"]
BACKEND_LOCAL_PATH = "backend_local"
BACKEND_LOCAL_ENV_LIST = [".venv", "venv"]
BACKEND_HERMES_PATH = "command_hermes"
BACKEND_HERMES_ENV_LIST = [".venv", "venv"]

BACKUP_PATH = "backup"
ROOT_TEMP_PATH = "temp"

DATABASE_TYPE = "sqlite"
SQLITE_DB_REL_PATH = Path("backend_server/_data/AiDiy/database.db")

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
        "task":           False,
        "task_envs":      {},
        "task_temp":      None,
        "team":           False,
        "team_env":       False,
        "team_temp":      False,
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

    choices["task"] = ask_yes_no("バックエンド(task)をクリーンアップしますか？", default="y")
    if choices["task"]:
        task_dir = base_dir / BACKEND_TASK_PATH
        if task_dir.exists():
            for env_name in BACKEND_TASK_ENV_LIST:
                if (task_dir / env_name).exists():
                    choices["task_envs"][env_name] = ask_yes_no(
                        f"  {BACKEND_TASK_PATH}/{env_name} を削除しますか？", default="y",
                    )
            if (task_dir / "temp").exists():
                choices["task_temp"] = ask_yes_no(
                    f"  {BACKEND_TASK_PATH}/temp フォルダを削除しますか？", default="y",
                )

    choices["team"] = ask_yes_no("バックエンド(team)をクリーンアップしますか？", default="y")
    if choices["team"]:
        team_dir = base_dir / BACKEND_TEAM_PATH
        if (team_dir / ".venv").exists():
            choices["team_env"] = ask_yes_no(
                f"  {BACKEND_TEAM_PATH}/.venv を削除しますか？", default="y",
            )
        if (team_dir / "temp").exists():
            choices["team_temp"] = ask_yes_no(
                f"  {BACKEND_TEAM_PATH}/temp フォルダを削除しますか？", default="y",
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
    print_info("  6. バックエンド(task)")
    print_info("  7. バックエンド(team)")
    print_info("  8. フロントエンド(Web)")
    print_info("  9. フロントエンド(Avatar)")
    print_info(" 10. コマンド(hermes)")
    print()

    choices = collect_cleanup_choices(base_dir)
    if choices is None:
        print_info("クリーンアップをキャンセルしました")
        return

    print_header("一括実行開始")

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
        _load_folder_module("backend_local").cleanup(choices)
    else:
        print_info("バックエンド(local) のクリーンアップをスキップしました")

    print()
    if choices["tools"]:
        _load_folder_module("backend_tools").cleanup(choices)
    else:
        print_info("バックエンド(tools) のクリーンアップをスキップしました")

    print()
    if choices["backend"]:
        _load_folder_module("backend_server").cleanup(choices)
    else:
        print_info("バックエンド(core,apps)のクリーンアップをスキップしました")

    print()
    if choices["task"]:
        _load_folder_module("backend_task").cleanup(choices)
    else:
        print_info("バックエンド(task)のクリーンアップをスキップしました")

    print()
    if choices["team"]:
        _load_folder_module("backend_team").cleanup(choices)
    else:
        print_info("バックエンド(team)のクリーンアップをスキップしました")

    print()
    if choices["web"]:
        _load_folder_module("frontend_web").cleanup(choices)
    else:
        print_info("フロントエンド(Web)のクリーンアップをスキップしました")

    print()
    if choices["avatar"]:
        _load_folder_module("frontend_avatar").cleanup(choices)
    else:
        print_info("フロントエンド(Avatar)のクリーンアップをスキップしました")

    print()
    if choices["hermes"]:
        _load_folder_module("command_hermes").cleanup(choices)
    else:
        print_info("コマンド(hermes) のクリーンアップをスキップしました")

    print()
    print_header("クリーンアップ完了")
    print_success("プロジェクトのクリーンアップが完了しました")
    print_info("他の担当者にプロジェクトを渡す準備ができました")
    print()
    print_info("クリーンアップは正常終了しました。5秒後に終了します...")
    time.sleep(5)


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
