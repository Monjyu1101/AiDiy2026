# -*- coding: utf-8 -*-

"""プロジェクト セットアップスクリプト

このスクリプトは、プロジェクト全体の初期セットアップを対話的に実行します。

対象:
- 共通
- バックエンド(core,apps): `backend_server`
- フロントエンド(Web): `frontend_web`
- フロントエンド(Avatar): `frontend_avatar`

Usage:
    python _setup.py
"""

import json
import os
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
# プロジェクト設定
# ============================================================
BACKEND_PATH = "backend_server"
BACKEND_ENV = ".venv"

FRONTEND_WEB_PATH = "frontend_web"
FRONTEND_AVATAR_PATH = "frontend_avatar"
BACKEND_MCP_PATH = "backend_mcp"

FRONTEND_COMMAND = "npm"
DATABASE_TYPE = "sqlite"
POSTGRES_PATH = "backend_server/postgres"

AUTO_MODE = False
GLOBAL_NPM_INSTALL_PROCESSES = []

BASE_DIR = Path(__file__).parent
BACKEND_DIR = BASE_DIR / BACKEND_PATH
BACKEND_VENV_DIR = BACKEND_DIR / BACKEND_ENV
FRONTEND_WEB_DIR = BASE_DIR / FRONTEND_WEB_PATH
FRONTEND_AVATAR_DIR = BASE_DIR / FRONTEND_AVATAR_PATH
BACKEND_MCP_DIR = BASE_DIR / BACKEND_MCP_PATH
POSTGRES_DIR = BASE_DIR / POSTGRES_PATH
BACKEND_MCP_ENV_CANDIDATES = [".venv", "venv"]


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


def run_command(command, cwd=None, shell=False, env=None):
    try:
        if isinstance(command, list):
            cmd_str = " ".join(str(c) for c in command)
        else:
            cmd_str = command

        print_info(f"実行中: {cmd_str}")
        subprocess.run(
            command,
            cwd=cwd,
            shell=shell,
            check=True,
            capture_output=False,
            text=True,
            env=env,
        )
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"コマンド実行エラー: {e}")
        return False
    except Exception as e:
        print_error(f"予期しないエラー: {e}")
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


def ensure_gitignore_entries(entries: list[str], path: Path | None = None) -> bool:
    target_path = path or (BASE_DIR / ".gitignore")
    try:
        existing_lines: list[str] = []
        if target_path.exists():
            existing_lines = target_path.read_text(encoding="utf-8").splitlines()

        normalized = {line.strip() for line in existing_lines}
        missing_entries = [entry for entry in entries if entry.strip() not in normalized]
        if not missing_entries:
            return True

        updated_lines = list(existing_lines)
        if updated_lines and updated_lines[-1].strip() != "":
            updated_lines.append("")
        updated_lines.append("# Local AI CLI settings")
        updated_lines.extend(missing_entries)
        target_path.write_text("\n".join(updated_lines).rstrip() + "\n", encoding="utf-8")
        print_success(f"ignore 設定を更新しました: {target_path}")
        return True
    except Exception as e:
        print_error(f"ignore 設定更新エラー: {target_path} ({e})")
        return False


def upsert_json_mcp_servers(path: Path, entries: list[tuple[str, dict]], top_key: str = "mcpServers") -> bool:
    """複数サーバーをまとめて 1 つの JSON ファイルへ書き込む（読み書き各 1 回）。"""
    try:
        data = {}
        if path.exists():
            with open(path, encoding="utf-8-sig") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                data = loaded

        servers = data.get(top_key)
        if not isinstance(servers, dict):
            servers = {}

        for server_name, server_config in entries:
            current = servers.get(server_name)
            if isinstance(current, dict):
                merged = dict(current)
                merged.update(server_config)
                servers[server_name] = merged
            else:
                servers[server_name] = dict(server_config)

        data[top_key] = servers
        if not write_json_file(path, data):
            return False
        names = ", ".join(sn for sn, _ in entries)
        print_success(f"MCP設定を書き込みました: {path} ({names})")
        return True
    except json.JSONDecodeError as e:
        print_error(f"JSON解析エラー: {path} ({e})")
        return False
    except Exception as e:
        print_error(f"MCP設定更新エラー: {path} ({e})")
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


def toml_escape_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def upsert_toml_table(path: Path, table_header: str, body_lines: list[str]) -> bool:
    try:
        content = path.read_text(encoding="utf-8") if path.exists() else ""
        updated = remove_toml_table(content, table_header).rstrip()
        block = table_header + "\n" + "\n".join(body_lines).rstrip() + "\n"
        if updated:
            updated = updated + "\n\n" + block
        else:
            updated = block
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(updated, encoding="utf-8")
        return True
    except Exception as e:
        print_error(f"TOML設定更新エラー: {path} ({e})")
        return False


def find_python_in_env(base_dir: Path, env_candidates: list[str]) -> Path | None:
    for env_name in env_candidates:
        if sys.platform == "win32":
            python_path = base_dir / env_name / "Scripts" / "python.exe"
        else:
            python_path = base_dir / env_name / "bin" / "python"
        if python_path.exists():
            return python_path
    return None


def upsert_codex_backend_mcp_config(module: dict) -> bool:
    config_path = Path.home() / ".codex" / "config.toml"
    server_name = module.get("server_name", module["name"])
    sse_url = module.get("sse_url", "").strip()
    table_header = f"[mcp_servers.{server_name}]"
    python_path = find_python_in_env(BACKEND_MCP_DIR, BACKEND_MCP_ENV_CANDIDATES)
    if python_path is None:
        print_error(f"Codex 設定用の Python 仮想環境が見つかりません: {BACKEND_MCP_DIR}")
        return False

    script_path = BACKEND_MCP_DIR / "mcp_stdio.py"
    if not script_path.exists():
        print_error(f"Codex 設定用のスクリプトが見つかりません: {script_path}")
        return False

    body_lines = [
        f'command = "{toml_escape_string(str(python_path))}"',
        "args = [",
        f'    "{toml_escape_string(str(script_path))}",',
        '    "--sse-url",',
        f'    "{toml_escape_string(sse_url)}",',
        "]",
        "startup_timeout_ms = 20000",
    ]

    if not upsert_toml_table(config_path, table_header, body_lines):
        return False

    print_success(f"Codex の {server_name} 設定を書き込みました: {config_path}")
    return True


def npm_command():
    return f"{FRONTEND_COMMAND}.cmd" if sys.platform == "win32" else FRONTEND_COMMAND


def get_electron_version(frontend_dir: Path) -> str:
    """node_modules/electron/package.json からバージョンを取得する。
    見つからない場合は package.json の devDependencies から推測する。"""
    # 1st: インストール済みの node_modules から正確なバージョンを取得
    pkg = frontend_dir / "node_modules" / "electron" / "package.json"
    if pkg.exists():
        with open(pkg, encoding="utf-8") as f:
            data = json.load(f)
        version = data.get("version", "")
        if version:
            return version

    # 2nd: package.json の devDependencies から取得 (^37.7.1 → 37.7.1 など)
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
    last_reported = [-1]

    def progress_hook(block_num, block_size, total_size):
        if total_size > 0:
            downloaded = min(block_num * block_size, total_size)
            percent = int(downloaded * 100 / total_size)
            # 次に報告すべきマイルストーンを探す
            for ms in MILESTONES:
                if ms > last_reported[0] and percent >= ms:
                    mb_done = downloaded // 1024 // 1024
                    mb_total = total_size // 1024 // 1024
                    print_info(f"  ダウンロード中... {ms}% ({mb_done}MB / {mb_total}MB)")
                    last_reported[0] = ms

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
        # (Python の zipfile モジュールはシンボリックリンクをテキストファイルとして展開するため)
        if sys.platform != "win32" and shutil.which("unzip"):
            result = subprocess.run(
                ["unzip", "-q", "-o", str(final_file), "-d", str(dist_dir)],
                capture_output=True,
                text=True,
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


def check_uv_installed():
    return shutil.which("uv") is not None


def check_npm_installed():
    return shutil.which(npm_command()) is not None or shutil.which(FRONTEND_COMMAND) is not None


def print_ai_cli_manual_setup():
    cmd = npm_command()
    print_info("共通: AI CLI ツールは個別にセットアップできます。")
    print_info("  個別セットアップ例:")
    print_info(f"    Claude Code : {cmd} install -g @anthropic-ai/claude-code")
    print_info(f"    GitHub Copilot: {cmd} install -g @github/copilot")
    print_info(f"    OpenAI Codex : {cmd} install -g @openai/codex")
    print_info(f"    Gemini CLI : {cmd} install -g @google/gemini-cli")


def start_global_npm_tools_install():
    print_header("共通セットアップ: npm ツール投入")
    print_info("対象: Anthropic / GitHub Copilot / OpenAI Codex / Gemini CLI")
    print_info("AI CLI ツールを並列で投入します。完了確認は最後にまとめて行います。")

    if not check_npm_installed():
        print_error("共通: npm がインストールされていません。")
        print_info("  Node.js をインストールしてください: https://nodejs.org/")
        return False

    cmd = npm_command()
    packages = [
        "@anthropic-ai/claude-code",
        "@github/copilot",
        "@openai/codex",
        "@google/gemini-cli",
    ]

    GLOBAL_NPM_INSTALL_PROCESSES.clear()
    for i, package in enumerate(packages, 1):
        command = [cmd, "install", "-g", package]
        print_info(f"  [{i}/{len(packages)}] 投入: {' '.join(command)}")
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
            )
            GLOBAL_NPM_INSTALL_PROCESSES.append((package, process))
            print_success(f"  [{i}/{len(packages)}] {package}: 投入完了")
        except Exception as exc:
            print_error(f"  [{i}/{len(packages)}] {package}: 投入失敗 - {exc}")

    if not GLOBAL_NPM_INSTALL_PROCESSES:
        print_warning("共通: AI CLI ツールの投入対象がありませんでした。")
        return False

    print_success("共通: AI CLI ツールの投入を開始しました。")
    return True


def wait_global_npm_tools_install() -> list[str]:
    if not GLOBAL_NPM_INSTALL_PROCESSES:
        return []

    print_header("共通セットアップ: npm ツール完了確認")
    print_info("並列投入した AI CLI ツールの導入結果を確認します...")

    failed_packages = []
    for i, (package, process) in enumerate(GLOBAL_NPM_INSTALL_PROCESSES, 1):
        try:
            stdout, stderr = process.communicate(timeout=300)
            if process.returncode == 0:
                print_success(f"  [{i}/{len(GLOBAL_NPM_INSTALL_PROCESSES)}] {package}: 導入完了")
            else:
                print_error(f"  [{i}/{len(GLOBAL_NPM_INSTALL_PROCESSES)}] {package}: 導入失敗 (終了コード: {process.returncode})")
                detail = (stderr or stdout or "").strip()
                if detail:
                    print_error(f"      エラー内容: {detail[:200]}")
                failed_packages.append(package)
        except subprocess.TimeoutExpired:
            process.kill()
            print_error(f"  [{i}/{len(GLOBAL_NPM_INSTALL_PROCESSES)}] {package}: タイムアウト")
            failed_packages.append(package)
        except Exception as exc:
            print_error(f"  [{i}/{len(GLOBAL_NPM_INSTALL_PROCESSES)}] {package}: エラー - {exc}")
            failed_packages.append(package)

    GLOBAL_NPM_INSTALL_PROCESSES.clear()

    if failed_packages:
        print_warning(f"共通: 一部 npm ツールの導入に失敗しました: {', '.join(failed_packages)}")
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
            error_locations.extend(
                [f"共通: Python ツール更新 ({tool_name})" for tool_name in failed_tools]
            )
        else:
            print_success("共通: Python ツールのアップグレードが完了しました。")
    else:
        print_warning("共通: Python ツールのアップグレードをスキップしました。")

    if choices.get("common_npm_install"):
        start_global_npm_tools_install()
    else:
        print_warning("共通: npm ツールのインストールをスキップしました。")
        print_ai_cli_manual_setup()

    return error_locations


def setup_backend(choices: dict):
    label = "バックエンド(core,apps)"
    print_header(f"{label} セットアップ")
    print_info(f"作業ディレクトリ: {BACKEND_DIR}")
    print_info("対象: FastAPI / SQLite / core_main / apps_main")

    if not BACKEND_DIR.exists():
        print_error(f"{label}: フォルダが見つかりません: {BACKEND_DIR}")
        return False

    pyproject_file = BACKEND_DIR / "pyproject.toml"
    if not pyproject_file.exists():
        print_error(f"{label}: pyproject.toml が見つかりません: {pyproject_file}")
        return False

    if not check_uv_installed():
        print_error(f"{label}: uv がインストールされていません。")
        print_info("  PowerShell: irm https://astral.sh/uv/install.ps1 | iex")
        print_info("  または: pip install uv")
        return False

    if BACKEND_VENV_DIR.exists():
        print_success(f"{label}: 既存の仮想環境を検出しました: {BACKEND_VENV_DIR}")

    if run_command(["uv", "sync"], cwd=BACKEND_DIR):
        print_success(f"{label}: セットアップが完了しました。")
    else:
        print_error(f"{label}: セットアップに失敗しました。")
        return False

    if DATABASE_TYPE.lower() == "postgresql":
        print_header(f"{label} PostgreSQL 補助処理")

        print_info("PostgreSQL を使う場合は以下のユーザーが必要です。")
        print_info("  ユーザー名: appsuser")
        print_info("  パスワード: appspass")
        print_info("  DB名: appsdb")

        if not choices.get("pg_user_created"):
            print_error("PostgreSQL ユーザーが未作成のため処理を終了します。")
            return False

        if choices.get("pg_restore"):
            create_db_script = POSTGRES_DIR / "create_database.py"
            if create_db_script.exists():
                if not run_command(["uv", "run", "python", str(create_db_script.name)], cwd=POSTGRES_DIR):
                    return False
            else:
                print_warning(f"初期データベース復元をスキップします: {create_db_script} が見つかりません。")

        if choices.get("pg_migrate"):
            if not run_command(["uv", "run", "alembic", "upgrade", "head"], cwd=BACKEND_DIR):
                return False
    else:
        print_info(f"{label}: DATABASE_TYPE={DATABASE_TYPE} のため PostgreSQL 関連処理はスキップします。")

    return True


def setup_frontend_web():
    label = "フロントエンド(Web)"
    print_header(f"{label} セットアップ")
    print_info(f"作業ディレクトリ: {FRONTEND_WEB_DIR}")
    print_info("対象: Vue 3 / Vite / TypeScript")

    if not FRONTEND_WEB_DIR.exists():
        print_error(f"{label}: フォルダが見つかりません: {FRONTEND_WEB_DIR}")
        return False

    if not check_npm_installed():
        print_error(f"{label}: npm がインストールされていません。")
        print_info("  Node.js をインストールしてください: https://nodejs.org/")
        return False

    package_json = FRONTEND_WEB_DIR / "package.json"
    if not package_json.exists():
        print_error(f"{label}: package.json が見つかりません: {package_json}")
        return False

    if run_command([npm_command(), "install"], cwd=FRONTEND_WEB_DIR):
        print_success(f"{label}: セットアップが完了しました。")
        return True

    print_error(f"{label}: セットアップに失敗しました。")
    return False


def setup_frontend_avatar():
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

    # テスト用: electron.exe を削除してフォールバックを検証
    # if electron_exe.exists():
    #     electron_exe.unlink()
    #     print_warning(f"{label}: [テスト用] {electron_exe} を削除しました。")

    # electron リカバリ処理
    if not electron_exe.exists():
        # a. --ignore-scripts で一度インストールして postinstall をスキップし、バイナリだけを手動で配置する
        if not run_command([npm_command(), "install", "--ignore-scripts"], cwd=FRONTEND_AVATAR_DIR):
            #return False
            pass
        # b. GitHub からバイナリ取得
        if not install_electron_binary(FRONTEND_AVATAR_DIR, label):
            return False
        # c. npm install を再実行して仕上げ
        #    Electron バイナリは配置済みのため、ここで失敗しても続行する
        print_info(f"{label}: npm install を再実行してセットアップを完了させます...")
        #if not run_command([npm_command(), "install"], cwd=FRONTEND_AVATAR_DIR):
        #    print_warning(f"{label}: npm install (再実行) に失敗しましたが続行します。")
        if not run_command([npm_command(), "install"], cwd=FRONTEND_AVATAR_DIR):
            return False
        # d. electron install 成功
        print_info(f"{label}: electron がインストール出来ました。")

    print_success(f"{label}: セットアップが完了しました。")
    return True


# ============================================================
# (mcp) モジュール定義
# 新しい (mcp) を追加するときはここにエントリを追加するだけ
# ============================================================
MCP_MODULES = [
    {
        "name":        "backend_mcp",
        "server_name": "aidiy_chrome_devtools",   # MCP 設定ファイル上のサーバーキー名
        "dir":         "backend_mcp",
        "desc":        "Python (uv) — Chrome DevTools Protocol + Desktop Capture",
        "start":       "uv run uvicorn mcp_main:app --host 0.0.0.0 --port 8095",
        "sse_url":     "http://localhost:8095/aidiy_chrome_devtools/sse",
        # 同一プロセスで追加公開するサーバー（uv sync は不要、設定書き込みのみ）
        "extra_servers": [
            {
                "server_name": "aidiy_desktop_capture",
                "sse_url":     "http://localhost:8095/aidiy_desktop_capture/sse",
            },
            {
                "server_name": "aidiy_sqlite",
                "sse_url":     "http://localhost:8095/aidiy_sqlite/sse",
            },
            {
                "server_name": "aidiy_postgres",
                "sse_url":     "http://localhost:8095/aidiy_postgres/sse",
            },
            {
                "server_name": "aidiy_logs",
                "sse_url":     "http://localhost:8095/aidiy_logs/sse",
            },
            {
                "server_name": "aidiy_code_check",
                "sse_url":     "http://localhost:8095/aidiy_code_check/sse",
            },
            {
                "server_name": "aidiy_backup_check",
                "sse_url":     "http://localhost:8095/aidiy_backup_check/sse",
            },
            {
                "server_name": "aidiy_backup_save",
                "sse_url":     "http://localhost:8095/aidiy_backup_save/sse",
            },
        ],
    },
]


def setup_mcp_module(module: dict) -> bool:
    """(mcp) モジュールを汎用的にセットアップする (uv sync + npm install)"""
    name  = module["name"]
    label = f"(mcp) {name}"
    mcp_dir = BASE_DIR / module["dir"]

    print_header(f"{label} セットアップ")
    print_info(f"作業ディレクトリ: {mcp_dir}")
    print_info(f"対象: {module.get('desc', '')}")

    if not mcp_dir.exists():
        print_error(f"{label}: フォルダが見つかりません: {mcp_dir}")
        return False

    # uv sync (pyproject.toml があれば)
    if (mcp_dir / "pyproject.toml").exists():
        if not check_uv_installed():
            print_error(f"{label}: uv がインストールされていません。")
            return False
        if not run_command(["uv", "sync", "--no-install-project"], cwd=mcp_dir):
            print_error(f"{label}: uv sync に失敗しました。")
            return False
        print_success(f"{label}: Python 依存関係のインストールが完了しました。")

    # npm install (package.json があれば)
    if (mcp_dir / "package.json").exists():
        if not check_npm_installed():
            print_error(f"{label}: npm がインストールされていません。")
            return False
        if not run_command([npm_command(), "install"], cwd=mcp_dir):
            print_error(f"{label}: npm install に失敗しました。")
            return False
        print_success(f"{label}: npm パッケージのインストールが完了しました。")

    print_success(f"{label}: セットアップが完了しました。")
    print_info(f"  起動方法: cd {module['dir']} && {module.get('start', 'uv run mcp_main.py')}")
    if "sse_url" in module:
        print_info(f"  SSE URL : {module['sse_url']}")
    return True


def setup_backend_mcp() -> bool:
    """登録済みの (mcp) モジュールを順番にセットアップする"""
    all_ok = True
    for module in MCP_MODULES:
        if not setup_mcp_module(module):
            all_ok = False
            break
    return all_ok


def show_current_mcp_config(module: dict) -> None:
    """MCP 設定ファイルの現在の内容を表示する"""
    # 対象サーバー名リスト（メイン + extra_servers）
    server_names = [module.get("server_name", module["name"])]
    for extra in module.get("extra_servers", []):
        server_names.append(extra["server_name"])

    copilot_home = Path(os.environ.get("COPILOT_HOME", str(Path.home() / ".copilot")))
    vscode_mcp   = get_vscode_mcp_path()

    targets = [
        ("グローバル ~/.claude.json (Claude Code)",               Path.home() / ".claude.json",            "mcpServers"),
        ("グローバル ~/.gemini/settings.json (Gemini CLI)",        Path.home() / ".gemini" / "settings.json", "mcpServers"),
        ("グローバル ~/.copilot/mcp-config.json (Copilot CLI)",    copilot_home / "mcp-config.json",        "mcpServers"),
        ("グローバル ~/.codex/config.toml (Codex CLI)",            Path.home() / ".codex" / "config.toml",  "mcpServers"),
        ("グローバル Code/User/mcp.json (VS Code)",                vscode_mcp,                              "servers"),
    ]

    print_info("─── MCP 設定ファイルの現在の状態 ───")
    for label, path, top_key in targets:
        if path.exists():
            try:
                if path.suffix.lower() == ".toml":
                    content = path.read_text(encoding="utf-8")
                    for sn in server_names:
                        table_header = f"[mcp_servers.{sn}]"
                        if table_header in content:
                            print_success(f"  [{label}] {sn}: stdio bridge configured")
                        else:
                            print_warning(f"  [{label}] ファイルあり、{sn} エントリなし")
                else:
                    data = json.loads(path.read_text(encoding="utf-8-sig"))
                    servers = data.get(top_key, {})
                    for sn in server_names:
                        if sn in servers:
                            url = servers[sn].get("url", "(url なし)")
                            print_success(f"  [{label}] {sn}: {url}")
                        else:
                            keys = list(servers.keys()) if servers else []
                            if keys:
                                print_warning(f"  [{label}] ファイルあり、{sn} エントリなし (キー: {', '.join(keys)})")
                            else:
                                print_warning(f"  [{label}] ファイルあり、{top_key} なし")
            except Exception:
                print_warning(f"  [{label}] 読み取りエラー: {path}")
        else:
            print_info(f"  [{label}] 未設定 (ファイルなし)")
    print()


def configure_backend_mcp_clients(module: dict) -> bool:
    """backend_mcp を各 CLI から使うための設定ファイルを書き込む（extra_servers も含む）。

    設定先ごとに全サーバーをまとめて 1 回だけ書き込む方式。
    """
    label = f"{module['name']} MCP 設定"
    print_header(label)
    print_info("Claude / Gemini / GitHub Copilot / Codex / VS Code 用のグローバル設定ファイルを書き込みます。")
    print_info("Codex CLI は stdio の mcp_stdio.py を起動し、その先で backend_mcp の SSE へ接続します。")

    # 書き込み対象サーバーリスト: メイン + extra_servers
    servers: list[tuple[str, str]] = []
    main_sn  = module.get("server_name", module["name"])
    main_url = module.get("sse_url", "").strip()
    if main_url:
        servers.append((main_sn, main_url))
    else:
        print_error(f"  {main_sn}: sse_url が未定義です。スキップします。")
    for extra in module.get("extra_servers", []):
        url = extra.get("sse_url", "").strip()
        if url:
            servers.append((extra["server_name"], url))
        else:
            print_error(f"  {extra['server_name']}: sse_url が未定義です。スキップします。")

    if not servers:
        print_warning(f"{label}: 書き込み対象サーバーが 1 つもありません。")
        return False

    print_info("書き込むサーバー:")
    for sn, url in servers:
        print_info(f"  ─ {sn} ({url})")

    all_ok = True

    # 1) AiDiy プロジェクト設定 (mcpServers)
    aidiy_mcp = BACKEND_DIR / "_config" / "AiDiy_mcp.json"
    print_info(f"[AiDiy設定]   {aidiy_mcp}")
    all_ok &= upsert_json_mcp_servers(
        aidiy_mcp,
        [(sn, {"type": "sse", "url": url}) for sn, url in servers],
    )

    # 2) Claude Code (mcpServers)
    claude_global = Path.home() / ".claude.json"
    print_info(f"[Claude Code] {claude_global}")
    all_ok &= upsert_json_mcp_servers(
        claude_global,
        [(sn, {"type": "sse", "url": url}) for sn, url in servers],
    )

    # 3) Gemini CLI (mcpServers)
    gemini_global = Path.home() / ".gemini" / "settings.json"
    print_info(f"[Gemini CLI]  {gemini_global}")
    all_ok &= upsert_json_mcp_servers(
        gemini_global,
        [(sn, {"url": url, "type": "sse"}) for sn, url in servers],
    )

    # 4) GitHub Copilot CLI (mcpServers)
    copilot_home = Path(os.environ.get("COPILOT_HOME", str(Path.home() / ".copilot")))
    copilot_global = copilot_home / "mcp-config.json"
    print_info(f"[Copilot CLI] {copilot_global}")
    all_ok &= upsert_json_mcp_servers(
        copilot_global,
        [(sn, {"type": "sse", "url": url}) for sn, url in servers],
    )

    # 5) Codex CLI (TOML, stdio ブリッジ)
    codex_path = Path.home() / ".codex" / "config.toml"
    print_info(f"[Codex CLI]   {codex_path}")
    for sn, url in servers:
        codex_module = {**module, "server_name": sn, "sse_url": url}
        all_ok &= upsert_codex_backend_mcp_config(codex_module)

    # 6) VS Code (servers)
    vscode_mcp = get_vscode_mcp_path()
    print_info(f"[VS Code]     {vscode_mcp}")
    all_ok &= upsert_json_mcp_servers(
        vscode_mcp,
        [(sn, {"type": "sse", "url": url}) for sn, url in servers],
        top_key="servers",
    )

    if all_ok:
        print_success(f"{label}: 設定ファイルの書き込みが完了しました。")
    else:
        print_warning(f"{label}: 一部設定ファイルの書き込みに失敗しました。")
    return all_ok


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
        "mcp":                   False,
        "mcp_config":            False,
        "backend":               False,
        "pg_user_created":       False,
        "pg_restore":            False,
        "pg_migrate":            False,
        "web":                   False,
        "avatar":                False,
        "continue_on_error":     False,
    }

    choices["common"] = ask_yes_no("共通セットアップを実行しますか？", default="y")
    if choices["common"]:
        choices["common_python_upgrade"] = ask_yes_no("共通: グローバル環境 Python ツールをアップグレードしますか？", default="y")
        choices["common_npm_install"]    = ask_yes_no("共通: グローバル環境の npm ツール(AI CLI)をインストール/アップデートしますか？", default="y")

    choices["mcp"] = ask_yes_no("バックエンド(mcp) のセットアップを実行しますか？", default="y")
    if choices["mcp"]:
        choices["mcp_config"] = ask_yes_no("バックエンド(mcp): backend_mcp の mcp機能を使えるよう構成しますか？", default="y")

    choices["backend"] = ask_yes_no("バックエンド(core,apps)のセットアップを実行しますか？", default="y")
    if choices["backend"] and DATABASE_TYPE.lower() == "postgresql":
        choices["pg_user_created"] = ask_yes_no("バックエンド: PostgreSQL ユーザー(appsuser)を作成しましたか？", default="y")
        choices["pg_restore"]      = ask_yes_no("バックエンド: 初期データベースを復元しますか？", default="n")
        choices["pg_migrate"]      = ask_yes_no("バックエンド: マイグレーション(alembic upgrade head)を実行しますか？", default="y")

    choices["web"] = ask_yes_no("フロントエンド(Web)のセットアップを実行しますか？", default="y")
    choices["avatar"] = ask_yes_no("フロントエンド(Avatar)のセットアップを実行しますか？", default="y")

    choices["continue_on_error"] = ask_yes_no("エラーが発生しても続行しますか？", default="y")

    return choices


def main():
    print_header("プロジェクト セットアップ")
    print(f"{Colors.BOLD}このスクリプトは、プロジェクト全体の初期セットアップを実行します。{Colors.ENDC}")
    print_info("セットアップ対象:")
    print_info("  1. 共通")
    print_info("  2. バックエンド(mcp)")
    print_info("  3. バックエンド(core,apps)")
    print_info("  4. フロントエンド(Web)")
    print_info("  5. フロントエンド(Avatar)")
    print()

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
        if GLOBAL_NPM_INSTALL_PROCESSES:
            print()
            failed_packages = wait_global_npm_tools_install()
            error_locations.extend(
                [f"共通: npm ツール導入 ({package})" for package in failed_packages]
            )
    else:
        print_warning("共通セットアップをスキップしました。")

    print()
    if choices["mcp"]:
        if not setup_backend_mcp():
            error_locations.append("バックエンド(mcp)")
            if not continue_on_error:
                print_setup_summary(error_locations)
                sys.exit(1)
        backend_mcp_module = next((module for module in MCP_MODULES if module.get("name") == "backend_mcp"), None)
        if backend_mcp_module:
            print()
            show_current_mcp_config(backend_mcp_module)
            if choices["mcp_config"]:
                if not configure_backend_mcp_clients(backend_mcp_module):
                    error_locations.append("バックエンド(mcp): MCP 設定ファイル書き込み")
                    if not continue_on_error:
                        print_setup_summary(error_locations)
                        sys.exit(1)
            else:
                print_warning("backend_mcp の MCP 設定ファイル書き込みをスキップしました。")
        else:
            print_warning("backend_mcp モジュール定義が見つからないため、MCP 設定をスキップしました。")
    else:
        print_warning("バックエンド(mcp) のセットアップをスキップしました。")

    print()
    if choices["backend"]:
        if not setup_backend(choices):
            error_locations.append("バックエンド(core,apps)")
            if not continue_on_error:
                print_setup_summary(error_locations)
                sys.exit(1)
    else:
        print_warning("バックエンド(core,apps)のセットアップをスキップしました。")

    print()
    if choices["web"]:
        if not setup_frontend_web():
            error_locations.append("フロントエンド(Web)")
            if not continue_on_error:
                print_setup_summary(error_locations)
                sys.exit(1)
    else:
        print_warning("フロントエンド(Web)のセットアップをスキップしました。")

    print()
    if choices["avatar"]:
        if not setup_frontend_avatar():
            error_locations.append("フロントエンド(Avatar)")
            if not continue_on_error:
                print_setup_summary(error_locations)
                sys.exit(1)
    else:
        print_warning("フロントエンド(Avatar)のセットアップをスキップしました。")

    print_setup_summary(error_locations)
    print_info("起動方法:")
    print_info("  全体起動: python _start.py")
    print_info("  個別起動:")
    print_info("    MCP起動 : cd backend_mcp && uv run uvicorn mcp_main:app --reload --host 0.0.0.0 --port 8095")
    print_info("    Core起動: cd backend_server && uv run uvicorn core_main:app --reload --host 0.0.0.0 --port 8091")
    print_info("    Apps起動: cd backend_server && uv run uvicorn apps_main:app --reload --host 0.0.0.0 --port 8092")
    print_info("    Web開発 : cd frontend_web && npm run dev")
    print_info("    Avatar  : cd frontend_avatar && npm run dev")
    print_info("セットアップは正常終了しました。5秒後に終了します...")
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
