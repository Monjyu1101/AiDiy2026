# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026

"""Teamのランチャーを登録する。共有依存はIDE群のセットアップで導入する。"""
import importlib.util
from pathlib import Path
ROOT = Path(__file__).resolve().parent

def setup(choices=None):
    spec = importlib.util.spec_from_file_location('aidiy_team_launcher', ROOT.parent / 'viewer/launcher.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.install_launcher(ROOT, 'team')
    return True
