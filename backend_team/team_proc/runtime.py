# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""backend_team の起動処理・定期処理・再起動監視。"""

from __future__ import annotations

import asyncio
import logging
import os
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator, Callable

from fastapi import FastAPI

from .store import シミュレーションループ
from .team_watcher import 状態監視間隔秒, 状態監視ループ, 起動監視ループ, 起動監視間隔秒, 起動時クリーンアップ

BASE_DIR = Path(__file__).resolve().parents[1]


def now_hms() -> str:
    return datetime.now().strftime("%H:%M:%S")


def setup_reboot_watcher(logger: logging.Logger) -> None:
    temp_dir = BASE_DIR / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    reboot_path = temp_dir / "reboot_team.txt"

    def consume_reboot_file() -> bool:
        if not reboot_path.is_file():
            return False
        try:
            reboot_path.unlink()
        except FileNotFoundError:
            pass
        except Exception:
            logger.exception("reboot_team.txt の削除に失敗しました")
        return True

    if consume_reboot_file():
        logger.info("reboot_team.txt を検知したため終了します")
        raise SystemExit("reboot_team.txt detected")

    def watch_loop() -> None:
        while True:
            time.sleep(1)
            if consume_reboot_file():
                logger.info("reboot_team.txt を検知したため終了します")
                os._exit(0)

    threading.Thread(target=watch_loop, daemon=True, name="backend_team_reboot_watcher").start()


def build_lifespan(logger: logging.Logger) -> Callable[[FastAPI], AsyncIterator[None]]:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        del app
        from . import team_db, team_exp_db, team_goal_db, team_pdca_db, team_talk_db, team_work_db

        team_work_db.初期化()
        team_exp_db.初期化()
        team_pdca_db.初期化()
        await asyncio.to_thread(team_db.初期要員を召喚)
        await asyncio.to_thread(team_goal_db.初期目標を投入)
        会話クリア件数 = await asyncio.to_thread(team_talk_db.起動時クリア)
        if 会話クリア件数:
            logger.info("backend_team 起動時にAチーム会話をクリアしました: %d件", 会話クリア件数)
        自動作業設定解除件数 = await asyncio.to_thread(team_goal_db.起動時自動作業設定をオフ)
        if 自動作業設定解除件数:
            logger.info(
                "backend_team 起動時にAチーム目標の自動作業設定をオフへ戻しました: %d件",
                自動作業設定解除件数,
            )
        作業ループ解除件数 = await asyncio.to_thread(team_goal_db.起動時作業ループをオフ)
        if 作業ループ解除件数:
            logger.info(
                "backend_team 起動時にAチーム目標の作業ループをオフへ戻しました: %d件",
                作業ループ解除件数,
            )
        # システム開始時（再起動含む）: 残存 PID・生成中の経験などをエラーとして記録しクリア（強制停止はしない）
        await asyncio.to_thread(起動時クリーンアップ, logger)
        tasks = [
            asyncio.create_task(シミュレーションループ(logger), name="backend_team_simulation"),
            asyncio.create_task(起動監視ループ(logger), name="backend_team_launch_watcher"),
            asyncio.create_task(状態監視ループ(logger), name="backend_team_status_watcher"),
        ]
        logger.info(
            "backend_team を開始しました (起動監視=%ss, 状態監視=%ss)",
            起動監視間隔秒, 状態監視間隔秒,
        )
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
