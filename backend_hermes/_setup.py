# -*- coding: utf-8 -*-

"""バックエンド(hermes) セットアップスクリプト

このフォルダ (backend_hermes) 単体のセットアップを行います。
仮想環境作成・依存関係インストールに加え、`aidiy_hermes` ランチャーの作成と
（非 Windows では）シェル PATH への登録を行います。

公開 API:
    setup(choices=None) -> bool
"""

import os
import subprocess
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    import msvcrt

# ============================================================
# 設定
# ============================================================
THIS_DIR = Path(__file__).resolve().parent
BACKEND_HERMES_DIR = THIS_DIR
BACKEND_HERMES_ENV = ".venv"
SHELL_PATH_MARKER_BEGIN = "# >>> AiDiy Hermes PATH >>>"
SHELL_PATH_MARKER_END = "# <<< AiDiy Hermes PATH <<<"

AUTO_MODE = False


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


def check_uv_installed():
    import shutil
    return shutil.which("uv") is not None


def _remove_marked_block(content: str, begin_marker: str, end_marker: str) -> str:
    lines = content.splitlines()
    result: list[str] = []
    skipping = False
    for line in lines:
        stripped = line.strip()
        if stripped == begin_marker:
            skipping = True
            continue
        if skipping and stripped == end_marker:
            skipping = False
            continue
        if not skipping:
            result.append(line)
    while result and result[-1].strip() == "":
        result.pop()
    return "\n".join(result).rstrip() + ("\n" if result else "")


def get_shell_profile_paths() -> list[Path]:
    if sys.platform == "win32":
        return []
    home = Path.home()
    if sys.platform == "darwin":
        return [home / ".zprofile", home / ".zshrc", home / ".bash_profile"]
    return [home / ".profile", home / ".bashrc"]


def ensure_shell_path_entry(bin_dir: Path, label: str) -> bool:
    if sys.platform == "win32":
        return True

    export_line = f'export PATH="{bin_dir}:$PATH"'
    block = "\n".join([SHELL_PATH_MARKER_BEGIN, export_line, SHELL_PATH_MARKER_END]) + "\n"
    updated_any = False

    for profile_path in get_shell_profile_paths():
        try:
            original = profile_path.read_text(encoding="utf-8") if profile_path.exists() else ""
            cleaned = _remove_marked_block(original, SHELL_PATH_MARKER_BEGIN, SHELL_PATH_MARKER_END).rstrip()
            updated = (cleaned + "\n\n" if cleaned else "") + block
            profile_path.parent.mkdir(parents=True, exist_ok=True)
            profile_path.write_text(updated, encoding="utf-8")
            print_success(f"{label}: PATH 設定を書き込みました: {profile_path}")
            updated_any = True
        except Exception as e:
            print_warning(f"{label}: PATH 設定の書き込みに失敗しました: {profile_path} ({e})")

    return updated_any


# ============================================================
# セットアップ本体
# ============================================================
def setup(choices: dict | None = None) -> bool:
    label = "バックエンド(hermes)"
    print_header(f"{label} セットアップ")
    print_info(f"作業ディレクトリ: {BACKEND_HERMES_DIR}")
    print_info("対象: Hermes CLI / pyproject.toml / uv")

    if not BACKEND_HERMES_DIR.exists():
        print_error(f"{label}: フォルダが見つかりません: {BACKEND_HERMES_DIR}")
        return False

    if not check_uv_installed():
        print_error(f"{label}: uv がインストールされていません。")
        print_info("  PowerShell: irm https://astral.sh/uv/install.ps1 | iex")
        print_info("  または: pip install uv")
        return False

    req_file = BACKEND_HERMES_DIR / "pyproject.toml"
    if not req_file.exists():
        print_error(f"{label}: pyproject.toml が見つかりません: {req_file}")
        return False

    venv_dir = BACKEND_HERMES_DIR / BACKEND_HERMES_ENV
    if not venv_dir.exists():
        print_info(f"{label}: 仮想環境を作成します...")
        if not run_command(["uv", "venv", BACKEND_HERMES_ENV], cwd=BACKEND_HERMES_DIR):
            print_error(f"{label}: 仮想環境の作成に失敗しました。")
            return False

    # uv sync --upgrade で依存関係を最新解決する
    if not run_command(["uv", "sync", "--upgrade"], cwd=BACKEND_HERMES_DIR):
        print_error(f"{label}: uv sync --upgrade に失敗しました。")
        return False

    hermes_dir = BACKEND_HERMES_DIR.resolve()
    cli_path = hermes_dir / "cli_main.py"
    launcher_dir = Path.home() / ".local" / "bin"
    launcher_dir.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        launcher_path = launcher_dir / "aidiy_hermes.cmd"
        py_path = hermes_dir / BACKEND_HERMES_ENV / "Scripts" / "python.exe"
        launcher_content = (
            "@echo off\n"
            "chcp 65001 >nul\n"
            "setlocal\n"
            "\n"
            f'set "PY={py_path}"\n'
            f'set "CLI={cli_path}"\n'
            "\n"
            'if not exist "%PY%" (\n'
            '  echo Python virtual environment was not found:\n'
            '  echo   %PY%\n'
            '  pause\n'
            '  exit /b 1\n'
            ')\n'
            "\n"
            '"%PY%" "%CLI%" %*\n'
        )
    else:
        launcher_path = launcher_dir / "aidiy_hermes"
        py_path = hermes_dir / BACKEND_HERMES_ENV / "bin" / "python"
        launcher_content = (
            "#!/usr/bin/env sh\n"
            f'PY="{py_path}"\n'
            f'CLI="{cli_path}"\n'
            'if [ ! -x "$PY" ]; then\n'
            '  echo "Python virtual environment was not found:"\n'
            '  echo "  $PY"\n'
            '  exit 1\n'
            'fi\n'
            'exec "$PY" "$CLI" "$@"\n'
        )
    try:
        launcher_path.write_text(launcher_content, encoding="utf-8")
        if sys.platform != "win32":
            launcher_path.chmod(0o755)
        print_success(f"{label}: {launcher_path.name} を作成しました: {launcher_path}")
        print_info(f"  Python: {py_path}")
        print_info(f"  CLI   : {cli_path}")
        if sys.platform != "win32" and str(launcher_dir) not in os.environ.get("PATH", "").split(os.pathsep):
            print_warning(f"{label}: {launcher_dir} が PATH に見つかりません。")
            if ensure_shell_path_entry(launcher_dir, label):
                print_info("  シェル設定へ PATH を追記しました。ターミナル再起動後に有効です。")
            else:
                print_info(f"  例: export PATH=\"{launcher_dir}:$PATH\"")
    except Exception as e:
        print_warning(f"{label}: {launcher_path.name} の作成に失敗しました: {e}")

    print_success(f"{label}: セットアップが完了しました。")
    return True


def main():
    global AUTO_MODE
    print_header("バックエンド(hermes) セットアップ")
    run_setup, AUTO_MODE = ask_start_mode("バックエンド(hermes) のセットアップを実行しますか?", default="n")
    if not run_setup:
        print_warning("セットアップをキャンセルしました。")
        return
    if AUTO_MODE:
        print_info("AUTOモードで実行します。")
    ok = setup()
    if not ok:
        print_error("バックエンド(hermes) のセットアップに失敗しました。")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_warning("セットアップが中断されました。")
        sys.exit(130)
