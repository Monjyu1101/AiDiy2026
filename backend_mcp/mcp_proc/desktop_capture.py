# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""
スクリーンショット取得モジュール

pyautogui / PIL.ImageGrab / screeninfo を使って
OS 画面を取得する。ウィンドウ操作は ctypes (Windows 専用、追加依存なし)。

参考: 認証済_スクリーンショット画像取得202405.py (Mitsuo KONDOU)
"""

import io
import os
import time
from typing import Optional

import pyautogui
import screeninfo
from PIL import Image, ImageDraw, ImageFont, ImageGrab


class DesktopCaptureError(Exception):
    """デスクトップキャプチャ取得エラー"""
    pass


class DesktopCapture:
    """
    デスクトップキャプチャ取得クラス

    screen_number パラメータ:
        "auto" — カーソルのあるモニター全体（デフォルト）
        "all"  — 全モニター結合
        "0"    — モニター番号 0
        "1"    — モニター番号 1
        ...
    """

    # ------------------------------------------------------------------ #
    # カーソル・モニター情報
    # ------------------------------------------------------------------ #

    def cursor_pos(self) -> tuple[int, int]:
        """現在のマウスカーソル座標を返す"""
        pos = pyautogui.position()
        return int(pos.x), int(pos.y)

    def monitors(self) -> list[dict]:
        """全モニターの情報を返す"""
        result = []
        for i, m in enumerate(screeninfo.get_monitors()):
            result.append({
                "index": i,
                "x": m.x,
                "y": m.y,
                "width": m.width,
                "height": m.height,
                "primary": getattr(m, "is_primary", i == 0),
            })
        return result

    # ------------------------------------------------------------------ #
    # 内部ヘルパー
    # ------------------------------------------------------------------ #

    def _grab_all(self) -> Image.Image:
        """全画面（全モニター結合）を取得"""
        try:
            return ImageGrab.grab(all_screens=True)
        except Exception:
            time.sleep(0.5)
            return ImageGrab.grab(all_screens=True)

    def _monitor_offsets(self) -> tuple[int, int]:
        """負座標モニターを考慮した全画面左上オフセットを返す"""
        mons = screeninfo.get_monitors()
        if not mons:
            return 0, 0
        min_x = min(m.x for m in mons)
        min_y = min(m.y for m in mons)
        return min_x, min_y

    # ------------------------------------------------------------------ #
    # スクリーンショット取得
    # ------------------------------------------------------------------ #

    def grab_screen(self, screen_number: str = "auto") -> tuple[Image.Image, dict]:
        """
        モニター単位でスクリーンショットを取得する。

        Returns:
            (image, info_dict)
            info_dict: x, y, width, height, cursor_x, cursor_y
        """
        mons = screeninfo.get_monitors()
        cursor_x, cursor_y = self.cursor_pos()

        if not mons:
            # fallback: pyautogui
            img = pyautogui.screenshot()
            return img, {
                "x": 0, "y": 0,
                "width": img.width, "height": img.height,
                "cursor_x": cursor_x, "cursor_y": cursor_y,
            }

        all_img = self._grab_all()
        min_x, min_y = self._monitor_offsets()

        if str(screen_number) == "all":
            return all_img, {
                "x": min_x, "y": min_y,
                "width": all_img.width, "height": all_img.height,
                "cursor_x": cursor_x, "cursor_y": cursor_y,
            }

        # モニター選択
        target = None
        if str(screen_number).isdigit():
            idx = int(screen_number)
            if 0 <= idx < len(mons):
                target = mons[idx]

        if target is None:  # "auto" またはインデックス範囲外 → カーソルのあるモニター
            for m in mons:
                if m.x <= cursor_x < m.x + m.width and m.y <= cursor_y < m.y + m.height:
                    target = m
                    break
            if target is None:
                target = mons[0]

        # 全画面から切り出し
        left = target.x - min_x
        top  = target.y - min_y
        img  = all_img.crop((left, top, left + target.width, top + target.height))

        return img, {
            "x": target.x, "y": target.y,
            "width": target.width, "height": target.height,
            "cursor_x": cursor_x, "cursor_y": cursor_y,
        }

    def grab_cursor_region(self, size: int, screen_number: str = "auto") -> tuple[Image.Image, dict]:
        """
        カーソル中心に size×size px の領域を切り出す。

        モニター境界でクランプするため、実際のサイズが size を下回る場合がある。

        Returns:
            (image, info_dict)
            info_dict: screen_x, screen_y, screen_width, screen_height,
                       cursor_x, cursor_y, crop_rel_x, crop_rel_y
        """
        screen_img, info = self.grab_screen(screen_number)
        cx, cy = info["cursor_x"], info["cursor_y"]

        # スクリーン相対座標に変換
        rel_x = cx - info["x"]
        rel_y = cy - info["y"]

        half  = size // 2
        left  = max(0, rel_x - half)
        top   = max(0, rel_y - half)
        right = min(info["width"],  rel_x + half)
        bottom = min(info["height"], rel_y + half)

        img = screen_img.crop((left, top, right, bottom))
        return img, {
            **info,
            "crop_rel_x": left,
            "crop_rel_y": top,
            "crop_width": right - left,
            "crop_height": bottom - top,
        }

    def grab_region(self, x: int, y: int, width: int, height: int) -> Image.Image:
        """絶対座標で領域を切り出す"""
        min_x, min_y = self._monitor_offsets()
        all_img = self._grab_all()
        left = x - min_x
        top  = y - min_y
        return all_img.crop((left, top, left + width, top + height))

    def grab_window(self, title: str) -> tuple[Image.Image, dict]:
        """
        ウィンドウタイトル（部分一致）でウィンドウをキャプチャする。
        Windows 専用（ctypes 使用、pywin32 不要）。

        Returns:
            (image, info_dict)  info_dict: hwnd, title, x, y, width, height
        """
        if os.name != "nt":
            raise DesktopCaptureError("ウィンドウキャプチャは Windows のみ対応しています")

        import ctypes
        from ctypes import wintypes

        found: dict = {}

        EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

        @EnumProc
        def _enum_cb(hwnd, lparam):
            if not ctypes.windll.user32.IsWindowVisible(hwnd):
                return True
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True
            buf = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
            win_title = buf.value
            if title.lower() in win_title.lower():
                found["hwnd"]  = hwnd
                found["title"] = win_title
                return False  # 最初にヒットしたものを使用
            return True

        ctypes.windll.user32.EnumWindows(_enum_cb, 0)

        if not found:
            raise DesktopCaptureError(f"ウィンドウが見つかりません: '{title}'")

        hwnd = found["hwnd"]
        rect = wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))

        x, y = rect.left, rect.top
        w, h = rect.right - rect.left, rect.bottom - rect.top
        if w <= 0 or h <= 0:
            raise DesktopCaptureError(f"ウィンドウサイズが不正です: '{found['title']}'")

        img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
        return img, {
            "hwnd":   hwnd,
            "title":  found["title"],
            "x": x, "y": y,
            "width": w, "height": h,
        }

    def list_windows(self) -> list[dict]:
        """
        表示中ウィンドウの一覧を返す。
        Windows 専用（ctypes 使用、pywin32 不要）。
        """
        if os.name != "nt":
            return []

        import ctypes
        from ctypes import wintypes

        windows: list[dict] = []

        EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

        @EnumProc
        def _enum_cb(hwnd, lparam):
            if not ctypes.windll.user32.IsWindowVisible(hwnd):
                return True
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True
            buf = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
            win_title = buf.value
            if win_title:
                rect = wintypes.RECT()
                ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
                w = rect.right  - rect.left
                h = rect.bottom - rect.top
                if w > 0 and h > 0:
                    windows.append({
                        "hwnd":   hwnd,
                        "title":  win_title,
                        "x":      rect.left,
                        "y":      rect.top,
                        "width":  w,
                        "height": h,
                    })
            return True

        ctypes.windll.user32.EnumWindows(_enum_cb, 0)
        return windows

    # ------------------------------------------------------------------ #
    # アノテーション
    # ------------------------------------------------------------------ #

    def annotate(
        self,
        img: Image.Image,
        crosshair_pos: Optional[tuple[int, int]] = None,
        label_text: Optional[str] = None,
    ) -> Image.Image:
        """
        画像にアノテーションを追加する。

        Args:
            crosshair_pos: 十字線を描く座標（画像内相対座標）
            label_text: 右下に表示するラベルテキスト
        """
        img = img.copy()
        draw = ImageDraw.Draw(img)

        if crosshair_pos:
            cx, cy = crosshair_pos
            color = (255, 50, 50)
            arm   = 20
            thick = 2
            draw.line([(cx - arm, cy), (cx + arm, cy)], fill=color, width=thick)
            draw.line([(cx, cy - arm), (cx, cy + arm)], fill=color, width=thick)
            r = 8
            draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline=color, width=thick)

        if label_text:
            w, h = img.size
            margin = 4
            # フォントサイズ推定（デフォルトフォントは約10px幅/文字）
            char_w, char_h = 8, 14
            text_w = len(label_text) * char_w
            bx0 = w - text_w - margin * 2
            by0 = h - char_h - margin * 2
            draw.rectangle([(bx0, by0), (w, h)], fill=(0, 0, 0, 180))
            draw.text((bx0 + margin, by0 + margin), label_text, fill=(255, 255, 255))

        return img

    # ------------------------------------------------------------------ #
    # 出力
    # ------------------------------------------------------------------ #

    def to_bytes(self, img: Image.Image, fmt: str = "png", quality: int = 85) -> bytes:
        """PIL Image を PNG または JPEG バイト列に変換する"""
        buf = io.BytesIO()
        fmt_upper = fmt.upper()
        if fmt_upper in ("JPEG", "JPG"):
            img = img.convert("RGB")
            img.save(buf, format="JPEG", quality=quality, optimize=True)
        else:
            img.save(buf, format="PNG", optimize=True)
        return buf.getvalue()
