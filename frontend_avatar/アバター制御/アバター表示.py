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

import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

from log_config import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class ThreeVRMViewerConfig:
    frontend_dir: Path
    viewer_script: Path
    viewer_html: Path
    vrm_path: Path
    window_x: int
    window_y: int
    window_width: int
    window_height: int
    always_on_top: bool
    title: str
    parent_pid: int


@dataclass(slots=True)
class ThreeVRMViewerProcess:
    process: subprocess.Popen[bytes]
    state_path: Path

    def 状態を書き込む(
        self,
        *,
        x: int | None = None,
        y: int | None = None,
        width: int | None = None,
        height: int | None = None,
        always_on_top: bool | None = None,
        running: bool | None = None,
        camera_zoom: float | None = None,
        camera_offset_x: float | None = None,
        camera_offset_y: float | None = None,
        camera_command: str | None = None,
        camera_command_seq: int | None = None,
        lip_sync: float | None = None,
    ) -> None:
        state = self._状態を読む()
        if x is not None:
            state["x"] = int(x)
        if y is not None:
            state["y"] = int(y)
        if width is not None:
            state["width"] = int(width)
        if height is not None:
            state["height"] = int(height)
        if always_on_top is not None:
            state["always_on_top"] = bool(always_on_top)
        if running is not None:
            state["running"] = bool(running)
        if camera_zoom is not None:
            state["camera_zoom"] = float(camera_zoom)
        if camera_offset_x is not None:
            state["camera_offset_x"] = float(camera_offset_x)
        if camera_offset_y is not None:
            state["camera_offset_y"] = float(camera_offset_y)
        if camera_command is not None:
            state["camera_command"] = str(camera_command)
        if camera_command_seq is not None:
            state["camera_command_seq"] = int(camera_command_seq)
        if lip_sync is not None:
            state["lip_sync"] = round(float(lip_sync), 3)
        self.state_path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

    def 停止する(self) -> None:
        if self.process.poll() is None:
            self.状態を書き込む(running=False)
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=5)
        try:
            self.state_path.unlink(missing_ok=True)
        except OSError:
            return

    def 状態を読む(self) -> dict:
        return self._状態を読む()

    def _状態を読む(self) -> dict:
        if not self.state_path.exists():
            return {}
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except Exception:
            return {}


class ThreeVRMViewerLauncher:
    def __init__(self, frontend_dir: Path) -> None:
        self.frontend_dir = frontend_dir
        self.assets_dir = frontend_dir / "アバター制御" / "three_vrm"
        self.viewer_script = self.assets_dir / "three_vrm_viewer.py"
        self.viewer_html = self.assets_dir / "three_vrm_index.html"

    def 設定を作る(
        self,
        *,
        vrm_path: Path,
        window_x: int,
        window_y: int,
        window_width: int,
        window_height: int,
        always_on_top: bool,
        title: str,
    ) -> ThreeVRMViewerConfig:
        return ThreeVRMViewerConfig(
            frontend_dir=self.frontend_dir,
            viewer_script=self.viewer_script,
            viewer_html=self.viewer_html,
            vrm_path=vrm_path,
            window_x=window_x,
            window_y=window_y,
            window_width=window_width,
            window_height=window_height,
            always_on_top=always_on_top,
            title=title,
            parent_pid=os.getpid(),
        )

    def 起動する(self, config: ThreeVRMViewerConfig) -> ThreeVRMViewerProcess:
        if not config.viewer_script.exists():
            raise FileNotFoundError(f"three-vrm ビューアスクリプトが見つかりません: {config.viewer_script}")
        if not config.viewer_html.exists():
            raise FileNotFoundError(f"three-vrm ビューアHTMLが見つかりません: {config.viewer_html}")
        if not config.vrm_path.exists():
            raise FileNotFoundError(f"VRM ファイルが見つかりません: {config.vrm_path}")

        state_path = Path(tempfile.gettempdir()) / f"frontend_avatar_three_vrm_{config.vrm_path.stem}.json"
        model_relative = config.vrm_path.relative_to(config.frontend_dir).as_posix()
        state = {
            "x": config.window_x,
            "y": config.window_y,
            "width": config.window_width,
            "height": config.window_height,
            "always_on_top": config.always_on_top,
            "running": True,
            "title": config.title,
            "model_url": "/" + quote(model_relative, safe="/"),
            "camera_zoom": 1.08,
            "camera_offset_x": 0.0,
            "camera_offset_y": 0.95,
            "camera_command": "",
            "camera_command_seq": 0,
        }
        state_path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

        command = [
            sys.executable,
            str(config.viewer_script),
            "--frontend-dir",
            str(config.frontend_dir),
            "--state-file",
            str(state_path),
            "--parent-pid",
            str(config.parent_pid),
        ]
        logger.info("three-vrm ビューアを起動します: %s", config.vrm_path)
        process = subprocess.Popen(command, cwd=str(config.frontend_dir))
        return ThreeVRMViewerProcess(process=process, state_path=state_path)
