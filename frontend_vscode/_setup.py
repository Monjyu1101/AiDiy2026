# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""フロントエンド(VS Code) セットアップスクリプト

Node.js 依存関係を導入して VSIX を生成し、VS Code 拡張機能として配置します。

公開 API:
    setup(choices=None) -> bool
"""

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    import msvcrt


THIS_DIR = Path(__file__).resolve().parent
FRONTEND_VSCODE_DIR = THIS_DIR
FRONTEND_COMMAND = "npm"

AUTO_MODE = False


class Colors:
    HEADER = "\033[97m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"


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


def run_command(command, cwd=None) -> bool:
    try:
        print_info(f"実行中: {' '.join(str(part) for part in command)}")
        subprocess.run(command, cwd=cwd, check=True, text=True)
        return True
    except subprocess.CalledProcessError as exc:
        print_error(f"コマンド実行エラー: {exc}")
        return False
    except Exception as exc:
        print_error(f"予期しないエラー: {exc}")
        return False


def npm_command() -> str:
    return f"{FRONTEND_COMMAND}.cmd" if sys.platform == "win32" else FRONTEND_COMMAND


def _is_working_vscode_cli(command: str) -> bool:
    """ファイルの存在だけでなく、実際に応答できる VS Code CLI か確認する。"""
    try:
        result = subprocess.run(
            [command, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def find_vscode_cli() -> str | None:
    """稼働中の Remote CLI、PATH、標準配置先の順に VS Code CLI を探す。"""
    candidates: list[Path] = []

    # Codespaces / Dev Container / Remote SSH の統合ターミナルでは、PATH 上の
    # `code` が利用不能でも、稼働中サーバーの Remote CLI を利用できる。
    vscode_cwd = os.environ.get("VSCODE_CWD")
    if vscode_cwd:
        candidates.append(Path(vscode_cwd) / "bin" / "remote-cli" / "code")

    command_names = (
        ("code.cmd", "code-insiders.cmd", "code", "code-insiders")
        if sys.platform == "win32"
        else ("code", "code-insiders")
    )
    for command_name in command_names:
        path = shutil.which(command_name)
        if path:
            candidates.append(Path(path))

    if sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            candidates.extend(
                (
                    Path(local_app_data)
                    / "Programs"
                    / "Microsoft VS Code"
                    / "bin"
                    / "code.cmd",
                    Path(local_app_data)
                    / "Programs"
                    / "Microsoft VS Code Insiders"
                    / "bin"
                    / "code-insiders.cmd",
                )
            )
        for env_name in ("PROGRAMFILES", "PROGRAMFILES(X86)"):
            base = os.environ.get(env_name)
            if base:
                candidates.extend(
                    (
                        Path(base) / "Microsoft VS Code" / "bin" / "code.cmd",
                        Path(base)
                        / "Microsoft VS Code Insiders"
                        / "bin"
                        / "code-insiders.cmd",
                    )
                )
    elif sys.platform == "darwin":
        candidates.extend(
            (
                Path("/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"),
                Path(
                    "/Applications/Visual Studio Code - Insiders.app/Contents/Resources/app/bin/code-insiders"
                ),
            )
        )

    checked: set[str] = set()
    for candidate in candidates:
        candidate_text = str(candidate)
        if candidate_text in checked:
            continue
        checked.add(candidate_text)
        if candidate.is_file() and _is_working_vscode_cli(candidate_text):
            return candidate_text
    return None


def get_extension_metadata() -> tuple[str, str, Path] | None:
    package_json = FRONTEND_VSCODE_DIR / "package.json"
    try:
        package = json.loads(package_json.read_text(encoding="utf-8"))
        extension_id = f"{package['publisher']}.{package['name']}"
        version = str(package["version"])
        vsix_path = (
            FRONTEND_VSCODE_DIR
            / "dist"
            / f"{package['name']}-{version}.vsix"
        )
        return extension_id, version, vsix_path
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        print_error(f"package.json の読み込みに失敗しました: {exc}")
        return None


def get_installed_extensions(vscode_cli: str, show_versions: bool = False) -> set[str] | None:
    command = [vscode_cli, "--list-extensions"]
    if show_versions:
        command.append("--show-versions")
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        return {line.strip().lower() for line in result.stdout.splitlines() if line.strip()}
    except (OSError, subprocess.SubprocessError) as exc:
        print_error(f"VS Code 拡張機能一覧の確認に失敗しました: {exc}")
        return None


def setup(choices: dict | None = None) -> bool:
    del choices
    label = "フロントエンド(VS Code)"
    print_header(f"{label} セットアップ")
    print_info(f"作業ディレクトリ: {FRONTEND_VSCODE_DIR}")
    print_info("対象: VS Code チャット拡張 / TypeScript / VSIX")

    package_json = FRONTEND_VSCODE_DIR / "package.json"
    if not package_json.is_file():
        print_error(f"{label}: package.json が見つかりません: {package_json}")
        return False

    npm_path = shutil.which(npm_command()) or shutil.which(FRONTEND_COMMAND)
    if npm_path is None:
        print_error(f"{label}: npm がインストールされていません。")
        print_info("  Node.js をインストールしてください: https://nodejs.org/")
        return False

    vscode_cli = find_vscode_cli()
    if vscode_cli is None:
        print_error(f"{label}: VS Code CLI (code) が見つかりません。")
        print_info("  VS Code をインストールし、code コマンドを PATH に追加してください。")
        return False

    metadata = get_extension_metadata()
    if metadata is None:
        return False
    extension_id, version, vsix_path = metadata

    if not run_command([npm_path, "install"], cwd=FRONTEND_VSCODE_DIR):
        print_error(f"{label}: 依存関係の導入に失敗しました。")
        return False
    if not run_command([npm_path, "update"], cwd=FRONTEND_VSCODE_DIR):
        print_error(f"{label}: 依存関係の最新版への更新に失敗しました。")
        return False
    if not run_command([npm_path, "run", "package"], cwd=FRONTEND_VSCODE_DIR):
        print_error(f"{label}: VSIX の生成に失敗しました。")
        return False
    if not vsix_path.is_file():
        print_error(f"{label}: 生成された VSIX が見つかりません: {vsix_path}")
        return False

    if not run_command(
        [vscode_cli, "--install-extension", str(vsix_path), "--force"],
        cwd=FRONTEND_VSCODE_DIR,
    ):
        print_error(f"{label}: VS Code 拡張機能の配置に失敗しました。")
        return False

    installed = get_installed_extensions(vscode_cli, show_versions=True)
    expected = f"{extension_id}@{version}".lower()
    if installed is None or expected not in installed:
        print_error(f"{label}: 配置後の確認に失敗しました: {expected}")
        return False

    print_success(f"{label}: {extension_id} を VS Code 拡張機能として配置しました。")
    print_info("  VS Code 本体や AiDiy の常駐サービスは停止していません。")
    print_info("  VS Code に反映されない場合は、ウィンドウを再読み込みしてください。")
    return True


def main():
    global AUTO_MODE
    print_header("フロントエンド(VS Code) セットアップ")
    run_setup, AUTO_MODE = ask_start_mode(
        "フロントエンド(VS Code) のセットアップを実行しますか?", default="n"
    )
    if not run_setup:
        print_warning("セットアップをキャンセルしました。")
        return
    if AUTO_MODE:
        print_info("AUTOモードで実行します。")
    if not setup():
        print_error("フロントエンド(VS Code) のセットアップに失敗しました。")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_warning("セットアップが中断されました。")
        sys.exit(130)
