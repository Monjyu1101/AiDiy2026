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
    if not (ROOT / 'diag_main.mjs').is_file() or not (ROOT / 'catalog.json').is_file():
        return False, '診断のソースファイルが見つかりません。'
    try:
        version = subprocess.run([node, '--version'], capture_output=True, text=True, timeout=5, check=True).stdout.strip()
        if int(version.lstrip('v').split('.')[0]) < 18:
            return False, 'Node.js 18 以降が必要です: https://nodejs.org/'
    except (ValueError, OSError, subprocess.SubprocessError):
        return False, 'Node.js のバージョンを確認できません。'
    return True, 'Node.js / Electron またはブラウザ / AIコア不要'


def start():
    node = shutil.which('node.exe' if sys.platform == 'win32' else 'node')
    if not node:
        raise RuntimeError('Node.js が見つかりません: https://nodejs.org/')
    # 認証 URL は直接ターミナルへ。集約出力のバッファ・ファイルへ保存しない。
    return subprocess.Popen([node, str(ROOT / 'diag_main.mjs')], cwd=ROOT,
                            start_new_session=sys.platform != 'win32',
                            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0)
