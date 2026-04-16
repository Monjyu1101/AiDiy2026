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


def ask_yes_no(prompt, default="n"):
    global AUTO_MODE

    if AUTO_MODE:
        print_info(f"[AUTO] {prompt} -> {'Yes' if default.lower() == 'y' else 'No'} (default)")
        return default.lower() == "y"

    prompt_text = f"\n{prompt} ([y]/n): " if default.lower() == "y" else f"\n{prompt} (y/[n]): "
    while True:
        response = input(prompt_text).strip().lower()
        if response == "":
            response = default.lower()
        if response in ["y", "yes"]:
            return True
        if response in ["n", "no"]:
            return False
        print_warning("'y' または 'n' で答えてください。")


def ask_start_mode(prompt, default="n"):
    prompt_text = f"\n{prompt} ([y]/n/a=auto): " if default.lower() == "y" else f"\n{prompt} (y/[n]/a=auto): "
    while True:
        response = input(prompt_text).strip().lower()
        if response == "":
            response = default.lower()
        if response in ["y", "yes"]:
            return True, False
        if response in ["n", "no"]:
            return False, False
        if response in ["a", "auto"]:
            return True, True
        print_warning("'y' または 'n' または 'a'(auto) で答えてください。")


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


def upsert_json_mcp_server(path: Path, server_name: str, server_config: dict) -> bool:
    try:
        data = {}
        if path.exists():
            with open(path, encoding="utf-8-sig") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                data = loaded

        servers = data.get("mcpServers")
        if not isinstance(servers, dict):
            servers = {}

        current = servers.get(server_name)
        if isinstance(current, dict):
            merged = dict(current)
            merged.update(server_config)
            servers[server_name] = merged
        else:
            servers[server_name] = dict(server_config)

        data["mcpServers"] = servers
        if not write_json_file(path, data):
            return False
        print_success(f"MCP設定を書き込みました: {path}")
        return True
    except json.JSONDecodeError as e:
        print_error(f"JSON解析エラー: {path} ({e})")
        return False
    except Exception as e:
        print_error(f"MCP設定更新エラー: {path} ({e})")
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


def wait_global_npm_tools_install():
    if not GLOBAL_NPM_INSTALL_PROCESSES:
        return True

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
        return False

    print_success("共通: AI CLI ツールの導入確認が完了しました。")
    return True


def setup_common_global_tools():
    print_header("共通セットアップ")
    print_info("対象: pip / wheel / setuptools / uv / AI CLI ツール")

    if ask_yes_no("共通: グローバル環境 Python ツールをアップグレードしますか？", default="y"):
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
        else:
            print_success("共通: Python ツールのアップグレードが完了しました。")
    else:
        print_warning("共通: Python ツールのアップグレードをスキップしました。")

    if ask_yes_no("共通: グローバル環境の npm ツール(AI CLI)をインストール/アップデートしますか？", default="y"):
        start_global_npm_tools_install()
    else:
        print_warning("共通: npm ツールのインストールをスキップしました。")
        print_ai_cli_manual_setup()


def setup_backend():
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

        if not ask_yes_no("PostgreSQL ユーザー(appsuser)を作成しましたか？", default="y"):
            print_error("PostgreSQL ユーザーが未作成のため処理を終了します。")
            return False

        if ask_yes_no("初期データベースを復元しますか？", default="n"):
            create_db_script = POSTGRES_DIR / "create_database.py"
            if create_db_script.exists():
                if not run_command(["uv", "run", "python", str(create_db_script.name)], cwd=POSTGRES_DIR):
                    return False
            else:
                print_warning(f"初期データベース復元をスキップします: {create_db_script} が見つかりません。")

        if ask_yes_no("マイグレーション(alembic upgrade head)を実行しますか？", default="y"):
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
        "desc":        "Python (uv) — Chrome DevTools Protocol + Screenshot",
        "start":       "uv run uvicorn mcp_main:app --host 0.0.0.0 --port 8095",
        "sse_url":     "http://localhost:8095/aidiy_chrome_devtools/sse",
        # 同一プロセスで追加公開するサーバー（uv sync は不要、設定書き込みのみ）
        "extra_servers": [
            {
                "server_name": "aidiy_screenshot",
                "sse_url":     "http://localhost:8095/aidiy_screenshot/sse",
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

    targets = [
        ("グローバル ~/.claude.json (Claude Code)",               Path.home() / ".claude.json"),
        ("グローバル ~/.gemini/settings.json (Gemini CLI)",        Path.home() / ".gemini" / "settings.json"),
        ("グローバル ~/.copilot/mcp-config.json (Copilot CLI)",    copilot_home / "mcp-config.json"),
        ("グローバル ~/.codex/config.toml (Codex CLI)",            Path.home() / ".codex" / "config.toml"),
    ]

    print_info("─── MCP 設定ファイルの現在の状態 ───")
    for label, path in targets:
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
                    servers = data.get("mcpServers", {})
                    for sn in server_names:
                        if sn in servers:
                            url = servers[sn].get("url", "(url なし)")
                            print_success(f"  [{label}] {sn}: {url}")
                        else:
                            keys = list(servers.keys()) if servers else []
                            if keys:
                                print_warning(f"  [{label}] ファイルあり、{sn} エントリなし (キー: {', '.join(keys)})")
                            else:
                                print_warning(f"  [{label}] ファイルあり、mcpServers なし")
            except Exception:
                print_warning(f"  [{label}] 読み取りエラー: {path}")
        else:
            print_info(f"  [{label}] 未設定 (ファイルなし)")
    print()


def _configure_one_server(server_name: str, sse_url: str, module_for_codex: dict) -> bool:
    """1サーバー分の設定を全 CLI へ書き込む内部ヘルパー"""
    all_ok = True

    aidiy_mcp = BACKEND_DIR / "_config" / "AiDiy_mcp.json"
    print_info(f"  [AiDiy設定]   {aidiy_mcp}")
    all_ok &= upsert_json_mcp_server(aidiy_mcp, server_name, {"type": "sse", "url": sse_url})

    claude_global = Path.home() / ".claude.json"
    print_info(f"  [Claude Code] {claude_global}")
    all_ok &= upsert_json_mcp_server(claude_global, server_name, {"type": "sse", "url": sse_url})

    gemini_global = Path.home() / ".gemini" / "settings.json"
    print_info(f"  [Gemini CLI]  {gemini_global}")
    all_ok &= upsert_json_mcp_server(gemini_global, server_name, {"url": sse_url, "type": "sse"})

    copilot_home = Path(os.environ.get("COPILOT_HOME", str(Path.home() / ".copilot")))
    copilot_global = copilot_home / "mcp-config.json"
    print_info(f"  [Copilot CLI] {copilot_global}")
    all_ok &= upsert_json_mcp_server(copilot_global, server_name, {"type": "sse", "url": sse_url})

    print_info(f"  [Codex CLI]   {Path.home() / '.codex' / 'config.toml'}")
    all_ok &= upsert_codex_backend_mcp_config(module_for_codex)

    return all_ok


def configure_backend_mcp_clients(module: dict) -> bool:
    """backend_mcp を各 CLI から使うための設定ファイルを書き込む（extra_servers も含む）"""
    label = f"{module['name']} MCP 設定"
    print_header(label)
    print_info("Claude / Gemini / GitHub Copilot / Codex 用のグローバル設定ファイルを書き込みます。")
    print_info("Codex CLI は stdio の mcp_stdio.py を起動し、その先で backend_mcp の SSE へ接続します。")

    # 書き込み対象リスト: メイン + extra_servers
    servers_to_write = [{
        "server_name": module.get("server_name", module["name"]),
        "sse_url":     module.get("sse_url", ""),
    }]
    for extra in module.get("extra_servers", []):
        servers_to_write.append({
            "server_name": extra["server_name"],
            "sse_url":     extra["sse_url"],
        })

    all_ok = True
    for entry in servers_to_write:
        sn  = entry["server_name"]
        url = entry["sse_url"].strip()
        if not url:
            print_error(f"  {sn}: sse_url が未定義です。スキップします。")
            all_ok = False
            continue
        print_info(f"─ {sn} ({url})")
        # Codex 設定は module の server_name / sse_url を差し替えて渡す
        codex_module = {**module, "server_name": sn, "sse_url": url}
        all_ok &= _configure_one_server(sn, url, codex_module)

    if all_ok:
        print_success(f"{label}: 設定ファイルの書き込みが完了しました。")
    else:
        print_warning(f"{label}: 一部設定ファイルの書き込みに失敗しました。")
    return all_ok


def main():
    global AUTO_MODE

    print_header("プロジェクト セットアップ")
    print(f"{Colors.BOLD}このスクリプトは、プロジェクト全体の初期セットアップを実行します。{Colors.ENDC}")
    print_info("セットアップ対象:")
    print_info("  1. 共通")
    print_info("  2. バックエンド(mcp)")
    print_info("  3. バックエンド(core,apps)")
    print_info("  4. フロントエンド(Web)")
    print_info("  5. フロントエンド(Avatar)")
    print()

    run_setup, AUTO_MODE = ask_start_mode("セットアップを実行しますか?", default="n")
    if not run_setup:
        print_warning("セットアップをキャンセルしました。")
        sys.exit(0)

    if AUTO_MODE:
        print_info("AUTOモードで実行します。以降の質問はデフォルト値で自動回答します。")

    print()
    if ask_yes_no("共通セットアップを実行しますか？", default="y"):
        setup_common_global_tools()
    else:
        print_warning("共通セットアップをスキップしました。")

    print()
    if ask_yes_no("バックエンド(mcp) のセットアップを実行しますか？", default="y"):
        if not setup_backend_mcp() and not ask_yes_no("バックエンド(mcp) で失敗しました。続行しますか？", default="n"):
            sys.exit(1)
    else:
        print_warning("バックエンド(mcp) のセットアップをスキップしました。")

    backend_mcp_module = next((module for module in MCP_MODULES if module.get("name") == "backend_mcp"), None)
    if backend_mcp_module:
        print()
        show_current_mcp_config(backend_mcp_module)
        if ask_yes_no("backend_mcp の mcp機能を使えるよう構成しますか？", default="y"):
            if not configure_backend_mcp_clients(backend_mcp_module) and not ask_yes_no("backend_mcp の MCP 設定書き込みで失敗しました。続行しますか？", default="n"):
                sys.exit(1)
        else:
            print_warning("backend_mcp の MCP 設定ファイル書き込みをスキップしました。")

    print()
    if ask_yes_no("バックエンド(core,apps)のセットアップを実行しますか？", default="y"):
        if not setup_backend() and not ask_yes_no("バックエンド(core,apps)で失敗しました。続行しますか？", default="n"):
            sys.exit(1)
    else:
        print_warning("バックエンド(core,apps)のセットアップをスキップしました。")

    print()
    if ask_yes_no("フロントエンド(Web)のセットアップを実行しますか？", default="y"):
        if not setup_frontend_web() and not ask_yes_no("フロントエンド(Web)で失敗しました。続行しますか？", default="n"):
            sys.exit(1)
    else:
        print_warning("フロントエンド(Web)のセットアップをスキップしました。")

    print()
    if ask_yes_no("フロントエンド(Avatar)のセットアップを実行しますか？", default="y"):
        if not setup_frontend_avatar() and not ask_yes_no("フロントエンド(Avatar)で失敗しました。続行しますか？", default="n"):
            sys.exit(1)
    else:
        print_warning("フロントエンド(Avatar)のセットアップをスキップしました。")

    print()
    if GLOBAL_NPM_INSTALL_PROCESSES:
        wait_global_npm_tools_install()

    print()
    print_header("セットアップ完了")
    print_success("セットアップ処理が完了しました。")
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
