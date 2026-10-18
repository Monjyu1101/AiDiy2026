# -*- coding: utf-8 -*-
#
# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""aidiy_discord の PATH ランチャーを登録・解除する。"""
from pathlib import Path
import shlex
import shutil
import sys
import importlib.util

_path_spec = importlib.util.spec_from_file_location('aidiy_discord_launcher_path', Path(__file__).resolve().parent.parent / 'scripts' / '_setup_path.py')
_path_helper = importlib.util.module_from_spec(_path_spec)
_path_spec.loader.exec_module(_path_helper)
ensure_launcher_path = _path_helper.ensure_launcher_path
remove_launcher_path = _path_helper.remove_launcher_path


def launcher_path() -> Path:
    return Path.home() / '.local' / 'bin' / ('aidiy_discord.cmd' if sys.platform == 'win32' else 'aidiy_discord')


def install_launcher(root: Path) -> None:
    node = shutil.which('node')
    if not node:
        raise OSError('Node.js が見つかりません。')
    script = root.resolve() / 'panel' / 'launch.mjs'
    if not script.is_file():
        raise OSError(f'起動スクリプトが見つかりません: {script}')
    path = launcher_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if sys.platform == 'win32':
        content = f'@echo off\nchcp 65001 >nul\nsetlocal EnableExtensions DisableDelayedExpansion\n"{node}" "{script}" %*\nexit /b %errorlevel%\n'
        path.write_bytes(content.replace('\n', '\r\n').encode('utf-8'))
    else:
        path.write_text(f'#!/bin/sh\nexec {shlex.quote(node)} {shlex.quote(str(script))} "$@"\n', encoding='utf-8')
        path.chmod(0o755)
    print(f'[OK] ランチャーを登録しました: {path}')
    if not ensure_launcher_path(path.parent):
        raise OSError('ランチャーの PATH 登録に失敗しました。')


def remove_launcher(root: Path) -> bool:
    path = launcher_path()
    try:
        if path.is_file() and str(root.resolve() / 'panel' / 'launch.mjs') in path.read_text(encoding='utf-8'):
            path.unlink()
        return remove_launcher_path(path.parent)
    except OSError:
        print(f'[NG] ランチャーを削除できません: {path}')
        return False
