# -*- coding: utf-8 -*-

from __future__ import annotations

import asyncio
import os
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

from .store import simulation_loop
from .team_watcher import startup_cleanup, watch_loop

BASE_DIR = Path(__file__).resolve().parents[1]


def setup_reboot_watcher(logger) -> None:
    temp_dir = BASE_DIR / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    reboot_path = temp_dir / "reboot_team.txt"

    def consume() -> bool:
        if not reboot_path.is_file():
            return False
        try:
            reboot_path.unlink()
        except FileNotFoundError:
            pass
        return True

    if consume():
        raise SystemExit("reboot_team.txt detected")

    def watch() -> None:
        while True:
            time.sleep(1)
            if consume():
                logger.info("reboot_team.txt を検知したため終了します")
                os._exit(0)

    threading.Thread(target=watch, daemon=True, name="backend_team_reboot_watcher").start()


@asynccontextmanager
async def lifespan(app):
    del app
    from log_config import get_logger
    from . import team_work_db

    logger = get_logger("team_main")
    team_work_db.initialize()
    startup_cleanup(logger)
    tasks = [
        asyncio.create_task(simulation_loop(logger), name="backend_team_simulation"),
        asyncio.create_task(watch_loop(logger), name="backend_team_work_watcher"),
    ]
    logger.info("backend_team を開始しました")
    try:
        yield
    finally:
        for task in tasks:
            task.cancel()
        for task in tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass
        logger.info("backend_team を停止しました")
