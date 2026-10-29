# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026

"""この作業コピーのDiag本体・残留Electronを照合して停止する。"""
import importlib.util
from pathlib import Path
import sys

_spec = importlib.util.spec_from_file_location(
    'diag_cleanup_processes', Path(__file__).resolve().parents[2] / 'scripts' / '_cleanup_processes.py')
common = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(common)


def is_diag(process, root, windows):
    def normalize(value):
        value = str(value).replace('\\', '/').rstrip('/')
        return value.casefold() if windows else value

    root = Path(root).resolve()
    try:
        args = common.process_arguments(process.get('CommandLine') or '', windows)
    except ValueError:
        # 解析できない無関係なプロセスで、Diag の停止全体を中断しない。
        args = []
    executable = process.get('ExecutablePath') or (args[0] if args else '')
    binary = normalize(executable)
    distribution = normalize(root / 'node_modules' / 'electron' / 'dist') + '/'
    # 親を失ったGPU・renderer・utilityも、このDiag専用の実行ファイルで識別する。
    # macOS の Electron / Electron Helper は大文字名。名前だけを正規化し、
    # POSIX の作業コピー・実行ファイルのパス照合は大文字小文字を区別する。
    if binary.startswith(distribution) and binary.rsplit('/', 1)[-1].casefold() in (
            'electron.exe', 'electron', 'electron helper', 'electron helper (gpu)',
            'electron helper (renderer)', 'electron helper (plugin)'):
        return True
    name = normalize(process.get('Name') or '').rsplit('/', 1)[-1].casefold()
    if name not in ('node', 'node.exe', 'electron', 'electron.exe') or not args:
        return False
    entries = {normalize(root / 'diag_main.mjs'), normalize(root / '起動' / 'electron-main.cjs')}
    index = 1
    while index < len(args):
        arg = args[index]
        if arg in ('--eval', '--print') or arg.startswith(('-e', '-p', '--eval=', '--print=')):
            return False
        if arg in ('-r', '--require', '--import'):
            index += 2
            continue
        if arg == '--':
            index += 1
            break
        if not arg.startswith('-'):
            break
        index += 1
    # 他のスクリプトの引数にDiagのパスが含まれるだけなら対象外。
    return index < len(args) and normalize(args[index]) in entries


def stop(root):
    return common.stop_matching(
        lambda process: is_diag(process, root, sys.platform == 'win32'),
        print, print, 'AiDiy Diag')
