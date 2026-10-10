# -*- coding: utf-8 -*-
#
# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""aidiy_ide の PATH ランチャーを登録・解除する。"""
from pathlib import Path
import shlex
import shutil
import sys


def launcher_path() -> Path:
    return Path.home() / '.local' / 'bin' / ('aidiy_ide.cmd' if sys.platform == 'win32' else 'aidiy_ide')


def install_launcher(root: Path) -> None:
    node = shutil.which('node')
    if not node:
        raise OSError('Node.js が見つかりません。')
    script = root.resolve() / 'launch.mjs'
    if not script.is_file():
        raise OSError(f'起動スクリプトが見つかりません: {script}')
    path = launcher_path()
    # この配置先の旧コマンドを撤去する。互換ランチャーは作らない。
    legacy = path.with_name('aidiy_dev.cmd' if sys.platform == 'win32' else 'aidiy_dev')
    if legacy.is_file() and str(script) in legacy.read_text(encoding='utf-8'):
        legacy.unlink()
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
        # 別の作業コピーが登録したランチャーは消さない
        if path.is_file() and str(root.resolve() / 'launch.mjs') in path.read_text(encoding='utf-8'):
            path.unlink()
            print(f'[OK] ランチャーを削除しました: {path}')
        return True
    except OSError:
        print(f'[NG] ランチャーを削除できません: {path}')
        return False
