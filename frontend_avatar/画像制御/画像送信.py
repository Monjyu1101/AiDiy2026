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

import base64
import ctypes
import io
import queue
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from PIL import Image, ImageChops, ImageGrab, ImageOps, ImageStat

from log_config import get_logger
from 通信制御.コア接続 import AIAvatarConnector

logger = get_logger(__name__)

コンテンツ種別 = Literal["camera", "desktop", "file"]

キャプチャ間隔秒 = 0.55
差分しきい値パーセント = 3.0
安定待機秒 = 2.0
強制送信秒 = 60.0
比較画像サイズ = (64, 36)
送信JPEG品質 = 80
プレビュー最大サイズ = (132, 74)


@dataclass(slots=True)
class 画像プレビューイベント:
    source_type: str
    source_label: str
    image: Image.Image | None
    flash: bool = False


@dataclass(slots=True)
class スクリーン情報:
    index: int
    left: int
    top: int
    right: int
    bottom: int
    label: str


@dataclass(slots=True)
class フォーム情報:
    hwnd: int
    title: str
    left: int
    top: int
    right: int
    bottom: int
    label: str


class 画像送信制御:
    def __init__(self, auth_user_id: str, connector: AIAvatarConnector, preview_queue: queue.Queue[画像プレビューイベント]) -> None:
        self.auth_user_id = auth_user_id
        self.connector = connector
        self.preview_queue = preview_queue
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._active = False
        self._source_type: コンテンツ種別 = "camera"
        self._source_label = "カメラ"
        self._file_image: Image.Image | None = None
        self._desktop_bbox: tuple[int, int, int, int] | None = None
        self._desktop_window_handle: int | None = None
        self._last_small_image: Image.Image | None = None
        self._last_change_at = 0.0
        self._last_send_at = 0.0
        self._stable_sent = False
        self._video_capture = None

    def 種別一覧(self) -> list[tuple[str, str]]:
        return [("camera", "カメラ"), ("desktop", "デスクトップ"), ("file", "画像ファイル")]

    def スクリーン一覧を取得(self) -> list[スクリーン情報]:
        if sys.platform == "win32":
            return self._Windowsスクリーン一覧を取得()
        try:
            image = ImageGrab.grab()
            width, height = image.size
            return [スクリーン情報(index=0, left=0, top=0, right=width, bottom=height, label=f"スクリーン1 ({width}x{height})")]
        except Exception:
            return [スクリーン情報(index=0, left=0, top=0, right=1920, bottom=1080, label="スクリーン1")]

    def フォーム一覧を取得(self) -> list[フォーム情報]:
        if sys.platform != "win32":
            return []

        windows: list[フォーム情報] = []

        class RECT(ctypes.Structure):
            _fields_ = [
                ("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long),
            ]

        enum_proc = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)
        user32 = ctypes.windll.user32

        def callback(hwnd, _lparam):
            if not user32.IsWindowVisible(hwnd):
                return 1
            if user32.IsIconic(hwnd):
                return 1
            length = user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return 1
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            title = buffer.value.strip()
            if not title:
                return 1
            rect = RECT()
            if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                return 1
            width = rect.right - rect.left
            height = rect.bottom - rect.top
            if width < 80 or height < 80:
                return 1
            windows.append(
                フォーム情報(
                    hwnd=int(hwnd),
                    title=title,
                    left=rect.left,
                    top=rect.top,
                    right=rect.right,
                    bottom=rect.bottom,
                    label=f"{title} ({width}x{height})",
                )
            )
            return 1

        user32.EnumWindows(enum_proc(callback), 0)
        return windows

    def 現在の種別を取得(self) -> str:
        with self._lock:
            return self._source_type

    def 現在のラベルを取得(self) -> str:
        with self._lock:
            return self._source_label

    def コンテンツ種別を設定(
        self,
        source_type: コンテンツ種別,
        file_path: Path | None = None,
        screen_index: int | None = None,
        desktop_mode: str | None = None,
        window_handle: int | None = None,
    ) -> bool:
        file_image: Image.Image | None = None
        desktop_bbox: tuple[int, int, int, int] | None = None
        desktop_label = "デスクトップ"
        if source_type == "file":
            if file_path is None:
                return False
            try:
                with Image.open(file_path) as image:
                    file_image = ImageOps.exif_transpose(image).convert("RGB").copy()
            except Exception as exc:
                logger.error("画像ファイルの読み込みに失敗しました: %s", exc)
                return False
        elif source_type == "desktop":
            if desktop_mode == "window":
                windows = self.フォーム一覧を取得()
                selected_window = next((window for window in windows if window.hwnd == window_handle), None)
                if selected_window is None:
                    return False
                desktop_label = f"フォーム: {selected_window.title}"
            else:
                screens = self.スクリーン一覧を取得()
                if not screens:
                    return False
                selected = next((screen for screen in screens if screen.index == screen_index), screens[0])
                desktop_bbox = (selected.left, selected.top, selected.right, selected.bottom)
                desktop_label = selected.label

        with self._lock:
            self._source_type = source_type
            self._source_label = {
                "camera": "カメラ",
                "desktop": desktop_label,
                "file": f"画像: {file_path.name}" if file_path else "画像ファイル",
            }[source_type]
            self._file_image = file_image
            self._desktop_bbox = desktop_bbox
            self._desktop_window_handle = window_handle if desktop_mode == "window" else None
            self._last_small_image = None
            now = time.time()
            self._last_change_at = now
            self._last_send_at = 0.0
            self._stable_sent = False

        self._カメラを閉じる()
        preview = file_image if file_image is not None else self._フレームを取得()
        self._プレビューを通知(preview)
        return True

    def 開始(self) -> bool:
        with self._lock:
            if self._active:
                return True
            source_type = self._source_type
            has_file_image = self._file_image is not None
        if source_type == "file" and not has_file_image:
            return False
        if source_type == "camera" and self._カメラを取得() is None:
            return False
        with self._lock:
            if self._active:
                return True
            self._active = True
            self._stop_event.clear()
            self._last_small_image = None
            now = time.time()
            self._last_change_at = now
            self._last_send_at = 0.0
            self._stable_sent = False
            if self._thread is None or not self._thread.is_alive():
                self._thread = threading.Thread(target=self._ループを実行, name="avatar-image-stream", daemon=True)
                self._thread.start()
        return True

    def 停止(self) -> None:
        with self._lock:
            self._active = False
        self._カメラを閉じる()
        self._プレビューを通知(None)

    def 終了(self) -> None:
        self.停止()
        self._stop_event.set()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=1.0)

    def _ループを実行(self) -> None:
        while not self._stop_event.is_set():
            with self._lock:
                active = self._active
                source_type = self._source_type

            if not active:
                time.sleep(0.1)
                continue

            try:
                if source_type == "file":
                    self._静止画像を処理()
                else:
                    self._動画画像を処理()
            except Exception as exc:
                logger.exception("画像送信ループでエラーが発生しました: %s", exc)
                time.sleep(1.0)
            time.sleep(キャプチャ間隔秒)

    def _静止画像を処理(self) -> None:
        with self._lock:
            image = self._file_image.copy() if self._file_image is not None else None
        if image is None:
            return
        self._プレビューを通知(image)
        now = time.time()
        if self._last_send_at <= 0 or (強制送信秒 > 0 and now - self._last_send_at >= 強制送信秒):
            self._画像を送信(image)
            self._last_send_at = now

    def _動画画像を処理(self) -> None:
        image = self._フレームを取得()
        if image is None:
            return
        self._プレビューを通知(image)
        small = image.resize(比較画像サイズ, Image.Resampling.BILINEAR).convert("RGB")
        if self._last_small_image is not None:
            diff = self._差分率を計算(self._last_small_image, small)
            if diff > 差分しきい値パーセント:
                self._last_change_at = time.time()
                self._stable_sent = False
        self._last_small_image = small

        now = time.time()
        stable = now - self._last_change_at >= 安定待機秒
        forced = 強制送信秒 > 0 and self._last_send_at > 0 and (now - self._last_send_at >= 強制送信秒)
        if (stable and not self._stable_sent) or forced:
            self._画像を送信(image)
            self._last_send_at = now
            if stable:
                self._stable_sent = True

    def _フレームを取得(self) -> Image.Image | None:
        source_type = self.現在の種別を取得()
        if source_type == "desktop":
            try:
                with self._lock:
                    bbox = self._desktop_bbox
                    window_handle = self._desktop_window_handle
                if window_handle:
                    return ImageGrab.grab(window=window_handle).convert("RGB")
                return ImageGrab.grab(bbox=bbox).convert("RGB")
            except Exception as exc:
                logger.error("デスクトップ画像取得に失敗しました: %s", exc)
                return None
        if source_type == "camera":
            capture = self._カメラを取得()
            if capture is None:
                return None
            ok, frame = capture.read()
            if not ok or frame is None:
                return None
            try:
                import cv2  # type: ignore
            except Exception as exc:
                logger.error("OpenCV の読み込みに失敗しました: %s", exc)
                return None
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return Image.fromarray(rgb_frame)
        with self._lock:
            return self._file_image.copy() if self._file_image is not None else None

    def _カメラを取得(self):
        with self._lock:
            if self._video_capture is not None:
                return self._video_capture
        try:
            import cv2  # type: ignore
        except Exception as exc:
            logger.error("OpenCV の読み込みに失敗しました: %s", exc)
            return None
        backend = cv2.CAP_DSHOW if hasattr(cv2, "CAP_DSHOW") else 0
        capture = cv2.VideoCapture(0, backend)
        if not capture.isOpened():
            try:
                capture.release()
            except Exception:
                pass
            logger.error("カメラを開けませんでした")
            return None
        with self._lock:
            self._video_capture = capture
        return capture

    def _カメラを閉じる(self) -> None:
        with self._lock:
            capture = self._video_capture
            self._video_capture = None
        if capture is not None:
            try:
                capture.release()
            except Exception:
                pass

    def _差分率を計算(self, before: Image.Image, after: Image.Image) -> float:
        diff = ImageChops.difference(before, after)
        rms = sum(ImageStat.Stat(diff).rms[:3]) / 3.0
        return (rms / 255.0) * 100.0

    def _画像を送信(self, image: Image.Image) -> None:
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=送信JPEG品質)
        base64_data = base64.b64encode(buffer.getvalue()).decode("ascii")
        payload = {
            "セッションID": self.auth_user_id,
            "チャンネル": "input",
            "出力先チャンネル": "0",
            "メッセージ識別": "input_image",
            "メッセージ内容": "image/jpeg",
            "ファイル名": base64_data,
            "サムネイル画像": None,
        }
        if self.connector.JSONを送信("input", payload):
            logger.info("画像送信: source=%s bytes=%s", self.現在の種別を取得(), len(base64_data))
            self._プレビューを通知(image, flash=True)

    def _プレビューを通知(self, image: Image.Image | None, flash: bool = False) -> None:
        preview = None
        if image is not None:
            preview = image.copy()
            preview.thumbnail(プレビュー最大サイズ, Image.Resampling.LANCZOS)
        try:
            self.preview_queue.put_nowait(
                画像プレビューイベント(
                    source_type=self.現在の種別を取得(),
                    source_label=self.現在のラベルを取得(),
                    image=preview,
                    flash=flash,
                )
            )
        except queue.Full:
            pass

    def _Windowsスクリーン一覧を取得(self) -> list[スクリーン情報]:
        monitors: list[スクリーン情報] = []

        class RECT(ctypes.Structure):
            _fields_ = [
                ("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long),
            ]

        monitor_enum_proc = ctypes.WINFUNCTYPE(
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.POINTER(RECT),
            ctypes.c_void_p,
        )

        def callback(_monitor, _hdc, rect_ptr, _data):
            rect = rect_ptr.contents
            index = len(monitors)
            width = rect.right - rect.left
            height = rect.bottom - rect.top
            monitors.append(
                スクリーン情報(
                    index=index,
                    left=rect.left,
                    top=rect.top,
                    right=rect.right,
                    bottom=rect.bottom,
                    label=f"スクリーン{index + 1} ({width}x{height})",
                )
            )
            return 1

        ctypes.windll.user32.EnumDisplayMonitors(0, 0, monitor_enum_proc(callback), 0)
        return monitors or [スクリーン情報(index=0, left=0, top=0, right=1920, bottom=1080, label="スクリーン1")]
