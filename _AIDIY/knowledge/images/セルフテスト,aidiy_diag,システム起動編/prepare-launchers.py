"""通常コマンドの再試験に必要な既存ランチャー登録を呼ぶ。"""
from pathlib import Path
import runpy
ROOT = Path(__file__).resolve().parents[4]
def load(relative):
    return runpy.run_path(str(ROOT / relative))
assert load('backend_diag/_setup.py')['setup'](desktop=False)
assert load('frontend_avatar/_setup.py')['install_standalone_launcher']()
assert load('frontend_ide/host/_setup.py')['install_standalone_launcher']()
assert load('frontend_ide/aidiy_term/_setup.py')['setup']()
load('frontend_ide/viewer/launcher.py')['install_launcher'](ROOT / 'frontend_ide/viewer')
load('frontend_channels/launcher.py')['install_launcher'](ROOT / 'frontend_channels')
