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

import argparse
import ctypes
import ctypes.wintypes
import json
import os
import socket
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PySide6.QtCore import QEvent, QPoint, QTimer, Qt, QUrl
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView


def 引数を解析する() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="frontend_gui three-vrm viewer")
    parser.add_argument("--frontend-dir", type=Path, required=True)
    parser.add_argument("--state-file", type=Path, required=True)
    parser.add_argument("--parent-pid", type=int, required=True)
    return parser.parse_args()


def 親プロセスが生存中か(parent_pid: int) -> bool:
    if parent_pid <= 0:
        return False
    if os.name == "nt":
        process_query_limited_information = 0x1000
        still_active = 259
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(process_query_limited_information, False, parent_pid)
        if not handle:
            return False
        try:
            exit_code = ctypes.c_ulong()
            if kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)) == 0:
                return False
            return exit_code.value == still_active
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(parent_pid, 0)
        return True
    except OSError:
        return False


def 空きポートを探す() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class LocalServerThread(threading.Thread):
    def __init__(self, root_dir: Path) -> None:
        super().__init__(daemon=True)
        self.root_dir = root_dir
        self.port = 空きポートを探す()
        self.server: ThreadingHTTPServer | None = None

    def run(self) -> None:
        root_dir = self.root_dir

        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(root_dir), **kwargs)

            def log_message(self, format: str, *args) -> None:
                return

        self.server = ThreadingHTTPServer(("127.0.0.1", self.port), Handler)
        self.server.serve_forever()

    def 停止する(self) -> None:
        if self.server is None:
            return
        self.server.shutdown()
        self.server.server_close()


_RESIZE_BORDER = 8


class GuiWindow(QMainWindow):
    def __init__(self, state_file: Path, index_url: str, parent_pid: int) -> None:
        super().__init__()
        self.state_file = state_file
        self.parent_pid = parent_pid
        self.last_state: dict[str, object] = {}

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

        central_widget = QWidget()
        central_widget.setStyleSheet("background: transparent;")
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        self.webview = QWebEngineView()
        self.webview.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.webview.page().setBackgroundColor(QColor(0, 0, 0, 0))
        self.webview.setStyleSheet("background: transparent;")
        self.webview.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.webview.setUrl(QUrl(index_url))
        self.webview.installEventFilter(self)
        self.webview.page().windowCloseRequested.connect(self._ウィンドウを閉じる)
        layout.addWidget(self.webview)

        self.timer = QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.状態を反映する)
        self.timer.start()
        self.状態を反映する()

    def 状態を反映する(self) -> None:
        if not 親プロセスが生存中か(self.parent_pid):
            QApplication.instance().quit()
            return
        state = self._状態を読む()
        if not state.get("running", True):
            QApplication.instance().quit()
            return

        x = int(state.get("x", 100))
        y = int(state.get("y", 100))
        width = int(state.get("width", 480))
        height = int(state.get("height", 720))
        always_on_top = bool(state.get("always_on_top", False))
        self.setGeometry(x, y, width, height)
        self.setWindowTitle(str(state.get("title", "AiDiy GUI")))
        if always_on_top != bool(self.last_state.get("always_on_top", False)) or not self.last_state:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, always_on_top)
            self.show()

        camera_zoom = float(state.get("camera_zoom", 0.0))
        camera_offset_x = float(state.get("camera_offset_x", 0.0))
        camera_offset_y = float(state.get("camera_offset_y", 0.0))
        camera_command = str(state.get("camera_command", ""))
        camera_command_seq = int(state.get("camera_command_seq", 0))
        last_camera_zoom = float(self.last_state.get("camera_zoom", 0.0))
        last_camera_offset_x = float(self.last_state.get("camera_offset_x", 0.0))
        last_camera_offset_y = float(self.last_state.get("camera_offset_y", 0.0))
        last_camera_command_seq = int(self.last_state.get("camera_command_seq", 0))
        if (
            camera_zoom != last_camera_zoom
            or camera_offset_x != last_camera_offset_x
            or camera_offset_y != last_camera_offset_y
            or not self.last_state
        ):
            self.webview.page().runJavaScript(
                f"window.updateGuiView && window.updateGuiView({{zoom: {camera_zoom}, offsetX: {camera_offset_x}, offsetY: {camera_offset_y}}});"
            )
        if camera_command and camera_command_seq != last_camera_command_seq:
            self.webview.page().runJavaScript(
                f"window.applyGuiCommand && window.applyGuiCommand({json.dumps(camera_command, ensure_ascii=False)});"
            )
        lip_sync = float(state.get("lip_sync", 0.0))
        if lip_sync != float(self.last_state.get("lip_sync", 0.0)):
            self.webview.page().runJavaScript(
                f"window.updateLipSync && window.updateLipSync({lip_sync});"
            )
        self.last_state = state

    def _ウィンドウを閉じる(self) -> None:
        state = self._状態を読む()
        state["running"] = False
        self.state_file.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
        self.close()

    def closeEvent(self, event) -> None:  # noqa: N802
        self.timer.stop()
        super().closeEvent(event)

    def _状態を読む(self) -> dict[str, object]:
        if not self.state_file.exists():
            return {"running": False}
        try:
            return json.loads(self.state_file.read_text(encoding="utf-8"))
        except Exception:
            return self.last_state or {"running": True}


def main() -> int:
    args = 引数を解析する()
    server = LocalServerThread(args.frontend_dir)
    server.start()

    app = QApplication([])
    state = json.loads(args.state_file.read_text(encoding="utf-8"))
    index_url = f"http://127.0.0.1:{server.port}/GUI制御/three_vrm/three_vrm_index.html?model={state['model_url']}"
    window = GuiWindow(args.state_file, index_url, args.parent_pid)
    window.show()
    try:
        return app.exec()
    finally:
        server.停止する()


if __name__ == "__main__":
    raise SystemExit(main())
