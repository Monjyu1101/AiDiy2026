from __future__ import annotations

import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


BACKEND_TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_TOOLS_DIR))

import tools_main  # noqa: E402


class PlatformRegistrationTests(unittest.TestCase):
    def test_windows_control_is_only_published_on_windows(self) -> None:
        windows = sys.platform == "win32"
        with TestClient(tools_main.app) as client:
            names = client.get("/").json()["mcps"]
            self.assertEqual(len(names), 19 if windows else 18)
            self.assertEqual("aidiy_windows_control" in names, windows)
            self.assertEqual(
                client.get("/aidiy_windows_control/ping").status_code,
                200 if windows else 404,
            )
            self.assertEqual(client.get("/aidiy_sqlite/ping").status_code, 200)


if __name__ == "__main__":
    unittest.main()
