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
        "注意": "_sound_SeatBeltSign2fast.mp3",
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

# 通知種別の英語エイリアス（legacy 名）→ 日本語キーへの変換
_TYPE_ALIAS: dict[str, str] = {
    "ready":  "準備",   # ready  = 準備完了
    "up":     "開始",   # up     = 開始・上昇
    "down":   "終了",   # down   = 終了・下降
    "ok":     "完了",   # ok     = 完了・成功
    "ng":     "注意",   # ng     = 警告・エラー
    "accept": "承認",   # accept = 承認・受理
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

    def resolve_notification_type(self, notification_type: str) -> str:
        """通知種別を正規化（英語エイリアス（ready/up/down/ok/ng/accept）を日本語キーへ変換）"""
        t = (notification_type or "").strip()
        return _TYPE_ALIAS.get(t.lower(), t)

    def resolve_sound_path(self, notification_type: str, scene: str) -> Path:
        """通知種別と scene からサウンドファイルの絶対パスを返す"""
        actual_scene = self.resolve_scene(scene)
        actual_type = self.resolve_notification_type(notification_type)
        scene_sounds = _SCENE_MAP[actual_scene]
        filename = scene_sounds.get(actual_type)
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
            notification_type: "開始" / "終了" / "注意"（"up" / "down" / "ng" 等の英語エイリアスも可）
            scene: "auto" / "plane" / "legacy"

        Returns:
            {"status": "ok", "scene": ..., "notification_type": ..., "file": ...}
        """
        path = self.resolve_sound_path(notification_type, scene)
        actual_scene = self.resolve_scene(scene)
        actual_type = self.resolve_notification_type(notification_type)

        logger.info(f"通知音再生: type={actual_type} scene={actual_scene} file={path.name}")
        try:
            self._playsound(str(path))
        except Exception as e:
            logger.warning(f"通知音再生スキップ (スピーカー無効等): {e}")

        return {
            "status": "ok",
            "scene": actual_scene,
            "notification_type": actual_type,
            "file": path.name,
        }

    @staticmethod
    def _playsound(path: str) -> None:
        """pygame.mixer によるクロスプラットフォーム再生（mp3/wav 対応・再生完了まで待機）"""
        # pygame の import 時歓迎メッセージを抑制（MCP 標準出力を汚さないため）
        import os
        os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
        import pygame

        # mixer は未初期化なら初期化（多重 init は無害だが念のためガード）
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        # 再生が終わるまで待機（同期再生）
        while pygame.mixer.music.get_busy():
            pygame.time.wait(50)

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
