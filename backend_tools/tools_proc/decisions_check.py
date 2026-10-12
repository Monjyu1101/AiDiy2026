"""AIコアのAI判断への薄い接続。判断ロジックはbackend_serverに集約する。"""
from pathlib import Path
import sys

_backend = str(Path(__file__).resolve().parents[2] / "backend_server")
if _backend not in sys.path:
    sys.path.append(_backend)

from AIコア.AI判断 import Decision  # noqa: E402, F401
from AIコア.AI判断共通 import DecisionError, DecisionRequest  # noqa: E402, F401
