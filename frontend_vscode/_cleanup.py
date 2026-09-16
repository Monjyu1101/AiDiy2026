# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""フロントエンド(VS Code) クリーンアップスクリプト

VS Code 拡張機能をアンインストールし、依存関係と生成物を削除します。

公開 API:
    cleanup(choices=None) -> bool
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


THIS_DIR = Path(__file__).resolve().parent
FRONTEND_VSCODE_DIR = THIS_DIR

AUTO_MODE = False


class Colors:
    HEADER = "\033[97m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


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


def handle_remove_readonly(func, path, exc_info):
    del exc_info
    os.chmod(path, stat.S_IWRITE)
    func(path)


def remove_directory(path: Path, description: str) -> bool:
    if not path.is_dir():
        return False
    try:
        shutil.rmtree(path, onerror=handle_remove_readonly)
        print_success(f"{description} を削除しました: {path}")
        return True
    except Exception as exc:
        print_error(f"{description} の削除に失敗しました: {path}")
        print_error(f"  理由: {exc}")
        return False


def remove_file(path: Path, description: str) -> bool:
    if not path.is_file():
        return False
    try:
        if not os.access(path, os.W_OK):
            os.chmod(path, stat.S_IWRITE)
        path.unlink()
        print_success(f"{description} を削除しました: {path}")
        return True
    except Exception as exc:
        print_error(f"{description} の削除に失敗しました: {path}")
        print_error(f"  理由: {exc}")
        return False


def _is_working_vscode_cli(command: str) -> bool:
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


def get_extension_id() -> str | None:
    try:
        package = json.loads(
            (FRONTEND_VSCODE_DIR / "package.json").read_text(encoding="utf-8")
        )
        return f"{package['publisher']}.{package['name']}"
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        print_warning(f"拡張機能 ID の取得に失敗しました: {exc}")
        return None


def get_installed_extensions(vscode_cli: str) -> set[str] | None:
    try:
        result = subprocess.run(
            [vscode_cli, "--list-extensions"],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        return {line.strip().lower() for line in result.stdout.splitlines() if line.strip()}
    except (OSError, subprocess.SubprocessError) as exc:
        print_warning(f"VS Code 拡張機能一覧の確認に失敗しました: {exc}")
        return None


def uninstall_extension() -> tuple[bool, int]:
    extension_id = get_extension_id()
    vscode_cli = find_vscode_cli()
    if extension_id is None:
        return False, 0
    if vscode_cli is None:
        print_warning("VS Code CLI (code) が見つからないため、拡張機能の解除を確認できません。")
        return False, 0

    try:
        installed = get_installed_extensions(vscode_cli)
        if installed is None:
            return False, 0
        if extension_id.lower() not in installed:
            print_info(f"VS Code 拡張機能は配置されていません: {extension_id}")
            return True, 0
        print_info(f"実行中: {vscode_cli} --uninstall-extension {extension_id}")
        subprocess.run(
            [vscode_cli, "--uninstall-extension", extension_id],
            check=True,
            text=True,
            timeout=60,
        )
        installed_after = get_installed_extensions(vscode_cli)
        if installed_after is None or extension_id.lower() in installed_after:
            print_warning(f"VS Code 拡張機能が解除されたことを確認できません: {extension_id}")
            return False, 0
        print_success(f"VS Code 拡張機能を解除しました: {extension_id}")
        print_info("  VS Code 本体は停止していません。反映にはウィンドウ再読み込みが必要です。")
        return True, 1
    except subprocess.CalledProcessError as exc:
        print_warning(f"VS Code 拡張機能の解除に失敗しました: {exc}")
        return False, 0
    except Exception as exc:
        print_warning(f"VS Code 拡張機能の確認に失敗しました: {exc}")
        return False, 0


def cleanup(choices: dict | None = None) -> bool:
    del choices
    label = "フロントエンド(VS Code)"
    print_header(f"{label} のクリーンアップ")

    extension_ok, deleted_count = uninstall_extension()
    cleanup_ok = extension_ok
    for directory_name in ("node_modules", "dist", "out", "__pycache__", ".pytest_cache"):
        directory_path = FRONTEND_VSCODE_DIR / directory_name
        existed = directory_path.is_dir()
        if remove_directory(
            directory_path,
            f"{directory_name} ({label})",
        ):
            deleted_count += 1
        elif existed:
            cleanup_ok = False

    for vsix_path in sorted(FRONTEND_VSCODE_DIR.glob("*.vsix")):
        existed = vsix_path.is_file()
        if remove_file(vsix_path, f"VSIX ({label})"):
            deleted_count += 1
        elif existed:
            cleanup_ok = False

    if cleanup_ok and deleted_count > 0:
        print_success(f"{label} のクリーンアップ完了 ({deleted_count}個削除)")
    elif cleanup_ok:
        print_info(f"{label}: 削除対象はありませんでした")
    else:
        print_warning(f"{label}: 一部のクリーンアップを完了できませんでした")
    return cleanup_ok


def main():
    global AUTO_MODE
    print_header("フロントエンド(VS Code) クリーンアップ")
    run_cleanup, AUTO_MODE = ask_start_mode("クリーンアップを実行しますか？", default="n")
    if not run_cleanup:
        print_info("クリーンアップをキャンセルしました")
        return
    if AUTO_MODE:
        print_info("AUTOモードで実行します。")
    if not cleanup():
        sys.exit(1)
    print_success("クリーンアップが完了しました")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_warning("クリーンアップが中断されました")
        sys.exit(1)
