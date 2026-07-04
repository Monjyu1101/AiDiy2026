# -*- coding: utf-8 -*-

"""バックエンド(task) FastAPI エントリポイント。"""

from __future__ import annotations

from log_config import setup_logging
from task_proc.app import create_app

setup_logging("task_main")

app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("task_main:app", host="0.0.0.0", port=8093)
