"""aidiy_discord の PATH ランチャーを登録・解除する。"""
from pathlib import Path
import shlex
import shutil
import sys


def launcher_path() -> Path:
    return Path.home() / '.local' / 'bin' / ('aidiy_discord.cmd' if sys.platform == 'win32' else 'aidiy_discord')


def install_launcher(root: Path) -> None:
    node = shutil.which('node')
    if not node:
        raise OSError('Node.js が見つかりません。')
    script = root.resolve() / 'panel' / 'launch.mjs'
    path = launcher_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if sys.platform == 'win32':
        content = f'@echo off\nchcp 65001 >nul\nsetlocal EnableExtensions DisableDelayedExpansion\n"{node}" "{script}" %*\nexit /b %errorlevel%\n'
        path.write_bytes(content.replace('\n', '\r\n').encode('utf-8'))
    else:
        path.write_text(f'#!/bin/sh\nexec {shlex.quote(node)} {shlex.quote(str(script))} "$@"\n', encoding='utf-8')
        path.chmod(0o755)
    print(f'[OK] ランチャーを登録しました: {path}')


def remove_launcher(root: Path) -> bool:
    path = launcher_path()
    try:
        if path.is_file() and str(root.resolve() / 'panel' / 'launch.mjs') in path.read_text(encoding='utf-8'):
            path.unlink()
        return True
    except OSError:
        print(f'[NG] ランチャーを削除できません: {path}')
        return False
