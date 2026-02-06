# -*- coding: utf-8 -*-

"""プロジェクト セットアップスクリプト

このスクリプトは、プロジェクトの初期セットアップを対話的に実行します。

Usage:
    python setup.py
    
機能:
    - バックエンド環境準備 (uv sync)
    - フロントエンド環境準備 (npm install)
    - PostgreSQLユーザー確認 (DBがpostgresqlの場合)
    - 初期データベース復元 (DBがpostgresqlの場合)
    - マイグレーション実行 (DBがpostgresqlの場合)
"""

import subprocess
import sys
import time
from pathlib import Path

# ============================================================
# プロジェクト設定
# ============================================================
# バックエンド設定
BACKEND_PATH = "backend_server"      # バックエンドフォルダ名
BACKEND_ENV = ".venv"                # Python環境: ".venv" (uv使用)

# フロントエンド設定
FRONTEND_PATH = "frontend_server"    # フロントエンドフォルダパス
FRONTEND_COMMAND = "npm"             # パッケージマネージャ: "npm" or "pnpm" or "yarn"

# データベース設定
DATABASE_TYPE = "sqlite"             # "postgresql" or "sqlite"
POSTGRES_PATH = "backend_server/postgres"  # PostgreSQLスクリプト格納フォルダ

# ============================================================

# プロジェクトルート
BASE_DIR = Path(__file__).parent
SERVER_DIR = BASE_DIR / BACKEND_PATH
CLIENT_DIR = BASE_DIR / FRONTEND_PATH
POSTGRES_DIR = BASE_DIR / POSTGRES_PATH
VENV_DIR = SERVER_DIR / BACKEND_ENV


# 色付き出力用
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
    """ヘッダーメッセージを表示"""
    print(f"\n{Colors.HEADER}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{message}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'=' * 60}{Colors.ENDC}\n")


def print_success(message):
    """成功メッセージを表示"""
    print(f"{Colors.OKBLUE}[OK] {message}{Colors.ENDC}")


def print_error(message):
    """エラーメッセージを表示"""
    print(f"{Colors.FAIL}[NG] {message}{Colors.ENDC}")


def print_warning(message):
    """警告メッセージを表示"""
    print(f"{Colors.WARNING}[WARN] {message}{Colors.ENDC}")


def print_info(message):
    """情報メッセージを表示"""
    print(f"{Colors.OKGREEN}[INFO] {message}{Colors.ENDC}")


def ask_yes_no(prompt, default="n"):
    """Yes/No質問を表示して回答を取得
    
    Args:
        prompt (str): 質問文
        default (str): デフォルト値 ("y" または "n")
    
    Returns:
        bool: Yesの場合True、Noの場合False
    """
    if default.lower() == "y":
        prompt_text = f"\n{prompt} ([y]/n): "
    else:
        prompt_text = f"\n{prompt} (y/[n]): "
    
    while True:
        response = input(prompt_text).strip().lower()
        
        # 未入力の場合はデフォルト値を使用
        if response == "":
            response = default.lower()
        
        if response in ["y", "yes"]:
            return True
        elif response in ["n", "no"]:
            return False
        else:
            print_warning("'y' または 'n' で答えてください。")


def run_command(command, cwd=None, shell=False):
    """コマンドを実行
    
    Args:
        command (str or list): 実行するコマンド
        cwd (Path): 作業ディレクトリ
        shell (bool): シェル経由で実行するか
    
    Returns:
        bool: 成功時True、失敗時False
    """
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
            text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"コマンド実行エラー: {e}")
        return False
    except Exception as e:
        print_error(f"予期しないエラー: {e}")
        return False


def check_python_venv():
    """Python仮想環境が存在するか確認"""
    return VENV_DIR.exists() and (VENV_DIR / "Scripts" / "python.exe").exists()


def get_venv_python():
    """venv内のPythonパスを取得"""
    return str(VENV_DIR / "Scripts" / "python.exe")


def check_uv_installed():
    """uvがインストールされているか確認"""
    try:
        subprocess.run(
            ["uv", "--version"],
            capture_output=True,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_npm_installed():
    """npmがインストールされているか確認"""
    try:
        # Windowsでは npm.cmd を使用
        npm_cmd = f"{FRONTEND_COMMAND}.cmd" if sys.platform == "win32" else FRONTEND_COMMAND
        subprocess.run(
            [npm_cmd, "--version"],
            capture_output=True,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def setup_server_environment():
    """バックエンド環境をセットアップ"""
    print_header("バックエンド環境セットアップ")
    
    print_info(f"作業ディレクトリ: {SERVER_DIR}")
    
    # uvがインストールされているか確認
    if not check_uv_installed():
        print_error("uvがインストールされていません。")
        print_info("uvをインストールしてください:")
        print_info("  PowerShell: irm https://astral.sh/uv/install.ps1 | iex")
        print_info("  または: pip install uv")
        return False
    
    # .venvが既に存在するか確認
    if check_python_venv():
        print_success("仮想環境は既に存在します。")
        if not ask_yes_no("既存の仮想環境を使用しますか?", default="y"):
            print_info("仮想環境を再作成します...")
            if VENV_DIR.exists():
                import shutil
                shutil.rmtree(VENV_DIR)
            else:
                print_warning("仮想環境のセットアップをキャンセルしました。")
                return False
    
    # pyproject.tomlの存在確認
    pyproject_file = SERVER_DIR / "pyproject.toml"
    if not pyproject_file.exists():
        print_error(f"pyproject.tomlが見つかりません: {pyproject_file}")
        return False
    
    # uv sync を実行
    print_info("uv sync を実行中...")
    if run_command(["uv", "sync"], cwd=SERVER_DIR, shell=False):
        print_success("バックエンド環境のセットアップが完了しました。")
        return True
    else:
        print_error("バックエンド環境のセットアップに失敗しました。")
        return False


def setup_client_environment():
    """フロントエンド環境をセットアップ"""
    print_header("フロントエンド環境セットアップ")
    
    if not check_npm_installed():
        print_error(f"{FRONTEND_COMMAND}がインストールされていません。")
        print_info("Node.jsをインストールしてください: https://nodejs.org/")
        return False
    
    print_info(f"作業ディレクトリ: {CLIENT_DIR}")
    
    # package.jsonの存在確認
    package_json = CLIENT_DIR / "package.json"
    if not package_json.exists():
        print_error(f"package.jsonが見つかりません: {package_json}")
        return False
    
    # パッケージマネージャコマンドを取得
    pkg_cmd = f"{FRONTEND_COMMAND}.cmd" if sys.platform == "win32" else FRONTEND_COMMAND
    if run_command([pkg_cmd, "install"], cwd=CLIENT_DIR, shell=False):
        print_success("フロントエンド環境のセットアップが完了しました。")
        return True
    else:
        print_error("フロントエンド環境のセットアップに失敗しました。")
        return False


def check_postgres_user():
    """PostgreSQLユーザーの作成確認"""
    print_header("PostgreSQL ユーザー確認")
    
    print_info("PostgreSQLに以下のユーザーを作成する必要があります:")
    print_info("  ユーザー名: baseuser")
    print_info("  パスワード: basepass")
    print()
    print_info("作成方法:")
    print_info("  psql -U postgres")
    print_info("  CREATE USER baseuser WITH PASSWORD 'basepass';")
    print_info("  CREATE DATABASE basedb OWNER baseuser;")
    print_info("  GRANT ALL PRIVILEGES ON DATABASE basedb TO baseuser;")
    print()
    
    return ask_yes_no("PostgreSQLユーザー(baseuser)を作成しましたか?", default="y")


def restore_initial_database():
    """初期データベースを復元"""
    print_header("初期データベース復元")
    
    # postgres ディレクトリが存在しない場合はスキップ
    if not POSTGRES_DIR.exists():
        print_warning("postgresディレクトリが見つかりません。初期データ復元をスキップします。")
        return True
    
    create_db_script = POSTGRES_DIR / "create_database.py"
    initial_sql = POSTGRES_DIR / "initial_basedb.sql"
    
    # スクリプトとSQLファイルの存在確認
    if not create_db_script.exists():
        print_warning(f"データベース作成スクリプトが見つかりません: {create_db_script}")
        print_info("初期データ復元をスキップします。")
        return True
    
    if not initial_sql.exists():
        print_warning(f"初期SQLファイルが見つかりません: {initial_sql}")
        print_info("初期データ復元をスキップします。")
        return True
    
    print_info(f"スクリプト: {create_db_script}")
    print_info(f"SQLファイル: {initial_sql}")
    
    # Pythonスクリプトを実行 (uv環境で)
    python_cmd = ["uv", "run", "python", str(create_db_script.name)]
    if run_command(python_cmd, cwd=POSTGRES_DIR, shell=False):
        print_success("初期データベースの復元が完了しました。")
        return True
    else:
        print_error("初期データベースの復元に失敗しました。")
        return False


def run_migration():
    """マイグレーションを実行"""
    print_header("データベースマイグレーション")
    
    print_info("Alembicマイグレーションを実行します。")
    
    # uv run alembic upgrade head を実行
    alembic_cmd = ["uv", "run", "alembic", "upgrade", "head"]
    if run_command(alembic_cmd, cwd=SERVER_DIR, shell=False):
        print_success("マイグレーションが完了しました。")
        return True
    else:
        print_error("マイグレーションに失敗しました。")
        return False


def upgrade_global_tools():
    """グローバル環境のツールをアップグレード"""
    print_header("グローバルツールのアップグレード")
    
    print_info("グローバル環境で必要なツールをアップグレードします...")
    
    commands = [
        (["python", "-m", "pip", "install", "--upgrade", "pip"], "pip"),
        (["pip", "install", "--upgrade", "wheel"], "wheel"),
        (["pip", "install", "--upgrade", "setuptools"], "setuptools"),
        (["pip", "install", "--upgrade", "uv"], "uv"),
    ]
    
    failed_tools = []
    for cmd, tool_name in commands:
        if not run_command(cmd, cwd=None, shell=False):
            failed_tools.append(tool_name)
    
    if failed_tools:
        print_warning(f"以下のツールのアップグレードに失敗しました: {', '.join(failed_tools)}")
        return False
    else:
        print_success("すべてのグローバルツールをアップグレードしました。")
        return True


def install_global_npm_tools():
    """グローバルnpmパッケージをインストール（並行実行）"""
    print_header("グローバルnpmツールのインストール")
    
    print_info("グローバル環境でAI関連のnpmツールをインストールします...")
    print_info("各パッケージを別シェルで並行インストール中...")
    
    # npmコマンドを取得（Windows対応）
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    
    packages = [
        "@anthropic-ai/claude-code",
        "@github/copilot",
        "@openai/codex",
        "@google/gemini-cli"
    ]
    
    # 並行実行用プロセスリスト
    processes = []
    for i, package in enumerate(packages, 1):
        print_info(f"  [{i}/{len(packages)}] 起動: {npm_cmd} install -g {package}")
        cmd = [npm_cmd, "install", "-g", package]
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
            )
            processes.append((package, process))
            print_success(f"  [{i}/{len(packages)}] {package}: プロセス起動成功")
        except Exception as e:
            print_error(f"  [{i}/{len(packages)}] {package}: プロセス起動失敗 - {e}")
    
    print()
    print_info(f"起動完了: {len(processes)}/{len(packages)} パッケージ")
    print_info("インストール完了を待機中...")
    print()
    
    # 全プロセスの完了を待つ
    failed_packages = []
    for i, (package, process) in enumerate(processes, 1):
        try:
            stdout, stderr = process.communicate(timeout=300)  # 5分タイムアウト
            if process.returncode == 0:
                print_success(f"  [{i}/{len(processes)}] {package}: インストール完了")
            else:
                print_error(f"  [{i}/{len(processes)}] {package}: インストール失敗 (終了コード: {process.returncode})")
                if stderr and stderr.strip():
                    print_error(f"      エラー内容: {stderr.strip()[:200]}")
                failed_packages.append(package)
        except subprocess.TimeoutExpired:
            print_error(f"  [{i}/{len(processes)}] {package}: タイムアウト")
            process.kill()
            failed_packages.append(package)
        except Exception as e:
            print_error(f"  [{i}/{len(processes)}] {package}: エラー - {e}")
            failed_packages.append(package)
    
    if failed_packages:
        print_warning(f"以下のパッケージのインストールに失敗しました: {', '.join(failed_packages)}")
        return False
    else:
        print_success("すべてのグローバルnpmツールをインストールしました。")
        return True


def main():
    """メイン処理"""
    print_header("プロジェクト セットアップ")
    
    print(f"{Colors.BOLD}このスクリプトは、プロジェクトの初期セットアップを実行します。{Colors.ENDC}")
    print()
    
    # セットアップ実行確認
    if not ask_yes_no("セットアップを実行しますか?", default="n"):
        print_warning("セットアップをキャンセルしました。")
        sys.exit(0)
    
    # グローバルツールのアップグレード
    if ask_yes_no("グローバル環境のツール(pip, wheel, setuptools, uv)をアップグレードしますか?", default="y"):
        if not upgrade_global_tools():
            print_warning("一部のツールのアップグレードに失敗しましたが、続行します。")
    else:
        print_warning("グローバルツールのアップグレードをスキップしました。")
    
    # グローバルnpmツールのインストール
    if ask_yes_no("グローバル環境のnpmツール(AI CLIツール)をインストール/アップデートしますか?", default="y"):
        if not install_global_npm_tools():
            print_warning("一部のnpmツールのインストールに失敗しましたが、続行します。")
    else:
        print_warning("グローバルnpmツールのインストールをスキップしました。")
    
    # バックエンド環境準備
    if ask_yes_no("バックエンド環境準備(uv sync)を実行しますか?", default="y"):
        if not setup_server_environment():
            print_error("バックエンド環境のセットアップに失敗しました。")
            if not ask_yes_no("続行しますか?", default="n"):
                sys.exit(1)
    else:
        print_warning("バックエンド環境準備をスキップしました。")
    
    # フロントエンド環境準備
    if ask_yes_no("フロントエンド環境準備(npm install)を実行しますか?", default="y"):
        if not setup_client_environment():
            print_error("フロントエンド環境のセットアップに失敗しました。")
            if not ask_yes_no("続行しますか?", default="n"):
                sys.exit(1)
    else:
        print_warning("フロントエンド環境準備をスキップしました。")
    
    if DATABASE_TYPE.lower() == "postgresql":
        # PostgreSQLユーザー確認
        if not check_postgres_user():
            print_error("PostgreSQLユーザーが作成されていません。")
            print_warning("セットアップを終了します。")
            sys.exit(1)

        # 初期データベース復元
        if ask_yes_no("初期データを復元しますか?", default="n"):
            if not restore_initial_database():
                print_error("初期データベースの復元に失敗しました。")
                if not ask_yes_no("続行しますか?", default="n"):
                    sys.exit(1)
        else:
            print_warning("初期データ復元をスキップしました。")

        # マイグレーション実行
        if ask_yes_no("マイグレーション(alembic upgrade head)を実行しますか?", default="y"):
            if not run_migration():
                print_error("マイグレーションに失敗しました。")
                sys.exit(1)
        else:
            print_warning("マイグレーションをスキップしました。")
    else:
        print_warning(f"DATABASE_TYPE={DATABASE_TYPE} のため、PostgreSQL関連の処理をスキップします。")
    
    # 完了メッセージ
    print_header("セットアップ完了")
    print_success("すべてのセットアップが完了しました！")
    print()
    print_info("開発サーバーを起動するには:")
    print_info("  python _start.py")
    print()
    print_info("または VS Code で F5 キーを押してください。")
    print()
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
