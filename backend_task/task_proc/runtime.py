# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""backend_task の定期処理と再起動監視。"""

from __future__ import annotations

import asyncio
import logging
import os
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncIterator, Callable

from fastapi import FastAPI

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def now_hms() -> str:
    return datetime.now().strftime("%H:%M:%S")


def setup_reboot_watcher(logger: logging.Logger) -> None:
    temp_dir = os.path.join(BASE_DIR, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    reboot_path = os.path.join(temp_dir, "reboot_task.txt")

    def consume_reboot_file() -> bool:
        if not os.path.isfile(reboot_path):
            return False
        try:
            os.remove(reboot_path)
        except FileNotFoundError:
            pass
        except Exception:
            logger.exception("reboot_task.txt の削除に失敗しました")
        return True

    if consume_reboot_file():
        logger.info("reboot_task.txt を検知したため終了します")
        raise SystemExit("reboot_task.txt detected")

    def watch_loop() -> None:
        while True:
            time.sleep(1)
            if consume_reboot_file():
                logger.info("reboot_task.txt を検知したため終了します")
                os._exit(0)

    threading.Thread(target=watch_loop, daemon=True, name="backend_task_reboot_watcher").start()


def build_lifespan(logger: logging.Logger) -> Callable[[FastAPI], AsyncIterator[None]]:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        del app
        # システム開始時（再起動含む）: 残存 PID のプロセスを強制停止してクリア
        from . import tasks_watcher
        await asyncio.to_thread(tasks_watcher.起動時クリーンアップ, logger)
        # タイマー起動前: 停止中に期限が到来した実行条件は発火させず次周期へ更新する
        await asyncio.to_thread(tasks_watcher.起動時実行条件初期化, logger)

        watcher = asyncio.create_task(tasks_watcher.監視ループ(logger), name="backend_task_ai_watcher")
        条件watcher = asyncio.create_task(
            tasks_watcher.実行条件監視ループ(logger), name="backend_task_condition_watcher"
        )
        logger.info(
            "backend_task を開始しました (明細起動=%ss, 実行条件確認=%ss)",
            tasks_watcher.監視間隔秒, tasks_watcher.実行条件監視間隔秒,
        )
        try:
            yield
        finally:
            for task in (watcher, 条件watcher):
                task.cancel()
            for task in (watcher, 条件watcher):
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            logger.info("backend_task を停止しました")

    return lifespan
