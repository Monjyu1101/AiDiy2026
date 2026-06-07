# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""
通知音再生モジュール

scene に応じた通知音（開始・終了・注意）をローカル再生する。

scene:
    "auto" / "plane" — 機内シーン (SeatBeltSign1/2/3)
    "legacy"         — 旧来の効果音 (ready / ok / ng)
"""

import os
import subprocess
from pathlib import Path

from log_config import get_logger

logger = get_logger(__name__)

# サウンドファイルが格納されているディレクトリ（backend_tools/sounds/）
_SOUNDS_DIR = Path(__file__).resolve().parent.parent / "sounds"

# scene → 通知種別 → ファイル名のマッピング
_SCENE_MAP: dict[str, dict[str, str]] = {
    "plane": {
        "準備": "_sound_SeatBeltSign3.mp3",
        "開始": "_sound_SeatBeltSign1.mp3",
        "終了": "_sound_SeatBeltSign2.mp3",
        "完了": "_sound_SeatBeltSign1.mp3",
        "注意": "_sound_SeatBeltSign2.mp3",
        "承認": "_sound_SeatBeltSign1.mp3",
    },
    "legacy": {
        "準備": "_sound_ready.mp3",    # ready   = 準備完了
        "開始": "_sound_up.mp3",       # up      = 開始・上昇
        "終了": "_sound_down.mp3",     # down    = 終了・下降
        "完了": "_sound_ok.mp3",       # ok      = 完了・成功
        "注意": "_sound_ng.mp3",       # ng      = 警告・エラー
        "承認": "_sound_accept.mp3",   # accept  = 承認・受理
    },
}

# "auto" は "plane" にマップ
_SCENE_ALIAS: dict[str, str] = {
    "auto": "plane",
}

VALID_SCENES = ["auto", "plane", "legacy"]
VALID_TYPES_PLANE  = ["準備", "開始", "終了", "完了", "注意", "承認"]
VALID_TYPES_LEGACY = ["準備", "開始", "終了", "完了", "注意", "承認"]
VALID_TYPES        = VALID_TYPES_LEGACY  # 全体の上位集合


class NotificationSoundsError(Exception):
    """通知音エラー"""
    pass


class NotificationSounds:
    """通知音再生クラス"""

    def resolve_scene(self, scene: str) -> str:
        """scene 文字列を正規化して実 scene キーを返す"""
        s = (scene or "auto").strip().lower()
        s = _SCENE_ALIAS.get(s, s)
        if s not in _SCENE_MAP:
            raise NotificationSoundsError(
                f"未対応の scene です: '{scene}'（auto / plane / legacy）"
            )
        return s

    def resolve_sound_path(self, notification_type: str, scene: str) -> Path:
        """通知種別と scene からサウンドファイルの絶対パスを返す"""
        actual_scene = self.resolve_scene(scene)
        scene_sounds = _SCENE_MAP[actual_scene]
        filename = scene_sounds.get(notification_type)
        if filename is None:
            raise NotificationSoundsError(
                f"未対応の通知種別です: '{notification_type}'（開始 / 終了 / 注意）"
            )
        path = _SOUNDS_DIR / filename
        if not path.exists():
            raise NotificationSoundsError(
                f"サウンドファイルが見つかりません: {path}"
            )
        return path

    def play(self, notification_type: str, scene: str = "auto") -> dict:
        """
        通知音を再生する。

        Args:
            notification_type: "開始" / "終了" / "注意"
            scene: "auto" / "plane" / "legacy"

        Returns:
            {"status": "ok", "scene": ..., "notification_type": ..., "file": ...}
        """
        path = self.resolve_sound_path(notification_type, scene)
        actual_scene = self.resolve_scene(scene)

        logger.info(f"通知音再生: type={notification_type} scene={actual_scene} file={path.name}")
        try:
            self._playsound(str(path))
        except Exception as e:
            logger.warning(f"通知音再生スキップ (スピーカー無効等): {e}")

        return {
            "status": "ok",
            "scene": actual_scene,
            "notification_type": notification_type,
            "file": path.name,
        }

    @staticmethod
    def _playsound(path: str) -> None:
        """プラットフォーム別最小サウンド再生。Windows: winmm、macOS: afplay、Linux: gst"""
        import platform
        pf = platform.system()
        if pf == "Windows":
            import ctypes
            ext = os.path.splitext(path)[1].lower()
            mci_type = "waveaudio" if ext == ".wav" else "mpegvideo"
            ctypes.windll.winmm.mciSendStringW(
                f'open "{path}" type {mci_type} alias _ns', None, 0, None)
            ctypes.windll.winmm.mciSendStringW(
                'play _ns wait', None, 0, None)
            ctypes.windll.winmm.mciSendStringW(
                'close _ns', None, 0, None)
        elif pf == "Darwin":
            subprocess.run(["afplay", path], timeout=30, check=False)
        else:
            subprocess.run(
                ["gst-launch-1.0", "playbin", f"uri=file://{path}"],
                timeout=30, check=False,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )

    def list_sounds(self, scene: str = "auto") -> dict:
        """指定 scene のサウンドマッピング一覧を返す"""
        actual_scene = self.resolve_scene(scene)
        result = {}
        for ntype, filename in _SCENE_MAP[actual_scene].items():
            path = _SOUNDS_DIR / filename
            result[ntype] = {
                "file": filename,
                "exists": path.exists(),
                "path": str(path),
            }
        return {
            "scene": actual_scene,
            "sounds": result,
        }
