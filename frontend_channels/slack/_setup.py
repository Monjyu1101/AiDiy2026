# -*- coding: utf-8 -*-
#
# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""Slack フロントエンドの依存導入と、共通設定の不足キー補完。"""
import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))
# 全体処理で他フォルダの同名 launcher がキャッシュされても取り違えない。
_launcher_spec = importlib.util.spec_from_file_location('aidiy_frontend_slack_launcher', THIS_DIR / 'launcher.py')
_launcher = importlib.util.module_from_spec(_launcher_spec)
_launcher_spec.loader.exec_module(_launcher)
install_launcher = _launcher.install_launcher
sys.path.insert(0, str(THIS_DIR.parent.parent / 'scripts'))
from _runtime_requirements import check_project_node_runtime
from _setup_electron import prepare_electron_binary, _runtime_in_use
from slack_processes import slack_tree_pids


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


def _slack_in_use() -> bool:
    """この配置先のパネル・Bot を読み取りだけで確認する（Discord の _discord_in_use と同じ役割）。"""
    return bool(slack_tree_pids(THIS_DIR)) or _runtime_in_use(THIS_DIR)


def setup(choices=None) -> bool:
    del choices
    print_header("Slack セットアップ")
    print_info(f"作業ディレクトリ: {THIS_DIR}")
    print_info("対象: Slack / Node.js / Vue 3 / TypeScript / Electron（HTTPS の定期取得、WebSocket 不使用）")
    # npm ci は node_modules を削除するため、稼働中のパネル・Bot がないことを先に確認する。
    try:
        if _slack_in_use():
            print_error('起動中の Slack は停止せず、依存更新を保留しました。他項目だけ更新する場合は Slack を選択しないでください。')
            return False
    except (OSError, ValueError, subprocess.SubprocessError):
        print_error('Slack の停止状態を確認できないためセットアップを中止します。依存・設定は変更しません。')
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
        # Electron 本体は npm で取得せず、他のフロントエンドの配置・共有 ZIP を再利用する。
        env = {**os.environ, 'ELECTRON_SKIP_BINARY_DOWNLOAD': '1'}
        command = "ci" if (THIS_DIR / "package-lock.json").is_file() else "install"
        print_info(f"実行中: {npm} {command} --include=dev --no-fund --no-audit")
        subprocess.run([npm, command, "--include=dev", "--no-fund", "--no-audit"], cwd=THIS_DIR, env=env, check=True)
        # Discord と同じく、ロック済みの旧版に留めず宣言範囲で Electron を更新する。
        print_info(f"実行中: {npm} run update:electron")
        subprocess.run([npm, "run", "update:electron"], cwd=THIS_DIR, env=env, check=True)
        # 導入済み依存から Vue 配布物を生成して manifest と揃える（通常起動では再ビルドしない）。
        for script in ('build:panel', 'check:panel'):
            print_info(f"実行中: {npm} run {script}")
            subprocess.run([npm, "run", script], cwd=THIS_DIR, env=env, check=True)
        if not prepare_electron_binary(THIS_DIR, 'Slack'):
            return False
        install_launcher(THIS_DIR)
        # キーを独自に上書きせず、backend と同じ補完・原子的保存を使う。
        backend_dir = THIS_DIR.parent.parent / "backend_server"
        sys.path.insert(0, str(backend_dir))
        spec = importlib.util.spec_from_file_location("_slack_conf_json", backend_dir / "conf" / "conf_json.py")
        conf_json_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(conf_json_mod)
        conf_json_mod.conf_json()
        print_success("共通設定の不足キーを補完しました。")
    except (OSError, ValueError, ImportError, subprocess.CalledProcessError):
        print_error("Slack の依存導入・パネル生成検証・ランチャー登録・共通設定の補完のいずれかに失敗しました。")
        return False
    print_success("Slack: aidiy_slack で起動できます。")
    return True


if __name__ == "__main__":
    sys.exit(0 if setup() else 1)
