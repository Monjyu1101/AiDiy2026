"""全体起動から呼ぶ診断の環境確認・起動。AIコアや npm は不要。"""
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def check_environment():
    node = shutil.which('node.exe' if sys.platform == 'win32' else 'node')
    if not node:
        return False, 'Node.js 18 以降が必要です: https://nodejs.org/'
    if not (ROOT / 'diag_main.mjs').is_file() or not (ROOT / '診断' / 'catalog.json').is_file():
        return False, '診断のソースファイルが見つかりません。'
    try:
        version = subprocess.run([node, '--version'], stdin=subprocess.DEVNULL, capture_output=True, text=True,
                                 creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
                                 timeout=5, check=True).stdout.strip()
        if int(version.lstrip('v').split('.')[0]) < 18:
            return False, 'Node.js 18 以降が必要です: https://nodejs.org/'
    except (ValueError, OSError, subprocess.SubprocessError):
        return False, 'Node.js のバージョンを確認できません。'
    return True, 'Node.js / Electron またはブラウザ / AIコア不要'


def run_headless():
    """全体起動の必須前処理。完了を待ってモデル合成ファイルを生成する。"""
    node = shutil.which('node.exe' if sys.platform == 'win32' else 'node')
    if not node:
        raise RuntimeError('Node.js が見つかりません: https://nodejs.org/')
    result = subprocess.run([node, str(ROOT / 'diag_main.mjs'), '--headless'], cwd=ROOT,
                            stdin=subprocess.DEVNULL,
                            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
    if result.returncode:
        raise RuntimeError(f'aidiy_diag --headless に失敗しました（終了コード {result.returncode}）。')


def launch_gui():
    """全体起動の診断選択から呼ぶ。画面を切り離して起動し、表示準備の完了で戻る。
    --auto により、画面側で保存済みの起動設定による「設定起動」を自動実行する。"""
    node = shutil.which('node.exe' if sys.platform == 'win32' else 'node')
    if not node:
        raise RuntimeError('Node.js が見つかりません: https://nodejs.org/')
    result = subprocess.run([node, str(ROOT / 'diag_main.mjs'), '--auto'], cwd=ROOT, stdin=subprocess.DEVNULL,
                            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
    if result.returncode:
        raise RuntimeError(f'aidiy_diag の起動に失敗しました（終了コード {result.returncode}）。')


def start():
    node = shutil.which('node.exe' if sys.platform == 'win32' else 'node')
    if not node:
        raise RuntimeError('Node.js が見つかりません: https://nodejs.org/')
    # 認証 URL は直接ターミナルへ。集約出力のバッファ・ファイルへ保存しない。
    return subprocess.Popen([node, str(ROOT / 'diag_main.mjs'), '--foreground'], cwd=ROOT,
                            start_new_session=sys.platform != 'win32',
                            creationflags=(subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW) if sys.platform == 'win32' else 0)
