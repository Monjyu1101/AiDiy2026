# -*- coding: utf-8 -*-
#
# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101
# -------------------------------------------------------------------------

from __future__ import annotations

import ctypes
import json
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class GuiSettings:
    gui_name: str = "AiDiy GUI"
    auth_base_url: str = "http://localhost:8091"
    display_backend: str = "three-vrm"
    scale: float = 0.24
    always_on_top: bool = True
    start_position: str = "bottom-right"
    offset_x: int = 20
    offset_y: int = 5
    message_duration_ms: int = 9000
    vrm_path: str = "GUI制御/vrm/AiDiy_Sample_M.vrm"
    vrm_window_width: int = 320
    vrm_window_height: int = 320

    @classmethod
    def 読み込み(cls, path: Path) -> "GuiSettings":
        if not path.exists():
            return cls()
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        base = cls()
        for key, value in data.items():
            if hasattr(base, key):
                setattr(base, key, value)
        return base


@dataclass(slots=True)
class AuthSession:
    user_id: str
    access_token: str
    token_type: str
    initial_page: str = ""


@dataclass(slots=True)
class CoreEvent:
    kind: str
    socket_no: str
    payload: dict | None = None
    message: str = ""


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]


def システムアイドル秒数を取得() -> float | None:
    if sys.platform != "win32":
        return None
    last_input = LASTINPUTINFO()
    last_input.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(last_input)):
        return None
    tick_count = ctypes.windll.kernel32.GetTickCount()
    return max(0.0, (tick_count - last_input.dwTime) / 1000.0)
