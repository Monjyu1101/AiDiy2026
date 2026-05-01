"""CLI 表示 — スピナー、ツールプレビュー、結果フォーマット。"""
import json
import logging
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


_RESET = "\033[0m"
_RED = "\033[31m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_CYAN = "\033[36m"


@dataclass
class Spinner:
    """CLI スピナー — API 呼び出し中にアニメーションを表示。"""

    frames: list = field(default_factory=lambda: ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"])
    interval: float = 0.1
    message: str = ""

    def __post_init__(self):
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

    def start(self, message: str = ""):
        """スピナーを開始する。"""
        if message:
            self.message = message
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        i = 0
        while not self._stop.is_set():
            frame = self.frames[i % len(self.frames)]
            msg = f" {frame} {self.message}" if self.message else f" {frame}"
            sys.stderr.write(f"\r{msg}")
            sys.stderr.flush()
            time.sleep(self.interval)
            i += 1

    def stop(self):
        """スピナーを停止し、行を消去する。"""
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1)
        sys.stderr.write("\r\033[K")
        sys.stderr.flush()


def display_tool_result(tool_name: str, result: str, emoji: str = "⚡") -> None:
    """ツール実行結果を表示する。"""
    try:
        data = json.loads(result)
    except json.JSONDecodeError:
        data = {"raw": result}

    if "error" in data:
        print(f"  {_RED}✗ {tool_name}: {data['error'][:200]}{_RESET}")
    elif "success" in data:
        print(f"  {_GREEN}{emoji} {tool_name} ✓{_RESET}")
    else:
        keys = list(data.keys())[:3]
        summary = ", ".join(f"{k}={data[k]}" for k in keys)
        print(f"  {_CYAN}{emoji} {tool_name} → {summary}{_RESET}")


def display_diff(diff_text: str) -> None:
    """unified diff を色付きで表示する。"""
    for line in diff_text.split("\n"):
        if line.startswith("+"):
            print(f"{_GREEN}{line}{_RESET}")
        elif line.startswith("-"):
            print(f"{_RED}{line}{_RESET}")
        elif line.startswith("@@"):
            print(f"{_CYAN}{line}{_RESET}")
        else:
            print(line)
