"""依存追加なしで aidiy_diag ランチャーを配置する。"""
import os
import hashlib
from pathlib import Path
import shlex
import sys

THIS_DIR = Path(__file__).resolve().parent


def launcher_content(script, windows=None):
    windows = sys.platform == 'win32' if windows is None else windows
    marker = 'aidiy_diag-owner:' + hashlib.sha256(str(script).encode('utf-8')).hexdigest()
    if windows:
        script = str(script).replace('%', '%%')
        return ('@echo off\r\nsetlocal DisableDelayedExpansion\r\n' + f'rem {marker}\r\n' + 'chcp 65001 >nul\r\n'
                'where node.exe >nul 2>nul\r\n'
                'if errorlevel 1 (echo Node.js 18+ is required: https://nodejs.org/ & exit /b 1)\r\n'
                f'node.exe "{script}" %*\r\nexit /b %ERRORLEVEL%\r\n')
    return ('#!/usr/bin/env sh\n' + f'# {marker}\n'
            'command -v node >/dev/null 2>&1 || { echo "Node.js 18+ is required: https://nodejs.org/" >&2; exit 1; }\n'
            f'exec node {shlex.quote(str(script))} "$@"\n')


def setup(choices=None):
    if choices is not None and choices.get('diag') is False:
        return True
    directory = Path.home() / '.local' / 'bin'
    launcher = directory / ('aidiy_diag.cmd' if sys.platform == 'win32' else 'aidiy_diag')
    try:
        directory.mkdir(parents=True, exist_ok=True)
        launcher.write_bytes(launcher_content(THIS_DIR / 'diag_main.mjs').encode('utf-8'))
        if sys.platform != 'win32':
            launcher.chmod(0o755)
    except OSError as exc:
        print(f'診断ランチャーを配置できません: {exc}')
        return False
    print(f'診断ランチャーを作成しました: {launcher}')
    if str(directory) not in os.environ.get('PATH', '').split(os.pathsep):
        print(f'{directory} を PATH に追加してください。')
    print('起動: aidiy_diag --browser（Node.js 標準モジュールのみ）')
    return True


if __name__ == '__main__':
    raise SystemExit(0 if setup() else 1)
