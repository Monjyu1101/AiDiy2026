# -*- coding: utf-8 -*-
"""_setup.py から install_electron_binary() だけを実行する一時スクリプト"""

import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))

from _setup import install_electron_binary, FRONTEND_AVATAR_DIR

label = "フロントエンド(Avatar)"
print(f"[INFO] Electron バイナリのみ取得します: {FRONTEND_AVATAR_DIR}")
result = install_electron_binary(FRONTEND_AVATAR_DIR, label)
print("結果:", "OK" if result else "NG")
