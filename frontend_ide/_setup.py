# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026

"""Console / Code / Live / IDE / Task / Team / Browserの依存・拡張・ランチャーをまとめて準備する。"""
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "scripts"))
from _setup_electron import frontend_dependency_guard
from _runtime_requirements import check_project_node_runtime

def prepare():
    ok, detail = check_project_node_runtime(ROOT, dependency="vite", fallback="^20.19.0 || >=22.12.0")
    if detail.startswith("[WARN]"):
        print(detail)
    if not ok:
        print(detail)
        return False

    npm = shutil.which('npm.cmd' if sys.platform == 'win32' else 'npm')
    if not npm:
        print("[NG] npm が見つかりません。対応する Node.js と同梱の npm を導入してください。")
        return False
    try:
        reuse = frontend_dependency_guard(ROOT, 'Console / Code / Live / IDE / Task / Team / Browser 共通UI', desktop=False)
        if reuse is not None:
            return reuse
        subprocess.run([npm, 'ci', '--include=dev', '--no-fund', '--no-audit'], cwd=ROOT, check=True)
        return True
    except (OSError, subprocess.CalledProcessError):
        return False

def load_setup_module(name):
    spec = importlib.util.spec_from_file_location('ide_setup_' + name.replace('/', '_'), ROOT.parent / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def register_launchers(host):
    """依存準備後に7コマンドを連続表示し、共有PATHの案内は一度だけ行う。"""
    launcher = load_setup_module('frontend_ide/viewer/launcher.py')
    print("\n起動コマンドの登録:")
    try:
        launcher.install_launcher(ROOT / 'aidiy_console', 'console', register_path=False)
        if not host.install_standalone_launcher(register_path=False):
            return False
        for kind, folder in (('ide', 'viewer'), ('task', 'aidiy_task'), ('team', 'aidiy_team'), ('browser', 'aidiy_browser')):
            launcher.install_launcher(ROOT / folder, kind, register_path=False)
        if not launcher.ensure_launcher_path(launcher.launcher_path().parent):
            print("[NG] 起動コマンドの PATH 登録に失敗しました。")
            return False
    except OSError as exc:
        print(f"[NG] 起動コマンドの登録に失敗しました: {exc}")
        return False
    return True


def setup(choices=None):
    if choices is not None and choices.get("ide") is False:
        return True
    print("\n" + "=" * 60)
    print("Console / Code / Live / IDE / Task / Team / Browser セットアップ")
    print("=" * 60 + "\n")
    print("対象: Node.js / Vue 3 / Vite / TypeScript / Electron / VS Code / VSIX")
    child_choices = {**(choices or {}), "ide": True, "_defer_ide_launchers": True}
    # hostからprepareだけを呼ぶため再帰しない。
    host = None
    for name in ('frontend_ide/aidiy_console', 'frontend_ide/host', 'frontend_ide/viewer', 'frontend_ide/aidiy_task', 'frontend_ide/aidiy_team', 'frontend_ide/aidiy_browser'):
        module = load_setup_module(name + '/_setup.py')
        if name == 'frontend_ide/host':
            host = module
        if not module.setup(child_choices):
            return False
    if not register_launchers(host):
        return False
    print("Console / Code / Live / IDE / Task / Team / Browser セットアップ完了")
    names = ('Console', 'Code', 'Live', 'IDE', 'Task', 'Team', 'Browser')
    width = max(map(len, names))
    for name in names:
        print(f"{name:<{width}} 起動: aidiy_{name.lower()}")
    return True

if __name__ == '__main__':
    sys.exit(0 if setup() else 1)
