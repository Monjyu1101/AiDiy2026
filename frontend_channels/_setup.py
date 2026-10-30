# -*- coding: utf-8 -*-
#
# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""Discord フロントエンドの依存導入と、共通設定の不足キー補完。"""
import importlib.util
import shutil
import os
import subprocess
import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))
# 全体処理で他フォルダの同名 launcher がキャッシュされても取り違えない。
_launcher_spec = importlib.util.spec_from_file_location('aidiy_frontend_discord_launcher', THIS_DIR / 'launcher.py')
_launcher = importlib.util.module_from_spec(_launcher_spec)
_launcher_spec.loader.exec_module(_launcher)
install_launcher = _launcher.install_launcher
sys.path.insert(0, str(THIS_DIR.parent / 'scripts'))
from _setup_electron import prepare_electron_binary, _runtime_in_use
from _runtime_requirements import check_project_node_runtime
from _setup_processes import snapshot, process_role
from _cleanup_processes import process_arguments
from discord_processes import is_discord_process


class Colors:
    HEADER = "\033[97m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
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


def print_info(message):
    print(f"{Colors.OKGREEN}[INFO] {message}{Colors.ENDC}")


def _discord_in_use() -> bool:
    """この配置先の Bot / パネルを読み取りだけで確認する。判定不能時は更新しない。"""
    if _runtime_in_use(THIS_DIR):
        return True
    windows = sys.platform == 'win32'
    # 同じ frontend_channels 配下でも、独立した Slack Bot（slack/）は Discord の稼働に数えない。
    slack_root = os.path.normcase(str(THIS_DIR / 'slack') + os.sep)
    for process in snapshot():
        if process.get('ProcessId') == os.getpid():
            continue  # この _setup.py 自身は Discord の稼働ではない。
        if slack_root in os.path.normcase(process.get('CommandLine') or ''):
            continue
        if (process_role(process, THIS_DIR.parent, windows) == 'frontend_channels'
                or is_discord_process(process, THIS_DIR, windows)):
            return True
        name = (process.get('Name') or '').lower()
        if name in ('node', 'node.exe') or name.startswith('electron'):
            # 権限不足・壊れた引数一覧を「未起動」と見なさない。
            if not process_arguments(process.get('CommandLine') or '', windows):
                raise ValueError('Node / Electron の所属を確認できません')
    return False


def setup(choices=None) -> bool:
    del choices
    print_header("Discord セットアップ")
    print_info(f"作業ディレクトリ: {THIS_DIR}")
    print_info("対象: Discord / Node.js / Vue 3 / TypeScript / Electron")
    print_info("外部チャンネル: Discord / Slack")
    # npm ci は node_modules を削除するため、Electron の準備より先に確認する。
    try:
        if _discord_in_use():
            print_error('起動中の Discord は停止せず、この Discord の依存更新を保留しました。他項目だけ更新する場合は Discord を選択しないでください。')
            return False
    except (OSError, ValueError, subprocess.SubprocessError):
        print_error('Discord の停止状態を確認できないためセットアップを中止します。依存・設定は変更しません。')
        return False
    ok, detail = check_project_node_runtime(THIS_DIR, fallback=">=22.12.0")
    if detail.startswith("[WARN]"):
        print(detail)
    if not ok:
        print_error(detail)
        return False

    npm = shutil.which("npm.cmd" if sys.platform == "win32" else "npm")
    if not npm:
        print_error("Node.js 22.12 以降と npm を導入してください。")
        return False
    try:
        env = {**os.environ, 'ELECTRON_SKIP_BINARY_DOWNLOAD': '1'}
        print_info(f"実行中: {npm} ci --include=dev --no-fund --no-audit")
        subprocess.run([npm, "ci", "--include=dev", "--no-fund", "--no-audit"], cwd=THIS_DIR, env=env, check=True)
        # ロック済みの旧版に留めず、他のフロントエンドと同じ宣言範囲で更新する。
        print_info(f"実行中: {npm} run update:electron")
        subprocess.run([npm, "run", "update:electron"], cwd=THIS_DIR, env=env, check=True)
        # npm update は lockfile も変更する。検証対象を省略せず、導入済み依存から
        # 実際に Vue 配布物を生成して manifest と揃える（通常起動では再ビルドしない）。
        for script in ('build:panel', 'check:panel'):
            print_info(f"実行中: {npm} run {script}")
            subprocess.run([npm, "run", script], cwd=THIS_DIR, env=env, check=True)
        if not prepare_electron_binary(THIS_DIR, 'Discord'):
            return False
        install_launcher(THIS_DIR)
        # キーを独自に上書きせず、backend と同じ補完・原子的保存を使う。
        # conf パッケージの __init__ は requests 等の backend 依存を読むため、
        # 素の Python でも動く conf_json.py だけを直接読み込む。
        backend_dir = THIS_DIR.parent / "backend_server"
        sys.path.insert(0, str(backend_dir))
        spec = importlib.util.spec_from_file_location("_discord_conf_json", backend_dir / "conf" / "conf_json.py")
        conf_json_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(conf_json_mod)
        conf_json_mod.conf_json()
        print_success("共通設定の不足キーを補完しました。")
    except (OSError, ValueError, ImportError, subprocess.CalledProcessError):
        print_error("Discord の依存導入・パネル生成検証・共通設定の補完のいずれかに失敗しました。")
        return False
    print_success("Discord: aidiy_discord で起動できます。")
    return True


if __name__ == "__main__":
    sys.exit(0 if setup() else 1)
