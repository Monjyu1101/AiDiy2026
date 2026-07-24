# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

from __future__ import annotations

import asyncio
import logging
import os
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Callable

from fastapi import FastAPI

from .store import シミュレーションループ
from .team_watcher import 監視ループ, 起動時クリーンアップ

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
        logger.info("reboot_team.txt を検知したため終了します")
        raise SystemExit("reboot_team.txt detected")

    def watch() -> None:
        while True:
            time.sleep(1)
            if consume():
                logger.info("reboot_team.txt を検知したため終了します")
                os._exit(0)

    threading.Thread(target=watch, daemon=True, name="backend_team_reboot_watcher").start()


def build_lifespan(logger: logging.Logger) -> Callable[[FastAPI], AsyncIterator[None]]:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        del app
        from . import team_work_db

        team_work_db.初期化()
        起動時クリーンアップ(logger)
        tasks = [
            asyncio.create_task(シミュレーションループ(logger), name="backend_team_simulation"),
            asyncio.create_task(監視ループ(logger), name="backend_team_work_watcher"),
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

    return lifespan
