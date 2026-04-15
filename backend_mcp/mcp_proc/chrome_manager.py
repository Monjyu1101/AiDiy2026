# Copyright (c) 2026 monjyu1101@gmail.com
"""
Chrome プロセス管理

Chrome を --remote-debugging-port で自動起動・状態確認する。
"""

import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from log_config import get_logger

logger = get_logger(__name__)

# Windows での Chrome/Edge 候補パス
_CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Users\{username}\AppData\Local\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    # Linux / macOS
    "/usr/bin/google-chrome",
    "/usr/bin/chromium-browser",
    "/usr/bin/chromium",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]

# 専用プロファイルディレクトリ (ユーザーの通常プロファイルと分離)
_PROFILE_DIR = str(Path(__file__).parent.parent / "temp" / "_chrome_profile")


class ChromeManager:
    """
    Chrome プロセスの起動・状態管理

    is_running() で疎通確認し、起動していなければ launch() で起動する。
    ensure_running() を呼ぶだけで自動起動まで完了する。
    """

    def __init__(self, debug_port: int = 9222, profile_dir: str = _PROFILE_DIR):
        self.debug_port = debug_port
        self.profile_dir = profile_dir
        self._process: subprocess.Popen | None = None

    # ------------------------------------------------------------------ #
    # 状態確認
    # ------------------------------------------------------------------ #

    def is_running(self) -> bool:
        """Chrome がデバッグポートで応答しているか確認"""
        url = f"http://localhost:{self.debug_port}/json/version"
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                return resp.status == 200
        except Exception:
            return False

    def get_version(self) -> dict | None:
        """Chrome のバージョン情報を返す (未起動時は None)"""
        import json

        url = f"http://localhost:{self.debug_port}/json/version"
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                return json.loads(resp.read().decode())
        except Exception:
            return None

    # ------------------------------------------------------------------ #
    # 起動
    # ------------------------------------------------------------------ #

    def find_chrome(self) -> str | None:
        """Chrome / Edge の実行ファイルパスを返す (見つからなければ None)"""
        username = os.environ.get("USERNAME", os.environ.get("USER", ""))
        for candidate in _CHROME_CANDIDATES:
            path = candidate.format(username=username)
            if Path(path).exists():
                return path

        # 環境変数で明示指定されている場合
        env_path = os.environ.get("CHROME_EXECUTABLE")
        if env_path and Path(env_path).exists():
            return env_path

        return None

    def launch(self, wait_timeout: float = 10.0) -> str:
        """
        Chrome をリモートデバッグモードで起動する。

        Args:
            wait_timeout: 起動完了待ちのタイムアウト秒数

        Returns:
            "already_running" | "launched" | "launch_failed"

        Raises:
            FileNotFoundError: Chrome が見つからない場合
        """
        if self.is_running():
            return "already_running"

        chrome_path = self.find_chrome()
        if not chrome_path:
            raise FileNotFoundError(
                "Chrome / Edge が見つかりません。\n"
                "環境変数 CHROME_EXECUTABLE にパスを指定するか、\n"
                "Chrome をインストールしてください。"
            )

        args = [
            chrome_path,
            f"--remote-debugging-port={self.debug_port}",
            f"--user-data-dir={self.profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-default-apps",
            "--enable-automation",   # 「自動制御されています」バナーを表示
        ]

        logger.info(f"起動: {chrome_path}")
        self._process = subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # 起動完了を待つ
        deadline = time.monotonic() + wait_timeout
        while time.monotonic() < deadline:
            if self.is_running():
                logger.info(f"起動完了 (port={self.debug_port})")
                return "launched"
            time.sleep(0.3)

        logger.warning("起動タイムアウト")
        return "launch_failed"

    def ensure_running(self) -> str:
        """
        Chrome が起動していなければ自動起動する。

        Returns:
            "already_running" | "launched" | "launch_failed"

        Raises:
            FileNotFoundError: Chrome が見つからない場合
        """
        if self.is_running():
            return "already_running"
        return self.launch()
