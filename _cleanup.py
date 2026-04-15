# -*- coding: utf-8 -*-

"""プロジェクトクリーンアップスクリプト

他の担当者にプロジェクトを渡す前に、
不要なキャッシュファイルやビルド成果物を削除します。

対象:
- バックエンド(mcp): `backend_mcp`
- バックエンド(core,apps): `backend_server`
- フロントエンド(Web): `frontend_web`
- フロントエンド(Avatar): `frontend_avatar`

Usage:
    python _cleanup.py
"""

import json
import os
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path

# ============================================================
# プロジェクト設定
# ============================================================
BACKEND_PATH = "backend_server"
BACKEND_ENV_LIST = [".venv", "venv"]

BACKEND_MCP_PATH = "backend_mcp"
BACKEND_MCP_ENV_LIST = [".venv", "venv"]

FRONTEND_WEB_PATH = "frontend_web"

FRONTEND_AVATAR_PATH = "frontend_avatar"
FRONTEND_AVATAR_BUILD_DIRS = ["dist", "dist-electron"]

DATABASE_TYPE = "sqlite"
SQLITE_DB_REL_PATH = Path("backend_server/_data/AiDiy/database.db")

AUTO_MODE = False
BACKEND_MCP_SERVER_NAME = "aidiy_chrome_devtools"


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


def ask_yes_no(prompt, default="n"):
    global AUTO_MODE

    if AUTO_MODE:
        print_info(f"[AUTO] {prompt} -> {'Yes' if default.lower() == 'y' else 'No'} (default)")
        return default.lower() == "y"

    prompt_text = f"\n{prompt}([y]/n): " if default.lower() == "y" else f"\n{prompt}([n]/y): "
    while True:
        answer = input(prompt_text).strip().lower()
        if answer == "":
            answer = default.lower()
        if answer in ["y", "yes"]:
            return True
        if answer in ["n", "no"]:
            return False
        print_warning("'y' または 'n' で答えてください")


def ask_start_mode(prompt, default="n"):
    if default.lower() == "y":
        prompt_text = f"\n{prompt}([y]/n/a=auto): "
    else:
        prompt_text = f"\n{prompt}([n]/y/a=auto): "

    while True:
        answer = input(prompt_text).strip().lower()
        if answer == "":
            answer = default.lower()
        if answer in ["y", "yes"]:
            return True, False
        if answer in ["n", "no"]:
            return False, False
        if answer in ["a", "auto"]:
            return True, True
        print_warning("'y' または 'n' または 'a'(auto) で答えてください")


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


def remove_file(path: Path, description: str) -> bool:
    if path.exists() and path.is_file():
        try:
            if not os.access(path, os.W_OK):
                os.chmod(path, stat.S_IWRITE)
            path.unlink()
            print_success(f"{description} を削除しました: {path}")
            return True
        except Exception as e:
            print_error(f"{description} の削除に失敗しました: {path}")
            print_error(f"  理由: {e}")
            print_warning("  ヒント: 管理者権限で実行するか、手動で削除してください")
            return False
    return False


def clean_directory_contents(path: Path, description: str) -> bool:
    if path.exists() and path.is_dir():
        try:
            deleted_count = 0
            for item in path.iterdir():
                if item.is_dir():
                    shutil.rmtree(item, onerror=handle_remove_readonly)
                else:
                    if not os.access(item, os.W_OK):
                        os.chmod(item, stat.S_IWRITE)
                    item.unlink()
                deleted_count += 1

            if deleted_count > 0:
                print_success(f"{description} の中身を削除しました: {path} ({deleted_count}個)")
            else:
                print_info(f"{description} は空です: {path}")
            return True
        except Exception as e:
            print_error(f"{description} の中身削除に失敗しました: {path}")
            print_error(f"  理由: {e}")
            print_warning("  ヒント: 管理者権限で実行するか、手動で削除してください")
            return False
    return False


def write_json_file(path: Path, data: dict) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return True
    except Exception as e:
        print_error(f"設定ファイル書き込みエラー: {path} ({e})")
        return False


def remove_json_mcp_server(path: Path, server_name: str) -> bool:
    try:
        if not path.exists():
            print_info(f"MCP 設定ファイルなし: {path}")
            return True

        with open(path, encoding="utf-8-sig") as f:
            loaded = json.load(f)
        if not isinstance(loaded, dict):
            print_warning(f"MCP 設定の形式が不正です。削除をスキップしました: {path}")
            return False

        servers = loaded.get("mcpServers")
        if not isinstance(servers, dict) or server_name not in servers:
            print_info(f"{server_name} は未設定です: {path}")
            return True

        del servers[server_name]
        if servers:
            loaded["mcpServers"] = servers
        else:
            loaded.pop("mcpServers", None)

        if not write_json_file(path, loaded):
            return False

        print_success(f"{server_name} の MCP 設定を削除しました: {path}")
        return True
    except json.JSONDecodeError as e:
        print_error(f"JSON解析エラー: {path} ({e})")
        return False
    except Exception as e:
        print_error(f"MCP 設定更新エラー: {path} ({e})")
        return False


def remove_toml_table(content: str, table_header: str) -> str:
    lines = content.splitlines()
    table_index = None
    for i, line in enumerate(lines):
        if line.strip() == table_header:
            table_index = i
            break

    if table_index is None:
        return content if content.endswith("\n") or content == "" else content + "\n"

    next_table_index = len(lines)
    for i in range(table_index + 1, len(lines)):
        stripped = lines[i].strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            next_table_index = i
            break

    del lines[table_index:next_table_index]
    while lines and lines[-1].strip() == "":
        lines.pop()
    return "\n".join(lines).rstrip() + ("\n" if lines else "")


def remove_codex_mcp_server(server_name: str) -> bool:
    config_path = Path.home() / ".codex" / "config.toml"
    table_header = f"[mcp_servers.{server_name}]"
    try:
        if not config_path.exists():
            print_info(f"MCP 設定ファイルなし: {config_path}")
            return True
        content = config_path.read_text(encoding="utf-8")
        updated = remove_toml_table(content, table_header)
        if updated == content:
            print_info(f"{server_name} は未設定です: {config_path}")
            return True
        config_path.write_text(updated, encoding="utf-8")
        print_success(f"{server_name} の MCP 設定を削除しました: {config_path}")
        return True
    except Exception as e:
        print_error(f"Codex設定更新エラー: {config_path} ({e})")
        return False


def cleanup_global_mcp_configs(server_name: str):
    print_header("グローバルMCP設定の解除")

    copilot_home = Path(os.environ.get("COPILOT_HOME", str(Path.home() / ".copilot")))
    targets = [
        Path.home() / ".claude.json",
        Path.home() / ".gemini" / "settings.json",
        copilot_home / "mcp-config.json",
    ]

    updated_count = 0
    for path in targets:
        if remove_json_mcp_server(path, server_name):
            updated_count += 1

    print_info(f"Codex CLI 設定も解除対象です: {Path.home() / '.codex' / 'config.toml'}")
    if remove_codex_mcp_server(server_name):
        updated_count += 1

    if updated_count > 0:
        print_success(f"グローバルMCP設定の解除処理を完了しました: {server_name}")
    else:
        print_warning(f"グローバルMCP設定の解除に失敗しました: {server_name}")


def cleanup_common_python_caches(target_dir: Path, label: str) -> int:
    deleted_count = 0

    print_info(f"{label}: __pycache__ フォルダを検索中...")
    for pycache in target_dir.rglob("__pycache__"):
        if remove_directory(pycache, f"__pycache__ ({label})"):
            deleted_count += 1

    print_info(f"{label}: .pytest_cache フォルダを検索中...")
    for pytest_cache in target_dir.rglob(".pytest_cache"):
        if remove_directory(pytest_cache, f".pytest_cache ({label})"):
            deleted_count += 1

    return deleted_count


def cleanup_backend(base_dir: Path):
    label = "バックエンド(core,apps)"
    print_header(f"{label} のクリーンアップ")

    backend_dir = base_dir / BACKEND_PATH
    if not backend_dir.exists():
        print_warning(f"{label} のフォルダが見つかりません")
        return

    deleted_count = cleanup_common_python_caches(backend_dir, label)

    print_info(f"{label}: 削除対象の仮想環境リスト: {', '.join(BACKEND_ENV_LIST)}")
    for env_name in BACKEND_ENV_LIST:
        env_dir = backend_dir / env_name
        if env_dir.exists():
            if ask_yes_no(f"  {BACKEND_PATH}/{env_name} を削除しますか？", default="y"):
                if remove_directory(env_dir, f"{env_name} ({label})"):
                    deleted_count += 1
                else:
                    print_error(f"  {BACKEND_PATH}/{env_name} 削除失敗。手動で削除してください: {env_dir}")
            else:
                print_info(f"  {BACKEND_PATH}/{env_name} はそのまま残します")

    logs_dir = backend_dir / "logs"
    if logs_dir.exists():
        if ask_yes_no(f"  {BACKEND_PATH}/logs の中身をクリアしますか？", default="y"):
            if clean_directory_contents(logs_dir, f"logs ({label})"):
                deleted_count += 1
        else:
            print_info(f"  {BACKEND_PATH}/logs はそのまま残します")

    temp_dir = backend_dir / "temp"
    if temp_dir.exists():
        if ask_yes_no(f"  {BACKEND_PATH}/temp の中身をクリアしますか？", default="y"):
            if clean_directory_contents(temp_dir, f"temp ({label})"):
                deleted_count += 1
        else:
            print_info(f"  {BACKEND_PATH}/temp はそのまま残します")

    if DATABASE_TYPE.lower() == "sqlite":
        sqlite_db = base_dir / SQLITE_DB_REL_PATH
        if sqlite_db.exists():
            if ask_yes_no("  SQLite データベースを削除しますか？", default="n"):
                if remove_file(sqlite_db, f"SQLite データベース ({label})"):
                    deleted_count += 1
            else:
                print_info("  SQLite データベースはそのまま残します")

    if deleted_count > 0:
        print_success(f"{label} のクリーンアップ完了 ({deleted_count}個削除)")
    else:
        print_info(f"{label}: 削除対象はありませんでした")


def cleanup_backend_mcp(base_dir: Path):
    label = "バックエンド(mcp)"
    print_header(f"{label} のクリーンアップ")

    backend_mcp_dir = base_dir / BACKEND_MCP_PATH
    if not backend_mcp_dir.exists():
        print_warning(f"{label} のフォルダが見つかりません")
        return

    deleted_count = cleanup_common_python_caches(backend_mcp_dir, label)

    print_info(f"{label}: 削除対象の仮想環境リスト: {', '.join(BACKEND_MCP_ENV_LIST)}")
    for env_name in BACKEND_MCP_ENV_LIST:
        env_dir = backend_mcp_dir / env_name
        if env_dir.exists():
            if ask_yes_no(f"  {BACKEND_MCP_PATH}/{env_name} を削除しますか？", default="y"):
                if remove_directory(env_dir, f"{env_name} ({label})"):
                    deleted_count += 1
                else:
                    print_error(f"  {BACKEND_MCP_PATH}/{env_name} 削除失敗。手動で削除してください: {env_dir}")
            else:
                print_info(f"  {BACKEND_MCP_PATH}/{env_name} はそのまま残します")

    node_modules_dir = backend_mcp_dir / "node_modules"
    if node_modules_dir.exists():
        if ask_yes_no(f"  {BACKEND_MCP_PATH}/node_modules を削除しますか？", default="y"):
            if remove_directory(node_modules_dir, f"node_modules ({label})"):
                deleted_count += 1
        else:
            print_info(f"  {BACKEND_MCP_PATH}/node_modules はそのまま残します")

    temp_dir = backend_mcp_dir / "temp"
    if temp_dir.exists():
        if ask_yes_no(f"  {BACKEND_MCP_PATH}/temp の中身をクリアしますか？", default="y"):
            if clean_directory_contents(temp_dir, f"temp ({label})"):
                deleted_count += 1
        else:
            print_info(f"  {BACKEND_MCP_PATH}/temp はそのまま残します")

    if deleted_count > 0:
        print_success(f"{label} のクリーンアップ完了 ({deleted_count}個削除)")
    else:
        print_info(f"{label}: 削除対象はありませんでした")


def cleanup_frontend_web(base_dir: Path):
    label = "フロントエンド(Web)"
    print_header(f"{label} のクリーンアップ")

    web_dir = base_dir / FRONTEND_WEB_PATH
    if not web_dir.exists():
        print_warning(f"{label} のフォルダが見つかりません")
        return

    deleted_count = 0

    node_modules_dir = web_dir / "node_modules"
    if remove_directory(node_modules_dir, f"node_modules ({label})"):
        deleted_count += 1
    elif node_modules_dir.exists():
        print_error(f"  node_modules 削除失敗。手動で削除してください: {node_modules_dir}")

    dist_dir = web_dir / "dist"
    if remove_directory(dist_dir, f"dist ({label})"):
        deleted_count += 1

    if deleted_count > 0:
        print_success(f"{label} のクリーンアップ完了 ({deleted_count}個削除)")
    else:
        print_info(f"{label}: 削除対象はありませんでした")


def cleanup_frontend_avatar(base_dir: Path):
    label = "フロントエンド(Avatar)"
    print_header(f"{label} のクリーンアップ")

    avatar_dir = base_dir / FRONTEND_AVATAR_PATH
    if not avatar_dir.exists():
        print_warning(f"{label} のフォルダが見つかりません")
        return

    deleted_count = 0

    node_modules_dir = avatar_dir / "node_modules"
    if remove_directory(node_modules_dir, f"node_modules ({label})"):
        deleted_count += 1
    elif node_modules_dir.exists():
        print_error(f"  node_modules 削除失敗。手動で削除してください: {node_modules_dir}")

    for build_dir_name in FRONTEND_AVATAR_BUILD_DIRS:
        build_dir = avatar_dir / build_dir_name
        if remove_directory(build_dir, f"{build_dir_name} ({label})"):
            deleted_count += 1

    if deleted_count > 0:
        print_success(f"{label} のクリーンアップ完了 ({deleted_count}個削除)")
    else:
        print_info(f"{label}: 削除対象はありませんでした")


def uninstall_global_npm_tools():
    print_header("グローバルnpmツールのアンインストール")

    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    packages = [
        "@anthropic-ai/claude-code",
        "@github/copilot",
        "@openai/codex",
        "@google/gemini-cli",
    ]

    uninstalled_count = 0
    for i, package in enumerate(packages, 1):
        if ask_yes_no(f"  [{i}/{len(packages)}] {package} をアンインストールしますか？", default="n"):
            cmd = [npm_cmd, "uninstall", "-g", package]
            print_info(f"実行中: {' '.join(cmd)}")
            try:
                subprocess.run(cmd, check=True, capture_output=False, text=True)
                print_success(f"  {package} をアンインストールしました")
                uninstalled_count += 1
            except subprocess.CalledProcessError as e:
                print_error(f"  {package} のアンインストールに失敗しました: {e}")
            except FileNotFoundError:
                print_error(f"  {npm_cmd} が見つかりません。Node.jsがインストールされているか確認してください")
                break
        else:
            print_info(f"  {package} はそのまま残します")

    if uninstalled_count > 0:
        print_success(f"グローバルnpmツールのアンインストール完了 ({uninstalled_count}個削除)")
    else:
        print_info("アンインストール対象はありませんでした")


def main():
    global AUTO_MODE

    print_header("プロジェクト クリーンアップ")

    base_dir = Path(__file__).parent
    print_info(f"プロジェクトディレクトリ: {base_dir}")
    print_info("クリーンアップ対象:")
    print_info("  1. バックエンド(mcp)")
    print_info("  2. バックエンド(core,apps)")
    print_info("  3. フロントエンド(Web)")
    print_info("  4. フロントエンド(Avatar)")
    print()

    run_cleanup, AUTO_MODE = ask_start_mode("クリーンアップを実行しますか？", default="n")
    if not run_cleanup:
        print_info("クリーンアップをキャンセルしました")
        return

    if AUTO_MODE:
        print_info("AUTOモードで実行します。以降の質問はデフォルト値で自動回答します。")

    if ask_yes_no("グローバルnpmツール(AI CLIツール)をアンインストールしますか？", default="n"):
        uninstall_global_npm_tools()
    else:
        print_info("グローバルnpmツールのアンインストールをスキップしました")

    backup_dir = base_dir / "backup"
    if backup_dir.exists():
        if ask_yes_no("backup フォルダを削除しますか？", default="y"):
            remove_directory(backup_dir, "backup")
        else:
            print_info("backup フォルダはそのまま残します")

    print()
    if ask_yes_no("バックエンド(mcp) をクリーンアップしますか？", default="y"):
        cleanup_backend_mcp(base_dir)
    else:
        print_info("バックエンド(mcp) のクリーンアップをスキップしました")

    print()
    if ask_yes_no("バックエンド(core,apps)をクリーンアップしますか？", default="y"):
        cleanup_backend(base_dir)
    else:
        print_info("バックエンド(core,apps)のクリーンアップをスキップしました")

    print()
    if ask_yes_no("フロントエンド(Web)をクリーンアップしますか？", default="y"):
        cleanup_frontend_web(base_dir)
    else:
        print_info("フロントエンド(Web)のクリーンアップをスキップしました")

    print()
    if ask_yes_no("フロントエンド(Avatar)をクリーンアップしますか？", default="y"):
        cleanup_frontend_avatar(base_dir)
    else:
        print_info("フロントエンド(Avatar)のクリーンアップをスキップしました")

    print()
    if ask_yes_no(f"グローバルMCP設定の {BACKEND_MCP_SERVER_NAME} を解除しますか？", default="y"):
        cleanup_global_mcp_configs(BACKEND_MCP_SERVER_NAME)
    else:
        print_warning(f"グローバルMCP設定の {BACKEND_MCP_SERVER_NAME} はそのまま残します")

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
