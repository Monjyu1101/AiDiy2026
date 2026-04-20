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

if sys.platform == "win32":
    import msvcrt

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
BACKEND_MCP_SERVER_PREFIX = "aidiy_"

NPM_PACKAGES = [
    "@anthropic-ai/claude-code",
    "@github/copilot",
    "@openai/codex",
    "@google/gemini-cli",
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


def _clear_keyboard_buffer() -> None:
    if sys.platform != "win32":
        return
    while msvcrt.kbhit():
        key = msvcrt.getch()
        if key in (b"\x00", b"\xe0") and msvcrt.kbhit():
            msvcrt.getch()


def _read_single_key(valid: tuple[bytes, ...], default_key: bytes) -> bytes:
    """1文字入力を受け付ける。Enter でデフォルト、valid 以外は無視して待機。"""
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


def remove_json_mcp_servers_by_prefix(path: Path, prefix: str, top_key: str = "mcpServers") -> bool:
    try:
        if not path.exists():
            print_info(f"MCP 設定ファイルなし: {path}")
            return True

        with open(path, encoding="utf-8-sig") as f:
            loaded = json.load(f)
        if not isinstance(loaded, dict):
            print_warning(f"MCP 設定の形式が不正です。削除をスキップしました: {path}")
            return False

        servers = loaded.get(top_key)
        if not isinstance(servers, dict):
            print_info(f"{prefix}* は未設定です: {path}")
            return True

        matched = [name for name in servers if name.startswith(prefix)]
        if not matched:
            print_info(f"{prefix}* は未設定です: {path}")
            return True

        for name in matched:
            del servers[name]

        if servers:
            loaded[top_key] = servers
        else:
            loaded.pop(top_key, None)

        if not write_json_file(path, loaded):
            return False

        print_success(f"{', '.join(matched)} の MCP 設定を削除しました: {path}")
        return True
    except json.JSONDecodeError as e:
        print_error(f"JSON解析エラー: {path} ({e})")
        return False
    except Exception as e:
        print_error(f"MCP 設定更新エラー: {path} ({e})")
        return False


def get_vscode_mcp_path() -> Path:
    """VS Code ユーザー設定フォルダ配下の mcp.json パスを返す。"""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming")))
        return base / "Code" / "User" / "mcp.json"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Code" / "User" / "mcp.json"
    return Path.home() / ".config" / "Code" / "User" / "mcp.json"


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


def remove_codex_mcp_servers_by_prefix(prefix: str) -> bool:
    config_path = Path.home() / ".codex" / "config.toml"
    header_prefix = f"[mcp_servers.{prefix}"
    try:
        if not config_path.exists():
            print_info(f"MCP 設定ファイルなし: {config_path}")
            return True
        content = config_path.read_text(encoding="utf-8")

        removed_names: list[str] = []
        updated = content
        while True:
            match_header = None
            match_name = None
            for line in updated.splitlines():
                stripped = line.strip()
                if stripped.startswith(header_prefix) and stripped.endswith("]"):
                    match_header = stripped
                    match_name = stripped[len("[mcp_servers."):-1]
                    break
            if match_header is None:
                break
            new_updated = remove_toml_table(updated, match_header)
            if new_updated == updated:
                break
            updated = new_updated
            removed_names.append(match_name)

        if not removed_names:
            print_info(f"{prefix}* は未設定です: {config_path}")
            return True

        config_path.write_text(updated, encoding="utf-8")
        print_success(f"{', '.join(removed_names)} の MCP 設定を削除しました: {config_path}")
        return True
    except Exception as e:
        print_error(f"Codex設定更新エラー: {config_path} ({e})")
        return False


def cleanup_global_mcp_configs(prefix: str):
    print_header("グローバルMCP設定の解除")

    copilot_home = Path(os.environ.get("COPILOT_HOME", str(Path.home() / ".copilot")))
    # (path, top_key) の組。VS Code のみ top-level キーが "servers"。
    targets = [
        (Path.home() / ".claude.json",            "mcpServers"),
        (Path.home() / ".gemini" / "settings.json","mcpServers"),
        (copilot_home / "mcp-config.json",        "mcpServers"),
        (get_vscode_mcp_path(),                   "servers"),
    ]

    updated_count = 0
    for path, top_key in targets:
        if remove_json_mcp_servers_by_prefix(path, prefix, top_key=top_key):
            updated_count += 1

    print_info(f"Codex CLI 設定も解除対象です: {Path.home() / '.codex' / 'config.toml'}")
    if remove_codex_mcp_servers_by_prefix(prefix):
        updated_count += 1

    if updated_count > 0:
        print_success(f"グローバルMCP設定の解除処理を完了しました: {prefix}*")
    else:
        print_warning(f"グローバルMCP設定の解除に失敗しました: {prefix}*")


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


def cleanup_backend(base_dir: Path, choices: dict):
    label = "バックエンド(core,apps)"
    print_header(f"{label} のクリーンアップ")

    backend_dir = base_dir / BACKEND_PATH
    if not backend_dir.exists():
        print_warning(f"{label} のフォルダが見つかりません")
        return

    deleted_count = cleanup_common_python_caches(backend_dir, label)

    backend_envs = choices.get("backend_envs", {})
    for env_name in BACKEND_ENV_LIST:
        env_dir = backend_dir / env_name
        if not env_dir.exists():
            continue
        if backend_envs.get(env_name):
            if remove_directory(env_dir, f"{env_name} ({label})"):
                deleted_count += 1
            else:
                print_error(
                    f"  {BACKEND_PATH}/{env_name} 削除失敗。"
                    f"手動で削除してください: {env_dir}"
                )
        elif env_name in backend_envs:
            print_info(f"  {BACKEND_PATH}/{env_name} はそのまま残します")

    logs_dir = backend_dir / "logs"
    if logs_dir.exists():
        if choices.get("backend_logs") is True:
            if clean_directory_contents(logs_dir, f"logs ({label})"):
                deleted_count += 1
        elif choices.get("backend_logs") is False:
            print_info(f"  {BACKEND_PATH}/logs はそのまま残します")

    temp_dir = backend_dir / "temp"
    if temp_dir.exists():
        if choices.get("backend_temp") is True:
            if clean_directory_contents(temp_dir, f"temp ({label})"):
                deleted_count += 1
        elif choices.get("backend_temp") is False:
            print_info(f"  {BACKEND_PATH}/temp はそのまま残します")

    if DATABASE_TYPE.lower() == "sqlite":
        sqlite_db = base_dir / SQLITE_DB_REL_PATH
        if sqlite_db.exists():
            if choices.get("backend_sqlite") is True:
                if remove_file(sqlite_db, f"SQLite データベース ({label})"):
                    deleted_count += 1
            elif choices.get("backend_sqlite") is False:
                print_info("  SQLite データベースはそのまま残します")

    if deleted_count > 0:
        print_success(f"{label} のクリーンアップ完了 ({deleted_count}個削除)")
    else:
        print_info(f"{label}: 削除対象はありませんでした")


def cleanup_backend_mcp(base_dir: Path, choices: dict):
    label = "バックエンド(mcp)"
    print_header(f"{label} のクリーンアップ")

    backend_mcp_dir = base_dir / BACKEND_MCP_PATH
    if not backend_mcp_dir.exists():
        print_warning(f"{label} のフォルダが見つかりません")
        return

    deleted_count = cleanup_common_python_caches(backend_mcp_dir, label)

    mcp_envs = choices.get("mcp_envs", {})
    for env_name in BACKEND_MCP_ENV_LIST:
        env_dir = backend_mcp_dir / env_name
        if not env_dir.exists():
            continue
        if mcp_envs.get(env_name):
            if remove_directory(env_dir, f"{env_name} ({label})"):
                deleted_count += 1
            else:
                print_error(
                    f"  {BACKEND_MCP_PATH}/{env_name} 削除失敗。"
                    f"手動で削除してください: {env_dir}"
                )
        elif env_name in mcp_envs:
            print_info(f"  {BACKEND_MCP_PATH}/{env_name} はそのまま残します")

    node_modules_dir = backend_mcp_dir / "node_modules"
    if node_modules_dir.exists():
        if choices.get("mcp_node_modules") is True:
            if remove_directory(node_modules_dir, f"node_modules ({label})"):
                deleted_count += 1
        elif choices.get("mcp_node_modules") is False:
            print_info(f"  {BACKEND_MCP_PATH}/node_modules はそのまま残します")

    temp_dir = backend_mcp_dir / "temp"
    if temp_dir.exists():
        if choices.get("mcp_temp") is True:
            if clean_directory_contents(temp_dir, f"temp ({label})"):
                deleted_count += 1
        elif choices.get("mcp_temp") is False:
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

    uninstalled_count = 0
    for i, package in enumerate(NPM_PACKAGES, 1):
        cmd = [npm_cmd, "uninstall", "-g", package]
        print_info(f"実行中: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, check=True, capture_output=False, text=True)
            print_success(
                f"  [{i}/{len(NPM_PACKAGES)}] "
                f"{package} をアンインストールしました"
            )
            uninstalled_count += 1
        except subprocess.CalledProcessError as e:
            print_error(
                f"  [{i}/{len(NPM_PACKAGES)}] "
                f"{package} のアンインストールに失敗しました: {e}"
            )
        except FileNotFoundError:
            print_error(f"  {npm_cmd} が見つかりません。Node.jsがインストールされているか確認してください")
            break

    if uninstalled_count > 0:
        print_success(f"グローバルnpmツールのアンインストール完了 ({uninstalled_count}個削除)")
    else:
        print_info("アンインストール対象はありませんでした")


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
        "mcp":            False,
        "mcp_envs":       {},
        "mcp_node_modules": None,
        "mcp_temp":       None,
        "backend":        False,
        "backend_envs":   {},
        "backend_logs":   None,
        "backend_temp":   None,
        "backend_sqlite": None,
        "web":            False,
        "avatar":         False,
    }

    choices["npm_uninstall"] = ask_yes_no(
        "グローバルnpmツール(AI CLIツール)をアンインストールしますか？",
        default="n",
    )

    choices["mcp"] = ask_yes_no("バックエンド(mcp) をクリーンアップしますか？", default="y")
    if choices["mcp"]:
        backend_mcp_dir = base_dir / BACKEND_MCP_PATH
        if backend_mcp_dir.exists():
            for env_name in BACKEND_MCP_ENV_LIST:
                if (backend_mcp_dir / env_name).exists():
                    choices["mcp_envs"][env_name] = ask_yes_no(
                        f"  {BACKEND_MCP_PATH}/{env_name} を削除しますか？",
                        default="y",
                    )
            if (backend_mcp_dir / "temp").exists():
                choices["mcp_temp"] = ask_yes_no(
                    f"  {BACKEND_MCP_PATH}/temp の中身をクリアしますか？",
                    default="y",
                )

    choices["backend"] = ask_yes_no(
        "バックエンド(core,apps)をクリーンアップしますか？",
        default="y",
    )
    if choices["backend"]:
        backend_dir = base_dir / BACKEND_PATH
        if backend_dir.exists():
            if (backend_dir / "temp").exists():
                choices["backend_temp"] = ask_yes_no(
                    f"  {BACKEND_PATH}/temp の中身をクリアしますか？",
                    default="y",
                )
            if (
                DATABASE_TYPE.lower() == "sqlite"
                and (base_dir / SQLITE_DB_REL_PATH).exists()
            ):
                choices["backend_sqlite"] = ask_yes_no(
                    "  SQLite データベースを削除しますか？",
                    default="n",
                )

    choices["web"] = ask_yes_no(
        "フロントエンド(Web)をクリーンアップしますか？",
        default="y",
    )
    choices["avatar"] = ask_yes_no("フロントエンド(Avatar)をクリーンアップしますか？", default="y")

    return choices


def main():
    print_header("プロジェクト クリーンアップ")

    base_dir = Path(__file__).parent
    print_info(f"プロジェクトディレクトリ: {base_dir}")
    print_info("クリーンアップ対象:")
    print_info("  1. バックエンド(mcp)")
    print_info("  2. バックエンド(core,apps)")
    print_info("  3. フロントエンド(Web)")
    print_info("  4. フロントエンド(Avatar)")
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
    if choices["mcp"]:
        cleanup_backend_mcp(base_dir, choices)
        print()
        cleanup_global_mcp_configs(BACKEND_MCP_SERVER_PREFIX)
    else:
        print_info("バックエンド(mcp) のクリーンアップをスキップしました")

    print()
    if choices["backend"]:
        cleanup_backend(base_dir, choices)
    else:
        print_info("バックエンド(core,apps)のクリーンアップをスキップしました")

    print()
    if choices["web"]:
        cleanup_frontend_web(base_dir)
    else:
        print_info("フロントエンド(Web)のクリーンアップをスキップしました")

    print()
    if choices["avatar"]:
        cleanup_frontend_avatar(base_dir)
    else:
        print_info("フロントエンド(Avatar)のクリーンアップをスキップしました")

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
