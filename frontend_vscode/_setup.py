# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""フロントエンド(VS Code) セットアップスクリプト

Node.js 依存関係と Electron バイナリを事前に導入して VSIX を配置し、
単独起動用ランチャーも作成します。Electron の通常取得が失敗した場合は
frontend_avatar/_setup.py と同様に Python で GitHub から取得します。

公開 API:
    setup(choices=None) -> bool
"""

import json
import os
import platform
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
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


def electron_executable_name() -> str:
    if sys.platform == "win32":
        return "electron.exe"
    if sys.platform == "darwin":
        return "Electron.app/Contents/MacOS/Electron"
    return "electron"


def electron_binary_ready(frontend_dir: Path) -> bool:
    """実行ファイル、path.txt、導入済みパッケージのバージョンを照合する。"""
    electron_dir = frontend_dir / "node_modules" / "electron"
    try:
        package = json.loads((electron_dir / "package.json").read_text(encoding="utf-8"))
        executable = electron_executable_name()
        return (
            (electron_dir / "path.txt").read_text(encoding="utf-8") == executable
            and (electron_dir / "dist" / executable).is_file()
            and (electron_dir / "dist" / "version").read_text(encoding="utf-8").strip().removeprefix("v")
            == package["version"]
        )
    except (OSError, KeyError, json.JSONDecodeError):
        return False


def install_electron_binary(frontend_dir: Path, label: str) -> bool:
    """Avatar と同じ GitHub リリース ZIP を Python で取得し、dist に配置する。"""
    electron_dir = frontend_dir / "node_modules" / "electron"
    try:
        version = json.loads((electron_dir / "package.json").read_text(encoding="utf-8"))["version"]
        machine = platform.machine().lower()
        if machine in ("arm64", "aarch64"):
            arch = "arm64"
        elif machine in ("x86", "i386", "i686"):
            arch = "ia32"
        else:
            arch = "x64"
        plat = "win32" if sys.platform == "win32" else "darwin" if sys.platform == "darwin" else "linux"
        zip_name = f"electron-v{version}-{plat}-{arch}.zip"
        url = f"https://github.com/electron/electron/releases/download/v{version}/{zip_name}"
        print_info(f"{label}: Electron v{version} ({plat}-{arch}) を Python でダウンロードします。")
        print_info(f"  URL: {url}")
        with tempfile.TemporaryDirectory(prefix="aidiy-vscode-electron-") as temporary:
            archive = Path(temporary) / zip_name
            with urllib.request.urlopen(url, timeout=60) as response, archive.open("wb") as output:
                total = int(response.headers.get("Content-Length", 0))
                downloaded = 0
                milestone = 30
                while block := response.read(1024 * 1024):
                    output.write(block)
                    downloaded += len(block)
                    if total and downloaded * 100 // total >= milestone:
                        print_info(f"  ダウンロード中... {min(downloaded * 100 // total, 100)}%")
                        milestone += 30

            # macOS のシンボリックリンクと Linux の実行権限も保持する。
            extracted = Path(temporary) / "dist"
            extracted.mkdir()
            if sys.platform != "win32" and shutil.which("unzip"):
                subprocess.run(["unzip", "-q", "-o", str(archive), "-d", str(extracted)], check=True)
            else:
                with zipfile.ZipFile(archive) as zipped:
                    zipped.extractall(extracted)
            executable = electron_executable_name()
            if not (extracted / executable).is_file():
                raise RuntimeError(f"展開した ZIP に {executable} がありません。")
            binary_version = (extracted / "version").read_text(encoding="utf-8").strip().removeprefix("v")
            if binary_version != version:
                raise RuntimeError(f"Electron のバージョンが一致しません: {binary_version} / {version}")
            if sys.platform != "win32":
                (extracted / executable).chmod(0o755)
            dist_dir = electron_dir / "dist"
            if dist_dir.exists():
                shutil.rmtree(dist_dir)
            shutil.move(str(extracted), str(dist_dir))
            (electron_dir / "path.txt").write_bytes(executable.encode("utf-8"))
        print_success(f"{label}: Electron バイナリを配置しました。")
        return electron_binary_ready(frontend_dir)
    except (OSError, KeyError, ValueError, RuntimeError, subprocess.SubprocessError, zipfile.BadZipFile) as exc:
        print_error(f"{label}: Electron バイナリの取得・配置に失敗しました: {exc}")
        return False


def prepare_electron_binary(frontend_dir: Path, label: str) -> bool:
    """npm の postinstall の有無に依存せず、セットアップ中に取得を完了する。"""
    if electron_binary_ready(frontend_dir):
        print_info(f"{label}: Electron バイナリを確認しました。")
        return True
    node = shutil.which("node.exe" if sys.platform == "win32" else "node")
    installer = frontend_dir / "node_modules" / "electron" / "install.js"
    if node and installer.is_file():
        print_info(f"{label}: Electron のインストーラーを実行します。")
        if run_command([node, str(installer)], cwd=frontend_dir) and electron_binary_ready(frontend_dir):
            return True
    print_warning(f"{label}: Electron バイナリを GitHub から手動取得します。")
    return install_electron_binary(frontend_dir, label)


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


def install_standalone_launcher() -> bool:
    """作業フォルダから aidiy_vscode で単独画面を開けるようにする。"""
    launcher_dir = Path.home() / ".local" / "bin"
    launcher_path = launcher_dir / ("aidiy_vscode.cmd" if sys.platform == "win32" else "aidiy_vscode")
    script_path = FRONTEND_VSCODE_DIR / "scripts" / "launch-standalone.mjs"
    if not script_path.is_file():
        print_error(f"単独起動スクリプトが見つかりません: {script_path}")
        return False
    if sys.platform == "win32":
        content = (
            "@echo off\n"
            "setlocal\n"
            f'node.exe "{script_path}" %*\n'
            "exit /b %ERRORLEVEL%\n"
        )
    else:
        content = f'#!/usr/bin/env sh\nexec node {shlex.quote(str(script_path))} "$@"\n'
    try:
        launcher_dir.mkdir(parents=True, exist_ok=True)
        launcher_path.write_text(content, encoding="utf-8")
        if sys.platform != "win32":
            launcher_path.chmod(0o755)
    except OSError as exc:
        print_error(f"単独起動ランチャーを作成できません: {launcher_path} ({exc})")
        return False
    print_success(f"単独起動ランチャーを作成しました: {launcher_path}")
    if str(launcher_dir).lower() not in (entry.lower() for entry in os.environ.get("PATH", "").split(os.pathsep)):
        print_warning(f"{launcher_dir} を PATH に追加し、新しいターミナルから aidiy_vscode を実行してください。")
    return True


def setup(choices: dict | None = None) -> bool:
    del choices
    label = "フロントエンド(VS Code)"
    print_header(f"{label} セットアップ")
    print_info(f"作業ディレクトリ: {FRONTEND_VSCODE_DIR}")
    print_info("対象: VS Code チャット拡張 / Electron / 単独起動ランチャー / TypeScript / VSIX")

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

    recovery_needed = False
    for action in ("install", "update"):
        if not run_command([npm_path, action], cwd=FRONTEND_VSCODE_DIR):
            print_warning(f"{label}: npm {action} が失敗しました。postinstall をスキップして再試行します。")
            recovery_needed = True
            if not run_command([npm_path, action, "--ignore-scripts"], cwd=FRONTEND_VSCODE_DIR):
                print_error(f"{label}: 依存関係の導入・更新に失敗しました。")
                return False

    if not prepare_electron_binary(FRONTEND_VSCODE_DIR, label):
        return False
    if recovery_needed:
        # --ignore-scripts で導入した esbuild などの postinstall も完了させる。
        if not run_command([npm_path, "rebuild"], cwd=FRONTEND_VSCODE_DIR):
            return False
        if not electron_binary_ready(FRONTEND_VSCODE_DIR):
            print_error(f"{label}: Electron バイナリを確認できません。")
            return False
    if vscode_cli is None:
        print_warning("VS Code CLI が見つからないため、単独画面だけをセットアップします。")
        if not run_command([npm_path, "run", "compile"], cwd=FRONTEND_VSCODE_DIR):
            print_error(f"{label}: 単独画面の生成に失敗しました。")
            return False
    else:
        metadata = get_extension_metadata()
        if metadata is None:
            return False
        extension_id, version, vsix_path = metadata
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

    if not install_standalone_launcher():
        return False

    if vscode_cli is not None:
        print_success(f"{label}: {extension_id} を VS Code 拡張機能として配置しました。")
        print_info("  VS Code 本体や AiDiy の常駐サービスは停止していません。")
        print_info("  VS Code に反映されない場合は、ウィンドウを再読み込みしてください。")
    print_success(f"{label}: aidiy_vscode で単独画面を起動できます。")
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
