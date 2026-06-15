# -*- coding: utf-8 -*-

"""フロントエンド(Avatar) セットアップスクリプト

Vue 3 / Vite / TypeScript / Electron の依存関係 (npm install) を導入します。
npm install で Electron バイナリが取得できない場合は GitHub から手動取得します。

公開 API:
    setup(choices=None) -> bool
"""

import json
import platform
import re
import shutil
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path

if sys.platform == "win32":
    import msvcrt

# ============================================================
# 設定
# ============================================================
THIS_DIR = Path(__file__).resolve().parent
FRONTEND_AVATAR_DIR = THIS_DIR
FRONTEND_COMMAND = "npm"

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


def npm_command():
    return f"{FRONTEND_COMMAND}.cmd" if sys.platform == "win32" else FRONTEND_COMMAND


def check_npm_installed():
    return shutil.which(npm_command()) is not None or shutil.which(FRONTEND_COMMAND) is not None


# ============================================================
# Electron バイナリ取得
# ============================================================
def get_electron_version(frontend_dir: Path) -> str:
    """node_modules/electron/package.json からバージョンを取得する。
    見つからない場合は package.json の devDependencies から推測する。"""
    pkg = frontend_dir / "node_modules" / "electron" / "package.json"
    if pkg.exists():
        with open(pkg, encoding="utf-8") as f:
            data = json.load(f)
        version = data.get("version", "")
        if version:
            return version

    fallback_pkg = frontend_dir / "package.json"
    if fallback_pkg.exists():
        with open(fallback_pkg, encoding="utf-8") as f:
            data2 = json.load(f)
        ver_spec = data2.get("devDependencies", {}).get("electron", "")
        if ver_spec:
            m = re.search(r"(\d+\.\d+\.\d+)", ver_spec)
            if m:
                print_info(f"  node_modules からバージョン取得できず、package.json の指定 ({ver_spec}) より {m.group(1)} を使用します。")
                return m.group(1)

    return ""


def get_electron_platform_str() -> str:
    """Electronリリース用のプラットフォーム文字列を返す (例: win32-x64)"""
    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == "windows":
        plat = "win32"
    elif system == "darwin":
        plat = "darwin"
    else:
        plat = "linux"
    arch = "arm64" if machine in ("arm64", "aarch64") else "x64"
    return f"{plat}-{arch}"


def install_electron_binary(frontend_dir: Path, label: str) -> bool:
    """GitHubからElectronバイナリをダウンロードして配置する"""
    version = get_electron_version(frontend_dir)
    if not version:
        print_error(f"{label}: Electronのバージョンが取得できませんでした。")
        return False

    plat_str = get_electron_platform_str()
    zip_name = f"electron-v{version}-{plat_str}.zip"
    url = f"https://github.com/electron/electron/releases/download/v{version}/{zip_name}"

    print_info(f"{label}: Electron v{version} ({plat_str}) をダウンロードします。")
    print_info(f"  URL: {url}")

    tmp_dir = Path(tempfile.gettempdir())
    part_file = tmp_dir / f"{zip_name}.part"
    final_file = tmp_dir / zip_name

    for stale in [part_file, final_file]:
        if stale.exists():
            stale.unlink()

    MILESTONES = [0, 30, 60, 90, 100]

    def _download_with_ctx(ctx=None):
        opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx)) if ctx else urllib.request.build_opener()
        with opener.open(url) as response:
            total_size = int(response.headers.get("Content-Length", 0))
            downloaded = 0
            block_size = 8192
            last_rep = [-1]
            with open(part_file, "wb") as f:
                while True:
                    block = response.read(block_size)
                    if not block:
                        break
                    f.write(block)
                    downloaded += len(block)
                    if total_size > 0:
                        percent = int(downloaded * 100 / total_size)
                        for ms in MILESTONES:
                            if ms > last_rep[0] and percent >= ms:
                                mb_done = downloaded // 1024 // 1024
                                mb_total = total_size // 1024 // 1024
                                print_info(f"  ダウンロード中... {ms}% ({mb_done}MB / {mb_total}MB)")
                                last_rep[0] = ms

    print_info(f"  ダウンロード先: {part_file}")
    try:
        _download_with_ctx()
    except Exception as e:
        is_ssl_error = "SSL" in str(e) or "certificate" in str(e).lower()
        if is_ssl_error:
            print_warning(f"{label}: SSL証明書エラー。証明書検証をスキップして再試行します。")
            try:
                _download_with_ctx(ssl._create_unverified_context())
            except Exception as e2:
                print_error(f"{label}: ダウンロード失敗: {e2}")
                if part_file.exists():
                    part_file.unlink()
                return False
        else:
            print_error(f"{label}: ダウンロード失敗: {e}")
            if part_file.exists():
                part_file.unlink()
            return False

    part_file.rename(final_file)
    size_mb = final_file.stat().st_size // 1024 // 1024
    print_success(f"{label}: ダウンロード完了: {final_file} ({size_mb}MB)")

    dist_dir = frontend_dir / "node_modules" / "electron" / "dist"
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir(parents=True, exist_ok=True)

    print_info(f"{label}: 展開中: {final_file} -> {dist_dir}")
    try:
        # macOS/Linux では unzip コマンドを使用してシンボリックリンクを正しく展開する
        if sys.platform != "win32" and shutil.which("unzip"):
            result = subprocess.run(
                ["unzip", "-q", "-o", str(final_file), "-d", str(dist_dir)],
                capture_output=True, text=True,
            )
            if result.returncode != 0:
                raise RuntimeError(result.stderr or result.stdout)
        else:
            with zipfile.ZipFile(final_file, "r") as zf:
                zf.extractall(dist_dir)
    except Exception as e:
        print_error(f"{label}: 展開失敗: {e}")
        return False

    if sys.platform == "win32":
        exe_name = "electron.exe"
        exe_path = dist_dir / exe_name
    elif sys.platform == "darwin":
        exe_name = "Electron.app/Contents/MacOS/Electron"
        exe_path = dist_dir / "Electron.app" / "Contents" / "MacOS" / "Electron"
    else:
        exe_name = "electron"
        exe_path = dist_dir / exe_name

    if not exe_path.exists():
        print_error(f"{label}: {exe_name} が展開先に見つかりませんでした: {dist_dir}")
        return False

    path_txt = frontend_dir / "node_modules" / "electron" / "path.txt"
    path_txt.write_bytes(exe_name.encode("utf-8"))

    print_success(f"{label}: Electronバイナリの配置が完了しました。")
    print_info(f"  実行ファイル: {exe_path}")
    return True


# ============================================================
# セットアップ本体
# ============================================================
def setup(choices: dict | None = None) -> bool:
    label = "フロントエンド(Avatar)"
    print_header(f"{label} セットアップ")
    print_info(f"作業ディレクトリ: {FRONTEND_AVATAR_DIR}")
    print_info("対象: Vue 3 / Vite / TypeScript / Electron")

    if not FRONTEND_AVATAR_DIR.exists():
        print_error(f"{label}: フォルダが見つかりません: {FRONTEND_AVATAR_DIR}")
        return False

    if not check_npm_installed():
        print_error(f"{label}: npm がインストールされていません。")
        print_info("  Node.js をインストールしてください: https://nodejs.org/")
        return False

    # 1. npm install（postinstall で Electron バイナリも取得を試みる。失敗しても続行）
    print_info(f"{label}: npm install を実行します...")
    if not run_command([npm_command(), "install"], cwd=FRONTEND_AVATAR_DIR):
        print_warning(f"{label}: npm install が失敗しました。Electron バイナリの手動取得を試みます。")

    exe_name = "electron.exe" if sys.platform == "win32" else "electron"
    electron_exe = FRONTEND_AVATAR_DIR / "node_modules" / "electron" / "dist" / exe_name

    # electron リカバリ処理
    if not electron_exe.exists():
        # a. --ignore-scripts で一度インストールして postinstall をスキップし、バイナリだけを手動で配置する
        if not run_command([npm_command(), "install", "--ignore-scripts"], cwd=FRONTEND_AVATAR_DIR):
            pass
        # b. GitHub からバイナリ取得
        if not install_electron_binary(FRONTEND_AVATAR_DIR, label):
            return False
        # c. npm install を再実行して仕上げ
        print_info(f"{label}: npm install を再実行してセットアップを完了させます...")
        if not run_command([npm_command(), "install"], cwd=FRONTEND_AVATAR_DIR):
            return False
        # d. electron install 成功
        print_info(f"{label}: electron がインストール出来ました。")

    print_success(f"{label}: セットアップが完了しました。")
    return True


def main():
    global AUTO_MODE
    print_header("フロントエンド(Avatar) セットアップ")
    run_setup, AUTO_MODE = ask_start_mode("フロントエンド(Avatar) のセットアップを実行しますか?", default="n")
    if not run_setup:
        print_warning("セットアップをキャンセルしました。")
        return
    if AUTO_MODE:
        print_info("AUTOモードで実行します。")
    if not setup():
        print_error("フロントエンド(Avatar) のセットアップに失敗しました。")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_warning("セットアップが中断されました。")
        sys.exit(130)
