# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""プロジェクト セットアップスクリプト（まとめ役）

各フォルダの `_setup.py` を import し、プロジェクト全体の初期セットアップを
対話的に一括実行します。共通（グローバル）のセットアップ（Python ツール更新・
AI CLI ツール導入）のみこのスクリプトが直接担当し、フォルダ固有の処理は
各フォルダの `_setup.py` に委譲します。

フォルダ別スクリプト:
- backend_server/_setup.py   バックエンド(core,apps)
- backend_task/_setup.py     バックエンド(task)
- backend_team/_setup.py     バックエンド(team)
- backend_tools/_setup.py    バックエンド(tools) + MCP 設定
- backend_local/_setup.py    バックエンド(local)
- frontend_web/_setup.py     フロントエンド(Web)
- frontend_avatar/_setup.py  フロントエンド(Avatar)
- command_hermes/_setup.py   コマンド(hermes)

Usage:
    python _setup.py
"""

import importlib.util
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

FRONTEND_COMMAND = "npm"
DATABASE_TYPE = "sqlite"

AUTO_MODE = False
GLOBAL_CLI_INSTALL_PROCESSES = []
HERMES_AGENT_INSTALL_COMMAND = (
    "curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash"
)
OLLAMA_INSTALL_COMMAND = "curl -fsSL https://ollama.com/install.sh | sh"
GIT_INSTALL_COMMAND_WINDOWS = ["winget", "install", "--id", "Git.Git", "-e", "--source", "winget"]
NODE_INSTALL_COMMAND_WINDOWS = ["winget", "install", "--id", "OpenJS.NodeJS.LTS", "-e", "--source", "winget"]
GIT_DOWNLOAD_URL = "https://git-scm.com/downloads"
NODE_DOWNLOAD_URL = "https://nodejs.org/"
ANTIGRAVITY_INSTALL_COMMAND_WINDOWS = (
    "curl -fsSL https://antigravity.google/cli/install.cmd -o install.cmd && install.cmd && del install.cmd"
)
ANTIGRAVITY_INSTALL_COMMAND_UNIX = "curl -fsSL https://antigravity.google/cli/install.sh | bash"


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
    print(f"\n{Colors.HEADER}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{message}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'=' * 60}{Colors.ENDC}\n")


def print_success(message):
    print(f"{Colors.OKBLUE}[OK] {message}{Colors.ENDC}")


def print_error(message):
    print(f"{Colors.FAIL}[NG] {message}{Colors.ENDC}")


def print_warning(message):
    print(f"{Colors.WARNING}[WARN] {message}{Colors.ENDC}")


def print_info(message):
    print(f"{Colors.OKGREEN}[INFO] {message}{Colors.ENDC}")


def print_setup_summary(error_locations: list[str]) -> None:
    print()
    print_header("セットアップ完了")
    if error_locations:
        print_warning("セットアップ処理は完了しましたが、一部でエラーが発生しました。")
        print_warning("エラー発生場所:")
        for location in error_locations:
            print_warning(f"  - {location}")
    else:
        print_success("セットアップ処理が完了しました。")


# ============================================================
# フォルダ別 _setup.py のローダー
# ============================================================
def _load_folder_module(folder: str):
    name = f"aidiy_{folder}_setup"
    path = BASE_DIR / folder / "_setup.py"
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


def ask_download_mode(prompt, default="n"):
    """モデルDL選択。戻り値: "no"(取得しない) / "one"(設定モデル) / "all"(候補一括)。"""
    global AUTO_MODE
    mode_of = {"y": "one", "a": "all"}
    if AUTO_MODE:
        mode = mode_of.get(default.lower(), "no")
        print_info(f"[AUTO] {prompt} -> {mode} (default)")
        return mode

    if default.lower() == "y":
        bracket = "[y]/n/a(all)"
    elif default.lower() == "a":
        bracket = "y/n/[a](all)"
    else:
        bracket = "y/[n]/a(all)"
    print(f"\n{prompt} ({bracket}): ", end="", flush=True)
    default_key = {"y": b"y", "a": b"a"}.get(default.lower(), b"n")
    key = _read_single_key((b"y", b"Y", b"n", b"N", b"a", b"A"), default_key)
    if key in (b"a", b"A"):
        return "all"
    if key in (b"y", b"Y"):
        return "one"
    return "no"


def run_command(command, cwd=None, shell=False, env=None):
    try:
        if isinstance(command, list):
            cmd_str = " ".join(str(c) for c in command)
        else:
            cmd_str = command
        print_info(f"実行中: {cmd_str}")
        subprocess.run(command, cwd=cwd, shell=shell, check=True, capture_output=False, text=True, env=env)
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"コマンド実行エラー: {e}")
        return False
    except Exception as e:
        print_error(f"予期しないエラー: {e}")
        return False


# ============================================================
# 共通（グローバル）セットアップ
# ============================================================
def npm_command():
    return f"{FRONTEND_COMMAND}.cmd" if sys.platform == "win32" else FRONTEND_COMMAND


def _command_version(executable, version_arg="--version"):
    """コマンドを実際に実行し、バージョン文字列を返す。動かなければ None。

    `shutil.which` による PATH 存在チェックだけでは、Node を一度アンインストール
    した後も `%APPDATA%\\npm` に残る `npm.cmd` / `npx.cmd` 等のシムを拾ってしまい、
    node 本体が無いのに「導入済み」と誤判定する。実行して終了コードまで確認し、
    あわせてバージョン表示用の文字列を取得する。
    """
    import shutil
    path = shutil.which(executable)
    if path is None:
        return None
    try:
        result = subprocess.run(
            [path, version_arg],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=20,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            return None
        text = (result.stdout or "").strip()
        return text.splitlines()[0] if text else "(バージョン不明)"
    except Exception:
        return None


def get_git_version():
    return _command_version("git")


def get_node_version():
    return _command_version("node")


def get_npm_version():
    return _command_version(npm_command()) or _command_version(FRONTEND_COMMAND)


def get_node_toolchain_version():
    """Node.js 本体（と判明すれば npm）のバージョン文字列を返す。未導入は None。"""
    node_v = get_node_version()
    if node_v is None:
        return None
    npm_v = get_npm_version()
    return f"{node_v} / npm {npm_v}" if npm_v else node_v


def check_npm_installed():
    return get_npm_version() is not None


def check_git_installed():
    return get_git_version() is not None


def check_node_installed():
    return get_node_version() is not None


def install_prerequisite(name, win_command, download_url) -> bool:
    """前提ツール(git/node)を導入する。Windows は winget を使う。"""
    if sys.platform != "win32":
        print_warning(f"{name}: 自動導入は Windows のみ対応です。手動で導入してください: {download_url}")
        return False
    import shutil
    if shutil.which("winget") is None:
        print_error(f"{name}: winget が見つからないため自動導入できません。手動で導入してください: {download_url}")
        return False
    return run_command(win_command)


def ensure_prerequisites() -> bool:
    """git / Node.js の導入確認。未導入なら [y]/n で導入を促す。

    通常の導入ステップは git / Node.js が導入済みであることを前提とする。
    両方とも導入済み（または導入成功）なら True を返す。
    """
    print_header("前提ツール確認: Git / Node.js")
    print_info("通常のセットアップは Git と Node.js が導入済みであることを前提とします。")

    all_ok = True

    for name, version_getter, win_command, url in (
        ("Git", get_git_version, GIT_INSTALL_COMMAND_WINDOWS, GIT_DOWNLOAD_URL),
        ("Node.js", get_node_toolchain_version, NODE_INSTALL_COMMAND_WINDOWS, NODE_DOWNLOAD_URL),
    ):
        version = version_getter()
        if version is not None:
            print_success(f"{name} は導入済みです。（{version}）")
            continue

        print_warning(f"{name} が見つかりません。")
        if ask_yes_no(f"{name} を導入しますか？", default="y"):
            installed = install_prerequisite(name, win_command, url)
            new_version = version_getter()
            if installed and new_version is not None:
                print_success(f"{name} を導入しました。（{new_version}）")
            else:
                print_warning(
                    f"{name} の導入を現在のシェルで確認できませんでした。"
                    " PATH 反映のためターミナルの再起動が必要な場合があります。"
                )
                all_ok = False
        else:
            print_warning(f"{name} の導入をスキップしました。手動で導入してください: {url}")
            all_ok = False

    if not all_ok:
        print_warning("Git / Node.js が未導入のままです。一部のセットアップが失敗する可能性があります。")

    return all_ok


def get_antigravity_install_command() -> str:
    return ANTIGRAVITY_INSTALL_COMMAND_WINDOWS if sys.platform == "win32" else ANTIGRAVITY_INSTALL_COMMAND_UNIX


def prepare_antigravity_installer():
    import tempfile
    import urllib.request
    install_url = (
        "https://antigravity.google/cli/install.cmd"
        if sys.platform == "win32"
        else "https://antigravity.google/cli/install.sh"
    )
    suffix = ".cmd" if sys.platform == "win32" else ".sh"
    try:
        with urllib.request.urlopen(install_url) as response:
            installer_bytes = response.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix="antigravity_install_") as tmp:
            tmp.write(installer_bytes)
            installer_path = Path(tmp.name)
        if sys.platform != "win32":
            installer_path.chmod(0o700)
        if sys.platform == "win32":
            return ["cmd", "/c", str(installer_path)], installer_path
        return ["/bin/bash", str(installer_path)], installer_path
    except Exception as exc:
        print_error(f"antigravity インストーラーの準備に失敗しました: {exc}")
        return None, None


def cleanup_temp_file(path) -> None:
    if path is None:
        return
    try:
        if path.exists():
            path.unlink()
    except Exception:
        pass


def print_ai_cli_manual_setup():
    print_info("共通: AI CLI ツールは個別にセットアップできます。")
    print_info("  個別セットアップ例:")
    if check_npm_installed():
        cmd = npm_command()
        print_info(f"    Claude Code : {cmd} install -g @anthropic-ai/claude-code")
        print_info(f"    GitHub Copilot: {cmd} install -g @github/copilot")
        print_info(f"    OpenAI Codex : {cmd} install -g @openai/codex")
        print_info(f"    OpenCode   : {cmd} install -g opencode-ai")
    else:
        print_info("    npm 系 CLI : Node.js / npm を導入後に個別セットアップしてください")
        print_info("      https://nodejs.org/")
    print_info(f"    Antigravity: {get_antigravity_install_command()}")
    print_info(f"    Hermes Agent: {HERMES_AGENT_INSTALL_COMMAND}")
    print_info(f"    Ollama     : {OLLAMA_INSTALL_COMMAND}")


def start_global_cli_tools_install():
    print_header("共通セットアップ: AI CLI ツール投入")
    print_info("対象: Anthropic / GitHub Copilot / OpenAI Codex / OpenCode / Antigravity")
    print_info("参考: Hermes Agent は npm ではなく、次の bash installer で導入します。")
    print_info(f"      {HERMES_AGENT_INSTALL_COMMAND}")
    print_info("参考: Ollama は次のコマンドで導入できます。")
    print_info(f"      {OLLAMA_INSTALL_COMMAND}")
    print_info("AI CLI ツールを並列で投入します。完了確認は最後にまとめて行います。")

    targets = []
    if check_npm_installed():
        cmd = npm_command()
        for package in ["@anthropic-ai/claude-code", "@github/copilot", "@openai/codex", "opencode-ai"]:
            command = [cmd, "install", "-g", package]
            targets.append((package, command, " ".join(command), None))
    else:
        print_warning("共通: npm がインストールされていないため、npm 系 CLI はスキップします。")
        print_info("  Node.js をインストールしてください: https://nodejs.org/")

    antigravity_command, antigravity_temp_path = prepare_antigravity_installer()
    if antigravity_command:
        targets.append(("antigravity", antigravity_command, get_antigravity_install_command(), antigravity_temp_path))

    GLOBAL_CLI_INSTALL_PROCESSES.clear()
    for i, (label, command, display_command, temp_path) in enumerate(targets, 1):
        print_info(f"  [{i}/{len(targets)}] 投入: {display_command}")
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
            )
            GLOBAL_CLI_INSTALL_PROCESSES.append((label, process, temp_path))
            print_success(f"  [{i}/{len(targets)}] {label}: 投入完了")
        except Exception as exc:
            print_error(f"  [{i}/{len(targets)}] {label}: 投入失敗 - {exc}")
            cleanup_temp_file(temp_path)

    if not GLOBAL_CLI_INSTALL_PROCESSES:
        print_warning("共通: AI CLI ツールの投入対象がありませんでした。")
        return False

    print_success("共通: AI CLI ツールの投入を開始しました。")
    return True


def wait_global_cli_tools_install() -> list[str]:
    if not GLOBAL_CLI_INSTALL_PROCESSES:
        return []

    print_header("共通セットアップ: AI CLI ツール完了確認")
    print_info("並列投入した AI CLI ツールの導入結果を確認します...")

    failed_packages = []
    for i, (package, process, temp_path) in enumerate(GLOBAL_CLI_INSTALL_PROCESSES, 1):
        try:
            stdout, stderr = process.communicate(timeout=300)
            if process.returncode == 0:
                print_success(f"  [{i}/{len(GLOBAL_CLI_INSTALL_PROCESSES)}] {package}: 導入完了")
            else:
                print_error(f"  [{i}/{len(GLOBAL_CLI_INSTALL_PROCESSES)}] {package}: 導入失敗 (終了コード: {process.returncode})")
                detail = (stderr or stdout or "").strip()
                if detail:
                    print_error(f"      エラー内容: {detail[:200]}")
                failed_packages.append(package)
        except subprocess.TimeoutExpired:
            process.kill()
            print_error(f"  [{i}/{len(GLOBAL_CLI_INSTALL_PROCESSES)}] {package}: タイムアウト")
            failed_packages.append(package)
        except Exception as exc:
            print_error(f"  [{i}/{len(GLOBAL_CLI_INSTALL_PROCESSES)}] {package}: エラー - {exc}")
            failed_packages.append(package)
        finally:
            cleanup_temp_file(temp_path)

    GLOBAL_CLI_INSTALL_PROCESSES.clear()

    if failed_packages:
        print_warning(f"共通: 一部 AI CLI ツールの導入に失敗しました: {', '.join(failed_packages)}")
        return failed_packages

    print_success("共通: AI CLI ツールの導入確認が完了しました。")
    return []


def setup_common_global_tools(choices: dict) -> list[str]:
    print_header("共通セットアップ")
    print_info("対象: pip / wheel / setuptools / uv / AI CLI ツール")

    error_locations: list[str] = []

    if choices.get("common_python_upgrade"):
        commands = [
            ([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], "pip"),
            (["pip", "install", "--upgrade", "wheel"], "wheel"),
            (["pip", "install", "--upgrade", "setuptools"], "setuptools"),
            (["pip", "install", "--upgrade", "uv"], "uv"),
        ]
        failed_tools = []
        for cmd, tool_name in commands:
            if not run_command(cmd):
                failed_tools.append(tool_name)
        if failed_tools:
            print_warning(f"共通: 一部ツールのアップグレードに失敗しました: {', '.join(failed_tools)}")
            error_locations.extend([f"共通: Python ツール更新 ({tool_name})" for tool_name in failed_tools])
        else:
            print_success("共通: Python ツールのアップグレードが完了しました。")
    else:
        print_warning("共通: Python ツールのアップグレードをスキップしました。")

    if choices.get("common_npm_install"):
        start_global_cli_tools_install()
    else:
        print_warning("共通: AI CLI ツールのインストールをスキップしました。")
        print_ai_cli_manual_setup()

    return error_locations


# ============================================================
# 選択収集
# ============================================================
def collect_setup_choices() -> dict | None:
    """全ての y/n を最初にまとめて聞く。キャンセル時は None を返す。"""
    global AUTO_MODE

    run_setup, AUTO_MODE = ask_start_mode("セットアップを実行しますか?", default="n")
    if not run_setup:
        return None

    if AUTO_MODE:
        print_info("AUTOモードで実行します。以降の質問はデフォルト値で自動回答します。")

    print_header("セットアップ内容の選択")
    print_info("最初に実行項目をまとめて選択してください。処理はまとめて一括実行されます。")

    choices: dict = {
        "common":                False,
        "common_python_upgrade": False,
        "common_npm_install":    False,
        "backend":               False,
        "pg_user_created":       False,
        "pg_restore":            False,
        "pg_migrate":            False,
        "local":                 False,
        "local_download":        "no",
        "task":                  False,
        "team":                  False,
        "mcp":                   False,
        "mcp_config":            False,
        "web":                   False,
        "avatar":                False,
        "hermes":                False,
        "continue_on_error":     False,
    }

    choices["common"] = ask_yes_no("共通セットアップを実行しますか？", default="y")
    if choices["common"]:
        choices["common_python_upgrade"] = ask_yes_no("共通: グローバル環境 Python ツールをアップグレードしますか？", default="y")
        choices["common_npm_install"]    = ask_yes_no("共通: グローバル環境の AI CLI ツール(npm + Antigravity)をインストール/アップデートしますか？", default="n")

    choices["local"] = ask_yes_no("バックエンド(local)のセットアップを実行しますか？", default="y")
    if choices["local"]:
        choices["local_download"] = ask_download_mode("バックエンド(local): モデルを事前ダウンロードしますか？（n=しない / y=設定モデル / a=候補一括 ※劇遅注意）", default="n")

    choices["mcp"] = ask_yes_no("バックエンド(tools) のセットアップを実行しますか？", default="y")
    if choices["mcp"]:
        choices["mcp_config"] = ask_yes_no("バックエンド(tools): backend_tools の MCP 機能を使えるよう構成しますか？", default="y")

    choices["backend"] = ask_yes_no("バックエンド(core,apps)のセットアップを実行しますか？", default="y")
    if choices["backend"] and DATABASE_TYPE.lower() == "postgresql":
        choices["pg_user_created"] = ask_yes_no("バックエンド: PostgreSQL ユーザー(appsuser)を作成しましたか？", default="y")
        choices["pg_restore"]      = ask_yes_no("バックエンド: 初期データベースを復元しますか？", default="n")
        choices["pg_migrate"]      = ask_yes_no("バックエンド: マイグレーション(alembic upgrade head)を実行しますか？", default="y")

    choices["task"] = ask_yes_no("バックエンド(task)のセットアップを実行しますか？", default="y")
    choices["team"] = ask_yes_no("バックエンド(team)のセットアップを実行しますか？", default="y")

    choices["web"] = ask_yes_no("フロントエンド(Web)のセットアップを実行しますか？", default="y")
    choices["avatar"] = ask_yes_no("フロントエンド(Avatar)のセットアップを実行しますか？", default="y")
    choices["hermes"] = ask_yes_no("コマンド(hermes)のセットアップを実行しますか？", default="y")

    choices["continue_on_error"] = ask_yes_no("エラーが発生しても続行しますか？", default="y")

    return choices


# ============================================================
# メイン
# ============================================================
def main():
    print_header("プロジェクト セットアップ")
    print(f"{Colors.BOLD}このスクリプトは、プロジェクト全体の初期セットアップを実行します。{Colors.ENDC}")
    print_info("セットアップ対象:")
    print_info("  1. 共通")
    print_info("  2. バックエンド(local)")
    print_info("  3. バックエンド(tools)")
    print_info("  4. バックエンド(core,apps)")
    print_info("  5. バックエンド(task)")
    print_info("  6. バックエンド(team)")
    print_info("  7. フロントエンド(Web)")
    print_info("  8. フロントエンド(Avatar)")
    print_info("  9. コマンド(hermes)")
    print()

    ensure_prerequisites()

    choices = collect_setup_choices()
    if choices is None:
        print_warning("セットアップをキャンセルしました。")
        sys.exit(0)

    print_header("一括実行開始")
    continue_on_error = choices["continue_on_error"]
    error_locations: list[str] = []

    print()
    if choices["common"]:
        error_locations.extend(setup_common_global_tools(choices))
        if GLOBAL_CLI_INSTALL_PROCESSES:
            print()
            failed_packages = wait_global_cli_tools_install()
            error_locations.extend([f"共通: AI CLI ツール導入 ({package})" for package in failed_packages])
    else:
        print_warning("共通セットアップをスキップしました。")

    print()
    if choices["local"]:
        local_mod = _load_folder_module("backend_local")
        if not local_mod.setup(choices):
            error_locations.append("バックエンド(local)")
            if not continue_on_error:
                print_setup_summary(error_locations)
                sys.exit(1)
    else:
        print_warning("バックエンド(local)のセットアップをスキップしました。")

    print()
    if choices["mcp"]:
        tools_mod = _load_folder_module("backend_tools")
        if not tools_mod.setup_dependencies():
            error_locations.append("バックエンド(tools)")
            if not continue_on_error:
                print_setup_summary(error_locations)
                sys.exit(1)
        print()
        tools_mod.show_current_config()
        if choices["mcp_config"]:
            if not tools_mod.configure_clients():
                error_locations.append("tools: MCP 設定ファイル書き込み")
                if not continue_on_error:
                    print_setup_summary(error_locations)
                    sys.exit(1)
        else:
            print_warning("backend_tools の MCP 設定ファイル書き込みをスキップしました。")
    else:
        print_warning("バックエンド(tools) のセットアップをスキップしました。")

    print()
    if choices["backend"]:
        backend_mod = _load_folder_module("backend_server")
        if not backend_mod.setup(choices):
            error_locations.append("バックエンド(core,apps)")
            if not continue_on_error:
                print_setup_summary(error_locations)
                sys.exit(1)
    else:
        print_warning("バックエンド(core,apps)のセットアップをスキップしました。")

    print()
    if choices["task"]:
        task_mod = _load_folder_module("backend_task")
        if not task_mod.setup(choices):
            error_locations.append("バックエンド(task)")
            if not continue_on_error:
                print_setup_summary(error_locations)
                sys.exit(1)
    else:
        print_warning("バックエンド(task)のセットアップをスキップしました。")

    print()
    if choices["team"]:
        team_mod = _load_folder_module("backend_team")
        if not team_mod.setup(choices):
            error_locations.append("バックエンド(team)")
            if not continue_on_error:
                print_setup_summary(error_locations)
                sys.exit(1)
    else:
        print_warning("バックエンド(team)のセットアップをスキップしました。")

    print()
    if choices["web"]:
        web_mod = _load_folder_module("frontend_web")
        if not web_mod.setup(choices):
            error_locations.append("フロントエンド(Web)")
            if not continue_on_error:
                print_setup_summary(error_locations)
                sys.exit(1)
    else:
        print_warning("フロントエンド(Web)のセットアップをスキップしました。")

    print()
    if choices["avatar"]:
        avatar_mod = _load_folder_module("frontend_avatar")
        if not avatar_mod.setup(choices):
            error_locations.append("フロントエンド(Avatar)")
            if not continue_on_error:
                print_setup_summary(error_locations)
                sys.exit(1)
    else:
        print_warning("フロントエンド(Avatar)のセットアップをスキップしました。")

    # モデル事前ダウンロードは時間がかかるため、別プロセスで投入する。
    # Hermes はセットアップ全体の最後に回すため、その前に投入だけ済ませる。
    print()
    if choices["local"]:
        local_mod = _load_folder_module("backend_local")
        local_mod.launch_model_download(choices)

    print()
    if choices["hermes"]:
        hermes_mod = _load_folder_module("command_hermes")
        if not hermes_mod.setup(choices):
            error_locations.append("コマンド(hermes)")
            if not continue_on_error:
                print_setup_summary(error_locations)
                sys.exit(1)
    else:
        print_warning("コマンド(hermes)のセットアップをスキップしました。")

    print_setup_summary(error_locations)
    print_info("起動方法:")
    print_info("  全体起動: python _start.py")
    print_info("  個別起動:")
    print_info("    Local起動: cd backend_local && uv run uvicorn local_main:app --reload --host 0.0.0.0 --port 8096")
    print_info("    MCP起動  : cd backend_tools && uv run uvicorn tools_main:app --reload --host 0.0.0.0 --port 8095")
    print_info("    Core起動 : cd backend_server && uv run uvicorn core_main:app --reload --host 0.0.0.0 --port 8091")
    print_info("    Apps起動 : cd backend_server && uv run uvicorn apps_main:app --reload --host 0.0.0.0 --port 9098")
    print_info("    Task起動 : cd backend_task && uv run uvicorn task_main:app --reload --host 0.0.0.0 --port 8093")
    print_info("    Team起動 : cd backend_team && uv run uvicorn team_main:app --reload --host 0.0.0.0 --port 8094")
    print_info("    Web開発  : cd frontend_web && npm run dev")
    print_info("    Avatar   : cd frontend_avatar && npm run dev")
    if sys.platform == "win32":
        print_info("    Hermes起動: aidiy_hermes.cmd または cd command_hermes && .venv/Scripts/python.exe cli_main.py")
    else:
        print_info("    Hermes起動: aidiy_hermes または cd command_hermes && .venv/bin/python cli_main.py")

    print()
    print_success("セットアップは正常終了しました。")
    if choices["local"] and choices.get("local_download") in ("one", "all"):
        print_info("バックエンド(local) のモデルダウンロードは別プロセスで継続中です。")
    print_info("5秒後に終了します...")
    time.sleep(5)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_warning("セットアップが中断されました。")
        sys.exit(130)
    except Exception as e:
        print_error(f"予期しないエラーが発生しました: {e}")
        sys.exit(1)
